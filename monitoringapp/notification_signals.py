# # Save as monitoringapp/notification_signals.py.
# from django.db.models.signals import post_save, post_delete

# from django.dispatch import receiver
# from django.urls import reverse
# from django.db import transaction
# import logging

# from .components.windows_push.delivery import send_windows_push

# logger = logging.getLogger(__name__)
# from .models import (
#     Announcement, ProjectAssign, MorningReport, EveningReport,
#     Task, Notepad, Knowledge, User, TeamLeadNotification,
# )

# from django.db import transaction
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver


# def notify(recipient, kind, title, message, url='', event_key=None):
#     if recipient is None:
#         return

#     fields = {
#         "recipient": recipient,
#         "kind": kind,
#         "title": title,
#         "message": message,
#         "url": url,
#     }

#     if event_key:
#         notification, created = TeamLeadNotification.objects.get_or_create(
#             event_key=event_key,
#             defaults=fields,
#         )
#         return notification

#     return TeamLeadNotification.objects.create(**fields)




# @receiver(post_save, sender=Announcement)
# def announcement_changed(sender, instance, created, **kwargs):
#     action = 'posted' if created else ('deleted' if not instance.is_active else 'updated')
#     notify(instance.created_by, 'announcement', f'Announcement {action}',
#            instance.title, reverse('teamlead_announcements'))


# @receiver(post_save, sender=ProjectAssign)
# def project_changed(sender, instance, created, **kwargs):
#     action = 'assigned' if created else 'updated'
#     notify(instance.assigned_by, 'project', f'Project {action}',
#            instance.work_name, reverse('teamlead_project_assigning'))


# @receiver(post_delete, sender=ProjectAssign)
# def project_deleted(sender, instance, **kwargs):
#     notify(instance.assigned_by, 'project', 'Project deleted', instance.work_name,
#            reverse('teamlead_project_assigning'))


# def report_received(instance, label):
#     user = instance.user
#     leads = User.objects.filter(team_id=user.team_id, job_Position__iexact='Team Lead')
#     for lead in leads:
#         notify(lead, 'report', f'{label} report received',
#                f'{user.name} submitted a {label.lower()} report.',
#                reverse('teamlead_reports'), f'report:{label}:{instance.pk}:{lead.pk}')


# @receiver(post_save, sender=MorningReport)
# def morning_report_received(sender, instance, created, **kwargs):
#     if created:
#         report_received(instance, 'Morning')


# @receiver(post_save, sender=EveningReport)
# def evening_report_received(sender, instance, created, **kwargs):
#     if created:
#         report_received(instance, 'Evening')


# @receiver(post_save, sender=Task)
# def task_changed(sender, instance, created, **kwargs):
#     notify(instance.created_by, 'task', 'Task created' if created else 'Task updated',
#            instance.title, reverse('teamlead_task'))


# @receiver(post_delete, sender=Task)
# def task_deleted(sender, instance, **kwargs):
#     notify(instance.created_by, 'task', 'Task deleted', instance.title,
#            reverse('teamlead_task'))


# @receiver(post_save, sender=Notepad)
# def note_changed(sender, instance, created, **kwargs):
#     notify(instance.user, 'note', 'Note added' if created else 'Note edited',
#            instance.title, reverse('teamlead_notepad'))


# @receiver(post_delete, sender=Notepad)
# def note_deleted(sender, instance, **kwargs):
#     notify(instance.user, 'note', 'Note deleted', instance.title,
#            reverse('teamlead_notepad'))


# @receiver(post_save, sender=Knowledge)
# def resource_changed(sender, instance, created, **kwargs):
#     notify(instance.user, 'resource', 'Resource added' if created else 'Resource updated',
#            instance.title, reverse('teamlead_repository'))


# @receiver(post_delete, sender=Knowledge)
# def resource_deleted(sender, instance, **kwargs):
#     notify(instance.user, 'resource', 'Resource deleted', instance.title,
#            reverse('teamlead_repository'))



