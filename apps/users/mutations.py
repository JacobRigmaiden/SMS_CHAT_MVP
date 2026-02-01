import graphene
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from core.exceptions import AuthError, ConflictError, DomainError, ValidationError
from core.graphql import FieldError, make_error

from .schema import UserType
from .services import UserService
from .verification import get_verification_service


class RequestVerificationInput(graphene.InputObjectType):
    phone_number = graphene.String(required=True)


class RequestVerificationPayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    verification_id = graphene.String()
    errors = graphene.List(FieldError)


class RequestVerification(graphene.Mutation):
    class Arguments:
        input = RequestVerificationInput(required=True)

    Output = RequestVerificationPayload

    @staticmethod
    def mutate(root, info, input):
        try:
            normalized_phone = UserService.validate_phone_number(input.phone_number)
            verification_id = get_verification_service().send_verification_code(normalized_phone)
            return RequestVerificationPayload(success=True, verification_id=verification_id, errors=[])
        except ValidationError as e:
            return RequestVerificationPayload(success=False, errors=[make_error("phone_number", str(e), e.code)])


class RegisterInput(graphene.InputObjectType):
    phone_number = graphene.String(required=True)
    name = graphene.String(required=True)
    password = graphene.String(required=True)
    verification_code = graphene.String(required=True)


class RegisterPayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    user = graphene.Field(UserType)
    token = graphene.String()
    errors = graphene.List(FieldError)


class Register(graphene.Mutation):
    class Arguments:
        input = RegisterInput(required=True)

    Output = RegisterPayload

    @staticmethod
    def mutate(root, info, input):
        errors = []

        name = input.name.strip() if input.name else ""
        if not name:
            errors.append(make_error("name", "Name is required", "REQUIRED"))

        if input.password:
            try:
                validate_password(input.password)
            except DjangoValidationError as e:
                for msg in e.messages:
                    errors.append(make_error("password", msg, "VALIDATION_ERROR"))
        else:
            errors.append(make_error("password", "Password is required", "REQUIRED"))

        try:
            normalized_phone = UserService.validate_phone_number(input.phone_number)
        except ValidationError as e:
            errors.append(make_error("phone_number", str(e), e.code))
            normalized_phone = None

        if normalized_phone:
            if not get_verification_service().check_verification_code(normalized_phone, input.verification_code):
                errors.append(make_error("verification_code", "Invalid verification code", "VALIDATION_ERROR"))

        if errors:
            return RegisterPayload(success=False, errors=errors)

        try:
            user = UserService.create_user(phone_number=normalized_phone, name=name, password=input.password)
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            token = UserService.generate_jwt_token(user)
            return RegisterPayload(success=True, user=user, token=token, errors=[])
        except ConflictError as e:
            return RegisterPayload(success=False, errors=[make_error("phone_number", str(e), e.code)])
        except DomainError as e:
            return RegisterPayload(success=False, errors=[make_error(None, str(e), e.code)])


class LoginInput(graphene.InputObjectType):
    phone_number = graphene.String(required=True)
    password = graphene.String(required=True)


class LoginPayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    user = graphene.Field(UserType)
    token = graphene.String()
    errors = graphene.List(FieldError)


class Login(graphene.Mutation):
    class Arguments:
        input = LoginInput(required=True)

    Output = LoginPayload

    @staticmethod
    def mutate(root, info, input):
        try:
            user = UserService.authenticate(input.phone_number, input.password)
            token = UserService.generate_jwt_token(user)
            return LoginPayload(success=True, user=user, token=token, errors=[])
        except AuthError as e:
            return LoginPayload(success=False, errors=[make_error(None, str(e), e.code)])


class UserMutation(graphene.ObjectType):
    request_verification = RequestVerification.Field()
    register = Register.Field()
    login = Login.Field()
