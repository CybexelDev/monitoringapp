# from django.db.models import Count

# from .models import User, TeamLeadNotification


# def logged_in_user(request):
#     user = None
#     is_team_lead = False
#     notification_counts = {}
#     unread_count = 0

#     user_id = request.session.get("user_id")

#     if user_id:
#         try:
#             user = User.objects.get(pk=user_id)
#             is_team_lead = (
#                 (user.job_Position or "").strip().lower() == "team lead"
#             )
#         except (User.DoesNotExist, ValueError, TypeError):
#             pass

#     if user and is_team_lead:
#         unread_notifications = (
#             TeamLeadNotification.objects
#             .filter(recipient=user, is_read=False,is_archived=False,)
#             .values("kind")
#             .annotate(total=Count("id"))
#         )

#         notification_counts = {
#             item["kind"]: item["total"]
#             for item in unread_notifications
#         }
#         unread_count = sum(notification_counts.values())

#     return {
#         "logged_in_user": user,
#         "is_team_lead": is_team_lead,
#         "teamlead_unread_count": unread_count,
#         "teamlead_notification_counts": notification_counts,
#     }


from django.db.models import Count

from .models import User, TeamLeadNotification


def logged_in_user(request):
    user = None
    is_team_lead = False
    is_team_member = False
    notification_counts = {}
    unread_count = 0

    user_id = request.session.get("user_id")

    if user_id:
        try:
            user = User.objects.get(pk=user_id)
            is_team_lead = (
                (user.job_Position or "").strip().lower() == "team lead"
            )
            is_team_member = (user.job_Position or "").strip().lower() == "team member"
        except (User.DoesNotExist, ValueError, TypeError):
            pass

    if user and (is_team_lead or is_team_member):
        unread_notifications = (
            TeamLeadNotification.objects
            .filter(recipient=user, is_read=False,is_archived=False,)
            .values("kind")
            .annotate(total=Count("id"))
        )

        notification_counts = {
            item["kind"]: item["total"]
            for item in unread_notifications
        }
        unread_count = sum(notification_counts.values())

    return {
        "logged_in_user": user,
        "is_team_lead": is_team_lead,
        "teamlead_unread_count": unread_count if is_team_lead else 0,
        "teammember_unread_count": unread_count if is_team_member else 0,
        "teammember_notification_counts": notification_counts if is_team_member else {},
        "teamlead_notification_counts": notification_counts if is_team_lead else {},
    }