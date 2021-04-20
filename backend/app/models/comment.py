"""All functions to handle model of comments."""
from typing import Optional

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel

from pydantic import conint


class CommentBase(CoreModel):
    """All common charateristics of Comments."""

    body: Optional[str]


class CommentCreate(CommentBase):
    """Create comments."""

    body: str
    todo_id: conint(ge=1)


class CommentUpdate(CommentBase):
    """Update comments."""

    pass


class CommentInDB(IDModelMixin, DateTimeModelMixin, CommentBase):
    """Comment in DB."""

    todo_id: int
    comment_owner: conint(ge=1)


class CommentPublic(CommentInDB):
    """Comment to public."""

    pass
