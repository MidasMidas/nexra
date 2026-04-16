import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "backend_py" / "config.json"
CONFIG_EXAMPLE_PATH = ROOT / "backend_py" / "config.example.json"
DATABASE_PRIVATE_PATH = ROOT / "backend_py" / "database.private.json"
MAIL_PRIVATE_PATH = ROOT / "backend_py" / "mailer.private.json"


def resolve_config_path() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    return CONFIG_EXAMPLE_PATH


def load_database_private_config() -> dict:
    if not DATABASE_PRIVATE_PATH.exists():
        return {}
    with DATABASE_PRIVATE_PATH.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def load_mail_private_config() -> dict:
    if not MAIL_PRIVATE_PATH.exists():
        return {}
    with MAIL_PRIVATE_PATH.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}
