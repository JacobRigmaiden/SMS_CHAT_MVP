"""
URL configuration for web UI.
"""
from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    # Auth
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("", views.dashboard_view, name="dashboard"),

    # Groups
    path("groups/create/", views.create_group_view, name="create_group"),
    path("groups/<uuid:group_id>/", views.group_detail_view, name="group_detail"),
    path("groups/<uuid:group_id>/join/", views.join_group_view, name="join_group"),
    path("groups/<uuid:group_id>/leave/", views.leave_group_view, name="leave_group"),
    path("groups/<uuid:group_id>/send/", views.send_message_view, name="send_message"),
]
