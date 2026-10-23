"""Admin IN-APP notification feed events.

Imported once by monitoringapp.notification_signals (which is already loaded by
MonitoringappConfig.ready()).  This module NEVER sends Windows/web push or toast.
It keeps AdminNotification (Admin) separate from TeamLeadNotification.
"""
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse

from chat.models import ChatMessage
from .models import (
    AdminKnowledge, AdminNotepad, AdminNotification, AdminReminder,
    Announcement, GoogleMeeting, GroupMember, GroupMessage, Knowledge,
    MorningReport, EveningReport, Notepad, ProjectAssign, Task, User,
)

logger = logging.getLogger(__name__)


def _safe_reverse(name, *args):
    try:
        return reverse(name, args=args or None)
    except Exception:
        logger.warning("Admin notification link not available: %s", name)
        return ""


def _admin_recipients():
    """Active management employees and active auth superadmins, NOT every employee."""
    for user_id in User.objects.filter(job_Position__iexact="Management", status="active").values_list("pk", flat=True):
        yield {"management_owner_id": user_id}
    for auth_id in get_user_model().objects.filter(is_superuser=True, is_active=True).values_list("pk", flat=True):
        yield {"auth_owner_id": auth_id}


def _one_owner(instance):
    if getattr(instance, "management_owner_id", None):
        return {"management_owner_id": instance.management_owner_id}
    if getattr(instance, "auth_owner_id", None):
        return {"auth_owner_id": instance.auth_owner_id}
    return None


def _commit_notification(owners, *, kind, title, message="", url="", event_key=None):
    """Write only after the source transaction commits. No push receivers called."""
    owners = list(owners)
    if not owners:
        return

    def write():
        for owner in owners:
            try:
                values = dict(owner, kind=kind, title=str(title)[:180], message=str(message)[:1200], url=url[:500])
                if event_key:
                    owner_type, owner_id = next(iter(owner.items()))
                    key = f"feed:{event_key}:{owner_type}:{owner_id}"[:180]
                    AdminNotification.objects.get_or_create(event_key=key, defaults=values)
                else:
                    AdminNotification.objects.create(**values)
            except Exception:
                # Feed failure must never make a successful Chat/Report save fail.
                logger.exception("Unable to write Admin in-app notification %s", kind)

    transaction.on_commit(write)


def _broadcast(*, kind, title, message="", url="", event_key=None):
    _commit_notification(_admin_recipients(), kind=kind, title=title,
                         message=message, url=url, event_key=event_key)


def _owner_event(instance, *, kind, title, message="", url="", event_key=None):
    owner = _one_owner(instance)
    if owner:
        _commit_notification([owner], kind=kind, title=title,
                             message=message, url=url, event_key=event_key)


def _person(user):
    return getattr(user, "name", "") or getattr(user, "username", "") or "Employee"


# Admin's own private notes/resources: do not disclose these to other admins.
@receiver(post_save, sender=AdminNotepad, dispatch_uid="admin_feed_adminnote_save_v1")
def admin_note_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    _owner_event(instance, kind="note", title=f"Note {verb}", message=instance.title,
                 url=_safe_reverse("admin_notepad"),
                 event_key=f"adminnote:{instance.pk}:created" if created else None)


@receiver(post_delete, sender=AdminNotepad, dispatch_uid="admin_feed_adminnote_delete_v1")
def admin_note_delete(sender, instance, **kwargs):
    _owner_event(instance, kind="note", title="Note deleted", message=instance.title,
                 url=_safe_reverse("admin_notepad"), event_key=f"adminnote:{instance.pk}:deleted")


@receiver(post_save, sender=AdminKnowledge, dispatch_uid="admin_feed_adminresource_save_v1")
def admin_resource_save(sender, instance, created, **kwargs):
    verb = "added" if created else "updated"
    _owner_event(instance, kind="resource", title=f"Knowledge resource {verb}", message=instance.title,
                 url=_safe_reverse("admin_repository"),
                 event_key=f"adminresource:{instance.pk}:created" if created else None)


