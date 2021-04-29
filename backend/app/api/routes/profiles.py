"""Routes for profile."""
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.profiles import ProfilesRepository
from app.models.profile import ProfilePublic, ProfileUpdate
from app.models.user import UserInDB

router = APIRouter()


@router.get("/{username}/", response_model=ProfilePublic, name="profiles:get-profile-by-username")
async def get_profile_by_username(*, username: str = Path(...,
                                  min_length=3, regex="^[a-zA-Z0-9_-]+$"),
                                  current_user: UserInDB = Depends(get_current_active_user),
                                  profile_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository))
                                  ) -> ProfilePublic:
    """Get profile by username route."""
    profile = await profile_repo.get_profile_by_username(username=username)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile found with that username.")
    return ProfilePublic(**profile.dict())


@router.put("/me/", response_model=ProfilePublic, name="profiles:update-own-profile")
async def update_own_profile(profile_update: ProfileUpdate = Body(..., embed=True),
                             current_user: UserInDB = Depends(get_current_active_user),
                             profile_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
                             ) -> ProfilePublic:
    """Upate pofile route."""
    updated_profile = await profile_repo.update_profile(profile_update=profile_update, requesting_user=current_user)
    return ProfilePublic(**updated_profile.dict())
