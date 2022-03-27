from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from tortoise.exceptions import IntegrityError

from main import app


class BadRequest(HTTPException):
    def __init__(self, message: str = 'Bad Request'):
        super().__init__(400, message)


class ValidationError(BadRequest):
    def __init__(self, message: str = 'Validation Error'):
        super().__init__(message)


class Unauthorized(HTTPException):
    def __init__(self, message: str = 'Unauthorized'):
        super().__init__(401, message)


class Forbidden(HTTPException):
    def __init__(self, message: str = 'Forbidden'):
        super().__init__(403, message)


class NotFound(HTTPException):
    def __init__(self, message: str = 'Not Found'):
        super().__init__(404, message)


class ServerError(HTTPException):
    def __init__(self, message: str = 'Internal Server Error'):
        super().__init__(500, message)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exception: IntegrityError):
    raise BadRequest(str(exception))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exception: RequestValidationError):
    message = ''
    errors = exception.errors()
    for error in errors:
        message += f'{".".join(error["loc"])} {error["msg"]}\n'
    return JSONResponse(
        content={'message': message.rstrip(), 'detail': errors},
        status_code=400
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exception: StarletteHTTPException):
    return JSONResponse(
        status_code=exception.status_code,
        content={'message': exception.detail},
    )
