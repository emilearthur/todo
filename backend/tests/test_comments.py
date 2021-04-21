"""Test for comments."""

from databases.core import Database
import pytest

from typing import List, Optional, Union, Dict
# from databases import Database

from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder

from httpx import AsyncClient

from app.models.user import UserInDB

from app.models.comment import CommentInDB, CommentPublic, CommentCreate
from app.models.todo import TodoInDB

from app.db.repositories.comments import CommentsRepository

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


class TestCreateComment:
    """Test comments create."""

    async def test_valid_input_create_comment(self, app: FastAPI,
                                              authorized_client: AsyncClient,
                                              test_user: UserInDB,
                                              new_comment: CommentInDB) -> None:
        res = await authorized_client.post(app.url_path_for("comments:create-comment"),
                                           json={"new_comment": jsonable_encoder(new_comment.dict())})
        assert res.status_code == status.HTTP_201_CREATED
        created_comment = CommentPublic(**res.json())
        assert created_comment.body == new_comment.body
        assert created_comment.todo_id == new_comment.todo_id
        assert created_comment.comment_owner == test_user.id

    async def test_comment_non_existing_todo(self, app: FastAPI,
                                             authorized_client: AsyncClient,
                                             test_user: UserInDB,) -> None:
        new_comment = CommentCreate(body="test comments", todo_id=5555)
        res = await authorized_client.post(app.url_path_for("comments:create-comment"),
                                           json={"new_comment": jsonable_encoder(new_comment.dict())})
        assert res.status_code == status.HTTP_404_NOT_FOUND

    async def test_unauthorized_user_unable_to_create_comment(self, app: FastAPI,
                                                              client: AsyncClient,
                                                              new_comment: CommentInDB) -> None:
        res = await client.post(app.url_path_for("comments:create-comment"),
                                json={"new_comment": jsonable_encoder(new_comment.dict())})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        assert res.status_code != status.HTTP_200_OK

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
            (None, 422),
            ({}, 422),
            ({"body": "some comments"}, 422),
            ({"todo_id": 10}, 422),
        ),
    )
    async def test_invalid_input_raises_error(self, app: FastAPI,
                                              authorized_client: AsyncClient,
                                              invalid_payload: Dict[str, Union[str, float]],
                                              test_comment: CommentInDB,
                                              status_code: int) -> None:
        res = await authorized_client.post(app.url_path_for("comments:create-comment"),
                                           json={"new_comment": jsonable_encoder(invalid_payload)})
        assert res.status_code == status_code


class TestUpdateComment:
    """Test comments update."""

    @pytest.mark.parametrize(
        "attrs_to_change, values",
        (
            (['body'], ["new fake comment here"]),
        ),
    )
    async def test_update_comment_with_valid_input(self, app: FastAPI,
                                                   authorized_client: AsyncClient,
                                                   test_comment: CommentInDB,
                                                   attrs_to_change: List[str],
                                                   values: List[str]) -> None:
        comments_update = {"comment_update": {attrs_to_change[i]: values[i] for i in range(len(attrs_to_change))}}
        res = await authorized_client.put(app.url_path_for("comments:update-comment-by-id", comment_id=test_comment.id),
                                          json=jsonable_encoder(comments_update))
        assert res.status_code == status.HTTP_200_OK
        updated_comment = CommentInDB(**res.json())
        for i in range(len(attrs_to_change)):
            assert getattr(updated_comment, attrs_to_change[i]) != getattr(test_comment, attrs_to_change[i])
            assert getattr(updated_comment, attrs_to_change[i]) == values[i]
        for attr, value in updated_comment.dict().items():
            if attr not in attrs_to_change and attr != "updated_at":
                assert getattr(test_comment, attr) == value

    async def test_user_gets_error_if_updating_other_users_todo(self, app: FastAPI,
                                                                authorized_client: AsyncClient,
                                                                test_comment_list: List[CommentInDB],) -> None:
        res = await authorized_client.put(app.url_path_for("comments:update-comment-by-id",
                                                           comment_id=test_comment_list[0].id),
                                          json=jsonable_encoder({"comment_update": {"body": "new test comments here"}}),
                                          )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    async def test_user_cant_change_ownership_of_todo(self, app: FastAPI,
                                                      authorized_client: AsyncClient,
                                                      test_comment: CommentInDB,
                                                      test_user: UserInDB,
                                                      test_user2: UserInDB,) -> None:
        res = await authorized_client.put(app.url_path_for("comments:update-comment-by-id",
                                                           comment_id=test_comment.id),
                                          json=jsonable_encoder({"todo_update": {"comment_owner": test_user2.id}}),)
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "id, payload, status_code",
        (
            (-1, {"body": "test"}, 422),
            (0, {"body": "test2"}, 422),
            (55555, {"body": "test3"}, 404),
            (1, None, 422),
        ),
    )
    async def test_update_comment_with_invalid_input_throws_error(self, app: FastAPI,
                                                                  authorized_client: AsyncClient,
                                                                  id: int,
                                                                  payload: Dict[str, Optional[str]],
                                                                  status_code: int,) -> None:
        comment_update = {"comment_update": payload}
        res = await authorized_client.put(app.url_path_for("comments:update-comment-by-id", comment_id=id),
                                          json=comment_update)
        assert res.status_code == status_code


