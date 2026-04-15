import sys
from pathlib import Path
from typing import Type

from http.server import BaseHTTPRequestHandler

ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = ROOT / "backend_py"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.common.logging_config import configure_logging
from app.http.handler import create_handler
from app.services.nexra_service import NexraService

configure_logging()
_full_service = None
_auth_service = None


def resolve_service(method: str, path: str):
    global _full_service, _auth_service
    if path.startswith("/api/auth/"):
        if _auth_service is None:
            _auth_service = NexraService(load_catalog=False)
        return _auth_service
    if _full_service is None:
        _full_service = NexraService(load_catalog=True)
    return _full_service


_handler_cls: Type[BaseHTTPRequestHandler] = create_handler(resolve_service)


class handler(_handler_cls):
    pass
