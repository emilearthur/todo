"""Test for comments."""

from typing import Callable, Dict, List, Optional, Union

import pytest
from app.db.repositories.comments import CommentsRepository
from app.models.comment import CommentCreate, CommentInDB, CommentPublic
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from databases.core import Database
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from redis.client import Redis

pytestmark = pytest.mark.asyncio


class TestCommentRoute:
    """Test for routes of comments."""

    async def test_routes_exists(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """Test for routes."""
        res = await client.post(app.url_path_for("comments:create-comment-todo", todo_id=1), json={})
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.put(app.url_path_for("comments:update-comment-by-id", comment_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.delete(app.url_path_for("comments:delete-comment-by-id", comment_id=0))
        assert res.status_code != status.HTTP_404_NOT_FOUND

    async def test_invalid_input_raises_error(
        self, app: FastAPI, authorized_client: AsyncClient, test_todo: TodoInDB
    ) -> None:
        """Test invalid comment returns 422."""
        res = await authorized_client.post(
            app.url_path_for("comments:create-comment-todo", todo_id=test_todo.id), json={}
        )
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateComment:
    """Test comments create."""

    async def test_valid_input_create_comment_for_todo(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        test_todo: TodoInDB,
    ) -> None:
        """Check comments with valid inputs."""
        new_comment = CommentCreate(body="test comments")
        res = await authorized_client.post(
            app.url_path_for("comments:create-comment-todo", todo_id=test_todo.id),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_201_CREATED
        created_comment = CommentPublic(**res.json())
        assert created_comment.body == new_comment.body
        assert created_comment.todo_id == test_todo.id
        assert created_comment.comment_owner == test_user.id

    async def test_valid_input_create_comment_for_task(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Check comments with valid inputs."""
        new_comment = CommentCreate(body="test comments")
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_201_CREATED
        created_comment = CommentPublic(**res.json())
        assert created_comment.body == new_comment.body
        assert created_comment.todo_id == test_todo_with_accepted_task_offer.id
        assert created_comment.comment_owner == test_user2.id

        authorized_client = create_authorized_client(user=test_user3)
        res = await authorized_client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_201_CREATED
        created_comment = CommentPublic(**res.json())
        assert created_comment.body == new_comment.body
        assert created_comment.todo_id == test_todo_with_accepted_task_offer.id
        assert created_comment.comment_owner == test_user3.id

    async def test_non_tasktaker_or_todo_owner_can_comment_task(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user: UserInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """User who's not a todo owner or tasktaker cannot comment a task."""
        new_comment = CommentCreate(body="test comments")
        authorized_client = create_authorized_client(user=test_user)
        res = await authorized_client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    async def test_valid_input_not_create_comment_on_other_todo(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        test_todo_2: TodoInDB,
    ) -> None:
        """Check comments with valid inputs."""
        new_comment = CommentCreate(body="test comments", task=True)
        res = await authorized_client.post(
            app.url_path_for("comments:create-comment-todo", todo_id=test_todo_2.id),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    async def test_comment_non_existing_todo(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
    ) -> None:
        """Test non existing todos cannot be commented."""
        new_comment = CommentCreate(body="test comments", task=True)
        res = await authorized_client.post(
            app.url_path_for("comments:create-comment-todo", todo_id=5555),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

    async def test_comment_non_existing_task(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user3: UserInDB,
        test_todo: TodoInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Test non existing task cannot be commented."""
        new_comment = CommentCreate(body="test comments", task=True)
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

    async def test_unauthorized_user_unable_to_create_comment_for_todo(
        self, app: FastAPI, client: AsyncClient, test_todo: TodoInDB, new_comment: CommentInDB
    ) -> None:
        """Test unauthorized users cannot comment."""
        res = await client.post(
            app.url_path_for("comments:create-comment-todo", todo_id=test_todo.id),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        assert res.status_code != status.HTTP_200_OK

    async def test_unauthorized_user_unable_to_create_comment_for_task(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_todo: TodoInDB,
        new_comment: CommentInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Test unauthorized users cannot comment."""
        new_comment = CommentCreate(body="test comments", task=True)
        res = await client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        assert res.status_code != status.HTTP_200_OK

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
            (None, 422),
            ({}, 422),
        ),
    )
    async def test_invalid_input_raises_error(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        create_authorized_client: Callable,
        invalid_payload: Dict[str, Union[str, float]],
        test_todo: TodoInDB,
        test_user2: UserInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
        status_code: int,
    ) -> None:
        """Testing error raised when invalid input is given for comments."""
        # for todo
        res = await authorized_client.post(
            app.url_path_for("comments:create-comment-todo", todo_id=test_todo.id),
            json={"new_comment": jsonable_encoder(invalid_payload)},
        )
        assert res.status_code == status_code

        # for taak
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(invalid_payload)},
        )
        assert res.status_code == status_code


class TestUpdateComment:
    """Test comments update."""

    @pytest.mark.parametrize(
        "attrs_to_change, values",
        ((["body"], ["new fake comment here"]),),
    )
    async def test_update_comment_with_valid_input(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_comment: CommentInDB,
        attrs_to_change: List[str],
        values: List[str],
    ) -> None:
        """Testing comments update."""
        comments_update = {"comment_update": {attrs_to_change[i]: values[i] for i in range(len(attrs_to_change))}}
        res = await authorized_client.put(
            app.url_path_for("comments:update-comment-by-id", comment_id=test_comment.id),
            json=jsonable_encoder(comments_update),
        )
        assert res.status_code == status.HTTP_200_OK
        updated_comment = CommentInDB(**res.json())
        for i in range(len(attrs_to_change)):
            assert getattr(updated_comment, attrs_to_change[i]) != getattr(test_comment, attrs_to_change[i])
            assert getattr(updated_comment, attrs_to_change[i]) == values[i]
        for attr, value in updated_comment.dict().items():
            if attr not in attrs_to_change and attr != "updated_at":
                assert getattr(test_comment, attr) == value

    async def test_user_gets_error_if_updating_other_users_comments(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_comment_list: List[CommentInDB],
    ) -> None:
        """Test error raise when updating another comments."""
        res = await authorized_client.put(
            app.url_path_for("comments:update-comment-by-id", comment_id=test_comment_list[0].id),
            json=jsonable_encoder({"comment_update": {"body": "new test comments here"}}),
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    async def test_user_cant_change_ownership_of_comment(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_comment: CommentInDB,
        test_user: UserInDB,
        test_user2: UserInDB,
    ) -> None:
        """Test comment ownership cannot be changed."""
        res = await authorized_client.put(
            app.url_path_for("comments:update-comment-by-id", comment_id=test_comment.id),
            json=jsonable_encoder({"todo_update": {"comment_owner": test_user2.id}}),
        )
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
    async def test_update_comment_with_invalid_input_throws_error(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        id: int,
        payload: Dict[str, Optional[str]],
        status_code: int,
    ) -> None:
        """Test invalid comment throws an error."""
        comment_update = {"comment_update": payload}
        res = await authorized_client.put(
            app.url_path_for("comments:update-comment-by-id", comment_id=id),
            json=comment_update,
        )
        assert res.status_code == status_code


class TestDeleteComment:
    """Test Comment Delete."""

    async def test_can_delete_comment_successfully(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_comment: CommentInDB,
        test_user: UserInDB,
        db: Database,
        r_db: Redis,
    ) -> None:
        """Test comments can be deleted successfully."""
        comments_repo = CommentsRepository(db, r_db)

        res = await authorized_client.delete(
            app.url_path_for("comments:delete-comment-by-id", comment_id=test_comment.id)
        )
        assert res.status_code == status.HTTP_200_OK
        # update comments to check if comment exists. should reutrn 404
        comment_update = {"comment_update": {"body": "test3"}}
        res = await authorized_client.put(
            app.url_path_for("comments:update-comment-by-id", comment_id=test_comment.id),
            json=comment_update,
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

        comment = await comments_repo.get_comments_by_id(id=test_comment.id, requesting_user=test_user)
        assert comment is None

    async def test_user_cannot_delete_others_comment(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_comment_list: List[CommentInDB],
    ) -> None:
        """Test user cannot deleted anothers comments."""
        res = await authorized_client.delete(
            app.url_path_for("comments:delete-comment-by-id", comment_id=test_comment_list[0].id)
        )
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
    async def test_can_delete_comment_invalid_throws_error(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_comment: CommentInDB,
        id: int,
        status_code: int,
    ) -> None:
        """Test deleting not existing comment of invalid inputs throws errors."""
        res = await authorized_client.delete(app.url_path_for("comments:delete-comment-by-id", comment_id=id))
        assert res.status_code == status_code


class TestGetComment:
    """Test get all comments."""

    async def test_get_all_todo_comment(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_todo: TodoInDB,
        test_comment: CommentInDB,
        test_comment_2: CommentInDB,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Test all todos comments can be requested."""
        # for todo
        res = await authorized_client.get(app.url_path_for("todos:list-all-todo-comments", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_200_OK
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0
        comments = [CommentInDB(**comment) for comment in res.json()]
        assert test_comment in comments
        assert test_comment_2 in comments

        # for task
        # create comment
        new_comment = CommentCreate(body="test comments", task=True)
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_201_CREATED
        created_comment_1 = CommentPublic(**res.json())

        new_comment = CommentCreate(body="test comments", task=True)
        authorized_client = create_authorized_client(user=test_user3)
        res = await authorized_client.post(
            app.url_path_for(
                "comments:create-comment-task",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"new_comment": jsonable_encoder(new_comment.dict())},
        )
        assert res.status_code == status.HTTP_201_CREATED
        created_comment_2 = CommentPublic(**res.json())

        res = await authorized_client.get(
            app.url_path_for(
                "task:list-all-task-comments",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
        )
        assert res.status_code == status.HTTP_200_OK
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0
        comments = [CommentInDB(**comment) for comment in res.json()]
        assert created_comment_1 in comments
        assert created_comment_2 in comments
        assert test_comment not in comments

    async def test_get_all_user_comment(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_todo: TodoInDB,
        test_comment: CommentInDB,
    ) -> None:
        """Test all users comments can be requested."""
        res = await authorized_client.get(app.url_path_for("users:get-user-comments"))
        assert res.status_code == status.HTTP_200_OK
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0
        comments = [CommentInDB(**comment) for comment in res.json()]
        assert test_comment in comments
