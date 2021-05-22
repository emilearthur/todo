"""Testing Feed Enpoint."""

import datetime
from typing import Counter, List

import pytest
from app.models.feed import TodoFeedItem
from app.models.todo import TodoInDB
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestFeedRoutes:
    """Testing Routes."""

    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        """Test if routes exists."""
        res = await client.get(app.url_path_for("feed:get-todo-feed-for-user"))
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestTodoFeed:
    """Testing TodoFeed."""

    async def test_todo_feed_returns_valid_response(
        self,
        *,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_list_of_new_and_updated_todos: List[TodoInDB],
    ) -> None:
        """Test todo feed returns valid response."""
        todo_ids = [todo.id for todo in test_list_of_new_and_updated_todos]
        res = await authorized_client.get(app.url_path_for("feed:get-todo-feed-for-user"))
        assert res.status_code == status.HTTP_200_OK
        todo_feed = res.json()
        assert isinstance(todo_feed, list)
        assert len(todo_feed) == 20
        assert set(feed_item["id"] for feed_item in todo_feed).issubset(
            set(todo_ids)
        )  # each unqiue id in the res is also a memeber of todo_ids.

    async def test_todo_feed_response_is_ordered_correctly(
        self,
        *,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_list_of_new_and_updated_todos: List[TodoInDB],
    ) -> None:
        """Check if feed is ordered correctly."""
        res = await authorized_client.get(app.url_path_for("feed:get-todo-feed-for-user"))
        assert res.status_code == status.HTTP_200_OK
        todo_feed = res.json()
        # the first 13 should be updated and the rest should not be updated
        for feed_item in todo_feed[:13]:
            assert feed_item["event_type"] == "is_update"
        for feed_item in todo_feed[13:]:
            assert feed_item["event_type"] == "is_create"

    async def test_todo_feed_can_paginate_correctly(
        self,
        *,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_list_of_new_and_updated_todos: List[TodoInDB],
    ) -> None:
        """Check if todo feed is paginated correctly."""
        res_page_1 = await authorized_client.get(app.url_path_for("feed:get-todo-feed-for-user"))
        assert res_page_1.status_code == status.HTTP_200_OK
        todo_feed_page_1 = res_page_1.json()
        assert len(todo_feed_page_1) == 20
        ids_page_1 = set(feed_item["id"] for feed_item in todo_feed_page_1)
        new_starting_date = todo_feed_page_1[-1]["event_timestamp"]

        res_page_2 = await authorized_client.get(
            app.url_path_for("feed:get-todo-feed-for-user"),
            params={"starting_date": new_starting_date, "page_chunk_size": 20},
        )
        assert res_page_2.status_code == status.HTTP_200_OK
        todo_feed_page_2 = res_page_2.json()
        assert len(todo_feed_page_2) == 20
        ids_page_2 = set(feed_item["id"] for feed_item in todo_feed_page_2)

        assert ids_page_1 != ids_page_2

    async def test_todo_feed_can_paginate_correctly_two(
        self,
        *,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_list_of_new_and_updated_todos: List[TodoInDB],
    ) -> None:
        """Check if todo feed is paginated correctly."""
        starting_date = datetime.datetime.now() + datetime.timedelta(minutes=10)
        combos = []
        for chunk_size in [25, 15, 10]:
            res = await authorized_client.get(
                app.url_path_for("feed:get-todo-feed-for-user"),
                params={"starting_date": starting_date, "page_chunk_size": chunk_size},
            )
            assert res.status_code == status.HTTP_200_OK
            page_json = res.json()
            assert len(page_json) == chunk_size
            id_and_event_combo = set(f"{item['id']}-{item['event_type']}" for item in page_json)
            combos.append(id_and_event_combo)
            starting_date = page_json[-1]["event_timestamp"]
        #  ensure all non of the items in any response exist in any other response.
        length_of_all_id_combos = sum(len(combo) for combo in combos)
        assert len(set().union(*combos)) == length_of_all_id_combos

    async def test_todo_feed_has_created_and_updated_items_for_modified_cleaning_jobs(
        self,
        *,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_list_of_new_and_updated_todos: List[TodoInDB],
    ) -> None:
        """Check if todo feed has created and updated items when changes are made."""
        res_page_1 = await authorized_client.get(
            app.url_path_for("feed:get-todo-feed-for-user"),
            params={"page_chunk_size": 30},
        )
        assert res_page_1.status_code == status.HTTP_200_OK
        ids_page_1 = [feed_item["id"] for feed_item in res_page_1.json()]
        todo_feeds = [TodoFeedItem(**feed_item) for feed_item in res_page_1.json()]
        for todo_feed in todo_feeds:
            assert todo_feed.as_task is True

        new_starting_date = res_page_1.json()[-1]["updated_at"]

        res_page_2 = await authorized_client.get(
            app.url_path_for("feed:get-todo-feed-for-user"),
            params={"starting_date": new_starting_date, "page_chunk_size": 33},
        )
        assert res_page_2.status_code == status.HTTP_200_OK
        ids_page_2 = [feed_item["id"] for feed_item in res_page_2.json()]
        todo_feeds_2 = [TodoFeedItem(**feed_item) for feed_item in res_page_2.json()]
        for todo_feed in todo_feeds_2:
            assert todo_feed.as_task is True

        # should have duplicate IDs for 13 update events an `is_create` event and an `is_update` event
        id_counts = Counter(ids_page_1 + ids_page_2)
        assert len([id for id, cnt in id_counts.items() if cnt > 1]) == 13
