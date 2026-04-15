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
service = NexraService()
_handler_cls: Type[BaseHTTPRequestHandler] = create_handler(service)


class handler(_handler_cls):
    pass
