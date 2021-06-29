"""All functions to handle models of todos."""

from datetime import date
from enum import Enum
from typing import Optional, Union

from app.models.core import CoreModel, DateTimeModelMixin, IDModelMixin
from app.models.user import UserPublic

#  from app.models.comment import CommentPublic


class PriorityType(str, Enum):
    """Types of priority types."""

    critical = "critical"
    high = "high"
    standard = "standard"
    normal = "normal"


class TodoBase(CoreModel):
    """All common characteristics of todo."""

    name: Optional[str]
    notes: Optional[str]
    priority: Optional[PriorityType] = "critical"
    duedate: Optional[date]  # consider design maybe you might change it.
    as_task: Optional[bool] = False


class TodoCreate(TodoBase):
    """Create todos."""

    name: str
    duedate: date  # consider design maybe you might change it.


class TodoUpdate(TodoBase):
    """Update todos."""

    priority: Optional[PriorityType]


# Done: Find way to add created at the both the TodoInDB and TODO in public
# this is help users see the time they created todo. Notes created date should not change.
class TodoInDB(IDModelMixin, DateTimeModelMixin, TodoBase):
    """Todo coming from DB."""

    name: str
    duedate: date
    priority: PriorityType
    owner: Union[int, UserPublic]


class TodoPublic(TodoInDB):
    """Todo to public."""

    owner: Union[int, UserPublic]
