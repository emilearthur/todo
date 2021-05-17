"""Model for assigning task."""

from enum import Enum
from typing import Optional

from app.models.core import CoreModel, DateTimeModelMixin
from app.models.todo import TodoPublic
from app.models.user import UserPublic


class TaskStatus(str, Enum):
    """Status of an assigned task."""

    accepted = "accepted"
    rejected = "rejected"
    pending = "pending"
    cancelled = "cancelled"
    completed = "completed"


class TaskBase(CoreModel):
    """Task base class."""

    user_id: Optional[int]
    todo_id: Optional[int]
    status: Optional[TaskStatus] = TaskStatus.pending


class TaskCreate(TaskBase):
    """Create task for todo."""

    user_id: int
    todo_id: int


class TaskUpdate(CoreModel):
    """Update status of an assigned task."""

    status: TaskStatus


class TaskInDB(DateTimeModelMixin, TaskBase):
    """Task of a todo in DB."""

    user_id: int
    todo_id: int


class TaskPublic(TaskInDB):
    """Task to public."""

    user: Optional[UserPublic]
    todo: Optional[TodoPublic]
