from django.urls import re_path

from .consumers import (
    MemberChatConsumer,
    MemberGroupChatConsumer,
    PersonalChatConsumer,
    AdminChatConsumer,
    AdminGroupChatConsumer,
    LeadGroupChatConsumer,
)
from .receipt_consumers import ChatUpdatesConsumer


websocket_urlpatterns = [
    re_path(r"^ws/admin/chat/(?P<conversation_id>\d+)/$", AdminChatConsumer.as_asgi()),
    re_path(r"^ws/admin/group/(?P<group_id>\d+)/$", AdminGroupChatConsumer.as_asgi()),
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


from .consumers import MasterAdminChatConsumer, MasterAdminGroupChatConsumer, MasterAdminChatUpdatesConsumer

websocket_urlpatterns += [
    re_path(r"^ws/master/chat/(?P<conversation_id>\d+)/$", MasterAdminChatConsumer.as_asgi()),
    re_path(r"^ws/master/group/(?P<group_id>\d+)/$", MasterAdminGroupChatConsumer.as_asgi()),
    re_path(r"^ws/master/chat-updates/$", MasterAdminChatUpdatesConsumer.as_asgi()),
]
