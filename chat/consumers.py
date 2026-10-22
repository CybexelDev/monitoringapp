"""Authenticated personal/group sockets shared by Team Lead and Team Member."""
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from monitoringapp.chat_receipts import broadcast_chat_activity

import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)
class MemberChatConsumer(AsyncWebsocketConsumer):
    group_chat = False
    allowed_positions = {'team_member'}

    async def connect(self):
        self.joined = False
        self.user_id, position = await self.session_identity()
        key = 'group_id' if self.group_chat else 'conversation_id'
        self.target_id = self.scope['url_route']['kwargs'][key]
        if position not in self.allowed_positions or not self.user_id or not await self.allowed():
            await self.close(code=4403)
            return
        self.room_group_name = ('group_' if self.group_chat else 'chat_') + str(self.target_id)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.joined = True
        await self.accept()

    @database_sync_to_async
    def session_identity(self):
        session = self.scope.get('session', {})
        return session.get('user_id'), str(session.get('position', '')).strip().lower().replace(' ', '_')

    async def disconnect(self, close_code):
        if getattr(self, 'joined', False):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def allowed(self):
        from monitoringapp.models import GroupMember
        from chat.models import Conversation
        from django.db.models import Q
        if self.group_chat:
            return GroupMember.objects.filter(group_id=self.target_id, user_id=self.user_id).exists()
        return Conversation.objects.filter(pk=self.target_id).filter(Q(user1_id=self.user_id) | Q(user2_id=self.user_id)).exists()

    async def receive(self, text_data=None, bytes_data=None):
        if not getattr(self, 'joined', False) or text_data is None:
            return
        try:
            data = json.loads(text_data)
        except (ValueError, TypeError):
            return
        if not isinstance(data, dict) or not isinstance(data.get('message'), str):
            return
        message = data['message'].strip()
        if not message or len(message) > 10000:
            await self.send(text_data=json.dumps({'error': 'Enter a message of 10,000 characters or fewer.'}))
            return
        result = await self.save_message(message)
        if result is None:
            await self.close(code=4403)
            return
        # Sender comes from the authenticated session, never from browser input.
        result['client_id'] = str(data.get('client_id', ''))[:100]
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                **result,
            },
        )

        await broadcast_chat_activity(
            self.group_chat,
            self.target_id,
        )
                # Send Windows Push after the message has been saved.
        try:
            await sync_to_async(
                self.send_teamlead_windows_push,
                thread_sensitive=False,
            )(result)
        except Exception:
            logger.exception("Chat Windows Push delivery failed.")

        # Team Member Windows Push (independent of existing Team Lead delivery).
        try:
            await sync_to_async(
                self.send_teammember_windows_push,
                thread_sensitive=False,
            )(result)
        except Exception:
            logger.exception("Team Member Chat Windows Push delivery failed.")

    @database_sync_to_async
    def save_message(self, message):
        from monitoringapp.models import User, GroupMember, GroupMessage
        from chat.models import Conversation, ChatMessage
        from django.db.models import Q
        from django.db import transaction
        with transaction.atomic():
            user = User.objects.filter(pk=self.user_id).first()
            if user is None:
                return None
            if self.group_chat:
                if not GroupMember.objects.filter(group_id=self.target_id, user=user).exists():
                    return None
                saved = GroupMessage.objects.create(group_id=self.target_id, sender=user, message=message)
                timestamp = saved.timestamp
            else:
                conversation = Conversation.objects.filter(pk=self.target_id).filter(Q(user1=user) | Q(user2=user)).first()
                if conversation is None:
                    return None
                saved = ChatMessage.objects.create(conversation=conversation, sender=user, content=message)
                timestamp = saved.created_at
        return {'message_id': saved.pk, 'message': message, 'sender_id': user.pk,
                'sender': user.name, 'sender_profile': user.profile_image.url if user.profile_image else None,
                'timestamp': timestamp.isoformat()}
    
    def send_teamlead_windows_push(self, result):
        """
        Send Windows Push only to eligible Team Lead recipients.
        Supports personal and group chat.
        """

        from django.urls import reverse
        from django.db.models import Q
        from monitoringapp.models import User, GroupMember
        from chat.models import Conversation
        from monitoringapp.components.windows_push.delivery import (
            send_windows_push,
        )

        sender_id = result["sender_id"]
        sender_name = result["sender"]
        message_id = result["message_id"]
        message = result["message"][:160]

        recipients = []

        if self.group_chat:
            recipients = list(
                User.objects.filter(
                    group_memberships__group_id=self.target_id,
                    job_Position__iexact="Team Lead",
                )
                .exclude(pk=sender_id)
                .distinct()
            )

            url = reverse(
                "teamlead_group_chat_view",
                kwargs={"group_id": self.target_id},
            )

            from monitoringapp.models import Group

            group = Group.objects.filter(
                pk=self.target_id
            ).only("name").first()

            group_name = group.name if group else "Group Chat"

            title = f"{group_name} — New Group Message"
            message = f"{sender_name}: {message}"

        else:
            conversation = (
                Conversation.objects.filter(
                    pk=self.target_id
                )
                .filter(
                    Q(user1_id=sender_id) | Q(user2_id=sender_id)
                )
                .first()
            )

            if conversation is None:
                return

            recipient_id = (
                conversation.user2_id
                if conversation.user1_id == sender_id
                else conversation.user1_id
            )

            recipients = list(
                User.objects.filter(
                    pk=recipient_id,
                    job_Position__iexact="Team Lead",
                )
            )

            url = reverse(
                "teamlead_chat_room",
                kwargs={"user_id": sender_id},
            )

            title = f"New message from {sender_name}"

        for recipient in recipients:
            try:
                send_windows_push(
                    recipient=recipient,
                    portal="team_lead",
                    title=title,
                    message=message,
                    url=url,
                    tag=(
                        f"teamlead-group-{message_id}"
                        if self.group_chat
                        else f"teamlead-personal-{message_id}"
                    ),
                )

            except Exception:
                logger.exception(
                    "Chat Windows Push failed for recipient %s",
                    recipient.pk,
                )


    def send_teammember_windows_push(self, result):
        """Push new personal/group messages to Team Member recipients only."""
        from django.db.models import Q
        from django.urls import reverse
        from monitoringapp.models import User, Group
        from chat.models import Conversation
        from monitoringapp.components.windows_push.delivery import send_windows_push

        sender_id = result["sender_id"]
        sender_name = result["sender"]
        message_id = result["message_id"]
        message = result["message"][:160]

        if self.group_chat:
            recipients = User.objects.filter(
                group_memberships__group_id=self.target_id,
                job_Position__iexact="Team Member",
            ).exclude(pk=sender_id).distinct()
            url = reverse("group_chat_view", kwargs={"group_id": self.target_id})
            group_name = (Group.objects.filter(pk=self.target_id)
                          .values_list("name", flat=True).first() or "Group Chat")
            title = f"{group_name} — New Group Message"
            message = f"{sender_name}: {message}"
        else:
            conversation = Conversation.objects.filter(
                pk=self.target_id
            ).filter(Q(user1_id=sender_id) | Q(user2_id=sender_id)).first()
            if conversation is None:
                return
            recipient_id = (conversation.user2_id if conversation.user1_id == sender_id
                            else conversation.user1_id)
            recipients = User.objects.filter(
                pk=recipient_id,
                job_Position__iexact="Team Member",
            )
            url = reverse("chat_room", kwargs={"user_id": sender_id})
            title = f"New message from {sender_name}"

        for recipient in recipients:
            try:
                send_windows_push(
                    recipient=recipient,
                    portal="team_member",
                    title=title,
                    message=message,
                    url=url,
                    tag=(f"teammember-group-{self.target_id}-{message_id}"
                         if self.group_chat else
                         f"teammember-personal-{self.target_id}-{message_id}"),
                )
            except Exception:
                logger.exception("Team Member Chat Push failed for recipient %s", recipient.pk)

    async def chat_change(self, event):
        if not await self.allowed():
            await self.close(code=4403)
            return
        if event.get('user_id') and str(event['user_id']) != str(self.user_id):
            return
        await self.send(text_data=json.dumps({'action': 'sync_messages'}))

    async def chat_message(self, event):
        if not await self.allowed():
            await self.close(code=4403)
            return
        await self.send(text_data=json.dumps({key: value for key, value in event.items() if key != 'type'}))


