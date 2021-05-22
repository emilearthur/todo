"""Confest module."""
import datetime
import os
import random
import warnings
from typing import Callable, List

import alembic
import pytest
from alembic.config import Config
from app.core.config import JWT_TOKEN_PREFIX, SECRET_KEY
from app.db.repositories.comments import CommentsRepository
from app.db.repositories.evaluations import EvaluationsRepository
from app.db.repositories.tasks import TasksRepository
from app.db.repositories.todos import TodosRepository
from app.db.repositories.users import UsersRepository
from app.models.comment import CommentCreate, CommentInDB
from app.models.evaluation import EvaluationCreate
from app.models.task import TaskCreate
from app.models.todo import TodoCreate, TodoInDB, TodoUpdate
from app.models.user import UserCreate, UserInDB
from app.services import auth_service
from asgi_lifespan import LifespanManager
from databases import Database
from fastapi import FastAPI
from httpx import AsyncClient
from redis.client import Redis


# apply migration at beginning and end of testing session
@pytest.fixture(scope="session")
def apply_migrations():
    """Handle db migrations."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


# create a new application for testing
@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    """Handle db migrations."""
    from app.api.server import get_application

    return get_application()


# getting db
@pytest.fixture
def db(app: FastAPI) -> Database:
    """Postgres db object."""
    return app.state._db


@pytest.fixture
def r_db(app: FastAPI) -> Database:
    """Redis database object."""
    return app.state._redis


# make requests in our test
@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Make request for test."""
    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"Content-Type": "application/json"},
        ) as client:
            yield client


@pytest.fixture
def new_todo():
    """Create todo."""
    return TodoCreate(
        name="test todo",
        notes="test notes",
        priority="critical",
        duedate=datetime.date.today(),
        as_task=False,
    )


@pytest.fixture
async def test_todo(db: Database, r_db: Redis, test_user: UserInDB) -> TodoInDB:
    """Create todo."""
    todo_repo = TodosRepository(db, r_db)
    new_todo = TodoCreate(
        name="test todo",
        notes="test notes",
        priority="critical",
        duedate=datetime.date.today(),
        as_task=False,
    )
    return await todo_repo.create_todo(new_todo=new_todo, requesting_user=test_user)


@pytest.fixture
async def test_todo_2(db: Database, r_db: Redis, test_user2: UserInDB) -> TodoInDB:
    """Create todo."""
    todo_repo = TodosRepository(db, r_db)
    new_todo = TodoCreate(
        name="test todo",
        notes="test notes",
        priority="critical",
        duedate=datetime.date.today(),
        as_task=False,
    )
    return await todo_repo.create_todo(new_todo=new_todo, requesting_user=test_user2)


@pytest.fixture
async def test_todo_astask(db: Database, r_db: Redis, test_user: UserInDB) -> TodoInDB:
    """Create todo as task."""
    todo_repo = TodosRepository(db, r_db)
    new_todo = TodoCreate(
        name="test todo3",
        notes="test notes3",
        priority="critical",
        duedate=datetime.date.today(),
        as_task=True,
    )
    return await todo_repo.create_todo(new_todo=new_todo, requesting_user=test_user)


@pytest.fixture
def new_comment(test_todo: TodoInDB):
    """Create comments."""
    return CommentCreate(body="test comments", todo_id=test_todo.id)


@pytest.fixture
def new_comment2(test_todo_2: TodoInDB):
    """Create comments."""
    return CommentCreate(body="test comments", todo_id=test_todo_2.id)


@pytest.fixture
async def test_comment(db: Database, r_db: Redis, test_user: UserInDB, test_todo: TodoInDB) -> CommentInDB:
    """Comments 1 to a todo."""
    comments_repo = CommentsRepository(db, r_db)
    new_comment = CommentCreate(body="test comments", todo_id=test_todo.id)
    return await comments_repo.create_comment(new_comment=new_comment, requesting_user=test_user)


@pytest.fixture
async def test_comment_2(db: Database, r_db: Redis, test_user: UserInDB, test_todo: TodoInDB) -> CommentInDB:
    """Comments 2 to a todo."""
    comments_repo = CommentsRepository(db, r_db)
    new_comment = CommentCreate(body="test comments", todo_id=test_todo.id)
    return await comments_repo.create_comment(new_comment=new_comment, requesting_user=test_user)


@pytest.fixture
def authorized_client(client: AsyncClient, test_user: UserInDB) -> AsyncClient:
    """Client with token assigned."""
    access_token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}",
    }
    return client


@pytest.fixture
async def test_todos_list(db: Database, r_db: Redis, test_user2: UserInDB) -> List[TodoInDB]:
    """List of todos."""
    todo_repo = TodosRepository(db, r_db)
    return [
        await todo_repo.create_todo(
            new_todo=TodoCreate(
                name=f"test todo {i}",
                notes="some notes",
                priority="critical",
                duedate=datetime.date.today(),
            ),
            requesting_user=test_user2,
        )
        for i in range(5)
    ]


