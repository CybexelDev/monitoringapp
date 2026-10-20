
"""
Cybexel - Reusable Windows Push Delivery

Phase 1: Team Lead push delivery.
Other portals will be enabled after their authentication
and logout handling are verified.
"""

import json
import logging
from uuid import uuid4

from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from pywebpush import webpush, WebPushException

from monitoringapp.models import ChatPushSubscription

logger = logging.getLogger(__name__)

ENABLED_PORTALS = {"team_lead"}


def _normal_role(value):
    return str(value or "").strip().lower().replace(" ", "_")


def _valid_subscription(subscription):
    """Confirm that the browser belongs to an active login session."""

    if not subscription.enabled:
        return False

    if subscription.expiration_time:
        if subscription.expiration_time <= timezone.now():
            return False

    try:
        session = Session.objects.get(
            session_key=subscription.session_key,
            expire_date__gt=timezone.now(),
        )
        data = session.get_decoded()
    except Session.DoesNotExist:
        return False

    return (
        str(data.get("user_id")) == str(subscription.user_id)
        and _normal_role(data.get("position")) == subscription.portal
        and _normal_role(subscription.user.job_Position)
        == subscription.portal
    )


def send_windows_push(
    *,
    recipient,
    portal,
    title,
    message,
    url,
    tag=None,
):
    """
    Send a Windows/browser push to one recipient.

    Returns delivery attempt statistics.
    """

    result = {
        "sent": 0,
        "failed": 0,
        "skipped": 0,
    }

    if portal not in ENABLED_PORTALS:
        raise ValueError("Push delivery is not enabled for this portal.")

    if not getattr(settings, "CHAT_PUSH_ENABLED", False):
        raise RuntimeError("VAPID configuration is not enabled.")

    if not isinstance(url, str) or not url.startswith("/"):
        raise ValueError("Notification URL must be a local path.")

    if url.startswith("//") or "\\" in url:
        raise ValueError("Invalid notification URL.")

    subscriptions = ChatPushSubscription.objects.filter(
        user=recipient,
        portal=portal,
        enabled=True,
    ).select_related("user")

    payload = json.dumps({
        "title": str(title)[:180],
        "body": str(message)[:300],
        "url": url,
        "tag": tag or f"cybexel-{uuid4().hex}",
        "portal": portal,
    })

    for subscription in subscriptions:
        if not _valid_subscription(subscription):
            result["skipped"] += 1
            continue

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=settings.CHAT_PUSH_VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": settings.CHAT_PUSH_VAPID_SUBJECT,
                },
                timeout=10,
            )

            result["sent"] += 1

        except WebPushException as error:
            result["failed"] += 1

            status_code = getattr(
                getattr(error, "response", None),
                "status_code",
                None,
            )

            if status_code in (404, 410):
                subscription.enabled = False
                subscription.save(update_fields=["enabled"])

            logger.warning(
                "Push delivery failed for subscription %s: HTTP %s",
                subscription.pk,
                status_code,
            )

        except Exception:
            result["failed"] += 1
            logger.exception(
                "Unexpected push delivery error for subscription %s",
                subscription.pk,
            )

    return result
