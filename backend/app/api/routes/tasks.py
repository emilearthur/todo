"""Routes for todo assignments."""

from typing import List

from fastapi import APIRouter, Body, Path, status

from app.models.task import TaskCreate, TaskInDB, TaskPublic, TaskUpdate

router = APIRouter()


@router.post(
    "/",
    response_model=TaskPublic,
    name="assigns:set-task-for-user",
    status_code=status.HTTP_201_CREATED,
)
async def set_task_for_user(task_create: TaskCreate = Body(..., embed=True)) -> TaskPublic:
    """Assign a task."""
    return None


@router.post(
    "/",
    response_model=TaskPublic,
    name="assigns:create-task",
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(task_create: TaskCreate = Body(..., embed=True)) -> TaskPublic:
    """Create an offer here."""
    return None


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
