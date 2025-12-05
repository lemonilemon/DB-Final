from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from core.dependencies import get_current_user_id
from schemas.fridge import (
    FridgeCreateRequest,
    FridgeUpdateRequest,
    FridgeBasicResponse,
    FridgeDetailResponse,
    AddMemberRequest,
    MessageResponse,
)
from services.fridge_service import FridgeService


router = APIRouter(prefix="/api/fridges", tags=["Fridges"])


@router.post(
    "",
    response_model=FridgeBasicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fridge"
)
async def create_fridge(
    request: FridgeCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new fridge.

    - The creator is automatically assigned as **Owner**
    - Owners can add/remove members and update fridge settings
    """
    fridge = await FridgeService.create_fridge(request, current_user_id, session)

    return FridgeBasicResponse(
        fridge_id=fridge.fridge_id,
        fridge_name=fridge.fridge_name,
        description=fridge.description,
        your_role="Owner"
    )


@router.get(
    "",
    response_model=List[FridgeBasicResponse],
    summary="List all your fridges"
)
async def list_fridges(
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all fridges that you have access to (as Owner or Member).

    - Returns your role in each fridge
    - Sorted by most recently updated first
    """
    return await FridgeService.get_user_fridges(current_user_id, session)


@router.get(
    "/{fridge_id}",
    response_model=FridgeDetailResponse,
    summary="Get fridge details"
)
async def get_fridge(
    fridge_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed information about a fridge, including all members.

    - You must have access to the fridge (Owner or Member)
    - Shows all members with their roles
    """
    return await FridgeService.get_fridge_detail(fridge_id, current_user_id, session)


@router.put(
    "/{fridge_id}",
    response_model=MessageResponse,
    summary="Update fridge information"
)
async def update_fridge(
    fridge_id: UUID,
    request: FridgeUpdateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Update fridge name and/or description.

    - **Only Owners** can update fridge information
    - Provide only the fields you want to update
    """
    updated_fridge = await FridgeService.update_fridge(
        fridge_id, request, current_user_id, session
    )

    return MessageResponse(
        message="Fridge updated successfully",
        detail=f"Updated '{updated_fridge.fridge_name}'"
    )


@router.post(
    "/{fridge_id}/members",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to the fridge"
)
async def add_member(
    fridge_id: UUID,
    request: AddMemberRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Add a user to the fridge with a specific role.

    - **Only Owners** can add members
    - Available roles: **Owner** or **Member**
    - Members can view and add items, Owners have full control
    """
    await FridgeService.add_member(fridge_id, request, current_user_id, session)

    return MessageResponse(
        message="Member added successfully",
        detail=f"User '{request.user_name}' added as {request.role}"
    )


@router.delete(
    "/{fridge_id}/members/{user_id}",
    response_model=MessageResponse,
    summary="Remove a member from the fridge"
)
async def remove_member(
    fridge_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Remove a user from the fridge.

    - **Only Owners** can remove members
    - Cannot remove the last Owner (must have at least one Owner)
    """
    await FridgeService.remove_member(fridge_id, user_id, current_user_id, session)

    return MessageResponse(
        message="Member removed successfully",
        detail="User access has been revoked"
    )


@router.delete(
    "/{fridge_id}",
    response_model=MessageResponse,
    summary="Delete a fridge"
)
async def delete_fridge(
    fridge_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a fridge permanently.

    - **Only Owners** can delete fridges
    - This will remove all associated data (members, items, etc.)
    - **This action cannot be undone**
    """
    await FridgeService.delete_fridge(fridge_id, current_user_id, session)

    return MessageResponse(
        message="Fridge deleted successfully",
        detail="All associated data has been removed"
    )
