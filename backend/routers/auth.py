from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse
)
from services.auth_service import AuthService
from services.behavior_service import BehaviorService

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password."
)
async def register(
    request: UserRegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user.

    - **user_name**: Unique username (3-20 characters, alphanumeric + underscore)
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)

    Returns a success message upon registration.
    """
    user = await AuthService.register_user(request, session)

    return MessageResponse(
        message="User registered successfully",
        detail=f"Welcome, {user.user_name}!"
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access token",
    description="Authenticate with username and password to receive a JWT token."
)
async def login(
    request: UserLoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Authenticate user and get access token.

    - **user_name**: Your username
    - **password**: Your password

    Returns:
    - **access_token**: JWT token for authenticated requests
    - **token_type**: Token type (bearer)
    - **user_id**: Your user ID
    - **user_name**: Your username
    - **roles**: Your assigned roles

    Use the access token in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    token_response = await AuthService.authenticate_user(request, session)

    # Log login action
    await BehaviorService.log_user_action(
        action_type="login",
        user_id=token_response.user_id,
        metadata={
            "user_name": token_response.user_name,
            "roles": token_response.roles
        }
    )

    return token_response
