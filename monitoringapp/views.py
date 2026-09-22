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
from django.utils.dateparse import parse_datetime
from django.utils.timezone import localtime, make_aware, is_naive
from django.views.decorators.cache import never_cache
from django.utils.cache import add_never_cache_headers

from django.http import JsonResponse
from django.db import transaction

from django.db.models.functions import Lower, Trim

from openpyxl.utils import get_column_letter
from django.utils.dateparse import parse_time

from django.db import IntegrityError
from django.db.models import Q



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

def get_logged_in_user_api(request):
    if request.session.get("user_id"):
        try:
            user = User.objects.get(id=request.session["user_id"])
            return JsonResponse({"name": user.name, "job_position": user.job_Position})
        except User.DoesNotExist:
            pass
    return JsonResponse({"name": None})





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


# Step 2: Verify OTP
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
def teamlead_dashboard(request):
    # 🔒 Restrict access
    if not request.session.get("user_id") or request.session.get("position") != "team_lead":
        return redirect("index")

    try:
        team_lead = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        request.session.flush()
        return redirect("index")

    # --- existing code for login_time, report times, etc. ---

    # ------------------------------
    # 🧩 Team Member Filters
    # ------------------------------
    team_members_qs = User.objects.filter(team=team_lead.team).exclude(id=team_lead.id)

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

    # Render
    return render(request, 'teamlead_dashboard.html', {
        # existing context...
        'team_lead': team_lead,
        'team_members': team_members_qs,
        'teams': teams,
        'positions': positions,
        'departments': departments,
        'total_users': total_users,
        'active_members': active_members,
        'inactive_members': inactive_members,
        # keep your report and timing data...
    })

def is_within_time_range(start_time, end_time, now=None):
    now = now or localtime().time()
    return start_time <= now <= end_time








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

    return render(request, 'teamlead_chat.html', context)




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

