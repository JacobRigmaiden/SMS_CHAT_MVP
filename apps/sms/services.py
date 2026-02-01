from django.conf import settings
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from core.exceptions import ExternalServiceError

__all__ = ["SMSService"]


class SMSService:
    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        self.account_sid = account_sid or getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.from_number = from_number or getattr(settings, "TWILIO_PHONE_NUMBER", "")
        self._client = None
        self._validator = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client

    @property
    def validator(self) -> RequestValidator:
        if self._validator is None:
            self._validator = RequestValidator(self.auth_token)
        return self._validator

    def send_sms(self, to: str, body: str) -> str:
        try:
            message = self.client.messages.create(body=body, from_=self.from_number, to=to)
            return message.sid
        except TwilioRestException as e:
            raise ExternalServiceError(f"Failed to send SMS: {e}") from e

    def send_bulk(self, recipients: list[str], body: str) -> dict[str, str]:
        results = {}
        for phone in recipients:
            try:
                results[phone] = self.send_sms(phone, body)
            except ExternalServiceError:
                continue
        return results

    def validate_webhook_signature(self, url: str, params: dict, signature: str) -> bool:
        return self.validator.validate(url, params, signature)
