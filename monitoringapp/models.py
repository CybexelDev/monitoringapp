# from django.db import models
# from datetime import timedelta
# from django.utils import timezone
# from django.utils.timezone import now
# from django.conf import settings

# from datetime import datetime



# class Department(models.Model):
#     name = models.CharField(max_length=100, unique=True)

#     def __str__(self):
#         return self.name

# class Team(models.Model):
#     name = models.CharField(max_length=100, unique=True)
    

#     def __str__(self):
#        return self.name




# class User(models.Model):
#     STATUS_CHOICES = (
#         ('active', 'Active'),
#         ('inactive', 'Inactive'),
#     )

#     name = models.CharField(max_length=150)
#     employee_id = models.CharField(max_length=50, unique=True)
#     email = models.EmailField(unique=True)
#     phone = models.CharField(max_length=15, blank=True, null=True)

#     department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
#     team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

#     job_Position = models.CharField(max_length=100)
#     designation = models.CharField(max_length=100)
#     work_location = models.CharField(max_length=150, blank=True, null=True)
#     joining_date = models.DateField(auto_now_add=True)

#     username = models.CharField(max_length=100, unique=True)
#     password = models.CharField(max_length=128)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
#     profile_image = models.ImageField(upload_to='user_images/', blank=True, null=True)

#     # ✅ Add these fields
#     last_login_time = models.DateTimeField(null=True, blank=True)
#     last_logout_time = models.DateTimeField(null=True, blank=True)
#     last_activity = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.name} ({self.designation})"



    

# class Announcement(models.Model):
#     title = models.CharField(max_length=200)  
#     message = models.TextField()  
#     created_at = models.DateTimeField(auto_now_add=True)  
#     updated_at = models.DateTimeField(auto_now=True)  
#     created_by = models.ForeignKey(User, on_delete=models.CASCADE)  
#     is_active = models.BooleanField(default=True)  

#     class Meta:
#         ordering = ['-created_at']  

#     def __str__(self):
#         return self.title

#     def is_valid(self):
#         return self.created_at >= timezone.now() - timedelta(hours=12)

# class AnnouncementRecipient(models.Model):
#     announcement = models.ForeignKey(
#         Announcement,
#         on_delete=models.CASCADE,
#         related_name="recipients"
#     )
#     recipient = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="announcement_recipients"
#     )
#     read_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         unique_together = ("announcement", "recipient")
#         ordering = ["-announcement__created_at"]

#     def __str__(self):
#         return f"{self.recipient.name} - {self.announcement.title}"

# class MorningReport(models.Model):
#     STATUS_CHOICES = [
#         ("Pending", "Pending"),
#         ("In Progress", "In Progress"),
#         ("Completed", "Completed"),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     department = models.CharField(max_length=150)
#     team = models.CharField(max_length=150)
#     report_text = models.TextField()
#     status = models.CharField(
#         max_length=50,
#         choices=STATUS_CHOICES,
#         default="Pending"
#     )
#     created_at = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"Morning Report - {self.user.username} ({self.created_at.date()}) | {self.status}"


# class EveningReport(models.Model):
#     STATUS_CHOICES = [
#         ("Pending", "Pending"),
#         ("In Progress", "In Progress"),
#         ("Completed", "Completed"),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     department = models.CharField(max_length=150)
#     team = models.CharField(max_length=150)
#     report_text = models.TextField()
#     status = models.CharField(
#         max_length=50,
#         choices=STATUS_CHOICES,
#         default="Pending"
#     )
#     created_at = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"Evening Report - {self.user.username} ({self.created_at.date()}) | {self.status}"
    



# # class ReportTimeSetting(models.Model):
# #     MORNING = 'morning'
# #     EVENING = 'evening'
# #     REPORT_TYPES = [
# #         (MORNING, 'Morning'),
# #         (EVENING, 'Evening'),
# #     ]

# #     report_type = models.CharField(max_length=20, choices=REPORT_TYPES, unique=True)
# #     start_time = models.TimeField()
# #     end_time = models.TimeField()

# #     def __str__(self):
# #         return f"{self.get_report_type_display()} Report ({self.start_time} - {self.end_time})"



# class ReportTimeSetting(models.Model):

#     MORNING = "morning"
#     EVENING = "evening"

