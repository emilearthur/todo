"""Test for comments."""

import pytest

from databases import Database

from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.user import UserInDB, UserPublic
from app.models.todo import TodoCreate, TodoInDB

from app.models.comment import CommentCreate, CommentInDB, CommentPublic

from app.db.repositories.profiles import ProfilesRepository

pytestmark = pytest.mark.asyncio


class TestCommentRoute:
    """Test for routes of comments."""

    async def test_routes_exists(self, app: FastAPI,
                                 client: AsyncClient,) -> None:
        """Test for routes."""
        res = await client.post(app.url_path_for("comments:create-comment"), json={})
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.put(app.url_path_for("comments:update-comment-by-id", comment_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.delete(app.url_path_for("comments:delete-comment-by-id", comment_id=0))
        assert res.status_code != status.HTTP_404_NOT_FOUND

    async def test_invalid_input_raises_error(self, app: FastAPI, authorized_client: AsyncClient) -> None:
        """Test invalid comment returns 422."""
        res = await authorized_client.post(app.url_path_for("comments:create-comment"), json={})
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
