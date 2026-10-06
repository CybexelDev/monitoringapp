"""Persistent message actions. Called only after the page's session/room checks."""
from datetime import timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from chat.models import Conversation, ChatMessage
from .models import Group, GroupMember, GroupMessage
from .chat_receipts import broadcast_chat_activity


def _chat_json(data, status=200):
    return JsonResponse({**data, 'server_now': timezone.now().isoformat()}, status=status)


def chat_action(request, user, target, group=False):
    action = request.POST.get('action', '')
    if action not in {'edit_message', 'delete_for_me', 'delete_for_everyone', 'clear_chat'}:
        return _chat_json({'ok': False, 'message': 'Invalid action.'}, status=400)
    manager = GroupMessage.objects if group else ChatMessage.objects
    scope = {'group': target} if group else {'conversation': target}
    if not group and user.pk not in {target.user1_id, target.user2_id}:
        return _chat_json({'ok': False, 'message': 'Access denied.'}, status=403)
    with transaction.atomic():
        # Same group lock is used by membership changes, so removal and actions serialize.
        type(target).objects.select_for_update().get(pk=target.pk)
        if group and not GroupMember.objects.filter(group=target, user=user).exists():
            return _chat_json({'ok': False, 'message': 'You are no longer a group member.'}, status=403)
        qs = manager.filter(**scope).exclude(hidden_for=user)
        if action == 'clear_chat':
            through = manager.model.hidden_for.through
            field = 'groupmessage_id' if group else 'chatmessage_id'
            through.objects.bulk_create([
                through(**{field: pk, 'user_id': user.pk}) for pk in qs.values_list('pk', flat=True)
            ], ignore_conflicts=True, batch_size=500)
            message = 'Chat cleared for you.'
        else:
            try:
                pk = int(request.POST.get('message_id', ''))
            except (ValueError, TypeError):
                return _chat_json({'ok': False, 'message': 'Invalid message ID.'}, status=400)
            saved = get_object_or_404(qs.select_for_update(), pk=pk)
            if action == 'delete_for_me':
                saved.hidden_for.add(user)
                message = 'Message deleted for you.'
            else:
                if saved.sender_id != user.pk:
                    return _chat_json({'ok': False, 'message': 'You can only change your own messages.'}, status=403)
                if saved.deleted_for_everyone:
                    return _chat_json({'ok': False, 'message': 'This message has already been deleted.'}, status=409)
                text_field = 'message' if group else 'content'
                if action == 'edit_message':
                    sent_at = saved.timestamp if group else saved.created_at
                    now = timezone.now()
                    if now >= sent_at + timedelta(hours=2):
                        return _chat_json({
                            'ok': False, 'code': 'edit_window_expired',
                            'message': 'Messages can only be edited within 2 hours of sending.',
                        }, status=403)
                    text = request.POST.get('message', '').strip()
                    if not text or len(text) > 10000:
                        return _chat_json({'ok': False, 'message': 'Enter 1–10,000 characters.'}, status=400)
                    setattr(saved, text_field, text)
                    saved.edited_at = now
                    saved.save(update_fields=[text_field, 'edited_at'])
                    message = 'Message updated.'
                else:
                    setattr(saved, text_field, 'This message was deleted.')
                    saved.deleted_for_everyone = True
                    saved.save(update_fields=[text_field, 'deleted_for_everyone'])
                    message = 'Message deleted for everyone.'
        channel_name = ('group_' if group else 'chat_') + str(target.pk)
        event = {'type': 'chat_change'}
        if action in {'delete_for_me', 'clear_chat'}:
            event['user_id'] = user.pk
        def notify():
            layer = get_channel_layer()
            if layer:
                try:
                    async_to_sync(layer.group_send)(channel_name, event)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception('Chat change delivery failed; history polling will reconcile.')
            async_to_sync(broadcast_chat_activity)(group, target.pk)
        transaction.on_commit(notify)
    return _chat_json({'ok': True, 'message': message})


def chat_history(request, user, target, group=False):
    """Full visible snapshot, reconciled in place by either role's chat page."""
    if group:
        get_object_or_404(GroupMember, group=target, user=user)
        qs = GroupMessage.objects.filter(group=target).order_by('timestamp', 'pk')
    else:
        if user.pk not in {target.user1_id, target.user2_id}:
            return _chat_json({'ok': False, 'message': 'Access denied.'}, status=403)
        qs = ChatMessage.objects.filter(conversation=target).order_by('created_at', 'pk')
    qs = qs.exclude(hidden_for=user).select_related('sender')
    items = []
    for saved in qs:
        sender = saved.sender
        items.append({
            'message_id': saved.pk, 'message': saved.message if group else saved.content,
            'sender_id': sender.pk, 'sender': sender.name,
            'sender_profile': sender.profile_image.url if sender.profile_image else None,
            'timestamp': (saved.timestamp if group else saved.created_at).isoformat(),
            'edited_at': saved.edited_at.isoformat() if saved.edited_at else None,
            'deleted': saved.deleted_for_everyone,
        })
    response = JsonResponse({'ok': True, 'items': items})
    response['Cache-Control'] = 'no-store'
    return response
