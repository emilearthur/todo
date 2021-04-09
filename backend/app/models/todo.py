from typing import Optional
from enum import Enum
from datetime import date  # , datetime

from app.models.core import IDModelMixin, CoreModel


class PriorityType(str, Enum):
    critical = "critical"
    high = "high"
    standard = "standard"
    normal = "normal"


class TodoBase(CoreModel):
    """ All common characteristics of todo """
    name: Optional[str]
    notes: Optional[str]
    priority: Optional[PriorityType] = "critical"
    duedate: Optional[date]  # consider design maybe you might change it.


class TodoCreate(TodoBase):
    name: str
    duedate: date  # consider design maybe you might change it.


class TodoUpdate(TodoBase):
    priority: Optional[PriorityType]


# TODO: Find way to add created at the both the TodoInDB and TODO in public
# this is help users see the time they created todo. Notes created date should not change.
class TodoInDB(IDModelMixin, TodoBase):
    name: str
    duedate: date
    priority: PriorityType
    #  created_at: Optional[datetime]


class TodoPublic(IDModelMixin, TodoBase):
    #  created_at: Optional[datetime]
    pass
