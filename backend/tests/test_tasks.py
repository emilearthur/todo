"""Test for assigning todo."""

import random
from typing import Callable, List

import pytest
from app.db.repositories.tasks import TasksRepository
from app.models.task import TaskInDB, TaskPublic
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestTaskRoutes:
    """Test to make sure task routes don't return 404s."""

    async def test_routes_exist(self, app: FastAPI, client: AsyncClient):
        """Making sure all routues are working."""
        res = await client.post(app.url_path_for("assigns:set-task", todo_id=1, username="johnmensah"))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.post(app.url_path_for("assigns:create-offer-for-task", todo_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.get(app.url_path_for("assigns:get_offer_from_user", todo_id=1, username="johnmensah"))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.put(app.url_path_for("assigns:accept-task-from-user", todo_id=1, username="johnmensah"))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.put(app.url_path_for("assigns:cancel-task-from-user", todo_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.delete(app.url_path_for("assigns:rescind-task-from-user", todo_id=1))
        res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.get(app.url_path_for("assigns:list-offers-for-task", todo_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestCreateTask:
    """Test creating tasks."""

    async def test_user_can_successfully_create_task_for_other_users_todo_task(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_todo_astask: TodoInDB,
        test_user3: UserInDB,
    ) -> None:
        """Test user can successful create task for others todo."""
        authorized_client = create_authorized_client(user=test_user3)
        res = await authorized_client.post(
            app.url_path_for("assigns:create-offer-for-task", todo_id=test_todo_astask.id)
        )
        assert res.status_code == status.HTTP_201_CREATED
        task = TaskInDB(**res.json())
        assert task.user_id == test_user3.id
        assert task.todo_id == test_todo_astask.id
        assert task.status == "pending"

    async def test_user_cant_successfully_create_task_for_other_users_todo_task_with_as_task_false(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_todo: TodoInDB,
        test_user3: UserInDB,
    ) -> None:
        """Test user cannot create task for others todo with as_task parameter false."""
        authorized_client = create_authorized_client(user=test_user3)
        res = await authorized_client.post(app.url_path_for("assigns:create-offer-for-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_user_cant_create_duplicate_task(
        self, app: FastAPI, create_authorized_client: Callable, test_todo_astask: TodoInDB, test_user4: UserInDB
    ) -> None:
        """Test task cannot be duplicated."""
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.post(
            app.url_path_for("assigns:create-offer-for-task", todo_id=test_todo_astask.id)
        )
        assert res.status_code == status.HTTP_201_CREATED

        res = await authorized_client.post(
            app.url_path_for("assigns:create-offer-for-task", todo_id=test_todo_astask.id)
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_user_unable_to_create_task_for_their_own_todo_job(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        test_todo: TodoInDB,
    ) -> None:
        """Test user unable to create task for their todo job."""
        res = await authorized_client.post(app.url_path_for("assigns:create-offer-for-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_unauthenticated_users_cant_create_todo(
        self, app: FastAPI, client: AsyncClient, test_todo: TodoInDB
    ) -> None:
        """Test unauthenticated users cannot create an offer for a task."""
        res = await client.post(app.url_path_for("assigns:create-offer-for-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "id, status_code",
        (
            (50000000, 404),
            (-1, 422),
            (None, 422),
        ),
    )
    async def test_wrong_id_give_error_status(
        self, app: FastAPI, create_authorized_client: Callable, test_user5: UserInDB, id: int, status_code: int
    ) -> None:
        """Test wrong todo ids returns errors."""
        authorized_client = create_authorized_client(user=test_user5)
        res = await authorized_client.post(app.url_path_for("assigns:create-offer-for-task", todo_id=id))
        assert res.status_code == status_code


class TestGetTasks:
    """Test users getting tasks."""

    async def test_task_owner_can_get_offer_from_user(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """Owner of a todo task can successfully fetch a single offer made for a todo task."""
        authorized_client = create_authorized_client(user=test_user2)
        selected_user = random.choice(test_user_list)
        res = await authorized_client.get(
            app.url_path_for(
                "assigns:get_offer_from_user",
                todo_id=test_todo_with_tasks.id,
                username=selected_user.username,
            )
        )
        assert res.status_code == status.HTTP_200_OK
        task = TaskPublic(**res.json())
        assert task.user_id == selected_user.id

    async def test_task_owner_can_get_own_offer(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """Creator of offer should be able to fetch their own offer."""
        first_test_user = test_user_list[0]
        authorized_client = create_authorized_client(user=first_test_user)
        res = await authorized_client.get(
            app.url_path_for(
                "assigns:get_offer_from_user",
                todo_id=test_todo_with_tasks.id,
                username=first_test_user.username,
            )
        )
        assert res.status_code == status.HTTP_200_OK
        task = TaskPublic(**res.json())
        assert task.user_id == first_test_user.id

    async def test_other_authenticated_users_cant_view_offer_from_user(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """Non-owners are fobidden from fetching an offer made for other users' todo task."""
        first_test_user = test_user_list[0]
        second_test_user = test_user_list[1]
        authorized_client = create_authorized_client(user=first_test_user)
        res = await authorized_client.get(
            app.url_path_for(
                "assigns:get_offer_from_user",
                todo_id=test_todo_with_tasks.id,
                username=second_test_user.username,
            )
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    async def test_todo_owner_get_all_offer_for_task(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """User able to fetch list of all offers made for their own todo task."""
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.get(
            app.url_path_for("assigns:list-offers-for-task", todo_id=test_todo_with_tasks.id)
        )
        assert res.status_code == status.HTTP_200_OK
        for offer in res.json():
            assert offer["user_id"] in [user.id for user in test_user_list]

    async def test_non_owners_forbidden_from_fetching_all_offers_for_task(
        self, app: FastAPI, authorized_client: AsyncClient, test_todo_with_tasks: TodoInDB
    ) -> None:
        """None owners forbidden from fetching a list of offer made for a todo task they don't own."""
        res = await authorized_client.get(
            app.url_path_for("assigns:list-offers-for-task", todo_id=test_todo_with_tasks.id)
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN


class TestAcceptTasks:
    """Test users accept tasks."""

    async def test_task_ower_can_accept_task_offer_successfully(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """Test todo task owner can accept offers."""
        selected_user = random.choice(test_user_list)
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.put(
            app.url_path_for(
                "assigns:accept-task-from-user",
                todo_id=test_todo_with_tasks.id,
                username=selected_user.username,
            )
        )
        assert res.status_code == status.HTTP_200_OK
        accepted_task = TaskPublic(**res.json())
        assert accepted_task.status == "accepted"
        assert accepted_task.user_id == selected_user.id
        assert accepted_task.todo_id == test_todo_with_tasks.id

    async def test_non_owner_forbidden_from_accepting_task_offer_for_todo(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """Test non task owner cannot accept offer."""
        selected_user = random.choice(test_user_list)
        res = await authorized_client.put(
            app.url_path_for(
                "assigns:accept-task-from-user",
                todo_id=test_todo_with_tasks.id,
                username=selected_user.username,
            )
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    async def test_todo_owner_cant_accept_multiple_task_offers(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """Test that todo owner can't accept multiple task offers."""
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.put(
            app.url_path_for(
                "assigns:accept-task-from-user",
                todo_id=test_todo_with_tasks.id,
                username=test_user_list[0].username,
            )
        )
        assert res.status_code == status.HTTP_200_OK

        res = await authorized_client.put(
            app.url_path_for(
                "assigns:accept-task-from-user",
                todo_id=test_todo_with_tasks.id,
                username=test_user_list[1].username,
            )
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_accepting_one_task_offer_rejects_all_other_offers(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """Test once a task is accepted, others are rejected."""
        selected_user = random.choice(test_user_list)
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.put(
            app.url_path_for(
                "assigns:accept-task-from-user",
                todo_id=test_todo_with_tasks.id,
                username=selected_user.username,
            )
        )
        assert res.status_code == status.HTTP_200_OK

        res = await authorized_client.get(
            app.url_path_for("assigns:list-offers-for-task", todo_id=test_todo_with_tasks.id)
        )
        assert res.status_code == status.HTTP_200_OK
        offers = [TaskPublic(**task) for task in res.json()]
        for offer in offers:
            if offer.user_id == selected_user.id:
                assert offer.status == "accepted"
            else:
                assert offer.status == "rejected"


class TestCancelTasks:
    """Test users cancels tasks."""

    async def test_user_can_cancel_task_offer_after_accepting_it(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Test user can cancel task after its been accepted."""
        accepted_user_client = create_authorized_client(user=test_user3)
        res = await accepted_user_client.put(
            app.url_path_for("assigns:cancel-task-from-user", todo_id=test_todo_with_accepted_task_offer.id)
        )
        assert res.status_code == status.HTTP_200_OK
        cancelled_task = TaskInDB(**res.json())
        assert cancelled_task.status == "cancelled"
        assert cancelled_task.user_id == test_user3.id
        assert cancelled_task.todo_id == test_todo_with_accepted_task_offer.id

    async def test_only_accepted_task_offers_can_be_cancelled(
        sefl,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user4: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Test only accpeted offers can be cancelled."""
        user_client = create_authorized_client(user=test_user4)
        res = await user_client.put(
            app.url_path_for("assigns:cancel-task-from-user", todo_id=test_todo_with_accepted_task_offer.id)
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_cancelling_task_offer_sets_all_others_to_pending(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Test cancelling task, set other existing offers to pending."""
        accepted_user_client = create_authorized_client(user=test_user3)
        res = await accepted_user_client.put(
            app.url_path_for("assigns:cancel-task-from-user", todo_id=test_todo_with_accepted_task_offer.id)
        )
        assert res.status_code == status.HTTP_200_OK
        tasks_repo = TasksRepository(app.state._db, app.state._redis)
        offers = await tasks_repo.list_offers_for_task(todo=test_todo_with_accepted_task_offer)
        for offer in offers:
            if offer.user_id == test_user3.id:
                assert offer.status == "cancelled"
            else:
                assert offer.status == "pending"


class TestRescindTasks:
    """Test users cancels tasks."""

    async def test_user_can_successfully_rescind_pending_task_offer(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user4: UserInDB,
        test_user_list: List[UserInDB],
        test_todo_with_tasks: TodoInDB,
    ) -> None:
        """After user rescind a pending task. It should not longer appear when listing task for todo."""
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.delete(
            app.url_path_for("assigns:rescind-task-from-user", todo_id=test_todo_with_tasks.id)
        )
        assert res.status_code == status.HTTP_200_OK
        tasks_repo = TasksRepository(app.state._db, app.state._redis)
        offers = await tasks_repo.list_offers_for_task(todo=test_todo_with_tasks)
        user_ids = [user.id for user in test_user_list]
        for offer in offers:
            assert offer.user_id in user_ids
            assert offer.user_id != test_user4.id

    async def test_users_cannot_rescind_accepted_task_offers(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Users cannot rescind an offer. They can only cancel it."""
        authorized_client = create_authorized_client(user=test_user3)
        res = await authorized_client.delete(
            app.url_path_for("assigns:rescind-task-from-user", todo_id=test_todo_with_accepted_task_offer.id)
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_users_cannot_rescind_cancelled_task_offers(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Cancelled offers should not be cancelled again."""
        authorized_client = create_authorized_client(user=test_user3)
        res = await authorized_client.put(
            app.url_path_for("assigns:cancel-task-from-user", todo_id=test_todo_with_accepted_task_offer.id)
        )
        assert res.status_code == status.HTTP_200_OK

        res = await authorized_client.delete(
            app.url_path_for("assigns:rescind-task-from-user", todo_id=test_todo_with_accepted_task_offer.id)
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_user_cannot_rescind_rejected_task_offers(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user4: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """If task offer for task is reject, user should not rescind it."""
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.delete(
            app.url_path_for("assigns:rescind-task-from-user", todo_id=test_todo_with_accepted_task_offer.id)
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