class TestDeleteComment:
    """Test Comment Delete."""

    async def test_can_delete_comment_successfully(self, app: FastAPI,
                                                   authorized_client: AsyncClient,
                                                   test_comment: CommentInDB,
                                                   test_user: UserInDB,
                                                   db: Database) -> None:
        comments_repo = CommentsRepository(db)

        res = await authorized_client.delete(app.url_path_for("comments:delete-comment-by-id",
                                                              comment_id=test_comment.id))
        assert res.status_code == status.HTTP_200_OK
        # update comments to check if comment exists. should reutrn 404
        comment_update = {"comment_update": {"body": "test3"}}
        res = await authorized_client.put(app.url_path_for("comments:update-comment-by-id",
                                                           comment_id=test_comment.id),
                                          json=comment_update)
        assert res.status_code == status.HTTP_404_NOT_FOUND

        comment = await comments_repo.get_comments_by_id(id=test_comment.id, requesting_user=test_user)
        assert comment is None

    async def test_user_cannot_delete_others_comment(self, app: FastAPI,
                                                     authorized_client: AsyncClient,
                                                     test_comment_list: List[CommentInDB]) -> None:
        res = await authorized_client.delete(app.url_path_for("comments:delete-comment-by-id",
                                                              comment_id=test_comment_list[0].id))
        assert res.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "id, status_code",
        (
            (500, 404),
            (0, 422),
            (-1, 422),
            (None, 422),
        ),
    )
    async def test_can_delete_comment_invalid_throws_error(self, app: FastAPI,
                                                           authorized_client: AsyncClient,
                                                           test_comment: CommentInDB,
                                                           id: int,
                                                           status_code: int) -> None:
        res = await authorized_client.delete(app.url_path_for("comments:delete-comment-by-id",
                                                              comment_id=id))
        assert res.status_code == status_code


class TestGetComment:
    """Test get all comments."""

    async def test_get_all_todo_comment(self, app: FastAPI,
                                        authorized_client: AsyncClient,
                                        test_todo: TodoInDB,
                                        test_comment: CommentInDB,
                                        test_comment_2: CommentInDB) -> None:
        res = await authorized_client.get(app.url_path_for("todos:list-all-todo-comments", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_200_OK
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0
        comments = [CommentInDB(**comment) for comment in res.json()]
        assert test_comment in comments
        assert test_comment_2 in comments

    async def test_get_all_user_comment(self, app: FastAPI,
                                        authorized_client: AsyncClient,
                                        test_todo: TodoInDB,
                                        test_comment: CommentInDB,) -> None:
        res = await authorized_client.get(app.url_path_for("users:get-user-comments"))
        assert res.status_code == status.HTTP_200_OK
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0
        comments = [CommentInDB(**comment) for comment in res.json()]
        assert test_comment in comments

