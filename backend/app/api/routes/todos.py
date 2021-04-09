from typing import List

from fastapi import APIRouter, Body, Path, Depends, status, HTTPException

from app.models.todo import TodoCreate, TodoPublic, TodoUpdate
from app.db.repositories.todos import TodosRepository
from app.api.dependencies.database import get_repository


router = APIRouter()


@router.post("/", response_model=TodoPublic, name="todos:create-todo", status_code=status.HTTP_201_CREATED)
async def create_new_todo(new_todo: TodoCreate = Body(..., embed=True),
                          todo_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> TodoPublic:
    created_todo = await todo_repo.create_todo(new_todo=new_todo)
    return created_todo


@router.get("/", response_model=List[TodoPublic], name="todos:get-all-todos")
async def get_all_todos(todo_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> List[TodoPublic]:
    return await todo_repo.get_all_todos()


@router.get("/{id}", response_model=TodoPublic, name="todos:get-todo-by-id")
async def get_todo_by_id(id: int = Path(..., ge=1),
                         todo_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> TodoPublic:
    todo = await todo_repo.get_todo_by_id(id=id)

    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with id: {id} not found")
    return todo


@router.put("/{id}", response_model=TodoPublic, name="todos:update-todo-by-id")
async def update_todos_by_id(id: int = Path(..., ge=1),
                             todo_update: TodoUpdate = Body(..., embed=True),
                             todo_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> TodoPublic:
    todo_updated = await todo_repo.update_todos_by_id(id=id, todo_update=todo_update)

    if not todo_updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No cleaning found with id:{id}.")
    return todo_updated


@router.delete("/{id}", response_model=int, name="todos:delete-todo-by-id")
async def delete_by_id(id: int = Path(..., ge=1, title="The todo ID to be deleted"),
                       todo_repo: TodosRepository = Depends(get_repository(TodosRepository)),) -> int:
    deleted_id = await todo_repo.delete_todo_by_id(id=id)
    if not deleted_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No todo found, thus cannot delete")
    return deleted_id
