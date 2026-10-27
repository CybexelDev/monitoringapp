"""Master Admin business-event notifications. Keep existing portal signals."""
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.urls import reverse
from . import models
import logging

logger = logging.getLogger(__name__)

EVENTS = {
    "User": ("user", "Employee", "master_admin_usermanagement"),
    "Department": ("department", "Department", "master_admin_departments"),
    "Designation": ("department", "Designation", "master_admin_departments"),
    "Team": ("team", "Team", "master_admin_teams"),
    "MorningReport": ("report", "Morning report", "master_admin_reports"),
    "EveningReport": ("report", "Evening report", "master_admin_reports"),
    "Task": ("task", "Task", "master_admin_tasks"),
    "ProjectAssign": ("project", "Project", "master_admin_projects"),
    "Announcement": ("announcement", "Announcement", "master_admin_announcements"),
    "Knowledge": ("resource", "Team resource", "master_admin_repository"),
    "AdminKnowledge": ("resource", "Admin resource", "master_admin_repository"),
    "GoogleMeeting": ("meeting", "Meeting", "master_admin_google_meet"),
    "AccountsIncome": ("income", "Income", "master_admin_accounts_income"),
    "AccountsExpense": ("expense", "Expense", "master_admin_accounts_expenses"),
    "AccountsSale": ("sale", "Sale", "master_admin_accounts_sales"),
    "AccountsSalePayment": ("sale", "Sale payment", "master_admin_accounts_sales"),
}


def _emit(sender, instance, action, **kwargs):
    if kwargs.get("raw"):
        return
    if sender.__name__ == "User" and action == "updated":
        fields = kwargs.get("update_fields")
        if fields and set(fields) <= {"last_activity", "last_login_time", "last_logout_time"}:
            return
    kind, label, route = EVENTS[sender.__name__]
    name = next((str(getattr(instance, f)) for f in ("title", "work_name", "purpose", "name", "reference")
                 if getattr(instance, f, None)), f"Record #{instance.pk}")
    # Snapshot before deletion; do not expose passwords, private notes, or financial values.
    title, message, url = f"{label} {action}", name[:500], reverse(route)
    event = uuid4().hex

    def deliver():
        from .components.windows_push.delivery import send_windows_push
        from .master_chat_identity import master_chat_user

        recipients = list(
            get_user_model().objects.filter(
                is_active=True,
                is_superuser=True
            )
        )

        # Existing Master Admin in-app notifications
        models.AdminNotification.objects.bulk_create([
            models.AdminNotification(
                auth_owner_id=account.pk,
                kind=kind,
                title=title,
                message=message,
                url=url,
                event_key=f"master-event:{event}:{account.pk}",
            )
            for account in recipients
        ])

        # Windows Push for important business events
        PUSH_KINDS = {
            "announcement",
            "report",
            "task",
            "project",
            "meeting",
        }

        if kind not in PUSH_KINDS:
            return

        for account in recipients:
            try:
                person = master_chat_user(account, create=False)

                if person is None:
                    continue

                result = send_windows_push(
                    recipient=person,
                    portal="master_admin",
                    title=title,
                    message=message,
                    url=url,
                    tag=f"master-{event}-{account.pk}",
                )

                logger.info(
                    "Master Admin Windows Push: account=%s result=%s",
                    account.pk,
                    result,
                )

            except Exception:
                logger.exception(
                    "Master Admin Windows Push failed: account=%s",
                    account.pk,
                )

    transaction.on_commit(deliver)


def _saved(sender, instance, created, **kwargs):
    _emit(sender, instance, "created" if created else "updated", **kwargs)


def _deleted(sender, instance, **kwargs):
    _emit(sender, instance, "deleted", **kwargs)


for model_name in EVENTS:
    model = getattr(models, model_name)
    post_save.connect(_saved, sender=model, dispatch_uid=f"master-notification-save-{model_name}")
    post_delete.connect(_deleted, sender=model, dispatch_uid=f"master-notification-delete-{model_name}")