@receiver(post_delete, sender=AdminKnowledge, dispatch_uid="admin_feed_adminresource_delete_v1")
def admin_resource_delete(sender, instance, **kwargs):
    _owner_event(instance, kind="resource", title="Knowledge resource deleted", message=instance.title,
                 url=_safe_reverse("admin_repository"), event_key=f"adminresource:{instance.pk}:deleted")


# Public activity, shown in every Admin's feed. Do not expose private note text.
@receiver(post_save, sender=MorningReport, dispatch_uid="admin_feed_morning_report_v1")
@receiver(post_save, sender=EveningReport, dispatch_uid="admin_feed_evening_report_v1")
def admin_report_activity(sender, instance, created, **kwargs):
    label = "Morning" if sender is MorningReport else "Evening"
    verb = "submitted" if created else "updated"
    _broadcast(kind="report", title=f"{label} report {verb}",
               message=f"{_person(instance.user)} · {instance.status}",
               url=_safe_reverse("admin_reports"),
               event_key=f"{label.lower()}report:{instance.pk}:created" if created else None)


@receiver(post_save, sender=ProjectAssign, dispatch_uid="admin_feed_project_save_v1")
def admin_project_save(sender, instance, created, **kwargs):
    verb = "assigned" if created else "updated"
    _broadcast(kind="project", title=f"Project {verb}",
               message=f"{instance.work_name} · {_person(instance.assign_to)}",
               url="",  # Admin has no dedicated project page; View shows details here.
               event_key=f"project:{instance.pk}:created" if created else None)


@receiver(post_delete, sender=ProjectAssign, dispatch_uid="admin_feed_project_delete_v1")
def admin_project_delete(sender, instance, **kwargs):
    _broadcast(kind="project", title="Project deleted", message=instance.work_name,
               url="", event_key=f"project:{instance.pk}:deleted")


@receiver(post_save, sender=Task, dispatch_uid="admin_feed_task_save_v1")
def admin_task_save(sender, instance, created, **kwargs):
    _broadcast(kind="task", title="Task created" if created else "Task updated",
               message=instance.title, url="",
               event_key=f"task:{instance.pk}:created" if created else None)


@receiver(post_delete, sender=Task, dispatch_uid="admin_feed_task_delete_v1")
def admin_task_delete(sender, instance, **kwargs):
    _broadcast(kind="task", title="Task deleted", message=instance.title,
               url="", event_key=f"task:{instance.pk}:deleted")


@receiver(post_save, sender=Knowledge, dispatch_uid="admin_feed_sharedresource_save_v1")
def shared_resource_save(sender, instance, created, **kwargs):
    if not created:
        return  # Shared Knowledge has no update timestamp; avoid false edits.
    _broadcast(kind="resource", title="Team knowledge resource added",
               message=f"{_person(instance.user)} · {instance.title}",
               url=_safe_reverse("admin_repository"), event_key=f"sharedresource:{instance.pk}:added")


@receiver(post_delete, sender=Knowledge, dispatch_uid="admin_feed_sharedresource_delete_v1")
def shared_resource_delete(sender, instance, **kwargs):
    _broadcast(kind="resource", title="Team knowledge resource deleted",
               message=f"{_person(instance.user)} · {instance.title}",
               url=_safe_reverse("admin_repository"), event_key=f"sharedresource:{instance.pk}:deleted")


@receiver(post_save, sender=Announcement, dispatch_uid="admin_feed_announcement_save_v1")
def admin_announcement_save(sender, instance, created, **kwargs):
    # Master Admin's announcements are handled separately by the Master portal.
    if instance.is_master_admin_announcement:
        return
    verb = "published" if created else ("deleted" if not instance.is_active else "updated")
    who = "Admin" if instance.is_admin_announcement else _person(instance.created_by)
    _broadcast(kind="announcement", title=f"Announcement {verb}",
               message=f"{who} · {instance.title}", url=_safe_reverse("admin_announcements"),
               event_key=f"announcement:{instance.pk}:published" if created else None)


