"""Routes for todo assignments."""

from typing import List

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.tasks import check_task_create_permissions
from app.api.dependencies.todos import get_todo_by_id_from_path
from app.db.repositories.tasks import TasksRepository
from app.models.task import TaskCreate, TaskInDB, TaskPublic, TaskUpdate
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

router = APIRouter()


@router.post(
    "/set",
    response_model=TaskPublic,
    name="assigns:set-task",
    status_code=status.HTTP_201_CREATED,
)
async def set_task(task_create: TaskCreate = Body(..., embed=True)) -> TaskPublic:
    """Assign a task."""
    return None


@router.post(
    "/",
    response_model=TaskPublic,
    name="assigns:create-task",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_task_create_permissions)],
)
async def create_task(
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
    tasks_repo: TasksRepository = Depends(get_repository(TasksRepository)),
) -> TaskPublic:
    """Create an offer here."""
    return await tasks_repo.create_task_for_todo(new_task=TaskCreate(todo_id=todo.id, user_id=current_user.id))


@router.get("/{username}/", response_model=TaskPublic, name="assigns:get_task_from_user")
async def get_task_from_user(username: str = Path(..., min_length=3)) -> TaskPublic:
    """Get task from user."""
    return None


@router.put("/{username}/", response_model=TaskPublic, name="assigns:accept-task-from-user")
async def accept_task_from_user(username: str = Path(..., min_length=3)) -> TaskPublic:
    """Accept task from a user."""
    return None


@router.put("/", response_model=TaskPublic, name="assigns:cancel-task-from-user")
async def cancel_task_from_user() -> TaskPublic:
    """Cancel task from a user."""
    return None


@router.delete("/", response_model=int, name="assigns:rescind-task-from-user")
async def rescind_task_from_user() -> TaskPublic:
    """Cancel task from a user."""
    return None


@router.get("/", response_model=List[TaskPublic], name="assigns:list-tasks-for-todo")
async def list_tasks_for_todo() -> List[TaskPublic]:
    """List offers for task."""
    return None
