from django.shortcuts import render
from monitoringapp.models import User


def personal_chat(request):

    current_user_id = request.session.get("user_id")

    if not current_user_id:
        return render(
            request,
            "chat/chat.html",
            {
                "users": [],
                "current_user": None,
            }
        )

    try:
        current_user = User.objects.get(id=current_user_id)
    except User.DoesNotExist:
        request.session.flush()
        return render(
            request,
            "chat/chat.html",
            {
                "users": [],
                "current_user": None,
            }
        )

    # Chat list:
    # Admin + Team Lead + Team Member
    # Current logged-in user മാത്രം ഒഴിവാക്കുന്നു
    users = User.objects.exclude(
        id=current_user.id
    ).order_by("name")

    return render(
        request,
        "chat/chat.html",
        {
            "users": users,
            "current_user": current_user,
        }
    )


from django.http import JsonResponse
from .models import Conversation


def get_or_create_conversation(request, user_id):

    current_user_id = request.session.get("user_id")

    if not current_user_id:
        return JsonResponse(
            {
                "success": False,
                "message": "User not authenticated",
            },
            status=401,
        )

    try:
        current_user = User.objects.get(id=current_user_id)
        selected_user = User.objects.get(id=user_id)

    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "User not found",
            },
            status=404,
        )

    if current_user.id == selected_user.id:
        return JsonResponse(
            {
                "success": False,
                "message": "You cannot chat with yourself",
            },
            status=400,
        )

    conversation = Conversation.objects.filter(
        user1=current_user,
        user2=selected_user,
    ).first()

    if not conversation:
        conversation = Conversation.objects.filter(
            user1=selected_user,
            user2=current_user,
        ).first()

    if not conversation:
        conversation = Conversation.objects.create(
            user1=current_user,
            user2=selected_user,
        )

    return JsonResponse(
        {
            "success": True,
            "conversation_id": conversation.id,
            "user_id": selected_user.id,
            "user_name": selected_user.name,
        }
    )