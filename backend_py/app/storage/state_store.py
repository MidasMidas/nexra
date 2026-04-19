import json
import logging
import math
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from app.common.utils import safe_text
from app.config import ROOT, load_database_private_config


log = logging.getLogger("nexra-python")


class FileStateStore:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.auth_state_path = state_path.with_name(f"{state_path.stem}-auth.json")

    def _load_json_file(self, path: Path):
        if not path.exists() or path.stat().st_size == 0:
            return None
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)

    def _save_json_file(self, path: Path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def load_snapshot(self):
        snapshot = self._load_json_file(self.state_path)
        if snapshot is None:
            return None
        log.info("Loaded Python backend state snapshot from %s", self.state_path)
        return snapshot

    def save_snapshot(self, snapshot):
        self._save_json_file(self.state_path, snapshot)

    def load_auth_state(self):
        auth_state = self._load_json_file(self.auth_state_path)
        if auth_state is not None:
            log.info("Loaded Python auth state from %s", self.auth_state_path)
            return auth_state
        snapshot = self.load_snapshot()
        if not snapshot:
            return None
        return {
            "users": snapshot.get("users", []),
            "sessions": snapshot.get("sessions", []),
        }

    def save_auth_state(self, auth_state):
        self._save_json_file(
            self.auth_state_path,
            {
                "users": auth_state.get("users", []),
                "sessions": auth_state.get("sessions", []),
                "verifications": auth_state.get("verifications", []),
            },
        )

    def upsert_auth_user(self, user):
        auth_state = self.load_auth_state() or {"users": [], "sessions": []}
        users = [row for row in auth_state.get("users", []) if row.get("id") != user["id"]]
        users.append(user)
        auth_state["users"] = users
        self.save_auth_state(auth_state)

    def upsert_auth_session(self, session):
        auth_state = self.load_auth_state() or {"users": [], "sessions": []}
        sessions = [row for row in auth_state.get("sessions", []) if row.get("token") != session["token"]]
        sessions.append(session)
        auth_state["sessions"] = sessions
        self.save_auth_state(auth_state)

    def delete_auth_session(self, token):
        auth_state = self.load_auth_state() or {"users": [], "sessions": []}
        auth_state["sessions"] = [
            row for row in auth_state.get("sessions", []) if row.get("token") != token
        ]
        self.save_auth_state(auth_state)

    def upsert_email_verification(self, verification):
        auth_state = self.load_auth_state() or {"users": [], "sessions": [], "verifications": []}
        verifications = [
            row for row in auth_state.get("verifications", []) if row.get("email") != verification["email"]
        ]
        verifications.append(verification)
        auth_state["verifications"] = verifications
        self.save_auth_state(auth_state)

    def delete_email_verification(self, email):
        auth_state = self.load_auth_state() or {"users": [], "sessions": [], "verifications": []}
        auth_state["verifications"] = [
            row for row in auth_state.get("verifications", []) if row.get("email") != email
        ]
        self.save_auth_state(auth_state)

    def describe(self):
        return f"file:{self.state_path}"


class MemoryStateStore:
    def __init__(self):
        self.snapshot = None

    def load_snapshot(self):
        return self.snapshot

    def save_snapshot(self, snapshot):
        self.snapshot = snapshot

    def describe(self):
        return "memory"


class PostgresStateStore:
    def __init__(self, dsn: str, state_key: str):
        self.dsn = dsn
        self.state_key = state_key
        self._snapshot_schema_ready = False
        self._auth_schema_ready = False
        self._business_schema_ready = False
        self._shared_conn = None

    def _connect(self):
        if self._shared_conn is not None and not getattr(self._shared_conn, "closed", False):
            return self._shared_conn
        try:
            import psycopg
            self._shared_conn = psycopg.connect(self.dsn)
            return self._shared_conn
        except ImportError:
            try:
                import psycopg2
            except ImportError as exc:
                raise RuntimeError(
                    "psycopg or psycopg2-binary is required for the Postgres state backend. "
                    "Add one of them to requirements.txt before deploying to Vercel."
                ) from exc
            self._shared_conn = psycopg2.connect(self.dsn)
            return self._shared_conn

    def _ensure_schema(self, conn):
        if self._snapshot_schema_ready:
            return
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_state_store (
                    state_key TEXT PRIMARY KEY,
                    snapshot JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()
        self._snapshot_schema_ready = True

    def _ensure_auth_schema(self, conn):
        if self._auth_schema_ready:
            return
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_auth_users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT '2026-01-01T00:00:00Z',
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                "ALTER TABLE nexra_auth_users ADD COLUMN IF NOT EXISTS created_at TEXT NOT NULL DEFAULT '2026-01-01T00:00:00Z'"
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_auth_sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_auth_verifications (
                    email TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()
        self._auth_schema_ready = True

    def _ensure_business_schema(self, conn):
        if self._business_schema_ready:
            return
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_skills (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price_per_call DOUBLE PRECISION NOT NULL,
                    status TEXT NOT NULL,
                    success_rate INTEGER NOT NULL,
                    latency_p95 INTEGER NOT NULL,
                    cost_efficiency INTEGER NOT NULL,
                    user_rating_avg DOUBLE PRECISION NOT NULL,
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
                    operating_system TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_skill_functions (
                    skill_id TEXT NOT NULL,
                    function_order INTEGER NOT NULL,
                    function_name TEXT NOT NULL,
                    PRIMARY KEY (skill_id, function_order)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_reviews (
                    id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_review_events (
                    id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    reviewer_user_id TEXT NOT NULL,
                    reviewer_name TEXT NOT NULL,
                    result TEXT NOT NULL,
                    note TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    last_used TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_billing_transactions (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    timestamp TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_daily_visits (
                    metric_date TEXT PRIMARY KEY,
                    visit_count INTEGER NOT NULL DEFAULT 0,
                    anonymous_visit_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                "ALTER TABLE nexra_catalog_daily_visits ADD COLUMN IF NOT EXISTS anonymous_visit_count INTEGER NOT NULL DEFAULT 0"
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_metric_totals (
                    metric_key TEXT PRIMARY KEY,
                    metric_value BIGINT NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_catalog_metric_daily (
                    metric_date TEXT PRIMARY KEY,
                    registered_users INTEGER NOT NULL DEFAULT 0,
                    visits INTEGER NOT NULL DEFAULT 0,
                    anonymous_visits INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()
        self._business_schema_ready = True

    def _load_business_snapshot(self, conn):
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id, name, category, description, price_per_call, status, success_rate,
                    latency_p95, cost_efficiency, user_rating_avg, user_rating_count, recent_calls,
                    invocation_method, submitted_by, approval_status, submitted_at, reviewed_at,
                    reviewed_by, review_result, source, source_url, source_author, license, operating_system
                FROM nexra_catalog_skills
                ORDER BY id ASC
                """
            )
            skills = [
                {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "description": row[3],
                    "pricePerCall": row[4],
                    "status": row[5],
                    "successRate": row[6],
                    "latencyP95": row[7],
                    "costEfficiency": row[8],
                    "userRatingAvg": row[9],
                    "userRatingCount": row[10],
                    "recentCalls": row[11],
                    "invocationMethod": row[12],
                    "submittedBy": row[13],
                    "approvalStatus": row[14],
                    "submittedAt": row[15],
                    "reviewedAt": row[16],
                    "reviewedBy": row[17],
                    "reviewResult": row[18],
                    "source": row[19],
                    "sourceUrl": row[20],
                    "sourceAuthor": row[21],
                    "license": row[22],
                    "operatingSystem": row[23],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT skill_id, function_order, function_name FROM nexra_catalog_skill_functions ORDER BY skill_id ASC, function_order ASC"
            )
            skill_functions = [
                {
                    "skill_id": row[0],
                    "function_order": row[1],
                    "function_name": row[2],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT id, skill_id, user_id, author, rating, comment, timestamp FROM nexra_catalog_reviews ORDER BY id ASC"
            )
            reviews = [
                {
                    "id": row[0],
                    "skill_id": row[1],
                    "user_id": row[2],
                    "author": row[3],
                    "rating": row[4],
                    "comment": row[5],
                    "timestamp": row[6],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT id, skill_id, reviewer_user_id, reviewer_name, result, note, timestamp FROM nexra_catalog_review_events ORDER BY id ASC"
            )
            skill_review_events = [
                {
                    "id": row[0],
                    "skill_id": row[1],
                    "reviewer_user_id": row[2],
                    "reviewer_name": row[3],
                    "result": row[4],
                    "note": row[5],
                    "timestamp": row[6],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute("SELECT id, name, scope, last_used, status FROM nexra_catalog_api_keys ORDER BY id ASC")
            api_keys = [
                {
                    "id": row[0],
                    "name": row[1],
                    "scope": row[2],
                    "last_used": row[3],
                    "status": row[4],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute("SELECT id, type, amount, timestamp FROM nexra_catalog_billing_transactions ORDER BY id ASC")
            billing_transactions = [
                {
                    "id": row[0],
                    "type": row[1],
                    "amount": row[2],
                    "timestamp": row[3],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT metric_date, visit_count, anonymous_visit_count FROM nexra_catalog_daily_visits ORDER BY metric_date ASC"
            )
            daily_visits = [
                {
                    "metric_date": row[0],
                    "visit_count": row[1],
                    "anonymous_visit_count": row[2],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT id, email, password, name, role, created_at FROM nexra_auth_users ORDER BY id ASC"
            )
            users = [
                {
                    "id": row[0],
                    "email": row[1],
                    "password": row[2],
                    "name": row[3],
                    "role": row[4],
                    "created_at": row[5],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute("SELECT token, user_id, created_at FROM nexra_auth_sessions ORDER BY token ASC")
            sessions = [
                {
                    "token": row[0],
                    "user_id": row[1],
                    "created_at": row[2],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT email, code, expires_at, created_at FROM nexra_auth_verifications ORDER BY email ASC"
            )
            email_verifications = [
                {
                    "email": row[0],
                    "code": row[1],
                    "expires_at": row[2],
                    "created_at": row[3],
                }
                for row in cursor.fetchall()
            ]
        return {
            "skills": skills,
            "skill_functions": skill_functions,
            "reviews": reviews,
            "skill_review_events": skill_review_events,
            "api_keys": api_keys,
            "billing_transactions": billing_transactions,
            "daily_visits": daily_visits,
            "users": users,
            "sessions": sessions,
            "email_verifications": email_verifications,
        }

    def _business_row_count(self, conn):
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM nexra_catalog_skills")
            return int(cursor.fetchone()[0] or 0)

    def _metric_total_row_count(self, conn):
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM nexra_catalog_metric_totals")
            return int(cursor.fetchone()[0] or 0)

    def _replace_metric_rows_from_snapshot(self, conn, snapshot):
        users = snapshot.get("users", [])
        visits = snapshot.get("daily_visits", [])
        daily_registrations = {}
        registered_users = 0
        for user in users:
            email = str(user.get("email", "")).strip().lower()
            role = str(user.get("role", "")).strip().upper()
            if role != "USER" or email.endswith("@nexra.local"):
                continue
            registered_users += 1
            metric_date = str(user.get("created_at", ""))[:10]
            if metric_date:
                daily_registrations[metric_date] = daily_registrations.get(metric_date, 0) + 1

        total_visits = 0
        total_anonymous_visits = 0
        daily_metrics = {}
        for visit in visits:
            metric_date = str(visit.get("metric_date", "")).strip()[:10]
            if not metric_date:
                continue
            visit_count = int(visit.get("visit_count", 0) or 0)
            anonymous_visit_count = int(visit.get("anonymous_visit_count", 0) or 0)
            total_visits += visit_count
            total_anonymous_visits += anonymous_visit_count
            bucket = daily_metrics.setdefault(
                metric_date,
                {"registered_users": 0, "visits": 0, "anonymous_visits": 0},
            )
            bucket["visits"] += visit_count
            bucket["anonymous_visits"] += anonymous_visit_count

        for metric_date, registration_count in daily_registrations.items():
            bucket = daily_metrics.setdefault(
                metric_date,
                {"registered_users": 0, "visits": 0, "anonymous_visits": 0},
            )
            bucket["registered_users"] += registration_count

        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE nexra_catalog_metric_daily, nexra_catalog_metric_totals")
            for metric_key, metric_value in (
                ("registered_users", registered_users),
                ("visits", total_visits),
                ("anonymous_visits", total_anonymous_visits),
            ):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_metric_totals (metric_key, metric_value, updated_at)
                    VALUES (%s, %s, NOW())
                    """,
                    (metric_key, metric_value),
                )
            for metric_date, metric_values in sorted(daily_metrics.items()):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_metric_daily (
                        metric_date, registered_users, visits, anonymous_visits, updated_at
                    )
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (
                        metric_date,
                        int(metric_values["registered_users"]),
                        int(metric_values["visits"]),
                        int(metric_values["anonymous_visits"]),
                    ),
                )

    def _replace_business_rows_from_snapshot(self, conn, snapshot):
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE nexra_catalog_skill_functions, nexra_catalog_reviews, nexra_catalog_review_events, nexra_catalog_api_keys, nexra_catalog_billing_transactions, nexra_catalog_daily_visits, nexra_catalog_skills")
            for skill in snapshot.get("skills", []):
                price_per_call = skill.get("pricePerCall", skill.get("price_per_call", 0))
                success_rate = skill.get("successRate", skill.get("success_rate", 0))
                latency_p95 = skill.get("latencyP95", skill.get("latency_p95", 0))
                cost_efficiency = skill.get("costEfficiency", skill.get("cost_efficiency", 0))
                user_rating_avg = skill.get("userRatingAvg", skill.get("user_rating_avg", 0))
                user_rating_count = skill.get("userRatingCount", skill.get("user_rating_count", 0))
                recent_calls = skill.get("recentCalls", skill.get("recent_calls", 0))
                invocation_method = skill.get("invocationMethod", skill.get("invocation_method", ""))
                submitted_by = skill.get("submittedBy", skill.get("submitted_by", ""))
                approval_status = skill.get("approvalStatus", skill.get("approval_status", "PENDING"))
                submitted_at = skill.get("submittedAt", skill.get("submitted_at", "2026-01-01T00:00:00Z"))
                reviewed_at = skill.get("reviewedAt", skill.get("reviewed_at"))
                reviewed_by = skill.get("reviewedBy", skill.get("reviewed_by", ""))
                review_result = skill.get("reviewResult", skill.get("review_result", approval_status))
                source_url = skill.get("sourceUrl", skill.get("source_url", ""))
                source_author = skill.get("sourceAuthor", skill.get("source_author", ""))
                operating_system = skill.get("operatingSystem", skill.get("operating_system", ""))
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_skills (
                        id, name, category, description, price_per_call, status, success_rate,
                        latency_p95, cost_efficiency, user_rating_avg, user_rating_count, recent_calls,
                        invocation_method, submitted_by, approval_status, submitted_at, reviewed_at,
                        reviewed_by, review_result, source, source_url, source_author, license, operating_system, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        skill["id"],
                        skill["name"],
                        skill["category"],
                        skill["description"],
                        float(price_per_call),
                        skill["status"],
                        int(success_rate),
                        int(latency_p95),
                        int(cost_efficiency),
                        float(user_rating_avg),
                        int(user_rating_count),
                        int(recent_calls),
                        invocation_method,
                        submitted_by,
                        approval_status,
                        submitted_at,
                        reviewed_at,
                        reviewed_by,
                        review_result,
                        skill.get("source", "manual"),
                        source_url,
                        source_author,
                        skill.get("license", "Unknown"),
                        operating_system,
                    ),
                )
            for row in snapshot.get("skill_functions", []):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_skill_functions (skill_id, function_order, function_name)
                    VALUES (%s, %s, %s)
                    """,
                    (row["skill_id"], row["function_order"], row["function_name"]),
                )
            for review in snapshot.get("reviews", []):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_reviews (id, skill_id, user_id, author, rating, comment, timestamp, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        review["id"],
                        review["skill_id"],
                        review["user_id"],
                        review["author"],
                        int(review["rating"]),
                        review["comment"],
                        review["timestamp"],
                    ),
                )
            for event in snapshot.get("skill_review_events", []):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_review_events (
                        id, skill_id, reviewer_user_id, reviewer_name, result, note, timestamp, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        event["id"],
                        event["skill_id"],
                        event.get("reviewer_user_id", event.get("reviewerUserId", "")),
                        event.get("reviewer_name", event.get("reviewerName", "")),
                        event["result"],
                        event["note"],
                        event["timestamp"],
                    ),
                )
            for key in snapshot.get("api_keys", []):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_api_keys (id, name, scope, last_used, status, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    """,
                    (key["id"], key["name"], key["scope"], key.get("last_used", key.get("lastUsed", "Never")), key["status"]),
                )
            for transaction in snapshot.get("billing_transactions", []):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_billing_transactions (id, type, amount, timestamp, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (transaction["id"], transaction["type"], float(transaction["amount"]), transaction["timestamp"]),
                )
            for visit in snapshot.get("daily_visits", []):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_daily_visits (metric_date, visit_count, anonymous_visit_count, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    """,
                    (
                        visit["metric_date"],
                        int(visit.get("visit_count", 0) or 0),
                        int(visit.get("anonymous_visit_count", 0) or 0),
                    ),
                )
        conn.commit()

    def _decode_json_value(self, value):
        if isinstance(value, str):
            return json.loads(value)
        return value

    def load_snapshot(self):
        with self._connect() as conn:
            self._ensure_schema(conn)
            self._ensure_auth_schema(conn)
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT snapshot FROM nexra_state_store WHERE state_key = %s",
                    (self.state_key,),
                )
                row = cursor.fetchone()
            snapshot = None
            if row:
                snapshot = self._decode_json_value(row[0])
            if os.getenv("NEXRA_EXPERIMENTAL_BUSINESS_TABLES", "").strip() == "1":
                business_count = self._business_row_count(conn)
                snapshot_skill_count = len(snapshot.get("skills", [])) if snapshot else 0
                if snapshot and business_count < snapshot_skill_count:
                    self._replace_business_rows_from_snapshot(conn, snapshot)
                    log.info(
                        "Loaded Python backend state snapshot from Postgres and refreshed incomplete business tables. stateKey=%s businessCount=%s snapshotSkillCount=%s",
                        self.state_key,
                        business_count,
                        snapshot_skill_count,
                    )
                    return snapshot
                if business_count > 0:
                    snapshot = self._load_business_snapshot(conn)
                    log.info("Loaded Python backend business snapshot from Postgres tables. stateKey=%s", self.state_key)
                    return snapshot
            if snapshot:
                log.info("Loaded Python backend state snapshot from Postgres. stateKey=%s", self.state_key)
                return snapshot
        return None

    def save_snapshot(self, snapshot):
        payload = json.dumps(snapshot, ensure_ascii=False)
        with self._connect() as conn:
            self._ensure_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_state_store (state_key, snapshot, updated_at)
                    VALUES (%s, %s::jsonb, NOW())
                    ON CONFLICT (state_key)
                    DO UPDATE SET snapshot = EXCLUDED.snapshot, updated_at = NOW()
                    """,
                    (self.state_key, payload),
                )
            conn.commit()

    def load_auth_state(self):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, password, name, role, created_at FROM nexra_auth_users ORDER BY id ASC"
                )
                users = [
                    {
                        "id": row[0],
                        "email": row[1],
                        "password": row[2],
                        "name": row[3],
                        "role": row[4],
                        "created_at": row[5],
                    }
                    for row in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT token, user_id, created_at FROM nexra_auth_sessions ORDER BY token ASC"
                )
                sessions = [
                    {
                        "token": row[0],
                        "user_id": row[1],
                        "created_at": row[2],
                    }
                    for row in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT email, code, expires_at, created_at FROM nexra_auth_verifications ORDER BY email ASC"
                )
                verifications = [
                    {
                        "email": row[0],
                        "code": row[1],
                        "expires_at": row[2],
                        "created_at": row[3],
                    }
                    for row in cursor.fetchall()
                ]
        return {"users": users, "sessions": sessions, "verifications": verifications}

    def find_auth_user_by_email(self, email):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password, name, role, created_at
                    FROM nexra_auth_users
                    WHERE LOWER(email) = LOWER(%s)
                    LIMIT 1
                    """,
                    (email,),
                )
                row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "email": row[1],
            "password": row[2],
            "name": row[3],
            "role": row[4],
            "created_at": row[5],
        }

    def find_auth_user_by_id(self, user_id):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password, name, role, created_at
                    FROM nexra_auth_users
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "email": row[1],
            "password": row[2],
            "name": row[3],
            "role": row[4],
            "created_at": row[5],
        }

    def find_email_verification(self, email):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT email, code, expires_at, created_at
                    FROM nexra_auth_verifications
                    WHERE LOWER(email) = LOWER(%s)
                    LIMIT 1
                    """,
                    (email,),
                )
                row = cursor.fetchone()
        if not row:
            return None
        return {
            "email": row[0],
            "code": row[1],
            "expires_at": row[2],
            "created_at": row[3],
        }

    def save_auth_state(self, auth_state):
        users = auth_state.get("users", [])
        sessions = auth_state.get("sessions", [])
        verifications = auth_state.get("verifications", [])
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_auth_verifications")
                cursor.execute("DELETE FROM nexra_auth_sessions")
                cursor.execute("DELETE FROM nexra_auth_users")
                for user in users:
                    cursor.execute(
                        """
                        INSERT INTO nexra_auth_users (id, email, password, name, role, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            user["id"],
                            user["email"],
                            user["password"],
                            user["name"],
                            user["role"],
                            user.get("created_at", "2026-01-01T00:00:00Z"),
                        ),
                    )
                for session in sessions:
                    cursor.execute(
                        """
                        INSERT INTO nexra_auth_sessions (token, user_id, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        """,
                        (
                            session["token"],
                            session["user_id"],
                            session["created_at"],
                        ),
                    )
                for verification in verifications:
                    cursor.execute(
                        """
                        INSERT INTO nexra_auth_verifications (email, code, expires_at, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        """,
                        (
                            verification["email"],
                            verification["code"],
                            verification["expires_at"],
                            verification["created_at"],
                        ),
                    )
            conn.commit()

    def upsert_auth_user(self, user):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_auth_users (id, email, password, name, role, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        email = EXCLUDED.email,
                        password = EXCLUDED.password,
                        name = EXCLUDED.name,
                        role = EXCLUDED.role,
                        created_at = EXCLUDED.created_at,
                        updated_at = NOW()
                    """,
                    (
                        user["id"],
                        user["email"],
                        user["password"],
                        user["name"],
                        user["role"],
                        user.get("created_at", "2026-01-01T00:00:00Z"),
                    ),
                )
            conn.commit()

    def upsert_auth_session(self, session):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_auth_sessions (token, user_id, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (token)
                    DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        created_at = EXCLUDED.created_at,
                        updated_at = NOW()
                    """,
                    (
                        session["token"],
                        session["user_id"],
                        session["created_at"],
                    ),
                )
            conn.commit()

    def delete_auth_session(self, token):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_auth_sessions WHERE token = %s", (token,))
            conn.commit()

    def upsert_email_verification(self, verification):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_auth_verifications (email, code, expires_at, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (email)
                    DO UPDATE SET
                        code = EXCLUDED.code,
                        expires_at = EXCLUDED.expires_at,
                        created_at = EXCLUDED.created_at,
                        updated_at = NOW()
                    """,
                    (
                        verification["email"],
                        verification["code"],
                        verification["expires_at"],
                        verification["created_at"],
                    ),
                )
            conn.commit()

    def delete_email_verification(self, email):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_auth_verifications WHERE email = %s", (email,))
            conn.commit()

    def describe(self):
        return f"postgres:{self.state_key}"

    def load_catalog_state(self):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            if self._business_row_count(conn) == 0:
                return None
            snapshot = self._load_business_snapshot(conn)
            if self._metric_total_row_count(conn) == 0:
                self._replace_metric_rows_from_snapshot(conn, snapshot)
                conn.commit()
            return snapshot

    def save_catalog_state(self, snapshot):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            self._replace_business_rows_from_snapshot(conn, snapshot)
            self._replace_metric_rows_from_snapshot(conn, snapshot)
            conn.commit()

    def upsert_skill(self, skill):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            self._upsert_skill_with_cursor(conn, skill)
            conn.commit()

    def _upsert_skill_with_cursor(self, conn, skill):
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO nexra_catalog_skills (
                    id, name, category, description, price_per_call, status, success_rate,
                    latency_p95, cost_efficiency, user_rating_avg, user_rating_count, recent_calls,
                    invocation_method, submitted_by, approval_status, submitted_at, reviewed_at,
                    reviewed_by, review_result, source, source_url, source_author, license, operating_system, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    description = EXCLUDED.description,
                    price_per_call = EXCLUDED.price_per_call,
                    status = EXCLUDED.status,
                    success_rate = EXCLUDED.success_rate,
                    latency_p95 = EXCLUDED.latency_p95,
                    cost_efficiency = EXCLUDED.cost_efficiency,
                    user_rating_avg = EXCLUDED.user_rating_avg,
                    user_rating_count = EXCLUDED.user_rating_count,
                    recent_calls = EXCLUDED.recent_calls,
                    invocation_method = EXCLUDED.invocation_method,
                    submitted_by = EXCLUDED.submitted_by,
                    approval_status = EXCLUDED.approval_status,
                    submitted_at = EXCLUDED.submitted_at,
                    reviewed_at = EXCLUDED.reviewed_at,
                    reviewed_by = EXCLUDED.reviewed_by,
                    review_result = EXCLUDED.review_result,
                    source = EXCLUDED.source,
                    source_url = EXCLUDED.source_url,
                    source_author = EXCLUDED.source_author,
                    license = EXCLUDED.license,
                    operating_system = EXCLUDED.operating_system,
                    updated_at = NOW()
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
            cursor.execute("DELETE FROM nexra_catalog_skill_functions WHERE skill_id = %s", (skill["id"],))
            for index, function_name in enumerate(skill.get("functions", [])):
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_skill_functions (skill_id, function_order, function_name)
                    VALUES (%s, %s, %s)
                    """,
                    (skill["id"], index, function_name),
                )

    def delete_skill(self, skill_id):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_catalog_reviews WHERE skill_id = %s", (skill_id,))
                cursor.execute("DELETE FROM nexra_catalog_review_events WHERE skill_id = %s", (skill_id,))
                cursor.execute("DELETE FROM nexra_catalog_skill_functions WHERE skill_id = %s", (skill_id,))
                cursor.execute("DELETE FROM nexra_catalog_skills WHERE id = %s", (skill_id,))
            conn.commit()

    def insert_review(self, review):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_reviews (id, skill_id, user_id, author, rating, comment, timestamp, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        skill_id = EXCLUDED.skill_id,
                        user_id = EXCLUDED.user_id,
                        author = EXCLUDED.author,
                        rating = EXCLUDED.rating,
                        comment = EXCLUDED.comment,
                        timestamp = EXCLUDED.timestamp,
                        updated_at = NOW()
                    """,
                    (
                        review["id"],
                        review["skill_id"],
                        review["user_id"],
                        review["author"],
                        int(review["rating"]),
                        review["comment"],
                        review["timestamp"],
                    ),
                )
            conn.commit()

    def insert_skill_review_event(self, event):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_review_events (
                        id, skill_id, reviewer_user_id, reviewer_name, result, note, timestamp, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        skill_id = EXCLUDED.skill_id,
                        reviewer_user_id = EXCLUDED.reviewer_user_id,
                        reviewer_name = EXCLUDED.reviewer_name,
                        result = EXCLUDED.result,
                        note = EXCLUDED.note,
                        timestamp = EXCLUDED.timestamp,
                        updated_at = NOW()
                    """,
                    (
                        event["id"],
                        event["skillId"],
                        event["reviewerUserId"],
                        event["reviewerName"],
                        event["result"],
                        event["note"],
                        event["timestamp"],
                    ),
                )
            conn.commit()

    def persist_skill_review_event_and_skill(self, event, skill):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_review_events (
                        id, skill_id, reviewer_user_id, reviewer_name, result, note, timestamp, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        skill_id = EXCLUDED.skill_id,
                        reviewer_user_id = EXCLUDED.reviewer_user_id,
                        reviewer_name = EXCLUDED.reviewer_name,
                        result = EXCLUDED.result,
                        note = EXCLUDED.note,
                        timestamp = EXCLUDED.timestamp,
                        updated_at = NOW()
                    """,
                    (
                        event["id"],
                        event["skillId"],
                        event["reviewerUserId"],
                        event["reviewerName"],
                        event["result"],
                        event["note"],
                        event["timestamp"],
                    ),
                )
            self._upsert_skill_with_cursor(conn, skill)
            conn.commit()

    def increment_registered_user(self, metric_date):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_metric_totals (metric_key, metric_value, updated_at)
                    VALUES ('registered_users', 1, NOW())
                    ON CONFLICT (metric_key)
                    DO UPDATE SET
                        metric_value = nexra_catalog_metric_totals.metric_value + 1,
                        updated_at = NOW()
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_metric_daily (metric_date, registered_users, visits, anonymous_visits, updated_at)
                    VALUES (%s, 1, 0, 0, NOW())
                    ON CONFLICT (metric_date)
                    DO UPDATE SET
                        registered_users = nexra_catalog_metric_daily.registered_users + 1,
                        updated_at = NOW()
                    """,
                    (metric_date,),
                )
            conn.commit()

    def increment_daily_visit(self, metric_date, anonymous=False):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_daily_visits (metric_date, visit_count, anonymous_visit_count, updated_at)
                    VALUES (%s, 1, %s, NOW())
                    ON CONFLICT (metric_date)
                    DO UPDATE SET
                        visit_count = nexra_catalog_daily_visits.visit_count + 1,
                        anonymous_visit_count = nexra_catalog_daily_visits.anonymous_visit_count + EXCLUDED.anonymous_visit_count,
                        updated_at = NOW()
                    """,
                    (metric_date, 1 if anonymous else 0),
                )
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_metric_totals (metric_key, metric_value, updated_at)
                    VALUES ('visits', 1, NOW())
                    ON CONFLICT (metric_key)
                    DO UPDATE SET
                        metric_value = nexra_catalog_metric_totals.metric_value + 1,
                        updated_at = NOW()
                    """
                )
                if anonymous:
                    cursor.execute(
                        """
                        INSERT INTO nexra_catalog_metric_totals (metric_key, metric_value, updated_at)
                        VALUES ('anonymous_visits', 1, NOW())
                        ON CONFLICT (metric_key)
                        DO UPDATE SET
                            metric_value = nexra_catalog_metric_totals.metric_value + 1,
                            updated_at = NOW()
                        """
                    )
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_metric_daily (metric_date, registered_users, visits, anonymous_visits, updated_at)
                    VALUES (%s, 0, 1, %s, NOW())
                    ON CONFLICT (metric_date)
                    DO UPDATE SET
                        visits = nexra_catalog_metric_daily.visits + 1,
                        anonymous_visits = nexra_catalog_metric_daily.anonymous_visits + EXCLUDED.anonymous_visits,
                        updated_at = NOW()
                    """,
                    (metric_date, 1 if anonymous else 0),
                )
            conn.commit()

    def upsert_api_key(self, api_key):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_catalog_api_keys (id, name, scope, last_used, status, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        scope = EXCLUDED.scope,
                        last_used = EXCLUDED.last_used,
                        status = EXCLUDED.status,
                        updated_at = NOW()
                    """,
                    (api_key["id"], api_key["name"], api_key["scope"], api_key["last_used"], api_key["status"]),
                )
            conn.commit()

    def get_catalog_metrics(self, days, page=0):
        page_size = min(max(int(days or 7), 1), 7)
        safe_page = max(int(page or 0), 0)
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT metric_key, metric_value
                    FROM nexra_catalog_metric_totals
                    WHERE metric_key IN ('registered_users', 'visits', 'anonymous_visits')
                    ORDER BY metric_key ASC
                    """
                )
                totals = {row[0]: int(row[1] or 0) for row in cursor.fetchall()}
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM nexra_catalog_metric_daily
                    """,
                )
                total_items = int(cursor.fetchone()[0] or 1)
                total_pages = max((total_items + page_size - 1) // page_size, 1)
                safe_page = min(safe_page, total_pages - 1)
                cursor.execute(
                    """
                    SELECT
                        metric_date,
                        registered_users,
                        visits,
                        anonymous_visits
                    FROM nexra_catalog_metric_daily
                    ORDER BY metric_date DESC
                    LIMIT %s OFFSET %s
                    """,
                    (page_size, safe_page * page_size),
                )
                daily = [
                    {
                        "date": row[0],
                        "registrations": int(row[1] or 0),
                        "visits": int(row[2] or 0),
                        "anonymousVisits": int(row[3] or 0),
                    }
                    for row in cursor.fetchall()
                ]
        return {
            "totals": {
                "registeredUsers": int(totals.get("registered_users", 0)),
                "visits": int(totals.get("visits", 0)),
                "anonymousVisits": int(totals.get("anonymous_visits", 0)),
            },
            "daily": daily,
            "days": page_size,
            "page": safe_page,
            "pageSize": page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
        }

    def get_public_dashboard(self):
        with self._connect() as conn:
            self._ensure_business_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    WITH skill_metrics AS (
                        SELECT
                            s.id,
                            s.name,
                            s.status,
                            s.approval_status,
                            s.success_rate,
                            s.latency_p95,
                            s.cost_efficiency,
                            s.recent_calls,
                            ROUND(
                                CASE
                                    WHEN s.user_rating_count > 0 THEN
                                        ROUND((s.user_rating_avg / 5.0) * 100) * 0.45
                                        + ROUND(
                                            s.success_rate * 0.5
                                            + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                            + s.cost_efficiency * 0.2
                                        ) * 0.55
                                    ELSE
                                        ROUND(
                                            s.success_rate * 0.5
                                            + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                            + s.cost_efficiency * 0.2
                                        )
                                END
                            ) AS overall_trust,
                            ROUND(
                                70 * 0.35
                                + ROUND(
                                    CASE
                                        WHEN s.user_rating_count > 0 THEN
                                            ROUND((s.user_rating_avg / 5.0) * 100) * 0.45
                                            + ROUND(
                                                s.success_rate * 0.5
                                                + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                                + s.cost_efficiency * 0.2
                                            ) * 0.55
                                        ELSE
                                            ROUND(
                                                s.success_rate * 0.5
                                                + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                                + s.cost_efficiency * 0.2
                                            )
                                    END
                                ) * 0.35
                                + LEAST(GREATEST(LOG(10, s.recent_calls + 10) * 20, 20), 100) * 0.15
                                + s.cost_efficiency * 0.10
                                + s.success_rate * 0.05
                            ) AS recommendation_score
                        FROM nexra_catalog_skills s
                    )
                    SELECT
                        COUNT(*) AS total_indexed_skills,
                        COUNT(*) FILTER (
                            WHERE LOWER(status) = 'active' AND UPPER(approval_status) = 'APPROVED'
                        ) AS approved_skills,
                        COUNT(*) FILTER (WHERE UPPER(approval_status) = 'PENDING') AS pending_skills,
                        ROUND(AVG(overall_trust)) AS average_trust,
                        ROUND(AVG(recommendation_score)) AS average_recommendation,
                        COUNT(*) FILTER (WHERE recent_calls >= 10000) AS popular_skills,
                        ROUND(AVG(success_rate)) AS average_success_rate,
                        ROUND(AVG(latency_p95)) AS average_latency_p95,
                        ROUND(AVG(cost_efficiency)) AS average_cost_efficiency
                    FROM skill_metrics
                    """
                )
                aggregate_row = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT function_name)
                    FROM nexra_catalog_skill_functions
                    """
                )
                searchable_functions = int(cursor.fetchone()[0] or 0)
                cursor.execute(
                    """
                    WITH skill_metrics AS (
                        SELECT
                            s.id,
                            s.name,
                            s.status,
                            s.approval_status,
                            ROUND(
                                CASE
                                    WHEN s.user_rating_count > 0 THEN
                                        ROUND((s.user_rating_avg / 5.0) * 100) * 0.45
                                        + ROUND(
                                            s.success_rate * 0.5
                                            + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                            + s.cost_efficiency * 0.2
                                        ) * 0.55
                                    ELSE
                                        ROUND(
                                            s.success_rate * 0.5
                                            + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                            + s.cost_efficiency * 0.2
                                        )
                                END
                            ) AS overall_trust,
                            ROUND(
                                70 * 0.35
                                + ROUND(
                                    CASE
                                        WHEN s.user_rating_count > 0 THEN
                                            ROUND((s.user_rating_avg / 5.0) * 100) * 0.45
                                            + ROUND(
                                                s.success_rate * 0.5
                                                + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                                + s.cost_efficiency * 0.2
                                            ) * 0.55
                                        ELSE
                                            ROUND(
                                                s.success_rate * 0.5
                                                + LEAST(GREATEST(100 - ((s.latency_p95 - 200) / 10.0), 35), 100) * 0.3
                                                + s.cost_efficiency * 0.2
                                            )
                                    END
                                ) * 0.35
                                + LEAST(GREATEST(LOG(10, s.recent_calls + 10) * 20, 20), 100) * 0.15
                                + s.cost_efficiency * 0.10
                                + s.success_rate * 0.05
                            ) AS recommendation_score
                        FROM nexra_catalog_skills s
                    )
                    SELECT id, name, overall_trust, recommendation_score
                    FROM skill_metrics
                    WHERE LOWER(status) = 'active' AND UPPER(approval_status) = 'APPROVED'
                    ORDER BY recommendation_score DESC, overall_trust DESC, name ASC
                    LIMIT 3
                    """
                )
                top_skills = [
                    {
                        "id": row[0],
                        "name": row[1],
                        "overallTrust": int(row[2] or 0),
                        "recommendationScore": int(row[3] or 0),
                    }
                    for row in cursor.fetchall()
                ]

        return {
            "totalIndexedSkills": int(aggregate_row[0] or 0),
            "approvedSkills": int(aggregate_row[1] or 0),
            "pendingSkills": int(aggregate_row[2] or 0),
            "averageTrust": int(aggregate_row[3] or 0),
            "averageRecommendation": int(aggregate_row[4] or 0),
            "searchableFunctions": searchable_functions,
            "popularSkills": int(aggregate_row[5] or 0),
            "averageSuccessRate": int(aggregate_row[6] or 0),
            "averageLatencyP95": int(aggregate_row[7] or 0),
            "averageCostEfficiency": int(aggregate_row[8] or 0),
            "topSkills": top_skills,
        }


class MySQLStateStore:
    def __init__(self, config: dict, state_key: str):
        self.config = config
        self.state_key = state_key

    def _connect(self):
        try:
            import mysql.connector
        except ImportError as exc:
            raise RuntimeError(
                "mysql-connector-python is required for the MySQL state backend. "
                "Add it to requirements.txt before deploying."
            ) from exc
        return mysql.connector.connect(**self.config)

    def _ensure_schema(self, conn):
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_state_store (
                    state_key VARCHAR(191) PRIMARY KEY,
                    snapshot LONGTEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()

    def _ensure_auth_schema(self, conn):
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_auth_users (
                    id VARCHAR(191) PRIMARY KEY,
                    email VARCHAR(191) NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    name VARCHAR(191) NOT NULL,
                    role VARCHAR(64) NOT NULL,
                    created_at VARCHAR(64) NOT NULL DEFAULT '2026-01-01T00:00:00Z',
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
            )
            try:
                cursor.execute(
                    "ALTER TABLE nexra_auth_users ADD COLUMN created_at VARCHAR(64) NOT NULL DEFAULT '2026-01-01T00:00:00Z'"
                )
            except Exception:
                pass
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_auth_sessions (
                    token VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(191) NOT NULL,
                    created_at VARCHAR(64) NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_auth_verifications (
                    email VARCHAR(191) PRIMARY KEY,
                    code VARCHAR(32) NOT NULL,
                    expires_at VARCHAR(64) NOT NULL,
                    created_at VARCHAR(64) NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()

    def load_snapshot(self):
        with self._connect() as conn:
            self._ensure_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT snapshot FROM nexra_state_store WHERE state_key = %s",
                    (self.state_key,),
                )
                row = cursor.fetchone()
        if not row:
            return None
        snapshot = row[0]
        if isinstance(snapshot, (bytes, bytearray)):
            snapshot = snapshot.decode("utf-8")
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        log.info("Loaded Python backend state snapshot from MySQL. stateKey=%s", self.state_key)
        return snapshot

    def save_snapshot(self, snapshot):
        payload = json.dumps(snapshot, ensure_ascii=False)
        with self._connect() as conn:
            self._ensure_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_state_store (state_key, snapshot)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        snapshot = VALUES(snapshot),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (self.state_key, payload),
                )
            conn.commit()

    def load_auth_state(self):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, password, name, role, created_at FROM nexra_auth_users ORDER BY id ASC"
                )
                users = [
                    {
                        "id": row[0],
                        "email": row[1],
                        "password": row[2],
                        "name": row[3],
                        "role": row[4],
                        "created_at": row[5],
                    }
                    for row in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT token, user_id, created_at FROM nexra_auth_sessions ORDER BY token ASC"
                )
                sessions = [
                    {
                        "token": row[0],
                        "user_id": row[1],
                        "created_at": row[2],
                    }
                    for row in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT email, code, expires_at, created_at FROM nexra_auth_verifications ORDER BY email ASC"
                )
                verifications = [
                    {
                        "email": row[0],
                        "code": row[1],
                        "expires_at": row[2],
                        "created_at": row[3],
                    }
                    for row in cursor.fetchall()
                ]
        return {"users": users, "sessions": sessions, "verifications": verifications}

    def save_auth_state(self, auth_state):
        users = auth_state.get("users", [])
        sessions = auth_state.get("sessions", [])
        verifications = auth_state.get("verifications", [])
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_auth_verifications")
                cursor.execute("DELETE FROM nexra_auth_sessions")
                cursor.execute("DELETE FROM nexra_auth_users")
                for user in users:
                    cursor.execute(
                        """
                        INSERT INTO nexra_auth_users (id, email, password, name, role, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user["id"],
                            user["email"],
                            user["password"],
                            user["name"],
                            user["role"],
                            user.get("created_at", "2026-01-01T00:00:00Z"),
                        ),
                    )
                for session in sessions:
                    cursor.execute(
                        """
                        INSERT INTO nexra_auth_sessions (token, user_id, created_at)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            session["token"],
                            session["user_id"],
                            session["created_at"],
                        ),
                    )
                for verification in verifications:
                    cursor.execute(
                        """
                        INSERT INTO nexra_auth_verifications (email, code, expires_at, created_at)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            verification["email"],
                            verification["code"],
                            verification["expires_at"],
                            verification["created_at"],
                        ),
                    )
            conn.commit()

    def upsert_auth_user(self, user):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_auth_users (id, email, password, name, role, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        email = VALUES(email),
                        password = VALUES(password),
                        name = VALUES(name),
                        role = VALUES(role),
                        created_at = VALUES(created_at),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        user["id"],
                        user["email"],
                        user["password"],
                        user["name"],
                        user["role"],
                        user.get("created_at", "2026-01-01T00:00:00Z"),
                    ),
                )
            conn.commit()

    def upsert_auth_session(self, session):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_auth_sessions (token, user_id, created_at)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        user_id = VALUES(user_id),
                        created_at = VALUES(created_at),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        session["token"],
                        session["user_id"],
                        session["created_at"],
                    ),
                )
            conn.commit()

    def delete_auth_session(self, token):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_auth_sessions WHERE token = %s", (token,))
            conn.commit()

    def upsert_email_verification(self, verification):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nexra_auth_verifications (email, code, expires_at, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        code = VALUES(code),
                        expires_at = VALUES(expires_at),
                        created_at = VALUES(created_at),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        verification["email"],
                        verification["code"],
                        verification["expires_at"],
                        verification["created_at"],
                    ),
                )
            conn.commit()

    def delete_email_verification(self, email):
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_auth_verifications WHERE email = %s", (email,))
            conn.commit()

    def describe(self):
        database = self.config.get("database", "")
        return f"mysql:{database or self.state_key}"


