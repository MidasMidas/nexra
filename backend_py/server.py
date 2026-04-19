import logging
import os
from http.server import ThreadingHTTPServer

from app.common.logging_config import configure_logging
from app.http.handler import create_handler
from app.services.lite_service import LiteNexraService
from app.services.nexra_service import NexraService


_full_service = None
_auth_service = None
_dashboard_service = None


def resolve_service(method: str, path: str):
    global _full_service, _auth_service, _dashboard_service
    if path.startswith("/api/auth/"):
        if _auth_service is None:
            _auth_service = LiteNexraService(mode="auth")
        return _auth_service
    if method == "GET" and path == "/api/dashboard":
        if _dashboard_service is None:
            _dashboard_service = LiteNexraService(mode="dashboard")
        return _dashboard_service
    if _full_service is None:
        _full_service = NexraService(load_catalog=True)
    return _full_service


def main():
    configure_logging()
    bootstrap = LiteNexraService(mode="auth")
    host = os.getenv("HOST") or os.getenv("NEXRA_HOST") or bootstrap.config.get("host", "0.0.0.0")
    port = int(os.getenv("PORT") or bootstrap.config.get("port", 8080))
    if host in {"127.0.0.1", "localhost"}:
        host = "0.0.0.0"
    server = ThreadingHTTPServer((host, port), create_handler(resolve_service))
    logging.getLogger("nexra-python").info("Nexra Python backend running at http://%s:%s/api", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
