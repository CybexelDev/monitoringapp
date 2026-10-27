

from django.urls import path, re_path
from . import views
from . import chat_receipts
from . import chat_push


urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login_view"),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path("admin_dashboard", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/notepad/", views.admin_notepad, name="admin_notepad"),
path(
    "admin-panel/notepad/<int:pk>/delete/",
    views.admin_notepad_delete,
    name="admin_notepad_delete",
),
path(
    "admin-panel/repository/",
    views.admin_repository,
    name="admin_repository",
),
path(
    "admin-panel/repository/<int:pk>/delete/",
    views.admin_repository_delete,
    name="admin_repository_delete",
),
path(
    "admin-panel/repository/<int:pk>/file/",
    views.admin_repository_file,
    name="admin_repository_file",
),
path(
    "admin-panel/announcements/",
    views.admin_announcements,
    name="admin_announcements",
),
path(
    "teamlead/announcements/<int:pk>/admin-seen/",
    views.teamlead_admin_announcement_seen,
    name="teamlead_admin_announcement_seen",
),
path(
    "admin-panel/google-meet/",
    views.admin_google_meet,
    name="admin_google_meet",
),

    path(
        "delete-department/<int:pk>/", views.delete_department, name="delete_department"
    ),
    path("delete-team/<int:pk>/", views.delete_team, name="delete_team"),
    path(
        "admin_usermanagement", views.admin_usermanagement, name="admin_usermanagement"
    ),