@receiver(post_save, sender=GoogleMeeting, dispatch_uid="admin_feed_meeting_save_v1")
def admin_meeting_save(sender, instance, created, **kwargs):
    if instance.is_master_admin_meeting:
        return
    verb = "scheduled" if created else "updated"
    _broadcast(kind="meeting", title=f"Google Meet {verb}",
               message=f"{instance.purpose} · {instance.date} {instance.time}",
               url=_safe_reverse("admin_google_meet"),
               event_key=f"meeting:{instance.pk}:scheduled" if created else None)


@receiver(post_save, sender=AdminReminder, dispatch_uid="admin_feed_reminder_save_v1")
def admin_reminder_save(sender, instance, created, update_fields=None, **kwargs):
    fields = set(update_fields or ())
    # Due-reminder worker sets notified_at/notification; that worker makes its own
    # due notification. Do not create an "updated" event for that internal save.
    if not created and fields and fields.issubset({"notified_at", "notification", "updated_at"}):
        return
    verb = "created" if created else ("completed" if instance.is_completed else "updated")
    _owner_event(instance, kind="reminder", title=f"Reminder {verb}",
                 message=instance.title, url=_safe_reverse("admin_reminders"),
                 event_key=f"reminder:{instance.pk}:created" if created else None)


@receiver(post_delete, sender=AdminReminder, dispatch_uid="admin_feed_reminder_delete_v1")
def admin_reminder_delete(sender, instance, **kwargs):
    _owner_event(instance, kind="reminder", title="Reminder deleted",
                 message=instance.title, url=_safe_reverse("admin_reminders"),
                 event_key=f"reminder:{instance.pk}:deleted")


# Incoming personal and group Chat for Management Admin only. No push or Toast.
# A Team Lead/Member's private conversations must NOT leak into Admin's feed.
@receiver(post_save, sender=ChatMessage, dispatch_uid="admin_feed_personal_chat_v1")
def admin_incoming_personal_chat(sender, instance, created, **kwargs):
    if not created or instance.deleted_for_everyone:
        return
    room = instance.conversation
    peer_id = room.user2_id if room.user1_id == instance.sender_id else room.user1_id
    if peer_id == instance.sender_id:
        return
    if not User.objects.filter(pk=peer_id, job_Position__iexact="Management").exists():
        return
    _commit_notification([{"management_owner_id": peer_id}], kind="chat",
                         title="New personal chat message",
                         message=f"From {_person(instance.sender)}",
                         url=_safe_reverse("admin_chat_room", instance.sender_id),
                         event_key=f"personalchat:{instance.pk}")


@receiver(post_save, sender=GroupMessage, dispatch_uid="admin_feed_group_chat_v1")
def admin_incoming_group_chat(sender, instance, created, **kwargs):
    if not created or instance.deleted_for_everyone:
        return
    recipient_ids = GroupMember.objects.filter(group_id=instance.group_id,
                     user__job_Position__iexact="Management").exclude(user_id=instance.sender_id).values_list("user_id", flat=True)
    owners = [{"management_owner_id": pk} for pk in recipient_ids]
    _commit_notification(owners, kind="chat", title="New group chat message",
                         message=f"{_person(instance.sender)} · {instance.group.name}",
                         url=_safe_reverse("admin_group_chat", instance.group_id), event_key=f"groupchat:{instance.pk}")


def admin_announcement_was_seen(announcement, viewer):
    """Called ONLY on the first-read transition by Lead/Member view actions.

    Their .update(read_at=...) bypasses Django post_save, so this explicit call
    is required. Do not alter TeamLeadNotification receipts for Team Lead posts.
    """
    if not announcement.is_admin_announcement or announcement.is_master_admin_announcement:
        return
    if announcement.admin_created_by_id:
        owners = [{"auth_owner_id": announcement.admin_created_by_id}]
    elif announcement.created_by_id:
        owners = [{"management_owner_id": announcement.created_by_id}]
    else:
        return
    _commit_notification(owners, kind="announcement", title="Announcement seen",
                         message=f"{_person(viewer)} viewed your announcement: {announcement.title}",
                         url=_safe_reverse("admin_announcements"),
                         event_key=f"announcement:{announcement.pk}:seen:{viewer.pk}")