#     REPORT_TYPES = [
#         (MORNING, "Morning"),
#         (EVENING, "Evening"),
#     ]

#     DAY_CHOICES = [
#         (0, "Monday"),
#         (1, "Tuesday"),
#         (2, "Wednesday"),
#         (3, "Thursday"),
#         (4, "Friday"),
#         (5, "Saturday"),
#         (6, "Sunday"),
#     ]

#     team_lead = models.ForeignKey(
#         "User",
#         on_delete=models.CASCADE,
#         related_name="report_time_settings",
#         null=True,
#         blank=True,
#         limit_choices_to={
#             "job_Position__iexact": "Team Lead"
#         },
#     )

#     day_of_week = models.PositiveSmallIntegerField(
#         choices=DAY_CHOICES,
#         null=True,
#         blank=True,
#     )

#     report_type = models.CharField(
#         max_length=20,
#         choices=REPORT_TYPES
#     )

#     start_time = models.TimeField()
#     end_time = models.TimeField()

#     is_active = models.BooleanField(default=True)

#     class Meta:
#         unique_together = (
#             "team_lead",
#             "day_of_week",
#             "report_type",
#         )
#         ordering = [
#             "day_of_week",
#             "report_type",
#         ]

#     def __str__(self):
#         return (
#             f"{self.team_lead} - "
#             f"{self.get_day_of_week_display()} - "
#             f"{self.get_report_type_display()} "
#             f"({self.start_time} - {self.end_time})"
#         )



# class ProjectAssign(models.Model):
#     WORK_TYPE_CHOICES = (
#         ("Client", "Client"),
#         ("Company", "Company"),
#         ("Other", "Other"),
#     )
#     PRIORITY_CHOICES = (
#         ("Low", "Low"),
#         ("Medium", "Medium"),
#         ("High", "High"),
#         ("Urgent", "Urgent"),
#     )
#     STATUS_CHOICES = (
#         ("Not Started", "Not Started"),
#         ("In Progress", "In Progress"),
#         ("On Hold", "On Hold"),
#         ("Completed", "Completed"),
#     )

#     team = models.ForeignKey("Team", on_delete=models.CASCADE)
#     department = models.ForeignKey("Department", on_delete=models.CASCADE)
#     assign_to = models.ForeignKey("User", related_name="assigned_works", on_delete=models.CASCADE)
#     assigned_by = models.ForeignKey("User", related_name="given_works", on_delete=models.CASCADE)

#     work_name = models.CharField(max_length=255)
#     work_type = models.CharField(max_length=50, choices=WORK_TYPE_CHOICES)
#     category = models.CharField(max_length=255, blank=True, null=True)
#     description = models.TextField(blank=True, null=True)
#     deadline = models.DateField(null=True, blank=True)
#     additional_notes = models.TextField(blank=True, null=True)

#     upload_file = models.FileField(upload_to="uploads/files/", blank=True, null=True)
#     upload_image = models.ImageField(upload_to="uploads/images/", blank=True, null=True)

#     color_preference = models.CharField(max_length=100, blank=True, null=True)
#     content_example = models.TextField(blank=True, null=True)

#     priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="Medium")
#     assigned_date = models.DateField(default=now)

#     # NEW FIELD
#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="Not Started"
#     )

#     def __str__(self):
#         return f"{self.work_name} → {self.assign_to.name}"

    




# class Notepad(models.Model):
#     user = models.ForeignKey("User", on_delete=models.CASCADE)  # multiple notes per user
#     title = models.CharField(max_length=255, default="Untitled")
#     content = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.title} ({self.user.name})"


# class Knowledge(models.Model):
#     department = models.ForeignKey("Department", on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)   # ✅ use your custom User
#     title = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)
#     file = models.FileField(upload_to="knowledge_files/", blank=True, null=True, max_length=500)
#     link = models.URLField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.title
    

# class Task(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('in_progress', 'In Progress'),
#         ('completed', 'Completed'),
#     ]
#     title = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)
#     assigned_to = models.ForeignKey(
#         "User", 
#         on_delete=models.CASCADE, 
#         related_name="tasks_assigned"
#     )
#     created_by = models.ForeignKey(
#         "User", 
#         on_delete=models.CASCADE, 
#         related_name="tasks_created",
#         null=True,  # temporarily allow null for existing rows
#         blank=True
#     )
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     progress = models.IntegerField(default=0)  # percentage
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.title
    


