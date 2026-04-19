import json
import logging
import base64
import hashlib
import hmac
import math
import os
import random
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta

from app.config import ROOT, resolve_config_path
from app.common.errors import ApiError
from app.common.utils import clamp, now_iso, safe_text
from app.services.email_service import EmailService
from app.services.sync_service import SyncManager
from app.storage.state_store import create_state_store


log = logging.getLogger("nexra-python")

QUERY_INTENT_TERMS = {
    "writing": {
        "positive": [
            "writing", "write", "writer", "copywriting", "content", "content creation",
            "blog", "article", "draft", "rewrite", "rewriting", "story", "novel",
            "script", "text summarization", "summarization", "summary", "report generation",
        ],
        "negative": [
            "filesystem access", "file operations", "file management", "write files",
            "writing files", "local file", "storage",
        ],
    },
    "summarization": {
        "positive": [
            "summary", "summarization", "summarize", "text summarization", "report generation",
            "notes", "brief", "digest",
        ],
        "negative": [
            "filesystem access", "file operations", "storage",
        ],
    },
    "text to image": {
        "positive": [
            "text to image", "image generation", "text-to-image", "media generation",
            "image generator", "image creation", "generate image", "design & media",
        ],
        "negative": [
            "project management", "ticket management", "design context", "filesystem access",
            "documentation", "browser automation", "code & git", "repository access",
        ],
    },
    "image edit": {
        "positive": [
            "image edit", "image editing", "image generation", "media generation",
            "design & media", "image",
        ],
        "negative": [
            "project management", "ticket management", "documentation",
        ],
    },
    "ocr": {
        "positive": [
            "ocr", "optical character recognition", "pdf", "document extraction",
            "text extraction", "scan", "image analyzer", "ocr pdf",
        ],
        "negative": [
            "design context", "project management", "browser automation", "documentation lookup", "documentation",
        ],
    },
    "rewrite": {
        "positive": [
            "rewrite", "rewriting", "text summarization", "content", "writing",
            "editor", "prompt", "copywriting",
        ],
        "negative": [
            "database queries", "databases", "ticket management", "project management",
        ],
    },
    "novel": {
        "positive": [
            "novel", "story", "writing", "rewrite", "content", "script",
            "text summarization", "media generation",
        ],
        "negative": [
            "ticket management", "project management", "database queries",
        ],
    },
}

