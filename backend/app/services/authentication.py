import bcrypt
import jwt

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from pydantic import ValidationError
from fastapi import HTTPException, status

from app.models.user import UserPasswordUpdate, UserInDB
from app.models.token import JWTMeta, JWTCreds, JWTPayload

from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AUthException(BaseException):
    """ Custom auth excpetion """
    pass


class AuthService:
    def create_salt_and_hashed_password(self, *, plaintext_pwd: str) -> UserPasswordUpdate:
        salt = self.generate_salt()
        hashed_password = self.hash_password(pwd=plaintext_pwd, salt=salt)
        return UserPasswordUpdate(salt=salt, password=hashed_password)

    def generate_salt(self) -> str:
        return bcrypt.gensalt().decode()

    def hash_password(self, *, pwd: str, salt: str) -> str:
        return pwd_context.hash(pwd + salt)

    def verify_password(self, *, pwd: str, salt: str, hashed_pwd: str) -> bool:
        return pwd_context.verify(pwd + salt, hashed_pwd)

    def create_access_token_for_user(self, *, user: UserInDB,
                                     secret_key: str = str(SECRET_KEY),
                                     audience: str = JWT_AUDIENCE,
                                     expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES,) -> str:
        if not user or not isinstance(user, UserInDB):
            return None

        jwt_meta = JWTMeta(aud=audience,
                           iat=datetime.timestamp(datetime.utcnow()),
                           exp=datetime.timestamp(datetime.utcnow() + timedelta(minutes=expires_in)),)
        jwt_creds = JWTCreds(sub=user.email, username=user.username)
        token_payload = JWTPayload(**jwt_meta.dict(), **jwt_creds.dict(),)
        access_token = jwt.encode(token_payload.dict(), secret_key, algorithm=JWT_ALGORITHM)
        return access_token

    def get_username_from_token(self, *, token: str, secret_key: str) -> Optional[str]:
        try:
            decoded_token = jwt.decode(token, str(secret_key), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
            payload = JWTPayload(**decoded_token)
        except (jwt.PyJWTError, ValidationError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate token credentials.",
                                headers={"WWW-Authenticate": "Bearer"})
        return payload.username