# @receiver(
#     post_save,
#     sender=TeamLeadNotification,
#     dispatch_uid="cybexel_teamlead_windows_push_v1",
# )
# def teamlead_windows_push_created(sender, instance, created, **kwargs):
#     if not created:
#         return
#         # Only important events should trigger Windows Push.
#     WINDOWS_PUSH_KINDS = {
#         "announcement",
#         "report",
#         "project",
#         "task",
#         "meeting",
#         "reminder",
#     }

#     if instance.kind not in WINDOWS_PUSH_KINDS:
#         return

#     notification_id = instance.pk

#     def deliver():
#         import logging
#         from .components.windows_push.delivery import send_windows_push

#         logger = logging.getLogger(__name__)

#         try:
#             notification = (
#                 TeamLeadNotification.objects
#                 .select_related("recipient")
#                 .filter(pk=notification_id)
#                 .first()
#             )

#             if notification is None:
#                 return

#             recipient = notification.recipient

#             role = str(recipient.job_Position or "")
#             role = role.strip().lower().replace(" ", "_")

#             if role != "team_lead":
#                 return

#             result = send_windows_push(
#                 recipient=recipient,
#                 portal="team_lead",
#                 title=notification.title,
#                 message=notification.message,
#                 url=notification.url or "/teamlead/notifications/",
#                 tag=f"teamlead-notification-{notification.pk}",
#             )

#             logger.info(
#                 "Team Lead Windows Push %s: %s",
#                 notification.pk,
#                 result,
#             )

#         except Exception:
#             logger.exception(
#                 "Windows Push failed for notification %s",
#                 notification_id,
#             )

#     transaction.on_commit(deliver)

# # ================================================================
# # TEAM MEMBER WEB PUSH — additive receiver only.
# # Leave the existing Team Lead receiver above unchanged.
# # Notifications must be created for Team Member recipients elsewhere.
# # ================================================================
# @receiver(
#     post_save,
#     sender=TeamLeadNotification,
#     dispatch_uid="cybexel_teammember_windows_push_v1",
# )
# def teammember_windows_push_created(sender, instance, created, **kwargs):
#     if not created or instance.kind not in {
#         "announcement", "project", "task", "meeting", "reminder", "report"
#     }:
#         return

#     if not instance.recipient_id:
#         return

#     role = str(instance.recipient.job_Position or "").strip().lower().replace(" ", "_")
#     if role != "team_member":
#         return

#     notification_id = instance.pk

#     def deliver_to_member():
#         try:
#             notification = (
#                 TeamLeadNotification.objects.select_related("recipient")
#                 .filter(pk=notification_id).first()
#             )
#             if notification is None:
#                 return
#             recipient = notification.recipient
#             role_now = str(recipient.job_Position or "").strip().lower().replace(" ", "_")
#             if role_now != "team_member":
#                 return

#             # Never open Team Lead pages from Team Member push notifications.
#             member_route = {
#                 "announcement": "teammember_announcements",
#                 "project": "teammember_project",
#                 "task": "teammember_task",
#                 "meeting": "teammember_google_meet",
#                 "reminder": "teammember_reminders",
#                 "report": "teammember_reports",
#             }.get(notification.kind, "teammember_notifications")
#             try:
#                 destination = reverse(member_route)
#             except Exception:
#                 destination = reverse("teammember_notifications")

#             result = send_windows_push(
#                 recipient=recipient,
#                 portal="team_member",
#                 title=notification.title,
#                 message=notification.message,
#                 url=destination,
#                 tag=f"teammember-notification-{notification.pk}",
#             )
#             logger.info("Team Member Windows Push %s: %s", notification.pk, result)
#         except Exception:
#             logger.exception("Team Member Windows Push failed for notification %s", notification_id)

#     transaction.on_commit(deliver_to_member)



# # ================================================
# # TEAM MEMBER - GOOGLE MEET WINDOWS PUSH
# # ================================================

# from django.db.models.signals import m2m_changed
# from .models import GoogleMeeting