@pytest.fixture
async def test_todos_list_as_task(db: Database, r_db: Redis, test_user2: UserInDB) -> List[TodoInDB]:
    """Todos for tasks."""
    todo_repo = TodosRepository(db, r_db)
    return [
        await todo_repo.create_todo(
            new_todo=TodoCreate(
                name=f"test todo {i}",
                notes="some notes",
                priority="critical",
                duedate=datetime.date.today(),
                as_task=True,
            ),
            requesting_user=test_user2,
        )
        for i in range(2)
    ]


@pytest.fixture
async def test_comment_list(
    db: Database, r_db: Redis, test_user2: UserInDB, test_todos_list: List[TodoInDB]
) -> List[CommentInDB]:
    """List of comments on a todo."""
    comments_repo = CommentsRepository(db, r_db)
    return [
        await comments_repo.create_comment(
            new_comment=CommentCreate(body=f"test comment {i}", todo_id=test_todos_list[i].id),
            requesting_user=test_user2,
        )
        for i in range(5)
    ]


@pytest.fixture
def create_authorized_client(client: AsyncClient) -> Callable:
    """Client with token assigned."""

    def _create_authorized_client(*, user: UserInDB) -> AsyncClient:
        access_token = auth_service.create_access_token_for_user(user=user, secret_key=str(SECRET_KEY))
        client.headers = {
            **client.headers,
            "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}",
        }
        return client

    return _create_authorized_client


async def user_fixture_helper(*, db: Database, r_db: Redis, new_user: UserCreate) -> UserInDB:
    """Func. helper to create user."""
    users_repo = UsersRepository(db, r_db)
    existing_user = await users_repo.get_user_by_email(email=new_user.email)
    if existing_user:
        return existing_user
    return await users_repo.register_new_user(new_user=new_user)


@pytest.fixture
async def test_user(db: Database, r_db: Redis) -> UserInDB:
    """User."""
    new_user = UserCreate(email="frederickauthur@hotmail.com", username="frederickauthur", password="mypassword")
    return await user_fixture_helper(db=db, r_db=r_db, new_user=new_user)


@pytest.fixture
async def test_user2(db: Database, r_db: Redis) -> UserInDB:
    """User number 2."""
    new_user = UserCreate(email="emilextrig@hotmail.com", username="emilextrig", password="somepassword")
    return await user_fixture_helper(db=db, r_db=r_db, new_user=new_user)


@pytest.fixture
async def test_user3(db: Database, r_db: Redis) -> UserInDB:
    """User number 3."""
    new_user = UserCreate(email="jojo@gmail.com", username="jojo", password="morepassword")
    return await user_fixture_helper(db=db, r_db=r_db, new_user=new_user)


@pytest.fixture
async def test_user4(db: Database, r_db: Redis) -> UserInDB:
    """User number 4."""
    new_user = UserCreate(email="akosua@hermail.com", username="akosua", password="moremorepassword")
    return await user_fixture_helper(db=db, r_db=r_db, new_user=new_user)


@pytest.fixture
async def test_user5(db: Database, r_db: Redis) -> UserInDB:
    """User number 5."""
    new_user = UserCreate(email="janet@jackson.com", username="janet", password="somorepassword")
    return await user_fixture_helper(db=db, r_db=r_db, new_user=new_user)


@pytest.fixture
async def test_user6(db: Database, r_db: Redis) -> UserInDB:
    """User number 6."""
    new_user = UserCreate(email="jay@cole.com", username="jaycole", password="jaycolepwd")
    return await user_fixture_helper(db=db, r_db=r_db, new_user=new_user)


@pytest.fixture
async def test_user_list(
    test_user3: UserInDB, test_user4: UserInDB, test_user5: UserInDB, test_user6: UserInDB
) -> List[UserInDB]:
    """List of Users."""
    return [test_user3, test_user4, test_user5, test_user6]


@pytest.fixture
async def test_todo_with_tasks(
    db: Database, r_db: Redis, test_user2: UserInDB, test_user_list: List[UserInDB]
) -> TodoInDB:
    """Todo with a task."""
    todos_repo = TodosRepository(db, r_db)
    tasks_repo = TasksRepository(db, r_db)

    new_todo = TodoCreate(
        name="todo with an offer",
        notes="some notes",
        priority="critical",
        duedate=datetime.date.today(),
    )
    created_todo = await todos_repo.create_todo(new_todo=new_todo, requesting_user=test_user2)
    for user in test_user_list:
        await tasks_repo.create_task_for_todo(new_task=TaskCreate(todo_id=created_todo.id, user_id=user.id))
    return created_todo


