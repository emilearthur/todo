import pytest

from databases import Database

from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.user import UserInDB, UserPublic
from app.models.profile import ProfileInDB, ProfilePublic

from app.db.repositories.profiles import ProfilesRepository

pytestmark = pytest.mark.asyncio


class TestProfileRoutes:
    async def test_routes_exists(self, app: FastAPI,
                                 client: AsyncClient,
                                 test_user: UserInDB) -> None:
        res = await client.get(app.url_path_for("profiles:get-profile-by-username",
                                                username=test_user.username))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        # update profile
        res = await client.put(app.url_path_for("profiles:update-own-profile"),
                               json={"profile_update": {}})
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestProfileCreate:
    async def test_profile_created_for_new_user(self, app: FastAPI,
                                                client: AsyncClient,
                                                db: Database) -> None:
        profiles_repo = ProfilesRepository(db)

        new_user = {"email": "frederick@emile.com", "username": "frederickemile", "password": "xxxxemile"}
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status.HTTP_201_CREATED

        created_user = UserPublic(**res.json())
        user_profile = await profiles_repo.get_profile_by_user_id(user_id=created_user.id)
        assert user_profile is not None
        assert isinstance(user_profile, ProfileInDB)


class TestProfileView:
    async def test_authenticated_user_can_view_other_users_profile(self, app: FastAPI,
                                                                   authorized_client: AsyncClient,
                                                                   test_user: UserInDB,
                                                                   test_user2: UserInDB,) -> None:
        res = await authorized_client.get(app.url_path_for("profiles:get-profile-by-username",
                                                           username=test_user2.username))
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert profile.username == test_user2.username

    async def test_unauthenticated_user_cannot_view_oter_users_profile(self, app: FastAPI,
                                                                       client: AsyncClient,
                                                                       test_user2: UserInDB,) -> None:
        res = await client.get(app.url_path_for("profiles:get-profile-by-username",
                                                username=test_user2.username))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_no_profile_when_user_does_not_exist(self, app: FastAPI,
                                                       authorized_client: AsyncClient,) -> None:
        res = await authorized_client.get(app.url_path_for("profiles:get-profile-by-username",
                                                           username="somename"))
        assert res.status_code == status.HTTP_404_NOT_FOUND


class TestProfileManagement:
    @pytest.mark.parametrize(
        "attr, value",
        (
            ("firstname", "Peter"),
            ("lastname", "BondzieArthur"),
            ("middlename", "Emile"),
            ("phone_number", "555-333-1000"),
            ("bio", "this is my bio for now"),
            ("image", "http://testimages.com/testimage"),
        ),
    )
    async def test_user_can_update_own_profile(self, app: FastAPI,
                                               authorized_client: AsyncClient,
                                               test_user: UserInDB,
                                               attr: str,
                                               value: str,) -> None:
        assert getattr(test_user.profile, attr) != value
        res = await authorized_client.put(app.url_path_for("profiles:update-own-profile"),
                                          json={"profile_update": {attr: value}},)
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert getattr(profile, attr) == value

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("firstname", [], 422),
            ("lastname", [], 422),
            ("middlename", [], 422),
            ("bio", {}, 422),
            ("image", "./image-string.png", 422),
            ("image", 5, 422),
        ),
    )
    async def test_user_gets_error_for_invalid_params(self, app: FastAPI,
                                                      authorized_client: AsyncClient,
                                                      test_user: UserInDB,
                                                      attr: str,
                                                      value: str,
                                                      status_code: int,) -> None:
        res = await authorized_client.put(app.url_path_for("profiles:update-own-profile"),
                                          json={"profile_update": {attr: value}},)
        assert res.status_code == status_code
