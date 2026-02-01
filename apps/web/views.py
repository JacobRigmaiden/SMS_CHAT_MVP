from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from apps.groups.models import Group, Membership
from apps.groups.services import GroupService, MembershipService
from apps.messages.services import MessageService
from apps.users.services import UserService
from apps.users.verification import get_verification_service
from core.exceptions import AuthError, ConflictError, DomainError, ValidationError


def get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return UserService.get_user_by_id(user_id)
    except DomainError:
        return None


def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_current_user(request)
        if not user:
            messages.error(request, "Please login to continue.")
            return redirect("web:login")
        request.user_obj = user
        return view_func(request, *args, **kwargs)
    return wrapper


def register_view(request):
    if get_current_user(request):
        return redirect("web:dashboard")

    context = {"user": None}

    if request.method == "POST":
        phone_number = request.POST.get("phone_number", "").strip()
        name = request.POST.get("name", "").strip()
        password = request.POST.get("password", "")
        verification_code = request.POST.get("verification_code", "").strip()

        context["phone_number"] = phone_number
        context["name"] = name

        try:
            normalized_phone = UserService.validate_phone_number(phone_number)

            if not get_verification_service().check_verification_code(normalized_phone, verification_code):
                context["error"] = "Invalid verification code. For demo, use any 6-digit code."
                return render(request, "web/register.html", context)

            user = UserService.create_user(phone_number=normalized_phone, name=name, password=password)
            user.is_verified = True
            user.save(update_fields=["is_verified"])

            request.session["user_id"] = str(user.id)
            messages.success(request, f"Welcome, {user.name}!")
            return redirect("web:dashboard")

        except ValidationError as e:
            context["error"] = str(e)
        except ConflictError:
            context["error"] = "This phone number is already registered."
        except DomainError as e:
            context["error"] = str(e)

    return render(request, "web/register.html", context)


def login_view(request):
    if get_current_user(request):
        return redirect("web:dashboard")

    context = {"user": None}

    if request.method == "POST":
        phone_number = request.POST.get("phone_number", "").strip()
        password = request.POST.get("password", "")
        context["phone_number"] = phone_number

        try:
            user = UserService.authenticate(phone_number, password)
            request.session["user_id"] = str(user.id)
            messages.success(request, f"Welcome back, {user.name}!")
            return redirect("web:dashboard")
        except AuthError:
            context["error"] = "Invalid phone number or password."

    return render(request, "web/login.html", context)


def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect("web:login")


@login_required
def dashboard_view(request):
    user = request.user_obj
    search_query = request.GET.get("q", "").strip()

    my_group_ids = Membership.objects.filter(user=user, is_active=True).values_list("group_id", flat=True)

    my_groups = (
        Group.objects
        .filter(id__in=my_group_ids)
        .annotate(_member_count=Count("memberships", filter=Q(memberships__is_active=True)))
        .order_by("-created_at")
    )

    available_qs = Group.objects.exclude(id__in=my_group_ids)
    if search_query:
        available_qs = available_qs.filter(name__icontains=search_query)

    available_groups = (
        available_qs
        .annotate(_member_count=Count("memberships", filter=Q(memberships__is_active=True)))
        .order_by("-created_at")[:20]
    )

    return render(request, "web/dashboard.html", {
        "user": user,
        "my_groups": my_groups,
        "available_groups": available_groups,
        "search_query": search_query,
    })


@login_required
def create_group_view(request):
    try:
        group = GroupService.create_group(name=request.POST.get("name", ""), creator=request.user_obj)
        messages.success(request, f'Group "{group.name}" created!')
    except DomainError as e:
        messages.error(request, str(e))
    return redirect("web:dashboard")


@login_required
def join_group_view(request, group_id):
    try:
        group = GroupService.get_group_by_id(str(group_id))
        MembershipService.join_group(request.user_obj, group)
        messages.success(request, f'You joined "{group.name}"!')
    except DomainError as e:
        messages.error(request, str(e))
    return redirect("web:dashboard")


@login_required
def leave_group_view(request, group_id):
    try:
        group = GroupService.get_group_by_id(str(group_id))
        MembershipService.leave_group(request.user_obj, group)
        messages.success(request, f'You left "{group.name}".')
    except DomainError as e:
        messages.error(request, str(e))
    return redirect("web:dashboard")


@login_required
def group_detail_view(request, group_id):
    user = request.user_obj

    try:
        group = GroupService.get_group_by_id(str(group_id))
    except DomainError:
        messages.error(request, "Group not found.")
        return redirect("web:dashboard")

    if not group.is_member(user):
        messages.error(request, "You must be a member to view this group.")
        return redirect("web:dashboard")

    messages_list = list(reversed(MessageService.get_group_messages(group, limit=50)))
    members = list(group.get_active_members())
    my_groups_count = Membership.objects.filter(user=user, is_active=True).count()

    return render(request, "web/group_detail.html", {
        "user": user,
        "group": group,
        "messages_list": messages_list,
        "members": members,
        "my_groups_count": my_groups_count,
        "twilio_number": getattr(settings, "TWILIO_PHONE_NUMBER", "N/A"),
    })


@login_required
def send_message_view(request, group_id):
    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, "Message cannot be empty.")
        return redirect("web:group_detail", group_id=group_id)

    try:
        group = GroupService.get_group_by_id(str(group_id))
        MessageService.send_message(sender=request.user_obj, group=group, content=content)
    except DomainError as e:
        messages.error(request, str(e))

    return redirect("web:group_detail", group_id=group_id)
