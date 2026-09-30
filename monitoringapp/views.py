from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User  
from .models import *
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from datetime import date
import openpyxl
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.hashers import check_password, make_password
import random
from django.core.mail import send_mail
from datetime import time, timedelta
from django.utils.dateparse import parse_datetime,parse_time
from django.utils.timezone import localtime, make_aware, is_naive
from django.views.decorators.cache import never_cache
from django.utils.cache import add_never_cache_headers
from .models import AnnouncementRecipient
from django.utils.dateparse import parse_time
from django.http import JsonResponse
from django.db import transaction
from django.db.models.functions import Lower, Trim
from openpyxl.utils import get_column_letter
from django.utils.dateparse import parse_time
from django.db import IntegrityError
from django.db.models import Q
from chat.models import Conversation
import calendar


@never_cache
def index(request):
    return render(request,'index.html')


@never_cache
def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not a superuser")

    return render(request, 'admin_login.html')

def admin_logout(request):
    logout(request)
    request.session.flush()
    return redirect("index")


@never_cache
def admin_dashboard(request):
    # Check superuser OR management session
    if (request.user.is_authenticated and request.user.is_superuser) or \
       (request.session.get("position", "").strip().lower().replace(" ", "_") == "management"):

        if request.method == "POST":
            if "add_department" in request.POST:
                name = request.POST.get("department_name")
                if name:
                    Department.objects.create(name=name)
                    return redirect('admin_dashboard')

            elif "add_team" in request.POST:
                name = request.POST.get("team_name")
                if name:
                    Team.objects.create(name=name)
                    return redirect('admin_dashboard')

        departments = Department.objects.all()
        teams = Team.objects.all()
        return render(request, "admin_dashboard.html", {"departments": departments, "teams": teams})

    # Not allowed → redirect
    return redirect("admin_login")


def delete_department(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    dept.delete()
    return redirect('admin_dashboard')

def delete_team(request, pk):
    team = get_object_or_404(Team, pk=pk)
    team.delete()
    return redirect('admin_dashboard')

@csrf_exempt
def admin_usermanagement(request):
    users = User.objects.all()

    # Hide currently logged-in management/admin user
    current_user_id = request.session.get("user_id")

    if current_user_id:
        users = users.exclude(id=current_user_id)
    departments = Department.objects.all()
    teams = Team.objects.all()
    job_positions = (
        User.objects.exclude(job_Position__isnull=True)
        .exclude(job_Position__exact="")
        .values_list('job_Position', flat=True)
        .distinct()
        .order_by('job_Position')
    )

    if request.method == "POST":
        user_id = request.POST.get("id")  # for edit (None for new user)
        name = request.POST.get("name")
        employee_id = request.POST.get("employee_id")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        department_id = request.POST.get("department")
        team_id = request.POST.get("team")
        job_Position = request.POST.get("job_Position")
        designation = request.POST.get("designation")
        work_location = request.POST.get("work_location")
        username = request.POST.get("username")
        password = request.POST.get("password")
        status = request.POST.get("status")
        image = request.FILES.get("profile_image")
        joining_date = request.POST.get("joining_date")

        # Foreign key fetch
        department = Department.objects.get(id=department_id) if department_id else None
        team = Team.objects.get(id=team_id) if team_id else None

        # Helper for uniqueness validation
        def check_unique(field_name, value):
            qs = User.objects.filter(**{field_name: value})
            if user_id:
                qs = qs.exclude(id=user_id)
            return qs.exists()

        # ========== EDIT EXISTING USER ==========
        if user_id:
            user = get_object_or_404(User, id=user_id)

            # Uniqueness checks
            if check_unique("employee_id", employee_id):
                messages.error(request, "⚠️ Employee ID already exists for another user.")
                return redirect("admin_usermanagement")
            if check_unique("username", username):
                messages.error(request, "⚠️ Username already exists for another user.")
                return redirect("admin_usermanagement")
            if check_unique("email", email):
                messages.error(request, "⚠️ Email already exists for another user.")
                return redirect("admin_usermanagement")

            # Update details
            user.name = name
            user.employee_id = employee_id
            user.email = email
            user.phone = phone
            user.department = department
            user.team = team
            user.job_Position = job_Position
            user.designation = designation
            user.work_location = work_location
            user.username = username
            user.status = status

            if password:
                user.password = make_password(password)
            if image:
                user.profile_image = image
            if joining_date:
                try:
                    user.joining_date = datetime.strptime(joining_date, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(request, "❌ Invalid date format! Use YYYY-MM-DD.")
                    return redirect("admin_usermanagement")

            try:
                user.save()
                messages.success(request, "✅ User updated successfully!")
            except IntegrityError as e:
                messages.error(request, f"⚠️ Cannot update user. Unique field conflict ({str(e)})")
                return redirect("admin_usermanagement")

        # ========== CREATE NEW USER ==========
        else:
            if check_unique("employee_id", employee_id):
                messages.error(request, "⚠️ Employee ID already exists. Please choose another one.")
                return redirect("admin_usermanagement")
            if check_unique("username", username):
                messages.error(request, "⚠️ Username already exists. Please choose another one.")
                return redirect("admin_usermanagement")
            if check_unique("email", email):
                messages.error(request, "⚠️ Email already exists. Please choose another one.")
                return redirect("admin_usermanagement")

            try:
                User.objects.create(
                    name=name,
                    employee_id=employee_id,
                    email=email,
                    phone=phone,
                    department=department,
                    team=team,
                    job_Position=job_Position,
                    designation=designation,
                    work_location=work_location,
                    username=username,
                    password=make_password(password) if password else "",
                    status=status,
                    profile_image=image,
                    joining_date=datetime.strptime(joining_date, "%Y-%m-%d").date() if joining_date else None,
                )
                messages.success(request, "✅ User created successfully!")
            except IntegrityError as e:
                messages.error(request, f"⚠️ Cannot create user. Unique field conflict ({str(e)})")
                return redirect("admin_usermanagement")

        return redirect("admin_usermanagement")

    # =======================================================
    # ===============   GET REQUEST (FILTERS)   =============
    # =======================================================

    search = request.GET.get("search", "").strip()
    department_filter = request.GET.get("department", "")
    team_filter = request.GET.get("team", "")
    position_filter = request.GET.get("position", "")

    if search:
        users = users.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(employee_id__icontains=search)
        )

    if department_filter:
        users = users.filter(department__name=department_filter)

    if team_filter:
        users = users.filter(team__name=team_filter)

    if position_filter:
        users = users.filter(job_Position=position_filter)

    context = {
        "users": users,
        "departments": departments,
        "teams": teams,
        "job_positions": job_positions,
    }
    return render(request, "admin_usermanagement.html", context)


def edit_user(request):
    if request.method == "POST":
        user_id = request.POST.get("id")
        user = get_object_or_404(User, id=user_id)

        # Get form values
        employee_id = request.POST.get("edit_emp_id")
        username = request.POST.get("edit_username")
        email = request.POST.get("edit_email")
        name = request.POST.get("edit_name")
        phone = request.POST.get("edit_phone")
        job_position = request.POST.get("edit_job_position")
        designation = request.POST.get("edit_designation")
        work_location = request.POST.get("edit_work_location")
        status = request.POST.get("edit_status")
        password = request.POST.get("edit_password")
        joining_date = request.POST.get("edit_joining_date")
        dept_id = request.POST.get("edit_department")
        team_id = request.POST.get("edit_team")

        # ========== Check uniqueness before saving ==========
        if User.objects.filter(employee_id=employee_id).exclude(id=user.id).exists():
            messages.error(request, "⚠️ Employee ID already exists for another user.")
            return redirect("admin_usermanagement")

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "⚠️ Username already exists for another user.")
            return redirect("admin_usermanagement")

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "⚠️ Email already exists for another user.")
            return redirect("admin_usermanagement")

        # ========== Update fields ==========
        user.employee_id = employee_id
        user.username = username
        user.email = email
        user.name = name
        user.phone = phone
        user.job_Position = job_position
        user.designation = designation
        user.work_location = work_location
        user.status = status

        if password:
            user.password = make_password(password)

        # Department & Team
        user.department = Department.objects.get(id=dept_id) if dept_id else None
        user.team = Team.objects.get(id=team_id) if team_id else None

        # Joining Date
        if joining_date:
            try:
                user.joining_date = datetime.strptime(joining_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "❌ Invalid date format! Use YYYY-MM-DD.")
                return redirect("admin_usermanagement")
        else:
            user.joining_date = None

        # Profile Image
        if request.FILES.get("edit_profile_upload"):
            user.profile_image = request.FILES["edit_profile_upload"]

        # ========== Save with try-except ==========
        try:
            user.save()
            messages.success(request, "✅ User updated successfully!")
        except IntegrityError as e:
            messages.error(request, f"⚠️ Cannot update user due to unique constraint. ({str(e)})")
            return redirect("admin_usermanagement")

        return redirect("admin_usermanagement")

    return redirect("admin_usermanagement")
@csrf_exempt
def check_username_exists(request):
    username = request.GET.get("username", "").strip()
    user_id = request.GET.get("user_id")  # optional — to exclude current user during edit

    if not username:
        return JsonResponse({"exists": False})

    # Filter case-insensitive
    qs = User.objects.filter(username__iexact=username)
    if user_id:
        qs = qs.exclude(id=user_id)

    return JsonResponse({"exists": qs.exists()})


