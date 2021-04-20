"""Dependecies for comment."""

from fastapi import HTTPException, Depends, Path, status
from starlette.status import HTTP_403_FORBIDDEN

from app.models.comment import CommentInDB

from app.db.repositories.comments import CommentsRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.models.user import UserInDB


async def get_comment_by_id_from_path(comment_id: int = Path(..., ge=1),
                                      current_user: UserInDB = Depends(get_current_active_user),
                                      comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
                                      ) -> CommentInDB:
    """Depency to get comment by using id."""
    comment = await comments_repo.get_comments_by_id(id=comment_id, requesting_user=current_user)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No comments found with that id")
    return comment


def check_comment_modification_permission(current_user: UserInDB = Depends(get_current_active_user),
                                          comment: CommentInDB = Depends(get_comment_by_id_from_path),) -> None:
    """Dependency to check modification permission of user."""
    if comment.comment_owner != current_user.id:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                            detail="Action forbidden. Users are unable to modify comments they did not create.")
