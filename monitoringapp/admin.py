from django.contrib import admin
from . models import *

admin.site.register(Department)
admin.site.register(Team)
admin.site.register(User)
admin.site.register(Announcement)
admin.site.register(MorningReport)
admin.site.register(EveningReport)
admin.site.register(ProjectAssign)
admin.site.register(Notepad)
admin.site.register(Knowledge)
admin.site.register(Task)
admin.site.register(ProjectFile)
admin.site.register(ProjectImage)
admin.site.register(ExtraContact)


# Additional Backend Models

admin.site.register([
    # Announcement
    AnnouncementRecipient,
    AnnouncementAuthRecipient,

    # Reports
    ReportTimeSetting,
    ReportDateSchedule,
    ReportDefaultSchedule,

    # Chat
    ChatRoom,
    Message,
    Group,
    GroupMember,
    GroupMessage,
    ChatReadState,
    MasterAdminChatIdentity,
    ChatPushSubscription,

    # Meetings
    GoogleMeeting,

    # Team Lead
    TeamReportLeave,
    TeamLeadNotification,
    TeamLeadReminder,

    # Accounts
    AccountsIncome,
    AccountsIncomeHistory,
    AccountsExpense,
    AccountsExpenseHistory,
    AccountsSale,
    AccountsSalePayment,
    AccountsNotification,
    AccountsReminder,

    # Admin
    AdminNotepad,
    AdminKnowledge,
    AdminNotification,
    AdminReminder,

    # Master Admin
    Designation,
    MasterAdminAccountsAudit,
    MasterAdminTaskAudit,
    MasterAdminProjectAudit,
    MasterAdminProfile,
])

