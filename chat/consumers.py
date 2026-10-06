"""Authenticated personal/group sockets shared by Team Lead and Team Member."""
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from monitoringapp.chat_receipts import broadcast_chat_activity

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
