import json
import logging
import smtplib
from email.message import EmailMessage
from urllib import error, request

from app.config import load_mail_private_config


log = logging.getLogger("nexra-python")


class EmailService:
    def __init__(self):
        self._private = load_mail_private_config()

    def _value(self, key, default=""):
        import os

        value = self._private.get(key)
        if value is None or value == "":
            value = os.getenv(key)
        if value is None or value == "":
            value = default
        if isinstance(value, str):
            return value.strip()
        return value

    def _request_timeout_seconds(self):
        raw_value = self._value("EMAIL_HTTP_TIMEOUT_SECONDS", "6")
        try:
            timeout = float(raw_value)
        except (TypeError, ValueError):
            timeout = 6.0
        return max(2.0, timeout)

    def _resend_headers(self):
        api_key = self._value("RESEND_API_KEY")
        if not api_key:
            return None
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Nexra/1.0 (+https://nexracat.com)",
        }

    def is_configured(self):
        return bool(
            self._resend_headers()
            or (self._value("SMTP_HOST") and self._value("SMTP_USER") and self._value("SMTP_PASSWORD"))
        )

    def _message_content(self, code: str, language: str):
        if language == "zh":
            return {
                "subject": "Nexra ?????",
                "text": (
                    "???\n\n"
                    f"?? Nexra ???????{code}\n"
                    "????? 10 ??????\n\n"
                    "???????????????????"
                ),
            }
        return {
            "subject": "Your Nexra verification code",
            "text": (
                "Hello,\n\n"
                f"Your Nexra verification code is: {code}\n"
                "The code will expire in 10 minutes.\n\n"
                "If you did not request this, you can ignore this email."
            ),
        }

    def _send_with_resend(self, email: str, content: dict):
        headers = self._resend_headers()
        if not headers:
            return False
        from_address = self._value("RESEND_FROM") or self._value("SMTP_FROM") or "Nexra <onboarding@resend.dev>"
        payload = json.dumps(
            {
                "from": from_address,
                "to": [email],
                "subject": content["subject"],
                "text": content["text"],
            }
        ).encode("utf-8")
        req = request.Request("https://api.resend.com/emails", data=payload, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self._request_timeout_seconds()) as response:
                if response.status >= 300:
                    raise RuntimeError("Resend email delivery failed.")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace").strip()
            log.error("Resend email delivery failed. status=%s, details=%s", exc.code, details or exc.reason)
            message = details or exc.reason
            try:
                payload = json.loads(details) if details else {}
                message = payload.get("message") or message
            except json.JSONDecodeError:
                pass
            raise RuntimeError(f"Resend email delivery failed: {message}") from exc
        except Exception as exc:
            log.error("Resend email delivery request failed. email=%s error=%s", email, exc)
            raise RuntimeError(f"Resend email delivery failed: {exc}") from exc
        log.info("Verification email sent through Resend. email=%s", email)
        return True

    def _send_with_smtp(self, email: str, content: dict):
        from_address = self._value("SMTP_FROM") or self._value("SMTP_USER")
        host = self._value("SMTP_HOST")
        port = int(self._value("SMTP_PORT", "465"))
        username = self._value("SMTP_USER")
        password = self._value("SMTP_PASSWORD")
        use_tls = self._value("SMTP_USE_TLS", "true").strip().lower() != "false"
        timeout = self._request_timeout_seconds()

        message = EmailMessage()
        message["From"] = from_address
        message["To"] = email
        message["Subject"] = content["subject"]
        message.set_content(content["text"])

        if port == 465 and use_tls:
            with smtplib.SMTP_SSL(host, port, timeout=timeout) as server:
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=timeout) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.send_message(message)
        log.info("Verification email sent through SMTP. email=%s", email)

    def send_verification_code(self, email: str, code: str, language: str = "en"):
        if not self.is_configured():
            raise RuntimeError("Email delivery is not configured.")

        content = self._message_content(code, language)
        if self._send_with_resend(email, content):
            return
        self._send_with_smtp(email, content)
