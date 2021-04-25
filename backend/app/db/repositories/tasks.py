from typing import List

from app.db.repositories.base import BaseRepository
from app.models.task import TaskCreate, TaskInDB, TaskUpdate
from asyncpg.exceptions import UniqueViolationError
from fastapi import HTTPException, status

CREATE_TASK_FOR_TODO_QUERY = """
    INSERT INTO user_assigns_or_offers_todos (todo_id, user_id, status)
    VALUES (:todo_id, :user_id, :status)
    RETURNING todo_id, user_id, status, created_at, updated_at;
"""


class TasksRepository(BaseRepository):
    """class for tasks."""

    async def create_task_for_todo(self, *, new_task: TaskCreate) -> TaskInDB:
        """Create a task."""
        try:
            created_task = await self.db.fetch_one(
                query=CREATE_TASK_FOR_TODO_QUERY, values={**new_task.dict(), "status": "pending"}
            )
            return TaskInDB(**created_task)
        except UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users aren't allowed to create more than one task for a todo job",
            )