def resolve_mysql_config():
    private = load_database_private_config()
    mysql_url = private.get("MYSQL_URL") or os.getenv("MYSQL_URL")
    database_url = private.get("DATABASE_URL") or os.getenv("DATABASE_URL")
    candidate = mysql_url or (database_url if (database_url or "").lower().startswith("mysql") else None)
    if candidate:
        parsed = urlparse(candidate)
        params = parse_qs(parsed.query)
        config = {
            "host": parsed.hostname,
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "database": parsed.path.lstrip("/"),
        }
        ssl_ca = params.get("ssl_ca", [None])[0] or private.get("MYSQL_SSL_CA") or os.getenv("MYSQL_SSL_CA")
        if ssl_ca:
            config["ssl_ca"] = ssl_ca
            config["ssl_verify_cert"] = True
        return config

    host = private.get("MYSQL_HOST") or os.getenv("MYSQL_HOST") or os.getenv("PLANETSCALE_DB_HOST")
    user = private.get("MYSQL_USER") or os.getenv("MYSQL_USER") or os.getenv("PLANETSCALE_DB_USERNAME")
    password = private.get("MYSQL_PASSWORD") or os.getenv("MYSQL_PASSWORD") or os.getenv("PLANETSCALE_DB_PASSWORD")
    database = private.get("MYSQL_DATABASE") or os.getenv("MYSQL_DATABASE") or os.getenv("PLANETSCALE_DATABASE") or os.getenv("PLANETSCALE_DB")
    if not host or not user or not database:
        return None
    config = {
        "host": host,
        "port": int(private.get("MYSQL_PORT") or os.getenv("MYSQL_PORT") or os.getenv("PLANETSCALE_DB_PORT") or "3306"),
        "user": user,
        "password": password or "",
        "database": database,
    }
    ssl_ca = private.get("MYSQL_SSL_CA") or os.getenv("MYSQL_SSL_CA") or os.getenv("PLANETSCALE_SSL_CA")
    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True
    return config


