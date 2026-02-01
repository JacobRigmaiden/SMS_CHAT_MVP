from datetime import datetime, timedelta, timezone

import jwt
import phonenumbers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from core.exceptions import AuthError, ConflictError, NotFound, ValidationError

User = get_user_model()

__all__ = ["UserService"]


class UserService:
    JWT_ISSUER = "sms-chat"
    JWT_AUDIENCE = "sms-chat-api"

    @staticmethod
    def validate_phone_number(phone_number: str) -> str:
        if not phone_number:
            raise ValidationError("Phone number is required")

        region = getattr(settings, "PHONE_NUMBER_DEFAULT_REGION", "US")
        try:
            parsed = phonenumbers.parse(phone_number, region)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValidationError("Invalid phone number format")

    @staticmethod
    def create_user(phone_number: str, name: str, password: str) -> User:
        normalized_phone = UserService.validate_phone_number(phone_number)
        try:
            return User.objects.create_user(
                phone_number=normalized_phone,
                name=name.strip(),
                password=password,
            )
        except IntegrityError:
            raise ConflictError("Phone number already registered")

    @staticmethod
    def authenticate(phone_number: str, password: str) -> User:
        try:
            normalized = UserService.validate_phone_number(phone_number)
        except ValidationError:
            raise AuthError("Invalid credentials")

        try:
            user = User.objects.get(phone_number=normalized)
        except User.DoesNotExist:
            raise AuthError("Invalid credentials")

        if not user.is_active or not user.check_password(password):
            raise AuthError("Invalid credentials")

        return user

    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound("User not found")

    @staticmethod
    def get_user_by_phone(phone_number: str) -> User | None:
        try:
            normalized = UserService.validate_phone_number(phone_number)
            return User.objects.get(phone_number=normalized)
        except (ValidationError, User.DoesNotExist):
            return None

    @staticmethod
    def generate_jwt_token(user: User) -> str:
        secret = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
        hours = getattr(settings, "JWT_EXPIRATION_HOURS", 24)

        payload = {
            "sub": str(user.id),
            "iss": UserService.JWT_ISSUER,
            "aud": UserService.JWT_AUDIENCE,
            "exp": datetime.now(timezone.utc) + timedelta(hours=hours),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def verify_jwt_token(token: str) -> User | None:
        secret = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=UserService.JWT_AUDIENCE,
                issuer=UserService.JWT_ISSUER,
            )
            return User.objects.get(id=payload["sub"], is_active=True)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return None
