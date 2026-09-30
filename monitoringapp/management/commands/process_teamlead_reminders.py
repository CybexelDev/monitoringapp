import hashlib
import time
from urllib.parse import urlencode

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections, transaction
from django.db.utils import OperationalError
from django.urls import reverse
from django.utils import timezone

from monitoringapp.models import TeamLeadNotification, TeamLeadReminder


class Command(BaseCommand):
    help = "Create notifications for due, incomplete team lead reminders."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true", help="Keep checking until Ctrl+C.")
        parser.add_argument("--interval", type=int, default=15, help="Seconds between checks (default: 15).")

    def process_due(self):
        now = timezone.now()
        ids = list(TeamLeadReminder.objects.filter(
            is_completed=False,
            notified_at__isnull=True,
            remind_at__lte=now,
        ).order_by("remind_at", "pk").values_list("pk", flat=True)[:500])
        count = 0
        for reminder_id in ids:
            with transaction.atomic():
                # Claim within the transaction. A concurrent worker cannot claim it again.
                claimed = TeamLeadReminder.objects.filter(
                    pk=reminder_id,
                    is_completed=False,
                    notified_at__isnull=True,
                    remind_at__lte=now,
                ).update(notified_at=now)
                if not claimed:
                    continue
                reminder = TeamLeadReminder.objects.get(pk=reminder_id)
                event_local = timezone.localtime(reminder.event_at)
                signature = hashlib.sha256(
                    (reminder.remind_at.isoformat() + "|" + reminder.event_at.isoformat()).encode()
                ).hexdigest()[:32]
                event_text = event_local.strftime("%d %b %Y, %I:%M %p")
                message = f"{reminder.title} — {event_text}"
                if reminder.description:
                    message += "\n" + reminder.description
                url = reverse("teamlead_reminders") + "?" + urlencode({
                    "month": event_local.strftime("%Y-%m"),
                    "date": event_local.strftime("%Y-%m-%d"),
                })
                notification, created = TeamLeadNotification.objects.get_or_create(
                    event_key=f"teamlead-reminder:{reminder.pk}:{signature}",
                    defaults={
                        "recipient_id": reminder.owner_id,
                        "kind": "reminder",
                        "title": reminder.title,
                        "message": message,
                        "url": url,
                        "is_read": False,
                        "is_archived": False,
                    },
                )
                TeamLeadReminder.objects.filter(pk=reminder.pk).update(
                    notification=notification,
                )
                count += int(created)
        return count

    def handle(self, *args, **options):
        interval = options["interval"]
        if interval < 1:
            raise CommandError("--interval must be at least 1 second.")
        watching = options["watch"]
        if watching:
            self.stdout.write(f"Reminder worker running. Checking every {interval}s. Ctrl+C to stop.")
        try:
            while True:
                close_old_connections()
                try:
                    count = self.process_due()
                    if count or not watching:
                        self.stdout.write(self.style.SUCCESS(f"Created {count} reminder notification(s)."))
                except OperationalError as exc:
                    if not watching:
                        raise CommandError(str(exc)) from exc
                    self.stderr.write(f"Database unavailable; retrying next check: {exc}")
                finally:
                    close_old_connections()
                if not watching:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write("Reminder worker stopped.")
