"""Dependies for todo."""

from fastapi import HTTPException, Depends, Path, status

from app.models.user import UserInDB
from app.models.todo import TodoInDB

from app.db.repositories.todos import TodosRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user


async def get_todo_by_id_from_path(todo_id: int = Path(..., ge=1),
                                   current_user: UserInDB = Depends(get_current_active_user),
                                   todos_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> TodoInDB:
    """Depedency for get todo using id."""
    todo = await todos_repo.get_todo_by_id(id=todo_id, requesting_user=current_user)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No todo found with that id")
    return todo


def check_todo_modification_permission(current_user: UserInDB = Depends(get_current_active_user),
                                       todo: TodoInDB = Depends(get_todo_by_id_from_path),) -> None:
    """Depedency to check modification permission of user."""
    if todo.owner != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Action forboidden. Users are only able to modify todos they own.")
