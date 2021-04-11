from typing import Optional
from pydantic import EmailStr, HttpUrl

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class ProfileBase(CoreModel):
    firstname: Optional[str]
    lastname: Optional[str]
    middlename: Optional[str]
    phone_number: Optional[str]
    bio: Optional[str]
    image: Optional[HttpUrl]


class ProfileCreate(ProfileBase):
    user_id: int


class ProfileUpdate(ProfileBase):
    pass


class ProfileInDB(IDModelMixin, DateTimeModelMixin, ProfileBase):
    user_id: int
    username: Optional[str]
    email: Optional[EmailStr]


class ProfilePublic(ProfileInDB):
    pass