path("admin-chat/<int:user_id>/", views.admin_chat_room, name="admin_chat_room"),
path("admin-chat/group/<int:group_id>/", views.admin_group_chat, name="admin_group_chat"),
path(
    "api/chat/meta/",
    chat_receipts.chat_meta,
    name="chat_meta",
),
path(
    "api/chat/read/",
    chat_receipts.chat_mark_read,
    name="chat_mark_read",
),
path("admin-panel/notifications/", views.admin_notifications, name="admin_notifications"),
path("admin-panel/notifications/read-all/", views.admin_notifications_read_all, name="admin_notifications_read_all"),
path("admin-panel/notifications/<int:notification_id>/open/", views.admin_notification_open, name="admin_notification_open"),
path("admin-panel/reminders/", views.admin_reminders, name="admin_reminders"),


    path("delete/<int:id>/", views.delete_user, name="delete_user"),
    path("edit-user/", views.edit_user, name="edit_user"),
    path("add-contact/", views.add_contact, name="add_contact"),
    path("admin_reports/", views.admin_reports, name="admin_reports"),
    path("admin-chat/", views.admin_chat, name="admin_chat"),
    path("admin_profile/", views.admin_profile, name="admin_profile"),
    path("teammember_project/", views.teammember_project, name="teammember_project"),
    path(
        "project/<int:pk>/update-status/",
        views.update_project_status,
        name="update_project_status",
    ),
    path(
        "api/logged-in-user/",
        views.get_logged_in_user_api,
        name="get_logged_in_user_api",
    ),
    path("api/update-activity/", views.update_activity, name="update_activity"),
    path(
        "api/user-status/<int:user_id>/", views.get_user_status, name="get_user_status"
    ),
    path("teamlead/dashboard/", views.teamlead_dashboard, name="teamlead_dashboard"),
    path("teamlead_reports", views.teamlead_reports, name="teamlead_reports"),
    path(
        "teamlead/edit-member/",
        views.teamlead_edit_member,
        name="teamlead_edit_member",
    ),
    path(
        "teamlead_project_assigning",
        views.teamlead_project_assigning,
        name="teamlead_project_assigning",
    ),
    path(
        "projects/edit/<int:pk>/", views.project_assign_edit, name="project_assign_edit"
    ),
    path(
        "projects/delete/<int:pk>/",
        views.project_assign_delete,
        name="project_assign_delete",
    ),
    path(
        "teamlead/announcements/",
        views.teamlead_announcements,
        name="teamlead_announcements",
    ),
    path("teamlead_repository/", views.teamlead_repository, name="teamlead_repository"),
    path(
        "teamlead_repository/delete/<int:pk>/",
        views.teamlead_repository_delete,
        name="teamlead_repository_delete",
    ),
    path("teamlead_profile/", views.teamlead_profile, name="teamlead_profile"),
    path(
        "teamlead_google_meet/",
        views.teamlead_google_meet,
        name="teamlead_google_meet",
    ),
    path("teamlead_chat/", views.teamlead_chat, name="teamlead_chat"),
    path(
        "teamlead_chat/<int:user_id>/",
        views.teamlead_chat_room,
        name="teamlead_chat_room",
    ),
    path(
        "teamlead_chat/group/<int:group_id>/",
        views.teamlead_group_chat_view,
        name="teamlead_group_chat_view",
    ),
    path("teamlead_notepad/", views.teamlead_notepad, name="teamlead_notepad"),
    path(
        "teamlead_notepad/delete/<int:pk>/",
        views.teamlead_notepad_delete,
        name="teamlead_notepad_delete",
    ),
    path("teamlead_task/", views.teamlead_task, name="teamlead_task"),
    path(
        "teamlead_task/update/<int:task_id>/",
        views.update_task_teamlead,
        name="update_task_teamlead",
    ),
    path(
        "teamlead_task/delete/<int:task_id>/",
        views.delete_task_teamlead,
        name="delete_task_teamlead",
    ),

    path("teamlead/logout/", views.teamlead_logout, name="teamlead_logout"),
    # path("teammember_chat/", views.teammember_chat, name="teammember_chat"),
    path("chat/", views.teammember_chat, name="teammember_chat"),
    path("chat/<int:user_id>/", views.teammember_chat_room, name="teammember_chat_room"),
    path("chat/<int:user_id>/", views.teammember_chat_room, name="chat_room"),
    path("chat/group/<int:group_id>/", views.teammember_group_chat, name="teammember_group_chat"),
    path("chat/group/<int:group_id>/", views.teammember_group_chat, name="group_chat_view"),
    path(
        "teamlead/notifications/",
        views.teamlead_notifications,
        name="teamlead_notifications",
    ),
    path(
        "teamlead/notifications/read-all/",
        views.teamlead_notifications_read_all,
        name="teamlead_notifications_read_all",
    ),
    path(
        "teamlead/notifications/<int:notification_id>/open/",
        views.teamlead_notification_open,
        name="teamlead_notification_open",
    ),
    path(
        "teamlead/reminders/",
        views.teamlead_reminders,
        name="teamlead_reminders",
    ),
    # <---TEAM MEMBERS--->
    path("teammember/logout/", views.teammember_logout, name="teammember_logout"),
        path(
        "teammember_task/update/<int:task_id>/", views.update_task, name="update_task"
    ),
    path(
        "teammember_task/delete/<int:task_id>/", views.delete_task, name="delete_task"
    ),
        path(
        "teammember_repository/",
        views.teammember_repository,
        name="teammember_repository",
    ),
    path("teammember_profile/", views.teammember_profile, name="teammember_profile"),
    path("teammember_task/", views.teammember_task, name="teammember_task"),
    path(
        "teammember_repository/delete/<int:pk>/",
        views.teammember_repository_delete,
        name="teammember_repository_delete",
    ),
    path("teammember_notepad/", views.teammember_notepad, name="teammember_notepad"),
    path(
        "teammember_notepad/delete/<int:pk>/",
        views.teammember_notepad_delete,
        name="teammember_notepad_delete",
    ),
    path(
        "teammember_google_meet/",
        views.teammember_google_meet,
        name="teammember_google_meet",
    ),
        path(
        "teammember/dashboard/", views.teammember_dashboard, name="teammember_dashboard"
    ),
        path("teammember_reports/", views.teammember_reports, name="teammember_reports"),
    path("teammember/announcements/", views.teammember_announcements, name="teammember_announcements"),
path("teammember/announcements/<int:pk>/seen/", views.teammember_announcement_seen, name="teammember_announcement_seen"),
path("teammember/reminders/", views.teammember_reminders, name="teammember_reminders"),

path("teammember/notifications/", views.teammember_notifications, name="teammember_notifications"),
path("teammember/notifications/read-all/", views.teammember_notifications_read_all, name="teammember_notifications_read_all"),
path("teammember/notifications/<int:notification_id>/open/", views.teammember_notification_open, name="teammember_notification_open"),

path(
    "teammember_project/<int:pk>/seen/",
    views.teammember_project_seen,
    name="teammember_project_seen",
),

path(
    "api/chat/meta/",
    chat_receipts.chat_meta,
    name="chat_meta",
),
path(
    "api/chat/read/",
    chat_receipts.chat_mark_read,
    name="chat_mark_read",
),

#<----------------------ACCOUNTS TEAM--------------------->

