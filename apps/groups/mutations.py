import graphene

from apps.users.schema import get_user_from_context
from apps.users.services import UserService
from core.exceptions import (
    AuthError,
    ConflictError,
    DomainError,
    NotFound,
    ValidationError,
)
from core.graphql import FieldError, make_error

from .schema import GroupType, MembershipType
from .services import GroupService, MembershipService


def require_auth(info):
    return get_user_from_context(info)


class CreateGroupInput(graphene.InputObjectType):
    name = graphene.String(required=True)


class CreateGroupPayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    group = graphene.Field(GroupType)
    errors = graphene.List(FieldError)


class CreateGroup(graphene.Mutation):
    class Arguments:
        input = CreateGroupInput(required=True)

    Output = CreateGroupPayload

    @staticmethod
    def mutate(root, info, input):
        user = require_auth(info)
        if not user:
            return CreateGroupPayload(success=False, errors=[make_error(None, "Authentication required", "AUTH_ERROR")])

        try:
            group = GroupService.create_group(name=input.name, creator=user)
            return CreateGroupPayload(success=True, group=group, errors=[])
        except (ConflictError, ValidationError) as e:
            return CreateGroupPayload(success=False, errors=[make_error("name", str(e), e.code)])
        except DomainError as e:
            return CreateGroupPayload(success=False, errors=[make_error(None, str(e), e.code)])


class JoinGroupInput(graphene.InputObjectType):
    group_id = graphene.UUID(required=True)


class JoinGroupPayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    membership = graphene.Field(MembershipType)
    errors = graphene.List(FieldError)


class JoinGroup(graphene.Mutation):
    class Arguments:
        input = JoinGroupInput(required=True)

    Output = JoinGroupPayload

    @staticmethod
    def mutate(root, info, input):
        user = require_auth(info)
        if not user:
            return JoinGroupPayload(success=False, errors=[make_error(None, "Authentication required", "AUTH_ERROR")])

        try:
            group = GroupService.get_group_by_id(str(input.group_id))
            membership = MembershipService.join_group(user, group)
            return JoinGroupPayload(success=True, membership=membership, errors=[])
        except NotFound as e:
            return JoinGroupPayload(success=False, errors=[make_error("group_id", str(e), e.code)])
        except (ConflictError, ValidationError) as e:
            return JoinGroupPayload(success=False, errors=[make_error(None, str(e), e.code)])


class LeaveGroupInput(graphene.InputObjectType):
    group_id = graphene.UUID(required=True)


class LeaveGroupPayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    errors = graphene.List(FieldError)


class LeaveGroup(graphene.Mutation):
    class Arguments:
        input = LeaveGroupInput(required=True)

    Output = LeaveGroupPayload

    @staticmethod
    def mutate(root, info, input):
        user = require_auth(info)
        if not user:
            return LeaveGroupPayload(success=False, errors=[make_error(None, "Authentication required", "AUTH_ERROR")])

        try:
            group = GroupService.get_group_by_id(str(input.group_id))
            MembershipService.leave_group(user, group)
            return LeaveGroupPayload(success=True, errors=[])
        except NotFound as e:
            return LeaveGroupPayload(success=False, errors=[make_error("group_id", str(e), e.code)])


class TransferOwnershipInput(graphene.InputObjectType):
    group_id = graphene.UUID(required=True)
    new_owner_id = graphene.UUID(required=True)


class TransferOwnershipPayload(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    group = graphene.Field(GroupType)
    errors = graphene.List(FieldError)


class TransferOwnership(graphene.Mutation):
    class Arguments:
        input = TransferOwnershipInput(required=True)

    Output = TransferOwnershipPayload

    @staticmethod
    def mutate(root, info, input):
        user = require_auth(info)
        if not user:
            return TransferOwnershipPayload(success=False, errors=[make_error(None, "Authentication required", "AUTH_ERROR")])

        try:
            group = GroupService.get_group_by_id(str(input.group_id))
            new_owner = UserService.get_user_by_id(str(input.new_owner_id))
            updated_group = MembershipService.transfer_ownership(user, group, new_owner)
            return TransferOwnershipPayload(success=True, group=updated_group, errors=[])
        except NotFound as e:
            return TransferOwnershipPayload(success=False, errors=[make_error(None, str(e), e.code)])
        except AuthError as e:
            return TransferOwnershipPayload(success=False, errors=[make_error("group_id", str(e), e.code)])


class GroupMutation(graphene.ObjectType):
    create_group = CreateGroup.Field()
    join_group = JoinGroup.Field()
    leave_group = LeaveGroup.Field()
    transfer_ownership = TransferOwnership.Field()
