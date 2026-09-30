# # consumers.py
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_id = self.scope['url_route']['kwargs']['room_id']
#         self.room_group_name = f'chat_{self.room_id}'
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         from .models import User, ChatRoom, Message
#         data = json.loads(text_data)
#         message = data['message']
#         sender_id = data['sender_id']

#         sender = await database_sync_to_async(User.objects.get)(id=sender_id)
#         room = await database_sync_to_async(ChatRoom.objects.get)(id=self.room_id)

#         await database_sync_to_async(Message.objects.create)(
#             room=room, sender=sender, content=message
#         )

#         # ✅ Include sender_id and sender_profile
#         sender_profile = sender.profile_image.url if sender.profile_image else None

#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'sender': sender.name,
#                 'sender_id': sender.id,              # ✅ include sender_id
#                 'sender_profile': sender_profile,    # ✅ optional
#             }
#         )

#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             'message': event['message'],
#             'sender': event['sender'],
#             'sender_id': event['sender_id'],            # ✅ include this
#             'sender_profile': event['sender_profile'],  # ✅ optional
#         }))



# class GroupChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.group_id = self.scope['url_route']['kwargs']['group_id']
#         self.room_group_name = f"group_{self.group_id}"

#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()

#         # Send previous messages
#         from .models import GroupMessage
#         old_messages = await database_sync_to_async(list)(
#             GroupMessage.objects.filter(group_id=self.group_id).order_by('timestamp').values(
#                 'sender__id', 'sender__name', 'message', 'timestamp'
#             )
#         )

#         for msg in old_messages:
#             await self.send(text_data=json.dumps({
#                 'message': msg['message'],
#                 'sender': msg['sender__name'],
#                 'sender_id': msg['sender__id'],
#                 'timestamp': msg['timestamp'].isoformat() if hasattr(msg['timestamp'], 'isoformat') else msg[
#                     'timestamp']
#             }))

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         from .models import Group, GroupMessage, User  # ✅ lazy import

#         data = json.loads(text_data)
#         message = data.get('message')
#         sender_id = data.get('sender_id')

#         if not message or not sender_id:
#             return

#         group = await database_sync_to_async(Group.objects.get)(id=self.group_id)
#         sender = await database_sync_to_async(User.objects.get)(id=sender_id)

#         # Save message
#         group_message = await database_sync_to_async(GroupMessage.objects.create)(
#             group=group, sender=sender, message=message
#         )

#         # Broadcast to group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': group_message.message,
#                 'sender': sender.name,
#                 'sender_id': sender.id,
#                 'timestamp': group_message.timestamp.isoformat()
#             }
#         )

#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps(event))



# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        from .models import User, ChatRoom, Message
        data = json.loads(text_data)
        message = data['message']
        sender_id = data['sender_id']

        sender = await database_sync_to_async(User.objects.get)(id=sender_id)
        room = await database_sync_to_async(ChatRoom.objects.get)(id=self.room_id)

        await database_sync_to_async(Message.objects.create)(
            room=room, sender=sender, content=message
        )

        # ✅ Include sender_id and sender_profile
        sender_profile = sender.profile_image.url if sender.profile_image else None

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.name,
                'sender_id': sender.id,              # ✅ include sender_id
                'sender_profile': sender_profile,    # ✅ optional
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],            # ✅ include this
            'sender_profile': event['sender_profile'],  # ✅ optional
        }))



class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f"group_{self.group_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        from .models import Group, GroupMessage, User  # ✅ lazy import

        data = json.loads(text_data)
        message = data.get('message')
        sender_id = data.get('sender_id')

        if not message or not sender_id:
            return

        group = await database_sync_to_async(Group.objects.get)(id=self.group_id)
        sender = await database_sync_to_async(User.objects.get)(id=sender_id)

        # Save message
        group_message = await database_sync_to_async(GroupMessage.objects.create)(
            group=group, sender=sender, message=message
        )

        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': group_message.message,
                'sender': sender.name,
                'sender_id': sender.id,
                'timestamp': group_message.timestamp.isoformat()
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
