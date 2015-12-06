# -*- coding: utf-8 -*-

from quixote.errors import PublishError


class CodeAPIError(PublishError):
    title = "Internal Server Error"
    status_code = 400
    problem_type = ""

    def __init__(self, detail=""):
        super(CodeAPIError, self).__init__()
        self.detail = detail

    def __dict__(self):
        error_data = {
            "type": self.problem_type,
            "title": self.title,
            "code": self.status_code,
            "message": self.detail,
            }
        return error_data

    def to_dict(self):
        return self.__dict__()


class NotJSONError(CodeAPIError):
    title = "Request body can not be parsed into JSON"
    status_code = 400
    problem_type = "not_json"


class UnauthorizedError(CodeAPIError):
    title = "Unauthorized Request"
    status_code = 401
    problem_type = "unauthorized"


class ForbiddenError(CodeAPIError):
    title = "You have NO permissions to perform this request"
    status_code = 403
    problem_type = "forbidden"


class NotTheAuthorError(ForbiddenError):
    problem_type = "not_the_author"

    def __init__(self, resource="item", action="edit"):
        detail = "Only the author of this %s can operate '%s' action" % (resource, action)
        super(NotTheAuthorError, self).__init__(detail)


class NoPushPermissionError(ForbiddenError):
    title = "You have no permission to push to this repository"
    problem_type = "no_push_permission"


class NotFoundError(CodeAPIError):
    title = "The resource you request does NOT exist"
    status_code = 404
    problem_type = "not_found"

    def __init__(self, resource_name="resource"):
        detail = "The %s your requested can not be found, it might have been removed" % resource_name
        super(NotFoundError, self).__init__(detail)


class MethodNotAllowedError(CodeAPIError):
    title = "The request method is not allowed"
    status_code = 405
    problem_type = "method_not_allowed"


class NotAcceptableError(CodeAPIError):
    title = "The request is not acceptable"
    status_code = 406
    problem_type = "not_accetable"


class UnprocessableEntityError(CodeAPIError):
    title = "Validation Failed"
    status_code = 422
    problem_type = "validation_failed"


class InvalidFieldError(UnprocessableEntityError):
    title = "The request's query data is invalid"

    def __init__(self, field_name, format_desc="a right one"):
        detail = "The field %s is invalid, you need supply %s." % (field_name, format_desc)
        super(InvalidFieldError, self).__init__(detail)


class MissingFieldError(UnprocessableEntityError):
    title = "Missing field"

    def __init__(self, field):
        if isinstance(field, basestring):
            detail = "This field is required: %s" % field
        elif isinstance(field, list):
            detail = "These fields are required: %s" % ", ".join(field)
        super(MissingFieldError, self).__init__(detail)

