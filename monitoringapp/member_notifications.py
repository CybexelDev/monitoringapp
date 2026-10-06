"""Member notification delivery using the existing notification/reminder tables."""
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from .models import (
    Announcement, AnnouncementRecipient, ProjectAssign, Task, User, GoogleMeeting,
    ReportDateSchedule, ReportDefaultSchedule, TeamReportLeave,
    MorningReport, EveningReport, TeamLeadNotification, TeamLeadReminder,
)


def _is_member(user):
    return user is not None and (user.job_Position or '').strip().lower() == 'team member'


def _notify(user, kind, title, message, route, key=None):
    if not _is_member(user):
        return
    fields = dict(recipient=user, kind=kind, title=title[:180], message=message, url=reverse(route))
    if key:
        return TeamLeadNotification.objects.get_or_create(event_key=key, defaults=fields)[0]
    return TeamLeadNotification.objects.create(**fields)


def sync_member_notifications(user):
    """Catch bulk-created recipients and overdue reminders without duplicate records."""
    sync_member_meetings(user)
    sync_member_report_windows(user)
    for row in AnnouncementRecipient.objects.filter(
        recipient=user, announcement__is_active=True,
        announcement__created_by__job_Position__iexact='Team Lead',
    ).select_related('announcement'):
        ann = row.announcement
        _notify(user, 'announcement', 'New announcement', ann.title or ann.message,
                'teammember_announcements', f'member-announcement:{ann.pk}:{user.pk}')
    for project in ProjectAssign.objects.filter(assign_to=user):
        _notify(user, 'project', 'Project assigned', project.work_name,
                'teammember_project', f'member-project:{project.pk}:{user.pk}')
    for task in Task.objects.filter(assigned_to=user).exclude(created_by=user):
        _notify(user, 'task', 'Task assigned', task.title,
                'teammember_task', f'member-task:{task.pk}:{user.pk}')
    # Small transactions keep completion/rescheduling and due delivery coordinated.
    due_ids = list(TeamLeadReminder.objects.filter(
        owner=user, is_completed=False, remind_at__lte=timezone.now(),
        notification__isnull=True,
    ).values_list('pk', flat=True))
    for pk in due_ids:
        with transaction.atomic():
            reminder = TeamLeadReminder.objects.select_for_update().filter(
                pk=pk, owner=user, is_completed=False,
                remind_at__lte=timezone.now(), notification__isnull=True,
            ).first()
            if reminder is None:
                continue
            local_event = timezone.localtime(reminder.event_at)
            key = f'member-reminder:{reminder.pk}:{reminder.remind_at.isoformat()}'
            notification = _notify(user, 'reminder', 'Reminder: ' + reminder.title,
                reminder.description or local_event.strftime('%d %b %Y, %I:%M %p'),
                'teammember_reminders', key)
            if notification is not None:
                notification.url = reverse('teammember_reminders') + local_event.strftime('?month=%Y-%m&date=%Y-%m-%d')
                notification.save(update_fields=['url'])
                TeamLeadReminder.objects.filter(pk=pk, owner=user).update(
                    notification=notification, notified_at=timezone.now())


@receiver(post_save, sender=ProjectAssign, dispatch_uid='member_project_notification')
def member_project_changed(sender, instance, created, **kwargs):
    _notify(instance.assign_to, 'project', 'Project assigned' if created else 'Project updated',
            instance.work_name, 'teammember_project',
            f'member-project:{instance.pk}:{instance.assign_to_id}' if created else None)


@receiver(post_delete, sender=ProjectAssign, dispatch_uid='member_project_deleted_notification')
def member_project_deleted(sender, instance, **kwargs):
    _notify(instance.assign_to, 'project', 'Project deleted', instance.work_name, 'teammember_project')


@receiver(post_save, sender=Task, dispatch_uid='member_assigned_task_notification')
def member_task_changed(sender, instance, created, **kwargs):
    # Existing signals already notify the creator, including personal member tasks.
    if instance.assigned_to_id and instance.assigned_to_id != instance.created_by_id:
        _notify(instance.assigned_to, 'task', 'Task assigned' if created else 'Task updated',
                instance.title, 'teammember_task',
                f'member-task:{instance.pk}:{instance.assigned_to_id}' if created else None)


@receiver(post_delete, sender=Task, dispatch_uid='member_assigned_task_deleted_notification')
def member_task_deleted(sender, instance, **kwargs):
    if instance.assigned_to_id and instance.assigned_to_id != instance.created_by_id:
        _notify(instance.assigned_to, 'task', 'Task deleted', instance.title, 'teammember_task')


@receiver(post_save, sender=Announcement, dispatch_uid='member_announcement_updated_notification')
def member_announcement_changed(sender, instance, created, **kwargs):
    if not created:
        for row in instance.recipients.select_related('recipient'):
            _notify(row.recipient, 'announcement', 'Announcement updated' if instance.is_active else 'Announcement removed',
                    instance.title, 'teammember_announcements')


