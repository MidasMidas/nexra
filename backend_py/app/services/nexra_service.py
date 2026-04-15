import json
import logging
import math
import re
import sqlite3
import threading
import uuid
from datetime import datetime

from app.config import ROOT, resolve_config_path
from app.common.errors import ApiError
from app.common.utils import clamp, now_iso, safe_text
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
    def __init__(self):
        self.config = self._load_config()
        self.skill_data_file = ROOT / self.config["skillDataFile"]
        self.state_store = create_state_store(self.config)
        self.lock = threading.RLock()
        self.conn = None
        self.sync_manager = SyncManager(self)
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
        self._load_snapshot_or_seed()
        self.sync_manager.last_imported_count = self.imported_skill_count()
        self.sync_manager.start_scheduler()
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
                    role TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
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
                """
            )

    def _seed_defaults(self):
        with self.lock, self.connect() as conn:
            seeded = False
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO users (id, email, password, name, role) VALUES (?, ?, ?, ?, ?)",
                    [
                        ("admin_1", "admin@nexra.local", "admin123", "Nexra Admin", "ADMIN"),
                        ("user_1", "alice@nexra.local", "alice123", "Alice Builder", "USER"),
                        ("user_2", "bob@nexra.local", "bob123", "Bob Operator", "USER"),
                    ],
                )
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
                self._save_snapshot()

    def _load_snapshot_or_seed(self):
        snapshot = self.state_store.load_snapshot()
        if snapshot:
            self._load_snapshot(snapshot)
            return
        self._seed_defaults()

    def _load_snapshot(self, snapshot):
        with self.lock, self.connect() as conn:
            conn.executescript(
                """
                DELETE FROM users;
                DELETE FROM sessions;
                DELETE FROM skills;
                DELETE FROM skill_functions;
                DELETE FROM reviews;
                DELETE FROM api_keys;
                DELETE FROM billing_transactions;
                """
            )
            for row in snapshot.get("users", []):
                conn.execute(
                    "INSERT INTO users (id, email, password, name, role) VALUES (?, ?, ?, ?, ?)",
                    (row["id"], row["email"], row["password"], row["name"], row["role"]),
                )
            for row in snapshot.get("sessions", []):
                conn.execute(
                    "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                    (row["token"], row["user_id"], row["created_at"]),
                )
            for row in snapshot.get("skills", []):
                conn.execute(
                    """
                    INSERT INTO skills (
                        id, name, category, description, price_per_call, status, success_rate,
                        latency_p95, cost_efficiency, user_rating_avg, user_rating_count, recent_calls,
                        invocation_method, submitted_by, approval_status, source, source_url,
                        source_author, license, operating_system
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"], row["name"], row["category"], row["description"], row["price_per_call"],
                        row["status"], row["success_rate"], row["latency_p95"], row["cost_efficiency"],
                        row["user_rating_avg"], row["user_rating_count"], row["recent_calls"],
                        row["invocation_method"], row["submitted_by"], row["approval_status"], row["source"],
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
            conn.commit()

    def _save_snapshot(self):
        with self.lock, self.connect() as conn:
            snapshot = {
                "users": [dict(row) for row in conn.execute("SELECT * FROM users").fetchall()],
                "sessions": [dict(row) for row in conn.execute("SELECT * FROM sessions").fetchall()],
                "skills": [dict(row) for row in conn.execute("SELECT * FROM skills").fetchall()],
                "skill_functions": [dict(row) for row in conn.execute("SELECT * FROM skill_functions").fetchall()],
                "reviews": [dict(row) for row in conn.execute("SELECT * FROM reviews").fetchall()],
                "api_keys": [dict(row) for row in conn.execute("SELECT * FROM api_keys").fetchall()],
                "billing_transactions": [dict(row) for row in conn.execute("SELECT * FROM billing_transactions").fetchall()],
            }
        self.state_store.save_snapshot(snapshot)

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
                    conn.execute("DELETE FROM skill_functions WHERE skill_id = ?", (skill_id,))
                    conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
            self._insert_skills(conn, imported_skills)
            conn.commit()
            self._save_snapshot()
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
                invocation_method, submitted_by, approval_status, source, source_url,
                source_author, license, operating_system
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        with self.connect() as conn:
            row = conn.execute("SELECT user_id FROM sessions WHERE token = ?", (token,)).fetchone()
        if row is None:
            raise ApiError(401, "Session expired. Please sign in again.")
        return row["user_id"]

    def require_user(self, user_id: str):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
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
            token = "nexra_" + uuid.uuid4().hex
            conn.execute(
                "INSERT OR REPLACE INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, row["id"], now_iso()),
            )
            conn.commit()
            self._save_snapshot()
        log.info("User logged in. userId=%s, email=%s, role=%s", row["id"], row["email"], row["role"])
        return {"token": token, "user": self._user_response(dict(row))}

    def register(self, payload):
        name = safe_text(payload.get("name")).strip()
        email = safe_text(payload.get("email")).strip().lower()
        password = safe_text(payload.get("password"))
        if not email:
            raise ApiError(400, "Invalid request: email is required.")
        if not password:
            raise ApiError(400, "Invalid request: password is required.")
        if len(password) < 6:
            raise ApiError(400, "Invalid request: password must be at least 6 characters.")
        if not name:
            local_part = email.split("@", 1)[0].strip()
            name = local_part or "Nexra User"
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                log.warning("Registration rejected for duplicate email. email=%s", email)
                raise ApiError(400, "This email is already registered.")
            user_id = "user_" + uuid.uuid4().hex[:8]
            conn.execute(
                "INSERT INTO users (id, email, password, name, role) VALUES (?, ?, ?, ?, ?)",
                (user_id, email, password, name, "USER"),
            )
            token = "nexra_" + uuid.uuid4().hex
            conn.execute(
                "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user_id, now_iso()),
            )
            conn.commit()
            self._save_snapshot()
        log.info("User registered. userId=%s, email=%s", user_id, email)
        return {"token": token, "user": self._user_response({"id": user_id, "name": name, "email": email, "role": "USER"})}

    def logout(self, authorization):
        token = self.extract_bearer_token(authorization)
        with self.connect() as conn:
            row = conn.execute("SELECT user_id FROM sessions WHERE token = ?", (token,)).fetchone()
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            self._save_snapshot()
        if row:
            log.info("User logged out. userId=%s", row["user_id"])
        return {"message": "Logged out."}

    def get_dashboard(self):
        skills = self._fetch_all_skills()
        approved = [skill for skill in skills if skill["status"].lower() != "revoked" and skill["approvalStatus"].upper() == "APPROVED"]
        pending = [skill for skill in skills if skill["approvalStatus"].upper() == "PENDING"]
        top_skills = [
            self._skill_response(skill, "", "")
            for skill in sorted(approved, key=lambda item: self.recommendation_score(item, "", ""), reverse=True)[:3]
        ]
        searchable_functions = len({function_name for skill in skills for function_name in skill["functions"]})
        return {
            "totalIndexedSkills": len(skills),
            "approvedSkills": len(approved),
            "pendingSkills": len(pending),
            "averageTrust": round(sum(self.overall_trust(skill) for skill in skills) / max(len(skills), 1)),
            "averageRecommendation": round(sum(self.recommendation_score(skill, "", "") for skill in skills) / max(len(skills), 1)),
            "searchableFunctions": searchable_functions,
            "popularSkills": len([skill for skill in skills if skill["recentCalls"] >= 10000]),
            "averageSuccessRate": round(sum(skill["successRate"] for skill in skills) / max(len(skills), 1)),
            "averageLatencyP95": round(sum(skill["latencyP95"] for skill in skills) / max(len(skills), 1)),
            "averageCostEfficiency": round(sum(skill["costEfficiency"] for skill in skills) / max(len(skills), 1)),
            "topSkills": top_skills,
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
            if not include_pending and skill["approvalStatus"].upper() != "APPROVED":
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
            self._save_snapshot()
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
            self._save_snapshot()
        log.info(
            "Skill submitted. skillId=%s, submittedBy=%s, category=%s, approvalStatus=%s",
            skill_id,
            user_id,
            skill["category"],
            skill["approvalStatus"],
        )
        return self._skill_response(skill, "", "")

    def get_pending_skills(self, authorization):
        self.require_admin(authorization)
        return [
            self._skill_response(skill, "", "")
            for skill in self._fetch_all_skills()
            if skill["approvalStatus"].upper() == "PENDING"
        ]

    def approve_skill(self, authorization, skill_id):
        admin = self.require_admin(authorization)
        with self.lock, self.connect() as conn:
            row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
            if row is None:
                raise ApiError(404, f"Skill not found: {skill_id}")
            conn.execute("UPDATE skills SET approval_status = 'APPROVED' WHERE id = ?", (skill_id,))
            conn.commit()
            self._save_snapshot()
        log.info("Skill approved. skillId=%s, adminUserId=%s", skill_id, admin["id"])
        return self._skill_response(self._find_skill(skill_id), "", "")

    def admin_update_skill(self, authorization, skill_id, payload):
        admin = self.require_admin(authorization)
        skill = self._find_skill(skill_id)
        updated = {
            **skill,
            "name": safe_text(payload.get("name")).strip(),
            "category": safe_text(payload.get("category")).strip(),
            "description": safe_text(payload.get("description")).strip(),
            "pricePerCall": float(payload.get("pricePerCall", 0)),
            "status": safe_text(payload.get("status")).strip(),
            "successRate": int(payload.get("successRate", 0)),
            "latencyP95": int(payload.get("latencyP95", 0)),
            "costEfficiency": int(payload.get("costEfficiency", 0)),
            "userRatingAvg": float(payload.get("userRatingAvg", 0)),
            "userRatingCount": int(payload.get("userRatingCount", 0)),
            "recentCalls": int(payload.get("recentCalls", 0)),
            "functions": self.sanitize_list(payload.get("functions", [])),
            "invocationMethod": safe_text(payload.get("invocationMethod")).strip(),
            "approvalStatus": safe_text(payload.get("approvalStatus")).strip(),
            "source": self.default_text(payload.get("source"), skill["source"]),
            "sourceUrl": self.default_text(payload.get("sourceUrl"), skill["sourceUrl"]),
            "sourceAuthor": self.default_text(payload.get("sourceAuthor"), skill["sourceAuthor"]),
            "license": self.default_text(payload.get("license"), skill["license"]),
            "operatingSystem": self.default_text(payload.get("operatingSystem"), skill["operatingSystem"]),
        }
        with self.lock, self.connect() as conn:
            self._insert_skill(conn, updated)
            conn.commit()
            self._save_snapshot()
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
            conn.execute("DELETE FROM skill_functions WHERE skill_id = ?", (skill_id,))
            conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
            conn.commit()
            self._save_snapshot()
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
            self._save_snapshot()
        log.info("API key created. name=%s, scope=%s, keyId=%s", key["name"], key["scope"], key["id"])
        return self._api_key_response(key)

    def _fetch_all_skills(self):
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
                    "source": row["source"],
                    "sourceUrl": row["source_url"],
                    "sourceAuthor": row["source_author"],
                    "license": row["license"],
                    "operatingSystem": row["operating_system"],
                }
            )
        return skills

    def _find_skill(self, skill_id):
        for skill in self._fetch_all_skills():
            if skill["id"] == skill_id:
                return skill
        raise ApiError(404, f"Skill not found: {skill_id}")

    def _user_response(self, user):
        return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}

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
        return round((float(skill["userRatingAvg"]) / 5.0) * 100)

    def agent_score(self, skill):
        latency_score = clamp(100 - (int(skill["latencyP95"]) - 200) / 10.0, 35, 100)
        return round(int(skill["successRate"]) * 0.5 + latency_score * 0.3 + int(skill["costEfficiency"]) * 0.2)

    def overall_trust(self, skill):
        return round(self.normalized_user_rating(skill) * 0.45 + self.agent_score(skill) * 0.55)

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
        return round(
            self.match_score(skill, query, function_name) * 0.35
            + self.overall_trust(skill) * 0.35
            + popularity * 0.15
            + int(skill["costEfficiency"]) * 0.10
            + int(skill["successRate"]) * 0.05
        )

    def recommendation_summary(self, skill, query, function_name):
        reasons = []
        if self.match_score(skill, query, function_name) >= 75:
            reasons.append("strong capability match")
        if self.overall_trust(skill) >= 85:
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

    def normalize_sort_by(self, sort_by):
        normalized = safe_text(sort_by).strip().lower()
        if normalized == "relevance":
            return "relevance"
        return "score"

    def skill_sort_key(self, skill, query, function_name, sort_by):
        match = self.match_score(skill, query, function_name)
        recommendation = self.recommendation_score(skill, query, function_name)
        trust = self.overall_trust(skill)
        agent = self.agent_score(skill)
        rating = float(skill["userRatingAvg"])
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
            "agentScore": agent_score,
            "systemScore": agent_score,
            "normalizedUserRating": self.normalized_user_rating(skill),
            "overallTrust": self.overall_trust(skill),
            "matchScore": self.match_score(skill, query, function_name),
            "recommendationScore": self.recommendation_score(skill, query, function_name),
            "recommendationSummary": self.recommendation_summary(skill, query, function_name),
            "functions": skill["functions"],
            "invocationMethod": skill["invocationMethod"],
            "submittedBy": skill["submittedBy"],
            "approvalStatus": skill["approvalStatus"],
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