@pytest.fixture
async def test_todo_with_accepted_task_offer(
    db: Database, r_db: Redis, test_user2: UserInDB, test_user3: UserInDB, test_user_list: List[UserInDB]
) -> TodoInDB:
    """Creating todo with accepted task offer."""
    todos_repo = TodosRepository(db, r_db)
    tasks_repo = TasksRepository(db, r_db)

    new_todo = TodoCreate(
        name="todo with an offer",
        notes="some notes",
        priority="critical",
        duedate=datetime.date.today(),
    )
    created_todo = await todos_repo.create_todo(new_todo=new_todo, requesting_user=test_user2)

    tasks = []
    for user in test_user_list:
        tasks.append(
            await tasks_repo.create_task_for_todo(new_task=TaskCreate(todo_id=created_todo.id, user_id=user.id))
        )
    await tasks_repo.accept_offer_for_task(task=[task for task in tasks if task.user_id == test_user3.id][0])
    return created_todo


async def create_todo_with_evaluated_task_helper(
    db: Database,
    r_db: Redis,
    owner: UserInDB,
    tasktaker: UserInDB,
    todo_create: TodoCreate,
    evaluation_create: EvaluationCreate,
) -> TodoInDB:
    """Func. Helper to create todo with evaluated task."""
    todos_repo = TodosRepository(db, r_db)
    tasks_repo = TasksRepository(db, r_db)
    evals_repo = EvaluationsRepository(db, r_db)

    created_todo = await todos_repo.create_todo(new_todo=todo_create, requesting_user=owner)
    task = await tasks_repo.create_task_for_todo(new_task=TaskCreate(todo_id=created_todo.id, user_id=tasktaker.id))
    await tasks_repo.accept_offer_for_task(task=task)
    await evals_repo.create_evaluation_for_tasktaker(
        evaluation_create=evaluation_create, todo=created_todo, tasktaker=tasktaker
    )
    return created_todo


@pytest.fixture
async def test_list_of_todos_with_evaluated_task(
    db: Database,
    r_db: Redis,
    test_user2: UserInDB,
    test_user3: UserInDB,
) -> List[TodoInDB]:
    """Creating a list of todos with evaluted offers."""
    return [
        await create_todo_with_evaluated_task_helper(
            db=db,
            r_db=r_db,
            owner=test_user2,
            tasktaker=test_user3,
            todo_create=TodoCreate(
                name=f"todo with an offer {i}",
                notes=f"some notes {i}",
                priority="critical",
                duedate=datetime.date.today(),
            ),
            evaluation_create=EvaluationCreate(
                professionalism=random.randint(0, 5),
                completeness=random.randint(0, 5),
                efficiency=random.randint(0, 5),
                overall_rating=random.randint(0, 5),
                headline=f"testing some headline here - {i}",
                comment=f"testing some comment here - {i}",
            ),
        )
        for i in range(5)
    ]


@pytest.fixture
async def test_list_of_new_and_updated_todos(
    db: Database, r_db: Redis, test_user_list: List[UserInDB]
) -> List[TodoInDB]:
    """List of new and updated todos."""
    todos_repo = TodosRepository(db, r_db)
    new_todos = [
        await todos_repo.create_todo(
            new_todo=TodoCreate(
                name=f"test todo {i}",
                notes="some notes",
                priority="critical",
                duedate=datetime.date.today(),
                as_task=True,
            ),
            requesting_user=test_user_list[i % len(test_user_list)],
        )
        for i in range(50)
    ]
    for i, todo in enumerate(new_todos):
        if i % 4 == 0:
            updated_todo = await todos_repo.update_todos_by_id(
                todo=todo,
                todo_update=TodoUpdate(notes=f"Updated {todo.notes}", priority="high"),
            )
            new_todos[i] = updated_todo
    return new_todos


@pytest.fixture
async def test_list_of_new_and_updated_todos_0(
    db: Database, r_db: Redis, test_user_list: List[UserInDB]
) -> List[TodoInDB]:
    """List of new and updated todos."""
    todos_repo = TodosRepository(db, r_db)
    new_todos = [
        await todos_repo.create_todo(
            new_todo=TodoCreate(
                name=f"test todo {i}",
                notes="some notes",
                priority="critical",
                duedate=datetime.date.today(),
                as_task=False,
            ),
            requesting_user=test_user_list[i % len(test_user_list)],
        )
        for i in range(10)
    ]
    for i, todo in enumerate(new_todos):
        if i % 4 == 10:
            updated_todo = await todos_repo.update_todos_by_id(
                todo=todo,
                todo_update=TodoUpdate(notes=f"Updated {todo.notes}", priority="high"),
            )
            new_todos[i] = updated_todo
    return new_todos
