"""Router for users."""
from typing import List

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.comments import CommentsRepository
from app.db.repositories.users import UsersRepository
from app.models.comment import CommentPublic
from app.models.token import AccessToken
from app.models.user import UserCreate, UserInDB, UserPublic, UserUpdate
from app.services import auth_service
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


@router.post("/", response_model=UserPublic, name="users:register-new-user", status_code=status.HTTP_201_CREATED)
async def register_new_user(
    new_user: UserCreate = Body(..., embed=True),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    """Register new user."""
    created_user = await user_repo.register_new_user(new_user=new_user)
    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=created_user), token_type="bearer"
    )
    return UserPublic(**created_user.copy(update={"access_token": access_token}).dict())


@router.post("/login/token/", response_model=AccessToken, name="users:login-email-and-password")
async def user_login_email_and_password(
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
) -> AccessToken:
    """Login new user and get access token."""
    user = await user_repo.authenticate_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenication unsuccessful",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = AccessToken(access_token=auth_service.create_access_token_for_user(user=user), token_type="bearer")
    return AccessToken(**access_token.dict())


@router.get("/me/", response_model=UserPublic, name="users:get-current-user")
async def get_current_user(current_user: UserInDB = Depends(get_current_active_user)) -> UserPublic:
    """Get current user logged in."""
    return UserPublic(**current_user.dict())


@router.put("/update/", response_model=UserPublic, name="users:update-own-detials")
async def update_own_details(
    user_update: UserUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    """Update user route."""
    updated_user_details = await user_repo.update_user_details(user_update=user_update, requesting_user=current_user)
    return UserPublic(**updated_user_details.dict())


@router.get("/me/send_verification_email/", name="users:send-email-verification")
async def send_email_verification(
    current_user: UserInDB = Depends(get_current_active_user),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> JSONResponse:
    """Send user verification email route."""
    sent_user = await user_repo.send_verification_email(requesting_user=current_user)
    if sent_user is None:
        content = {"message": f"Auth code already sent to {current_user.email}"}
    else:
        content = {"message": f"email has been sent  to {sent_user}"}
    return JSONResponse(status_code=200, content=content)


@router.get("/me/verify/{verification_code}/", response_model=UserPublic, name="users:email-verification")
async def verify_user(
    verification_code: str,
    current_user: UserInDB = Depends(get_current_active_user),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    """Update user route."""
    verified_user = await user_repo.verify_email(requesting_user=current_user, verification_code=verification_code)
    if not verified_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Verfication Code or Code expired")
    return UserPublic(**verified_user.dict())


@router.get("/comments/", response_model=List[CommentPublic], name="users:get-user-comments")
async def get_user_comments(
    current_user: UserInDB = Depends(get_current_active_user),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> List[CommentPublic]:
    """Get all user comments."""
    return await comments_repo.get_users_comments(requesting_user=current_user)
