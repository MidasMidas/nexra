import base64
import hashlib
import hmac
import json
import logging
import os
import random
import threading
import uuid
from datetime import datetime, timedelta

from app.common.errors import ApiError
from app.common.utils import now_iso, safe_text
from app.config import resolve_config_path
from app.services.email_service import EmailService
from app.storage.state_store import create_state_store


log = logging.getLogger("nexra-python")


class LiteNexraService:
    def __init__(self, mode="auth"):
        self.mode = mode
        self.config = self._load_config()
        self.state_store = create_state_store(self.config)
        self.email_service = EmailService()
        self._dashboard_cache = None
        self._dashboard_cache_ttl_seconds = 30
        self._dashboard_shared_cache_ttl_seconds = 300

    def _load_config(self):
        config_path = resolve_config_path()
        with config_path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)

    def _auth_secret(self):
        secret = (
            os.getenv("NEXRA_AUTH_SECRET")
            or os.getenv("JWT_SECRET")
            or os.getenv("MYSQL_URL")
            or os.getenv("MYSQL_HOST")
            or os.getenv("POSTGRES_URL")
            or os.getenv("DATABASE_URL")
            or "nexra-dev-secret"
        )
        return secret.encode("utf-8")

    def _issue_auth_token(self, user_id: str):
        payload = {"user_id": user_id, "iat": now_iso()}
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        encoded = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
        signature = hmac.new(self._auth_secret(), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"nexra_{encoded}.{signature}"

    def _generate_verification_code(self):
        return f"{random.randint(0, 999999):06d}"

    def _parse_iso_datetime(self, value: str):
        normalized = safe_text(value).strip()
        if not normalized:
            return None
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    def _user_response(self, user):
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "createdAt": user.get("created_at"),
        }

    def get_dashboard(self):
        now_ts = datetime.utcnow().timestamp()
        if self._dashboard_cache and (now_ts - self._dashboard_cache["timestamp"]) < self._dashboard_cache_ttl_seconds:
            return self._dashboard_cache["payload"]
        if hasattr(self.state_store, "get_cached_public_dashboard"):
            cached_payload = self.state_store.get_cached_public_dashboard(self._dashboard_shared_cache_ttl_seconds)
            if cached_payload:
                self._dashboard_cache = {"timestamp": now_ts, "payload": cached_payload}
                return cached_payload
        if hasattr(self.state_store, "get_public_dashboard"):
            payload = self.state_store.get_public_dashboard()
            if hasattr(self.state_store, "set_cached_public_dashboard"):
                self.state_store.set_cached_public_dashboard(payload)
            self._dashboard_cache = {"timestamp": now_ts, "payload": payload}
            return payload
        raise ApiError(503, "Dashboard is warming up. Please retry in a moment.")

    def _deliver_verification_email_async(self, email, code, language):
        def runner():
            try:
                self.email_service.send_verification_code(email, code, language)
                log.info("Verification email queued successfully. email=%s", email)
            except Exception:
                log.exception("Async verification email delivery failed. email=%s", email)
                if hasattr(self.state_store, "delete_email_verification"):
                    self.state_store.delete_email_verification(email)

        thread = threading.Thread(target=runner, name="nexra-email-dispatch", daemon=True)
        thread.start()

    def request_register_code(self, payload):
        email = safe_text(payload.get("email")).strip().lower()
        language = safe_text(payload.get("language")).strip().lower() or "en"
        if not email:
            raise ApiError(400, "Invalid request: email is required.")
        if "@" not in email:
            raise ApiError(400, "Invalid request: email format is invalid.")
        if not hasattr(self.state_store, "find_auth_user_by_email"):
            raise ApiError(503, "Registration is warming up. Please retry in a moment.")
        existing = self.state_store.find_auth_user_by_email(email)
        if existing:
            raise ApiError(400, "This email is already registered.")
        if not self.email_service.is_configured():
            raise ApiError(503, "Email verification is not configured yet.")
        code = self._generate_verification_code()
        verification = {
            "email": email,
            "code": code,
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
            "created_at": now_iso(),
        }
        self.state_store.upsert_email_verification(verification)
        self._deliver_verification_email_async(email, code, language)
        return {"message": "Verification code is being sent."}

    def login(self, payload):
        email = safe_text(payload.get("email")).strip().lower()
        password = safe_text(payload.get("password"))
        if not email or not password:
            raise ApiError(400, "Invalid request: missing email or password.")
        if not hasattr(self.state_store, "find_auth_user_by_email"):
            raise ApiError(503, "Login is warming up. Please retry in a moment.")
        user = self.state_store.find_auth_user_by_email(email)
        if user is None or user.get("password") != password:
            raise ApiError(401, "Invalid email or password.")
        token = self._issue_auth_token(user["id"])
        return {"token": token, "user": self._user_response(user)}

    def register(self, payload):
        if not hasattr(self.state_store, "find_auth_user_by_email") or not hasattr(
            self.state_store, "find_email_verification"
        ):
            raise ApiError(503, "Registration is warming up. Please retry in a moment.")
        name = safe_text(payload.get("name")).strip()
        email = safe_text(payload.get("email")).strip().lower()
        password = safe_text(payload.get("password"))
        verification_code = safe_text(payload.get("verificationCode")).strip()
        if not email:
            raise ApiError(400, "Invalid request: email is required.")
        if not password:
            raise ApiError(400, "Invalid request: password is required.")
        if len(password) < 6:
            raise ApiError(400, "Invalid request: password must be at least 6 characters.")
        if not verification_code:
            raise ApiError(400, "Invalid request: verification code is required.")
        if not name:
            local_part = email.split("@", 1)[0].strip()
            name = local_part or "Nexra User"
        verification = self.state_store.find_email_verification(email)
        if verification is None:
            raise ApiError(400, "Please request an email verification code first.")
        expires_at = self._parse_iso_datetime(verification.get("expires_at"))
        if expires_at is None or expires_at < datetime.utcnow():
            self.state_store.delete_email_verification(email)
            raise ApiError(400, "Verification code expired. Please request a new one.")
        if verification.get("code") != verification_code:
            raise ApiError(400, "Verification code is invalid.")
        existing = self.state_store.find_auth_user_by_email(email)
        if existing:
            raise ApiError(400, "This email is already registered.")
        user_id = "user_" + uuid.uuid4().hex[:8]
        created_at = now_iso()
        user = {
            "id": user_id,
            "email": email,
            "password": password,
            "name": name,
            "role": "USER",
            "created_at": created_at,
        }
        self.state_store.upsert_auth_user(user)
        if hasattr(self.state_store, "increment_registered_user"):
            self.state_store.increment_registered_user(created_at[:10])
        self.state_store.delete_email_verification(email)
        token = self._issue_auth_token(user_id)
        return {"token": token, "user": self._user_response(user)}
