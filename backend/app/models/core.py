"""Core data that exist in all Models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


class CoreModel(BaseModel):
    """Any common logic to be shared by all models."""

    pass


class IDModelMixin(BaseModel):
    """ID data."""

    id: int


class DateTimeModelMixin(BaseModel):
    """Datetime model datas."""

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @validator("created_at", "updated_at", pre=True)
    def default_datetime(cls, value: datetime) -> datetime:
        """Validate both created_at and update_at data."""
        return value or datetime.datetime.now()
