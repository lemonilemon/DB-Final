from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from core.security import get_user_id_from_token
from services.auth_service import AuthService
from models import User
from core.config import USER_STATUS_ACTIVE, USER_ROLE_ADMIN

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """
    Extract and validate user ID from JWT token.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        User UUID if token is valid

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    user_id = get_user_id_from_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Get current authenticated user from database.

    Args:
        user_id: User ID from token
        session: Database session

    Returns:
        User object

    Raises:
        HTTPException: If user not found or account disabled
    """
    user = await AuthService.get_user_by_id(user_id, session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != USER_STATUS_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Alias for get_current_user for clarity.
    Ensures user is authenticated and active.

    Usage in routes:
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_active_user)
        ):
            return {"user": current_user.user_name}
    """
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Require user to have Admin role.

    Usage in routes:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            admin_user: User = Depends(require_admin)
        ):
            # Only admins can access this
            ...
    """
    roles = await AuthService.get_user_roles(current_user.user_id, session)

    if USER_ROLE_ADMIN not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


# Optional: Get user if token is provided, None otherwise
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """
    Get user if authenticated, None otherwise.
    Useful for routes that work differently for authenticated vs anonymous users.

    Usage:
        @router.get("/recipes")
        async def list_recipes(
            user: Optional[User] = Depends(get_optional_user)
        ):
            # Show public recipes + user's private recipes if authenticated
            ...
    """
    if credentials is None:
        return None

    user_id = get_user_id_from_token(credentials.credentials)
    if user_id is None:
        return None

    user = await AuthService.get_user_by_id(user_id, session)
    return user if user and user.status == USER_STATUS_ACTIVE else None
