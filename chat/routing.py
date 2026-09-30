

from django.urls import re_path

from .consumers import PersonalChatConsumer
from monitoringapp.consumers import GroupChatConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/chat/(?P<conversation_id>\d+)/$",
        PersonalChatConsumer.as_asgi(),
    ),
    re_path(
        r"^ws/chat/group/(?P<group_id>\d+)/$",
        GroupChatConsumer.as_asgi(),
    ),
]