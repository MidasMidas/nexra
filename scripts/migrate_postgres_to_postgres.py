import json
import os
import sys

try:
    import psycopg
    from psycopg.types.json import Json
except ImportError as exc:
    raise SystemExit("psycopg is required. Install requirements.txt first.") from exc


TABLES = [
    "nexra_state_store",
    "nexra_auth_users",
    "nexra_auth_sessions",
    "nexra_auth_verifications",
]


TARGET_SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS nexra_state_store (
        state_key TEXT PRIMARY KEY,
        snapshot JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
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
    """,
    """
    CREATE TABLE IF NOT EXISTS nexra_auth_sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS nexra_auth_verifications (
        email TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
]


def load_private_source_url():
    candidate_paths = [
        os.path.join("backend_py", "database.private.json"),
        os.path.join("backend", "database.private.json"),
    ]
    for path in candidate_paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            value = payload.get("DATABASE_URL") or payload.get("POSTGRES_URL")
            if value:
                return str(value).strip()
    return ""


def main():
    source_dsn = os.getenv("SOURCE_DATABASE_URL") or load_private_source_url()
    target_dsn = os.getenv("TARGET_DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")

    if not source_dsn:
        raise SystemExit("Missing SOURCE_DATABASE_URL and no local source database.private.json was found.")
    if not target_dsn:
        raise SystemExit("Missing TARGET_DATABASE_URL or SUPABASE_DATABASE_URL.")

    with psycopg.connect(source_dsn) as source_conn, psycopg.connect(target_dsn) as target_conn:
        source_conn.autocommit = True
        target_conn.autocommit = False
        with source_conn.cursor() as source_cur, target_conn.cursor() as target_cur:
            for statement in TARGET_SCHEMA_SQL:
                target_cur.execute(statement)
            for table in TABLES:
                source_cur.execute(
                    """
                    SELECT EXISTS (
                      SELECT 1
                      FROM information_schema.tables
                      WHERE table_name = %s
                    )
                    """,
                    (table,),
                )
                if not source_cur.fetchone()[0]:
                    print(f"skip {table}: missing in source")
                    continue

                source_cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (table,),
                )
                columns = [row[0] for row in source_cur.fetchall()]
                if not columns:
                    print(f"skip {table}: no columns")
                    continue

                quoted_columns = ", ".join(columns)
                target_cur.execute(f"DELETE FROM {table}")
                source_cur.execute(f"SELECT {quoted_columns} FROM {table}")
                rows = []
                for raw_row in source_cur.fetchall():
                    normalized_row = []
                    for value in raw_row:
                        if isinstance(value, (dict, list)):
                            normalized_row.append(Json(value))
                        else:
                            normalized_row.append(value)
                    rows.append(tuple(normalized_row))
                if rows:
                    placeholders = ", ".join(["%s"] * len(columns))
                    target_cur.executemany(
                        f"INSERT INTO {table} ({quoted_columns}) VALUES ({placeholders})",
                        rows,
                    )
                print(f"migrated {table}: {len(rows)} rows")

        target_conn.commit()

    print("Postgres migration complete.")


if __name__ == "__main__":
    main()
