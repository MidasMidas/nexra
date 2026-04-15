import logging
import os
import threading
import time

from app.common.utils import now_iso


log = logging.getLogger("nexra-python")


class SyncManager:
    def __init__(self, app):
        self.app = app
        self.enabled = bool(app.config["skillSync"].get("enabled", True))
        self.target_count = int(app.config["skillSync"].get("targetCount", 3000))
        self.initial_delay = int(app.config["skillSync"].get("initialDelaySeconds", 900))
        self.interval = int(app.config["skillSync"].get("intervalSeconds", 43200))
        self.in_progress = False
        self.last_attempt_at = None
        self.last_success_at = None
        self.last_error = None
        self.last_imported_count = 0
        self._thread = None

    def start_scheduler(self):
        if not self.enabled:
            log.info("Scheduled skill sync disabled in config.")
            return
        if os.getenv("VERCEL") == "1":
            log.info("Scheduled skill sync disabled in Vercel serverless runtime.")
            return

        def loop():
            time.sleep(self.initial_delay)
            while True:
                try:
                    self.sync_now(trigger="scheduled")
                except Exception:
                    log.exception("Unexpected error during scheduled skill sync.")
                time.sleep(self.interval)

        self._thread = threading.Thread(target=loop, daemon=True, name="skill-sync")
        self._thread.start()
        log.info(
            "Skill sync scheduler started. initialDelaySeconds=%s intervalSeconds=%s",
            self.initial_delay,
            self.interval,
        )

    def status(self):
        return {
            "enabled": self.enabled,
            "inProgress": self.in_progress,
            "dataFile": str(self.app.skill_data_file),
            "targetCount": self.target_count,
            "currentImportedCount": self.app.imported_skill_count(),
            "lastAttemptAt": self.last_attempt_at,
            "lastSuccessAt": self.last_success_at,
            "lastError": self.last_error,
            "lastImportedCount": self.last_imported_count,
        }

    def sync_now(self, trigger: str = "manual"):
        self.last_attempt_at = now_iso()
        if not self.enabled:
            self.last_imported_count = self.app.imported_skill_count()
            log.info("Skill sync skipped because it is disabled. trigger=%s", trigger)
            return self.status()
        if self.in_progress:
            log.info("Skill sync skipped because another sync is already running. trigger=%s", trigger)
            return self.status()

        self.in_progress = True
        self.last_error = None
        log.info("Skill sync started. trigger=%s dataFile=%s", trigger, self.app.skill_data_file)
        try:
            imported_skills = self.app.read_skill_seed_file()
            self.app.replace_imported_skills(imported_skills)
            self.last_imported_count = len(imported_skills)
            self.last_success_at = now_iso()
            log.info("Skill sync completed. trigger=%s importedCount=%s", trigger, self.last_imported_count)
        except Exception as exc:
            self.last_error = str(exc)
            log.exception("Skill sync failed. trigger=%s", trigger)
        finally:
            self.in_progress = False
        return self.status()
