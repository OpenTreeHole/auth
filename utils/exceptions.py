from sanic.exceptions import SanicException


class BadRequest(SanicException):
    status_code = 400
    message = 'Bad Request'
    quiet = True


class ValidationError(BadRequest):
    message = 'Validation Error'