# class ProjectFile(models.Model):
#     project = models.ForeignKey(ProjectAssign, on_delete=models.CASCADE, related_name="files")
#     file = models.FileField(upload_to="project_files/")

# class ProjectImage(models.Model):
#     project = models.ForeignKey(ProjectAssign, on_delete=models.CASCADE, related_name="images")
#     image = models.ImageField(upload_to="project_images/")

# # models.py
# class ExtraContact(models.Model):
#     name = models.CharField(max_length=150)
#     phone = models.CharField(max_length=15, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.name} ({self.phone})"


# class ChatRoom(models.Model):
#     """Private chat between two users"""
#     user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user1')
#     user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user2')
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user1', 'user2')

#     def __str__(self):
#         return f"Chat between {self.user1.name} and {self.user2.name}"

#     def get_room_name(self):
#         return f"room_{self.id}"


# class Message(models.Model):
#     room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
#     sender = models.ForeignKey(User, on_delete=models.CASCADE)
#     content = models.TextField()
#     timestamp = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"{self.sender.name}: {self.content[:20]}"


# class Group(models.Model):
#     name = models.CharField(max_length=150)
#     description = models.TextField(blank=True, null=True)
#     created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='created_groups')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name


# class GroupMember(models.Model):
#     ROLE_CHOICES = (
#         ('admin', 'Admin'),
#         ('member', 'Member'),
#     )

#     group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
#     user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='group_memberships')
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
#     added_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('group', 'user')

#     def __str__(self):
#         return f"{self.user.name} in {self.group.name}"


# class GroupMessage(models.Model):
#     group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
#     sender = models.ForeignKey('User', on_delete=models.CASCADE)
#     message = models.TextField()
#     timestamp = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"{self.sender.name}: {self.message[:30]}"


# class GoogleMeeting(models.Model):

#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="created_google_meetings"
#     )

#     date = models.DateField()
#     time = models.TimeField()

#     meeting_link = models.URLField()

#     purpose = models.CharField(
#         max_length=255
#     )

#     participants = models.ManyToManyField(
#         User,
#         related_name="google_meetings",
#         blank=True
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     @property
#     def scheduled_datetime(self):
#         """
#         Meeting date + time in Django's current timezone.
#         """
#         naive_datetime = datetime.combine(
#             self.date,
#             self.time
#         )

#         return timezone.make_aware(
#             naive_datetime,
#             timezone.get_current_timezone()
#         )

#     @property
#     def meeting_end_datetime(self):
#         """
#         Meeting automatically ends 1 hour
#         after the scheduled start time.
#         """
#         return self.scheduled_datetime + timedelta(hours=1)

#     @property
#     def can_join(self):
#         """
#         Join button is active from the scheduled
#         start time until 1 hour after start.
#         """
#         current_time = timezone.now()

#         return (
#             current_time >= self.scheduled_datetime
#             and current_time < self.meeting_end_datetime
#         )

#     @property
#     def meeting_status(self):
#         """
#         Meeting status based on scheduled date/time.

#         Before start  -> Upcoming
#         During 1 hour -> Live Now
#         After 1 hour  -> Meeting Ended
#         """
#         current_time = timezone.now()

#         if current_time < self.scheduled_datetime:
#             return "upcoming"

#         if current_time < self.meeting_end_datetime:
#             return "live"

#         return "ended"






from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.conf import settings

from datetime import datetime



class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    

    def __str__(self):
       return self.name




class User(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    name = models.CharField(max_length=150)
    employee_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    job_Position = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    work_location = models.CharField(max_length=150, blank=True, null=True)
    joining_date = models.DateField(auto_now_add=True)

    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    profile_image = models.ImageField(upload_to='user_images/', blank=True, null=True)

    # ✅ Add these fields
    last_login_time = models.DateTimeField(null=True, blank=True)
    last_logout_time = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.designation})"



    

class Announcement(models.Model):
    title = models.CharField(max_length=200)  
    message = models.TextField()  
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  
    is_active = models.BooleanField(default=True)  

    class Meta:
        ordering = ['-created_at']  

    def __str__(self):
        return self.title

    def is_valid(self):
        return self.created_at >= timezone.now() - timedelta(hours=12)

