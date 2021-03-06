"""Routes for comments."""

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.comments import (
    check_comment_modification_permission,
    check_comment_task_permission,
    check_comment_todo_permission,
    get_comment_by_id_from_path,
)
from app.api.dependencies.database import get_repository
from app.api.dependencies.tasks import get_offer_for_task_from_user_by_path
from app.api.dependencies.todos import get_todo_by_id_from_path
from app.db.repositories.comments import CommentsRepository
from app.models.comment import CommentCreate, CommentInDB, CommentPublic, CommentUpdate
from app.models.task import TaskInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import APIRouter, Body, Depends, status

router = APIRouter()


@router.post(
    "/{todo_id}",
    response_model=CommentPublic,
    name="comments:create-comment-todo",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_comment_todo_permission)],
)
async def create_new_comment(
    new_comment: CommentCreate = Body(..., embed=True),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
) -> CommentPublic:
    """Create comments for todo."""
    created_comment = await comments_repo.create_comment_todo(
        new_comment=new_comment, todo=todo, requesting_user=current_user
    )
    return CommentPublic(**created_comment.dict())


@router.put(
    "/{comment_id}/",
    response_model=CommentPublic,
    name="comments:update-comment-by-id",
    dependencies=[Depends(check_comment_modification_permission)],
)
async def update_comment_by_id(
    comment: CommentInDB = Depends(get_comment_by_id_from_path),
    comment_update: CommentUpdate = Body(..., embed=True),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> CommentPublic:
    """Update comment."""
    return await comments_repo.update_comments(comment=comment, comment_update=comment_update)


@router.delete(
    "/{comment_id}/",
    response_model=int,
    name="comments:delete-comment-by-id",
    dependencies=[Depends(check_comment_modification_permission)],
)
async def delete_comment(
    comment: CommentInDB = Depends(get_comment_by_id_from_path),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> int:
    """Delete comment."""
    return await comments_repo.delete_comment(comment=comment)


@router.post(
    "/{todo_id}/{username}/",
    response_model=CommentPublic,
    name="comments:create-comment-task",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_comment_task_permission)],
)
async def create_new_comment_task(
    new_comment: CommentCreate = Body(..., embed=True),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
    current_user: UserInDB = Depends(get_current_active_user),
    task: TaskInDB = Depends(get_offer_for_task_from_user_by_path),
) -> CommentPublic:
    """Create comments for task."""
    created_comment = await comments_repo.create_comment_task(
        new_comment=new_comment, task=task, requesting_user=current_user
    )
    return CommentPublic(**created_comment.dict())
