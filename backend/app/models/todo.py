"""All functions to handle models of todos."""

from typing import Optional, Union
from enum import Enum
from datetime import date

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin
from app.models.user import UserPublic


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