class AnnouncementRecipient(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="recipients"
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="announcement_recipients"
    )
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("announcement", "recipient")
        ordering = ["-announcement__created_at"]

    def __str__(self):
        return f"{self.recipient.name} - {self.announcement.title}"

class MorningReport(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=150)
    team = models.CharField(max_length=150)
    report_text = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Morning Report - {self.user.username} ({self.created_at.date()}) | {self.status}"


class EveningReport(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=150)
    team = models.CharField(max_length=150)
    report_text = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Evening Report - {self.user.username} ({self.created_at.date()}) | {self.status}"
    



# class ReportTimeSetting(models.Model):
#     MORNING = 'morning'
#     EVENING = 'evening'
#     REPORT_TYPES = [
#         (MORNING, 'Morning'),
#         (EVENING, 'Evening'),
#     ]

#     report_type = models.CharField(max_length=20, choices=REPORT_TYPES, unique=True)
#     start_time = models.TimeField()
#     end_time = models.TimeField()

#     def __str__(self):
#         return f"{self.get_report_type_display()} Report ({self.start_time} - {self.end_time})"



class ReportTimeSetting(models.Model):

    MORNING = "morning"
    EVENING = "evening"

    REPORT_TYPES = [
        (MORNING, "Morning"),
        (EVENING, "Evening"),
    ]

    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    team_lead = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="report_time_settings",
        null=True,
        blank=True,
        limit_choices_to={
            "job_Position__iexact": "Team Lead"
        },
    )

    day_of_week = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        null=True,
        blank=True,
    )

    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (
            "team_lead",
            "day_of_week",
            "report_type",
        )
        ordering = [
            "day_of_week",
            "report_type",
        ]

    def __str__(self):
        return (
            f"{self.team_lead} - "
            f"{self.get_day_of_week_display()} - "
            f"{self.get_report_type_display()} "
            f"({self.start_time} - {self.end_time})"
        )

class ReportDateSchedule(models.Model):
    """Morning or evening report time for one calendar date."""

    team_lead = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="date_report_schedules",
    )
    date = models.DateField()
    report_type = models.CharField(
        max_length=20,
        choices=ReportTimeSetting.REPORT_TYPES,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_lead", "date", "report_type"],
                name="unique_team_lead_date_report_type",
            )
        ]
        ordering = ["date", "report_type"]

    def __str__(self):
        return f"{self.team_lead} - {self.date} - {self.report_type}"

class ReportDefaultSchedule(models.Model):
    DAY_KIND_CHOICES = [
        ("regular", "Regular days"),
        ("saturday", "Saturday"),
    ]

    team_lead = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="default_report_schedules",
    )
    effective_from = models.DateField()
    day_kind = models.CharField(
        max_length=10,
        choices=DAY_KIND_CHOICES,
        default="regular",
    )
    report_type = models.CharField(
        max_length=20,
        choices=ReportTimeSetting.REPORT_TYPES,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "team_lead",
                    "effective_from",
                    "day_kind",
                    "report_type",
                ],
                name="unique_default_report_schedule",
            )
        ]
        ordering = ["effective_from", "day_kind", "report_type"]

    def __str__(self):
        return (
            f"{self.team_lead} - {self.day_kind} - "
            f"{self.report_type} from {self.effective_from}"
        )

class ProjectAssign(models.Model):
    WORK_TYPE_CHOICES = (
        ("Client", "Client"),
        ("Company", "Company"),
        ("Other", "Other"),
    )
    PRIORITY_CHOICES = (
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
        ("Urgent", "Urgent"),
    )
    STATUS_CHOICES = (
        ("Not Started", "Not Started"),
        ("In Progress", "In Progress"),
        ("On Hold", "On Hold"),
        ("Completed", "Completed"),
    )

    team = models.ForeignKey("Team", on_delete=models.CASCADE)
    department = models.ForeignKey("Department", on_delete=models.CASCADE)
    assign_to = models.ForeignKey("User", related_name="assigned_works", on_delete=models.CASCADE)
    assigned_by = models.ForeignKey("User", related_name="given_works", on_delete=models.CASCADE)

    work_name = models.CharField(max_length=255)
    work_type = models.CharField(max_length=50, choices=WORK_TYPE_CHOICES)
    category = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField(null=True, blank=True)
    additional_notes = models.TextField(blank=True, null=True)

    upload_file = models.FileField(upload_to="uploads/files/", blank=True, null=True)
    upload_image = models.ImageField(upload_to="uploads/images/", blank=True, null=True)

    color_preference = models.CharField(max_length=100, blank=True, null=True)
    content_example = models.TextField(blank=True, null=True)

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="Medium")
    assigned_date = models.DateField(default=now)

    # NEW FIELD
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Not Started"
    )

    def __str__(self):
        return f"{self.work_name} → {self.assign_to.name}"

    




