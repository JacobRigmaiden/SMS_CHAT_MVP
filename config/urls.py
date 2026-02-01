"""
URL configuration for sms_chat project.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from apps.sms.views import twilio_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path("webhooks/twilio/inbound/", twilio_webhook, name="twilio_webhook"),
    # Web UI
    path("", include("apps.web.urls")),
]
