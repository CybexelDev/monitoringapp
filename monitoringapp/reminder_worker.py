"""
Background worker that processes due reminders on the server itself,
so reminders do not wait for someone to open a portal page.

It runs inside the web server process (Daphne) and starts ONLY when the
environment variable RUN_REMINDER_WORKER is set to 1 (set it on Render).
On your own computer (variable not set) nothing starts.

It reuses the existing reminder code:
  - process_teamlead_reminders()  -> Team Lead and Team Member reminders
  - _process_admin_reminders()    -> Admin and Master Admin reminders
Those functions already protect against duplicate notifications.
"""
import logging
import os
import threading
import time

from django.db import connections

logger = logging.getLogger(__name__)

_started = False
_lock = threading.Lock()


def _run_once():
    # Imported here so this module can be imported before the app is fully loaded.
    from monitoringapp.reminder_processing import process_teamlead_reminders
    from monitoringapp.views import _process_admin_reminders

    created = {}
    for name, func in (
        ("team_lead_member", process_teamlead_reminders),
        ("admin", _process_admin_reminders),
    ):
        try:
            created[name] = func()
        except Exception:
            logger.exception("Reminder worker: %s processing failed", name)
        finally:
            # Release this thread's database connection after every step.
            connections.close_all()
    return created


def _loop(interval):
    logger.info("Reminder worker started (every %s seconds)", interval)
    time.sleep(15)  # let the server finish starting first
    while True:
        try:
            created = _run_once()
            if any(created.values()):
                logger.info("Reminder worker created notifications: %s", created)
        except Exception:
            logger.exception("Reminder worker loop error")
        time.sleep(interval)


def start_reminder_worker():
    if os.environ.get("RUN_REMINDER_WORKER") != "1":
        return

    global _started
    with _lock:
        if _started:
            return
        _started = True

    try:
        interval = max(10, int(os.environ.get("REMINDER_WORKER_INTERVAL", "30")))
    except ValueError:
        interval = 30

    thread = threading.Thread(
        target=_loop,
        args=(interval,),
        name="reminder-worker",
        daemon=True,
    )
    thread.start()