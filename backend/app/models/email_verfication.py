"""All functions to handle models of Email verifcation."""

from pydantic import EmailStr

from app.models.core import CoreModel, DateTimeModelMixin


class EmailSchema(CoreModel):
    """Email schema to send email."""

    email: EmailStr


class EmailVerficationBase(CoreModel):
    """All common x'tics of email verification."""

    generated_code: str


class EmailVerficationCreate(EmailVerficationBase):
    """Create email verification."""

    user_id: int


class EmailVerificationUpdate(EmailVerficationBase):
    """Update generated_code once it expires."""

    pass


class EmailVerficationInDB(DateTimeModelMixin, EmailVerficationBase):
    """EmailVerifcation from DB."""

    user_id: int
