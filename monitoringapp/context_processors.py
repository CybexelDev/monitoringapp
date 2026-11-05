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


from django.db.models import Count , Q

from .models import (
    User,
    Announcement,
    TeamLeadNotification,
    AnnouncementRecipient,
    AnnouncementAuthRecipient,
    AdminNotification,
) 


def logged_in_user(request):
    user = None
    is_team_lead = False
    is_team_member = False
    is_master_admin = False
    masteradmin_announcement_unread_count = 0
    notification_counts = {}
    unread_count = 0
    unread_announcement_count = 0
    teammember_announcement_unread_count = 0
    is_admin_portal = False
    admin_announcement_unread_count = 0


    user_id = request.session.get("user_id")

    if user_id:
        try:
            user = User.objects.get(pk=user_id)
            is_team_lead = (
                (user.job_Position or "").strip().lower() == "team lead"
            )
            is_team_member = (user.job_Position or "").strip().lower() == "team member"
            is_master_admin = (
                (user.job_Position or "").strip().lower() == "master admin")
            is_admin_portal = (
                (user.job_Position or "").strip().lower() == "admin"
)
        except (User.DoesNotExist, ValueError, TypeError):
            pass

    if user and is_team_member:
        teammember_announcement_unread_count = AnnouncementRecipient.objects.filter(
        recipient=user,
        announcement__is_active=True,
        read_at__isnull=True,
    ).filter(
        Q(announcement__is_admin_announcement=True)
        | Q(announcement__created_by__job_Position__iexact="Team Lead")
    ).count()

    if user and is_team_lead:
            unread_announcement_count = AnnouncementRecipient.objects.filter(
            recipient=user,
            announcement__is_active=True,
            announcement__is_admin_announcement=True,
            read_at__isnull=True,
        ).count()

    admin_announcement_unread_count = 0

    if user and is_admin_portal:

        # 1. Active Team Lead announcements only
        active_lead_ids = Announcement.objects.filter(
            is_admin_announcement=False,
            is_master_admin_announcement=False,
            is_active=True,
            created_by__job_Position__iexact="Team Lead",
        ).values_list("pk", flat=True)

        lead_event_keys = [
            f"feed:announcement:{announcement_id}:published:management_owner_id:{user.pk}"
            for announcement_id in active_lead_ids
        ]

        team_lead_unread_count = AdminNotification.objects.filter(
            management_owner=user,
            auth_owner__isnull=True,
            kind="announcement",
            is_read=False,
            is_archived=False,
            event_key__in=lead_event_keys,
        ).count()

        # 2. Active Master Admin announcements addressed to this Admin
        active_master_ids = Announcement.objects.filter(
            is_master_admin_announcement=True,
            is_active=True,
            recipients__recipient=user,
        ).values_list("pk", flat=True).distinct()

        master_event_keys = [
            f"master-announcement:{announcement_id}:employee:{user.pk}"
            for announcement_id in active_master_ids
        ]

        master_unread_count = AdminNotification.objects.filter(
            management_owner=user,
            auth_owner__isnull=True,
            kind="announcement",
            is_read=False,
            is_archived=False,
            event_key__in=master_event_keys,
        ).count()

        # Only Team Lead + Master Admin unread announcements
        admin_announcement_unread_count = (
            team_lead_unread_count + master_unread_count
        )

    # if user and is_master_admin:
    #     masteradmin_unread_ids = set(
    #         AnnouncementRecipient.objects.filter(
    #             recipient=user,
    #             announcement__is_active=True,
    #             read_at__isnull=True,
    #         ).values_list("announcement_id", flat=True)
    #     )

    #     masteradmin_unread_ids.update(
    #         AnnouncementAuthRecipient.objects.filter(
    #             recipient=user,
    #             announcement__is_active=True,
    #             read_at__isnull=True,
    #         ).values_list("announcement_id", flat=True)
    #     )

    #     masteradmin_announcement_unread_count = len(masteradmin_unread_ids)
    if user and is_master_admin:
        announcement_scope = (
            Q(
                announcement__is_admin_announcement=True,
                announcement__is_master_admin_announcement=False,
            )
            | Q(
                announcement__is_admin_announcement=False,
                announcement__is_master_admin_announcement=False,
                announcement__created_by__job_Position__iexact="Team Lead",
            )
        )

        masteradmin_unread_ids = set()

        # Team Lead announcements received through monitoringapp.User
        masteradmin_unread_ids.update(
            AnnouncementRecipient.objects.filter(
                recipient=user,
                announcement__is_active=True,
                read_at__isnull=True,
            ).filter(
                announcement_scope
            ).values_list("announcement_id", flat=True)
        )

        # Admin / Team Lead announcements received through auth.User
        if request.user.is_authenticated and request.user.is_active:
            masteradmin_unread_ids.update(
                AnnouncementAuthRecipient.objects.filter(
                    recipient=request.user,
                    announcement__is_active=True,
                    read_at__isnull=True,
                ).filter(
                    announcement_scope
                ).values_list("announcement_id", flat=True)
            )

        masteradmin_announcement_unread_count = len(masteradmin_unread_ids)

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
        "teamlead_announcement_unread_count": unread_announcement_count,
        "teammember_announcement_unread_count": teammember_announcement_unread_count,
        "is_master_admin": is_master_admin,
        "masteradmin_announcement_unread_count": masteradmin_announcement_unread_count,
        "is_admin_portal": is_admin_portal,
        "admin_announcement_unread_count": admin_announcement_unread_count,
        "debug_session_user_id": request.session.get("user_id"),
        "debug_master_admin": is_master_admin,
    }