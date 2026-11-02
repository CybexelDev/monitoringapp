
import logging

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import TeamLeadNotification, TeamLeadReminder


logger = logging.getLogger(__name__)


def process_teamlead_reminders(owner=None, limit=200):
    """Create one notification for each due Team Lead/Member reminder."""

    now = timezone.now()

    due = TeamLeadReminder.objects.filter(
        is_completed=False,
        notified_at__isnull=True,
        remind_at__lte=now,
    )

    if owner is not None:
        due = due.filter(owner_id=getattr(owner, "pk", owner))

    due_ids = list(
        due.order_by("remind_at", "pk")
        .values_list("pk", flat=True)[:limit]
    )

    created_count = 0

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
                    remind_at__lte=now,
                )
                .first()
            )

            if reminder is None:
                continue

            role = (
                str(reminder.owner.job_Position or "")
                .strip()
                .lower()
                .replace(" ", "_")
            )

            if role not in {"team_lead", "team_member"}:
                continue

            # Claim the reminder so another processor cannot
            # create a second notification for the same schedule.
            claimed = TeamLeadReminder.objects.filter(
                pk=reminder.pk,
                is_completed=False,
                notified_at__isnull=True,
                remind_at__lte=now,
            ).update(notified_at=now)

            if not claimed:
                continue

            event_time = timezone.localtime(
                reminder.event_at
            ).strftime("%d %b %Y, %I:%M %p")

            message = (
                f"Event: {event_time}\n"
                f"{reminder.description}"
            ).strip()

            destination = reverse(
                "teamlead_reminders"
                if role == "team_lead"
                else "teammember_reminders"
            )

            # A changed schedule gets a different event key.
            event_key = (
                f"teamlead-reminder:{reminder.pk}:"
                f"{reminder.updated_at.isoformat()}"
            )

            notification, added = (
                TeamLeadNotification.objects.get_or_create(
                    event_key=event_key,
                    defaults={
                        "recipient_id": reminder.owner_id,
                        "kind": "reminder",
                        "title": f"Reminder: {reminder.title}",
                        "message": message,
                        "url": destination,
                    },
                )
            )

            TeamLeadReminder.objects.filter(
                pk=reminder.pk
            ).update(notification_id=notification.pk)

            created_count += int(added)

    return created_count
