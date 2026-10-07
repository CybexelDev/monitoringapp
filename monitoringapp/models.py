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


# class GroupMessage(models.Model):
#     group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
#     sender = models.ForeignKey('User', on_delete=models.CASCADE)
#     message = models.TextField()
#     timestamp = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"{self.sender.name}: {self.message[:30]}"


class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('User', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_for_everyone = models.BooleanField(default=False)
    hidden_for = models.ManyToManyField(User, blank=True, related_name="%(app_label)s_%(class)s_hidden_messages")

    def __str__(self):
        return f"{self.sender.name}: {self.message[:30]}"

class ChatReadState(models.Model):
    user = models.ForeignKey(
        "monitoringapp.User",
        on_delete=models.CASCADE,
        related_name="chat_read_states",
    )

    conversation = models.ForeignKey(
        "chat.Conversation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="read_states",
    )

    group = models.ForeignKey(
        "monitoringapp.Group",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="read_states",
    )

    last_read_id = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "conversation"],
                name="unique_user_conversation_read",
            ),
            models.UniqueConstraint(
                fields=["user", "group"],
                name="unique_user_group_read",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        conversation__isnull=False,
                        group__isnull=True,
                    )
                    | models.Q(
                        conversation__isnull=True,
                        group__isnull=False,
                    )
                ),
                name="chat_read_exactly_one_target",
            ),
        ]



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


from django.test import TestCase
from django.urls import reverse
from monitoringapp.models import User, Group, GroupMember
from chat.models import Conversation


class MemberChatTests(TestCase):
    def setUp(self):
        self.member = self.person('member', 'Team Member')
        self.lead = self.person('lead', 'Team Lead')
        self.outsider = self.person('outsider', 'Team Member')
        session = self.client.session
        session['user_id'] = self.member.pk
        session['position'] = 'team_member'
        session.save()

    def person(self, name, position):
        return User.objects.create(name=name, employee_id=name, email=f'{name}@example.com',
                                   username=name, password='unused', job_Position=position,
                                   designation='Developer')

    def test_reuses_existing_lead_conversation(self):
        room = Conversation.objects.create(user1=self.lead, user2=self.member)
        response = self.client.get(reverse('chat_room', args=[self.lead.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['room'].pk, room.pk)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_group_requires_another_person(self):
        response = self.client.post(reverse('teammember_chat'), {'action': 'create_group', 'group_name': 'Demo'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Group.objects.count(), 0)

    def test_create_group_deduplicates_members_and_sets_creator_admin(self):
        response = self.client.post(reverse('teammember_chat'),
                                    {'action': 'create_group', 'group_name': 'Demo', 'members': [self.lead.pk, self.lead.pk]})
        self.assertTrue(response.json()['ok'])
        group = Group.objects.get()
        self.assertEqual(group.memberships.count(), 2)
        self.assertEqual(group.memberships.get(user=self.member).role, 'admin')

    def test_nonmember_cannot_read_group(self):
        group = Group.objects.create(name='Private', created_by=self.lead)
        GroupMember.objects.create(group=group, user=self.lead)
        response = self.client.get(reverse('group_chat_view', args=[group.pk]))
        self.assertEqual(response.status_code, 404)

    def test_regular_member_cannot_manage_group(self):
        group = Group.objects.create(name='Demo', created_by=self.lead)
        GroupMember.objects.create(group=group, user=self.lead, role='admin')
        GroupMember.objects.create(group=group, user=self.member)
        response = self.client.post(reverse('group_chat_view', args=[group.pk]),
                                    {'action': 'add_member', 'user_id': self.outsider.pk})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(group.memberships.count(), 2)


#<--------------ACCOUNTS TEAM--------------->

# Replace the old AccountsIncome class with this entire block.
from pathlib import Path
from uuid import uuid4
from decimal import Decimal
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import MinValueValidator
from django.utils.deconstruct import deconstructible

@deconstructible
class IncomeReceiptStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=Path(settings.BASE_DIR) / "private_income_receipts")

def income_receipt_upload_path(instance, filename):
    return f"receipts/{uuid4().hex}{Path(filename).suffix.lower()}"

from django.db import models
from django.utils import timezone

class AccountsIncome(models.Model):
    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("card", "Card"),
        ("other", "Other"),
    ]

    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="bank_transfer",
    )
    receipt = models.FileField(upload_to=income_receipt_upload_path, storage=IncomeReceiptStorage(), blank=True)
    description = models.TextField()
    reference = models.CharField(max_length=150, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_income_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["date"], name="accounts_income_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="accounts_income_amount_gt_zero",
            ),
        ]

    def __str__(self):
        return f"{self.date} | {self.category} | {self.amount}"