# @receiver(
#     m2m_changed,
#     sender=GoogleMeeting.participants.through,
#     dispatch_uid="teammember_google_meet_push_v1",
# )
# def teammember_google_meet_push(
#     sender, instance, action, reverse, pk_set, **kwargs
# ):
#     if action != "post_add" or reverse or not pk_set:
#         return

#     # Master Admin already has its own notification flow.
#     if instance.is_master_admin_meeting:
#         return

#     meeting_id = instance.pk
#     member_ids = list(
#         User.objects.filter(
#             pk__in=pk_set,
#             job_Position__iexact="Team Member",
#         ).values_list("pk", flat=True)
#     )

#     def deliver():
#         try:
#             meeting = GoogleMeeting.objects.filter(
#                 pk=meeting_id
#             ).first()

#             if meeting is None:
#                 return

#             for member in User.objects.filter(pk__in=member_ids):
#                 # Check that the user is still invited.
#                 if not meeting.participants.filter(
#                     pk=member.pk
#                 ).exists():
#                     continue

#                 notify(
#                     recipient=member,
#                     kind="meeting",
#                     title="New Google Meet Scheduled",
#                     message=(
#                         f"{meeting.purpose} - "
#                         f"{meeting.date:%d %b %Y} "
#                         f"at {meeting.time:%I:%M %p}"
#                     ),
#                     url=reverse("teammember_google_meet"),
#                     event_key=(
#                         f"member-meeting-invite:"
#                         f"{meeting.pk}:{member.pk}"
#                     ),
#                 )

#         except Exception:
#             logger.exception(
#                 "Team Member Google Meet notification failed"
#             )

#     transaction.on_commit(deliver)


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

# ================================================================
# TEAM MEMBER WEB PUSH — additive receiver only.
# Leave the existing Team Lead receiver above unchanged.
# Notifications must be created for Team Member recipients elsewhere.
# ================================================================
@receiver(
    post_save,
    sender=TeamLeadNotification,
    dispatch_uid="cybexel_teammember_windows_push_v1",
)
def teammember_windows_push_created(sender, instance, created, **kwargs):
    if not created or instance.kind not in {
        "announcement", "project", "task", "meeting", "reminder", "report"
    }:
        return

    if not instance.recipient_id:
        return

    role = str(instance.recipient.job_Position or "").strip().lower().replace(" ", "_")
    if role != "team_member":
        return

    notification_id = instance.pk

    def deliver_to_member():
        try:
            notification = (
                TeamLeadNotification.objects.select_related("recipient")
                .filter(pk=notification_id).first()
            )
            if notification is None:
                return
            recipient = notification.recipient
            role_now = str(recipient.job_Position or "").strip().lower().replace(" ", "_")
            if role_now != "team_member":
                return

            # Never open Team Lead pages from Team Member push notifications.
            member_route = {
                "announcement": "teammember_announcements",
                "project": "teammember_project",
                "task": "teammember_task",
                "meeting": "teammember_google_meet",
                "reminder": "teammember_reminders",
                "report": "teammember_reports",
            }.get(notification.kind, "teammember_notifications")
            try:
                destination = reverse(member_route)
            except Exception:
                destination = reverse("teammember_notifications")

            result = send_windows_push(
                recipient=recipient,
                portal="team_member",
                title=notification.title,
                message=notification.message,
                url=destination,
                tag=f"teammember-notification-{notification.pk}",
            )
            logger.info("Team Member Windows Push %s: %s", notification.pk, result)
        except Exception:
            logger.exception("Team Member Windows Push failed for notification %s", notification_id)

    transaction.on_commit(deliver_to_member)



# ================================================
# TEAM MEMBER - GOOGLE MEET WINDOWS PUSH
# ================================================

from django.db.models.signals import m2m_changed
from .models import GoogleMeeting


