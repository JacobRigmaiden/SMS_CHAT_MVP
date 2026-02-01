import graphene

from apps.groups.mutations import GroupMutation
from apps.groups.schema import GroupQuery
from apps.messages.mutations import MessageMutation
from apps.users.mutations import UserMutation
from apps.users.schema import UserQuery


class Query(UserQuery, GroupQuery, graphene.ObjectType):
    pass


class Mutation(UserMutation, GroupMutation, MessageMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
