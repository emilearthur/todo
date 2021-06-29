"""Routes for todo."""

from typing import List

from fastapi import APIRouter, Body, Depends, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.todos import (check_todo_modification_permission,
                                        get_todo_by_id_from_path)
from app.db.repositories.comments import CommentsRepository
from app.db.repositories.todos import TodosRepository
from app.models.comment import CommentInDB
from app.models.todo import TodoCreate, TodoInDB, TodoPublic, TodoUpdate
from app.models.user import UserInDB

router = APIRouter()


@router.post("/", response_model=TodoPublic, name="todos:create-todo", status_code=status.HTTP_201_CREATED)
async def create_new_todo(new_todo: TodoCreate = Body(..., embed=True),
                          todos_repo: TodosRepository = Depends(get_repository(TodosRepository)),
                          current_user: UserInDB = Depends(get_current_active_user),) -> TodoPublic:
    """Post Method to Create TODOs."""
    created_todo = await todos_repo.create_todo(new_todo=new_todo, requesting_user=current_user)
    return TodoPublic(**created_todo.dict())


@router.get("/", response_model=List[TodoPublic], name="todos:list-all-user-todos")
async def get_all_todos(current_user: UserInDB = Depends(get_current_active_user),
                        todos_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> List[TodoPublic]:
    """Get Method to get all users TODOs."""
    return await todos_repo.list_all_user_todos(requesting_user=current_user)


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


@router.get("/{todo_id}/comments/", response_model=List[CommentInDB], name="todos:list-all-todo-comments")
async def get_all_comments(todo: TodoInDB = Depends(get_todo_by_id_from_path),
                           comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
                           ) -> List[CommentInDB]:
    """List all comment in todos."""
    return await comments_repo.get_todo_comments(todo=todo)
