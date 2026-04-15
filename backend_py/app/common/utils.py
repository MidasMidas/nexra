from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_text(value):
    return "" if value is None else str(value)


def clamp(value, low, high):
    return min(max(value, low), high)
