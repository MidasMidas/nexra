import json
import logging
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

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
            return psycopg.connect(self.dsn)
        except ImportError:
            try:
                import psycopg2
            except ImportError as exc:
                raise RuntimeError(
                    "psycopg or psycopg2-binary is required for the Postgres state backend. "
                    "Add one of them to requirements.txt before deploying to Vercel."
                ) from exc
            return psycopg2.connect(self.dsn)

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
                    INSERT INTO nexra_auth_users (id, email, password, name, role, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        email = EXCLUDED.email,
                        password = EXCLUDED.password,
                        name = EXCLUDED.name,
                        role = EXCLUDED.role,
                        updated_at = NOW()
                    """,
                    (
                        user["id"],
                        user["email"],
                        user["password"],
                        user["name"],
                        user["role"],
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

    def describe(self):
        return f"postgres:{self.state_key}"


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
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
            )
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
                        INSERT INTO nexra_auth_users (id, email, password, name, role)
                        VALUES (%s, %s, %s, %s, %s)
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
                    INSERT INTO nexra_auth_users (id, email, password, name, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        email = VALUES(email),
                        password = VALUES(password),
                        name = VALUES(name),
                        role = VALUES(role),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        user["id"],
                        user["email"],
                        user["password"],
                        user["name"],
                        user["role"],
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
