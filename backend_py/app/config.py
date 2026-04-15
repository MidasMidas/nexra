from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "backend_py" / "config.json"
CONFIG_EXAMPLE_PATH = ROOT / "backend_py" / "config.example.json"


def resolve_config_path() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    return CONFIG_EXAMPLE_PATH
