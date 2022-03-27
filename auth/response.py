from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class TokensResponse(MessageResponse):
    access: str
    refresh: str


class EmailVerifyResponse(MessageResponse):
    scope: str


class APIKeyVerifyResponse(MessageResponse):
    code: str
    scope: str
