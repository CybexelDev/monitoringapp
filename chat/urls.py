from django.urls import path

from .views import personal_chat, get_or_create_conversation


urlpatterns = [
    path(
        "personal/",
        personal_chat,
        name="personal_chat",
    ),

    path(
        "conversation/<int:user_id>/",
        get_or_create_conversation,
        name="get_or_create_conversation",
    ),
]