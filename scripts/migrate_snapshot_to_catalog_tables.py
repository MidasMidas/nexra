import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend_py"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.storage.state_store import PostgresStateStore  # noqa: E402


def main():
    dsn = os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not dsn:
        raise SystemExit("Missing TARGET_DATABASE_URL or DATABASE_URL or POSTGRES_URL.")

    store = PostgresStateStore(dsn, os.getenv("NEXRA_STATE_KEY", "primary"))
    snapshot = store.load_snapshot()
    if not snapshot:
        raise SystemExit("No legacy snapshot found in nexra_state_store.")
    store.save_catalog_state(snapshot)
    print(
        "catalog migration complete",
        {
            "skills": len(snapshot.get("skills", [])),
            "reviews": len(snapshot.get("reviews", [])),
            "reviewEvents": len(snapshot.get("skill_review_events", [])),
            "apiKeys": len(snapshot.get("api_keys", [])),
            "billingTransactions": len(snapshot.get("billing_transactions", [])),
            "dailyVisits": len(snapshot.get("daily_visits", [])),
        },
    )


if __name__ == "__main__":
    main()
