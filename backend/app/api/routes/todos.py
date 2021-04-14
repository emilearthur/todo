"""Routes for todo."""

from typing import List

from fastapi import APIRouter, Body, Depends, status

from app.models.todo import TodoCreate, TodoPublic, TodoUpdate, TodoInDB
from app.models.user import UserInDB

from app.db.repositories.todos import TodosRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.todos import get_todo_by_id_from_path, check_todo_modification_permission


router = APIRouter()


@router.post("/", response_model=TodoPublic, name="todos:create-todo", status_code=status.HTTP_201_CREATED)
async def create_new_todo(new_todo: TodoCreate = Body(..., embed=True),
                          todo_repo: TodosRepository = Depends(get_repository(TodosRepository)),
                          current_user: UserInDB = Depends(get_current_active_user),) -> TodoPublic:
    """Post Method to Create TODOs."""
    created_todo = await todo_repo.create_todo(new_todo=new_todo, requesting_user=current_user)
    return TodoPublic(**created_todo.dict())


@router.get("/", response_model=List[TodoPublic], name="todos:list-all-user-todos")
async def get_all_todos(current_user: UserInDB = Depends(get_current_active_user),
                        todo_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> List[TodoPublic]:
    """Get Method to get all users TODOs."""
    return await todo_repo.list_all_user_todos(requesting_user=current_user)


@router.get("/{todo_id}/", response_model=TodoPublic, name="todos:get-todo-by-id")
async def get_todo_by_id(todo: TodoInDB = Depends(get_todo_by_id_from_path)) -> TodoPublic:
    """Get Method to get TODOs by id."""
    return todo


@router.put("/{todo_id}/", response_model=TodoPublic, name="todos:update-todo-by-id",
            dependencies=[Depends(check_todo_modification_permission)],)
async def update_todos_by_id(todo: TodoInDB = Depends(get_todo_by_id_from_path),
                             todo_update: TodoUpdate = Body(..., embed=True),
                             todos_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> TodoPublic:
    """Update Method to update TODOs by id."""
    return await todos_repo.update_todos_by_id(todo=todo, todo_update=todo_update)


@router.delete("/{todo_id}/", response_model=int, name="todos:delete-todo-by-id",
               dependencies=[Depends(check_todo_modification_permission)],)
async def delete_by_id(todo: TodoInDB = Depends(get_todo_by_id_from_path),
                       todos_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> int:
    """Delete Method to delete TODOs by id."""
    return await todos_repo.delete_todo_by_id(todo=todo)
