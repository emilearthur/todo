"""All functions to handle models of user."""

from typing import Optional

from app.models.core import CoreModel, DateTimeModelMixin, IDModelMixin
from app.models.profile import ProfilePublic
from app.models.token import AccessToken
from pydantic import EmailStr, constr

regex = "^[a-zA-Z0-9_-]+$"


class UserBase(CoreModel):
    """All common characteristics of user."""

    email: Optional[EmailStr]
    username: Optional[str]
    email_verified: bool = False
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(CoreModel):
    """Email, username and password for registering new user."""

    email: EmailStr
    password: constr(min_length=7, max_length=80)
    username: constr(min_length=3, regex=regex)


class UserUpdate(CoreModel):
    """Users are allowed to update their email and username."""

    email: Optional[EmailStr]
    username: Optional[constr(min_length=3, regex=regex)]
    password: Optional[constr(min_length=7, max_length=80)]


class UserUpdateInDB(UserUpdate, IDModelMixin):
    """Users Update details In DB."""

    salt: str
    email_verified: bool


class UserPasswordUpdate(CoreModel):
    """Generated pasword and salt."""

    password: constr(min_length=7, max_length=100)
    salt: str


class UserPasswordChange(CoreModel):
    """User can change their password."""

    password: constr(min_length=7, max_length=100)


class UserInDB(IDModelMixin, DateTimeModelMixin, UserBase):
    """User coming from DB."""

    password: constr(min_length=7, max_length=100)
    salt: str


class UserPublic(IDModelMixin, DateTimeModelMixin, UserBase):
    """User to public."""

    access_token: Optional[AccessToken]
    profile: Optional[ProfilePublic]


class UserEmailVerifcationUpdate(CoreModel):
    """Update user email verification."""

    email_verified: bool = True