@never_cache
def teammember_dashboard(request):

    # =========================================================
    # CHECK LOGIN / SESSION
    # =========================================================

    if (
        not request.session.get("user_id")
        or request.session.get("position") != "team_member"
    ):
        messages.error(
            request,
            "Your session has expired. Please log in again."
        )
        return redirect("login_view")


    # =========================================================
    # FETCH LOGGED-IN TEAM MEMBER
    # =========================================================

    try:

        team_member = User.objects.get(
            id=request.session["user_id"]
        )

    except User.DoesNotExist:

        request.session.flush()

        messages.error(
            request,
            "Your account session is no longer valid. Please log in again."
        )

        return redirect("login_view")


    team_name = team_member.team


    # =========================================================
    # LOGIN TIME
    # =========================================================

    login_time_str = request.session.get("login_time")

    login_time = (
        parse_datetime(login_time_str)
        if login_time_str
        else None
    )

    if login_time:

        if is_naive(login_time):
            login_time = make_aware(login_time)

        login_time = localtime(login_time)


    # =========================================================
    # REPORT TIME SETTINGS
    # =========================================================

    morning_setting = ReportTimeSetting.objects.filter(
        report_type="morning"
    ).first()

    evening_setting = ReportTimeSetting.objects.filter(
        report_type="evening"
    ).first()


    # Default times

    morning_start = (
        morning_setting.start_time
        if morning_setting
        else time(9, 30)
    )

    morning_end = (
        morning_setting.end_time
        if morning_setting
        else time(10, 30)
    )

    evening_start = (
        evening_setting.start_time
        if evening_setting
        else time(15, 0)
    )

    evening_end = (
        evening_setting.end_time
        if evening_setting
        else time(18, 15)
    )


    # =========================================================
    # HANDLE POST REQUESTS
    # =========================================================

    if request.method == "POST":

        now_time = localtime().time()


        # =====================================================
        # MORNING REPORT
        # =====================================================

        if "morning_submit" in request.POST:

            report_text = request.POST.get(
                "morning_report",
                ""
            ).strip()

            status = request.POST.get(
                "morning_status",
                ""
            ).strip()


            # ---------------------------------------------
            # CHECK TIME
            # ---------------------------------------------

            if not is_within_time_range(
                morning_start,
                morning_end,
                now_time
            ):

                messages.error(
                    request,
                    f"Morning report can only be submitted between "
                    f"{morning_start.strftime('%I:%M %p')} and "
                    f"{morning_end.strftime('%I:%M %p')}."
                )

                return redirect("teammember_dashboard")


            # ---------------------------------------------
            # CHECK REQUIRED FIELDS
            # ---------------------------------------------

            if not report_text:

                messages.error(
                    request,
                    "Please enter your morning report."
                )

                return redirect("teammember_dashboard")


            if not status:

                messages.error(
                    request,
                    "Please select a status for your morning report."
                )

                return redirect("teammember_dashboard")


            # ---------------------------------------------
            # CREATE MORNING REPORT
            # ---------------------------------------------

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

                status=status
            )


            # ---------------------------------------------
            # SUCCESS TOAST
            # ---------------------------------------------

            messages.success(
                request,
                f"Morning report submitted successfully with status: {status}."
            )

            return redirect("teammember_dashboard")


        # =====================================================
        # EVENING REPORT
        # =====================================================

        elif "evening_submit" in request.POST:

            report_text = request.POST.get(
                "evening_report",
                ""
            ).strip()

            status = request.POST.get(
                "evening_status",
                ""
            ).strip()


            # ---------------------------------------------
            # CHECK TIME
            # ---------------------------------------------

            if not is_within_time_range(
                evening_start,
                evening_end,
                now_time
            ):

                messages.error(
                    request,
                    f"Evening report can only be submitted between "
                    f"{evening_start.strftime('%I:%M %p')} and "
                    f"{evening_end.strftime('%I:%M %p')}."
                )

                return redirect("teammember_dashboard")


            # ---------------------------------------------
            # CHECK REQUIRED FIELDS
            # ---------------------------------------------

            if not report_text:

                messages.error(
                    request,
                    "Please enter your evening report."
                )

                return redirect("teammember_dashboard")


            if not status:

                messages.error(
                    request,
                    "Please select a status for your evening report."
                )

                return redirect("teammember_dashboard")


            # ---------------------------------------------
            # CREATE EVENING REPORT
            # ---------------------------------------------

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

                status=status
            )


            # ---------------------------------------------
            # SUCCESS TOAST
            # ---------------------------------------------

            messages.success(
                request,
                f"Evening report submitted successfully with status: {status}."
            )

            return redirect("teammember_dashboard")


    # =========================================================
    # FETCH REPORTS - LAST 24 HOURS
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

    for report in morning_reports:
        report["type"] = "Morning"


    evening_reports = EveningReport.objects.filter(
        user=team_member,
        created_at__gte=report_cutoff
    ).values(
        "report_text",
        "status",
        "created_at"
    )

    for report in evening_reports:
        report["type"] = "Evening"


    # =========================================================
    # COMBINE REPORTS
    # =========================================================

    all_reports = sorted(
        list(morning_reports) + list(evening_reports),
        key=lambda x: x["created_at"],
        reverse=True
    )


    # =========================================================
    # ANNOUNCEMENTS
    # =========================================================

    announcements = Announcement.objects.filter(
        created_by__team=team_member.team,
        created_at__gte=now() - timedelta(hours=12)
    ).order_by("-created_at")


    # =========================================================
    # RENDER DASHBOARD
    # =========================================================

    return render(
        request,
        "team_member/teammember_dashboard.html",
        {
            "announcements": announcements,

            "morning_allowed": is_within_time_range(
                morning_start,
                morning_end
            ),

            "evening_allowed": is_within_time_range(
                evening_start,
                evening_end
            ),

            "login_time": login_time,

            "all_reports": all_reports,

            "morning_start": morning_start,

            "morning_end": morning_end,

            "evening_start": evening_start,

            "evening_end": evening_end,
        }
    )

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

#     announcements = Announcement.objects.filter(
#         created_by__team=team_member.team,
#         created_at__gte=now() - timedelta(hours=12)
#     ).order_by('-created_at')

