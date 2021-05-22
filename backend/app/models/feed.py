"""Model for Feed."""

import datetime
from typing import Literal, Optional

from app.models.core import CoreModel
from app.models.todo import TodoPublic


class FeedItem(CoreModel):
    """Feeditem base class."""

    row_number: Optional[int]
    event_timestamp: Optional[datetime.datetime]


class TodoFeedItem(TodoPublic, FeedItem):
    """Class item for todofeed."""

    event_type: Optional[Literal["is_update", "is_create"]]  # we could have used Enum though.
