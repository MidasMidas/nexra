import json
import logging
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from app.common.errors import ApiError


log = logging.getLogger("nexra-python")


def create_handler(app):
    class NexraHandler(BaseHTTPRequestHandler):
        server_version = "NexraPython/1.0"

        def do_OPTIONS(self):
            self.send_response(204)
            self._write_headers()
            self.end_headers()

        def do_GET(self):
            self._handle("GET")

        def do_POST(self):
            self._handle("POST")

        def do_PUT(self):
            self._handle("PUT")

        def do_DELETE(self):
            self._handle("DELETE")

        def _handle(self, method):
            parsed = urlparse(self.path)
            path = parsed.path
            query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
            try:
                payload = self._read_json_body() if method in {"POST", "PUT"} else None
                result = self.route(method, path, query, payload)
                self._send_json(200, result)
            except ApiError as exc:
                self._send_json(exc.status, {"message": exc.message})
            except Exception:
                log.exception("Unhandled server error. method=%s path=%s", method, path)
                self._send_json(500, {"message": "Internal server error."})

        def route(self, method, path, query, payload):
            auth = self.headers.get("Authorization")
            if method == "GET" and path == "/api":
                return app.get_welcome(self._request_origin(), self._api_base_url())
            if method == "GET" and path == "/api/agent-guide":
                return app.get_agent_guide(self._request_origin(), self._api_base_url())
            if method == "GET" and path == "/api/dashboard":
                return app.get_dashboard()
            if method == "POST" and path == "/api/auth/login":
                return app.login(payload or {})
            if method == "POST" and path == "/api/auth/register":
                return app.register(payload or {})
            if method == "POST" and path == "/api/auth/logout":
                return app.logout(auth)
            if method == "GET" and path == "/api/skills":
                return app.search_skills(
                    query=query.get("q", ""),
                    function_name=query.get("function", ""),
                    readiness=query.get("readiness", ""),
                    hide_templates=str(query.get("hideTemplates", "false")).lower() == "true",
                    page=int(query.get("page", "0")),
                    page_size=int(query.get("pageSize", "10")),
                    include_pending=False,
                )
            if method == "GET" and path.startswith("/api/skills/") and not path.endswith("/reviews"):
                return app.get_skill_detail(path.removeprefix("/api/skills/"))
            if method == "POST" and path == "/api/skills/submissions":
                return app.submit_skill(auth, payload or {})
            if method == "POST" and path.endswith("/reviews") and path.startswith("/api/skills/"):
                skill_id = path[len("/api/skills/") : -len("/reviews")]
                return app.add_review(auth, skill_id, payload or {})
            if method == "GET" and path == "/api/users":
                return app.get_users(auth)
            if method == "GET" and path == "/api/users/me":
                return app.get_user_profile(auth)
            if method == "GET" and path == "/api/billing/summary":
                return app.get_billing_summary(auth)
            if method == "GET" and path == "/api/billing/transactions":
                return app.get_transactions(auth)
            if method == "GET" and path == "/api/keys":
                return app.get_api_keys(auth)
            if method == "POST" and path == "/api/keys":
                return app.create_api_key(auth, payload or {})
            if method == "GET" and path == "/api/admin/skills/pending":
                return app.get_pending_skills(auth)
            if method == "POST" and path.startswith("/api/admin/skills/") and path.endswith("/approve"):
                skill_id = path[len("/api/admin/skills/") : -len("/approve")]
                return app.approve_skill(auth, skill_id)
            if method == "PUT" and path.startswith("/api/admin/skills/"):
                return app.admin_update_skill(auth, path.removeprefix("/api/admin/skills/"), payload or {})
            if method == "DELETE" and path.startswith("/api/admin/skills/"):
                return app.admin_delete_skill(auth, path.removeprefix("/api/admin/skills/"))
            if method == "GET" and path == "/api/admin/skills/sync/status":
                app.require_admin(auth)
                return app.sync_manager.status()
            if method == "POST" and path == "/api/admin/skills/sync":
                app.require_admin(auth)
                return app.sync_manager.sync_now(trigger="manual")
            raise ApiError(404, f"Path not found: {path}")

        def _read_json_body(self):
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError:
                raise ApiError(400, "Invalid request: body must be valid JSON.")

        def _send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self._write_headers(len(body))
            self.end_headers()
            self.wfile.write(body)

        def _request_origin(self):
            forwarded_host = self.headers.get("X-Forwarded-Host")
            host = forwarded_host or self.headers.get("Host") or f"{self.server.server_name}:{self.server.server_port}"
            forwarded_proto = self.headers.get("X-Forwarded-Proto")
            proto = forwarded_proto or ("https" if str(self.server.server_port) == "443" else "http")
            return f"{proto}://{host}"

        def _api_base_url(self):
            return f"{self._request_origin()}/api"

        def _write_headers(self, content_length=0):
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(content_length))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

        def log_message(self, fmt, *args):
            log.info("%s - %s", self.address_string(), fmt % args)

    return NexraHandler
