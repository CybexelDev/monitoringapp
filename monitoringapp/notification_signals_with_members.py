# Save as monitoringapp/notification_signals.py.
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse

from .models import (
    Announcement, ProjectAssign, MorningReport, EveningReport,
    Task, Notepad, Knowledge, User, TeamLeadNotification,
)


def notify(recipient, kind, title, message, url='', event_key=None):
    if recipient is None:
        return
    if (recipient.job_Position or '').strip().lower() == 'team member':
        routes = {'announcement':'teammember_announcements', 'project':'teammember_project',
                  'task':'teammember_task', 'note':'teammember_notepad',
                  'resource':'teammember_repository', 'report':'teammember_reports',
                  'reminder':'teammember_reminders'}
        if kind in routes:
            url = reverse(routes[kind])
    fields = dict(recipient=recipient, kind=kind, title=title, message=message, url=url)
    if event_key:
        TeamLeadNotification.objects.get_or_create(event_key=event_key, defaults=fields)
    else:
        TeamLeadNotification.objects.create(**fields)


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

# Load the Member receivers alongside the existing Lead receivers.
from . import member_notifications
