import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.joined = False
        self.user_id = await self.get_user_id()

        if not self.user_id:
            await self.close(code=4403)
            return

        self.update_group = f"chat_receipts_user_{self.user_id}"

        await self.channel_layer.group_add(
            self.update_group,
            self.channel_name,
        )

        self.joined = True
        await self.accept()

    @database_sync_to_async
    def get_user_id(self):
        from monitoringapp.models import User

        session = self.scope.get("session", {})
        position = (
            str(session.get("position", ""))
            .strip()
            .lower()
            .replace(" ", "_")
        )

        if position not in {"team_member", "team_lead"}:
            return None

        user_id = session.get("user_id")

        return (
            User.objects.filter(pk=user_id)
            .values_list("pk", flat=True)
            .first()
        )

    async def disconnect(self, close_code):
        if getattr(self, "joined", False):
            await self.channel_layer.group_discard(
                self.update_group,
                self.channel_name,
            )

    async def chat_invalidate(self, event):
        await self.send(
            text_data=json.dumps({
                "action": "sync_chat_meta",
            })
        )