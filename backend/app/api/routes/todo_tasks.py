"""API router to get all todos are offered as task.
Anyone can view them."""

from typing import List

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.todos import TodosRepository
from app.models.todo import TodoPublic
from app.models.user import UserInDB
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/", response_model=List[TodoPublic], name="todo_task:list-all-tasks")
async def get_all_todo_tasks(
    current_user: UserInDB = Depends(get_current_active_user),
    todos_repo: TodosRepository = Depends(get_repository(TodosRepository)),
) -> List[TodoPublic]:
    """Get all todos offered as tasks."""
    return await todos_repo.list_all_todo_for_task(requesting_user=current_user)
