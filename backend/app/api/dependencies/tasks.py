"""Dependencies for task."""

from typing import List

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.todos import get_todo_by_id_from_path
from app.api.dependencies.users import get_user_by_username_from_path
from app.db.repositories.tasks import TasksRepository
from app.models.task import TaskInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import Depends, HTTPException, status


async def check_task_create_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    tasks_repo: TasksRepository = Depends(get_repository(TasksRepository)),
) -> None:
    """Permission for user can create task."""
    if todo.owner == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Users are unable to create tasks for todo jobs they own"
        )
    if await tasks_repo.get_offer_for_task_from_user(todo=todo, user=current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users aren't allowed create more than one offer for a cleaning job.",
        )


async def get_task_for_todo_from_user(
    *,
    user: UserInDB,
    todo: TodoInDB,
    tasks_repo: TasksRepository,
) -> TaskInDB:
    """Check and return task if it exists."""
    task = await tasks_repo.get_offer_for_task_from_user(todo=todo, user=user)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


async def get_offer_for_task_from_user_by_path(
    user: UserInDB = Depends(get_user_by_username_from_path),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    tasks_repo: TasksRepository = Depends(get_repository(TasksRepository)),
) -> TodoInDB:
    """Get a task from a todo."""
    return await get_task_for_todo_from_user(user=user, todo=todo, tasks_repo=tasks_repo)


async def list_offers_for_task_by_id_from_path(
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    tasks_repo: TasksRepository = Depends(get_repository(TasksRepository)),
) -> List[TaskInDB]:
    """List all offers for todo."""
    return await tasks_repo.list_offers_for_task(todo=todo)


async def check_offer_list_permissions(
    current_user: UserInDB = Depends(get_current_active_user), todo: TodoInDB = Depends(get_todo_by_id_from_path)
) -> None:
    """Permission for todo owner to view list of offers for thier tasks."""
    if todo.owner != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to access offers.")


async def check_task_get_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    task: TaskInDB = Depends(get_offer_for_task_from_user_by_path),
) -> None:
    """Perission to access task."""
    if todo.owner != current_user.id and task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to access task")


def check_task_acceptance_permission(
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    task: TaskInDB = Depends(get_offer_for_task_from_user_by_path),
    existing_offer: List[TaskInDB] = Depends(list_offers_for_task_by_id_from_path),
) -> None:
    """Check if tasks can be accepted."""
    if todo.owner != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the onwer of the todo may accept offers."
        )
    if task.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Can only accept tasks that are currently pending."
        )
    if "accepted" in [task.status for task in existing_offer]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The todo already has an accepted offer.")


# async def get_offer_todo_from_current_user(
#     current_user: UserInDB = Depends(get_current_active_user),
#     todo: TodoInDB = Depends(get_todo_by_id_from_path),
#     tasks_repo: TasksRepository = Depends(get_repository(TasksRepository)),
# ) -> None:
#     """Get all tas"""
#     return await get_task_for_todo_from_user(user=current_user, todo=todo, tasks_repo=tasks_repo)