class MemberGroupChatConsumer(MemberChatConsumer):
    group_chat = True


class LeadGroupChatConsumer(MemberChatConsumer):
    group_chat = True
    allowed_positions = {"team_lead"}


class PersonalChatConsumer(MemberChatConsumer):
    allowed_positions = {"team_lead"}


class AdminChatConsumer(MemberChatConsumer):
    allowed_positions = {"management"}

    @database_sync_to_async
    def is_management_user(self):
        from monitoringapp.models import User
        return User.objects.filter(pk=self.user_id, job_Position__iexact="Management").exists()

    async def allowed(self):
        return await self.is_management_user() and await super().allowed()

    async def save_message(self, message):
        if not await self.is_management_user():
            return None
        return await super().save_message(message)


class AdminGroupChatConsumer(AdminChatConsumer):
    group_chat = True


from .receipt_consumers import ChatUpdatesConsumer


class MasterAdminChatConsumer(MemberChatConsumer):
    allowed_positions = {"master_admin"}

    @database_sync_to_async
    def session_identity(self):
        from monitoringapp.master_chat_identity import master_chat_user
        person = master_chat_user(self.scope.get("user"))
        return (person.pk, "master_admin") if person else (None, "")

    @database_sync_to_async
    def valid_master_identity(self):
        from monitoringapp.master_chat_identity import master_chat_user
        person = master_chat_user(self.scope.get("user"))
        return person is not None and person.pk == self.user_id

    async def allowed(self):
        return await self.valid_master_identity() and await super().allowed()

    async def save_message(self, message):
        if not await self.valid_master_identity():
            return None
        return await super().save_message(message)


class MasterAdminGroupChatConsumer(MasterAdminChatConsumer):
    group_chat = True


class MasterAdminChatUpdatesConsumer(ChatUpdatesConsumer):
    @database_sync_to_async
    def get_user_id(self):
        from monitoringapp.master_chat_identity import master_chat_user
        person = master_chat_user(self.scope.get("user"))
        return person.pk if person else None

    async def chat_invalidate(self, event):
        if not await self.get_user_id():
            await self.close(code=4403)
            return
        await super().chat_invalidate(event)
