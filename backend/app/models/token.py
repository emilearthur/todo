from datetime import datetime, timedelta

from pydantic import EmailStr

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_AUDIENCE
from app.models.core import CoreModel


class JWTMeta(CoreModel):
    iss: str = "occupy-todo.io"
    aud: str = JWT_AUDIENCE
    iat: float = datetime.timestamp(datetime.utcnow())
    exp: float = datetime.timestamp(datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


class JWTCreds(CoreModel):
    """ Identify users """
    sub: EmailStr
    username: str


class JWTPayload(JWTMeta, JWTCreds):
    pass


class AccessToken(CoreModel):
    access_token: str
    token_type: str
