"""Routes for todo feeds."""

import datetime
from typing import List

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.feed import FeedRepository
from app.models.feed import TodoFeedItem
from app.models.user import UserInDB
from fastapi import APIRouter, Depends, Query

router = APIRouter()


@router.get(
    "/tasks/",
    response_model=List[TodoFeedItem],
    name="feed:get-todo-feed-for-user",
    dependencies=[Depends(get_current_active_user)],
)
async def get_todo_feed_for_user(
    current_user: UserInDB = Depends(get_current_active_user),
    page_chunk_size: int = Query(
        20, ge=1, le=50, description="Used to determine how many todo feed item objects to return in the response"
    ),
    starting_date: datetime.datetime = Query(
        datetime.datetime.now() + datetime.timedelta(minutes=10),
        description="Used to determine the timestamp at which to begin querying for todo feed items.",
    ),
    feeds_repo: FeedRepository = Depends(get_repository(FeedRepository)),
) -> List[TodoFeedItem]:
    """Get todo feed for user."""
    return await feeds_repo.fetch_todo_jobs_feed(
        requesting_user=current_user,
        page_chunk_size=page_chunk_size,
        starting_date=starting_date,
    )
