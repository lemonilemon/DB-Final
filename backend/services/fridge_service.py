from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.fridge import Fridge, FridgeAccess
from models.user import User
from schemas.fridge import (
    FridgeCreateRequest,
    FridgeUpdateRequest,
    FridgeBasicResponse,
    FridgeDetailResponse,
    FridgeMemberResponse,
    AddMemberRequest,
)
from core.config import FRIDGE_ROLE_OWNER, FRIDGE_ROLE_MEMBER


class FridgeService:
    """Service for fridge management operations."""

    @staticmethod
    async def create_fridge(
        request: FridgeCreateRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> Fridge:
        """
        Create a new fridge and assign the creator as Owner.

        Args:
            request: Fridge creation data
            current_user_id: ID of the user creating the fridge
            session: Database session

        Returns:
            Created Fridge object
        """
        # Create new fridge
        new_fridge = Fridge(
            fridge_name=request.fridge_name,
            description=request.description,
        )
        session.add(new_fridge)
        await session.flush()

        # Assign creator as Owner
        owner_access = FridgeAccess(
            user_id=current_user_id,
            fridge_id=new_fridge.fridge_id,
            access_role=FRIDGE_ROLE_OWNER
        )
        session.add(owner_access)
        await session.commit()
        await session.refresh(new_fridge)

        return new_fridge

    @staticmethod
    async def get_user_fridges(
        current_user_id: UUID,
        session: AsyncSession
    ) -> List[FridgeBasicResponse]:
        """
        Get all fridges that the user has access to.

        Args:
            current_user_id: ID of the current user
            session: Database session

        Returns:
            List of fridges with user's role in each
        """
        # Query fridges where user has access
        query = (
            select(Fridge, FridgeAccess.access_role)
            .join(FridgeAccess, Fridge.fridge_id == FridgeAccess.fridge_id)
            .where(FridgeAccess.user_id == current_user_id)
            .order_by(Fridge.fridge_name)
        )
        result = await session.execute(query)
        rows = result.all()

        # Build response list
        fridges = []
        for fridge, role in rows:
            fridges.append(
                FridgeBasicResponse(
                    fridge_id=fridge.fridge_id,
                    fridge_name=fridge.fridge_name,
                    description=fridge.description,
                    your_role=role
                )
            )

        return fridges

    @staticmethod
    async def get_fridge_detail(
        fridge_id: UUID,
        current_user_id: UUID,
        session: AsyncSession
    ) -> FridgeDetailResponse:
        """
        Get detailed fridge information including all members.

        Args:
            fridge_id: ID of the fridge
            current_user_id: ID of the current user (for permission check)
            session: Database session

        Returns:
            Detailed fridge information with members

        Raises:
            HTTPException: If fridge not found or user doesn't have access
        """
        # Check user has access to this fridge
        user_role = await FridgeService._check_fridge_access(
            fridge_id, current_user_id, session
        )

        # Get fridge
        fridge_result = await session.execute(
            select(Fridge).where(Fridge.fridge_id == fridge_id)
        )
        fridge = fridge_result.scalar_one_or_none()
        if not fridge:
            raise HTTPException(status_code=404, detail="Fridge not found")

        # Get all members with their info
        query = (
            select(User, FridgeAccess.access_role)
            .join(FridgeAccess, User.user_id == FridgeAccess.user_id)
            .where(FridgeAccess.fridge_id == fridge_id)
            .order_by(
                # Owners first, then by username
                FridgeAccess.access_role.desc(),
                User.user_name
            )
        )
        result = await session.execute(query)
        rows = result.all()

        members = []
        for user, role in rows:
            members.append(
                FridgeMemberResponse(
                    user_id=user.user_id,
                    user_name=user.user_name,
                    email=user.email,
                    role=role
                )
            )

        return FridgeDetailResponse(
            fridge_id=fridge.fridge_id,
            fridge_name=fridge.fridge_name,
            description=fridge.description,
            your_role=user_role,
            members=members
        )

    @staticmethod
    async def update_fridge(
        fridge_id: UUID,
        request: FridgeUpdateRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> Fridge:
        """
        Update fridge information. Only owners can update.

        Args:
            fridge_id: ID of the fridge to update
            request: Update data
            current_user_id: ID of the current user
            session: Database session

        Returns:
            Updated Fridge object

        Raises:
            HTTPException: If not owner or fridge not found
        """
        # Check user is owner
        await FridgeService._check_fridge_owner(
            fridge_id, current_user_id, session
        )

        # Get fridge
        fridge_result = await session.execute(
            select(Fridge).where(Fridge.fridge_id == fridge_id)
        )
        fridge = fridge_result.scalar_one_or_none()
        if not fridge:
            raise HTTPException(status_code=404, detail="Fridge not found")

        # Update fields if provided
        if request.fridge_name is not None:
            fridge.fridge_name = request.fridge_name
        if request.description is not None:
            fridge.description = request.description

        session.add(fridge)
        await session.commit()
        await session.refresh(fridge)

        return fridge

    @staticmethod
    async def add_member(
        fridge_id: UUID,
        request: AddMemberRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """
        Add a member to a fridge. Only owners can add members.

        Args:
            fridge_id: ID of the fridge
            request: Member to add (username and role)
            current_user_id: ID of the current user
            session: Database session

        Raises:
            HTTPException: If not owner, user not found, already member, or invalid role
        """
        # Check user is owner
        await FridgeService._check_fridge_owner(
            fridge_id, current_user_id, session
        )

        # Validate role
        if request.role not in [FRIDGE_ROLE_OWNER, FRIDGE_ROLE_MEMBER]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be '{FRIDGE_ROLE_OWNER}' or '{FRIDGE_ROLE_MEMBER}'"
            )

        # Find user by username
        user_result = await session.execute(
            select(User).where(User.user_name == request.user_name)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User '{request.user_name}' not found"
            )

        # Check if user already has access
        existing_access = await session.execute(
            select(FridgeAccess).where(
                and_(
                    FridgeAccess.fridge_id == fridge_id,
                    FridgeAccess.user_id == user.user_id
                )
            )
        )
        if existing_access.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"User '{request.user_name}' already has access to this fridge"
            )

        # Add access
        new_access = FridgeAccess(
            user_id=user.user_id,
            fridge_id=fridge_id,
            access_role=request.role
        )
        session.add(new_access)
        await session.commit()

    @staticmethod
    async def remove_member(
        fridge_id: UUID,
        user_id_to_remove: UUID,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """
        Remove a member from a fridge. Only owners can remove members.
        Cannot remove the last owner.

        Args:
            fridge_id: ID of the fridge
            user_id_to_remove: ID of the user to remove
            current_user_id: ID of the current user
            session: Database session

        Raises:
            HTTPException: If not owner, can't remove last owner, or member not found
        """
        # Check user is owner
        await FridgeService._check_fridge_owner(
            fridge_id, current_user_id, session
        )

        # Get the access record to remove
        access_result = await session.execute(
            select(FridgeAccess).where(
                and_(
                    FridgeAccess.fridge_id == fridge_id,
                    FridgeAccess.user_id == user_id_to_remove
                )
            )
        )
        access_to_remove = access_result.scalar_one_or_none()
        if not access_to_remove:
            raise HTTPException(
                status_code=404,
                detail="User is not a member of this fridge"
            )

        # If removing an owner, check if there are other owners
        if access_to_remove.access_role == FRIDGE_ROLE_OWNER:
            owner_count_result = await session.execute(
                select(FridgeAccess).where(
                    and_(
                        FridgeAccess.fridge_id == fridge_id,
                        FridgeAccess.access_role == FRIDGE_ROLE_OWNER
                    )
                )
            )
            owner_count = len(owner_count_result.all())

            if owner_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove the last owner of the fridge"
                )

        # Remove access
        await session.delete(access_to_remove)
        await session.commit()

    @staticmethod
    async def delete_fridge(
        fridge_id: UUID,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """
        Delete a fridge. Only owners can delete.

        Args:
            fridge_id: ID of the fridge to delete
            current_user_id: ID of the current user
            session: Database session

        Raises:
            HTTPException: If not owner or fridge not found
        """
        # Check user is owner
        await FridgeService._check_fridge_owner(
            fridge_id, current_user_id, session
        )

        # Get fridge
        fridge_result = await session.execute(
            select(Fridge).where(Fridge.fridge_id == fridge_id)
        )
        fridge = fridge_result.scalar_one_or_none()
        if not fridge:
            raise HTTPException(status_code=404, detail="Fridge not found")

        # Delete fridge (cascade will handle fridge_access)
        await session.delete(fridge)
        await session.commit()

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    async def _check_fridge_access(
        fridge_id: UUID,
        user_id: UUID,
        session: AsyncSession
    ) -> str:
        """
        Check if user has access to a fridge and return their role.

        Returns:
            User's role (Owner or Member)

        Raises:
            HTTPException: If user doesn't have access
        """
        access_result = await session.execute(
            select(FridgeAccess).where(
                and_(
                    FridgeAccess.fridge_id == fridge_id,
                    FridgeAccess.user_id == user_id
                )
            )
        )
        access = access_result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this fridge"
            )

        return access.access_role

    @staticmethod
    async def _check_fridge_owner(
        fridge_id: UUID,
        user_id: UUID,
        session: AsyncSession
    ) -> None:
        """
        Check if user is an owner of the fridge.

        Raises:
            HTTPException: If user is not an owner
        """
        role = await FridgeService._check_fridge_access(
            fridge_id, user_id, session
        )

        if role != FRIDGE_ROLE_OWNER:
            raise HTTPException(
                status_code=403,
                detail="Only fridge owners can perform this action"
            )
