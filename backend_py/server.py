import logging
from http.server import ThreadingHTTPServer

from app.common.logging_config import configure_logging
from app.http.handler import create_handler
from app.services.nexra_service import NexraService


def main():
    configure_logging()
    app = NexraService()
    host = app.config.get("host", "127.0.0.1")
    port = int(app.config.get("port", 8080))
    server = ThreadingHTTPServer((host, port), create_handler(app))
    logging.getLogger("nexra-python").info("Nexra Python backend running at http://%s:%s/api", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
