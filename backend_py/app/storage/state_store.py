import json
import logging
import os
from pathlib import Path

from app.config import ROOT


log = logging.getLogger("nexra-python")


class FileStateStore:
    def __init__(self, state_path: Path):
        self.state_path = state_path

    def load_snapshot(self):
        if not self.state_path.exists() or self.state_path.stat().st_size == 0:
            return None
        with self.state_path.open("r", encoding="utf-8-sig") as handle:
            snapshot = json.load(handle)
        log.info("Loaded Python backend state snapshot from %s", self.state_path)
        return snapshot

    def save_snapshot(self, snapshot):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=False, indent=2)

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

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "psycopg is required for the Postgres state backend. "
                "Add it to requirements.txt before deploying to Vercel."
            ) from exc
        return psycopg.connect(self.dsn)

    def _ensure_schema(self, conn):
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

    def _ensure_auth_schema(self, conn):
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nexra_auth_users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
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
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        log.info("Loaded Python backend state snapshot from Postgres. stateKey=%s", self.state_key)
        return snapshot

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
                    "SELECT id, email, password, name, role FROM nexra_auth_users ORDER BY id ASC"
                )
                users = [
                    {
                        "id": row[0],
                        "email": row[1],
                        "password": row[2],
                        "name": row[3],
                        "role": row[4],
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
        return {"users": users, "sessions": sessions}

    def save_auth_state(self, auth_state):
        users = auth_state.get("users", [])
        sessions = auth_state.get("sessions", [])
        with self._connect() as conn:
            self._ensure_auth_schema(conn)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM nexra_auth_sessions")
                cursor.execute("DELETE FROM nexra_auth_users")
                for user in users:
                    cursor.execute(
                        """
                        INSERT INTO nexra_auth_users (id, email, password, name, role, updated_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            user["id"],
                            user["email"],
                            user["password"],
                            user["name"],
                            user["role"],
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
            conn.commit()

    def describe(self):
        return f"postgres:{self.state_key}"


def create_state_store(config):
    backend = os.getenv("NEXRA_STATE_BACKEND", "auto").strip().lower()
    postgres_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
    state_key = os.getenv("NEXRA_STATE_KEY", "primary")

    if backend == "postgres" or (backend == "auto" and postgres_url):
        if not postgres_url:
            raise RuntimeError("NEXRA_STATE_BACKEND=postgres requires POSTGRES_URL or DATABASE_URL.")
        return PostgresStateStore(postgres_url, state_key)

    if os.getenv("VERCEL") == "1":
        log.warning(
            "POSTGRES_URL/DATABASE_URL is not configured. Falling back to in-memory state in Vercel runtime. "
            "Data will reset between invocations until a database is configured."
        )
        return MemoryStateStore()

    return FileStateStore(ROOT / config["databasePath"])
