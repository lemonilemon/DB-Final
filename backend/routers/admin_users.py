"""
Admin endpoints for user management and role assignment.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_session
from core.dependencies import require_admin
from models.user import User, UserRoleEnum
from schemas.auth import UserResponse, MessageResponse
from core.config import USER_ROLE_ADMIN, USER_ROLE_USER, USER_STATUS_ACTIVE, USER_STATUS_DISABLED


router = APIRouter(prefix="/api/admin/users", tags=["Admin - Users"])


# ============================================================================
# User Management
# ============================================================================

@router.get(
    "",
    response_model=List[UserResponse],
    summary="[Admin] List all users"
)
async def get_all_users(
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    **[Admin Only]** Get a list of all users in the system.

    Returns user details including ID, username, email, status, and role.
    """
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    return [
        UserResponse(
            user_id=user.user_id,
            user_name=user.user_name,
            email=user.email,
            status=user.status,
            role=user.role
        )
        for user in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Get user details"
)
async def get_user_by_id(
    user_id: UUID,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    **[Admin Only]** Get detailed information about a specific user.
    """
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=user.user_id,
        user_name=user.user_name,
        email=user.email,
        status=user.status,
        role=user.role
    )


@router.put(
    "/{user_id}/status",
    response_model=MessageResponse,
    summary="[Admin] Update user status"
)
async def update_user_status(
    user_id: UUID,
    new_status: str,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    **[Admin Only]** Enable or disable a user account.

    Valid statuses:
    - Active
    - Disabled
    """
    if new_status not in [USER_STATUS_ACTIVE, USER_STATUS_DISABLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be '{USER_STATUS_ACTIVE}' or '{USER_STATUS_DISABLED}'"
        )

    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = new_status
    session.add(user)
    await session.commit()

    return MessageResponse(
        message=f"User status updated to {new_status}",
        detail=f"User '{user.user_name}' is now {new_status}"
    )


# ============================================================================
# Role Management
# ============================================================================

@router.post(
    "/{user_id}/roles/{role_name}",
    response_model=MessageResponse,
    summary="[Admin] Set user role"
)
async def grant_role(
    user_id: UUID,
    role_name: str,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    **[Admin Only]** Set a user's role.

    Valid roles:
    - User (default, standard user)
    - Admin (grants administrative privileges)

    Example: To make a user an admin, POST to `/api/admin/users/{user_id}/roles/Admin`
    """
    # Validate role
    if role_name not in [USER_ROLE_USER, USER_ROLE_ADMIN]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be '{USER_ROLE_USER}' or '{USER_ROLE_ADMIN}'"
        )

    # Verify user exists
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user already has this role
    if user.role == role_name:
        raise HTTPException(
            status_code=400,
            detail=f"User already has role '{role_name}'"
        )

    # Update role
    user.role = role_name
    session.add(user)
    await session.commit()

    return MessageResponse(
        message=f"Role '{role_name}' granted successfully",
        detail=f"User '{user.user_name}' now has role '{role_name}'"
    )


@router.delete(
    "/{user_id}/roles/{role_name}",
    response_model=MessageResponse,
    summary="[Admin] Revoke admin role"
)
async def revoke_role(
    user_id: UUID,
    role_name: str,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    **[Admin Only]** Revoke admin role from a user (demote to User).

    Note: Can only revoke 'Admin' role. Users always have at least 'User' role.
    """
    # Verify user exists
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Can only revoke Admin role
    if role_name != USER_ROLE_ADMIN:
        raise HTTPException(
            status_code=400,
            detail="Can only revoke 'Admin' role. Users always have at least 'User' role."
        )

    # Check if user has Admin role
    if user.role != USER_ROLE_ADMIN:
        raise HTTPException(
            status_code=400,
            detail=f"User does not have '{role_name}' role"
        )

    # Demote to User
    user.role = USER_ROLE_USER
    session.add(user)
    await session.commit()

    return MessageResponse(
        message=f"Role '{role_name}' revoked successfully",
        detail=f"User '{user.user_name}' demoted to '{USER_ROLE_USER}'"
    )


@router.get(
    "/{user_id}/role",
    response_model=str,
    summary="[Admin] Get user role"
)
async def get_user_role(
    user_id: UUID,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    **[Admin Only]** Get the role assigned to a user.
    """
    # Verify user exists
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.role
