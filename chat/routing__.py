from django.urls import re_path

from .consumers import (
    MemberChatConsumer,
    MemberGroupChatConsumer,
    PersonalChatConsumer,
    LeadGroupChatConsumer,
)
from .receipt_consumers import ChatUpdatesConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/member/chat/(?P<conversation_id>\d+)/$",
        MemberChatConsumer.as_asgi(),
    ),
    re_path(
        r"^ws/member/group/(?P<group_id>\d+)/$",
        MemberGroupChatConsumer.as_asgi(),
    ),
    re_path(
        r"^ws/chat/(?P<conversation_id>\d+)/$",
        PersonalChatConsumer.as_asgi(),
    ),
    re_path(
        r"^ws/chat/group/(?P<group_id>\d+)/$",
        LeadGroupChatConsumer.as_asgi(),
    ),
    re_path(
        r"^ws/member/chat-updates/$",
        ChatUpdatesConsumer.as_asgi(),
    ),
]