class AccountsIncomeHistory(models.Model):
    income = models.ForeignKey(AccountsIncome, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="history")
    income_number = models.PositiveBigIntegerField()
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="income_history_actions")
    actor_name = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=10, choices=[("created", "Created"), ("updated", "Updated"), ("deleted", "Deleted")])
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at", "-pk"]



# monitoringapp/models.py: add these imports at the top only if missing.
from decimal import Decimal
from django.core.validators import MinValueValidator


# # Append this class BELOW AccountsIncome. Keep all existing models unchanged.
# # Your existing models.py already imports models, timezone and defines User.
# class AccountsExpense(models.Model):
#     PAYMENT_METHODS = [
#         ("cash", "Cash"),
#         ("bank_transfer", "Bank Transfer"),
#         ("upi", "UPI"),
#         ("card", "Card"),
#         ("other", "Other"),
#     ]

#     date = models.DateField(default=timezone.localdate)
#     category = models.CharField(max_length=100)
#     amount = models.DecimalField(
#         max_digits=14,
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal("0.01"))],
#     )
#     payment_method = models.CharField(
#         max_length=20,
#         choices=PAYMENT_METHODS,
#         default="bank_transfer",
#     )
#     paid_to = models.CharField(max_length=150, blank=True)
#     description = models.TextField()
#     reference = models.CharField(max_length=150, blank=True)
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="accounts_expense_entries",
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ["-date", "-id"]
#         indexes = [
#             models.Index(fields=["date"], name="accounts_expense_date_idx"),
#         ]
#         constraints = [
#             models.CheckConstraint(
#                 condition=models.Q(amount__gt=0),
#                 name="accounts_expense_amount_gt_zero",
#             ),
#         ]

#     def __str__(self):
#         return f"{self.date} | {self.category} | {self.amount}"

# Replace the old AccountsExpense class with this entire block.
from pathlib import Path
from uuid import uuid4
from decimal import Decimal
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import MinValueValidator
from django.utils.deconstruct import deconstructible

@deconstructible
class ExpenseReceiptStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=Path(settings.BASE_DIR) / "private_expense_receipts")

def expense_receipt_upload_path(instance, filename):
    return f"receipts/{uuid4().hex}{Path(filename).suffix.lower()}"

class AccountsExpense(models.Model):
    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("card", "Card"),
        ("other", "Other"),
    ]

    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="bank_transfer",
    )
    # NULL means fully paid for existing entries created before this upgrade.
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.00"))])
    receipt = models.FileField(upload_to=expense_receipt_upload_path,
        storage=ExpenseReceiptStorage(), blank=True)
    paid_to = models.CharField(max_length=150, blank=True)
    description = models.TextField()
    reference = models.CharField(max_length=150, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_expense_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["date"], name="accounts_expense_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=(models.Q(paid_amount__isnull=True) |
                (models.Q(paid_amount__gte=0) & models.Q(paid_amount__lte=models.F("amount")))),
                name="expense_paid_amount_valid"),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="accounts_expense_amount_gt_zero",
            ),
        ]

    @property
    def effective_paid_amount(self):
        return self.amount if self.paid_amount is None else self.paid_amount

    @property
    def balance_amount(self):
        return self.amount - self.effective_paid_amount

    @property
    def payment_status(self):
        if self.effective_paid_amount == self.amount:
            return "paid"
        return "pending" if self.effective_paid_amount == 0 else "partial"

    @property
    def payment_status_label(self):
        return {"paid": "Paid", "pending": "Pending", "partial": "Partially Paid"}[self.payment_status]

    def __str__(self):
        return f"{self.date} | {self.category} | {self.amount}"

