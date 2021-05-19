"""Dependies for todo."""

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.todos import TodosRepository
from app.models.todo import TodoPublic
from app.models.user import UserInDB
from fastapi import Depends, HTTPException, Path, status


async def get_todo_by_id_from_path(
    todo_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    todos_repo: TodosRepository = Depends(get_repository(TodosRepository)),
) -> TodoPublic:
    """Depedency for get todo using id."""
    todo = await todos_repo.get_todo_by_id(id=todo_id, requesting_user=current_user)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No todo found with that id")
    return todo


def check_todo_modification_permission(
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoPublic = Depends(get_todo_by_id_from_path),
) -> None:
    """Depedency to check modification permission of user."""
    if not user_owns_todo(user=current_user, todo=todo):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forboidden. Users are only able to modify todos they own.",
        )


def user_owns_todo(*, user: UserInDB, todo: TodoPublic) -> bool:
    """Check if user owns the todo."""
    if isinstance(todo.owner, int):
        return todo.owner == user.id
    return todo.owner.id == user.id