def delete_user(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('admin_usermanagement') 


@never_cache
def admin_reports(request):
    show_all = request.GET.get('all')
    export = request.GET.get('export')
    filter_date = request.GET.get('date')

    if filter_date in (None, "", "None"):
        filter_date = None

    # Determine report queryset
    if show_all:
        morning_reports = MorningReport.objects.select_related('user').order_by('-created_at')
        evening_reports = EveningReport.objects.select_related('user').order_by('-created_at')
    else:
        today = timezone.now().date()
        morning_reports = MorningReport.objects.filter(created_at__date=today).select_related('user').order_by('-created_at')
        evening_reports = EveningReport.objects.filter(created_at__date=today).select_related('user').order_by('-created_at')

    # Apply date filter if provided
    if filter_date:
        morning_reports = morning_reports.filter(created_at__date=filter_date)
        evening_reports = evening_reports.filter(created_at__date=filter_date)

    # Export filtered reports to Excel
    if export:
        wb = Workbook()
        ws = wb.active
        ws.title = "Team Reports"

        headers = ["Report Type", "Date", "Time", "Name", "Team", "Department", "Report", "Status"]
        ws.append(headers)

        def add_report_to_sheet(report_list, report_type):
            for report in report_list:
                local_dt = timezone.localtime(report.created_at)
                ws.append([
                    report_type,
                    local_dt.strftime("%Y-%m-%d"),
                    local_dt.strftime("%I:%M %p"),
                    getattr(report.user, "name", report.user.username),
                    report.team,
                    report.department,
                    report.report_text,
                    getattr(report, "status", ""),
                ])

        add_report_to_sheet(morning_reports, "Morning")
        add_report_to_sheet(evening_reports, "Evening")

        for row in ws.iter_rows(min_row=2, min_col=7, max_col=7):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

        column_widths = [15, 15, 12, 20, 15, 20, 50, 15]
        for i, width in enumerate(column_widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = width

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response['Content-Disposition'] = 'attachment; filename="team_reports.xlsx"'
        wb.save(response)
        return response

    context = {
        'morning_reports': morning_reports,
        'evening_reports': evening_reports,
        'show_all': show_all,
        'filter_date': filter_date,
    }
    return render(request, 'admin_reports.html', context)

def admin_chat(request):
    # ============================
    # 🔹 LOGIN CHECK
    # ============================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    current_user = get_object_or_404(User, id=user_id)

    # ============================
    # 🔹 USERS & GROUPS
    # ============================
    users = list(User.objects.exclude(id=current_user.id))
    users.sort(key=lambda u: u.name.lower())

    extra_contacts = ExtraContact.objects.all()
    groups = Group.objects.filter(memberships__user=current_user).distinct()

    # ============================
    # 🔹 HANDLE GROUP CREATION
    # ============================
    if request.method == "POST" and request.POST.get("action") == "create_group":
        group_name = request.POST.get("group_name")
        member_ids = request.POST.getlist("members")  # list of user ids

        if group_name:
            with transaction.atomic():
                # Create group
                group = Group.objects.create(name=group_name, created_by=current_user)

                # Add creator
                GroupMember.objects.create(group=group, user=current_user)

                # Add selected members
                for uid in member_ids:
                    user = User.objects.get(id=uid)
                    GroupMember.objects.get_or_create(group=group, user=user)

            messages.success(request, f"Group '{group_name}' created successfully!")
            return redirect("admin_chat")
        else:
            messages.error(request, "Please provide a group name.")

    # ============================
    # 🔹 CONTEXT FOR TEMPLATE
    # ============================
    context = {
        "current_user": current_user,
        "users": users,
        "extra_contacts": extra_contacts,
        "groups": groups,
        "role": "admin_chat",
    }

    return render(request, "admin_chat.html", context)

def add_contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")

        # prevent duplicate phone numbers
        if ExtraContact.objects.filter(phone=phone).exists():
            messages.error(request, "Contact with this phone already exists!")
        else:
            ExtraContact.objects.create(name=name, phone=phone)
            messages.success(request, "Contact added successfully!")

        return redirect("admin_chat")  # back to chat page

    return redirect("admin_chat")

@never_cache
def admin_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("index")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        action = request.POST.get("action")

        # AJAX Profile Image Update
        if action == "edit_profile" and request.FILES.get("profile_image"):
            user.profile_image = request.FILES["profile_image"]
            user.save()
            return JsonResponse({
                "success": True,
                "image_url": user.profile_image.url
            })

        # Normal form update for other details
        elif action == "edit_profile":
            user.name = request.POST.get("name")
            user.email = request.POST.get("email")
            user.phone = request.POST.get("phone")
            user.work_location = request.POST.get("work_location")
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("admin_profile")

    # Render page
    response = render(request, "admin_profile.html", {"user": user})
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

@never_cache
def login_view(request):
    # Already logged in → redirect
    if request.session.get("user_id") and request.session.get("position"):
        position = request.session["position"]
        if position == "team_lead":
            return redirect("teamlead_dashboard")
        elif position == "management":
            return redirect("admin_dashboard")
        else:
            return redirect("teammember_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        # Fetch user from DB
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "Invalid username or password")
            return render(request, "user_login.html")

        # Check hashed password
        if not check_password(password, user.password):
            messages.error(request, "Invalid username or password")
            return render(request, "user_login.html")

        # ✅ Update user status and last login time (normalize status explicitly)
        now = timezone.now()
        user.status = "active"                # canonical value (no spaces, lowercase)
        user.last_login_time = now
        user.last_activity = now

        # if model happens to have is_active (boolean), keep it in sync
        if hasattr(user, "is_active"):
            try:
                setattr(user, "is_active", True)
            except Exception:
                pass

        user.save()

        # Normalize DB position
        db_position = user.job_Position.strip().lower().replace(" ", "_")

        # Save session
        request.session["user_id"] = user.id
        request.session["position"] = db_position
        request.session["login_time"] = str(now)

        # Redirect based on DB position only
        if db_position == "team_lead":
            return redirect("teamlead_dashboard")
        elif db_position == "management":
            return redirect("admin_dashboard")
        else:
            return redirect("teammember_dashboard")

    return render(request, "user_login.html")

# def get_logged_in_user_api(request):
#     if request.session.get("user_id"):
#         try:
#             user = User.objects.get(id=request.session["user_id"])
#             return JsonResponse({"name": user.name, "job_position": user.job_Position})
#         except User.DoesNotExist:
#             pass
#     return JsonResponse({"name": None})



def get_logged_in_user_api(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"name": None, "profile_image_url": None})
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return JsonResponse({"name": None, "profile_image_url": None})
    return JsonResponse({
        "name": user.name,
        "username": user.username,
        "job_position": user.job_Position,
        "profile_image_url": user.profile_image.url if user.profile_image else None,
    })


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
            otp = random.randint(100000, 999999)
            request.session['reset_email'] = email
            request.session['reset_otp'] = str(otp)

            # Send OTP via email
            send_mail(
                "Password Reset OTP",
                f"Your OTP for password reset is {otp}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, "OTP sent to your email")
            return redirect("verify_otp")

        except User.DoesNotExist:
            messages.error(request, "Email not registered")
    
    return render(request, "forgot_password.html")

def verify_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        if otp == request.session.get("reset_otp"):
            return redirect("reset_password")
        else:
            messages.error(request, "Invalid OTP")

    return render(request, "verify_otp.html")


# Step 3: Reset Password
def reset_password(request):
    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password == confirm_password:
            email = request.session.get("reset_email")
            user = User.objects.get(email=email)
            user.password = password   # ⚠️ Better: use user.set_password(password) if using Django's auth User
            user.save()

            # Clear session values
            request.session.pop("reset_email", None)
            request.session.pop("reset_otp", None)

            messages.success(request, "Password reset successful. Please login.")
            return redirect("login")
        else:
            messages.error(request, "Passwords do not match")

    return render(request, "reset_password.html")


@never_cache
def teamlead_edit_member(request):

    # -----------------------------------------
    # TEAM LEAD ACCESS CHECK
    # -----------------------------------------
    if (
        not request.session.get("user_id")
        or request.session.get("position") != "team_lead"
    ):
        return redirect("index")

    try:
        team_lead = User.objects.get(
            id=request.session["user_id"]
        )
    except User.DoesNotExist:
        request.session.flush()
        return redirect("index")


    # -----------------------------------------
    # ONLY POST ALLOWED
    # -----------------------------------------
    if request.method != "POST":
        return redirect("teamlead_dashboard")


    member_id = request.POST.get("id")

    if not member_id:
        messages.error(request, "Member ID is missing.")
        return redirect("teamlead_dashboard")


    # -----------------------------------------
    # SECURITY:
    # ONLY TEAM MEMBERS FROM TL'S DEPARTMENT
    # -----------------------------------------
    user = get_object_or_404(
        User,
        id=member_id,
        department=team_lead.department,
        job_Position__iexact="Team Member",
    )


    # -----------------------------------------
    # FORM VALUES
    # -----------------------------------------
    employee_id = request.POST.get("employee_id", "").strip()
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()
    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()

    job_position = request.POST.get(
        "job_position",
        "Team Member"
    ).strip()

    designation = request.POST.get(
        "designation",
        ""
    ).strip()

    work_location = request.POST.get(
        "work_location",
        ""
    ).strip()

    status = request.POST.get(
        "status",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    ).strip()

    joining_date = request.POST.get(
        "joining_date",
        ""
    ).strip()

    department_name = request.POST.get(
        "department",
        ""
    ).strip()

    team_name = request.POST.get(
        "team",
        ""
    ).strip()


    # -----------------------------------------
    # UNIQUENESS CHECKS
    # -----------------------------------------
    if User.objects.filter(
        employee_id=employee_id
    ).exclude(id=user.id).exists():

        messages.error(
            request,
            "Employee ID already exists for another user."
        )

        return redirect("teamlead_dashboard")


    if User.objects.filter(
        username=username
    ).exclude(id=user.id).exists():

        messages.error(
            request,
            "Username already exists for another user."
        )

        return redirect("teamlead_dashboard")


    if User.objects.filter(
        email=email
    ).exclude(id=user.id).exists():

        messages.error(
            request,
            "Email already exists for another user."
        )

        return redirect("teamlead_dashboard")


    # -----------------------------------------
    # UPDATE BASIC DETAILS
    # -----------------------------------------
    user.employee_id = employee_id
    user.username = username
    user.email = email
    user.name = name
    user.phone = phone

    user.designation = designation
    user.work_location = work_location
    user.status = status


    # -----------------------------------------
    # KEEP JOB POSITION AS TEAM MEMBER
    # -----------------------------------------
    user.job_Position = "Team Member"


    # -----------------------------------------
    # DEPARTMENT
    # -----------------------------------------
    if department_name:

        try:
            department = Department.objects.get(
                name__iexact=department_name
            )

            # Team Lead can only keep member
            # inside their own department.
            if department.id != team_lead.department_id:
                messages.error(
                    request,
                    "You can only edit members from your department."
                )

                return redirect("teamlead_dashboard")

            user.department = department

        except Department.DoesNotExist:

            messages.error(
                request,
                "Selected department does not exist."
            )

            return redirect("teamlead_dashboard")


    # -----------------------------------------
    # TEAM
    # -----------------------------------------
    if team_name:

        try:
            team = Team.objects.get(
                name__iexact=team_name
            )

            user.team = team

        except Team.DoesNotExist:

            messages.error(
                request,
                "Selected team does not exist."
            )

            return redirect("teamlead_dashboard")

    else:

        user.team = None


    # -----------------------------------------
    # JOINING DATE
    # -----------------------------------------
    if joining_date:

        try:

            user.joining_date = datetime.strptime(
                joining_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            messages.error(
                request,
                "Invalid joining date."
            )

            return redirect("teamlead_dashboard")

    else:

        user.joining_date = None


    # -----------------------------------------
    # PASSWORD
    # Blank = Keep Existing Password
    # -----------------------------------------
    if password:

        user.password = make_password(
            password
        )


    # -----------------------------------------
    # PROFILE IMAGE
    # -----------------------------------------
    if request.FILES.get("profile_image"):

        user.profile_image = request.FILES[
            "profile_image"
        ]


    # -----------------------------------------
    # SAVE
    # -----------------------------------------
    try:

        user.save()

        messages.success(
            request,
            "Team member updated successfully."
        )

    except IntegrityError:

        messages.error(
            request,
            "Unable to update member because of a unique field conflict."
        )

        return redirect("teamlead_dashboard")


    return redirect("teamlead_dashboard")


@never_cache
def teamlead_dashboard(request):
    # 🔒 Restrict access
    if not request.session.get("user_id") or request.session.get("position") != "team_lead":
        return redirect("index")

    try:
        team_lead = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        request.session.flush()
        return redirect("index")

        # Save default Morning and Evening times from an effective date.
    if (
        request.method == "POST"
        and request.POST.get("action") == "save_default_report_schedule"
    ):
        from django.utils import timezone
        from django.utils.dateparse import parse_date

        day_kind = request.POST.get("day_kind", "regular")
        try:
            effective_from = parse_date(
                request.POST.get("effective_from", "")
            )
        except ValueError:
            effective_from = None

        if day_kind not in ("regular", "saturday") or effective_from is None:
            messages.error(request, "Select a valid schedule and start date.")
            return redirect("teamlead_dashboard")

        if effective_from < timezone.localdate():
            messages.error(request, "Start date must be today or later.")
            return redirect("teamlead_dashboard")

        timings = []
        for report_type in ("morning", "evening"):
            start_time = parse_time(
                request.POST.get(f"{report_type}_start", "")
            )
            end_time = parse_time(
                request.POST.get(f"{report_type}_end", "")
            )

            if not start_time or not end_time or start_time >= end_time:
                messages.error(
                    request,
                    f"Enter valid {report_type} start and end times."
                )
                return redirect("teamlead_dashboard")

            timings.append((report_type, start_time, end_time))

        with transaction.atomic():
            for report_type, start_time, end_time in timings:
                ReportDefaultSchedule.objects.update_or_create(
                    team_lead=team_lead,
                    effective_from=effective_from,
                    day_kind=day_kind,
                    report_type=report_type,
                    defaults={
                        "start_time": start_time,
                        "end_time": end_time,
                        "is_active": True,
                    },
                )

        messages.success(
            request,
            f"Default report times saved from {effective_from:%d %B %Y}."
        )
        return redirect(
            f"{request.path}?month={effective_from:%Y-%m}"
        )

    # Save morning/evening windows for one calendar date.
    if request.method == "POST" and request.POST.get("action") == "save_date_report_schedule":
        from django.utils.dateparse import parse_date

        try:
            schedule_date = parse_date(request.POST.get("schedule_date", ""))
        except ValueError:
            schedule_date = None

        if schedule_date is None:
            messages.error(request, "Select a valid report date.")
            return redirect("teamlead_dashboard")

        changes = []

        for report_type in ("morning", "evening"):
            enabled = request.POST.get(f"{report_type}_enabled") == "on"
            start_value = request.POST.get(f"{report_type}_start", "")
            end_value = request.POST.get(f"{report_type}_end", "")

            if enabled:
                start_time = parse_time(start_value)
                end_time = parse_time(end_value)

                if not start_time or not end_time or start_time >= end_time:
                    messages.error(
                        request,
                        f"Enter a valid {report_type} start and end time."
                    )
                    return redirect(
                        f"{request.path}?month={schedule_date:%Y-%m}"
                    )

                changes.append((report_type, True, start_time, end_time))
            else:
                changes.append((report_type, False, None, None))

        with transaction.atomic():
            for report_type, enabled, start_time, end_time in changes:
                if enabled:
                    ReportDateSchedule.objects.update_or_create(
                        team_lead=team_lead,
                        date=schedule_date,
                        report_type=report_type,
                        defaults={
                            "start_time": start_time,
                            "end_time": end_time,
                            "is_active": True,
                        },
                    )
                else:
                    date_setting = ReportDateSchedule.objects.filter(
                        team_lead=team_lead,
                        date=schedule_date,
                        report_type=report_type,
                    ).first()

                    if date_setting is not None:
                        date_setting.is_active = False
                        date_setting.save(update_fields=["is_active"])
                        continue

                    # Save an inactive date override so the default
                    # does not apply to this date.
                    start_value = request.POST.get(
                        f"{report_type}_start", ""
                    )
                    end_value = request.POST.get(
                        f"{report_type}_end", ""
                    )
                    disabled_start = parse_time(start_value)
                    disabled_end = parse_time(end_value)

                    if not disabled_start or not disabled_end:
                        kinds = (
                            ("saturday", "regular")
                            if schedule_date.weekday() == 5
                            else ("regular",)
                        )
                        for kind in kinds:
                            default_setting = (
                                ReportDefaultSchedule.objects.filter(
                                    team_lead=team_lead,
                                    effective_from__lte=schedule_date,
                                    day_kind=kind,
                                    report_type=report_type,
                                )
                                .order_by("-effective_from", "-id")
                                .first()
                            )
                            if default_setting is not None:
                                disabled_start = default_setting.start_time
                                disabled_end = default_setting.end_time
                                break

                    if disabled_start and disabled_end:
                        ReportDateSchedule.objects.create(
                            team_lead=team_lead,
                            date=schedule_date,
                            report_type=report_type,
                            start_time=disabled_start,
                            end_time=disabled_end,
                            is_active=False,
                        )

        messages.success(
            request,
            f"Report times saved for {schedule_date:%d %B %Y}."
        )
        return redirect(f"{request.path}?month={schedule_date:%Y-%m}")
    if request.method == "POST" and request.POST.get("action") == "mark_sundays_holiday":
        month_value = request.POST.get("month", "")

        try:
            first_day = date.fromisoformat(f"{month_value}-01")
        except ValueError:
            messages.error(request, "Select a valid month.")
            return redirect("teamlead_dashboard")

        last_day = calendar.monthrange(first_day.year, first_day.month)[1]

        with transaction.atomic():
            for number in range(1, last_day + 1):
                holiday_date = date(first_day.year, first_day.month, number)
                if holiday_date.weekday() == 6:
                    TeamReportLeave.objects.update_or_create(
                        team_lead=team_lead,
                        date=holiday_date,
                        defaults={
                            "morning_leave": True,
                            "evening_leave": True,
                            "reason": "Sunday holiday",
                        },
                    )

        messages.success(request, "All Sundays marked as Holiday.")
        return redirect(f"{request.path}?month={month_value}")

    # Save one-date leave for the team lead and all members of the team.
    if request.method == "POST" and request.POST.get("action") == "save_team_report_leave":
        from django.utils import timezone
        from django.utils.dateparse import parse_date

        leave_date = parse_date(request.POST.get("leave_date", ""))
        if leave_date is None or leave_date < timezone.localdate():
            messages.error(request, "Select a valid date today or later.")
            return redirect("teamlead_dashboard")

        morning_leave = request.POST.get("morning_leave") == "on"
        evening_leave = request.POST.get("evening_leave") == "on"
        if not morning_leave and not evening_leave:
            # Clearing both selections removes any previous leave on this date.
            TeamReportLeave.objects.filter(team_lead=team_lead, date=leave_date).delete()
            messages.success(request, f"Report leave cleared for {leave_date}.")
        else:
            TeamReportLeave.objects.update_or_create(
                team_lead=team_lead,
                date=leave_date,
                defaults={
                    "morning_leave": morning_leave,
                    "evening_leave": evening_leave,
                    "reason": request.POST.get("reason", "").strip()[:255],
                },
            )
            messages.success(request, f"Report leave saved for {leave_date}.")

        return redirect(f"{request.path}?month={leave_date:%Y-%m}")
    # =========================================================
    # ⚙️ REPORT SCHEDULE CONFIGURATION
    # =========================================================

    report_days = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
    ]

    # ---------------------------------------------------------
    # SAVE REPORT SCHEDULE FROM DASHBOARD MODAL
    # ---------------------------------------------------------
    if (
        request.method == "POST"
        and request.POST.get("action") == "update_report_schedule"
    ):

        for day_value, day_name in report_days:

            # =========================
            # MORNING
            # =========================

            morning_start = request.POST.get(
                f"morning_start_{day_value}"
            )

            morning_end = request.POST.get(
                f"morning_end_{day_value}"
            )

            morning_enabled = request.POST.get(
                f"morning_enabled_{day_value}"
            )

            morning_setting = ReportTimeSetting.objects.filter(
                team_lead=team_lead,
                day_of_week=day_value,
                report_type="morning",
            ).first()

            if (
                morning_enabled == "on"
                and morning_start
                and morning_end
            ):

                ReportTimeSetting.objects.update_or_create(
                    team_lead=team_lead,
                    day_of_week=day_value,
                    report_type="morning",
                    defaults={
                        "start_time": morning_start,
                        "end_time": morning_end,
                        "is_active": True,
                    },
                )

            elif morning_setting:

                morning_setting.is_active = False

                morning_setting.save(
                    update_fields=["is_active"]
                )

            # =========================
            # EVENING
            # =========================

            evening_start = request.POST.get(
                f"evening_start_{day_value}"
            )

            evening_end = request.POST.get(
                f"evening_end_{day_value}"
            )

            evening_enabled = request.POST.get(
                f"evening_enabled_{day_value}"
            )

            evening_setting = ReportTimeSetting.objects.filter(
                team_lead=team_lead,
                day_of_week=day_value,
                report_type="evening",
            ).first()

            if (
                evening_enabled == "on"
                and evening_start
                and evening_end
            ):

                ReportTimeSetting.objects.update_or_create(
                    team_lead=team_lead,
                    day_of_week=day_value,
                    report_type="evening",
                    defaults={
                        "start_time": evening_start,
                        "end_time": evening_end,
                        "is_active": True,
                    },
                )

            elif evening_setting:

                evening_setting.is_active = False

                evening_setting.save(
                    update_fields=["is_active"]
                )

            messages.success(request, "Report schedule updated successfully.")
        return redirect("teamlead_dashboard")

      


    
        # ---------------------------------
    # 📢 Team Lead Announcements
    # ---------------------------------
# ---------------------------------
# 📢 Team Lead Announcements
# ---------------------------------
    if request.method == "POST" and request.POST.get("announcement_submit") == "1":

        announcement_message = request.POST.get("message", "").strip()
        send_to = request.POST.get("send_to", "team")
        selected_member_ids = request.POST.getlist("recipient_ids")

        if not announcement_message:
            messages.error(request, "Please enter an announcement message.")
            return redirect("teamlead_dashboard")

        # Create announcement
        announcement = Announcement.objects.create(
            title="Team Lead Announcement",
            message=announcement_message,
            created_by=team_lead
        )

        # Only Team Members under this Team Lead's department
        eligible_members = User.objects.filter(
            department=team_lead.department,
            job_Position__iexact="Team Member"
        ).exclude(
            id=team_lead.id
        )

        # ---------------------------------
        # Send to Entire Team
        # ---------------------------------
        if send_to == "team":

            recipients = [
                AnnouncementRecipient(
                    announcement=announcement,
                    recipient=member
                )
                for member in eligible_members
            ]

            if recipients:
                AnnouncementRecipient.objects.bulk_create(recipients)

            messages.success(
                request,
                "Announcement sent to the entire team."
            )

        # ---------------------------------
        # Send to Selected Members
        # ---------------------------------
        elif send_to == "selected":

            selected_members = eligible_members.filter(
                id__in=selected_member_ids
            )

            if not selected_members.exists():
                announcement.delete()
                messages.error(
                    request,
                    "Please select at least one team member."
                )
                return redirect("teamlead_dashboard")

            recipients = [
                AnnouncementRecipient(
                    announcement=announcement,
                    recipient=member
                )
                for member in selected_members
            ]

            AnnouncementRecipient.objects.bulk_create(recipients)

            messages.success(
                request,
                "Announcement sent to selected members."
            )


    # --- existing code for login_time, report times, etc. ---

    # ------------------------------
    # 🧩 Team Members
    # ------------------------------

    team_members_qs = User.objects.filter(
        department=team_lead.department,
        job_Position__iexact="Team Member"
    ).exclude(
        id=team_lead.id
    )

    # Get filters from GET request
    search = request.GET.get("search", "").strip()
    team_filter = request.GET.get("team", "")
    position_filter = request.GET.get("position", "")
    department_filter = request.GET.get("department", "")

    # Apply filters dynamically
    if search:
        team_members_qs = team_members_qs.filter(
            Q(name__icontains=search) | Q(email__icontains=search)
        )
    if team_filter:
        team_members_qs = team_members_qs.filter(team__name__iexact=team_filter)
    if position_filter:
        team_members_qs = team_members_qs.filter(job_Position__iexact=position_filter)
    if department_filter:
        team_members_qs = team_members_qs.filter(department__name__iexact=department_filter)

    # Dropdown data
    teams = User.objects.filter(team__isnull=False).values_list('team__name', flat=True).distinct()
    positions = User.objects.filter(job_Position__isnull=False).values_list('job_Position', flat=True).distinct()
    departments = User.objects.filter(department__isnull=False).values_list('department__name', flat=True).distinct()

    # --- Keep your existing stats and report context below ---
    annotated = team_members_qs.annotate(status_clean=Lower(Trim('status')))
    active_members = annotated.filter(status_clean='active').count()
    inactive_members = annotated.filter(status_clean='inactive').count()
    total_users = team_members_qs.count()

        # =========================================================
    # 🕒 CURRENT DAY REPORT SCHEDULE
    # =========================================================

    today = localtime().date()
    current_day = today.weekday()

    today_leave = TeamReportLeave.objects.filter(
        team_lead=team_lead,
        date=today,
    ).first()

    morning_on_leave = bool(today_leave and today_leave.morning_leave)
    evening_on_leave = bool(today_leave and today_leave.evening_leave)

    def get_today_schedule(report_type, on_leave):
        if on_leave:
            return None

        # A date-specific setting has first priority.
        date_setting = ReportDateSchedule.objects.filter(
            team_lead=team_lead,
            date=today,
            report_type=report_type,
        ).first()

        if date_setting is not None:
            return date_setting if date_setting.is_active else None

        # Saturday timing, if saved; otherwise regular timing.
        kinds = (
            ("saturday", "regular")
            if today.weekday() == 5
            else ("regular",)
        )

        for kind in kinds:
            default_setting = (
                ReportDefaultSchedule.objects.filter(
                    team_lead=team_lead,
                    effective_from__lte=today,
                    day_kind=kind,
                    report_type=report_type,
                )
                .order_by("-effective_from", "-id")
                .first()
            )
            if default_setting is not None:
                return default_setting if default_setting.is_active else None

        return None

    current_morning = get_today_schedule(
        "morning", morning_on_leave
    )
    current_evening = get_today_schedule(
        "evening", evening_on_leave
    )

    morning_start = (
        current_morning.start_time if current_morning else None
    )
    morning_end = (
        current_morning.end_time if current_morning else None
    )
    evening_start = (
        current_evening.start_time if current_evening else None
    )
    evening_end = (
        current_evening.end_time if current_evening else None
    )

        # =========================================================
    # 📝 TEAM LEAD REPORT SUBMISSION
    # =========================================================

    morning_allowed = (
        is_within_time_range(
            morning_start,
            morning_end
        )
        if morning_start and morning_end
        else False
    )

    evening_allowed = (
        is_within_time_range(
            evening_start,
            evening_end
        )
        if evening_start and evening_end
        else False
    )

    # ---------------------------------------------------------
    # HANDLE MORNING / EVENING REPORT SUBMISSION
    # ---------------------------------------------------------

    if request.method == "POST":

        now_time = localtime().time()

        # =====================================================
        # 🌅 MORNING REPORT
        # =====================================================

        if "morning_submit" in request.POST:

            if not current_morning:

                messages.error(
                    request,
                    "Morning report submission is not available today."
                )

            elif is_within_time_range(
                morning_start,
                morning_end,
                now_time
            ):

                report_text = request.POST.get(
                    "morning_report",
                    ""
                ).strip()

                status = request.POST.get(
                    "morning_status"
                )

                if report_text and status:

                    MorningReport.objects.create(
                        user=team_lead,
                        department=(
                            str(team_lead.department.name)
                            if team_lead.department
                            else "Unassigned"
                        ),
                        team=(
                            str(team_lead.team.name)
                            if team_lead.team
                            else "Unassigned"
                        ),
                        report_text=report_text,
                        status=status,
                    )
                    messages.success(request, "Morning report submitted successfully.")

                    return redirect(
                        "teamlead_dashboard"
                    )

                else:

                    messages.error(
                        request,
                        "Please fill in all fields before submitting."
                    )

            else:

                messages.error(
                    request,
                    f"You can only submit morning reports between "
                    f"{morning_start.strftime('%I:%M %p')} and "
                    f"{morning_end.strftime('%I:%M %p')}."
                )

        # =====================================================
        # 🌇 EVENING REPORT
        # =====================================================

        elif "evening_submit" in request.POST:

            if not current_evening:

                messages.error(
                    request,
                    "Evening report submission is not available today."
                )

            elif is_within_time_range(
                evening_start,
                evening_end,
                now_time
            ):

                report_text = request.POST.get(
                    "evening_report",
                    ""
                ).strip()

                status = request.POST.get(
                    "evening_status"
                )

                if report_text and status:

                    EveningReport.objects.create(
                        user=team_lead,
                        department=(
                            str(team_lead.department.name)
                            if team_lead.department
                            else "Unassigned"
                        ),
                        team=(
                            str(team_lead.team.name)
                            if team_lead.team
                            else "Unassigned"
                        ),
                        report_text=report_text,
                        status=status,
                    )
                    messages.success(request, "Evening report submitted successfully.")
                    return redirect(
                        "teamlead_dashboard"
                    )

                else:

                    messages.error(
                        request,
                        "Please fill in all fields before submitting."
                    )

            else:

                messages.error(
                    request,
                    f"You can only submit evening reports between "
                    f"{evening_start.strftime('%I:%M %p')} and "
                    f"{evening_end.strftime('%I:%M %p')}."
                )

    # =========================================================
    # 📊 TEAM LEAD REPORTS — LAST 24 HOURS
    # =========================================================

    report_cutoff = now() - timedelta(hours=24)

    morning_reports = MorningReport.objects.filter(
        user=team_lead,
        created_at__gte=report_cutoff
    ).values(
        "report_text",
        "status",
        "created_at"
    )

    for report in morning_reports:
        report["type"] = "Morning"

    evening_reports = EveningReport.objects.filter(
        user=team_lead,
        created_at__gte=report_cutoff
    ).values(
        "report_text",
        "status",
        "created_at"
    )

    for report in evening_reports:
        report["type"] = "Evening"

    all_reports = sorted(
        list(morning_reports) + list(evening_reports),
        key=lambda report: report["created_at"],
        reverse=True
    )


    # =========================================================
    # 📅 ALL SAVED REPORT SCHEDULES
    # =========================================================

    schedule_qs = ReportTimeSetting.objects.filter(
        team_lead=team_lead
    ).order_by(
        "day_of_week",
        "report_type"
    )

    # report_schedule = {}

    # for day_value, day_name in report_days:

    #     morning = schedule_qs.filter(
    #         day_of_week=day_value,
    #         report_type="morning",
    #     ).first()

    #     evening = schedule_qs.filter(
    #         day_of_week=day_value,
    #         report_type="evening",
    #     ).first()

    #     report_schedule[day_value] = {
    #         "day_name": day_name,
    #         "morning": morning,
    #         "evening": evening,
    #     }

    report_schedule = []

    for day_value, day_name in report_days:

        morning = schedule_qs.filter(
            day_of_week=day_value,
            report_type="morning",
        ).first()

        evening = schedule_qs.filter(
            day_of_week=day_value,
            report_type="evening",
        ).first()

        report_schedule.append({
            "day_value": day_value,
            "day_name": day_name,
            "morning": morning,
            "evening": evening,
        })
            # Dates to show in the report schedule modal
    selected_month = request.GET.get("month", "")
    try:
        year, month = map(int, selected_month.split("-"))
        if not 1 <= month <= 12:
            raise ValueError
        first_date = date(year, month, 1)
    except (ValueError, TypeError):
        first_date = localtime().date().replace(day=1)

    year, month = first_date.year, first_date.month
    days_in_month = calendar.monthrange(year, month)[1]

    saved_schedules = {
        (item.date, item.report_type): item
        for item in ReportDateSchedule.objects.filter(
            team_lead=team_lead,
            date__year=year,
            date__month=month,
        )
    }

    saved_leaves = {
        item.date: item
        for item in TeamReportLeave.objects.filter(
            team_lead=team_lead,
            date__year=year,
            date__month=month,
        )
    }

    last_date = date(year, month, days_in_month)
    default_schedules = list(
        ReportDefaultSchedule.objects.filter(
            team_lead=team_lead,
            effective_from__lte=last_date,
        ).order_by("-effective_from", "-id")
    )

    def timing_for(report_date, report_type):
        # A saved date setting takes priority, even when disabled.
        date_setting = saved_schedules.get((report_date, report_type))
        if date_setting is not None:
            return date_setting, "date"

        # Saturday can have its own default. Otherwise use regular timing.
        kinds = (
            ("saturday", "regular")
            if report_date.weekday() == 5
            else ("regular",)
        )

        for kind in kinds:
            for setting in default_schedules:
                if (
                    setting.effective_from <= report_date
                    and setting.day_kind == kind
                    and setting.report_type == report_type
                ):
                    return setting, kind

        return None, None

    date_report_schedule = []
    for day_number in range(1, days_in_month + 1):
        report_date = date(year, month, day_number)
        morning, morning_source = timing_for(report_date, "morning")
        evening, evening_source = timing_for(report_date, "evening")

        date_report_schedule.append({
            "date": report_date,
            "weekday": report_date.strftime("%A"),
            "is_sunday": report_date.weekday() == 6,
            "morning": morning,
            "evening": evening,
            "morning_source": morning_source,
            "evening_source": evening_source,
            "leave": saved_leaves.get(report_date),
        })

        # My tasks and assigned tasks currently in progress
        ongoing_tasks = Task.objects.filter(
        created_by=team_lead,
        status="in_progress",
    ).select_related(
        "assigned_to"
    ).order_by("-created_at", "-id")

    return render(
        request,
        "team_lead/teamlead_dashboard.html",
        {
            "team_lead": team_lead,
            "ongoing_tasks": ongoing_tasks,
            "team_members": team_members_qs,
            "teams": teams,
            "positions": positions,
            "departments": departments,

            "total_users": total_users,
            "active_members": active_members,
            "inactive_members": inactive_members,

            "morning_start": morning_start,
            "morning_end": morning_end,
            "evening_start": evening_start,
            "evening_end": evening_end,
            "morning_allowed": morning_allowed,
            "evening_allowed": evening_allowed,
            "all_reports": all_reports,
            "morning_on_leave": morning_on_leave,
            "evening_on_leave": evening_on_leave,

            "report_schedule": report_schedule,
            "date_report_schedule": date_report_schedule,
            "selected_month": first_date.strftime("%Y-%m"),
            "selected_month_label": first_date.strftime("%B %Y"),
            "current_day": current_day,
        }
    )


def is_within_time_range(start_time, end_time, now=None):
    now = now or localtime().time()
    return start_time <= now <= end_time

# =========================================================
# 🎥 TEAM LEAD GOOGLE MEET
# =========================================================

@never_cache
def teamlead_google_meet(request):

    # =====================================================
    # 🔒 TEAM LEAD ONLY
    # =====================================================
    if (
        not request.session.get("user_id")
        or request.session.get("position") != "team_lead"
    ):
        return redirect("index")

    # =====================================================
    # 👤 LOGGED-IN TEAM LEAD
    # =====================================================
    team_lead = get_object_or_404(
        User,
        id=request.session["user_id"]
    )

    # =====================================================
    # 👥 TEAM MEMBERS
    # =====================================================
    team_members = User.objects.filter(
        department=team_lead.department,
        job_Position__iexact="Team Member"
    ).exclude(
        id=team_lead.id
    ).order_by("name")

    # =====================================================
    # 📋 ELIGIBLE MEMBERS
    # =====================================================
    eligible_members = User.objects.filter(
        department=team_lead.department,
        job_Position__iexact="Team Member"
    ).exclude(
        id=team_lead.id
    )

    # =====================================================
    # 📩 POST
    # =====================================================
    if request.method == "POST":

        action = request.POST.get(
            "action",
            "create_meeting"
        ).strip()

        # =================================================
        # COMMON FORM DATA
        # =================================================
        purpose = request.POST.get(
            "purpose",
            ""
        ).strip()

        meeting_date = request.POST.get(
            "date",
            ""
        ).strip()

        meeting_time = request.POST.get(
            "time",
            ""
        ).strip()

        meeting_link = request.POST.get(
            "meeting_link",
            ""
        ).strip()

        participant_type = request.POST.get(
            "participant_type",
            "all"
        ).strip()

        selected_member_ids = request.POST.getlist(
            "participants"
        )

        # =================================================
        # REQUIRED VALIDATION
        # =================================================
        if not purpose:
            messages.error(
                request,
                "Please enter the meeting purpose."
            )
            return redirect("teamlead_google_meet")

        if not meeting_date:
            messages.error(
                request,
                "Please select a meeting date."
            )
            return redirect("teamlead_google_meet")

        if not meeting_time:
            messages.error(
                request,
                "Please select a meeting time."
            )
            return redirect("teamlead_google_meet")

        if not meeting_link:
            messages.error(
                request,
                "Please enter the Google Meet link."
            )
            return redirect("teamlead_google_meet")

        # =================================================
        # DATE VALIDATION
        # =================================================
        try:
            parsed_date = datetime.strptime(
                meeting_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            messages.error(
                request,
                "Invalid meeting date."
            )
            return redirect("teamlead_google_meet")

        # =================================================
        # TIME VALIDATION
        # =================================================
        try:
            parsed_time = datetime.strptime(
                meeting_time,
                "%H:%M"
            ).time()

        except ValueError:
            messages.error(
                request,
                "Invalid meeting time."
            )
            return redirect("teamlead_google_meet")

        # =================================================
        # GOOGLE MEET LINK VALIDATION
        # =================================================
        if not (
            meeting_link.startswith(
                "https://meet.google.com/"
            )
            or meeting_link.startswith(
                "http://meet.google.com/"
            )
        ):
            messages.error(
                request,
                "Please enter a valid Google Meet link."
            )
            return redirect("teamlead_google_meet")

        # =================================================
        # 👥 PARTICIPANTS VALIDATION
        # =================================================
        if participant_type == "all":

            final_members = eligible_members

        elif participant_type == "selected":

            if not selected_member_ids:

                messages.error(
                    request,
                    "Please select at least one team member."
                )

                return redirect(
                    "teamlead_google_meet"
                )

            final_members = eligible_members.filter(
                id__in=selected_member_ids
            )

            if not final_members.exists():

                messages.error(
                    request,
                    "Selected team members are not valid."
                )

                return redirect(
                    "teamlead_google_meet"
                )

        else:

            messages.error(
                request,
                "Invalid participant selection."
            )

            return redirect(
                "teamlead_google_meet"
            )

        # =================================================
        # ✏️ EDIT MEETING
        # =================================================
        if action == "edit_meeting":

            meeting_id = request.POST.get(
                "meeting_id"
            )

            if not meeting_id:

                messages.error(
                    request,
                    "Meeting ID is missing."
                )

                return redirect(
                    "teamlead_google_meet"
                )

            meeting = get_object_or_404(
                GoogleMeeting,
                id=meeting_id,
                created_by=team_lead
            )
            # ---------------------------------------------
            # PREVENT EDITING ENDED MEETINGS
            # ---------------------------------------------
            if meeting.meeting_status == "ended":
                messages.error(
                    request,
                    "This meeting has already ended and can no longer be edited."
                )
                return redirect("teamlead_google_meet")

            # ---------------------------------------------
            # UPDATE
            # ---------------------------------------------
            meeting.purpose = purpose
            meeting.date = parsed_date
            meeting.time = parsed_time
            meeting.meeting_link = meeting_link

            meeting.save()

            # ---------------------------------------------
            # UPDATE PARTICIPANTS
            # ---------------------------------------------
            meeting.participants.set(
                final_members
            )

            messages.success(
                request,
                "Google Meet updated successfully."
            )

            return redirect(
                "teamlead_google_meet"
            )

        # =================================================
        # ➕ CREATE MEETING
        # =================================================
        meeting = GoogleMeeting.objects.create(
            created_by=team_lead,
            date=parsed_date,
            time=parsed_time,
            meeting_link=meeting_link,
            purpose=purpose,
        )

        meeting.participants.set(
            final_members
        )

        messages.success(
            request,
            "Google Meet scheduled successfully."
        )

        return redirect(
            "teamlead_google_meet"
        )

    # =====================================================
    # 📅 MEETINGS
    # =====================================================
    meetings = GoogleMeeting.objects.filter(
        created_by=team_lead
    ).prefetch_related(
        "participants"
    ).order_by(
        "date",
        "time"
    )

    # =====================================================
    # CONTEXT
    # =====================================================
    context = {
        "team_lead": team_lead,
        "team_members": team_members,
        "meetings": meetings,
    }

    return render(
        request,
        "team_lead/teamlead_google_meet.html",
        context
    )

@never_cache
def teamlead_announcements(request):
    # 🔒 Restrict access
    if (
        not request.session.get("user_id")
        or request.session.get("position") != "team_lead"
    ):
        return redirect("index")

    try:
        team_lead = User.objects.get(
            id=request.session["user_id"]
        )
    except User.DoesNotExist:
        request.session.flush()
        return redirect("index")

    # =========================================================
    # 📢 ANNOUNCEMENT ACTIONS
    # =========================================================

    if request.method == "POST":

        action = request.POST.get("action", "").strip()

        # =====================================================
        # ✏️ EDIT ANNOUNCEMENT
        # =====================================================

        if action == "edit_announcement":

            announcement_id = request.POST.get(
                "announcement_id"
            )

            edited_message = request.POST.get(
                "message", ""
            ).strip()

            if not edited_message:
                messages.error(
                    request,
                    "Announcement message cannot be empty."
                )
                return redirect(
                    "teamlead_announcements"
                )

            try:
                announcement = Announcement.objects.get(
                    id=announcement_id,
                    created_by=team_lead,
                    is_active=True
                )
            except Announcement.DoesNotExist:
                messages.error(
                    request,
                    "Announcement not found."
                )
                return redirect(
                    "teamlead_announcements"
                )

            # Update the SAME announcement.
            # All existing recipients will see the
            # updated message.
            announcement.message = edited_message
            announcement.save()

            messages.success(
                request,
                "Announcement updated successfully."
            )

            return redirect(
                "teamlead_announcements"
            )


        # =====================================================
        # 🗑️ DELETE ANNOUNCEMENT
        # =====================================================

        elif action == "delete_announcement":

            announcement_id = request.POST.get(
                "announcement_id"
            )

            try:
                announcement = Announcement.objects.get(
                    id=announcement_id,
                    created_by=team_lead,
                    is_active=True
                )
            except Announcement.DoesNotExist:
                messages.error(
                    request,
                    "Announcement not found."
                )
                return redirect(
                    "teamlead_announcements"
                )

            # Soft delete.
            # Recipient records stay safe, but the
            # announcement will no longer be displayed.
            announcement.is_active = False
            announcement.save(
                update_fields=["is_active"]
            )

            messages.success(
                request,
                "Announcement deleted successfully."
            )

            return redirect(
                "teamlead_announcements"
            )


        # =====================================================
        # 📢 CREATE ANNOUNCEMENT
        # =====================================================

        elif action == "create_announcement":

            announcement_message = request.POST.get(
                "message", ""
            ).strip()

            send_to = request.POST.get(
                "send_to",
                "team"
            )

            selected_member_ids = request.POST.getlist(
                "recipient_ids"
            )

            # Empty message validation
            if not announcement_message:
                messages.error(
                    request,
                    "Please enter an announcement message."
                )
                return redirect(
                    "teamlead_announcements"
                )

            # -------------------------------------------------
            # Create announcement
            # -------------------------------------------------

            announcement = Announcement.objects.create(
                title="Team Lead Announcement",
                message=announcement_message,
                created_by=team_lead
            )

            # -------------------------------------------------
            # Only Team Members under this Team Lead's
            # department
            # -------------------------------------------------

            eligible_members = User.objects.filter(
                department=team_lead.department,
                job_Position__iexact="Team Member"
            ).exclude(
                id=team_lead.id
            )

            # -------------------------------------------------
            # Send to Entire Team
            # -------------------------------------------------

            if send_to == "team":

                recipients = [
                    AnnouncementRecipient(
                        announcement=announcement,
                        recipient=member
                    )
                    for member in eligible_members
                ]

                if recipients:
                    AnnouncementRecipient.objects.bulk_create(
                        recipients
                    )

                messages.success(
                    request,
                    "Announcement sent to the entire team."
                )


            # -------------------------------------------------
            # Send to Selected Members
            # -------------------------------------------------

            elif send_to == "selected":

                selected_members = eligible_members.filter(
                    id__in=selected_member_ids
                )

                if not selected_members.exists():

                    announcement.delete()

                    messages.error(
                        request,
                        "Please select at least one team member."
                    )

                    return redirect(
                        "teamlead_announcements"
                    )

                recipients = [
                    AnnouncementRecipient(
                        announcement=announcement,
                        recipient=member
                    )
                    for member in selected_members
                ]

                AnnouncementRecipient.objects.bulk_create(
                    recipients
                )

                messages.success(
                    request,
                    "Announcement sent to selected members."
                )

            return redirect(
                "teamlead_announcements"
            )


    # =========================================================
    # 📢 PREVIOUS ANNOUNCEMENTS
    # =========================================================

    announcements = Announcement.objects.filter(
    created_by=team_lead,
    is_active=True
).prefetch_related(
    "recipients__recipient"
).order_by(
    "-created_at"
)[:20]


    # =========================================================
    # 👥 TEAM MEMBERS
    # =========================================================

    team_members = User.objects.filter(
        department=team_lead.department,
        job_Position__iexact="Team Member"
    ).exclude(
        id=team_lead.id
    ).order_by("name")


    return render(
        request,
        "team_lead/teamlead_announcements.html",
        {
            "announcements": announcements,
            "team_members": team_members,
            "team_lead": team_lead,
        }
    )




def teamlead_chat(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    current_user = get_object_or_404(User, id=user_id)

    # Bring current user to the top of the list
    users = list(User.objects.exclude(id=current_user.id))
    users.sort(key=lambda u: u.name.lower())

    extra_contacts = ExtraContact.objects.all()
    groups = Group.objects.filter(memberships__user=current_user).distinct()

    # Handle Create Group from modal
    if request.method == "POST" and request.POST.get("action") == "create_group":
        group_name = request.POST.get("group_name")
        member_ids = request.POST.getlist("members")  # list of user ids

        if group_name:
            with transaction.atomic():
                # ✅ Create group with required created_by field
                group = Group.objects.create(name=group_name, created_by=current_user)

                # Add creator as group member
                GroupMember.objects.create(group=group, user=current_user)

                # Add other selected members
                for uid in member_ids:
                    user = User.objects.get(id=uid)
                    GroupMember.objects.get_or_create(group=group, user=user)

            messages.success(request, f"Group '{group_name}' created successfully!")
            return redirect("teammember_chat")
        else:
            messages.error(request, "Please provide a group name.")

    context = {
        "current_user": current_user,
        "users": users,
        "extra_contacts": extra_contacts,
        "role": "teammember",
        "groups": groups,
    }

    return render(request, 'team_lead/teamlead_chat.html', context)



def teamlead_chat_room(request, user_id):

    user_id_session = request.session.get("user_id")

    if not user_id_session:
        return redirect("login_view")

    current_user = get_object_or_404(
        User,
        id=user_id_session
    )

    other_user = get_object_or_404(
        User,
        id=user_id
    )

    # =========================================================
    # CHAT APP CONVERSATION
    # =========================================================

    user1 = current_user
    user2 = other_user

    # Keep the same user order
    # so duplicate conversations are avoided.
    if user1.id > user2.id:
        user1, user2 = user2, user1

    conversation = Conversation.objects.filter(
        user1=user1,
        user2=user2
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(
            user1=user1,
            user2=user2
        )

    # =========================================================
    # MESSAGES
    # =========================================================

    messages_list = conversation.messages.select_related(
        "sender"
    ).order_by("created_at")

    # =========================================================
    # SIDEBAR USERS
    # =========================================================

    users = User.objects.exclude(
        id=current_user.id
    ).order_by("name")

    # Existing groups
    groups = Group.objects.filter(
        memberships__user=current_user
    ).distinct()

    context = {
        "room": conversation,
        "current_user": current_user,
        "other_user": other_user,
        "messages": messages_list,
        "users": users,
        "groups": groups,
    }

    return render(
        request,
        "team_lead/teamlead_chat_room.html",
        context
    )

def teamlead_group_chat_view(request, group_id):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login_view")

    current_user = get_object_or_404(
        User,
        id=user_id
    )

    group = get_object_or_404(
        Group,
        id=group_id
    )

    messages_qs = GroupMessage.objects.filter(
        group=group
    ).order_by("timestamp")

    members = GroupMember.objects.filter(
        group=group
    ).select_related("user")

    all_users = User.objects.exclude(
        id__in=[member.user.id for member in members]
    )

    users = list(
        User.objects.exclude(id=current_user.id)
    )

    users.sort(
        key=lambda user: user.name.lower()
    )

    extra_contacts = ExtraContact.objects.all()

    groups = Group.objects.filter(
        memberships__user=current_user
    ).distinct()

    # -----------------------------
    # ADD MEMBER / REMOVE MEMBER
    # -----------------------------
    if request.method == "POST":

        action = request.POST.get("action")

        if action == "add_member":

            new_user_id = request.POST.get("user_id")

            new_user = get_object_or_404(
                User,
                id=new_user_id
            )

            GroupMember.objects.get_or_create(
                group=group,
                user=new_user
            )

            messages.success(
                request,
                f"{new_user.name} added to {group.name}."
            )

            return redirect(
                "teamlead_group_chat_view",
                group_id=group.id
            )

        elif action == "remove_member":

            rem_user_id = request.POST.get("user_id")

            member = get_object_or_404(
                GroupMember,
                group=group,
                user_id=rem_user_id
            )

            member.delete()

            messages.warning(
                request,
                "Member removed successfully."
            )

            return redirect(
                "teamlead_group_chat_view",
                group_id=group.id
            )

    context = {
        "group": group,
        "messages": messages_qs,
        "members": members,
        "all_users": all_users,
        "current_user": current_user,
        "users": users,
        "extra_contacts": extra_contacts,
        "groups": groups,
        "user_role": "team_lead",
    }

    return render(
        request,
        "team_lead/teamlead_group_chat.html",
        context
    )



# # ✅ List of all team members (chat sidebar)
# def teammember_chat(request):
#     user_id = request.session.get("user_id")
#     if not user_id:
#         return redirect("login_view")
#
#     current_user = get_object_or_404(User, id=user_id)
#
#     # Bring current user to the top of the list
#     users = list(User.objects.exclude(id=current_user.id))
#     users.sort(key=lambda u: u.name.lower())
#
#     extra_contacts = ExtraContact.objects.all()
#     # ✅ Fetch groups where the current user is a member
#     groups = Group.objects.filter(memberships__user=current_user).distinct()
#
#     context = {
#         "current_user": current_user,
#         "users": users,
#         "extra_contacts": extra_contacts,
#         "groups": groups,
#         "role": "teammember",
#     }
#     return render(request, "teammember_chat.html", context)


def teammember_chat(request):
    # Check session-based login
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    current_user = get_object_or_404(User, id=user_id)

    # Users list excluding current user
    users = list(User.objects.exclude(id=current_user.id))
    users.sort(key=lambda u: u.name.lower())

    extra_contacts = ExtraContact.objects.all()
    groups = Group.objects.filter(memberships__user=current_user).distinct()

    # Handle Create Group from modal
    if request.method == "POST" and request.POST.get("action") == "create_group":
        group_name = request.POST.get("group_name")
        member_ids = request.POST.getlist("members")  # list of user ids

        if group_name:
            with transaction.atomic():
                # ✅ Create group with required created_by field
                group = Group.objects.create(name=group_name, created_by=current_user)

                # Add creator as group member
                GroupMember.objects.create(group=group, user=current_user)

                # Add other selected members
                for uid in member_ids:
                    user = User.objects.get(id=uid)
                    GroupMember.objects.get_or_create(group=group, user=user)

            messages.success(request, f"Group '{group_name}' created successfully!")
            return redirect("teammember_chat")
        else:
            messages.error(request, "Please provide a group name.")

    context = {
        "current_user": current_user,
        "users": users,
        "extra_contacts": extra_contacts,
        "groups": groups,
        "role": "teammember",
    }

    return render(request, "team_member/teammember_chat.html", context)




def get_or_create_room(user1, user2):
    
    if user1.id > user2.id:
        user1, user2 = user2, user1
    room, created = ChatRoom.objects.get_or_create(user1=user1, user2=user2)
    return room



def chat_room(request, user_id):
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return redirect("login_view")

    current_user = get_object_or_404(User, id=current_user_id)
    other_user = get_object_or_404(User, id=user_id)
    room = get_or_create_room(current_user, other_user)
    users = User.objects.exclude(id=current_user.id).order_by('name')
    extra_contacts = User.objects.filter(status='inactive').exclude(id=current_user.id)
    messages_list = room.messages.order_by("timestamp")
    groups = Group.objects.filter(memberships__user=current_user).distinct()

    # ✅ Normalize role safely
    user_role = request.session.get("position", "").strip().lower().replace(" ", "_")

    # Handle group creation
    if request.method == "POST" and request.POST.get("action") == "create_group":
        group_name = request.POST.get("group_name")
        member_ids = request.POST.getlist("members")

        if group_name:
            with transaction.atomic():
                group = Group.objects.create(name=group_name, created_by=current_user)
                GroupMember.objects.create(group=group, user=current_user)
                for uid in member_ids:
                    user = User.objects.get(id=uid)
                    GroupMember.objects.get_or_create(group=group, user=user)

            messages.success(request, f"Group '{group_name}' created successfully!")
            return redirect("chat_room", user_id=user_id)
        else:
            messages.error(request, "Please provide a group name.")

    context = {
        "room": room,
        "current_user": current_user,
        "other_user": other_user,
        "messages": messages_list,
        "users": users,
        "extra_contacts": extra_contacts,
        "groups": groups,
        "user_role": user_role,   # ✅ correct key used in template
    }

    return render(request, "chat_room.html", context)


def group_chat_view(request, group_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    current_user = get_object_or_404(User, id=user_id)

    # ✅ Correct role logic
    user_role = request.session.get("position", "").strip().lower().replace(" ", "_")

    group = get_object_or_404(Group, id=group_id)
    messages_qs = GroupMessage.objects.filter(group=group).order_by('timestamp')
    members = GroupMember.objects.filter(group=group).select_related('user')
    all_users = User.objects.exclude(id__in=[m.user.id for m in members])

    users = list(User.objects.exclude(id=current_user.id))
    users.sort(key=lambda u: u.name.lower())
    extra_contacts = ExtraContact.objects.all()
    groups = Group.objects.filter(memberships__user=current_user).distinct()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_member":
            new_user_id = request.POST.get("user_id")
            new_user = get_object_or_404(User, id=new_user_id)
            GroupMember.objects.get_or_create(group=group, user=new_user)
            messages.success(request, f"{new_user.name} added to {group.name}.")
            return redirect('group_chat_view', group_id=group.id)

        elif action == "remove_member":
            rem_user_id = request.POST.get("user_id")
            member = get_object_or_404(GroupMember, group=group, user_id=rem_user_id)
            member.delete()
            messages.warning(request, "Member removed successfully.")
            return redirect('group_chat_view', group_id=group.id)

    # AJAX partial
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('partial') == 'true':
        return render(request, 'partials/group_chat_partial.html', {
            "group": group,
            "messages": messages_qs,
            "members": members,
            "all_users": all_users,
            "current_user": current_user,
            "users": users,
            "extra_contacts": extra_contacts,
            "groups": groups,
            "user_role": user_role,  # ✅ pass correct role
        })

    # Full page render
    context = {
        "group": group,
        "messages": messages_qs,
        "members": members,
        "all_users": all_users,
        "current_user": current_user,
        "users": users,
        "extra_contacts": extra_contacts,
        "groups": groups,
        "user_role": user_role,  # ✅ correct value
    }
    return render(request, 'group_chat.html', context)


# @never_cache
# def teammember_dashboard(request):
#     # ❌ Redirect if not logged in or invalid session
#     if not request.session.get("user_id") or request.session.get("position") != "team_member":
#         return redirect("login_view")

#     # ✅ Fetch logged-in team member
#     try:
#         team_member = User.objects.get(id=request.session['user_id'])
#     except User.DoesNotExist:
#         request.session.flush()
#         return redirect("login_view")

#     team_name = team_member.team

#     # 🕒 Convert login time from session
#     login_time_str = request.session.get('login_time')
#     login_time = parse_datetime(login_time_str) if login_time_str else None
#     if login_time:
#         if is_naive(login_time):
#             login_time = make_aware(login_time)
#         login_time = localtime(login_time)

#     # 🕗 Fetch configurable report submission windows from DB
#     morning_setting = ReportTimeSetting.objects.filter(report_type='morning').first()
#     evening_setting = ReportTimeSetting.objects.filter(report_type='evening').first()

#     # Default/fallback times
#     morning_start = morning_setting.start_time if morning_setting else time(9, 30)
#     morning_end = morning_setting.end_time if morning_setting else time(10, 30)
#     evening_start = evening_setting.start_time if evening_setting else time(17, 0)
#     evening_end = evening_setting.end_time if evening_setting else time(18, 15)

#     # 📝 Handle report submissions
#     if request.method == "POST":
#         now_time = localtime().time()

#         # 🌅 Morning report submission
#         if 'morning_submit' in request.POST:
#             if is_within_time_range(morning_start, morning_end, now_time):
#                 report_text = request.POST.get("morning_report")
#                 status = request.POST.get("morning_status")

#                 if report_text and status:
#                     MorningReport.objects.create(
#                         user=team_member,
#                         department=str(team_member.department.name) if team_member.department else "Unassigned",
#                         team=str(team_member.team.name) if team_member.team else "Unassigned",
#                         report_text=report_text,
#                         status=status
#                     )
#                     messages.success(request, "Morning report submitted successfully.")
#                     return redirect('teammember_dashboard')
#                 else:
#                     messages.error(request, "Please fill in all fields before submitting.")
#             else:
#                 messages.error(
#                     request,
#                     f"You can only submit morning reports between "
#                     f"{morning_start.strftime('%I:%M %p')} and {morning_end.strftime('%I:%M %p')}."
#                 )

#         # 🌇 Evening report submission
#         elif 'evening_submit' in request.POST:
#             if is_within_time_range(evening_start, evening_end, now_time):
#                 report_text = request.POST.get("evening_report")
#                 status = request.POST.get("evening_status")

#                 if report_text and status:
#                     EveningReport.objects.create(
#                         user=team_member,
#                         department=str(team_member.department.name) if team_member.department else "Unassigned",
#                         team=str(team_member.team.name) if team_member.team else "Unassigned",
#                         report_text=report_text,
#                         status=status
#                     )
#                     messages.success(request, "Evening report submitted successfully.")
#                     return redirect('teammember_dashboard')
#                 else:
#                     messages.error(request, "Please fill in all fields before submitting.")
#             else:
#                 messages.error(
#                     request,
#                     f"You can only submit evening reports between "
#                     f"{evening_start.strftime('%I:%M %p')} and {evening_end.strftime('%I:%M %p')}."
#                 )

#     # 📊 Fetch reports submitted in the last 24 hours
#     report_cutoff = now() - timedelta(hours=24)

#     morning_reports = MorningReport.objects.filter(
#         user=team_member,
#         created_at__gte=report_cutoff
#     ).values("report_text", "status", "created_at")

#     for r in morning_reports:
#         r["type"] = "Morning"

#     evening_reports = EveningReport.objects.filter(
#         user=team_member,
#         created_at__gte=report_cutoff
#     ).values("report_text", "status", "created_at")

#     for r in evening_reports:
#         r["type"] = "Evening"

#     # Combine & sort all reports
#     all_reports = sorted(
#         list(morning_reports) + list(evening_reports),
#         key=lambda x: x["created_at"],
#         reverse=True
#     )

# #     announcements = Announcement.objects.filter(
# #     created_by__department=team_member.department,
# #     created_by__job_Position__iexact="Team Lead",
# #     created_at__gte=now() - timedelta(hours=12)
# # ).order_by('-created_at')

#     # ---------------------------------
#     # 📢 Team Member Announcements
#     # ---------------------------------
#     # Show only announcements specifically assigned
#     # to the currently logged-in Team Member.
#     # announcements = Announcement.objects.filter(
#     #     recipients__recipient=team_member,
#     #     created_at__gte=now() - timedelta(hours=12)
#     # ).distinct().order_by('-created_at')



#     announcements = Announcement.objects.filter(
#         recipients__recipient=team_member,
#         is_active=True,
#         created_at__gte=now() - timedelta(hours=12)
#     ).distinct().order_by('-created_at')

#         # ---------------------------------
#     # 👁️ Automatically mark announcements as Seen
#     # ---------------------------------
#     unread_recipients = AnnouncementRecipient.objects.filter(
#         recipient=team_member,
#         announcement_id__in=[ann.id for ann in announcements],
#         read_at__isnull=True
#     )

#     if unread_recipients.exists():
#         unread_recipients.update(read_at=localtime())

#     # 🧭 Render dashboard
#     return render(request, 'team_member/teammember_dashboard.html', {
#         'announcements': announcements,
#         'morning_allowed': is_within_time_range(morning_start, morning_end),
#         'evening_allowed': is_within_time_range(evening_start, evening_end),
#         'login_time': login_time,
#         'all_reports': all_reports,
#         'morning_start': morning_start,
#         'morning_end': morning_end,
#         'evening_start': evening_start,
#         'evening_end': evening_end,
#     })


@never_cache
def teammember_dashboard(request):
    # ❌ Redirect if not logged in or invalid session
    if (
        not request.session.get("user_id")
        or request.session.get("position") != "team_member"
    ):
        return redirect("login_view")

    # ✅ Fetch logged-in team member
    try:
        team_member = User.objects.get(
            id=request.session["user_id"]
        )
    except User.DoesNotExist:
        request.session.flush()
        return redirect("login_view")

    team_name = team_member.team

    # =========================================================
    # 🕒 LOGIN TIME
    # =========================================================
    login_time_str = request.session.get("login_time")
    login_time = parse_datetime(login_time_str) if login_time_str else None

    if login_time:
        if is_naive(login_time):
            login_time = make_aware(login_time)
        login_time = localtime(login_time)

    # =========================================================
    # 📅 TODAY'S DAY
    # Monday = 0
    # Tuesday = 1
    # ...
    # Saturday = 5
    # Sunday = 6
    # =========================================================
    current_datetime = localtime()
    today = current_datetime.date()
    current_day = today.weekday()

    # Use the lead of this member's team.
    team_lead = None
    if team_member.team_id:
        team_lead = User.objects.filter(
            team_id=team_member.team_id,
            job_Position__iexact="Team Lead",
        ).first()

    morning_setting = None
    evening_setting = None
    morning_on_leave = False
    evening_on_leave = False

    if team_lead:
        today_leave = TeamReportLeave.objects.filter(
            team_lead=team_lead,
            date=today,
        ).first()

        morning_on_leave = bool(today_leave and today_leave.morning_leave)
        evening_on_leave = bool(today_leave and today_leave.evening_leave)

        if not morning_on_leave:
            morning_setting = ReportDateSchedule.objects.filter(
                team_lead=team_lead,
                date=today,
                report_type="morning",
                is_active=True,
            ).first()

        if not evening_on_leave:
            evening_setting = ReportDateSchedule.objects.filter(
                team_lead=team_lead,
                date=today,
                report_type="evening",
                is_active=True,
            ).first()

    # =========================================================
    # 🌅 MORNING REPORT TIME
    # =========================================================
    morning_start = (
        morning_setting.start_time
        if morning_setting
        else None
    )

    morning_end = (
        morning_setting.end_time
        if morning_setting
        else None
    )

    # =========================================================
    # 🌇 EVENING REPORT TIME
    # =========================================================
    evening_start = (
        evening_setting.start_time
        if evening_setting
        else None
    )

    evening_end = (
        evening_setting.end_time
        if evening_setting
        else None
    )

    # =========================================================
    # 📝 HANDLE REPORT SUBMISSIONS
    # =========================================================
    if request.method == "POST":
        now_time = localtime().time()

        # =====================================================
        # 🌅 MORNING REPORT
        # =====================================================
        if "morning_submit" in request.POST:

            # No schedule configured for today
            if not morning_setting:
                messages.error(
                    request,
                    "Morning report submission is not available today."
                )

            elif is_within_time_range(
                morning_start,
                morning_end,
                now_time
            ):
                report_text = request.POST.get("morning_report")
                status = request.POST.get("morning_status")

                if report_text and status:
                    MorningReport.objects.create(
                        user=team_member,
                        department=(
                            str(team_member.department.name)
                            if team_member.department
                            else "Unassigned"
                        ),
                        team=(
                            str(team_member.team.name)
                            if team_member.team
                            else "Unassigned"
                        ),
                        report_text=report_text,
                        status=status,
                    )

                    messages.success(
                        request,
                        "Morning report submitted successfully."
                    )

                    return redirect("teammember_dashboard")

                else:
                    messages.error(
                        request,
                        "Please fill in all fields before submitting."
                    )

            else:
                messages.error(
                    request,
                    f"You can only submit morning reports between "
                    f"{morning_start.strftime('%I:%M %p')} and "
                    f"{morning_end.strftime('%I:%M %p')}."
                )

        # =====================================================
        # 🌇 EVENING REPORT
        # =====================================================
        elif "evening_submit" in request.POST:

            # No schedule configured for today
            if not evening_setting:
                messages.error(
                    request,
                    "Evening report submission is not available today."
                )

            elif is_within_time_range(
                evening_start,
                evening_end,
                now_time
            ):
                report_text = request.POST.get("evening_report")
                status = request.POST.get("evening_status")

                if report_text and status:
                    EveningReport.objects.create(
                        user=team_member,
                        department=(
                            str(team_member.department.name)
                            if team_member.department
                            else "Unassigned"
                        ),
                        team=(
                            str(team_member.team.name)
                            if team_member.team
                            else "Unassigned"
                        ),
                        report_text=report_text,
                        status=status,
                    )

                    messages.success(
                        request,
                        "Evening report submitted successfully."
                    )

                    return redirect("teammember_dashboard")

                else:
                    messages.error(
                        request,
                        "Please fill in all fields before submitting."
                    )

            else:
                messages.error(
                    request,
                    f"You can only submit evening reports between "
                    f"{evening_start.strftime('%I:%M %p')} and "
                    f"{evening_end.strftime('%I:%M %p')}."
                )

    # =========================================================
    # 📊 FETCH REPORTS FROM LAST 24 HOURS
    # =========================================================
    report_cutoff = now() - timedelta(hours=24)

    morning_reports = MorningReport.objects.filter(
        user=team_member,
        created_at__gte=report_cutoff
    ).values(
        "report_text",
        "status",
        "created_at"
    )

    for r in morning_reports:
        r["type"] = "Morning"

    evening_reports = EveningReport.objects.filter(
        user=team_member,
        created_at__gte=report_cutoff
    ).values(
        "report_text",
        "status",
        "created_at"
    )

    for r in evening_reports:
        r["type"] = "Evening"

    # =========================================================
    # 🔄 COMBINE + SORT REPORTS
    # =========================================================
    all_reports = sorted(
        list(morning_reports) + list(evening_reports),
        key=lambda x: x["created_at"],
        reverse=True
    )

    # =========================================================
    # 📢 TEAM MEMBER ANNOUNCEMENTS
    # =========================================================
    announcements = Announcement.objects.filter(
        recipients__recipient=team_member,
        is_active=True,
        created_at__gte=now() - timedelta(hours=12)
    ).distinct().order_by("-created_at")

    # =========================================================
    # 👁️ AUTOMATICALLY MARK ANNOUNCEMENTS AS SEEN
    # =========================================================
    unread_recipients = AnnouncementRecipient.objects.filter(
        recipient=team_member,
        announcement_id__in=[
            ann.id for ann in announcements
        ],
        read_at__isnull=True
    )

    if unread_recipients.exists():
        unread_recipients.update(
            read_at=localtime()
        )

    # =========================================================
    # 🧭 RENDER DASHBOARD
    # =========================================================
    return render(
        request,
        "team_member/teammember_dashboard.html",
        {
            "announcements": announcements,

            # Report availability
            "morning_allowed": (
                is_within_time_range(
                    morning_start,
                    morning_end
                )
                if morning_start and morning_end
                else False
            ),

            "evening_allowed": (
                is_within_time_range(
                    evening_start,
                    evening_end
                )
                if evening_start and evening_end
                else False
            ),

            # Login
            "login_time": login_time,

            # Reports
            "all_reports": all_reports,

            # Morning timing
            "morning_start": morning_start,
            "morning_end": morning_end,

            # Evening timing
            "evening_start": evening_start,
            "evening_end": evening_end,

            # Optional extra context
            "current_day": current_day,
            "team_lead": team_lead,
            "morning_on_leave": morning_on_leave,
            "evening_on_leave": evening_on_leave,
        },
    )

# @never_cache
# def teamlead_reports(request):
#     if (
#         not request.session.get("user_id")
#         or request.session.get("position") != "team_lead"
#     ):
#         return redirect("index")

#     team_lead = get_object_or_404(
#         User,
#         id=request.session["user_id"]
#     )

#     show_all = request.GET.get("all") == "1"
#     filter_date_str = request.GET.get("date")

#     if filter_date_str:
#         try:
#             filter_date = datetime.strptime(
#                 filter_date_str, "%Y-%m-%d"
#             ).date()
#         except ValueError:
#             messages.error(request, "Invalid date format.")
#             return redirect("teamlead_reports")
#     else:
#         filter_date = None

#     morning_reports = MorningReport.objects.filter(
#         team=team_lead.team
#     ).select_related("user")

#     evening_reports = EveningReport.objects.filter(
#         team=team_lead.team
#     ).select_related("user")

#     if not show_all:
#         selected_date = filter_date or localtime().date()
#         morning_reports = morning_reports.filter(
#             created_at__date=selected_date
#         )
#         evening_reports = evening_reports.filter(
#             created_at__date=selected_date
#         )

#     if "export" in request.GET:
#         wb = Workbook()
#         ws = wb.active
#         ws.title = "Team Reports"

#         ws.append([
#             "Date", "Time", "Report Type", "Name",
#             "Team", "Department", "Report", "Status"
#         ])

#         for reports, report_type in (
#             (morning_reports, "Morning"),
#             (evening_reports, "Evening"),
#         ):
#             for report in reports:
#                 report_time = localtime(report.created_at)

#                 ws.append([
#                     report_time.strftime("%Y-%m-%d"),
#                     report_time.strftime("%I:%M %p"),
#                     report_type,
#                     str(report.user.name),
#                     str(report.team or ""),
#                     str(report.department or ""),
#                     str(report.report_text or ""),
#                     str(report.status or ""),
#                 ])

#         for cell in ws[1]:
#             cell.alignment = Alignment(
#                 horizontal="center",
#                 vertical="center"
#             )

#         for row in ws.iter_rows(min_row=2, min_col=7, max_col=7):
#             for cell in row:
#                 cell.alignment = Alignment(
#                     wrap_text=True,
#                     vertical="top"
#                 )

#         for column, width in enumerate(
#             [15, 12, 14, 22, 20, 22, 50, 16],
#             start=1
#         ):
#             ws.column_dimensions[
#                 get_column_letter(column)
#             ].width = width

#         response = HttpResponse(
#             content_type=(
#                 "application/vnd.openxmlformats-officedocument."
#                 "spreadsheetml.sheet"
#             )
#         )
#         response["Content-Disposition"] = (
#             'attachment; filename="team_reports.xlsx"'
#         )

#         wb.save(response)
#         return response

#     return render(
#         request,
#         "team_lead/teamlead_reports.html",
#         {
#             "morning_reports": morning_reports,
#             "evening_reports": evening_reports,
#             "show_all": show_all,
#             "filter_date": filter_date,
#         }
#     )

# @never_cache
# def teamlead_reports(request):
#     if (
#         not request.session.get("user_id")
#         or request.session.get("position") != "team_lead"
#     ):
#         return redirect("index")

#     team_lead = get_object_or_404(
#         User,
#         id=request.session["user_id"]
#     )

#     report_tab = request.GET.get("tab", "members")
#     if report_tab not in ("my", "members"):
#         report_tab = "members"

#     show_all = request.GET.get("all") == "1"
#     filter_date_str = request.GET.get("date")
#     filter_date = None

#     if filter_date_str:
#         try:
#             filter_date = datetime.strptime(
#                 filter_date_str,
#                 "%Y-%m-%d"
#             ).date()
#         except ValueError:
#             messages.error(request, "Invalid date format.")
#             return redirect("teamlead_reports")

#     if report_tab == "my":
#         report_filters = {"user": team_lead}
#     else:
#         report_filters = {
#             "user__team_id": team_lead.team_id,
#             "user__job_Position__iexact": "Team Member",
#         }

#     morning_reports = MorningReport.objects.filter(
#         **report_filters
#     ).select_related("user").order_by("-created_at")

#     evening_reports = EveningReport.objects.filter(
#         **report_filters
#     ).select_related("user").order_by("-created_at")

#     if not show_all:
#         selected_date = filter_date or localtime().date()
#         morning_reports = morning_reports.filter(
#             created_at__date=selected_date
#         )
#         evening_reports = evening_reports.filter(
#             created_at__date=selected_date
#         )
#     report_date = filter_date or localtime().date()
#     report_day_leave = None

#     if not show_all:
#         report_day_leave = TeamReportLeave.objects.filter(
#             team_lead=team_lead,
#             date=report_date,
#         ).first()
        
#     holiday_users = []

#     if report_day_leave:
#         if report_tab == "my":
#             holiday_users = [team_lead]
#         elif team_lead.team_id:
#             holiday_users = list(
#                 User.objects.filter(
#                     team_id=team_lead.team_id,
#                     job_Position__iexact="Team Member",
#                 ).order_by("name")
#             )

#     if "export" in request.GET:
#         wb = Workbook()
#         ws = wb.active
#         ws.title = (
#             "My Reports"
#             if report_tab == "my"
#             else "Team Members Reports"
#         )

#         ws.append([
#             "Date", "Time", "Report Type", "Name",
#             "Team", "Department", "Report", "Status"
#         ])

#         for reports, report_type in (
#             (morning_reports, "Morning"),
#             (evening_reports, "Evening"),
#         ):
#             for report in reports:
#                 report_time = localtime(report.created_at)

#                 ws.append([
#                     report_time.strftime("%Y-%m-%d"),
#                     report_time.strftime("%I:%M %p"),
#                     report_type,
#                     str(report.user.name),
#                     str(report.team or ""),
#                     str(report.department or ""),
#                     str(report.report_text or ""),
#                     str(report.status or ""),
#                 ])
#         if report_day_leave:
#             for report_type, is_holiday in (
#                 ("Morning", report_day_leave.morning_leave),
#                 ("Evening", report_day_leave.evening_leave),
#             ):
#                 if is_holiday:
#                     for person in holiday_users:
#                         ws.append([
#                             report_date.strftime("%Y-%m-%d"),
#                             "",
#                             report_type,
#                             str(person.name),
#                             str(person.team.name) if person.team else "",
#                             str(person.department.name) if person.department else "",
#                             report_day_leave.reason or "Holiday",
#                             "Holiday",
#                         ])

#         for cell in ws[1]:
#             cell.alignment = Alignment(
#                 horizontal="center",
#                 vertical="center"
#             )

#         for row in ws.iter_rows(min_row=2, min_col=7, max_col=7):
#             for cell in row:
#                 cell.alignment = Alignment(
#                     wrap_text=True,
#                     vertical="top"
#                 )

#         for column, width in enumerate(
#             [15, 12, 14, 22, 20, 22, 50, 16],
#             start=1
#         ):
#             ws.column_dimensions[
#                 get_column_letter(column)
#             ].width = width

#         response = HttpResponse(
#             content_type=(
#                 "application/vnd.openxmlformats-officedocument."
#                 "spreadsheetml.sheet"
#             )
#         )
#         filename = (
#             "my_reports.xlsx"
#             if report_tab == "my"
#             else "team_members_reports.xlsx"
#         )
#         response["Content-Disposition"] = (
#             f'attachment; filename="{filename}"'
#         )

#         wb.save(response)
#         return response

#     return render(
#         request,
#         "team_lead/teamlead_reports.html",
#         {
#             "morning_reports": morning_reports,
#             "evening_reports": evening_reports,
#             "show_all": show_all,
#             "filter_date": filter_date,
#             "report_tab": report_tab,
#             "report_date": report_date,
#             "report_day_leave": report_day_leave,
#             "holiday_users": holiday_users,
#         }
#     )


@never_cache
def teamlead_reports(request):
    """Team lead report list, daily holiday rows, and matching Excel export."""
    if (
        not request.session.get("user_id")
        or request.session.get("position") != "team_lead"
    ):
        return redirect("index")

    team_lead = get_object_or_404(User, id=request.session["user_id"])
    report_tab = request.GET.get("tab", "members")
    if report_tab not in ("my", "members"):
        report_tab = "members"

    show_all = request.GET.get("all") == "1"
    filter_date = None
    filter_date_str = request.GET.get("date")
    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("teamlead_reports")

    report_date = filter_date or localtime().date()
    if report_tab == "my":
        report_filters = {"user": team_lead}
    elif team_lead.team_id:
        report_filters = {
            "user__team_id": team_lead.team_id,
            "user__job_Position__iexact": "Team Member",
        }
    else:
        # A lead without a team cannot see unrelated unassigned users' reports.
        report_filters = {"user__id__in": []}

    morning_reports = MorningReport.objects.filter(
        **report_filters
    ).select_related("user").order_by("-created_at")
    evening_reports = EveningReport.objects.filter(
        **report_filters
    ).select_related("user").order_by("-created_at")

    report_day_leave = None
    holiday_users = []
    if not show_all:
        morning_reports = morning_reports.filter(created_at__date=report_date)
        evening_reports = evening_reports.filter(created_at__date=report_date)
        report_day_leave = TeamReportLeave.objects.filter(
            team_lead=team_lead, date=report_date
        ).first()
        if report_day_leave and (
            report_day_leave.morning_leave or report_day_leave.evening_leave
        ):
            if report_tab == "my":
                holiday_users = [team_lead]
            elif team_lead.team_id:
                holiday_users = list(
                    User.objects.filter(
                        team_id=team_lead.team_id,
                        job_Position__iexact="Team Member",
                    ).order_by("name")
                )

    if "export" in request.GET:
        wb = Workbook()
        ws = wb.active
        ws.title = "My Reports" if report_tab == "my" else "Team Members Reports"
        ws.append([
            "Date", "Time", "Report Type", "Name",
            "Team", "Department", "Report", "Status",
        ])

        for reports, report_type in (
            (morning_reports, "Morning"),
            (evening_reports, "Evening"),
        ):
            for report in reports:
                report_time = localtime(report.created_at)
                ws.append([
                    report_time.strftime("%Y-%m-%d"),
                    report_time.strftime("%I:%M %p"),
                    report_type,
                    str(report.user.name),
                    str(report.team or ""),
                    str(report.department or ""),
                    str(report.report_text or ""),
                    str(report.status or ""),
                ])

        if report_day_leave:
            for report_type, is_holiday in (
                ("Morning", report_day_leave.morning_leave),
                ("Evening", report_day_leave.evening_leave),
            ):
                if is_holiday:
                    for person in holiday_users:
                        ws.append([
                            report_date.strftime("%Y-%m-%d"),
                            "",
                            report_type,
                            str(person.name),
                            str(person.team.name) if person.team else "",
                            str(person.department.name) if person.department else "",
                            report_day_leave.reason or "Holiday",
                            "Holiday",
                        ])

        for cell in ws[1]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for row in ws.iter_rows(min_row=2, min_col=7, max_col=7):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        for column, width in enumerate(
            [15, 12, 14, 22, 20, 22, 50, 16], start=1
        ):
            ws.column_dimensions[get_column_letter(column)].width = width

        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )
        filename = (
            "my_reports.xlsx" if report_tab == "my"
            else "team_members_reports.xlsx"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )
        wb.save(response)
        return response

    return render(
        request,
        "team_lead/teamlead_reports.html",
        {
            "morning_reports": morning_reports,
            "evening_reports": evening_reports,
            "show_all": show_all,
            "filter_date": filter_date,
            "report_tab": report_tab,
            "report_date": report_date,
            "report_day_leave": report_day_leave,
            "holiday_users": holiday_users,
        },
    )


@never_cache
def teamlead_project_assigning(request):
    # 🔒 Prevent KeyError: check session before accessing user
    if not request.session.get("user_id") or request.session.get("position") != "team_lead":
        return redirect("index")

    team_lead = get_object_or_404(User, id=request.session["user_id"])
    departments = Department.objects.all()

    team_members = User.objects.filter(
        team=team_lead.team,
        job_Position__icontains="team member"
    ).exclude(id=team_lead.id)

    if request.method == "POST":
        # First create the project without files/images
        project = ProjectAssign.objects.create(
            team=team_lead.team,
            department_id=request.POST.get("department"),
            assign_to_id=request.POST.get("assign_to"),
            assigned_by=team_lead,
            work_name=request.POST.get("work_name"),
            work_type=request.POST.get("work_type"),
            category=request.POST.get("category"),
            description=request.POST.get("description"),
            deadline=request.POST.get("deadline"),
            additional_notes=request.POST.get("additional_notes"),
            color_preference=request.POST.get("color_preference"),
            content_example=request.POST.get("content_example"),
            priority=request.POST.get("priority"),
        )

        # Handle multiple uploaded files
        for file in request.FILES.getlist("upload_file[]"):
            ProjectFile.objects.create(project=project, file=file)

        # Handle multiple uploaded images
        for image in request.FILES.getlist("upload_image[]"):
            ProjectImage.objects.create(project=project, image=image)

        messages.success(request, "Project assigned successfully.")

        return redirect("teamlead_project_assigning")

    projects = ProjectAssign.objects.filter(team=team_lead.team)

    return render(request, "team_lead/teamlead_project_assigning.html", {
        "departments": departments,
        "team_lead": team_lead,
        "team_members": team_members,
        "projects": projects,
    })

def project_assign_edit(request, pk):
    project = get_object_or_404(ProjectAssign, id=pk)
    departments = Department.objects.all()
    team_members = User.objects.filter(
        team=project.team, job_Position__iexact="Team Member"
    ).exclude(id=project.assigned_by.id)

    if request.method == "POST":
        project.department_id = request.POST.get("department")
        project.assign_to_id = request.POST.get("assign_to")
        project.work_name = request.POST.get("work_name")
        project.work_type = request.POST.get("work_type")
        project.category = request.POST.get("category")
        project.description = request.POST.get("description")

        deadline = request.POST.get("deadline")
        project.deadline = deadline if deadline else None

        project.additional_notes = request.POST.get("additional_notes")
        project.color_preference = request.POST.get("color_preference")
        project.content_example = request.POST.get("content_example")
        project.priority = request.POST.get("priority")
        project.save()

        # ✅ Save new files (without removing old ones)
        for file in request.FILES.getlist("upload_file[]"):
            ProjectFile.objects.create(project=project, file=file)

        # ✅ Save new images (without removing old ones)
        for image in request.FILES.getlist("upload_image[]"):
            ProjectImage.objects.create(project=project, image=image)

        messages.success(request, "Project updated successfully.")

        return redirect("teamlead_project_assigning")

    return render(request, "team_lead/teamlead_project_assigning.html", {
        "project": project,
        "departments": departments,
        "team_members": team_members,
    })

def project_assign_delete(request, pk):
    project = get_object_or_404(ProjectAssign, id=pk)
    project.delete()
    messages.success(request, "Project deleted successfully.")
    return redirect("teamlead_project_assigning")

@never_cache
def teammember_project(request):
    user_id = request.session.get("user_id")
    if not user_id:   # if session expired or user logged out
        return redirect("index")

    user = get_object_or_404(User, id=user_id)
    projects = ProjectAssign.objects.filter(assign_to=user).order_by("-assigned_date")

    if request.method == "POST":
        project_id = request.POST.get("project_id")
        status = request.POST.get("status")
        project = get_object_or_404(ProjectAssign, id=project_id, assign_to=user)
        project.status = status
        project.save()
        return redirect("teammember_project")

    return render(request, "team_member/teammember_project.html", {"projects": projects})
def update_project_status(request, pk):
    user_id = request.session.get("user_id")  
    if not user_id:
        messages.error(request, "You must be logged in to update status.")
        return redirect("index")  # or your login page

    user = get_object_or_404(User, id=user_id)
    project = get_object_or_404(ProjectAssign, pk=pk, assign_to=user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(ProjectAssign.STATUS_CHOICES):
            project.status = new_status
            project.save()
            messages.success(request, f"Project status updated to {new_status}")
        else:
            messages.error(request, "Invalid status selected.")

    return redirect("teammember_project")
# Ensure these imports exist at the TOP of monitoringapp/views.py.
from urllib.parse import urlencode
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

# Replace ONLY your existing teamlead_notepad function (including @never_cache).
# Keep your existing Notepad/User, render/redirect/get_object_or_404,
# messages and never_cache imports. Keep teamlead_notepad_delete unchanged.

@never_cache
def teamlead_notepad(request):
    user_id = request.session.get("user_id")
    if not user_id or request.session.get("position") != "team_lead":
        return redirect("index")
    user = get_object_or_404(User, pk=user_id)
    owned = Notepad.objects.filter(user=user)
    params = request.POST if request.method == "POST" else request.GET
    query = params.get("q", "").strip()[:200]
    sort = params.get("sort", "updated")
    orderings = {"updated": ("-updated_at", "-id"), "created": ("-created_at", "-id"), "title": ("title", "id")}
    if sort not in orderings:
        sort = "updated"
    notes = owned
    if query:
        notes = notes.filter(Q(title__icontains=query) | Q(content__icontains=query))
    page_obj = Paginator(notes.order_by(*orderings[sort]), 4).get_page(params.get("page"))
    selected_id = request.POST.get("note_id") if request.method == "POST" else None
    note = None
    if selected_id:
        try:
            selected_id = int(selected_id)
        except (ValueError, TypeError):
            return HttpResponseBadRequest("Invalid note ID.")
        note = get_object_or_404(owned, pk=selected_id)
    error = ""
    title = note.title if note else ""
    content = (note.content or "") if note else ""
    if request.method == "POST":
        title = request.POST.get("title", "").strip() or "Untitled"
        content = request.POST.get("content", "")
        if len(title) > 255:
            error = "Title must be 255 characters or fewer."
        elif not content.strip():
            error = "Write some content before saving the note."
        else:
            if note:
                note.title, note.content = title, content
                note.save()
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({
                        "ok": True, "id": note.pk, "title": note.title,
                        "content": note.content or "",
                        "updated_at": timezone.localtime(note.updated_at).strftime("%d %b %Y, %I:%M %p"),
                    })
                messages.success(request, "Note updated successfully.")
            else:
                note = Notepad.objects.create(user=user, title=title, content=content)
                messages.success(request, "Note created successfully.")
            return redirect(reverse("teamlead_notepad") + "?" + urlencode({
                "q": query if selected_id else "", "sort": sort if selected_id else "updated", "page": page_obj.number if selected_id else 1,
            }))
    if error and selected_id and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": False, "message": error}, status=400)
    response = render(request, "team_lead/teamlead_notepad.html", {
        "note": None, "page_obj": page_obj, "query": query, "sort": sort,
        "form_title": title if not selected_id else "", "form_content": content if not selected_id else "", "note_error": error,
        "total_notes": owned.count(),
    })
    if error:
        response.status_code = 400
    return response


@never_cache
@require_POST
def teamlead_notepad_delete(request, pk):
    user_id = request.session.get("user_id")
    if not user_id or request.session.get("position") != "team_lead":
        return redirect("index")
    user = get_object_or_404(User, pk=user_id)
    note = get_object_or_404(Notepad, pk=pk, user=user)
    note.delete()
    messages.success(request, "Note deleted successfully.")
    sort = request.POST.get("sort", "updated")
    if sort not in {"updated", "created", "title"}:
        sort = "updated"
    return redirect(reverse("teamlead_notepad") + "?" + urlencode({
        "q": request.POST.get("q", "").strip()[:200],
        "sort": sort, "page": request.POST.get("page", "1"),
    }))




@never_cache
def teammember_notepad(request):
    user_id = request.session.get("user_id")
    if not user_id:   # 🔒 No session → back to index
        return redirect("index")

    user = get_object_or_404(User, id=user_id)

    # All notes for this user
    all_notes = Notepad.objects.filter(user=user).order_by("-updated_at")

    # Pagination (4 notes per page)
    paginator = Paginator(all_notes, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Note to edit/view
    note_id = request.GET.get("note_id")
    note = None
    if note_id:
        try:
            note = Notepad.objects.get(id=note_id, user=user)
        except Notepad.DoesNotExist:
            note = None  # Invalid ID → open new note

    if request.method == "POST":
        note_id_post = request.POST.get("note_id")
        title = request.POST.get("title") or "Untitled"
        content = request.POST.get("content")

        if note_id_post:
            # Update existing note
            note = get_object_or_404(Notepad, id=note_id_post, user=user)
            note.title = title
            note.content = content
            note.save()
        else:
            # Create new note
            note = Notepad.objects.create(user=user, title=title, content=content)

        return redirect(f"{request.path}?note_id={note.id}")

    return render(request, "team_member/teammember_notepad.html", {"note": note, "page_obj": page_obj})




@never_cache
def teamlead_repository(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("index")  # or "login_view" if you want login page

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        link = request.POST.get("link")
        file = request.FILES.get("file")

        Knowledge.objects.create(
            department=user.department,
            user=user,
            title=title,
            description=description,
            link=link,
            file=file
        )

        messages.success(request, "Resource added successfully.")
        return redirect("teamlead_repository")

    knowledge_items = Knowledge.objects.filter(department=user.department).order_by("-created_at")

    response = render(request, "team_lead/teamlead_repository.html", {"knowledge_items": knowledge_items})
    
    # Extra cache protection
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    
    return response


def teamlead_repository_delete(request, pk):
    user = get_object_or_404(User, id=request.session.get("user_id"))
    resource = get_object_or_404(Knowledge, id=pk, department=user.department)

    if request.method == "POST":
        resource.delete()
        messages.success(request, "Resource deleted successfully.")
        return redirect("teamlead_repository")

from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.cache import never_cache

@never_cache
def teammember_repository(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("index")

    user = get_object_or_404(User, id=user_id)

    # ✅ If user has no department, assign fallback
    department = user.department if hasattr(user, "department") and user.department else Department.objects.first()

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        link = request.POST.get("link")
        file = request.FILES.get("file")

        # ✅ Make sure department is not None before saving
        if not department:
            return render(request, "team_member/teammember_repository.html", {
                "error": "No department found for this user or in database."
            })

        Knowledge.objects.create(
            department=department,
            user=user,
            title=title,
            description=description,
            link=link,
            file=file
        )

        return redirect("teammember_repository")

    # ✅ Fetch repository items department-wise
    knowledge_items = Knowledge.objects.filter(department=department).order_by("-created_at")

    return render(request, "team_member/teammember_repository.html", {
        "knowledge_items": knowledge_items
    })


@never_cache
def teammember_repository_delete(request, pk):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("index")  # redirect to login page

    user = get_object_or_404(User, id=user_id)
    department = user.department if hasattr(user, "department") and user.department else Department.objects.first()
    resource = get_object_or_404(Knowledge, id=pk, department=department)

    # Allow both GET and POST delete
    resource.delete()
    return redirect("teammember_repository")
@never_cache
def teamlead_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("index")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        action = request.POST.get("action")

        # AJAX Profile Image Update
        if action == "edit_profile" and request.FILES.get("profile_image"):
            user.profile_image = request.FILES["profile_image"]
            user.save()
            return JsonResponse({
                "success": True,
                "image_url": user.profile_image.url
            })

        # Normal form update for other details
        elif action == "edit_profile":
            user.name = request.POST.get("name")
            user.email = request.POST.get("email")
            user.phone = request.POST.get("phone")
            user.work_location = request.POST.get("work_location")
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("teamlead_profile")

    # Render page
    response = render(request, "team_lead/teamlead_profile.html", {"user": user})
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

@never_cache
def teammember_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("index")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        action = request.POST.get("action")

        # Profile image AJAX upload
        if action == "edit_profile" and request.FILES.get("profile_image"):
            user.profile_image = request.FILES["profile_image"]
            user.save()

            # Check if AJAX
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "image_url": user.profile_image.url
                })

            # fallback redirect for normal form submit
            messages.success(request, "Profile image updated successfully!")
            return redirect("teammember_profile")

        # Normal form update (other details)
        elif action == "edit_profile":
            user.name = request.POST.get("name")
            user.email = request.POST.get("email")
            user.phone = request.POST.get("phone")
            user.work_location = request.POST.get("work_location")

            if "profile_image" in request.FILES:
                user.profile_image = request.FILES["profile_image"]

            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("teammember_profile")

    return render(request, "team_member/teammember_profile.html", {"user": user})
@never_cache
def teammember_task(request):
    user_id = request.session.get("user_id")
    if not user_id:   # 🔒 session expired or logged out
        return redirect("index")   # safer than showing error

    user = get_object_or_404(User, id=user_id)

    # ✅ Only tasks created by this logged-in user
    tasks = Task.objects.filter(created_by=user).order_by("-created_at")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        if title:  # prevent empty titles
            Task.objects.create(
                title=title,
                description=description,
                assigned_to=user,   # optional: assign to self
                created_by=user     # track who created it
            )
        return redirect("teammember_task")

    return render(request, "team_member/teammember_task.html", {"tasks": tasks})


# TEAM MEMBER UPDATE TASK
def update_task(request, task_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    user = User.objects.get(id=user_id)

    # ✅ Only allow updating tasks created by this user
    task = get_object_or_404(Task, id=task_id, created_by=user)

    if request.method == "POST":
        status = request.POST.get("status")
        task.status = status
        # Update progress based on status
        task.progress = {"pending": 0, "in_progress": 50, "completed": 100}.get(status, 0)
        task.save()

    return redirect("teammember_task")


# TEAM MEMBER DELETE TASK
def delete_task(request, task_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    user = User.objects.get(id=user_id)

    # ✅ Only allow deletion of tasks created by this user
    task = get_object_or_404(Task, id=task_id, created_by=user)

    if request.method == "POST":
        task.delete()

    return redirect("teammember_task")

@never_cache
def teamlead_task(request):

    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("index")

    user = get_object_or_404(User, id=user_id)


    # =========================================================
    # TEAM MEMBERS
    # =========================================================

    team_members = User.objects.filter(
        team=user.team
    ).exclude(
        id=user.id
    ).order_by("name")


    # =========================================================
    # MY TASKS
    # =========================================================

    my_tasks = Task.objects.filter(
        created_by=user,
        assigned_to=user
    ).order_by("-created_at")


    # =========================================================
    # ASSIGNED TASKS
    # =========================================================

    assigned_tasks = Task.objects.filter(
        created_by=user
    ).exclude(
        assigned_to=user
    ).select_related(
        "assigned_to"
    ).order_by("-created_at")


    # =========================================================
    # ALL TASKS
    # Used for summary cards
    # =========================================================

    all_tasks = Task.objects.filter(
        created_by=user
    )


    total_tasks = all_tasks.count()


    pending_tasks = all_tasks.filter(
        status="pending"
    ).count()


    completed_tasks = all_tasks.filter(
        status="completed"
    ).count()


    # =========================================================
    # CREATE / ASSIGN TASK
    # =========================================================

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        task_mode = request.POST.get(
            "task_mode",
            "personal"
        )

        assigned_to_id = request.POST.get(
            "assigned_to"
        )


        # =====================================================
        # TITLE VALIDATION
        # =====================================================

        if not title:

            messages.error(
                request,
                "Please enter a task title."
            )

            return redirect("teamlead_task")


        # =====================================================
        # MY TASK
        # =====================================================

        if task_mode == "personal":

            Task.objects.create(
                title=title,
                description=description,
                assigned_to=user,
                created_by=user,
                status="pending",
                progress=0
            )

            messages.success(
                request,
                "Your task has been created successfully."
            )

            return redirect("teamlead_task")


        # =====================================================
        # ASSIGN TASK
        # =====================================================

        if task_mode == "assign":

            if not assigned_to_id:

                messages.error(
                    request,
                    "Please select a team member."
                )

                return redirect("teamlead_task")


            # -------------------------------------------------
            # ONLY CURRENT TEAM MEMBERS ARE ALLOWED
            # -------------------------------------------------

            assigned_user = get_object_or_404(
                User,
                id=assigned_to_id,
                team=user.team
            )


            Task.objects.create(
                title=title,
                description=description,
                assigned_to=assigned_user,
                created_by=user,
                status="pending",
                progress=0
            )


            messages.success(
                request,
                f"Task assigned to {assigned_user.name} successfully."
            )

            return redirect("teamlead_task")


        # =====================================================
        # INVALID TASK MODE
        # =====================================================

        messages.error(
            request,
            "Invalid task request."
        )

        return redirect("teamlead_task")


    # =========================================================
    # PAGE
    # =========================================================

    response = render(
        request,
        "team_lead/teamlead_task.html",
        {
            "my_tasks": my_tasks,
            "assigned_tasks": assigned_tasks,
            "team_members": team_members,
            "team_lead": user,

            # Summary cards
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
        }
    )


    response["Cache-Control"] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
    )

    response["Pragma"] = "no-cache"

    response["Expires"] = "0"


    return response

def update_task_teamlead(request, task_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    user = User.objects.get(id=user_id)
    # ✅ Only allow updating tasks created by logged-in user
    task = get_object_or_404(Task, id=task_id, created_by=user)

    if request.method == "POST":
        status = request.POST.get("status")
        task.status = status
        task.progress = {"pending": 0, "in_progress": 50, "completed": 100}.get(status, 0)
        task.save()
        messages.success(request, "Task status updated successfully.")

    return redirect('teamlead_task')


def delete_task_teamlead(request, task_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    user = User.objects.get(id=user_id)
    # ✅ Only allow deletion of tasks created by logged-in user
    task = get_object_or_404(Task, id=task_id, created_by=user)

    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted successfully.")

    return redirect("teamlead_task")



@never_cache
def teamlead_logout(request):
    if "user_id" in request.session:
        try:
            user = User.objects.get(id=request.session["user_id"])
            user.status = "inactive"
            user.last_logout_time = timezone.now()
            user.save()
        except User.DoesNotExist:
            pass

    request.session.flush()
    response = redirect("index")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

@never_cache
def teammember_logout(request):
    if "user_id" in request.session:
        try:
            user = User.objects.get(id=request.session["user_id"])
            user.status = "inactive"
            user.last_logout_time = timezone.now()

            # Set user inactive if applicable
            if hasattr(user, "is_active"):
                try:
                    setattr(user, "is_active", False)
                except Exception:
                    pass

            user.save()
        except User.DoesNotExist:
            pass

    # Clear session
    request.session.flush()

    # Redirect with no-cache protection (same as teamlead)
    response = redirect("index")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

def update_inactive_users():
    cutoff_time = timezone.now() - timedelta(minutes=10)

    User.objects.filter(
        status="active",
        last_activity__lt=cutoff_time
    ).update(status="inactive")

@csrf_exempt
def update_activity(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    user_id = request.session.get("user_id")
    update_inactive_users()

    if not user_id:
        return JsonResponse({"success": False, "message": "Not logged in"}, status=401)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)

    now = timezone.now()

    user.last_activity = now
    user.status = "active"
    user.save(update_fields=["last_activity", "status"])

    return JsonResponse({
        "success": True,
        "status": "active"
    })


def get_user_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "User not found"
        }, status=404)

    # Check if last activity is older than 10 minutes
    if user.last_activity:
        cutoff_time = timezone.now() - timedelta(minutes=10)

        if user.last_activity < cutoff_time:
            user.status = "inactive"
            user.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "status": user.status
    })

from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme


def _notification_teamlead(request):
    if (
        not request.session.get("user_id")
        or request.session.get("position") != "team_lead"
    ):
        return None

    return User.objects.filter(
        pk=request.session["user_id"]
    ).first()

@never_cache
def teamlead_notifications(request):
    team_lead = _notification_teamlead(request)

    if team_lead is None:
        return redirect("login_view")

    notifications = TeamLeadNotification.objects.filter(
        recipient=team_lead
    ).order_by("-created_at", "-id")

    return render(
        request,
        "team_lead/teamlead_notifications.html",
        {
            "items": notifications,
            "unread_count": notifications.filter(
                is_read=False,
                is_archived=False,
            ).count(),
        },
    )


@require_POST
def teamlead_notifications_read_all(request):
    team_lead = _notification_teamlead(request)

    if team_lead is None:
        return redirect("login_view")

    TeamLeadNotification.objects.filter(
        recipient=team_lead,
        is_read=False,
        is_archived=False,
    ).update(is_read=True)

    return redirect("teamlead_notifications")


@require_POST
def teamlead_notification_open(request, notification_id):
    team_lead = _notification_teamlead(request)

    if team_lead is None:
        return redirect("login_view")

    notification = get_object_or_404(
        TeamLeadNotification,
        pk=notification_id,
        recipient=team_lead,
    )

    action = request.POST.get("action", "open")

    changes = {
        "mark_read": {"is_read": True},
        "mark_unread": {"is_read": False},
        "archive": {"is_archived": True},
        "restore": {"is_archived": False},
    }

    if action in changes:
        TeamLeadNotification.objects.filter(
            pk=notification.pk,
            recipient=team_lead,
        ).update(**changes[action])

        return redirect("teamlead_notifications")

    if action != "open":
        return redirect("teamlead_notifications")

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    if notification.url and url_has_allowed_host_and_scheme(
        notification.url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(notification.url)

    return redirect("teamlead_notifications")


# -----------------------------
# TEAM LEAD REMINDERS
# -----------------------------
import calendar
from datetime import datetime as reminder_datetime

from django.contrib import messages as reminder_messages
from django.utils import timezone as reminder_timezone
from django.utils.dateparse import parse_datetime as reminder_parse_datetime
from django.views.decorators.http import require_http_methods

from .models import TeamLeadReminder


def _parse_reminder_datetime(value):
    try:
        parsed = reminder_parse_datetime(value or "")

        if parsed and reminder_timezone.is_naive(parsed):
            parsed = reminder_timezone.make_aware(
                parsed,
                reminder_timezone.get_current_timezone(),
            )

        return parsed
    except (ValueError, TypeError, OverflowError):
        return None


@never_cache
@require_http_methods(["GET", "POST"])
def teamlead_reminders(request):
    team_lead = _notification_teamlead(request)

    if team_lead is None:
        return redirect("login_view")

    # All queries are restricted to this team lead.
    reminders = TeamLeadReminder.objects.filter(owner=team_lead)

    if request.method == "POST":
        action = request.POST.get("action", "")
        reminder = None

        if action in {"update", "delete", "complete", "reopen"}:
            reminder = get_object_or_404(
                reminders,
                pk=request.POST.get("reminder_id"),
            )

        if action == "delete":
            reminder.delete()
            reminder_messages.success(request, "Reminder deleted.")
            return redirect("teamlead_reminders")

        if action in {"complete", "reopen"}:
            reminder.is_completed = action == "complete"
            reminder.save(
                update_fields=["is_completed", "updated_at"]
            )

            response_message = (
                "Reminder completed."
                if reminder.is_completed
                else "Reminder reopened."
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                from django.http import JsonResponse

                return JsonResponse({
                    "ok": True,
                    "id": reminder.pk,
                    "is_completed": reminder.is_completed,
                    "message": response_message,
                })

            reminder_messages.success(
                request,
                response_message,
            )
            return redirect("teamlead_reminders")

        if action not in {"create", "update"}:
            reminder_messages.error(request, "Invalid reminder action.")
            return redirect("teamlead_reminders")

        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        event_at = _parse_reminder_datetime(
            request.POST.get("event_at")
        )
        remind_at = _parse_reminder_datetime(
            request.POST.get("remind_at")
        )

        if not title or len(title) > 180:
            reminder_messages.error(
                request,
                "Enter a title with a maximum of 180 characters.",
            )
            return redirect("teamlead_reminders")

        if event_at is None or remind_at is None:
            reminder_messages.error(
                request,
                "Enter valid event and reminder dates and times.",
            )
            return redirect("teamlead_reminders")

        if remind_at > event_at:
            reminder_messages.error(
                request,
                "Reminder time must be on or before the event time.",
            )
            return redirect("teamlead_reminders")

        if remind_at <= reminder_timezone.now():
            reminder_messages.error(
                request,
                "Choose a future reminder time.",
            )
            return redirect("teamlead_reminders")

        if reminder is None:
            reminder = TeamLeadReminder(owner=team_lead)

        # Changing the dates allows a new notification to be scheduled.
        schedule_changed = (
            reminder.pk is None
            or reminder.event_at != event_at
            or reminder.remind_at != remind_at
        )

        reminder.title = title
        reminder.description = description
        reminder.event_at = event_at
        reminder.remind_at = remind_at

        if schedule_changed:
            reminder.notified_at = None
            reminder.notification = None
            reminder.is_completed = False

        reminder.save()

        reminder_messages.success(
            request,
            "Reminder created."
            if action == "create"
            else "Reminder updated.",
        )
        return redirect("teamlead_reminders")

    today = reminder_timezone.localdate()

    try:
        selected_month = reminder_datetime.strptime(
            request.GET.get("month", today.strftime("%Y-%m")),
            "%Y-%m",
        ).date()
    except (ValueError, TypeError):
        selected_month = today.replace(day=1)

    month_reminders = reminders.filter(
        event_at__year=selected_month.year,
        event_at__month=selected_month.month,
    ).order_by("event_at", "id")

    calendar_items = []

    for reminder in month_reminders:
        local_event = reminder_timezone.localtime(reminder.event_at)
        local_remind = reminder_timezone.localtime(reminder.remind_at)

        calendar_items.append({
            "id": reminder.pk,
            "title": reminder.title,
            "description": reminder.description,
            "date": local_event.strftime("%Y-%m-%d"),
            "event_at": local_event.strftime("%Y-%m-%dT%H:%M"),
            "remind_at": local_remind.strftime("%Y-%m-%dT%H:%M"),
            "is_completed": reminder.is_completed,
        })

    return render(
        request,
        "team_lead/teamlead_reminders.html",
        {
            "selected_month": selected_month.strftime("%Y-%m"),
            "month_label": selected_month.strftime("%B %Y"),
            "calendar_weeks": calendar.monthcalendar(
                selected_month.year,
                selected_month.month,
            ),
            "calendar_items": calendar_items,
            "today": today.isoformat(),
            "reminders": month_reminders,
        },
    )