class AccountsExpenseHistory(models.Model):
    expense = models.ForeignKey(AccountsExpense, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="history")
    expense_number = models.PositiveBigIntegerField()
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="expense_history_actions")
    actor_name = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=10, choices=[("created", "Created"), ("updated", "Updated"), ("deleted", "Deleted")])
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at", "-pk"]



# monitoringapp/models.py: add these imports at the top only if missing.
from decimal import Decimal
from django.core.validators import MinValueValidator
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible

@deconstructible
class SalesInvoiceStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=Path(settings.BASE_DIR) / "private_sales_invoices")

def sales_invoice_upload_path(instance, filename):
    return f"invoices/{uuid4().hex}{Path(filename).suffix.lower()}"

from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator
class AccountsSale(models.Model):
    date = models.DateField(default=timezone.localdate)
    customer_name = models.CharField(max_length=150)
    invoice_number = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True)
    invoice_file = models.FileField(upload_to=sales_invoice_upload_path, storage=SalesInvoiceStorage(), blank=True)
    description = models.TextField()
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    received_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_sales_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["date"], name="accounts_sale_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="accounts_sale_amount_gt_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(received_amount__gte=0),
                name="accounts_sale_received_gte_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(received_amount__lte=models.F("amount")),
                name="accounts_sale_received_lte_amt",
            ),
        ]

    @property
    def balance_amount(self):
        return self.amount - self.received_amount

    @property
    def is_overdue(self):
        return bool(self.due_date and self.due_date < timezone.localdate() and self.balance_amount > 0)

    @property
    def payment_status(self):
        if self.received_amount == self.amount:
            return "paid"
        if self.received_amount > 0:
            return "partial"
        return "unpaid"

    @property
    def payment_status_label(self):
        return {
            "paid": "Paid",
            "partial": "Partially Paid",
            "unpaid": "Unpaid",
        }[self.payment_status]

    def __str__(self):
        return f"{self.date} | {self.customer_name} | {self.amount}"


class AccountsSalePayment(models.Model):
    sale = models.ForeignKey(AccountsSale, on_delete=models.CASCADE, related_name="payments")
    date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))])
    payment_method = models.CharField(max_length=20, choices=[("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"), ("upi", "UPI"), ("card", "Card"), ("other", "Other")], default="bank_transfer")
    reference = models.CharField(max_length=150, blank=True)
    note = models.TextField(blank=True)
    request_token = models.UUIDField(default=uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="accounts_sale_payments")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-date", "-created_at", "-pk"]
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name="sale_payment_amount_positive")]


class AccountsNotification(models.Model):
    recipient = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="accounts_notifications",
    )
    actor = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_notification_actions",
    )
    kind = models.CharField(
        max_length=30,
        choices=[
            ("income", "Income"),
            ("expense", "Expense"),
            ("sale", "Sale"),
            ("payment", "Payment"),
            ("reminder", "Reminder"),
        ],
        db_index=True,
    )
    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)

    event_key = models.CharField(
        max_length=180,
        unique=True,
        null=True,
        blank=True,
    )
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=[
                    "recipient",
                    "is_archived",
                    "is_read",
                    "-created_at",
                ],
                name="acct_notif_inbox_idx",
            ),
        ]

    def __str__(self):
        return f"{self.recipient.name}: {self.title}"


class AccountsReminder(models.Model):
    owner = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="accounts_reminders",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)

    event_at = models.DateTimeField(db_index=True)
    remind_at = models.DateTimeField(db_index=True)

    is_completed = models.BooleanField(default=False)
    notified_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    notification = models.OneToOneField(
        "AccountsNotification",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_reminder",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_at", "id"]
        indexes = [
            models.Index(
                fields=["owner", "is_completed", "remind_at"],
                name="acct_reminder_due_idx",
            ),
        ]

    def __str__(self):
        return self.title