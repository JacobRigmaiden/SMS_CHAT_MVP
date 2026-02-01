import graphene

from apps.groups.services import GroupService
from apps.users.schema import get_user_from_context
from core.exceptions import AuthError, DomainError, NotFound, ValidationError
from core.graphql import FieldError, make_error

from .schema import MessageType
from .services import MessageService


class SendMessageInput(graphene.InputObjectType):
    group_id = graphene.UUID(required=True)
    content = graphene.String(required=True)


class SendMessagePayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.Field(MessageType)
    errors = graphene.List(FieldError)


class SendMessage(graphene.Mutation):
    class Arguments:
        input = SendMessageInput(required=True)

    Output = SendMessagePayload

    @staticmethod
    def mutate(root, info, input):
        user = get_user_from_context(info)
        if not user:
            return SendMessagePayload(success=False, errors=[make_error(None, "Authentication required", "AUTH_ERROR")])

        try:
            group = GroupService.get_group_by_id(str(input.group_id))
            message = MessageService.send_message(sender=user, group=group, content=input.content)
            return SendMessagePayload(success=True, message=message, errors=[])
        except NotFound as e:
            return SendMessagePayload(success=False, errors=[make_error("group_id", str(e), e.code)])
        except (AuthError, ValidationError) as e:
            return SendMessagePayload(success=False, errors=[make_error(None, str(e), e.code)])
        except DomainError as e:
            return SendMessagePayload(success=False, errors=[make_error(None, str(e), e.code)])


class MessageMutation(graphene.ObjectType):
    send_message = SendMessage.Field()