class NexraService:
    def __init__(self, load_catalog=True):
        self.load_catalog = load_catalog
        self.config = self._load_config()
        self.skill_data_file = ROOT / self.config["skillDataFile"]
        self.state_store = create_state_store(self.config)
        self.lock = threading.RLock()
        self.conn = None
        self.email_service = EmailService()
        self.sync_manager = SyncManager(self)
        self._dashboard_cache = None
        self._dashboard_cache_ttl_seconds = 30
        self._skill_cache = None
        self._skill_cache_by_id = None
        self._prepare()

    def _load_config(self):
        config_path = resolve_config_path()
        log.info("Loading application config from %s", config_path)
        with config_path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)

    def _prepare(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        if self.load_catalog:
            self._load_snapshot_or_seed()
            self._load_or_initialize_auth_state()
            self._rebuild_metric_tables()
            self.sync_manager.last_imported_count = self.imported_skill_count()
            self.sync_manager.start_scheduler()
        else:
            self._load_auth_only_state()
        log.info("State backend initialized. target=%s", self.state_store.describe())

    def connect(self):
        return self.conn

    def _init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS email_verifications (
                    email TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS skills (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price_per_call REAL NOT NULL,
                    status TEXT NOT NULL,
                    success_rate INTEGER NOT NULL,
                    latency_p95 INTEGER NOT NULL,
                    cost_efficiency INTEGER NOT NULL,
                    user_rating_avg REAL NOT NULL,
                    user_rating_count INTEGER NOT NULL,
                    recent_calls INTEGER NOT NULL,
                    invocation_method TEXT NOT NULL,
                    submitted_by TEXT NOT NULL,
                    approval_status TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    reviewed_by TEXT,
                    review_result TEXT,
                    source TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_author TEXT NOT NULL,
                    license TEXT NOT NULL,
                    operating_system TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS skill_functions (
                    skill_id TEXT NOT NULL,
                    function_order INTEGER NOT NULL,
                    function_name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS skill_review_events (
                    id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    reviewer_user_id TEXT NOT NULL,
                    reviewer_name TEXT NOT NULL,
                    result TEXT NOT NULL,
                    note TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    last_used TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS billing_transactions (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS daily_visits (
                    metric_date TEXT PRIMARY KEY,
                    visit_count INTEGER NOT NULL DEFAULT 0,
                    anonymous_visit_count INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS metric_totals (
                    metric_key TEXT PRIMARY KEY,
                    metric_value INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS metric_daily (
                    metric_date TEXT PRIMARY KEY,
                    registered_users INTEGER NOT NULL DEFAULT 0,
                    visits INTEGER NOT NULL DEFAULT 0,
                    anonymous_visits INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            self._migrate_schema(conn)

    def _migrate_schema(self, conn):
        migrations = [
            "ALTER TABLE users ADD COLUMN created_at TEXT",
            "ALTER TABLE skills ADD COLUMN submitted_at TEXT",
            "ALTER TABLE skills ADD COLUMN reviewed_at TEXT",
            "ALTER TABLE skills ADD COLUMN reviewed_by TEXT",
            "ALTER TABLE skills ADD COLUMN review_result TEXT",
            "ALTER TABLE daily_visits ADD COLUMN anonymous_visit_count INTEGER NOT NULL DEFAULT 0",
        ]
        for statement in migrations:
            try:
                conn.execute(statement)
            except Exception:
                pass
        conn.execute(
            """
            UPDATE users
            SET created_at = COALESCE(created_at, '2026-01-01T00:00:00Z')
            WHERE created_at IS NULL OR created_at = ''
            """
        )
        conn.execute(
            """
            UPDATE skills
            SET submitted_at = COALESCE(submitted_at, '2026-01-01T00:00:00Z'),
                reviewed_at = reviewed_at,
                reviewed_by = reviewed_by,
                review_result = COALESCE(review_result, approval_status)
            WHERE submitted_at IS NULL OR review_result IS NULL
            """
        )

    def _seed_defaults(self):
        with self.lock, self.connect() as conn:
            seeded = False
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                self._seed_default_users(conn)
                log.info("Seeded default user accounts.")
                seeded = True

            if conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0] == 0:
                self._insert_skills(conn, self.read_skill_seed_file())
                self._insert_skill(
                    conn,
                    {
                        "id": "skill-report",
                        "name": "Report Composer",
                        "category": "Productivity",
                        "description": "Drafts structured summaries, release notes, and stakeholder-ready reports from operational events.",
                        "pricePerCall": 0.05,
                        "status": "draft",
                        "successRate": 90,
                        "latencyP95": 480,
                        "costEfficiency": 79,
                        "userRatingAvg": 0.0,
                        "userRatingCount": 0,
                        "recentCalls": 0,
                        "functions": ["report generation", "summarization", "release notes"],
                        "invocationMethod": "REST API with JSON instructions",
                        "submittedBy": "user_1",
                        "approvalStatus": "PENDING",
                        "submittedAt": "2026-01-01T00:00:00Z",
                        "reviewedAt": None,
                        "reviewedBy": "",
                        "reviewResult": "PENDING",
                        "source": "manual",
                        "sourceUrl": "https://example.com/report-composer",
                        "sourceAuthor": "Alice Builder",
                        "license": "Proprietary",
                        "operatingSystem": "Cloud / API",
                    },
                )
                log.info("Seeded initial skill catalog.")
                seeded = True

            if conn.execute("SELECT COUNT(*) FROM billing_transactions").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO billing_transactions (id, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                    [
                        ("txn_1001", "Invocation charges", -124.32, "2026-04-09 18:10"),
                        ("txn_1002", "Top-up", 500.00, "2026-04-08 09:30"),
                        ("txn_1003", "Invocation charges", -87.76, "2026-04-07 20:12"),
                    ],
                )
                seeded = True

            if conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO api_keys (id, name, scope, last_used, status) VALUES (?, ?, ?, ?, ?)",
                    [
                        ("nk_live_01", "Production Search Client", "skills:read", "3 min ago", "active"),
                        ("nk_test_02", "Staging Agent", "skills:read", "2 hrs ago", "active"),
                        ("nk_old_03", "Legacy QA", "skills:read", "12 days ago", "revoked"),
                    ],
                )
                seeded = True
            if seeded:
                conn.commit()
                self._save_catalog_state()

    def _seed_default_users(self, conn):
        conn.executemany(
            "INSERT INTO users (id, email, password, name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("admin_1", "admin@nexra.local", "admin123", "Nexra Admin", "ADMIN", "2026-01-01T00:00:00Z"),
                ("user_1", "alice@nexra.local", "alice123", "Alice Builder", "USER", "2026-01-01T00:00:00Z"),
                ("user_2", "bob@nexra.local", "bob123", "Bob Operator", "USER", "2026-01-01T00:00:00Z"),
            ],
        )

    def _load_snapshot_or_seed(self):
        if hasattr(self.state_store, "load_catalog_state"):
            catalog_state = self.state_store.load_catalog_state()
            if catalog_state and catalog_state.get("skills"):
                self._load_catalog_state(catalog_state)
                return
        snapshot = self.state_store.load_snapshot()
        if snapshot:
            self._load_snapshot(snapshot)
            return
        self._seed_defaults()

    def _load_catalog_state(self, catalog_state):
        with self.lock, self.connect() as conn:
            conn.executescript(
                """
                DELETE FROM skills;
                DELETE FROM skill_functions;
                DELETE FROM reviews;
                DELETE FROM skill_review_events;
                DELETE FROM api_keys;
                DELETE FROM billing_transactions;
                DELETE FROM daily_visits;
                """
            )
            for row in catalog_state.get("skills", []):
                self._insert_skill(conn, row)
            for row in catalog_state.get("reviews", []):
                conn.execute(
                    "INSERT INTO reviews (id, skill_id, user_id, author, rating, comment, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["id"], row["skill_id"], row["user_id"], row["author"], row["rating"], row["comment"], row["timestamp"]),
                )
            for row in catalog_state.get("skill_review_events", []):
                conn.execute(
                    """
                    INSERT INTO skill_review_events (id, skill_id, reviewer_user_id, reviewer_name, result, note, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row["skill_id"],
                        row["reviewer_user_id"],
                        row["reviewer_name"],
                        row["result"],
                        row["note"],
                        row["timestamp"],
                    ),
                )
            for row in catalog_state.get("api_keys", []):
                conn.execute(
                    "INSERT INTO api_keys (id, name, scope, last_used, status) VALUES (?, ?, ?, ?, ?)",
                    (row["id"], row["name"], row["scope"], row["last_used"], row["status"]),
                )
            for row in catalog_state.get("billing_transactions", []):
                conn.execute(
                    "INSERT INTO billing_transactions (id, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                    (row["id"], row["type"], row["amount"], row["timestamp"]),
                )
            for row in catalog_state.get("daily_visits", []):
                conn.execute(
                    "INSERT INTO daily_visits (metric_date, visit_count, anonymous_visit_count) VALUES (?, ?, ?)",
                    (row["metric_date"], row["visit_count"], row.get("anonymous_visit_count", 0)),
                )
            conn.commit()

    def _current_catalog_state(self):
        with self.lock, self.connect() as conn:
            return {
                "skills": self._fetch_all_skills(),
                "skill_functions": [dict(row) for row in conn.execute("SELECT * FROM skill_functions").fetchall()],
                "reviews": [dict(row) for row in conn.execute("SELECT * FROM reviews").fetchall()],
                "skill_review_events": [dict(row) for row in conn.execute("SELECT * FROM skill_review_events").fetchall()],
                "api_keys": [dict(row) for row in conn.execute("SELECT * FROM api_keys").fetchall()],
                "billing_transactions": [dict(row) for row in conn.execute("SELECT * FROM billing_transactions").fetchall()],
                "daily_visits": [dict(row) for row in conn.execute("SELECT * FROM daily_visits").fetchall()],
            }

    def _save_catalog_state(self):
        if hasattr(self.state_store, "save_catalog_state"):
            self.state_store.save_catalog_state(self._current_catalog_state())
            return
        self._save_snapshot()

    def _invalidate_skill_cache(self):
        self._skill_cache = None
        self._skill_cache_by_id = None

    def _copy_skill(self, skill):
        return {
            **skill,
            "functions": list(skill.get("functions", [])),
        }

    def _load_snapshot(self, snapshot):
        with self.lock, self.connect() as conn:
            conn.executescript(
                """
                DELETE FROM users;
                DELETE FROM sessions;
                DELETE FROM email_verifications;
                DELETE FROM skills;
                DELETE FROM skill_functions;
                DELETE FROM reviews;
                DELETE FROM skill_review_events;
                DELETE FROM api_keys;
                DELETE FROM billing_transactions;
                DELETE FROM daily_visits;
                """
            )
            for row in snapshot.get("users", []):
                conn.execute(
                    "INSERT INTO users (id, email, password, name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row["id"], row["email"], row["password"], row["name"], row["role"], row.get("created_at", "2026-01-01T00:00:00Z")),
                )
            for row in snapshot.get("sessions", []):
                conn.execute(
                    "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                    (row["token"], row["user_id"], row["created_at"]),
                )
            for row in snapshot.get("email_verifications", []):
                conn.execute(
                    "INSERT INTO email_verifications (email, code, expires_at, created_at) VALUES (?, ?, ?, ?)",
                    (row["email"], row["code"], row["expires_at"], row["created_at"]),
                )
            for row in snapshot.get("skills", []):
                conn.execute(
                    """
                    INSERT INTO skills (
                        id, name, category, description, price_per_call, status, success_rate,
                        latency_p95, cost_efficiency, user_rating_avg, user_rating_count, recent_calls,
                        invocation_method, submitted_by, approval_status, submitted_at, reviewed_at, reviewed_by, review_result, source, source_url,
                        source_author, license, operating_system
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"], row["name"], row["category"], row["description"], row["price_per_call"],
                        row["status"], row["success_rate"], row["latency_p95"], row["cost_efficiency"],
                        row["user_rating_avg"], row["user_rating_count"], row["recent_calls"],
                        row["invocation_method"], row["submitted_by"], row["approval_status"], row.get("submitted_at", "2026-01-01T00:00:00Z"),
                        row.get("reviewed_at"), row.get("reviewed_by"), row.get("review_result", row["approval_status"]), row["source"],
                        row["source_url"], row["source_author"], row["license"], row["operating_system"],
                    ),
                )
            for row in snapshot.get("skill_functions", []):
                conn.execute(
                    "INSERT INTO skill_functions (skill_id, function_order, function_name) VALUES (?, ?, ?)",
                    (row["skill_id"], row["function_order"], row["function_name"]),
                )
            for row in snapshot.get("reviews", []):
                conn.execute(
                    "INSERT INTO reviews (id, skill_id, user_id, author, rating, comment, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["id"], row["skill_id"], row["user_id"], row["author"], row["rating"], row["comment"], row["timestamp"]),
                )
            for row in snapshot.get("skill_review_events", []):
                conn.execute(
                    """
                    INSERT INTO skill_review_events (id, skill_id, reviewer_user_id, reviewer_name, result, note, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"], row["skill_id"], row["reviewer_user_id"], row["reviewer_name"],
                        row["result"], row["note"], row["timestamp"],
                    ),
                )
            for row in snapshot.get("api_keys", []):
                conn.execute(
                    "INSERT INTO api_keys (id, name, scope, last_used, status) VALUES (?, ?, ?, ?, ?)",
                    (row["id"], row["name"], row["scope"], row["last_used"], row["status"]),
                )
            for row in snapshot.get("billing_transactions", []):
                conn.execute(
                    "INSERT INTO billing_transactions (id, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                    (row["id"], row["type"], row["amount"], row["timestamp"]),
                )
            for row in snapshot.get("daily_visits", []):
                conn.execute(
                    "INSERT INTO daily_visits (metric_date, visit_count, anonymous_visit_count) VALUES (?, ?, ?)",
                    (row["metric_date"], row["visit_count"], row.get("anonymous_visit_count", 0)),
                )
            conn.commit()

    def _save_snapshot(self):
        with self.lock, self.connect() as conn:
            snapshot = {
                "users": [dict(row) for row in conn.execute("SELECT * FROM users").fetchall()],
                "sessions": [dict(row) for row in conn.execute("SELECT * FROM sessions").fetchall()],
                "email_verifications": [dict(row) for row in conn.execute("SELECT * FROM email_verifications").fetchall()],
                "skills": [dict(row) for row in conn.execute("SELECT * FROM skills").fetchall()],
                "skill_functions": [dict(row) for row in conn.execute("SELECT * FROM skill_functions").fetchall()],
                "reviews": [dict(row) for row in conn.execute("SELECT * FROM reviews").fetchall()],
                "skill_review_events": [dict(row) for row in conn.execute("SELECT * FROM skill_review_events").fetchall()],
                "api_keys": [dict(row) for row in conn.execute("SELECT * FROM api_keys").fetchall()],
                "billing_transactions": [dict(row) for row in conn.execute("SELECT * FROM billing_transactions").fetchall()],
                "daily_visits": [dict(row) for row in conn.execute("SELECT * FROM daily_visits").fetchall()],
            }
        self.state_store.save_snapshot(snapshot)

    def _auth_state_supported(self):
        return hasattr(self.state_store, "load_auth_state") and hasattr(self.state_store, "save_auth_state")

    def _current_auth_state(self):
        with self.lock, self.connect() as conn:
            return {
                "users": [dict(row) for row in conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()],
                "sessions": [dict(row) for row in conn.execute("SELECT * FROM sessions ORDER BY token ASC").fetchall()],
                "verifications": [dict(row) for row in conn.execute("SELECT * FROM email_verifications ORDER BY email ASC").fetchall()],
            }

    def _save_auth_state(self):
        if not self._auth_state_supported():
            self._save_snapshot()
            return
        self.state_store.save_auth_state(self._current_auth_state())

    def _business_state_supported(self):
        required = ["upsert_skill", "delete_skill", "insert_review", "insert_skill_review_event", "increment_daily_visit"]
        return all(hasattr(self.state_store, name) for name in required)

    def _persist_skill_state(self, skill):
        if self._business_state_supported():
            self.state_store.upsert_skill(skill)
            return
        self._save_snapshot()

    def _delete_persisted_skill_state(self, skill_id):
        if self._business_state_supported():
            self.state_store.delete_skill(skill_id)
            return
        self._save_snapshot()

    def _persist_review_state(self, review):
        if self._business_state_supported():
            self.state_store.insert_review(review)
            return
        self._save_snapshot()

    def _persist_skill_review_event_state(self, event):
        if self._business_state_supported():
            self.state_store.insert_skill_review_event(event)
            return
        self._save_snapshot()

    def _persist_visit_state(self, metric_date, anonymous=False):
        if self._business_state_supported():
            self.state_store.increment_daily_visit(metric_date, anonymous=anonymous)
            return
        self._save_snapshot()

    def _persist_registered_user_state(self, metric_date):
        if hasattr(self.state_store, "increment_registered_user"):
            self.state_store.increment_registered_user(metric_date)
            return
        self._save_snapshot()

    def _rebuild_metric_tables(self):
        with self.lock, self.connect() as conn:
            conn.execute("DELETE FROM metric_totals")
            conn.execute("DELETE FROM metric_daily")

            users = [dict(row) for row in conn.execute("SELECT email, role, created_at FROM users").fetchall()]
            daily_registrations = {}
            registered_users = 0
            for user in users:
                if not self._is_counted_registered_user(user):
                    continue
                registered_users += 1
                metric_date = safe_text(user.get("created_at"))[:10]
                if metric_date:
                    daily_registrations[metric_date] = daily_registrations.get(metric_date, 0) + 1

            visit_rows = conn.execute(
                "SELECT metric_date, visit_count, anonymous_visit_count FROM daily_visits ORDER BY metric_date ASC"
            ).fetchall()
            total_visits = 0
            total_anonymous_visits = 0
            daily_metrics = {}
            for row in visit_rows:
                metric_date = safe_text(row["metric_date"])[:10]
                if not metric_date:
                    continue
                visit_count = int(row["visit_count"] or 0)
                anonymous_visit_count = int(row["anonymous_visit_count"] or 0)
                total_visits += visit_count
                total_anonymous_visits += anonymous_visit_count
                daily_metrics[metric_date] = {
                    "visits": visit_count,
                    "anonymousVisits": anonymous_visit_count,
                }

            for metric_date, registration_count in daily_registrations.items():
                visit_counts = daily_metrics.get(metric_date, {"visits": 0, "anonymousVisits": 0})
                conn.execute(
                    """
                    INSERT INTO metric_daily (metric_date, registered_users, visits, anonymous_visits)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        metric_date,
                        registration_count,
                        int(visit_counts["visits"]),
                        int(visit_counts["anonymousVisits"]),
                    ),
                )

            for metric_date, visit_counts in daily_metrics.items():
                if metric_date in daily_registrations:
                    continue
                conn.execute(
                    """
                    INSERT INTO metric_daily (metric_date, registered_users, visits, anonymous_visits)
                    VALUES (?, 0, ?, ?)
                    """,
                    (
                        metric_date,
                        int(visit_counts["visits"]),
                        int(visit_counts["anonymousVisits"]),
                    ),
                )

            conn.executemany(
                "INSERT INTO metric_totals (metric_key, metric_value) VALUES (?, ?)",
                [
                    ("registered_users", registered_users),
                    ("visits", total_visits),
                    ("anonymous_visits", total_anonymous_visits),
                ],
            )
            conn.commit()

    def _persist_api_key_state(self, api_key):
        if hasattr(self.state_store, "upsert_api_key"):
            self.state_store.upsert_api_key(api_key)
            return
        self._save_snapshot()

    def _invalidate_dashboard_cache(self):
        self._dashboard_cache = None
        if hasattr(self.state_store, "invalidate_public_dashboard_cache"):
            self.state_store.invalidate_public_dashboard_cache()

    def _persist_auth_session(self, token, user_id, created_at):
        if self._auth_state_supported() and hasattr(self.state_store, "upsert_auth_session"):
            self.state_store.upsert_auth_session(
                {"token": token, "user_id": user_id, "created_at": created_at}
            )
            return
        self._save_auth_state()

    def _persist_auth_user(self, user):
        if self._auth_state_supported() and hasattr(self.state_store, "upsert_auth_user"):
            self.state_store.upsert_auth_user(user)
            return
        self._save_auth_state()

    def _remove_auth_session(self, token):
        if self._auth_state_supported() and hasattr(self.state_store, "delete_auth_session"):
            self.state_store.delete_auth_session(token)
            return
        self._save_auth_state()

    def _load_or_initialize_auth_state(self):
        if not self._auth_state_supported():
            return
        auth_state = self.state_store.load_auth_state() or {}
        users = auth_state.get("users", [])
        sessions = auth_state.get("sessions", [])
        verifications = auth_state.get("verifications", [])
        if not users:
            self._save_auth_state()
            log.info("Initialized persistent auth state from current in-memory state.")
            return
        with self.lock, self.connect() as conn:
            conn.execute("DELETE FROM email_verifications")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM users")
            for row in users:
                conn.execute(
                    "INSERT INTO users (id, email, password, name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row["id"], row["email"], row["password"], row["name"], row["role"], row.get("created_at", "2026-01-01T00:00:00Z")),
                )
            for row in sessions:
                conn.execute(
                    "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                    (row["token"], row["user_id"], row["created_at"]),
                )
            for row in verifications:
                conn.execute(
                    "INSERT INTO email_verifications (email, code, expires_at, created_at) VALUES (?, ?, ?, ?)",
                    (row["email"], row["code"], row["expires_at"], row["created_at"]),
                )
            conn.commit()
        log.info("Loaded auth state from dedicated auth store. users=%s sessions=%s verifications=%s", len(users), len(sessions), len(verifications))

    def _load_auth_only_state(self):
        if not self._auth_state_supported():
            self._load_snapshot_or_seed()
            return
        auth_state = self.state_store.load_auth_state() or {}
        users = auth_state.get("users", [])
        sessions = auth_state.get("sessions", [])
        verifications = auth_state.get("verifications", [])
        if not users:
            snapshot = self.state_store.load_snapshot() or {}
            users = snapshot.get("users", [])
            sessions = snapshot.get("sessions", [])
        with self.lock, self.connect() as conn:
            conn.execute("DELETE FROM email_verifications")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM users")
            if users:
                for row in users:
                    conn.execute(
                        "INSERT INTO users (id, email, password, name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (row["id"], row["email"], row["password"], row["name"], row["role"], row.get("created_at", "2026-01-01T00:00:00Z")),
                    )
                for row in sessions:
                    conn.execute(
                        "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                        (row["token"], row["user_id"], row["created_at"]),
                    )
                for row in verifications:
                    conn.execute(
                        "INSERT INTO email_verifications (email, code, expires_at, created_at) VALUES (?, ?, ?, ?)",
                        (row["email"], row["code"], row["expires_at"], row["created_at"]),
                    )
            else:
                self._seed_default_users(conn)
            conn.commit()
        log.info("Initialized auth-only runtime. users=%s sessions=%s verifications=%s", len(users) or 3, len(sessions), len(verifications))

    def _sync_user_from_auth_state(self, user_id: str):
        if not self._auth_state_supported():
            return None
        auth_state = self.state_store.load_auth_state() or {}
        for row in auth_state.get("users", []):
            if row.get("id") != user_id:
                continue
            with self.lock, self.connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO users (id, email, password, name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row["id"], row["email"], row["password"], row["name"], row["role"], row.get("created_at", "2026-01-01T00:00:00Z")),
                )
                conn.commit()
            return row
        return None

    def read_skill_seed_file(self):
        with self.skill_data_file.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        skills = []
        for item in data:
            skill = dict(item)
            skill.setdefault("source", "public-registry")
            skill.setdefault("sourceUrl", "")
            skill.setdefault("sourceAuthor", "")
            skill.setdefault("license", "Unknown")
            skill.setdefault("operatingSystem", "")
            skill.setdefault("submittedAt", "2026-01-01T00:00:00Z")
            skill.setdefault("reviewedAt", None)
            skill.setdefault("reviewedBy", "")
            skill.setdefault("reviewResult", skill.get("approvalStatus", "APPROVED"))
            skills.append(skill)
        return skills

    def imported_skill_count(self):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM skills WHERE LOWER(submitted_by) = 'glama-import'"
            ).fetchone()
            return row["count"]

    def replace_imported_skills(self, imported_skills):
        with self.lock, self.connect() as conn:
            imported_ids = [
                row["id"]
                for row in conn.execute(
                    "SELECT id FROM skills WHERE LOWER(submitted_by) = 'glama-import'"
                ).fetchall()
            ]
            if imported_ids:
                for skill_id in imported_ids:
                    conn.execute("DELETE FROM reviews WHERE skill_id = ?", (skill_id,))
                    conn.execute("DELETE FROM skill_review_events WHERE skill_id = ?", (skill_id,))
                    conn.execute("DELETE FROM skill_functions WHERE skill_id = ?", (skill_id,))
                    conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
            self._insert_skills(conn, imported_skills)
            conn.commit()
        self._save_catalog_state()
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.info(
            "Replaced imported skill catalog. removed=%s added=%s",
            len(imported_ids),
            len(imported_skills),
        )

    def _insert_skills(self, conn, skills):
        for skill in skills:
            self._insert_skill(conn, skill)

    def _insert_skill(self, conn, skill):
        conn.execute(
            """
            INSERT OR REPLACE INTO skills (
                id, name, category, description, price_per_call, status, success_rate,
                latency_p95, cost_efficiency, user_rating_avg, user_rating_count, recent_calls,
                invocation_method, submitted_by, approval_status, submitted_at, reviewed_at, reviewed_by, review_result, source, source_url,
                source_author, license, operating_system
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                skill["id"],
                skill["name"],
                skill["category"],
                skill["description"],
                float(skill["pricePerCall"]),
                skill["status"],
                int(skill["successRate"]),
                int(skill["latencyP95"]),
                int(skill["costEfficiency"]),
                float(skill["userRatingAvg"]),
                int(skill["userRatingCount"]),
                int(skill["recentCalls"]),
                skill["invocationMethod"],
                skill["submittedBy"],
                skill["approvalStatus"],
                skill.get("submittedAt", "2026-01-01T00:00:00Z"),
                skill.get("reviewedAt"),
                skill.get("reviewedBy", ""),
                skill.get("reviewResult", skill["approvalStatus"]),
                skill.get("source", "manual"),
                skill.get("sourceUrl", ""),
                skill.get("sourceAuthor", ""),
                skill.get("license", "Unknown"),
                skill.get("operatingSystem", ""),
            ),
        )
        conn.execute("DELETE FROM skill_functions WHERE skill_id = ?", (skill["id"],))
        for index, function_name in enumerate(skill.get("functions", [])):
            conn.execute(
                "INSERT INTO skill_functions (skill_id, function_order, function_name) VALUES (?, ?, ?)",
                (skill["id"], index, function_name),
            )

    def auth_user_id(self, authorization: str):
        token = self.extract_bearer_token(authorization)
        token_user_id = self._verify_auth_token(token)
        if token_user_id:
            return token_user_id
        with self.connect() as conn:
            row = conn.execute("SELECT user_id FROM sessions WHERE token = ?", (token,)).fetchone()
        if row is None:
            raise ApiError(401, "Session expired. Please sign in again.")
        return row["user_id"]

    def require_user(self, user_id: str):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            synced = self._sync_user_from_auth_state(user_id)
            if synced is not None:
                return synced
            raise ApiError(404, f"User not found: {user_id}")
        return dict(row)

    def require_admin(self, authorization: str):
        user = self.require_user(self.auth_user_id(authorization))
        if user["role"].upper() != "ADMIN":
            raise ApiError(403, "Admin permission required.")
        return user

    def extract_bearer_token(self, authorization: str):
        if not authorization:
            raise ApiError(401, "Please sign in first.")
        if not authorization.lower().startswith("bearer "):
            raise ApiError(401, "Unsupported authorization format.")
        token = authorization[7:].strip()
        if not token:
            raise ApiError(401, "Missing bearer token.")
        return token

    def _auth_secret(self):
        secret = (
            os.getenv("NEXRA_AUTH_SECRET")
            or os.getenv("JWT_SECRET")
            or os.getenv("MYSQL_URL")
            or os.getenv("MYSQL_HOST")
            or os.getenv("POSTGRES_URL")
            or os.getenv("DATABASE_URL")
            or "nexra-dev-secret"
        )
        return secret.encode("utf-8")

    def _issue_auth_token(self, user_id: str):
        payload = {"user_id": user_id, "iat": now_iso()}
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        encoded = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
        signature = hmac.new(self._auth_secret(), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"nexra_{encoded}.{signature}"

    def _verify_auth_token(self, token: str):
        if not token.startswith("nexra_") or "." not in token:
            return None
        encoded, signature = token[6:].split(".", 1)
        expected = hmac.new(self._auth_secret(), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        try:
            padding = "=" * (-len(encoded) % 4)
            payload = json.loads(base64.urlsafe_b64decode(encoded + padding).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None
        return safe_text(payload.get("user_id")).strip() or None

    def _generate_verification_code(self):
        return f"{random.randint(0, 999999):06d}"

    def _parse_iso_datetime(self, value: str):
        normalized = safe_text(value).strip()
        if not normalized:
            return None
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    def _store_email_verification(self, email: str, code: str):
        created_at = now_iso()
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        with self.lock, self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO email_verifications (email, code, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (email, code, expires_at, created_at),
            )
            conn.commit()
        verification = {"email": email, "code": code, "expires_at": expires_at, "created_at": created_at}
        if self._auth_state_supported() and hasattr(self.state_store, "upsert_email_verification"):
            self.state_store.upsert_email_verification(verification)
        else:
            self._save_auth_state()
        return verification

    def _load_email_verification(self, email: str):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT email, code, expires_at, created_at FROM email_verifications WHERE email = ?",
                (email,),
            ).fetchone()
        return dict(row) if row else None

    def _delete_email_verification(self, email: str):
        with self.lock, self.connect() as conn:
            conn.execute("DELETE FROM email_verifications WHERE email = ?", (email,))
            conn.commit()
        if self._auth_state_supported() and hasattr(self.state_store, "delete_email_verification"):
            self.state_store.delete_email_verification(email)
        else:
            self._save_auth_state()

    def request_register_code(self, payload):
        email = safe_text(payload.get("email")).strip().lower()
        language = safe_text(payload.get("language")).strip().lower() or "en"
        if not email:
            raise ApiError(400, "Invalid request: email is required.")
        if "@" not in email:
            raise ApiError(400, "Invalid request: email format is invalid.")
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                raise ApiError(400, "This email is already registered.")
        if not self.email_service.is_configured():
            raise ApiError(503, "Email verification is not configured yet.")
        code = self._generate_verification_code()
        self._store_email_verification(email, code)
        try:
            self.email_service.send_verification_code(email, code, language)
        except Exception as exc:
            self._delete_email_verification(email)
            log.exception("Registration verification email delivery failed. email=%s", email)
            raise ApiError(502, f"Verification email delivery failed: {exc}") from exc
        log.info("Registration verification code issued. email=%s", email)
        return {"message": "Verification code sent."}

    def login(self, payload):
        email = safe_text(payload.get("email")).strip().lower()
        password = safe_text(payload.get("password"))
        if not email or not password:
            raise ApiError(400, "Invalid request: missing email or password.")
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if row is None:
                log.warning("Login failed due to unknown email. email=%s", email)
                raise ApiError(401, "Invalid email or password.")
            if row["password"] != password:
                log.warning("Login failed due to invalid password. email=%s", email)
                raise ApiError(401, "Invalid email or password.")
            token = self._issue_auth_token(row["id"])
        log.info("User logged in. userId=%s, email=%s, role=%s", row["id"], row["email"], row["role"])
        return {"token": token, "user": self._user_response(dict(row))}

    def register(self, payload):
        name = safe_text(payload.get("name")).strip()
        email = safe_text(payload.get("email")).strip().lower()
        password = safe_text(payload.get("password"))
        verification_code = safe_text(payload.get("verificationCode")).strip()
        if not email:
            raise ApiError(400, "Invalid request: email is required.")
        if not password:
            raise ApiError(400, "Invalid request: password is required.")
        if len(password) < 6:
            raise ApiError(400, "Invalid request: password must be at least 6 characters.")
        if not verification_code:
            raise ApiError(400, "Invalid request: verification code is required.")
        if not name:
            local_part = email.split("@", 1)[0].strip()
            name = local_part or "Nexra User"
        verification = self._load_email_verification(email)
        if verification is None:
            raise ApiError(400, "Please request an email verification code first.")
        expires_at = self._parse_iso_datetime(verification.get("expires_at"))
        if expires_at is None or expires_at < datetime.utcnow():
            self._delete_email_verification(email)
            raise ApiError(400, "Verification code expired. Please request a new one.")
        if verification.get("code") != verification_code:
            raise ApiError(400, "Verification code is invalid.")
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                log.warning("Registration rejected for duplicate email. email=%s", email)
                raise ApiError(400, "This email is already registered.")
            user_id = "user_" + uuid.uuid4().hex[:8]
            created_at = now_iso()
            conn.execute(
                "INSERT INTO users (id, email, password, name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, email, password, name, "USER", created_at),
            )
            metric_date = created_at[:10]
            conn.execute(
                """
                INSERT INTO metric_totals (metric_key, metric_value)
                VALUES ('registered_users', 1)
                ON CONFLICT(metric_key) DO UPDATE SET metric_value = metric_value + 1
                """
            )
            conn.execute(
                """
                INSERT INTO metric_daily (metric_date, registered_users, visits, anonymous_visits)
                VALUES (?, 1, 0, 0)
                ON CONFLICT(metric_date) DO UPDATE SET registered_users = registered_users + 1
                """,
                (metric_date,),
            )
            conn.commit()
            self._persist_auth_user(
                {"id": user_id, "email": email, "password": password, "name": name, "role": "USER", "created_at": created_at}
            )
            token = self._issue_auth_token(user_id)
        self._persist_registered_user_state(metric_date)
        self._delete_email_verification(email)
        log.info("User registered. userId=%s, email=%s", user_id, email)
        return {"token": token, "user": self._user_response({"id": user_id, "name": name, "email": email, "role": "USER", "created_at": created_at})}

    def logout(self, authorization):
        token = self.extract_bearer_token(authorization)
        token_user_id = self._verify_auth_token(token)
        if token_user_id:
            log.info("User logged out. userId=%s", token_user_id)
            return {"message": "Logged out."}
        with self.connect() as conn:
            row = conn.execute("SELECT user_id FROM sessions WHERE token = ?", (token,)).fetchone()
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            self._remove_auth_session(token)
        if row:
            log.info("User logged out. userId=%s", row["user_id"])
        return {"message": "Logged out."}

    def get_dashboard(self):
        now_ts = datetime.utcnow().timestamp()
        if self._dashboard_cache and (now_ts - self._dashboard_cache["timestamp"]) < self._dashboard_cache_ttl_seconds:
            return self._dashboard_cache["payload"]
        skills = self._fetch_all_skills()
        approved = [skill for skill in skills if skill["status"].lower() == "active" and skill["approvalStatus"].upper() == "APPROVED"]
        pending = [skill for skill in skills if skill["approvalStatus"].upper() == "PENDING"]
        trust_values = [self.overall_trust(skill) for skill in skills if self.overall_trust(skill) is not None]
        recommendation_values = [self.recommendation_score(skill, "", "") for skill in skills]
        top_skills = [
            self._skill_response(skill, "", "")
            for skill in sorted(approved, key=lambda item: self.recommendation_score(item, "", ""), reverse=True)[:3]
        ]
        searchable_functions = len({function_name for skill in skills for function_name in skill["functions"]})
        payload = {
            "totalIndexedSkills": len(skills),
            "approvedSkills": len(approved),
            "pendingSkills": len(pending),
            "averageTrust": round(sum(trust_values) / max(len(trust_values), 1)),
            "averageRecommendation": round(sum(recommendation_values) / max(len(recommendation_values), 1)),
            "searchableFunctions": searchable_functions,
            "popularSkills": len([skill for skill in skills if skill["recentCalls"] >= 10000]),
            "averageSuccessRate": round(sum(skill["successRate"] for skill in skills) / max(len(skills), 1)),
            "averageLatencyP95": round(sum(skill["latencyP95"] for skill in skills) / max(len(skills), 1)),
            "averageCostEfficiency": round(sum(skill["costEfficiency"] for skill in skills) / max(len(skills), 1)),
            "topSkills": top_skills,
        }
        self._dashboard_cache = {"timestamp": now_ts, "payload": payload}
        return payload

    def record_visit(self, authorization=None):
        metric_date = datetime.utcnow().date().isoformat()
        anonymous = True
        if authorization:
            try:
                self.auth_user_id(authorization)
                anonymous = False
            except ApiError:
                anonymous = True
        with self.lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO daily_visits (metric_date, visit_count, anonymous_visit_count)
                VALUES (?, 1, ?)
                ON CONFLICT(metric_date) DO UPDATE SET
                    visit_count = visit_count + 1,
                    anonymous_visit_count = anonymous_visit_count + excluded.anonymous_visit_count
                """,
                (metric_date, 1 if anonymous else 0),
            )
            conn.execute(
                """
                INSERT INTO metric_totals (metric_key, metric_value)
                VALUES ('visits', 1)
                ON CONFLICT(metric_key) DO UPDATE SET metric_value = metric_value + 1
                """
            )
            if anonymous:
                conn.execute(
                    """
                    INSERT INTO metric_totals (metric_key, metric_value)
                    VALUES ('anonymous_visits', 1)
                    ON CONFLICT(metric_key) DO UPDATE SET metric_value = metric_value + 1
                    """
                )
            conn.execute(
                """
                INSERT INTO metric_daily (metric_date, registered_users, visits, anonymous_visits)
                VALUES (?, 0, 1, ?)
                ON CONFLICT(metric_date) DO UPDATE SET
                    visits = visits + 1,
                    anonymous_visits = anonymous_visits + excluded.anonymous_visits
                """,
                (metric_date, 1 if anonymous else 0),
            )
            conn.commit()
        self._persist_visit_state(metric_date, anonymous=anonymous)
        log.info("Platform visit recorded. metricDate=%s anonymous=%s", metric_date, anonymous)
        return {"message": "Visit recorded.", "date": metric_date, "anonymous": anonymous}

    def _auth_users_for_metrics(self):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()]

    def _is_counted_registered_user(self, user):
        email = safe_text(user.get("email")).strip().lower()
        role = safe_text(user.get("role")).strip().upper()
        return role == "USER" and not email.endswith("@nexra.local")

    def get_admin_metrics(self, authorization, days=7, page=0):
        self.require_admin(authorization)
        if hasattr(self.state_store, "get_catalog_metrics"):
            return self.state_store.get_catalog_metrics(days, page)
        page_size = min(max(int(days or 7), 1), 7)
        safe_page = max(int(page or 0), 0)
        with self.connect() as conn:
            total_rows = conn.execute(
                "SELECT metric_key, metric_value FROM metric_totals ORDER BY metric_key ASC"
            ).fetchall()
            totals = {row["metric_key"]: int(row["metric_value"] or 0) for row in total_rows}
            total_items = int(
                conn.execute("SELECT COUNT(*) AS count FROM metric_daily").fetchone()["count"] or 1
            )
            total_pages = max(math.ceil(total_items / page_size), 1)
            safe_page = min(safe_page, total_pages - 1)
            rows = conn.execute(
                """
                SELECT metric_date, registered_users, visits, anonymous_visits
                FROM metric_daily
                ORDER BY metric_date DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, safe_page * page_size),
            ).fetchall()
        series = [
            {
                "date": row["metric_date"],
                "registrations": int(row["registered_users"] or 0),
                "visits": int(row["visits"] or 0),
                "anonymousVisits": int(row["anonymous_visits"] or 0),
            }
            for row in rows
        ]

        return {
            "totals": {
                "registeredUsers": int(totals.get("registered_users", 0)),
                "visits": int(totals.get("visits", 0)),
                "anonymousVisits": int(totals.get("anonymous_visits", 0)),
            },
            "daily": series,
            "days": page_size,
            "page": safe_page,
            "pageSize": page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
        }

    def get_welcome(self, frontend_origin=None, api_base_url=None):
        frontend_url = frontend_origin or "http://127.0.0.1:4173"
        agent_guide_url = f"{(api_base_url or 'http://localhost:8080/api').rstrip('/')}/agent-guide"
        return {
            "productName": "Nexra",
            "headline": "Find the right skill before your agent calls it",
            "summary": "Nexra helps your agent search, compare, and evaluate external skills with trust signals, recommendation scores, and clear calling guidance.",
            "steps": [
                "Search the marketplace by keyword or capability.",
                "Compare recommendation score, trust score, price, and calling method.",
                "Open a skill detail page to read provider docs and calling notes.",
                "Let your own agent call the external skill directly and come back to Nexra for feedback.",
            ],
            "capabilities": [
                "Search and recommendation for agent-ready skills",
                "Dual scoring with user rating and system rating",
                "Moderation, governance, and calling guidance in one place",
            ],
            "frontendUrl": frontend_url,
            "agentGuideUrl": agent_guide_url,
        }

    def get_agent_guide(self, frontend_origin=None, api_base_url=None):
        api_base = (api_base_url or "http://localhost:8080/api").rstrip("/")
        return {
            "name": "Nexra Agent Guide",
            "goal": "Help any AI agent discover, choose, and call external skills correctly.",
            "invokeEndpoint": "/api/skills and /api/skills/{id}",
            "workflow": [
                "Fetch available skills from GET /api/skills.",
                "Compare recommendationScore, overallTrust, userRatingAvg, systemScore, and pricePerCall.",
                "Select the best skill for the task and read its provider docs.",
                "Use GET /api/skills/{id} for deeper trust, calling notes, and review context.",
                "Call the chosen skill directly from your own agent runtime.",
                "After a human sees the result, submit feedback to POST /api/skills/{id}/reviews.",
            ],
            "rules": [
                "Prefer higher recommendationScore when the capability match is strong.",
                "Use overallTrust as a blended quality signal.",
                "Use userRatingAvg to estimate human satisfaction.",
                "Use systemScore to estimate operational reliability.",
                "Treat provider documentation as the source of truth for external invocation details.",
            ],
            "exampleCall": {
                "method": "GET",
                "endpoint": f"{api_base}/skills?q=image&function=ocr&page=0&pageSize=5",
                "contentType": "application/json",
                "payload": "{\"note\":\"Choose a skill from the search results, then call the provider directly.\"}",
            },
        }

    def search_skills(
        self,
        query,
        function_name,
        readiness,
        hide_templates,
        page,
        page_size,
        include_pending=False,
        sort_by="score",
    ):
        safe_page = max(page, 0)
        safe_page_size = max(min(page_size, 10), 1)
        skills = self._fetch_all_skills()
        filtered = []
        fallback_candidates = []
        minimum_match = self.minimum_match_threshold(query, function_name)
        for skill in skills:
            if not include_pending and (skill["approvalStatus"].upper() != "APPROVED" or skill["status"].lower() != "active"):
                continue
            if not self.matches_query(skill, query, function_name, minimum_match):
                continue
            if not self.matches_function(skill, function_name):
                continue
            if not self.matches_readiness(skill, readiness, hide_templates):
                continue
            match_score = self.match_score(skill, query, function_name)
            if self.has_search_terms(query, function_name) and match_score < minimum_match:
                fallback_candidates.append(skill)
                continue
            filtered.append(skill)
        if not filtered and fallback_candidates:
            fallback_threshold = max(minimum_match - 12, 8)
            filtered = [
                skill
                for skill in fallback_candidates
                if self.match_score(skill, query, function_name) >= fallback_threshold
            ]
        normalized_sort = self.normalize_sort_by(sort_by)
        filtered.sort(
            key=lambda item: self.skill_sort_key(item, query, function_name, normalized_sort),
            reverse=True,
        )
        start = min(safe_page * safe_page_size, len(filtered))
        end = min(start + safe_page_size, len(filtered))
        total_pages = 0 if not filtered else math.ceil(len(filtered) / safe_page_size)
        log.info(
            "Skill search executed. query='%s', function='%s', readiness='%s', hideTemplates=%s, includePending=%s, page=%s, pageSize=%s, sortBy=%s, minMatch=%s, totalItems=%s",
            safe_text(query),
            safe_text(function_name),
            safe_text(readiness),
            hide_templates,
            include_pending,
            safe_page,
            safe_page_size,
            normalized_sort,
            minimum_match,
            len(filtered),
        )
        return {
            "items": [self._skill_response(skill, query, function_name) for skill in filtered[start:end]],
            "page": safe_page,
            "pageSize": safe_page_size,
            "totalItems": len(filtered),
            "totalPages": total_pages,
            "sortBy": normalized_sort,
        }

    def get_skill_detail(self, skill_id):
        skill = self._find_skill(skill_id)
        with self.connect() as conn:
            reviews = conn.execute(
                "SELECT * FROM reviews WHERE skill_id = ? ORDER BY timestamp DESC", (skill_id,)
            ).fetchall()
        return {
            "skill": self._skill_response(skill, "", ""),
            "reviews": [self._review_response(dict(review)) for review in reviews],
        }

    def add_review(self, authorization, skill_id, payload):
        user_id = self.auth_user_id(authorization)
        user = self.require_user(user_id)
        skill = self._find_skill(skill_id)
        rating = int(payload.get("rating", 0))
        if rating < 1 or rating > 5:
            raise ApiError(400, "Invalid request: rating must be between 1 and 5.")
        comment = safe_text(payload.get("comment")).strip() or "No written feedback left."
        review_id = "rev_" + uuid.uuid4().hex[:8]
        timestamp = datetime.now().date().isoformat()
        new_count = skill["userRatingCount"] + 1
        new_avg = ((skill["userRatingAvg"] * skill["userRatingCount"]) + rating) / new_count
        review = {
            "id": review_id,
            "skill_id": skill_id,
            "user_id": user_id,
            "author": user["name"],
            "rating": rating,
            "comment": comment,
            "timestamp": timestamp,
        }
        with self.lock, self.connect() as conn:
            conn.execute(
                "INSERT INTO reviews (id, skill_id, user_id, author, rating, comment, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (review_id, skill_id, user_id, user["name"], rating, comment, timestamp),
            )
            conn.execute(
                "UPDATE skills SET user_rating_avg = ?, user_rating_count = ? WHERE id = ?",
                (new_avg, new_count, skill_id),
            )
            conn.commit()
        updated_skill = {
            **skill,
            "userRatingAvg": new_avg,
            "userRatingCount": new_count,
        }
        self._persist_review_state(review)
        self._persist_skill_state(updated_skill)
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.info(
            "Review submitted. skillId=%s, userId=%s, rating=%s, newUserRatingAvg=%s, newUserRatingCount=%s",
            skill_id,
            user_id,
            rating,
            round(new_avg, 3),
            new_count,
        )
        return {
            "id": review_id,
            "skillId": skill_id,
            "author": user["name"],
            "rating": rating,
            "comment": comment,
            "timestamp": timestamp,
        }

    def submit_skill(self, authorization, payload):
        user_id = self.auth_user_id(authorization)
        user = self.require_user(user_id)
        skill_id = "skill-" + uuid.uuid4().hex[:8]
        submitted_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        skill = {
            "id": skill_id,
            "name": safe_text(payload.get("name")).strip(),
            "category": safe_text(payload.get("category")).strip(),
            "description": safe_text(payload.get("description")).strip(),
            "pricePerCall": float(payload.get("pricePerCall", 0)),
            "status": "draft",
            "successRate": int(payload.get("successRate", 0)),
            "latencyP95": int(payload.get("latencyP95", 0)),
            "costEfficiency": int(payload.get("costEfficiency", 0)),
            "userRatingAvg": 0.0,
            "userRatingCount": 0,
            "recentCalls": int(payload.get("recentCalls", 0)),
            "functions": self.sanitize_list(payload.get("functions", [])),
            "invocationMethod": safe_text(payload.get("invocationMethod")).strip(),
            "submittedBy": user_id,
            "approvalStatus": "PENDING",
            "submittedAt": submitted_at,
            "reviewedAt": None,
            "reviewedBy": "",
            "reviewResult": "PENDING",
            "source": self.default_text(payload.get("source"), "manual"),
            "sourceUrl": self.default_text(payload.get("sourceUrl"), ""),
            "sourceAuthor": self.default_text(payload.get("sourceAuthor"), user["name"]),
            "license": self.default_text(payload.get("license"), "Unknown"),
            "operatingSystem": self.default_text(payload.get("operatingSystem"), "Cloud / API"),
        }
        if not skill["name"] or not skill["category"] or not skill["description"] or not skill["functions"] or not skill["invocationMethod"]:
            raise ApiError(400, "Invalid request: skill submission fields are incomplete.")
        with self.lock, self.connect() as conn:
            self._insert_skill(conn, skill)
            conn.commit()
        self._persist_skill_state(skill)
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.info(
            "Skill submitted. skillId=%s, submittedBy=%s, category=%s, approvalStatus=%s",
            skill_id,
            user_id,
            skill["category"],
            skill["approvalStatus"],
        )
        return self._skill_response(skill, "", "")

    def update_submitted_skill(self, authorization, skill_id, payload):
        user_id = self.auth_user_id(authorization)
        user = self.require_user(user_id)
        skill = self._find_skill(skill_id)
        if skill["submittedBy"] != user_id:
            raise ApiError(403, "You can only edit skills that you submitted.")
        updated = {
            **skill,
            "name": safe_text(payload.get("name")).strip(),
            "category": safe_text(payload.get("category")).strip(),
            "description": safe_text(payload.get("description")).strip(),
            "pricePerCall": float(payload.get("pricePerCall", skill["pricePerCall"])),
            "functions": self.sanitize_list(payload.get("functions", skill["functions"])),
            "invocationMethod": safe_text(payload.get("invocationMethod")).strip(),
            "source": self.default_text(payload.get("source"), skill["source"]),
            "sourceUrl": self.default_text(payload.get("sourceUrl"), skill["sourceUrl"]),
            "sourceAuthor": self.default_text(payload.get("sourceAuthor"), user["name"]),
            "license": self.default_text(payload.get("license"), skill["license"]),
            "operatingSystem": self.default_text(payload.get("operatingSystem"), skill["operatingSystem"]),
            "approvalStatus": "PENDING",
            "status": "draft",
            "reviewedAt": None,
            "reviewedBy": "",
            "reviewResult": "PENDING",
        }
        if not updated["name"] or not updated["category"] or not updated["description"] or not updated["functions"] or not updated["invocationMethod"]:
            raise ApiError(400, "Invalid request: skill submission fields are incomplete.")
        with self.lock, self.connect() as conn:
            self._insert_skill(conn, updated)
            conn.commit()
        self._persist_skill_state(updated)
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.info(
            "Skill updated by submitter. skillId=%s, userId=%s, approvalStatus=%s",
            skill_id,
            user_id,
            updated["approvalStatus"],
        )
        return self._skill_response(updated, "", "")

    def get_pending_skills(self, authorization):
        self.require_admin(authorization)
        return [
            self._skill_response(skill, "", "")
            for skill in sorted(
                [skill for skill in self._fetch_all_skills() if skill["approvalStatus"].upper() == "PENDING"],
                key=lambda item: safe_text(item.get("submittedAt")) or "9999",
            )
        ]

    def _record_skill_review_event(self, conn, skill_id, reviewer, result, note=""):
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        event = {
            "id": "sre_" + uuid.uuid4().hex[:10],
            "skillId": skill_id,
            "reviewerUserId": reviewer["id"],
            "reviewerName": reviewer["name"],
            "result": result,
            "note": safe_text(note).strip(),
            "timestamp": timestamp,
        }
        conn.execute(
            """
            INSERT INTO skill_review_events (id, skill_id, reviewer_user_id, reviewer_name, result, note, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                skill_id,
                reviewer["id"],
                reviewer["name"],
                result,
                event["note"],
                timestamp,
            ),
        )
        return event

    def _skill_review_history_map(self, conn):
        history = {}
        rows = conn.execute(
            "SELECT * FROM skill_review_events ORDER BY timestamp DESC, id DESC"
        ).fetchall()
        for row in rows:
            entry = {
                "id": row["id"],
                "skillId": row["skill_id"],
                "reviewerUserId": row["reviewer_user_id"],
                "reviewerName": row["reviewer_name"],
                "result": row["result"],
                "note": row["note"],
                "timestamp": row["timestamp"],
            }
            history.setdefault(row["skill_id"], []).append(entry)
        return history

    def get_admin_skills(self, authorization, status="", search="", page=0, page_size=10):
        self.require_admin(authorization)
        with self.connect() as conn:
            history_map = self._skill_review_history_map(conn)
        normalized_status = safe_text(status).strip().upper()
        filtered = []
        for skill in self._fetch_all_skills():
            if normalized_status in {"PENDING", "APPROVED", "REJECTED"} and skill["approvalStatus"].upper() != normalized_status:
                continue
            if safe_text(search).strip() and not self.matches_query(skill, search, "", minimum_match=10):
                search_lower = safe_text(search).strip().lower()
                review_blob = " ".join(
                    [
                        safe_text(skill.get("reviewedBy")),
                        safe_text(skill.get("reviewResult")),
                        safe_text(skill.get("submittedBy")),
                    ]
                ).lower()
                if search_lower not in review_blob:
                    continue
            filtered.append(skill)

        if normalized_status == "PENDING":
            filtered.sort(key=lambda item: (safe_text(item.get("submittedAt")) or "9999", item["name"].lower()))
        else:
            filtered.sort(
                key=lambda item: (
                    safe_text(item.get("reviewedAt")) or "",
                    item["name"].lower(),
                ),
                reverse=True,
            )

        safe_page_size = min(max(int(page_size or 10), 1), 50)
        safe_page = max(int(page or 0), 0)
        total_items = len(filtered)
        total_pages = max(math.ceil(total_items / safe_page_size), 1)
        if safe_page >= total_pages:
            safe_page = max(total_pages - 1, 0)
        start = safe_page * safe_page_size
        end = start + safe_page_size

        items = []
        for skill in filtered[start:end]:
            item = self._skill_response(skill, "", "")
            item["reviewHistory"] = history_map.get(skill["id"], [])
            items.append(item)
        return {
            "items": items,
            "page": safe_page,
            "pageSize": safe_page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
            "status": normalized_status or "ALL",
            "q": safe_text(search).strip(),
        }

    def approve_skill(self, authorization, skill_id):
        admin = self.require_admin(authorization)
        with self.lock, self.connect() as conn:
            row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
            if row is None:
                raise ApiError(404, f"Skill not found: {skill_id}")
            function_rows = conn.execute(
                "SELECT function_name FROM skill_functions WHERE skill_id = ? ORDER BY function_order",
                (skill_id,),
            ).fetchall()
            event = self._record_skill_review_event(conn, skill_id, admin, "APPROVED")
            conn.execute(
                """
                UPDATE skills
                SET approval_status = 'APPROVED', status = 'active', reviewed_at = ?, reviewed_by = ?, review_result = 'APPROVED'
                WHERE id = ?
                """,
                (event["timestamp"], admin["name"], skill_id),
            )
            conn.commit()
        existing_skill = self._skill_from_row(dict(row), [item["function_name"] for item in function_rows])
        updated_skill = {
            **existing_skill,
            "approvalStatus": "APPROVED",
            "status": "active",
            "reviewedAt": event["timestamp"],
            "reviewedBy": admin["name"],
            "reviewResult": "APPROVED",
        }
        if hasattr(self.state_store, "persist_skill_review_event_and_skill"):
            self.state_store.persist_skill_review_event_and_skill(event, updated_skill)
        else:
            self._persist_skill_review_event_state(event)
            self._persist_skill_state(updated_skill)
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.info("Skill approved. skillId=%s, adminUserId=%s", skill_id, admin["id"])
        return self._skill_response(updated_skill, "", "")

    def reject_skill(self, authorization, skill_id):
        admin = self.require_admin(authorization)
        with self.lock, self.connect() as conn:
            row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
            if row is None:
                raise ApiError(404, f"Skill not found: {skill_id}")
            function_rows = conn.execute(
                "SELECT function_name FROM skill_functions WHERE skill_id = ? ORDER BY function_order",
                (skill_id,),
            ).fetchall()
            event = self._record_skill_review_event(conn, skill_id, admin, "REJECTED")
            conn.execute(
                """
                UPDATE skills
                SET approval_status = 'REJECTED', status = 'draft', reviewed_at = ?, reviewed_by = ?, review_result = 'REJECTED'
                WHERE id = ?
                """,
                (event["timestamp"], admin["name"], skill_id),
            )
            conn.commit()
        existing_skill = self._skill_from_row(dict(row), [item["function_name"] for item in function_rows])
        updated_skill = {
            **existing_skill,
            "approvalStatus": "REJECTED",
            "status": "draft",
            "reviewedAt": event["timestamp"],
            "reviewedBy": admin["name"],
            "reviewResult": "REJECTED",
        }
        if hasattr(self.state_store, "persist_skill_review_event_and_skill"):
            self.state_store.persist_skill_review_event_and_skill(event, updated_skill)
        else:
            self._persist_skill_review_event_state(event)
            self._persist_skill_state(updated_skill)
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.info("Skill rejected. skillId=%s, adminUserId=%s", skill_id, admin["id"])
        return self._skill_response(updated_skill, "", "")

    def admin_update_skill(self, authorization, skill_id, payload):
        admin = self.require_admin(authorization)
        skill = self._find_skill(skill_id)
        approval_status = self.normalize_approval_status(payload.get("approvalStatus"), skill["approvalStatus"])
        status = self.normalize_skill_status(payload.get("status"), approval_status, skill["status"])
        updated = {
            **skill,
            "name": safe_text(payload.get("name")).strip(),
            "category": safe_text(payload.get("category")).strip(),
            "description": safe_text(payload.get("description")).strip(),
            "pricePerCall": float(payload.get("pricePerCall", 0)),
            "status": status,
            "successRate": int(payload.get("successRate", 0)),
            "latencyP95": int(payload.get("latencyP95", 0)),
            "costEfficiency": int(payload.get("costEfficiency", 0)),
            "userRatingAvg": float(payload.get("userRatingAvg", 0)),
            "userRatingCount": int(payload.get("userRatingCount", 0)),
            "recentCalls": int(payload.get("recentCalls", 0)),
            "functions": self.sanitize_list(payload.get("functions", [])),
            "invocationMethod": safe_text(payload.get("invocationMethod")).strip(),
            "approvalStatus": approval_status,
            "source": self.default_text(payload.get("source"), skill["source"]),
            "sourceUrl": self.default_text(payload.get("sourceUrl"), skill["sourceUrl"]),
            "sourceAuthor": self.default_text(payload.get("sourceAuthor"), skill["sourceAuthor"]),
            "license": self.default_text(payload.get("license"), skill["license"]),
            "operatingSystem": self.default_text(payload.get("operatingSystem"), skill["operatingSystem"]),
        }
        with self.lock, self.connect() as conn:
            review_event = None
            if updated["approvalStatus"] != skill["approvalStatus"]:
                review_event = self._record_skill_review_event(conn, skill_id, admin, updated["approvalStatus"])
                updated["reviewedAt"] = review_event["timestamp"]
                updated["reviewedBy"] = admin["name"]
                updated["reviewResult"] = updated["approvalStatus"]
            elif updated["status"] != skill["status"] and updated["approvalStatus"] == "APPROVED":
                action = "REPUBLISHED" if updated["status"] == "active" else "UNPUBLISHED"
                review_event = self._record_skill_review_event(conn, skill_id, admin, action)
                updated["reviewedAt"] = review_event["timestamp"]
                updated["reviewedBy"] = admin["name"]
                updated["reviewResult"] = updated["approvalStatus"]
            self._insert_skill(conn, updated)
            conn.commit()
        if review_event and hasattr(self.state_store, "persist_skill_review_event_and_skill"):
            self.state_store.persist_skill_review_event_and_skill(review_event, updated)
        else:
            if review_event:
                self._persist_skill_review_event_state(review_event)
            self._persist_skill_state(updated)
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.info(
            "Skill updated by admin. skillId=%s, adminUserId=%s, approvalStatus=%s, status=%s",
            skill_id,
            admin["id"],
            updated["approvalStatus"],
            updated["status"],
        )
        return self._skill_response(updated, "", "")

    def admin_delete_skill(self, authorization, skill_id):
        admin = self.require_admin(authorization)
        with self.lock, self.connect() as conn:
            conn.execute("DELETE FROM reviews WHERE skill_id = ?", (skill_id,))
            conn.execute("DELETE FROM skill_review_events WHERE skill_id = ?", (skill_id,))
            conn.execute("DELETE FROM skill_functions WHERE skill_id = ?", (skill_id,))
            conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
            conn.commit()
        self._delete_persisted_skill_state(skill_id)
        self._invalidate_skill_cache()
        self._invalidate_dashboard_cache()
        log.warning("Skill deleted by admin. skillId=%s, adminUserId=%s", skill_id, admin["id"])
        return {"message": "Deleted."}

    def get_users(self, authorization):
        self.require_admin(authorization)
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY name ASC").fetchall()
        return [self._user_response(dict(row)) for row in rows]

    def get_user_profile(self, authorization):
        user_id = self.auth_user_id(authorization)
        user = self.require_user(user_id)
        all_skills = self._fetch_all_skills()
        skill_map = {skill["id"]: skill for skill in all_skills}
        submitted_skills = [
            self._skill_response(skill, "", "")
            for skill in sorted(
                [skill for skill in all_skills if skill["submittedBy"] == user_id],
                key=lambda item: self.recommendation_score(item, "", ""),
                reverse=True,
            )
        ]
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM reviews WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)
            ).fetchall()
        submitted_reviews = [
            {
                "id": row["id"],
                "skillId": row["skill_id"],
                "skillName": skill_map.get(row["skill_id"], {}).get("name", row["skill_id"]),
                "rating": row["rating"],
                "comment": row["comment"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
        return {
            "user": self._user_response(user),
            "submittedSkills": submitted_skills,
            "submittedReviews": submitted_reviews,
        }

    def get_billing_summary(self, authorization):
        self.auth_user_id(authorization)
        return {"currentBalance": 2864.92, "spend30d": 212.08, "avgCallPrice": 0.06}

    def get_transactions(self, authorization):
        self.auth_user_id(authorization)
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM billing_transactions ORDER BY timestamp DESC").fetchall()
        return [dict(row) for row in rows]

    def get_api_keys(self, authorization):
        self.auth_user_id(authorization)
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM api_keys").fetchall()
        return [self._api_key_response(dict(row)) for row in rows]

    def create_api_key(self, authorization, payload):
        self.auth_user_id(authorization)
        name = safe_text(payload.get("name")).strip()
        if not name:
            raise ApiError(400, "Invalid request: API key name is required.")
        scope = self.default_text(payload.get("scope"), "skills:read")
        with self.lock, self.connect() as conn:
            count = conn.execute("SELECT COUNT(*) AS count FROM api_keys").fetchone()["count"]
            key = {
                "id": f"nk_live_{count + 1:02d}",
                "name": name,
                "scope": scope,
                "last_used": "Never",
                "status": "active",
            }
            conn.execute(
                "INSERT INTO api_keys (id, name, scope, last_used, status) VALUES (?, ?, ?, ?, ?)",
                (key["id"], key["name"], key["scope"], key["last_used"], key["status"]),
            )
            conn.commit()
        self._persist_api_key_state(key)
        log.info("API key created. name=%s, scope=%s, keyId=%s", key["name"], key["scope"], key["id"])
        return self._api_key_response(key)

    def _load_all_skills_from_db(self):
        with self.connect() as conn:
            rows = [dict(row) for row in conn.execute("SELECT * FROM skills").fetchall()]
            functions_rows = conn.execute(
                "SELECT skill_id, function_order, function_name FROM skill_functions ORDER BY skill_id, function_order"
            ).fetchall()
        functions_map = {}
        for row in functions_rows:
            functions_map.setdefault(row["skill_id"], []).append(row["function_name"])
        skills = []
        for row in rows:
            skills.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "category": row["category"],
                    "description": row["description"],
                    "pricePerCall": row["price_per_call"],
                    "status": row["status"],
                    "successRate": row["success_rate"],
                    "latencyP95": row["latency_p95"],
                    "costEfficiency": row["cost_efficiency"],
                    "userRatingAvg": row["user_rating_avg"],
                    "userRatingCount": row["user_rating_count"],
                    "recentCalls": row["recent_calls"],
                    "functions": functions_map.get(row["id"], []),
                    "invocationMethod": row["invocation_method"],
                    "submittedBy": row["submitted_by"],
                    "approvalStatus": row["approval_status"],
                    "submittedAt": row.get("submitted_at"),
                    "reviewedAt": row.get("reviewed_at"),
                    "reviewedBy": row.get("reviewed_by"),
                    "reviewResult": row.get("review_result"),
                    "source": row["source"],
                    "sourceUrl": row["source_url"],
                    "sourceAuthor": row["source_author"],
                    "license": row["license"],
                    "operatingSystem": row["operating_system"],
                }
            )
        return skills

    def _fetch_all_skills(self):
        if self._skill_cache is None:
            skills = self._load_all_skills_from_db()
            self._skill_cache = skills
            self._skill_cache_by_id = {skill["id"]: skill for skill in skills}
        return [self._copy_skill(skill) for skill in self._skill_cache]

    def _skill_from_row(self, row, functions):
        return {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "description": row["description"],
            "pricePerCall": row["price_per_call"],
            "status": row["status"],
            "successRate": row["success_rate"],
            "latencyP95": row["latency_p95"],
            "costEfficiency": row["cost_efficiency"],
            "userRatingAvg": row["user_rating_avg"],
            "userRatingCount": row["user_rating_count"],
            "recentCalls": row["recent_calls"],
            "functions": functions,
            "invocationMethod": row["invocation_method"],
            "submittedBy": row["submitted_by"],
            "approvalStatus": row["approval_status"],
            "submittedAt": row.get("submitted_at"),
            "reviewedAt": row.get("reviewed_at"),
            "reviewedBy": row.get("reviewed_by"),
            "reviewResult": row.get("review_result"),
            "source": row["source"],
            "sourceUrl": row["source_url"],
            "sourceAuthor": row["source_author"],
            "license": row["license"],
            "operatingSystem": row["operating_system"],
        }

    def _fetch_skill_by_id(self, skill_id):
        skills_by_id = self._skill_cache_by_id
        if skills_by_id is None:
            self._fetch_all_skills()
            skills_by_id = self._skill_cache_by_id or {}
        skill = skills_by_id.get(skill_id)
        if skill is None:
            raise ApiError(404, f"Skill not found: {skill_id}")
        return self._copy_skill(skill)

    def _find_skill(self, skill_id):
        return self._fetch_skill_by_id(skill_id)

    def _user_response(self, user):
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "createdAt": user.get("created_at"),
        }

    def _review_response(self, review):
        return {
            "id": review["id"],
            "skillId": review["skill_id"],
            "author": review["author"],
            "rating": review["rating"],
            "comment": review["comment"],
            "timestamp": review["timestamp"],
        }

    def _api_key_response(self, key):
        return {
            "id": key["id"],
            "name": key["name"],
            "scope": key["scope"],
            "lastUsed": key["last_used"],
            "status": key["status"],
        }

    def sanitize_list(self, values):
        return [safe_text(item).strip() for item in values if safe_text(item).strip()]

    def default_text(self, value, fallback):
        text = safe_text(value).strip()
        return text or fallback

    def expanded_query_terms(self, query):
        normalized = safe_text(query).strip().lower()
        if not normalized:
            return []
        terms = {normalized}
        terms.update(token for token in re.split(r"[^a-z0-9]+", normalized) if token)
        intent = QUERY_INTENT_TERMS.get(normalized)
        if intent:
            terms.update(intent["positive"])
        return [term for term in terms if term]

    def intent_adjustment(self, skill, query):
        normalized = safe_text(query).strip().lower()
        intent = QUERY_INTENT_TERMS.get(normalized)
        if not intent:
            return 0
        searchable = " ".join(
            [
                skill["name"],
                skill["category"],
                skill["description"],
                skill["invocationMethod"],
                " ".join(skill["functions"]),
            ]
        ).lower()
        bonus = 0
        if any(term in searchable for term in intent["positive"]):
            bonus += 18
        if any(term in searchable for term in intent["negative"]):
            bonus -= 20
        generic_markers = ["design context", "project management", "ticket management"]
        if any(marker in searchable for marker in generic_markers) and not any(term in searchable for term in intent["positive"]):
            bonus -= 12
        return bonus

    def normalized_user_rating(self, skill):
        if not self.has_user_rating(skill):
            return None
        return round((float(skill["userRatingAvg"]) / 5.0) * 100)

    def agent_score(self, skill):
        if not self.has_agent_rating(skill):
            return None
        latency_score = clamp(100 - (int(skill["latencyP95"]) - 200) / 10.0, 35, 100)
        return round(int(skill["successRate"]) * 0.5 + latency_score * 0.3 + int(skill["costEfficiency"]) * 0.2)

    def overall_trust(self, skill):
        user_score = self.normalized_user_rating(skill)
        agent_score = self.agent_score(skill)
        if user_score is not None and agent_score is not None:
            return round(user_score * 0.45 + agent_score * 0.55)
        if user_score is not None:
            return round(user_score)
        if agent_score is not None:
            return round(agent_score)
        return None

    def match_score(self, skill, query, function_name):
        no_filters = not safe_text(query).strip() and not safe_text(function_name).strip()
        if no_filters:
            return 70
        score = 0
        normalized_query = safe_text(query).strip().lower()
        normalized_function = safe_text(function_name).strip().lower()
        query_terms = self.expanded_query_terms(query)
        haystack = " ".join(
            [
                skill["name"].lower(),
                skill["category"].lower(),
                skill["description"].lower(),
                skill["invocationMethod"].lower(),
                " ".join(skill["functions"]).lower(),
            ]
        )
        if normalized_query:
            if normalized_query in skill["name"].lower():
                score += 40
            if normalized_query in skill["category"].lower():
                score += 15
            if normalized_query in skill["description"].lower():
                score += 20
            if normalized_query in skill["invocationMethod"].lower():
                score += 10
            if any(normalized_query in item.lower() for item in skill["functions"]):
                score += 15
            for term in query_terms:
                if term in skill["category"].lower():
                    score += 4
                if any(term in item.lower() for item in skill["functions"]):
                    score += 6
                if term in skill["description"].lower():
                    score += 3
        if normalized_function:
            if any(item.lower() == normalized_function for item in skill["functions"]):
                score += 35
            elif any(normalized_function in item.lower() for item in skill["functions"]):
                score += 25
            elif normalized_function in haystack:
                score += 15
        score += self.intent_adjustment(skill, query)
        return int(clamp(score, 0, 100))

    def recommendation_score(self, skill, query, function_name):
        popularity = clamp(math.log10(int(skill["recentCalls"]) + 10) * 20, 20, 100)
        trust = self.overall_trust(skill) or 0
        return round(
            self.match_score(skill, query, function_name) * 0.35
            + trust * 0.35
            + popularity * 0.15
            + int(skill["costEfficiency"]) * 0.10
            + int(skill["successRate"]) * 0.05
        )

    def recommendation_summary(self, skill, query, function_name):
        reasons = []
        if self.match_score(skill, query, function_name) >= 75:
            reasons.append("strong capability match")
        trust = self.overall_trust(skill)
        if trust is not None and trust >= 85:
            reasons.append("high trust")
        if int(skill["recentCalls"]) >= 10000:
            reasons.append("popular in recent usage")
        if int(skill["costEfficiency"]) >= 80:
            reasons.append("good cost efficiency")
        if not reasons:
            reasons.append("balanced trust and coverage")
        return ", ".join(reasons)

    def provider_name(self, skill):
        return safe_text(skill.get("sourceAuthor")).strip() or skill["submittedBy"]

    def provider_url(self, skill):
        return safe_text(skill.get("sourceUrl")).strip()

    def auth_requirement(self, skill):
        invocation = skill["invocationMethod"].lower()
        if "local" in invocation:
            return "Requires local runtime setup. Check provider docs for installation steps."
        if not self.provider_url(skill):
            return "Check the provider before use. Authentication requirements are not documented in Nexra yet."
        return "Review the provider documentation for API key, OAuth, or local runtime requirements before calling."

    def call_example(self, skill):
        function_name = skill["functions"][0] if skill["functions"] else "task"
        return (
            '{ "task": "' + function_name + '", "skill": "' + skill["name"] +
            '", "notes": "Call this provider directly after choosing it in Nexra." }'
        )

    def derive_readiness_code(self, skill):
        text = " ".join(
            [
                safe_text(skill.get("name")),
                safe_text(skill.get("description")),
                safe_text(skill.get("invocationMethod")),
                " ".join(skill.get("functions", [])),
                safe_text(self.provider_name(skill)),
                safe_text(skill.get("category")),
            ]
        ).lower()
        if any(marker in text for marker in ["template", "boilerplate", "starter", "scaffold", "example sdk", "starter project"]):
            return "template"
        if any(marker in text for marker in ["local", "filesystem", "file storage", "ollama", "plugin bridge", "desktop", "install", "self-hosted"]):
            return "local"
        if any(marker in text for marker in ["token", "oauth", "api key", "slack", "mysql", "sql server", "postgres", "database", "figma", "shopify", "jumpseller", "aws", "azure", "gcp"]):
            return "credentials"
        return "ready"

    def has_search_terms(self, query, function_name):
        return bool(safe_text(query).strip() or safe_text(function_name).strip())

    def minimum_match_threshold(self, query, function_name):
        if not self.has_search_terms(query, function_name):
            return 0
        query_text = safe_text(query).strip()
        function_text = safe_text(function_name).strip()
        if query_text and function_text:
            return 30
        query_word_count = len([part for part in re.split(r"\s+", query_text) if part])
        if query_word_count >= 2:
            return 28
        if len(query_text) >= 10:
            return 24
        return 20

    def has_user_rating(self, skill):
        return int(skill.get("userRatingCount", 0) or 0) > 0

    def has_agent_rating(self, skill):
        return any(
            int(skill.get(field, 0) or 0) > 0
            for field in ("successRate", "latencyP95", "costEfficiency", "recentCalls")
        )

    def normalize_approval_status(self, approval_status, default="PENDING"):
        normalized = safe_text(approval_status).strip().upper() or default
        if normalized not in {"PENDING", "APPROVED", "REJECTED"}:
            return default
        return normalized

    def normalize_skill_status(self, status, approval_status="PENDING", default="draft"):
        normalized = safe_text(status).strip().lower() or default
        if normalized not in {"active", "draft", "revoked"}:
            normalized = default
        if approval_status == "APPROVED" and normalized not in {"active", "revoked"}:
            return "active"
        if approval_status == "REJECTED":
            return "draft"
        if approval_status == "PENDING" and normalized == "active":
            return "draft"
        return normalized

    def normalize_sort_by(self, sort_by):
        normalized = safe_text(sort_by).strip().lower()
        if normalized == "relevance":
            return "relevance"
        return "score"

    def skill_sort_key(self, skill, query, function_name, sort_by):
        match = self.match_score(skill, query, function_name)
        recommendation = self.recommendation_score(skill, query, function_name)
        trust = self.overall_trust(skill) if self.overall_trust(skill) is not None else -1
        agent_score = self.agent_score(skill)
        agent = agent_score if agent_score is not None else -1
        rating = float(skill["userRatingAvg"]) if self.has_user_rating(skill) else -1
        calls = int(skill["recentCalls"])
        if sort_by == "relevance":
            return (match, recommendation, trust, agent, calls, rating)
        return (recommendation, trust, match, agent, rating, calls)

    def matches_query(self, skill, query, function_name="", minimum_match=None):
        if not self.has_search_terms(query, function_name):
            return True
        threshold = self.minimum_match_threshold(query, function_name) if minimum_match is None else minimum_match
        return self.match_score(skill, query, function_name) >= threshold

    def matches_function(self, skill, function_name):
        normalized = safe_text(function_name).strip().lower()
        if not normalized:
            return True
        return any(normalized in item.lower() for item in skill["functions"])

    def matches_readiness(self, skill, readiness, hide_templates):
        readiness_code = self.derive_readiness_code(skill)
        if hide_templates and readiness_code == "template":
            return False
        normalized = safe_text(readiness).strip().lower()
        if not normalized or normalized == "all":
            return True
        return readiness_code == normalized

    def _skill_response(self, skill, query, function_name):
        agent_score = self.agent_score(skill)
        normalized_user_rating = self.normalized_user_rating(skill)
        overall_trust = self.overall_trust(skill)
        has_user_rating = self.has_user_rating(skill)
        has_system_rating = self.has_agent_rating(skill)
        return {
            "id": skill["id"],
            "name": skill["name"],
            "category": skill["category"],
            "description": skill["description"],
            "pricePerCall": skill["pricePerCall"],
            "status": skill["status"],
            "successRate": skill["successRate"],
            "latencyP95": skill["latencyP95"],
            "costEfficiency": skill["costEfficiency"],
            "userRatingAvg": skill["userRatingAvg"],
            "userRatingCount": skill["userRatingCount"],
            "recentCalls": skill["recentCalls"],
            "hasUserRating": has_user_rating,
            "hasSystemRating": has_system_rating,
            "agentScore": agent_score,
            "systemScore": agent_score,
            "normalizedUserRating": normalized_user_rating,
            "overallTrust": overall_trust,
            "matchScore": self.match_score(skill, query, function_name),
            "recommendationScore": self.recommendation_score(skill, query, function_name),
            "recommendationSummary": self.recommendation_summary(skill, query, function_name),
            "functions": skill["functions"],
            "invocationMethod": skill["invocationMethod"],
            "submittedBy": skill["submittedBy"],
            "approvalStatus": skill["approvalStatus"],
            "submittedAt": skill.get("submittedAt"),
            "reviewedAt": skill.get("reviewedAt"),
            "reviewedBy": skill.get("reviewedBy"),
            "reviewResult": skill.get("reviewResult"),
            "source": skill["source"],
            "sourceUrl": skill["sourceUrl"],
            "sourceAuthor": skill["sourceAuthor"],
            "license": skill["license"],
            "operatingSystem": skill["operatingSystem"],
            "providerName": self.provider_name(skill),
            "providerUrl": self.provider_url(skill),
            "apiDocsUrl": self.provider_url(skill),
            "authRequirement": self.auth_requirement(skill),
            "callExample": self.call_example(skill),
        }
