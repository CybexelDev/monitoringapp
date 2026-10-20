"""Shared chat Web Push subscription API. Delivery is added in Step 2."""
import base64
import hashlib
import json
import re
from datetime import datetime, timezone as datetime_timezone
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import ChatPushSubscription, User

PORTALS = {"team_lead", "team_member", "management", "master_admin"}
DEFAULT_PUSH_HOSTS = (
    "fcm.googleapis.com", "updates.push.services.mozilla.com",
    "web.push.apple.com", "*.push.apple.com",
    "*.notify.windows.com",
)


def _normal_role(value):
    return str(value or "").strip().lower().replace(" ", "_")


def _identity(request, portal, *, create=False):
    if portal not in PORTALS:
        return None
    if portal == "master_admin":
        from .master_chat_identity import master_chat_user
        return master_chat_user(getattr(request, "user", None), create=create)
    position = _normal_role(request.session.get("position"))
    if position != portal:
        return None
    raw_id = request.session.get("user_id")
    if isinstance(raw_id, bool) or not str(raw_id or "").isdigit():
        return None
    person = User.objects.filter(pk=raw_id).first()
    # User.status is activity presence, NOT a login permission flag.
    if person is None or _normal_role(person.job_Position) != portal:
        return None
    return person


def _error(message, status=400):
    return JsonResponse({"ok": False, "message": message}, status=status)


def _body(request):
    if request.content_type != "application/json":
        raise ValueError("Send application/json.")
    if len(request.body) > 8192:
        raise ValueError("Subscription data is too large.")
    try:
        value = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Invalid JSON.") from None
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return value


def _key(value, length):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", value) or len(value) > 100:
        raise ValueError("Invalid browser subscription keys.")
    try:
        decoded = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except ValueError:
        raise ValueError("Invalid browser subscription keys.") from None
    if len(decoded) != length or (length == 65 and decoded[0] != 4):
        raise ValueError("Invalid browser subscription keys.")
    return base64.urlsafe_b64encode(decoded).decode().rstrip("=")


def _endpoint(value):
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) <= 32 for c in value):
        raise ValueError("Invalid push endpoint.")
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        valid = parsed.scheme == "https" and parsed.port in (None, 443)
    except ValueError:
        raise ValueError("Invalid push endpoint.") from None
    if not valid or not host or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Use a valid HTTPS push endpoint.")
    hosts = getattr(settings, "CHAT_PUSH_ALLOWED_HOSTS", DEFAULT_PUSH_HOSTS)
    if not any(host == item or (item.startswith("*.") and host.endswith(item[1:]) and host != item[2:]) for item in hosts):
        raise ValueError("This browser push provider is not enabled on the server.")
    return value


def _subscription(data):
    endpoint = _endpoint(data.get("endpoint"))
    keys = data.get("keys")
    if not isinstance(keys, dict):
        raise ValueError("Browser subscription keys are required.")
    p256dh, auth = _key(keys.get("p256dh"), 65), _key(keys.get("auth"), 16)
    expires = data.get("expirationTime")
    expiration_time = None
    if expires is not None:
        if isinstance(expires, bool) or not isinstance(expires, (int, float)):
            raise ValueError("Invalid subscription expiry.")
        try:
            expiration_time = datetime.fromtimestamp(expires / 1000, tz=datetime_timezone.utc)
        except (ValueError, OverflowError, OSError):
            raise ValueError("Invalid subscription expiry.") from None
        if expiration_time <= timezone.now():
            raise ValueError("This subscription has expired. Enable notifications again.")
    return {"endpoint": endpoint, "endpoint_hash": hashlib.sha256(endpoint.encode()).hexdigest(),
            "p256dh": p256dh, "auth": auth, "expiration_time": expiration_time}


@never_cache
@ensure_csrf_cookie
@require_GET
def config(request, portal):
    # Master Admin mapping may not exist until their first chat visit.
    if portal == "master_admin":
        from django.contrib.auth import get_user_model
        account = getattr(request, "user", None)
        allowed = account is not None and account.is_authenticated and get_user_model().objects.filter(
            pk=account.pk, is_active=True, is_superuser=True
        ).exists()
    else:
        allowed = _identity(request, portal) is not None
    if not allowed:
        return _error("Chat login required.", 403)
    public_key = str(getattr(settings, "CHAT_PUSH_VAPID_PUBLIC_KEY", "") or "").strip()
    ready = False
    if public_key:
        try:
            public_key = _key(public_key, 65)
            ready = bool(getattr(settings, "CHAT_PUSH_ENABLED", False))
        except ValueError:
            public_key = ""
    return JsonResponse({"ok": True, "configured": ready, "public_key": public_key,
                         "message": "Chat push is configured." if ready else "Chat push setup is not complete yet."})


@never_cache
@require_POST
@csrf_protect
def subscribe(request, portal):
    person = _identity(request, portal, create=True)
    if person is None:
        return _error("Chat login required.", 403)
    try:
        values = _subscription(_body(request))
    except ValueError as exc:
        return _error(str(exc))
    if not request.session.session_key:
        request.session.save()
    with transaction.atomic():
        row, _ = ChatPushSubscription.objects.select_for_update().get_or_create(
            endpoint_hash=values["endpoint_hash"],
            defaults={**values, "user": person, "portal": portal,
                      "session_key": request.session.session_key},
        )
        # Rebinding an existing browser endpoint requires its existing secrets.
        if row.endpoint != values["endpoint"] or not constant_time_compare(row.auth, values["auth"]) or not constant_time_compare(row.p256dh, values["p256dh"]):
            return _error("Subscription changed. Disable and re-enable browser notifications.", 409)
        for key, value in values.items():
            setattr(row, key, value)
        row.user = person
        row.portal = portal
        row.session_key = request.session.session_key
        row.enabled = True
        row.save()
    return JsonResponse({"ok": True, "message": "Chat notification subscription saved."})


@never_cache
@require_POST
@csrf_protect
def unsubscribe(request, portal):
    person = _identity(request, portal)
    if person is None:
        return _error("Chat login required.", 403)
    try:
        endpoint = _endpoint(_body(request).get("endpoint"))
    except ValueError as exc:
        return _error(str(exc))
    ChatPushSubscription.objects.filter(
        user=person, portal=portal, endpoint_hash=hashlib.sha256(endpoint.encode()).hexdigest()
    ).delete()
    return JsonResponse({"ok": True, "message": "Chat notifications disabled for this browser."})
