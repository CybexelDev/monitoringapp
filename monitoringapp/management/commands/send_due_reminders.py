
from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from monitoringapp.models import (
    TeamLeadReminder,
    TeamLeadNotification,
)


class Command(BaseCommand):
    help = "Send due Team Lead reminder notifications."

    def handle(self, *args, **options):
        now = timezone.now()

        due_ids = list(
            TeamLeadReminder.objects.filter(
                is_completed=False,
                notified_at__isnull=True,
                remind_at__lte=now,
                owner__job_Position__iexact="Team Lead",
            ).values_list("id", flat=True)
        )

        sent_count = 0

        for reminder_id in due_ids:
            with transaction.atomic():
                reminder = (
                    TeamLeadReminder.objects
                    .select_for_update()
                    .select_related("owner")
                    .filter(
                        pk=reminder_id,
                        is_completed=False,
                        notified_at__isnull=True,
                        remind_at__lte=timezone.now(),
                    )
                    .first()
                )

                if reminder is None:
                    continue

                event_time = timezone.localtime(
                    reminder.event_at
                ).strftime("%d %b %Y, %I:%M %p")

                # A changed schedule can trigger a new reminder.
                event_key = (
                    f"teamlead-reminder:"
                    f"{reminder.pk}:"
                    f"{int(reminder.remind_at.timestamp())}"
                )

                notification, created = (
                    TeamLeadNotification.objects.get_or_create(
                        event_key=event_key,
                        defaults={
                            "recipient": reminder.owner,
                            "kind": "reminder",
                            "title": f"Reminder: {reminder.title}",
                            "message": (
                                f"Event: {event_time}\n"
                                f"{reminder.description or ''}"
                            ).strip(),
                            "url": reverse("teamlead_reminders"),
                        },
                    )
                )

                reminder.notification = notification
                reminder.notified_at = timezone.now()

                reminder.save(
                    update_fields=[
                        "notification",
                        "notified_at",
                        "updated_at",
                    ]
                )

                if created:
                    sent_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Reminder notifications created: {sent_count}"
            )
        )
