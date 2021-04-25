"""Dependencies for task."""

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.todos import get_todo_by_id_from_path
from app.db.repositories.tasks import TasksRepository
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import Depends, HTTPException, status


async def check_task_create_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    tasks_repo: TasksRepository = Depends(get_repository(TasksRepository)),
) -> None:
    """Check if user can create task."""
    if todo.owner == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Users are unable to create tasks for todo jobs they own"
        )