class Notepad(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)  # multiple notes per user
    title = models.CharField(max_length=255, default="Untitled")
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.user.name})"


class Knowledge(models.Model):
    department = models.ForeignKey("Department", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)   # ✅ use your custom User
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="knowledge_files/", blank=True, null=True, max_length=500)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        "User", 
        on_delete=models.CASCADE, 
        related_name="tasks_assigned"
    )
    created_by = models.ForeignKey(
        "User", 
        on_delete=models.CASCADE, 
        related_name="tasks_created",
        null=True,  # temporarily allow null for existing rows
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)  # percentage
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    


class ProjectFile(models.Model):
    project = models.ForeignKey(ProjectAssign, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="project_files/")

class ProjectImage(models.Model):
    project = models.ForeignKey(ProjectAssign, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="project_images/")

# models.py
class ExtraContact(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"


class ChatRoom(models.Model):
    """Private chat between two users"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Chat between {self.user1.name} and {self.user2.name}"

    def get_room_name(self):
        return f"room_{self.id}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender.name}: {self.content[:20]}"


class Group(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.name} in {self.group.name}"


class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('User', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender.name}: {self.message[:30]}"


class GoogleMeeting(models.Model):

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_google_meetings"
    )

    date = models.DateField()
    time = models.TimeField()

    meeting_link = models.URLField()

    purpose = models.CharField(
        max_length=255
    )

    participants = models.ManyToManyField(
        User,
        related_name="google_meetings",
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def scheduled_datetime(self):
        """
        Meeting date + time in Django's current timezone.
        """
        naive_datetime = datetime.combine(
            self.date,
            self.time
        )

        return timezone.make_aware(
            naive_datetime,
            timezone.get_current_timezone()
        )

    @property
    def meeting_end_datetime(self):
        """
        Meeting automatically ends 1 hour
        after the scheduled start time.
        """
        return self.scheduled_datetime + timedelta(hours=1)

    @property
    def can_join(self):
        """
        Join button is active from the scheduled
        start time until 1 hour after start.
        """
        current_time = timezone.now()

        return (
            current_time >= self.scheduled_datetime
            and current_time < self.meeting_end_datetime
        )

    @property
    def meeting_status(self):
        """
        Meeting status based on scheduled date/time.

        Before start  -> Upcoming
        During 1 hour -> Live Now
        After 1 hour  -> Meeting Ended
        """
        current_time = timezone.now()

        if current_time < self.scheduled_datetime:
            return "upcoming"

        if current_time < self.meeting_end_datetime:
            return "live"

        return "ended"

class TeamReportLeave(models.Model):
    """One date of report leave for a team lead and their team."""

    team_lead = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_report_leaves",
    )
    date = models.DateField()
    morning_leave = models.BooleanField(default=False)
    evening_leave = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_lead", "date"],
                name="unique_team_report_leave_date",
            )
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.team_lead.name}: {self.date} leave"


class TeamLeadNotification(models.Model):
    recipient = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="teamlead_notifications"
    )
    kind = models.CharField(max_length=40, db_index=True)
    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)
    event_key = models.CharField(
        max_length=180,
        unique=True,
        null=True,
        blank=True
    )
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.name}: {self.title}"


class TeamLeadReminder(models.Model):
    owner = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="teamlead_reminders",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)

    # Meeting/event നടക്കേണ്ട തീയതിയും സമയവും
    event_at = models.DateTimeField(db_index=True)

    # Notification വരേണ്ട തീയതിയും സമയവും
    remind_at = models.DateTimeField(db_index=True)

    is_completed = models.BooleanField(default=False)
    notified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notification = models.OneToOneField(
        "TeamLeadNotification",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reminder",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_at", "id"]

    def __str__(self):
        return self.title