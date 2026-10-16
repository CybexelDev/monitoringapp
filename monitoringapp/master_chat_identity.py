"""Explicit Django-superuser to shared-chat identity mapping."""
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from .models import MasterAdminChatIdentity, User


def master_chat_user(account, *, create=False, touch=False):
    if not account or not account.is_authenticated:
        return None
    # Verify current database permissions as well as the session snapshot.
    accounts = get_user_model().objects.filter(pk=account.pk, is_active=True, is_superuser=True)
    if not accounts.exists():
        return None
    with transaction.atomic():
        if create:
            current = accounts.select_for_update().first()
            if current is None:
                return None
        else:
            current = account
        link = MasterAdminChatIdentity.objects.select_related("chat_user").filter(account_id=account.pk).first()
        if link is None:
            if not create:
                return None
            token = uuid4().hex
            person = User.objects.create(
                name=(current.get_full_name() or current.username)[:150],
                employee_id="MASTER-CHAT-" + token,
                email="master-chat-" + token + "@chat.invalid",
                username="master-chat-" + token,
                password=make_password(None),
                job_Position="Master Admin", designation="Master Admin",
                status="active", last_activity=timezone.now(),
            )
            link = MasterAdminChatIdentity.objects.create(account=current, chat_user=person)
        person = link.chat_user
        if create or touch:
            values = {"name": (current.get_full_name() or current.username)[:150],
                "status": "active", "last_activity": timezone.now()}
            profile = getattr(current, "master_admin_profile", None)
            if profile is not None:
                values["profile_image"] = profile.profile_image.name or ""
            User.objects.filter(pk=person.pk).update(**values)
            for key, value in values.items():
                setattr(person, key, value)
        return person
