from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os


def main() -> None:
    root = Path(__file__).resolve().parent
    os.chdir(root)
    server = ThreadingHTTPServer(("127.0.0.1", 4173), SimpleHTTPRequestHandler)
    print("Frontend running at http://127.0.0.1:4173")
    server.serve_forever()


if __name__ == "__main__":
    main()
