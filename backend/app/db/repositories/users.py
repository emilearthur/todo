"""DB repo for profile."""

import logging
import random
import string
from datetime import timedelta
from typing import Optional

from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.models.profile import ProfileCreate
from app.models.user import UserCreate, UserInDB, UserPasswordUpdate, UserPublic, UserUpdate
from app.services import auth_service, email_service
from databases import Database
from fastapi import HTTPException, status
from pydantic import EmailStr
from redis.client import Redis

logger = logging.getLogger(__name__)


GET_USER_BY_EMAIL_QUERY = """
    SELECT id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE email = :email;
"""

GET_USER_BY_USERNAME_QUERY = """
    SELECT id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE username = :username;
"""

REGISTER_NEW_USER_QUERY = """
    INSERT INTO users (username, email, password, salt)
    VALUES (:username, :email, :password, :salt)
    RETURNING id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at
"""

UPDATE_EMAIL_STATUS_QUERY = """
    UPDATE users
    SET email_verified  = :email_verified
    WHERE id = :id
    RETURNING id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at;
"""

UPDATE_USER_DETAILS_QUERY = """
    UPDATE users
    SET email = :email,
        email_verified  = :email_verified,
        username = :username
    WHERE id = :id
    RETURNING id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at;
"""

GET_USER_BY_ID_QUERY = """
    SELECT id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE id = :id;
"""

UPDATE_USER_PASSWORD_QUERY = """
    UPDATE users
    SET password  = :password,
        salt      = :salt
    WHERE id = :id
    RETURNING id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at;
"""


class UsersRepository(BaseRepository):
    """All db actions associated with the Users resources."""

    def __init__(self, db: Database, r_db: Redis) -> None:
        """Initialize db, auth_path and profiles_repo."""
        super().__init__(db, r_db)
        self.auth_service = auth_service
        self.email_service = email_service
        self.profiles_repo = ProfilesRepository(db, r_db)

    async def populate_user(self, *, user: UserInDB) -> UserInDB:
        """Get profile of user and add to user profile."""
        return UserPublic(**user.dict(), profile=await self.profiles_repo.get_profile_by_user_id(user_id=user.id))

    async def get_user_by_email(self, *, email: EmailStr, populate: bool = True) -> UserInDB:
        """Get user by email."""
        user_record = await self.db.fetch_one(query=GET_USER_BY_EMAIL_QUERY, values={"email": email})
        if user_record:
            user = UserInDB(**user_record)
            if populate:
                return await self.populate_user(user=user)
            return user

    async def get_user_by_username(self, *, username: str, populate: bool = True) -> UserInDB:
        """Get user by username."""
        user_record = await self.db.fetch_one(query=GET_USER_BY_USERNAME_QUERY, values={"username": username})
        if user_record:
            user = UserInDB(**user_record)
            if populate:
                return await self.populate_user(user=user)
            return user

    async def register_new_user(self, *, new_user: UserCreate) -> UserInDB:
        """Register new user."""
        if await self.get_user_by_email(email=new_user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{new_user.email} is already taken. Register with a new email",
            )
        if await self.get_user_by_username(username=new_user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{new_user.username} is already taken. Register with a new email",
            )
        user_pwd_update = self.auth_service.create_salt_and_hashed_password(plaintext_pwd=new_user.password)
        new_user_params = new_user.copy(update=user_pwd_update.dict())
        created_user = await self.db.fetch_one(query=REGISTER_NEW_USER_QUERY, values=new_user_params.dict())

        # create profile for new user
        await self.profiles_repo.create_profile_for_user(profile_create=ProfileCreate(user_id=created_user["id"]))
        return await self.populate_user(user=UserInDB(**created_user))

    async def authenticate_user(self, *, email: EmailStr, password: str) -> Optional[UserInDB]:
        """Authenticate user."""
        user = await self.get_user_by_email(email=email, populate=False)
        if not user:
            return None
        if not self.auth_service.verify_password(pwd=password, salt=user.salt, hashed_pwd=user.password):
            return None
        return user

    async def update_user_email_verification(self, *, requesting_user: UserInDB) -> UserInDB:
        """Update user details."""
        update_params = await self.db.fetch_one(
            query=UPDATE_EMAIL_STATUS_QUERY, values={"email_verified": True, "id": requesting_user.id}
        )
        return UserInDB(**update_params)

    def generate_otp(self, *, size=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase) -> str:
        """Generate opt for user verification."""
        return "".join(random.choice(chars) for _ in range(size))

    async def send_verification_email(self, *, requesting_user: UserInDB) -> Optional[str]:
        """Send email to user."""
        code_record = await self.r_db.get(requesting_user.email)
        if code_record is None:
            generated_code = generated_code = self.generate_otp()
            await self.r_db.setex(requesting_user.email, timedelta(seconds=300).seconds, value=generated_code)
            try:
                await self.email_service.send_email_gmail(
                    emails=requesting_user.email.split(),
                    username=requesting_user.username,
                    generated_code=generated_code,
                )
            except Exception as e:
                logger.warn("STMP Error")
                logger.warn(e)
                logger.warn("Email Failed")
        return requesting_user.email

    async def verify_email(self, *, requesting_user: UserInDB, verification_code: str) -> Optional[UserInDB]:
        """Verification of user."""
        code_record = await self.r_db.get(requesting_user.email)
        if not code_record:
            return None
        if not code_record.decode("utf-8") == verification_code:
            return None
        user = await self.update_user_email_verification(requesting_user=requesting_user)
        return user

    async def get_user_by_id(self, *, user_id: int, populate: bool = True) -> UserPublic:
        """Get user details by id."""
        user_record = await self.db.fetch_one(query=GET_USER_BY_ID_QUERY, values={"id": user_id})
        if user_record:
            user = UserInDB(**user_record)
            if populate:
                return await self.populate_user(user=user)
            return user

    async def update_user_details(self, *, user_update: UserUpdate, requesting_user: UserInDB) -> UserInDB:
        """Update user details."""
        if await self.get_user_by_email(email=user_update.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{user_update.email} is already taken. Register with a new email",
            )
        if await self.get_user_by_username(username=user_update.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{user_update.username} is already taken. Register with a new email",
            )
        user = await self.get_user_by_email(email=requesting_user.email, populate=False)
        user_details = UserUpdate(**user.dict())
        user_updated_params = user_details.copy(update=user_update.dict(exclude_unset=True))
        if user_update.email is not None:
            email_verified = False
        else:
            email_verified = user.email_verified

        updated_user = await self.db.fetch_one(
            query=UPDATE_USER_DETAILS_QUERY,
            values={
                "email": user_updated_params.email,
                "username": user_updated_params.username,
                "email_verified": email_verified,
                "id": requesting_user.id,
            },
        )
        return UserInDB(**updated_user)

    async def update_password(self, *, password_update: Optional[str], requesting_user: UserInDB) -> UserInDB:
        """Update User Password."""
        user = await self.get_user_by_email(email=requesting_user.email, populate=False)
        if password_update is not None:
            user_pwd_update = self.auth_service.create_salt_and_hashed_password(plaintext_pwd=password_update)
            user.password = user_pwd_update.password
            user.salt = user_pwd_update.salt
        updated_user = await self.db.fetch_one(
            query=UPDATE_USER_PASSWORD_QUERY,
            values={"password": user.password, "salt": user.salt, "id": requesting_user.id},
        )
        return UserInDB(**updated_user)
