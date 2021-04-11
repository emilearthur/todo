from typing import Optional
from pydantic import EmailStr
from fastapi import HTTPException, status

from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository

from app.models.user import UserCreate, UserInDB, UserPublic
from app.models.profile import ProfileCreate

from app.services import auth_service

from databases import Database


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


class UsersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service
        self.profiles_repo = ProfilesRepository(db)

    async def populate_user(self, *, user: UserInDB) -> UserInDB:
        return UserPublic(**user.dict(), profile=await self.profiles_repo.get_profile_by_user_id(user_id=user.id))

    async def get_user_by_email(self, *, email: EmailStr, populate: bool = True) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_EMAIL_QUERY, values={"email": email})
        if user_record:
            user = UserInDB(**user_record)
            if populate:
                return await self.populate_user(user=user)
            return user

    async def get_user_by_username(self, *, username: str, populate: bool = True) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_USERNAME_QUERY, values={"username": username})
        if user_record:
            user = UserInDB(**user_record)
            if populate:
                return await self.populate_user(user=user)
            return user

    async def register_new_user(self, *, new_user: UserCreate) -> UserInDB:
        if await self.get_user_by_email(email=new_user.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"{new_user.email} is already taken. Register with a new email")
        if await self.get_user_by_username(username=new_user.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"{new_user.username} is already taken. Register with a new email")
        user_pwd_update = self.auth_service.create_salt_and_hashed_password(plaintext_pwd=new_user.password)
        new_user_params = new_user.copy(update=user_pwd_update.dict())
        created_user = await self.db.fetch_one(query=REGISTER_NEW_USER_QUERY, values=new_user_params.dict())

        # create profile for new user
        await self.profiles_repo.create_profile_for_user(profile_create=ProfileCreate(user_id=created_user["id"]))
        return await self.populate_user(user=UserInDB(**created_user))

    async def authenticate_user(self, *, email: EmailStr, password: str) -> Optional[UserInDB]:
        user = await self.get_user_by_email(email=email, populate=False)
        if not user:
            return None
        if not self.auth_service.verify_password(pwd=password, salt=user.salt, hashed_pwd=user.password):
            return None
        return user
