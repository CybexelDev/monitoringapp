# Save as monitoringapp/notification_signals.py.
from django.db.models.signals import post_save, post_delete

from django.dispatch import receiver
from django.urls import reverse
from django.db import transaction
import logging

from .components.windows_push.delivery import send_windows_push

logger = logging.getLogger(__name__)
from .models import (
    Announcement, ProjectAssign, MorningReport, EveningReport,
    Task, Notepad, Knowledge, User, TeamLeadNotification,
)

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


def notify(recipient, kind, title, message, url='', event_key=None):
    if recipient is None:
        return

    fields = {
        "recipient": recipient,
        "kind": kind,
        "title": title,
        "message": message,
        "url": url,
    }

    if event_key:
        notification, created = TeamLeadNotification.objects.get_or_create(
            event_key=event_key,
            defaults=fields,
        )
        return notification

    return TeamLeadNotification.objects.create(**fields)




@receiver(post_save, sender=Announcement)
def announcement_changed(sender, instance, created, **kwargs):
    action = 'posted' if created else ('deleted' if not instance.is_active else 'updated')
    notify(instance.created_by, 'announcement', f'Announcement {action}',
           instance.title, reverse('teamlead_announcements'))


@receiver(post_save, sender=ProjectAssign)
def project_changed(sender, instance, created, **kwargs):
    action = 'assigned' if created else 'updated'
    notify(instance.assigned_by, 'project', f'Project {action}',
           instance.work_name, reverse('teamlead_project_assigning'))


@receiver(post_delete, sender=ProjectAssign)
def project_deleted(sender, instance, **kwargs):
    notify(instance.assigned_by, 'project', 'Project deleted', instance.work_name,
           reverse('teamlead_project_assigning'))


def report_received(instance, label):
    user = instance.user
    leads = User.objects.filter(team_id=user.team_id, job_Position__iexact='Team Lead')
    for lead in leads:
        notify(lead, 'report', f'{label} report received',
               f'{user.name} submitted a {label.lower()} report.',
               reverse('teamlead_reports'), f'report:{label}:{instance.pk}:{lead.pk}')


@receiver(post_save, sender=MorningReport)
def morning_report_received(sender, instance, created, **kwargs):
    if created:
        report_received(instance, 'Morning')


@receiver(post_save, sender=EveningReport)
def evening_report_received(sender, instance, created, **kwargs):
    if created:
        report_received(instance, 'Evening')


@receiver(post_save, sender=Task)
def task_changed(sender, instance, created, **kwargs):
    notify(instance.created_by, 'task', 'Task created' if created else 'Task updated',
           instance.title, reverse('teamlead_task'))


@receiver(post_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
    notify(instance.created_by, 'task', 'Task deleted', instance.title,
           reverse('teamlead_task'))


@receiver(post_save, sender=Notepad)
def note_changed(sender, instance, created, **kwargs):
    notify(instance.user, 'note', 'Note added' if created else 'Note edited',
           instance.title, reverse('teamlead_notepad'))


@receiver(post_delete, sender=Notepad)
def note_deleted(sender, instance, **kwargs):
    notify(instance.user, 'note', 'Note deleted', instance.title,
           reverse('teamlead_notepad'))


@receiver(post_save, sender=Knowledge)
def resource_changed(sender, instance, created, **kwargs):
    notify(instance.user, 'resource', 'Resource added' if created else 'Resource updated',
           instance.title, reverse('teamlead_repository'))


@receiver(post_delete, sender=Knowledge)
def resource_deleted(sender, instance, **kwargs):
    notify(instance.user, 'resource', 'Resource deleted', instance.title,
           reverse('teamlead_repository'))



@receiver(
    post_save,
    sender=TeamLeadNotification,
    dispatch_uid="cybexel_teamlead_windows_push_v1",
)
def teamlead_windows_push_created(sender, instance, created, **kwargs):
    if not created:
        return
        # Only important events should trigger Windows Push.
    WINDOWS_PUSH_KINDS = {
        "announcement",
        "report",
        "project",
        "task",
        "meeting",
        "reminder",
    }

    if instance.kind not in WINDOWS_PUSH_KINDS:
        return

    notification_id = instance.pk

    def deliver():
        import logging
        from .components.windows_push.delivery import send_windows_push

        logger = logging.getLogger(__name__)

        try:
            notification = (
                TeamLeadNotification.objects
                .select_related("recipient")
                .filter(pk=notification_id)
                .first()
            )

            if notification is None:
                return

            recipient = notification.recipient

            role = str(recipient.job_Position or "")
            role = role.strip().lower().replace(" ", "_")

            if role != "team_lead":
                return

            result = send_windows_push(
                recipient=recipient,
                portal="team_lead",
                title=notification.title,
                message=notification.message,
                url=notification.url or "/teamlead/notifications/",
                tag=f"teamlead-notification-{notification.pk}",
            )

            logger.info(
                "Team Lead Windows Push %s: %s",
                notification.pk,
                result,
            )

        except Exception:
            logger.exception(
                "Windows Push failed for notification %s",
                notification_id,
            )

    transaction.on_commit(deliver)
