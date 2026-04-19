import json
import logging
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from app.common.errors import ApiError


log = logging.getLogger("nexra-python")


def allowed_origin(request_origin: str):
    configured = os.getenv("NEXRA_CORS_ALLOW_ORIGINS", "").strip()
    if not configured:
        return "*"
    allowed = [item.strip() for item in configured.split(",") if item.strip()]
    if not allowed:
        return "*"
    if "*" in allowed:
        return "*"
    if request_origin in allowed:
        return request_origin
    return allowed[0]


def build_welcome_payload(frontend_origin: str, api_base_url: str):
    agent_guide_url = f"{api_base_url.rstrip('/')}/agent-guide"
    return {
        "productName": "Nexra",
        "headline": "Find the right skill before your agent calls it",
        "summary": "Nexra helps your agent search, compare, and evaluate external skills with trust signals, recommendation scores, and clear calling guidance.",
        "steps": [
            "Search the marketplace by keyword or capability.",
            "Compare recommendation score, trust score, price, and calling method.",
            "Open a skill detail page to read provider docs and calling notes.",
            "Let your own agent call the external skill directly and come back to Nexra for feedback.",
        ],
        "capabilities": [
            "Search and recommendation for agent-ready skills",
            "Dual scoring with user rating and system rating",
            "Moderation, governance, and calling guidance in one place",
        ],
        "frontendUrl": frontend_origin,
        "agentGuideUrl": agent_guide_url,
    }


def build_agent_guide_payload(api_base_url: str):
    api_base = api_base_url.rstrip("/")
    return {
        "name": "Nexra Agent Guide",
        "goal": "Help any AI agent discover, choose, and call external skills correctly.",
        "invokeEndpoint": "/api/skills and /api/skills/{id}",
        "workflow": [
            "Fetch available skills from GET /api/skills.",
            "Compare recommendationScore, overallTrust, userRatingAvg, systemScore, and pricePerCall.",
            "Select the best skill for the task and read its provider docs.",
            "Use GET /api/skills/{id} for deeper trust, calling notes, and review context.",
            "Call the chosen skill directly from your own agent runtime.",
            "After a human sees the result, submit feedback to POST /api/skills/{id}/reviews.",
        ],
        "rules": [
            "Prefer higher recommendationScore when the capability match is strong.",
            "Use overallTrust as a blended quality signal.",
            "Use userRatingAvg to estimate human satisfaction.",
            "Use systemScore to estimate operational reliability.",
            "Treat provider documentation as the source of truth for external invocation details.",
        ],
        "exampleCall": {
            "method": "GET",
            "endpoint": f"{api_base}/skills?q=image&function=ocr&page=0&pageSize=5",
            "contentType": "application/json",
            "payload": "{\"note\":\"Choose a skill from the search results, then call the provider directly.\"}",
        },
    }


def create_handler(app):
    class NexraHandler(BaseHTTPRequestHandler):
        server_version = "NexraPython/1.0"

        def _app(self, method, path):
            return app(method, path) if callable(app) else app

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
            if method == "POST" and path == "/api/auth/logout":
                # Logout is client-driven in the current stateless token model.
                # Return immediately so sign-out is not blocked by service cold starts.
                return {"message": "Logged out."}
            if method == "GET" and path == "/api":
                return build_welcome_payload(self._request_origin(), self._api_base_url())
            if method == "GET" and path == "/api/agent-guide":
                return build_agent_guide_payload(self._api_base_url())
            current_app = self._app(method, path)
            if method == "GET" and path == "/api/dashboard":
                return current_app.get_dashboard()
            if method == "POST" and path == "/api/analytics/visit":
                return current_app.record_visit(auth)
            if method == "POST" and path == "/api/auth/login":
                return current_app.login(payload or {})
            if method == "POST" and path == "/api/auth/register/request-code":
                return current_app.request_register_code(payload or {})
            if method == "POST" and path == "/api/auth/register":
                return current_app.register(payload or {})
            if method == "GET" and path == "/api/skills":
                return current_app.search_skills(
                    query=query.get("q", ""),
                    function_name=query.get("function", ""),
                    readiness=query.get("readiness", ""),
                    hide_templates=str(query.get("hideTemplates", "false")).lower() == "true",
                    page=int(query.get("page", "0")),
                    page_size=int(query.get("pageSize", "10")),
                    include_pending=False,
                    sort_by=query.get("sortBy", "score"),
                )
            if method == "GET" and path.startswith("/api/skills/") and not path.endswith("/reviews"):
                return current_app.get_skill_detail(path.removeprefix("/api/skills/"))
            if method == "POST" and path == "/api/skills/submissions":
                return current_app.submit_skill(auth, payload or {})
            if method == "PUT" and path.startswith("/api/skills/submissions/"):
                return current_app.update_submitted_skill(auth, path.removeprefix("/api/skills/submissions/"), payload or {})
            if method == "POST" and path.endswith("/reviews") and path.startswith("/api/skills/"):
                skill_id = path[len("/api/skills/") : -len("/reviews")]
                return current_app.add_review(auth, skill_id, payload or {})
            if method == "GET" and path == "/api/users":
                return current_app.get_users(auth)
            if method == "GET" and path == "/api/users/me":
                return current_app.get_user_profile(auth)
            if method == "GET" and path == "/api/billing/summary":
                return current_app.get_billing_summary(auth)
            if method == "GET" and path == "/api/billing/transactions":
                return current_app.get_transactions(auth)
            if method == "GET" and path == "/api/keys":
                return current_app.get_api_keys(auth)
            if method == "POST" and path == "/api/keys":
                return current_app.create_api_key(auth, payload or {})
            if method == "GET" and path == "/api/admin/skills":
                return current_app.get_admin_skills(
                    auth,
                    status=query.get("status", ""),
                    search=query.get("q", ""),
                    page=int(query.get("page", "0")),
                    page_size=int(query.get("pageSize", "10")),
                )
            if method == "GET" and path == "/api/admin/metrics":
                return current_app.get_admin_metrics(
                    auth,
                    days=int(query.get("days", "7")),
                    page=int(query.get("page", "0")),
                )
            if method == "GET" and path == "/api/admin/skills/pending":
                return current_app.get_pending_skills(auth)
            if method == "POST" and path.startswith("/api/admin/skills/") and path.endswith("/approve"):
                skill_id = path[len("/api/admin/skills/") : -len("/approve")]
                return current_app.approve_skill(auth, skill_id)
            if method == "POST" and path.startswith("/api/admin/skills/") and path.endswith("/reject"):
                skill_id = path[len("/api/admin/skills/") : -len("/reject")]
                return current_app.reject_skill(auth, skill_id)
            if method == "PUT" and path.startswith("/api/admin/skills/"):
                return current_app.admin_update_skill(auth, path.removeprefix("/api/admin/skills/"), payload or {})
            if method == "DELETE" and path.startswith("/api/admin/skills/"):
                return current_app.admin_delete_skill(auth, path.removeprefix("/api/admin/skills/"))
            if method == "GET" and path == "/api/admin/skills/sync/status":
                current_app.require_admin(auth)
                return current_app.sync_manager.status()
            if method == "POST" and path == "/api/admin/skills/sync":
                current_app.require_admin(auth)
                return current_app.sync_manager.sync_now(trigger="manual")
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
            request_origin = self.headers.get("Origin", "")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(content_length))
            self.send_header("Access-Control-Allow-Origin", allowed_origin(request_origin))
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Vary", "Origin")

        def log_message(self, fmt, *args):
            log.info("%s - %s", self.address_string(), fmt % args)

    return NexraHandler