path("accounts/dashboard/", views.accounts_dashboard, name="accounts_dashboard"),
path("accounts/logout/", views.accounts_logout, name="accounts_logout"),
path("accounts/income/", views.accounts_income, name="accounts_income"),
path(
    "accounts/income/<int:pk>/edit/",
    views.accounts_income_edit,
    name="accounts_income_edit",
),
path(
    "accounts/income/<int:pk>/delete/",
    views.accounts_income_delete,
    name="accounts_income_delete",
),
path(
    "accounts/expenses/",
    views.accounts_expenses,
    name="accounts_expenses",
),
path(
    "accounts/expenses/<int:pk>/edit/",
    views.accounts_expense_edit,
    name="accounts_expense_edit",
),
path(
    "accounts/expenses/<int:pk>/delete/",
    views.accounts_expense_delete,
    name="accounts_expense_delete",
),
path(
    "accounts/sales/",
    views.accounts_sales,
    name="accounts_sales",
),
path(
    "accounts/sales/<int:pk>/edit/",
    views.accounts_sale_edit,
    name="accounts_sale_edit",
),
path(
    "accounts/sales/<int:pk>/delete/",
    views.accounts_sale_delete,
    name="accounts_sale_delete",
),
path("accounts/expenses/<int:pk>/receipt/", views.accounts_expense_receipt, name="accounts_expense_receipt"),
path("accounts/expenses/<int:pk>/history/", views.accounts_expense_history, name="accounts_expense_history"),
path("accounts/income/<int:pk>/receipt/", views.accounts_income_receipt, name="accounts_income_receipt"),
path("accounts/income/<int:pk>/history/", views.accounts_income_history, name="accounts_income_history"),
path("accounts/sales/<int:pk>/invoice/", views.accounts_sale_invoice, name="accounts_sale_invoice"),
path("accounts/sales/<int:pk>/payments/", views.accounts_sale_payments, name="accounts_sale_payments"),
path(
    "accounts/notifications/",
    views.accounts_notifications,
    name="accounts_notifications",
),
path(
    "accounts/notifications/read-all/",
    views.accounts_notifications_read_all,
    name="accounts_notifications_read_all",
),
path(
    "accounts/notifications/<int:pk>/action/",
    views.accounts_notification_action,
    name="accounts_notification_action",
),
path(
    "accounts/reminders/",
    views.accounts_reminders,
    name="accounts_reminders",
),
path("accounts/notepad/", views.accounts_notepad, name="accounts_notepad"),
path(
    "accounts/notepad/delete/<int:pk>/",
    views.accounts_notepad_delete,
    name="accounts_notepad_delete",
),
path("accounts/profile/", views.accounts_profile, name="accounts_profile"),
    path("master-admin/login/", views.master_admin_login, name="master_admin_login"),
    path("master-admin/logout/", views.master_admin_logout, name="master_admin_logout"),
    path("master-admin/dashboard/", views.master_admin_dashboard, name="master_admin_dashboard"),
    path("master-admin/users/", views.master_admin_usermanagement, name="master_admin_usermanagement"),
    path("master-admin/users/edit/", views.master_admin_edit_user, name="master_admin_edit_user"),
    path("master-admin/users/<int:pk>/delete/", views.master_admin_delete_user, name="master_admin_delete_user"),
    path("master-admin/departments/", views.master_admin_departments, name="master_admin_departments"),
    path("master-admin/reports/", views.master_admin_reports, name="master_admin_reports"),