def resolve_postgres_url():
    private = load_database_private_config()
    return (
        private.get("POSTGRES_URL")
        or private.get("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("DATABASE_URL")
    )


def create_state_store(config):
    backend = os.getenv("NEXRA_STATE_BACKEND", "auto").strip().lower()
    postgres_url = resolve_postgres_url()
    mysql_config = resolve_mysql_config()
    state_key = os.getenv("NEXRA_STATE_KEY", "primary")

    if backend == "mysql" or (backend == "auto" and mysql_config):
        if not mysql_config:
            raise RuntimeError("NEXRA_STATE_BACKEND=mysql requires MYSQL_URL or MYSQL_* / PLANETSCALE_* variables.")
        return MySQLStateStore(mysql_config, state_key)

    if backend == "postgres" or (backend == "auto" and postgres_url):
        if not postgres_url:
            raise RuntimeError("NEXRA_STATE_BACKEND=postgres requires POSTGRES_URL or DATABASE_URL.")
        return PostgresStateStore(postgres_url, state_key)

    if os.getenv("VERCEL") == "1":
        log.warning(
            "MySQL/Postgres environment variables are not configured. Falling back to in-memory state in Vercel runtime. "
            "Data will reset between invocations until a database is configured."
        )
        return MemoryStateStore()

    return FileStateStore(ROOT / config["databasePath"])
