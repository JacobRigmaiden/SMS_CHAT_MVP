from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.messages.services import MessageService
from apps.users.services import UserService

from .routing import SMSRouter
from .services import SMSService


def make_twiml_response(message: str = "") -> HttpResponse:
    msg_xml = f"<Message>{escape(message)}</Message>" if message else ""
    return HttpResponse(
        f'<?xml version="1.0" encoding="UTF-8"?><Response>{msg_xml}</Response>',
        content_type="application/xml"
    )


@csrf_exempt
@require_POST
def twilio_webhook(request) -> HttpResponse:
    signature = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")
    if not signature:
        return make_twiml_response()

    if not SMSService().validate_webhook_signature(
        request.build_absolute_uri(),
        request.POST.dict(),
        signature
    ):
        return make_twiml_response()

    from_number = request.POST.get("From", "")
    body = request.POST.get("Body", "")

    response = _process_inbound_sms(from_number, body)
    return make_twiml_response(response)


def _process_inbound_sms(from_number: str, body: str) -> str:
    user = UserService.get_user_by_phone(from_number)
    if not user:
        return "This phone number is not registered. Sign up at the website to join."

    group, content = SMSRouter.get_target_group(user, body)

    if not group:
        if not user.memberships.filter(is_active=True).exists():
            return "You're not in any groups. Join a group at the website to start chatting."
        return SMSRouter.get_clarification_message(user)

    if not content or not content.strip():
        return "Message cannot be empty."

    try:
        MessageService.send_message(sender=user, group=group, content=content)
        return ""
    except Exception:
        return "Sorry, there was an error sending your message. Please try again."
