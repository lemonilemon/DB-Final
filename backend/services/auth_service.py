from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models import User
from core.security import hash_password, verify_password, create_access_token
from core.config import USER_STATUS_ACTIVE, USER_ROLE_USER
from schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse


class AuthService:
    """
    Authentication service for user registration and login.
    """

    @staticmethod
    async def register_user(
        request: UserRegisterRequest,
        session: AsyncSession
    ) -> User:
        """
        Register a new user.

        Args:
            request: User registration data
            session: Database session

        Returns:
            Created user object

        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username already exists
        stmt = select(User).where(User.user_name == request.user_name)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email already exists
        stmt = select(User).where(User.email == request.email)
        result = await session.execute(stmt)
        existing_email = result.scalar_one_or_none()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user (role defaults to "User" in model)
        hashed_password = hash_password(request.password)
        new_user = User(
            user_name=request.user_name,
            email=request.email,
            password=hashed_password,
            status=USER_STATUS_ACTIVE,
            role=USER_ROLE_USER  # Default role
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return new_user

    @staticmethod
    async def authenticate_user(
        request: UserLoginRequest,
        session: AsyncSession
    ) -> TokenResponse:
        """
        Authenticate user and generate JWT token.

        Args:
            request: Login credentials
            session: Database session

        Returns:
            Token response with JWT and user info

        Raises:
            HTTPException: If credentials are invalid or user is disabled
        """
        # Find user by username
        stmt = select(User).where(User.user_name == request.user_name)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if user.status != USER_STATUS_ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        # Create access token with user role
        token_data = {
            "sub": str(user.user_id),
            "username": user.user_name,
            "role": user.role
        }
        access_token = create_access_token(data=token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id,
            user_name=user.user_name,
            role=user.role
        )

    @staticmethod
    async def get_user_by_id(
        user_id: UUID,
        session: AsyncSession
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID
            session: Database session

        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_role(
        user_id: UUID,
        session: AsyncSession
    ) -> Optional[str]:
        """
        Get role for a user.

        Args:
            user_id: User UUID
            session: Database session

        Returns:
            User's role (User or Admin)
        """
        user = await AuthService.get_user_by_id(user_id, session)
        return user.role if user else None
