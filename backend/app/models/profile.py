"""All functions to handle models of profile."""

from typing import Optional
from pydantic import EmailStr, HttpUrl

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class ProfileBase(CoreModel):
    """All common characteristics of profile."""

    firstname: Optional[str]
    lastname: Optional[str]
    middlename: Optional[str]
    phone_number: Optional[str]
    bio: Optional[str]
    image: Optional[HttpUrl]


class ProfileCreate(ProfileBase):
    """Create profile."""

    user_id: int


class ProfileUpdate(ProfileBase):
    """Update profile."""

    pass


class ProfileInDB(IDModelMixin, DateTimeModelMixin, ProfileBase):
    """Profile coming from DB."""

    user_id: int
    username: Optional[str]
    email: Optional[EmailStr]


class ProfilePublic(ProfileInDB):
    """Profile to public."""

    pass
