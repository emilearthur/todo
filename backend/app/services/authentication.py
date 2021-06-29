"""Handling authentication tasks."""

from datetime import datetime, timedelta
from typing import Optional, Type

import bcrypt
import jwt
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_AUDIENCE, SECRET_KEY
from app.models.token import JWTCreds, JWTMeta, JWTPayload
from app.models.user import UserBase, UserPasswordUpdate
from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import ValidationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AUthException(BaseException):
    """Custom auth excpetion."""

    pass


class AuthService:
    """Authenticate class for all authentication."""

    def create_salt_and_hashed_password(self, *, plaintext_pwd: str) -> UserPasswordUpdate:
        """Create salt and hased password."""
        salt = self.generate_salt()
        hashed_password = self.hash_password(pwd=plaintext_pwd, salt=salt)
        return UserPasswordUpdate(salt=salt, password=hashed_password)

    def generate_salt(self) -> str:
        """Generate salt."""
        return bcrypt.gensalt().decode()

    def hash_password(self, *, pwd: str, salt: str) -> str:
        """Hash password."""
        return pwd_context.hash(pwd + salt)

    def verify_password(self, *, pwd: str, salt: str, hashed_pwd: str) -> bool:
        """Verify password."""
        return pwd_context.verify(pwd + salt, hashed_pwd)

    def create_access_token_for_user(
        self,
        *,
        user: Type[UserBase],
        secret_key: str = str(SECRET_KEY),
        audience: str = JWT_AUDIENCE,
        expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> str:
        """Create access token for user."""
        if not user or not isinstance(user, UserBase):
            return None

        jwt_meta = JWTMeta(
            aud=audience,
            iat=datetime.timestamp(datetime.utcnow()),
            exp=datetime.timestamp(datetime.utcnow() + timedelta(minutes=expires_in)),
        )
        jwt_creds = JWTCreds(sub=user.email, username=user.username)
        token_payload = JWTPayload(
            **jwt_meta.dict(),
            **jwt_creds.dict(),
        )
        access_token = jwt.encode(token_payload.dict(), secret_key, algorithm=JWT_ALGORITHM)
        return access_token

    def get_username_from_token(self, *, token: str, secret_key: str) -> Optional[str]:
        """Get username from token."""
        try:
            decoded_token = jwt.decode(token, str(secret_key), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
            payload = JWTPayload(**decoded_token)
        except (jwt.PyJWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload.username