path("master-admin/accounts/income/", views.master_admin_accounts_income, name="master_admin_accounts_income"),
path("master-admin/accounts/income/<int:pk>/edit/", views.master_admin_accounts_income_edit, name="master_admin_accounts_income_edit"),
path("master-admin/accounts/income/<int:pk>/delete/", views.master_admin_accounts_income_delete, name="master_admin_accounts_income_delete"),
path("master-admin/accounts/income/<int:pk>/receipt/", views.master_admin_accounts_income_receipt, name="master_admin_accounts_income_receipt"),
path("master-admin/accounts/income/<int:pk>/history/", views.master_admin_accounts_income_history, name="master_admin_accounts_income_history"),
path("master-admin/accounts/expenses/", views.master_admin_accounts_expenses, name="master_admin_accounts_expenses"),
path("master-admin/accounts/expense/<int:pk>/edit/", views.master_admin_accounts_expense_edit, name="master_admin_accounts_expense_edit"),
path("master-admin/accounts/expense/<int:pk>/delete/", views.master_admin_accounts_expense_delete, name="master_admin_accounts_expense_delete"),
path("master-admin/accounts/expense/<int:pk>/receipt/", views.master_admin_accounts_expense_receipt, name="master_admin_accounts_expense_receipt"),
path("master-admin/accounts/expense/<int:pk>/history/", views.master_admin_accounts_expense_history, name="master_admin_accounts_expense_history"),
path("master-admin/accounts/sales/", views.master_admin_accounts_sales, name="master_admin_accounts_sales"),
path("master-admin/accounts/sale/<int:pk>/edit/", views.master_admin_accounts_sale_edit, name="master_admin_accounts_sale_edit"),
path("master-admin/accounts/sale/<int:pk>/delete/", views.master_admin_accounts_sale_delete, name="master_admin_accounts_sale_delete"),
path("master-admin/accounts/sale/<int:pk>/invoice/", views.master_admin_accounts_sale_invoice, name="master_admin_accounts_sale_invoice"),
path("master-admin/accounts/sale/<int:pk>/payments/", views.master_admin_accounts_sale_payments, name="master_admin_accounts_sale_payments"),
path("master-admin/accounts/", views.master_admin_accounts_overview, name="master_admin_accounts_overview"),
path("master-admin/tasks/", views.master_admin_tasks, name="master_admin_tasks"),
path("master-admin/tasks/<int:pk>/update/", views.master_admin_task_update, name="master_admin_task_update"),
path("master-admin/tasks/<int:pk>/delete/", views.master_admin_task_delete, name="master_admin_task_delete"),
path("master-admin/projects/", views.master_admin_projects, name="master_admin_projects"),
path("master-admin/projects/<int:pk>/update/", views.master_admin_project_update, name="master_admin_project_update"),
path("master-admin/projects/<int:pk>/delete/", views.master_admin_project_delete, name="master_admin_project_delete"),
path("master-admin/announcements/", views.master_admin_announcements, name="master_admin_announcements"),
path("portal/announcements/<int:pk>/", views.portal_announcement_detail, name="portal_announcement_detail"),
path("portal/announcements/<int:pk>/seen/", views.portal_announcement_seen, name="portal_announcement_seen"),
path("master-admin/repository/", views.master_admin_repository, name="master_admin_repository"),
path("master-admin/repository/<str:source>/<int:pk>/update/", views.master_admin_repository_update, name="master_admin_repository_update"),
path("master-admin/repository/<str:source>/<int:pk>/delete/", views.master_admin_repository_delete, name="master_admin_repository_delete"),
path("master-admin/repository/<str:source>/<int:pk>/file/", views.master_admin_repository_file, name="master_admin_repository_file"),
path("master-admin/google-meet/", views.master_admin_google_meet, name="master_admin_google_meet"),
path("master-admin/google-meet/<int:pk>/delete/", views.master_admin_google_meet_delete, name="master_admin_google_meet_delete"),
path("master-admin/notifications/", views.master_admin_notifications, name="master_admin_notifications"),
path("master-admin/notifications/<int:pk>/action/", views.master_admin_notification_action, name="master_admin_notification_action"),
path("master-admin/reminders/", views.master_admin_reminders, name="master_admin_reminders"),
path("master-admin/notepad/", views.master_admin_notepad, name="master_admin_notepad"),
path("master-admin/notepad/<int:pk>/delete/", views.master_admin_notepad_delete, name="master_admin_notepad_delete"),
path("master-admin/profile/", views.master_admin_profile, name="master_admin_profile"),
path("master-admin/chat/", views.master_admin_chat, name="master_admin_chat"),
path("master-admin/chat/<int:user_id>/", views.master_admin_chat_room, name="master_admin_chat_room"),
path("master-admin/group/<int:group_id>/", views.master_admin_group_chat, name="master_admin_group_chat"),
path("master-admin/chat/meta/", views.master_admin_chat_meta, name="master_admin_chat_meta"),
path("master-admin/chat/read/", views.master_admin_chat_read, name="master_admin_chat_read"),
path("api/chat/push/<str:portal>/config/", chat_push.config, name="chat_push_config"),
path("api/chat/push/<str:portal>/subscribe/", chat_push.subscribe, name="chat_push_subscribe"),
path("api/chat/push/<str:portal>/unsubscribe/", chat_push.unsubscribe, name="chat_push_unsubscribe"),



]
