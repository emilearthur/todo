"""DB repo for profile."""
from app.db.repositories.base import BaseRepository
from app.models.profile import ProfileCreate, ProfileInDB, ProfileUpdate
from app.models.user import UserInDB

CREATE_PROFILE_FOR_USER_QUERY = """
    INSERT INTO profiles (firstname, lastname, middlename, phone_number, bio, image, user_id)
    VALUES (:firstname, :lastname, :middlename, :phone_number, :bio, :image, :user_id)
    RETURNING id, firstname, lastname, middlename, phone_number, bio, image, user_id, created_at, updated_at;
"""

GET_PROFILE_BY_USER_ID_QUERY = """
    SELECT id, firstname, lastname, middlename, phone_number, bio, image, user_id, created_at, updated_at
    FROM profiles
    WHERE user_id = :user_id;
"""

GET_PROFILE_BY_USERNAME_QUERY = """
    SELECT  p.id, u.email AS email, u.username as username, firstname, lastname, middlename, phone_number, bio, image,
            user_id, p.created_at, p.updated_at
    FROM    profiles AS p
            INNER JOIN users AS u
            ON p.user_id = u.id
    WHERE   user_id = (SELECT id FROM users WHERE username = :username)
"""

UPDATE_PROFILE_QUERY = """
    UPDATE profiles
    SET firstname       = :firstname,
        lastname        = :lastname,
        middlename      = :middlename,
        phone_number    = :phone_number,
        bio             = :bio,
        image           = :image
    WHERE user_id = :user_id
    RETURNING id, firstname, lastname, middlename, phone_number, bio, image, user_id, created_at, updated_at;
"""


class ProfilesRepository(BaseRepository):
    """All db actions associated with the Profile resources."""

    async def create_profile_for_user(self, *, profile_create: ProfileCreate) -> ProfileInDB:
        """Create profile for user."""
        created_profile = await self.db.fetch_one(query=CREATE_PROFILE_FOR_USER_QUERY, values=profile_create.dict())
        return ProfileInDB(**created_profile)

    async def get_profile_by_user_id(self, *, user_id: int) -> ProfileInDB:
        """Get user profile by user_id."""
        profile = await self.db.fetch_one(query=GET_PROFILE_BY_USER_ID_QUERY, values={"user_id": user_id})
        if not profile:
            return None
        return ProfileInDB(**profile)

    async def get_profile_by_username(self, *, username: str) -> ProfileInDB:
        """Get user profile by user_name."""
        profile = await self.db.fetch_one(query=GET_PROFILE_BY_USERNAME_QUERY, values={"username": username})
        if profile:
            return ProfileInDB(**profile)

    async def update_profile(self, *, profile_update: ProfileUpdate, requesting_user: UserInDB) -> ProfileInDB:
        """Update user proile."""
        profile = await self.get_profile_by_user_id(user_id=requesting_user.id)
        update_params = profile.copy(update=profile_update.dict(exclude_unset=True))
        updated_profile = await self.db.fetch_one(
            query=UPDATE_PROFILE_QUERY,
            values=update_params.dict(exclude={"id", "created_at", "updated_at", "username", "email"}),
        )
        return ProfileInDB(**updated_profile)
