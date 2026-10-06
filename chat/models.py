from django.db import models

# Create your models here.


from django.db import models
from monitoringapp.models import User


class Conversation(models.Model):
    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_conversations_as_user1",
    )

    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_conversations_as_user2",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user1", "user2"],
                name="unique_chat_conversation",
            )
        ]

    def __str__(self):
        return f"{self.user1.name} - {self.user2.name}"


# class ChatMessage(models.Model):
#     conversation = models.ForeignKey(
#         Conversation,
#         on_delete=models.CASCADE,
#         related_name="messages",
#     )

#     sender = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="sent_chat_messages",
#     )

#     content = models.TextField()

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ["created_at"]

#     def __str__(self):
#         return f"{self.sender.name}: {self.content[:30]}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_for_everyone = models.BooleanField(default=False)
    hidden_for = models.ManyToManyField(User, blank=True, related_name="%(app_label)s_%(class)s_hidden_messages")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.name}: {self.content[:30]}"

    