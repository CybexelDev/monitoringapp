"""Persistent unread counts and read receipts for the shared chat models."""
import logging

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from chat.models import ChatMessage, Conversation
from .models import ChatReadState, Group, GroupMember, GroupMessage, User

logger = logging.getLogger(__name__)


def _user(request):
    position = str(request.session.get("position", "")).strip().lower().replace(" ", "_")
    if position not in {"team_member", "team_lead"}:
        return None
    return User.objects.filter(pk=request.session.get("user_id")).first()


def _target(user, kind, target_id, lock=False):
    if kind == "personal":
        qs = Conversation.objects.filter(Q(user1=user) | Q(user2=user))
    elif kind == "group":
        qs = Group.objects.filter(memberships__user=user)
    else:
        return None
    if lock:
        qs = qs.select_for_update()
    return qs.filter(pk=target_id).first()


@database_sync_to_async
def _recipients(group, target_id):
    if group:
        return list(GroupMember.objects.filter(group_id=target_id).values_list("user_id", flat=True))
    row = Conversation.objects.filter(pk=target_id).values("user1_id", "user2_id").first()
    return [row["user1_id"], row["user2_id"]] if row else []


async def broadcast_chat_activity(group, target_id):
    """Call after a committed send, read, clear or delete operation."""
    try:
        layer = get_channel_layer()
        if layer is None:
            return
        for user_id in await _recipients(group, target_id):
            await layer.group_send(
                f"chat_receipts_user_{user_id}", {"type": "chat_invalidate"}
            )
    except Exception:
        logger.exception("Chat receipt broadcast failed; metadata polling can recover.")


def _receipts(user, target, kind):
    is_group = kind == "group"
    field = "group" if is_group else "conversation"
    model = GroupMessage if is_group else ChatMessage
    time_field = "timestamp" if is_group else "created_at"
    messages = model.objects.filter(**{field: target}, sender=user).exclude(hidden_for=user)
    messages = messages.filter(deleted_for_everyone=False)
    states = dict(ChatReadState.objects.filter(**{field: target}).values_list("user_id", "last_read_id"))
    if is_group:
        readers = list(GroupMember.objects.filter(group=target).exclude(user=user).values_list("user_id", "added_at"))
    else:
        peer = target.user2_id if target.user1_id == user.pk else target.user1_id
        readers = [(peer, None)]
    result = []
    for message_id, sent_at in messages.values_list("pk", time_field):
        eligible = [uid for uid, joined_at in readers if joined_at is None or joined_at <= sent_at]
        count = sum(states.get(uid, 0) >= message_id for uid in eligible)
        result.append({
            "message_id": message_id,
            "seen": bool(eligible) and count == len(eligible),
            "read_count": count,
            "reader_count": len(eligible),
        })
    return result


@never_cache
@require_GET
def chat_meta(request):
    user = _user(request)
    if user is None:
        return JsonResponse({"ok": False, "message": "Please sign in again."}, status=401)
    personal_states = dict(ChatReadState.objects.filter(user=user, conversation__isnull=False).values_list("conversation_id", "last_read_id"))
    group_states = dict(ChatReadState.objects.filter(user=user, group__isnull=False).values_list("group_id", "last_read_id"))
    conversations = list(Conversation.objects.filter(Q(user1=user) | Q(user2=user)).order_by("pk"))
    # Existing pages select the oldest conversation if an old reversed duplicate exists.
    canonical = {}
    for row in conversations:
        peer = row.user2_id if row.user1_id == user.pk else row.user1_id
        canonical.setdefault(peer, row.pk)
    personal_filter = Q(pk__in=[])
    for conversation_id in canonical.values():
        personal_filter |= Q(conversation_id=conversation_id, pk__gt=personal_states.get(conversation_id, 0))
    personal_counts = dict(ChatMessage.objects.filter(personal_filter, deleted_for_everyone=False).exclude(sender=user).exclude(hidden_for=user).order_by().values("conversation_id").annotate(total=Count("pk")).values_list("conversation_id", "total"))
    group_ids = list(GroupMember.objects.filter(user=user).values_list("group_id", flat=True))
    group_filter = Q(pk__in=[])
    for group_id in group_ids:
        group_filter |= Q(group_id=group_id, pk__gt=group_states.get(group_id, 0))
    group_counts = dict(GroupMessage.objects.filter(group_filter, deleted_for_everyone=False).exclude(sender=user).exclude(hidden_for=user).order_by().values("group_id").annotate(total=Count("pk")).values_list("group_id", "total"))
    data = {
        "ok": True,
        "personal": [{"peer_id": peer, "conversation_id": cid, "unread": personal_counts.get(cid, 0)} for peer, cid in canonical.items()],
        "groups": [{"group_id": gid, "unread": group_counts.get(gid, 0)} for gid in group_ids],
        "receipts": [],
    }
    target_id = request.GET.get("target_id")
    if target_id:
        try:
            target_id = int(target_id)
        except (ValueError, TypeError):
            return JsonResponse({"ok": False, "message": "Invalid chat ID."}, status=400)
        kind = request.GET.get("kind")
        target = _target(user, kind, target_id)
        if target is None:
            return JsonResponse({"ok": False, "message": "Chat unavailable."}, status=404)
        data["receipts"] = _receipts(user, target, kind)
    return JsonResponse(data)


@never_cache
@require_POST
def chat_mark_read(request):
    user = _user(request)
    if user is None:
        return JsonResponse({"ok": False, "message": "Please sign in again."}, status=401)
    try:
        target_id = int(request.POST.get("target_id", ""))
        message_id = int(request.POST.get("message_id", ""))
        if target_id < 1 or message_id < 1:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "message": "Invalid chat or message ID."}, status=400)
    kind = request.POST.get("kind")
    with transaction.atomic():
        target = _target(user, kind, target_id, lock=True)
        if target is None:
            return JsonResponse({"ok": False, "message": "Chat unavailable."}, status=404)
        field = "group" if kind == "group" else "conversation"
        model = GroupMessage if kind == "group" else ChatMessage
        if not model.objects.filter(pk=message_id, **{field: target}).exclude(hidden_for=user).exists():
            return JsonResponse({"ok": False, "message": "Message unavailable."}, status=404)
        state, _ = ChatReadState.objects.get_or_create(user=user, **{field: target})
        if message_id > state.last_read_id:
            state.last_read_id = message_id
            state.save(update_fields=["last_read_id", "updated_at"])
            transaction.on_commit(lambda: async_to_sync(broadcast_chat_activity)(kind == "group", target_id))
        last_read_id = state.last_read_id
    return JsonResponse({"ok": True, "last_read_id": last_read_id})