@receiver(
    m2m_changed,
    sender=GoogleMeeting.participants.through,
    dispatch_uid="teammember_google_meet_push_v1",
)
def teammember_google_meet_push(
    sender, instance, action, reverse, pk_set, **kwargs
):
    if action != "post_add" or reverse or not pk_set:
        return

    # Master Admin already has its own notification flow.
    if instance.is_master_admin_meeting:
        return

    meeting_id = instance.pk
    member_ids = list(
        User.objects.filter(
            pk__in=pk_set,
            job_Position__iexact="Team Member",
        ).values_list("pk", flat=True)
    )

    def deliver():
        try:
            meeting = GoogleMeeting.objects.filter(
                pk=meeting_id
            ).first()

            if meeting is None:
                return

            for member in User.objects.filter(pk__in=member_ids):
                # Check that the user is still invited.
                if not meeting.participants.filter(
                    pk=member.pk
                ).exists():
                    continue

                notify(
                    recipient=member,
                    kind="meeting",
                    title="New Google Meet Scheduled",
                    message=(
                        f"{meeting.purpose} - "
                        f"{meeting.date:%d %b %Y} "
                        f"at {meeting.time:%I:%M %p}"
                    ),
                    url=reverse("teammember_google_meet"),
                    event_key=(
                        f"member-meeting-invite:"
                        f"{meeting.pk}:{member.pk}"
                    ),
                )

        except Exception:
            logger.exception(
                "Team Member Google Meet notification failed"
            )

    transaction.on_commit(deliver)


# Admin in-app feed events; does not alter existing Team Lead/Member signals or push.
from . import admin_notification_events  # noqa: F401


@receiver(
    post_save,
    sender=Announcement,
    dispatch_uid="cybexel_management_announcement_windows_push_v1",
)
def management_announcement_windows_push(sender, instance, created, **kwargs):
    # Only newly published announcements; no push on every edit/save.
    if not created or not getattr(instance, "is_active", True):
        return

    announcement_id = instance.pk

    def deliver_to_management():
        try:
            announcement = Announcement.objects.filter(
                pk=announcement_id, is_active=True
            ).first()
            if announcement is None:
                return

            destination = reverse("admin_announcements")
            recipients = User.objects.filter(job_Position__iexact="Management")

            for admin in recipients.iterator():
                result = send_windows_push(
                    recipient=admin,
                    portal="management",
                    title="New Announcement",
                    message=str(announcement.title),
                    url=destination,
                    tag=f"admin-announcement-{announcement.pk}",
                )
                logger.info(
                    "Admin announcement push: announcement=%s recipient=%s result=%s",
                    announcement.pk, admin.pk, result,
                )
        except Exception:
            logger.exception(
                "Admin announcement Windows Push failed: announcement=%s",
                announcement_id,
            )

    transaction.on_commit(deliver_to_management)



def queue_announcement_recipient_notifications(announcement_id):
    from .models import AnnouncementRecipient

    def deliver():
        announcement = Announcement.objects.filter(
            pk=announcement_id,
            is_active=True,
        ).first()

        if not announcement or announcement.is_master_admin_announcement:
            return

        author = (
            "Admin" if announcement.is_admin_announcement
            else announcement.created_by.name
            if announcement.created_by else "Team Lead"
        )

        recipients = AnnouncementRecipient.objects.filter(
            announcement_id=announcement_id,
            recipient__job_Position__in=["Team Lead", "Team Member"],
        ).select_related("recipient")

        for item in recipients.iterator():
            role = item.recipient.job_Position.strip().lower()

            if role == "team lead":
                page = "teamlead_announcements"
            elif role == "team member":
                page = "teammember_announcements"
            else:
                continue

            TeamLeadNotification.objects.get_or_create(
                event_key=f"announcement-invite:{announcement.pk}:{item.recipient_id}",
                defaults={
                    "recipient": item.recipient,
                    "kind": "announcement",
                    "title": "New Announcement",
                    "message": f"From {author}: {announcement.message[:250]}",
                    "url": reverse(page),
                },
            )

    transaction.on_commit(deliver)
