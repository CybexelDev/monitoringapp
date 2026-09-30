
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class PersonalChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        print(
            f"WebSocket CONNECTED: conversation={self.conversation_id}"
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

        print(
            f"WebSocket DISCONNECTED: conversation={self.conversation_id}"
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        message = data.get("message", "").strip()
        sender_id = data.get("sender_id")

        if not message or not sender_id:
            return

        result = await self.save_message(
            message,
            sender_id,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": result["message"],
                "message_id": result["message_id"],
                "sender_id": result["sender_id"],
                "sender": result["sender"],
                "sender_profile": result["sender_profile"],
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps({
                "message": event["message"],
                "message_id": event["message_id"],
                "sender_id": event["sender_id"],
                "sender": event["sender"],
                "sender_profile": event["sender_profile"],
            })
        )

    @database_sync_to_async
    def save_message(self, message, sender_id):
        from .models import Conversation, ChatMessage

        conversation = Conversation.objects.select_related(
            "user1",
            "user2",
        ).get(id=self.conversation_id)

        if str(sender_id) == str(conversation.user1.id):
            sender = conversation.user1

        elif str(sender_id) == str(conversation.user2.id):
            sender = conversation.user2

        else:
            raise ValueError(
                "User is not a member of this conversation."
            )

        chat_message = ChatMessage.objects.create(
            conversation=conversation,
            sender=sender,
            content=message,
        )

        return {
            "message_id": chat_message.id,
            "message": chat_message.content,
            "sender_id": sender.id,
            "sender": sender.name,
            "sender_profile": (
                sender.profile_image.url
                if sender.profile_image
                else None
            ),
        }