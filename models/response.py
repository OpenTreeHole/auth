class MessageResponse:
    message: str


class TokensResponse:
    access: str
    refresh: str


class EmailVerifyResponse(MessageResponse):
    scope: str


class APIKeyVerifyResponse(MessageResponse):
    code: str
    scope: str