#     # 🧭 Render dashboard
#     return render(request, 'teammember_dashboard.html', {
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
def teamlead_reports(request):
    if not request.session.get("user_id") or request.session.get("position") != "team_lead":
        return redirect("index")

    team_lead = get_object_or_404(User, id=request.session["user_id"])
    team_name = team_lead.team

    show_all = request.GET.get("all") == "1"
    filter_date_str = request.GET.get("date")

    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("teamlead_reports")
    else:
        filter_date = None

    # Morning Reports
    if show_all:
        morning_reports = MorningReport.objects.filter(team=team_name)
        evening_reports = EveningReport.objects.filter(team=team_name)
    else:
        today = datetime.today().date()
        morning_reports = MorningReport.objects.filter(team=team_name, created_at__date=filter_date or today)
        evening_reports = EveningReport.objects.filter(team=team_name, created_at__date=filter_date or today)

    # Export to Excel
    if "export" in request.GET:
        if not morning_reports.exists() and not evening_reports.exists():
            messages.error(request, "No reports available to export.")
            return redirect("teamlead_reports")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Team Reports"
        headers = ["Date", "Time", "Report Type", "Name", "Team", "Department", "Report", "Status"]
        ws.append(headers)

        def add_reports(report_list, report_type):
            for report in report_list:
                local_time = timezone.localtime(report.created_at)
                ws.append([
                    local_time.strftime("%Y-%m-%d"),
                    local_time.strftime("%I:%M %p"),
                    report_type,
                    getattr(report.user, "name", report.user.username),
                    report.team,
                    report.department,
                    report.report_text,
                    report.status
                ])

        add_reports(morning_reports, "Morning")
        add_reports(evening_reports, "Evening")

        for row in ws.iter_rows(min_row=2, min_col=7, max_col=7):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

        column_widths = [15, 12, 12, 20, 15, 20, 50, 15]
        for i, width in enumerate(column_widths, start=1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="team_reports.xlsx"'
        wb.save(response)
        return response

    return render(request, "teamlead_reports.html", {
        "morning_reports": morning_reports,
        "evening_reports": evening_reports,
        "show_all": show_all,
    })

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

        messages.success(
            request,
            f'Project "{project.work_name}" assigned successfully!'
        )

        return redirect("teamlead_project_assigning")

    projects = ProjectAssign.objects.filter(team=team_lead.team)

    return render(request, "teamlead_project_assigning.html", {
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
        messages.success(
            request,
            f'Project "{project.work_name}" updated successfully!'
        )

        return redirect("teamlead_project_assigning")

    return render(request, "teamlead_project_assigning.html", {
        "project": project,
        "departments": departments,
        "team_members": team_members,
    })

def project_assign_delete(request, pk):
    project = get_object_or_404(ProjectAssign, id=pk)
    project_name = project.work_name
    project.delete()
    messages.success(
        request,
        f'Project "{project_name}" deleted successfully!'
    )
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
        # project.status = status
        # project.save()
        if status in dict(ProjectAssign.STATUS_CHOICES):
            project.status = status
            project.save()

            messages.success(
                request,
                f'Project "{project.work_name}" updated to {project.get_status_display()}.'
            )
        else:
            messages.error(
                request,
                "Invalid status selected."
            )
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
            # messages.success(request, f"Project status updated to {new_status}")
            messages.success(
                request,
                f'Project "{project.work_name}" updated to {project.get_status_display()}.'
            )
        else:
            messages.error(request, "Invalid status selected.")

    return redirect("teammember_project")

@never_cache
def teamlead_notepad(request):
    # 🔒 Prevent access if logged out
    user_id = request.session.get("user_id")
    if not user_id or request.session.get("position") != "team_lead":
        return redirect("index")

    user = get_object_or_404(User, id=user_id)

    # ✅ Only this user's notes
    all_notes = Notepad.objects.filter(user=user).order_by("-updated_at")

    # Pagination
    paginator = Paginator(all_notes, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # View/Edit a specific note (only if it belongs to this user)
    note = None
    note_id = request.GET.get("note_id")
    if note_id:
        note = Notepad.objects.filter(id=note_id, user=user).first()

    if request.method == "POST":
        note_id_post = request.POST.get("note_id")
        title = request.POST.get("title") or "Untitled"
        content = request.POST.get("content")

        if note_id_post:
            # ✅ Update only if owned by this user
            note = get_object_or_404(Notepad, id=note_id_post, user=user)
            note.title = title
            note.content = content
            note.save()
            messages.success(
                request,
                f'Note "{title}" updated successfully!'
            )
        else:
            # ✅ New note tied to this user
            note = Notepad.objects.create(user=user, title=title, content=content)
            messages.success(
                request,
                f'Note "{title}" saved successfully!'
            )

        return redirect(f"{request.path}?note_id={note.id}")

    return render(
        request,
        "teamlead_notepad.html",
        {"note": note, "page_obj": page_obj},
    )




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
            messages.success(
                request,
                f'Note "{note.title}" updated successfully.'
            )
        else:
            # Create new note
            note = Notepad.objects.create(user=user, title=title, content=content)
            messages.success(
                request,
                f'Note "{note.title}" created successfully.'
            )

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
        messages.success(
            request,
            f'Resource "{title}" added successfully!'
        )
        return redirect("teamlead_repository")

    knowledge_items = Knowledge.objects.filter(department=user.department).order_by("-created_at")

    response = render(request, "teamlead_repository.html", {"knowledge_items": knowledge_items})
    
    # Extra cache protection
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    
    return response


def teamlead_repository_delete(request, pk):
    user = get_object_or_404(User, id=request.session.get("user_id"))
    resource = get_object_or_404(Knowledge, id=pk, department=user.department)

    if request.method == "POST":
        title = resource.title
        resource.delete()
        messages.success(
            request,
            f'Resource "{title}" deleted successfully!'
        )
        return redirect("teamlead_repository")
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

        if not title:

            messages.error(
                request,
                "Resource title is required."
            )

        Knowledge.objects.create(
            department=department,
            user=user,
            title=title,
            description=description,
            link=link,
            file=file
        )
        messages.success(
            request,
            f'Resource "{title}" added successfully.'
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
    if request.method == "POST":

        resource_title = resource.title

        resource.delete()

        messages.success(
            request,
            f'Resource "{resource_title}" deleted successfully.'
        )
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
    response = render(request, "teamlead_profile.html", {"user": user})
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

# @never_cache
# def teammember_profile(request):
#     user_id = request.session.get("user_id")
#     if not user_id:
#         return redirect("index")

#     user = get_object_or_404(User, id=user_id)

#     if request.method == "POST":
#         action = request.POST.get("action")

#         # Profile image AJAX upload
#         if action == "edit_profile" and request.FILES.get("profile_image"):
#             user.profile_image = request.FILES["profile_image"]
#             user.save()

#             # Check if AJAX
#             if request.headers.get("x-requested-with") == "XMLHttpRequest":
#                 return JsonResponse({
#                     "success": True,
#                     "image_url": user.profile_image.url
#                 })

#             # fallback redirect for normal form submit
#             messages.success(request, "Profile image updated successfully!")
#             return redirect("teammember_profile")

#         # Normal form update (other details)
#         elif action == "edit_profile":
#             user.name = request.POST.get("name")
#             user.email = request.POST.get("email")
#             user.phone = request.POST.get("phone")
#             user.work_location = request.POST.get("work_location")

#             if "profile_image" in request.FILES:
#                 user.profile_image = request.FILES["profile_image"]

#             user.save()
#             messages.success(request, "Profile updated successfully!")
#             return redirect("teammember_profile")

#     return render(request, "teammember_profile.html", {"user": user})


@never_cache
def teammember_profile(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("index")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        action = request.POST.get("action")

        # ==========================================
        # Profile image AJAX upload
        # ==========================================
        if action == "edit_profile" and request.FILES.get("profile_image"):

            user.profile_image = request.FILES["profile_image"]
            user.save()

            # AJAX request
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "image_url": user.profile_image.url
                })

            # Normal form submission
            messages.success(
                request,
                "Profile image updated successfully!"
            )

            return redirect("teammember_profile")

        # ==========================================
        # Normal profile update
        # ==========================================
        elif action == "edit_profile":

            user.name = request.POST.get("name")
            user.email = request.POST.get("email")
            user.phone = request.POST.get("phone")
            user.work_location = request.POST.get("work_location")

            if "profile_image" in request.FILES:
                user.profile_image = request.FILES["profile_image"]

            user.save()

            messages.success(
                request,
                "Profile updated successfully!"
            )

            return redirect("teammember_profile")

    return render(
        request,
        "team_member/teammember_profile.html",
        {
            "user": user
        }
    )


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
            messages.success(
                request,
                f'Task "{title}" added successfully.'
            )
        else:
            messages.error(
                request,
                "Task title is required."
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
        valid_statuses = [
            "pending",
            "in_progress",
            "completed"
        ]
        if status in valid_statuses:
            task.status = status
            # Update progress based on status
            task.progress = {"pending": 0, "in_progress": 50, "completed": 100}.get(status, 0)
            task.save()
            status_text = task.get_status_display()

            messages.success(
                request,
                f'Task "{task.title}" updated to {status_text}.'
            )
        else:

            messages.error(
                request,
                "Invalid task status."
            )

    return redirect("teammember_task")


# TEAM MEMBER DELETE TASK
def delete_task(request, task_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login_view")

    user = get_object_or_404(User, id=user_id)

    # ✅ Only allow deletion of tasks created by this user
    task = get_object_or_404(Task, id=task_id, created_by=user)

    if request.method == "POST":
        task_title = task.title

        task.delete()

        messages.success(
            request,
            f'Task "{task_title}" deleted successfully.'
        )

    return redirect("teammember_task")



@never_cache
def teamlead_task(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("index")  # Redirect to index if not logged in

    user = get_object_or_404(User, id=user_id)

    # Only show tasks created by this logged-in user
    tasks = Task.objects.filter(created_by=user).order_by('-created_at')

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        if not title:  # prevent creating empty tasks
            messages.error(
                request,
                "Task title is required."
            )
            return redirect("teamlead_task")

        Task.objects.create(
            title=title,
            description=description,
            assigned_to=user,
            created_by=user
        )
        messages.success(
            request,
            f'Task "{title}" created successfully.'
        )

        return redirect("teamlead_task")

    response = render(request, 'teamlead_task.html', {"tasks": tasks})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def update_task_teamlead(request, task_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(
            request,
            "You must be logged in."
        )
        return redirect("login_view")

    user = User.objects.get(id=user_id)
    # ✅ Only allow updating tasks created by logged-in user
    task = get_object_or_404(Task, id=task_id, created_by=user)

    if request.method == "POST":
        status = request.POST.get("status")
        valid_statuses = {
            "pending": 0,
            "in_progress": 50,
            "completed": 100
        }

        if status not in valid_statuses:

            messages.error(
                request,
                "Invalid task status."
            )

            return redirect("teamlead_task")
        task.status = status
        # task.progress = {"pending": 0, "in_progress": 50, "completed": 100}.get(status, 0)
        task.progress = valid_statuses[status]
        task.save()
        messages.success(
            request,
            f'Task "{task.title}" updated to '
            f'"{task.get_status_display()}".'
        )

    return redirect('teamlead_task')


def delete_task_teamlead(request, task_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(
            request,
            "You must be logged in."
        )
        return redirect("login_view")

    user = User.objects.get(id=user_id)
    # ✅ Only allow deletion of tasks created by logged-in user
    task = get_object_or_404(Task, id=task_id, created_by=user)

    if request.method == "POST":
        task_title = task.title
        task.delete()
        messages.success(
            request,
            f'Task "{task_title}" deleted successfully.'
        )
    else:
        messages.error(
            request,
            "Invalid request."
        )


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