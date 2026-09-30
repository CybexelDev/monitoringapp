# Save as monitoringapp/notification_seen.py.
from django.urls import reverse
from .models import Announcement, ProjectAssign, TeamLeadNotification


def notify_announcements_seen(member, announcement_ids):
    for announcement in Announcement.objects.filter(pk__in=announcement_ids).select_related('created_by'):
        TeamLeadNotification.objects.get_or_create(
            event_key=f'announcement-seen:{announcement.pk}:{member.pk}',
            defaults={
                'recipient': announcement.created_by,
                'kind': 'announcement',
                'title': 'Announcement seen',
                'message': f'{member.name} saw your announcement: {announcement.title}',
                'url': reverse('teamlead_announcements'),
            },
        )


def notify_projects_opened(member):
    # Called only when the member actually opens the assigned projects page.
    for project in ProjectAssign.objects.filter(assign_to=member).select_related('assigned_by'):
        TeamLeadNotification.objects.get_or_create(
            event_key=f'project-opened:{project.pk}:{member.pk}',
            defaults={
                'recipient': project.assigned_by,
                'kind': 'project',
                'title': 'Project list opened',
                'message': f'{member.name} opened the page containing {project.work_name}.',
                'url': reverse('teamlead_project_assigning'),
            },
        )
