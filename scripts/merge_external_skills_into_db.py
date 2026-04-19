import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend_py"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import resolve_config_path  # noqa: E402
from app.storage.state_store import create_state_store  # noqa: E402


def normalize(value):
    return " ".join(str(value or "").strip().lower().split())


def load_existing_keys(store):
    if hasattr(store, "_connect") and hasattr(store, "_ensure_business_schema"):
        with store._connect() as conn:
            with conn.cursor() as cursor:
                if store.__class__.__name__ == "PostgresStateStore":
                    cursor.execute("SET statement_timeout TO 0")
                cursor.execute(
                    "SELECT source_url, name, source_author FROM nexra_catalog_skills"
                )
                rows = cursor.fetchall()
        seen_urls = {normalize(row[0]) for row in rows if row[0]}
        seen_names = {(normalize(row[1]), normalize(row[2])) for row in rows}
        return seen_urls, seen_names, len(rows)

    snapshot = store.load_catalog_state() or {"skills": []}
    skills = snapshot.get("skills", [])
    seen_urls = {normalize(skill.get("sourceUrl")) for skill in skills if skill.get("sourceUrl")}
    seen_names = {(normalize(skill.get("name")), normalize(skill.get("sourceAuthor"))) for skill in skills}
    return seen_urls, seen_names, len(skills)


def bulk_upsert_skills(store, skills):
    if hasattr(store, "_connect") and hasattr(store, "_ensure_business_schema") and hasattr(
        store, "_upsert_skill_with_cursor"
    ):
        with store._connect() as conn:
            with conn.cursor() as cursor:
                if store.__class__.__name__ == "PostgresStateStore":
                    cursor.execute("SET statement_timeout TO 0")
            for index, skill in enumerate(skills, start=1):
                store._upsert_skill_with_cursor(conn, skill)
                if index % 200 == 0:
                    conn.commit()
            conn.commit()
        return

    snapshot = store.load_catalog_state() or {
        "skills": [],
        "skill_functions": [],
        "reviews": [],
        "skill_review_events": [],
        "api_keys": [],
        "billing_transactions": [],
        "daily_visits": [],
    }
    snapshot["skills"] = list(snapshot.get("skills", [])) + list(skills)
    store.save_catalog_state(snapshot)


def main():
    source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "backend_py" / "data" / "pulsemcp-skills.json"
    if not source_path.exists():
        raise SystemExit(f"Missing source file: {source_path}")

    with source_path.open("r", encoding="utf-8") as handle:
        imported_skills = json.load(handle)

    with resolve_config_path().open("r", encoding="utf-8-sig") as handle:
        config = json.load(handle)

    store = create_state_store(config)
    seen_urls, seen_names, existing_count = load_existing_keys(store)
    to_add = []
    for skill in imported_skills:
        url_key = normalize(skill.get("sourceUrl"))
        name_key = (normalize(skill.get("name")), normalize(skill.get("sourceAuthor")))
        if url_key and url_key in seen_urls:
            continue
        if name_key in seen_names:
            continue
        to_add.append(skill)
        if url_key:
            seen_urls.add(url_key)
        seen_names.add(name_key)
    bulk_upsert_skills(store, to_add)

    print(
        json.dumps(
            {
                "existingSkills": existing_count,
                "importedCandidates": len(imported_skills),
                "addedSkills": len(to_add),
                "finalSkills": existing_count + len(to_add),
                "sourceFile": str(source_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
