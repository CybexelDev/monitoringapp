from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login_view'),
    path('admin_login', views.admin_login, name='admin_login'),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('delete-department/<int:pk>/', views.delete_department, name='delete_department'),
    path('delete-team/<int:pk>/', views.delete_team, name='delete_team'),
    path('admin_usermanagement', views.admin_usermanagement, name='admin_usermanagement'),
    path('delete/<int:id>/', views.delete_user, name='delete_user'),
    path('edit-user/', views.edit_user, name='edit_user'),
    path("add-contact/", views.add_contact, name="add_contact"),
    path("admin_reports/", views.admin_reports, name="admin_reports"),
    
    path("admin-chat/", views.admin_chat, name="admin_chat"),  
    path("admin_profile/", views.admin_profile, name="admin_profile"), 
   




    path('teammember_project/', views.teammember_project, name='teammember_project'),
    path('project/<int:pk>/update-status/', views.update_project_status, name='update_project_status'),
    path('api/logged-in-user/', views.get_logged_in_user_api, name='get_logged_in_user_api'),
    path('api/update-activity/', views.update_activity, name='update_activity'),
    path('api/user-status/<int:user_id>/', views.get_user_status, name='get_user_status'),

    path('teammember_task/update/<int:task_id>/', views.update_task, name='update_task'),
    path('teammember_task/delete/<int:task_id>/', views.delete_task, name='delete_task'),

    
    path('teamlead/dashboard/', views.teamlead_dashboard, name='teamlead_dashboard'),
    path('teamlead_reports', views.teamlead_reports, name='teamlead_reports'),
    path('teamlead_project_assigning', views.teamlead_project_assigning, name='teamlead_project_assigning'),
    path('projects/edit/<int:pk>/', views.project_assign_edit, name='project_assign_edit'),
    path('projects/delete/<int:pk>/', views.project_assign_delete, name='project_assign_delete'),

    path('teammember/dashboard/', views.teammember_dashboard, name='teammember_dashboard'),
    path("teamlead_repository/", views.teamlead_repository, name="teamlead_repository"),
    path('teamlead_repository/delete/<int:pk>/', views.teamlead_repository_delete, name='teamlead_repository_delete'),
    path('teamlead_profile/', views.teamlead_profile, name='teamlead_profile'),
    path("teamlead_chat/", views.teamlead_chat, name="teamlead_chat"), 
    path('teamlead_notepad/', views.teamlead_notepad, name='teamlead_notepad'),
    path('teamlead_task/', views.teamlead_task, name='teamlead_task'),

    path('teamlead_task/update/<int:task_id>/', views.update_task_teamlead, name='update_task_teamlead'),
    path('teamlead_task/delete/<int:task_id>/', views.delete_task_teamlead, name='delete_task_teamlead'),

    path("teammember_repository/", views.teammember_repository, name="teammember_repository"),
    path("teammember_profile/", views.teammember_profile, name="teammember_profile"),
    path("teammember_task/", views.teammember_task, name="teammember_task"),
    path('teammember_repository/delete/<int:pk>/', views.teammember_repository_delete, name='teammember_repository_delete'),
    path('teammember_notepad/', views.teammember_notepad, name='teammember_notepad'),

    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("reset-password/", views.reset_password, name="reset_password"),

    path("teamlead/logout/", views.teamlead_logout, name="teamlead_logout"),
    path("teammember/logout/", views.teammember_logout, name="teammember_logout"),
    # path("teammember_chat/", views.teammember_chat, name="teammember_chat"),
    path('chat/', views.teammember_chat, name='teammember_chat'),
    path('chat/<int:user_id>/', views.chat_room, name='chat_room'),

    path('chat/group/<int:group_id>/', views.group_chat_view, name='group_chat_view'),
    
]
