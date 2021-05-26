"""Dependecies for comment."""

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.tasks import get_offer_for_task_from_user_by_path
from app.api.dependencies.todos import get_todo_by_id_from_path, user_owns_todo
from app.api.dependencies.users import get_user_by_username_from_path
from app.db.repositories.comments import CommentsRepository
from app.models.comment import CommentInDB
from app.models.task import TaskInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import Depends, HTTPException, Path, status


async def get_comment_by_id_from_path(
    comment_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> CommentInDB:
    """Depency to get comment by using id."""
    comment = await comments_repo.get_comments_by_id(id=comment_id, requesting_user=current_user)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No comments found with that id")
    return comment


def check_comment_modification_permission(
    current_user: UserInDB = Depends(get_current_active_user),
    comment: CommentInDB = Depends(get_comment_by_id_from_path),
) -> None:
    """Dependency to check modification permission of user."""
    if comment.comment_owner != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forbidden. Users are unable to modify comments they did not create.",
        )


def check_comment_todo_permission(
    current_user: UserInDB = Depends(get_current_active_user), todo: TodoInDB = Depends(get_todo_by_id_from_path)
):
    """Permission of a todo owner to comment on a todo. This can be extended to groups when introduced."""
    if not user_owns_todo(user=current_user, todo=todo):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users are unable to comment todos they don't own.",
        )


def check_comment_task_permission(
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    tasktaker: UserInDB = Depends(get_user_by_username_from_path),
    task: TaskInDB = Depends(get_offer_for_task_from_user_by_path),
):
    """Permission for task owner and task taker to comment on a task."""
    if (not user_owns_todo(user=current_user, todo=todo)) or (not (task.user_id == current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users are unable to leave comments for todos or tasks they don't own.",
        )
    # only tasks accepted can be commented.
    if task.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only users accepted tasks can be commented."
        )
    # check that comments can only be made for user whose offer for task was accepted for a job.
    # if task.user_id != tasktaker.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="You are not authorized to leave an comments...",
    #     )
