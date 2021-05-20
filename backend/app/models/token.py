"""Model for token data."""

from datetime import datetime, timedelta

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_AUDIENCE
from app.models.core import CoreModel
from pydantic import EmailStr


class JWTMeta(CoreModel):
    """Model for JWT MetaData."""

    iss: str = "occupy-todo.io"
    aud: str = JWT_AUDIENCE
    iat: float = datetime.timestamp(datetime.utcnow())
    exp: float = datetime.timestamp(datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


class JWTCreds(CoreModel):
    """Identify users model."""

    sub: EmailStr
    username: str


class JWTPayload(JWTMeta, JWTCreds):
    """Model for JWT Payload."""

    pass


class AccessToken(CoreModel):
    """Model for Accesstoken."""

    access_token: str
    token_type: str