@receiver(post_save, sender=MorningReport, dispatch_uid='member_morning_report_notification')
def member_morning_report(sender, instance, created, **kwargs):
    if created:
        _notify(instance.user, 'report', 'Morning report submitted', 'Your morning report was saved.',
                'teammember_reports', f'member-report:morning:{instance.pk}:{instance.user_id}')


@receiver(post_save, sender=EveningReport, dispatch_uid='member_evening_report_notification')
def member_evening_report(sender, instance, created, **kwargs):
    if created:
        _notify(instance.user, 'report', 'Evening report submitted', 'Your evening report was saved.',
                'teammember_reports', f'member-report:evening:{instance.pk}:{instance.user_id}')


# Polling on every member page creates each current meeting/window alert once.
def sync_member_meetings(user):
    import hashlib
    now = timezone.now()
    for meeting in GoogleMeeting.objects.filter(participants=user).distinct():
        if meeting.meeting_end_datetime <= now:
            continue
        version = "|".join((meeting.purpose, str(meeting.date), str(meeting.time), meeting.meeting_link))
        digest = hashlib.sha256(version.encode("utf-8")).hexdigest()[:24]
        _notify(user, "meeting", "Google Meet scheduled / updated",
                f"{meeting.purpose} — {meeting.date:%d %b %Y}, {meeting.time:%I:%M %p}",
                "teammember_google_meet", f"member-meeting:{meeting.pk}:{user.pk}:{digest}")


def sync_member_report_windows(user):
    if not user.team_id:
        return
    lead = User.objects.filter(team_id=user.team_id, job_Position__iexact="Team Lead").first()
    if lead is None:
        return
    current = timezone.localtime()
    today = current.date()
    leave = TeamReportLeave.objects.filter(team_lead=lead, date=today).first()
    for kind in ("morning", "evening"):
        if leave and getattr(leave, kind + "_leave"):
            continue
        schedule = ReportDateSchedule.objects.filter(team_lead=lead, date=today, report_type=kind).first()
        if schedule is None:
            kinds = ("saturday", "regular") if today.weekday() == 5 else ("regular",)
            for day_kind in kinds:
                schedule = ReportDefaultSchedule.objects.filter(
                    team_lead=lead, effective_from__lte=today,
                    day_kind=day_kind, report_type=kind,
                ).order_by("-effective_from", "-id").first()
                if schedule is not None:
                    break
        if schedule is None or not schedule.is_active:
            continue
        report_model = MorningReport if kind == "morning" else EveningReport
        if report_model.objects.filter(user=user, created_at__date=today).exists():
            continue
        if schedule.start_time <= current.time() <= schedule.end_time:
            _notify(user, "schedule", kind.capitalize() + " report is open",
                    f"Submit your {kind} report between {schedule.start_time:%I:%M %p} and {schedule.end_time:%I:%M %p}.",
                    "teammember_dashboard", f"member-window:{user.pk}:{today}:{kind}")

from django.db.models.signals import pre_delete, m2m_changed


@receiver(pre_delete, sender=GoogleMeeting, dispatch_uid='member_meeting_deleted_notification')
def member_meeting_deleted(sender, instance, **kwargs):
    for user in instance.participants.all():
        _notify(user, 'meeting', 'Google Meet cancelled', instance.purpose,
                'teammember_google_meet', f'member-meeting-cancelled:{instance.pk}:{user.pk}')


@receiver(m2m_changed, sender=GoogleMeeting.participants.through,
          dispatch_uid='member_meeting_invitation_removed')
def member_meeting_invitation_removed(sender, instance, action, reverse, pk_set, **kwargs):
    if reverse or action not in {'pre_remove', 'pre_clear'}:
        return
    removed = instance.participants.all()
    if action == 'pre_remove':
        removed = removed.filter(pk__in=pk_set or ())
    for user in removed:
        _notify(user, 'meeting', 'Meeting invitation removed', instance.purpose,
                'teammember_google_meet')

@receiver(post_save, sender=TeamLeadReminder, dispatch_uid='member_reminder_operation_notification')
def member_reminder_operation(sender, instance, created, **kwargs):
    title = 'Reminder created' if created else ('Reminder completed' if instance.is_completed else 'Reminder updated / reopened')
    _notify(instance.owner, 'reminder', title, instance.title, 'teammember_reminders')


@receiver(post_delete, sender=TeamLeadReminder, dispatch_uid='member_reminder_deleted_notification')
def member_reminder_deleted(sender, instance, **kwargs):
    _notify(instance.owner, 'reminder', 'Reminder deleted', instance.title, 'teammember_reminders')
