"""Routes for comments."""
from fastapi import APIRouter, Body, Depends, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.comments import (
    check_comment_modification_permission, get_comment_by_id_from_path)
from app.api.dependencies.database import get_repository
from app.db.repositories.comments import CommentsRepository
from app.models.comment import (CommentCreate, CommentInDB, CommentPublic,
                                CommentUpdate)
from app.models.user import UserInDB

router = APIRouter()


@router.post("/", response_model=CommentPublic, name="comments:create-comment", status_code=status.HTTP_201_CREATED)
async def create_new_comment(new_comment: CommentCreate = Body(..., embed=True),
                             comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
                             current_user: UserInDB = Depends(get_current_active_user),
                             ) -> CommentPublic:
    """Create comments."""
    created_comment = await comments_repo.create_comment(new_comment=new_comment, requesting_user=current_user)
    return CommentPublic(**created_comment.dict())


@router.put("/{comment_id}/", response_model=CommentPublic, name="comments:update-comment-by-id",
            dependencies=[Depends(check_comment_modification_permission)],)
async def update_comment_by_id(comment: CommentInDB = Depends(get_comment_by_id_from_path),
                               comment_update: CommentUpdate = Body(..., embed=True),
                               comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
                               ) -> CommentPublic:
    """Update comment."""
    return await comments_repo.update_comments(comment=comment,
                                               comment_update=comment_update)


@router.delete("/{comment_id}/", response_model=int, name="comments:delete-comment-by-id",
               dependencies=[Depends(check_comment_modification_permission)],)
async def delete_comment(comment: CommentInDB = Depends(get_comment_by_id_from_path),
                         comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
                         ) -> int:
    """Delete comment."""
    return await comments_repo.delete_comment(comment=comment)
