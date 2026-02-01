import graphene

__all__ = ["FieldError", "make_error"]


class FieldError(graphene.ObjectType):
    field = graphene.String()
    messages = graphene.List(graphene.String, required=True)
    code = graphene.String(required=True)


def make_error(field: str | None, message: str, code: str) -> FieldError:
    return FieldError(field=field, messages=[message], code=code)
