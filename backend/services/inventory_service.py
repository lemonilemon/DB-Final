from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory import Ingredient, FridgeItem
from models.fridge import Fridge
from schemas.inventory import (
    IngredientCreateRequest,
    IngredientResponse,
    FridgeItemAddRequest,
    FridgeItemUpdateRequest,
    FridgeItemResponse,
    ConsumeRequest,
    ConsumeResponse,
)
from services.fridge_service import FridgeService


class InventoryService:
    """Service for inventory management operations."""

    # ========================================================================
    # Ingredient Management
    # ========================================================================

    @staticmethod
    async def create_ingredient(
        request: IngredientCreateRequest,
        session: AsyncSession
    ) -> Ingredient:
        """
        Create a new ingredient.

        Args:
            request: Ingredient creation data
            session: Database session

        Returns:
            Created Ingredient object

        Raises:
            HTTPException: If ingredient name already exists
        """
        # Check if ingredient name already exists
        existing = await session.execute(
            select(Ingredient).where(Ingredient.name == request.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Ingredient '{request.name}' already exists"
            )

        # Validate standard_unit
        valid_units = ["g", "ml", "pcs"]
        if request.standard_unit not in valid_units:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid standard_unit. Must be one of: {', '.join(valid_units)}"
            )

        # Create ingredient
        new_ingredient = Ingredient(
            name=request.name,
            standard_unit=request.standard_unit,
            shelf_life_days=request.shelf_life_days
        )
        session.add(new_ingredient)
        await session.commit()
        await session.refresh(new_ingredient)

        return new_ingredient

    @staticmethod
    async def get_all_ingredients(
        session: AsyncSession,
        search: str = None
    ) -> List[IngredientResponse]:
        """
        Get all ingredients, optionally filtered by search term.

        Args:
            session: Database session
            search: Optional search term for ingredient name

        Returns:
            List of ingredients
        """
        query = select(Ingredient).order_by(Ingredient.name)

        if search:
            query = query.where(Ingredient.name.ilike(f"%{search}%"))

        result = await session.execute(query)
        ingredients = result.scalars().all()

        return [IngredientResponse.model_validate(ing) for ing in ingredients]

    @staticmethod
    async def get_ingredient(
        ingredient_id: int,
        session: AsyncSession
    ) -> Ingredient:
        """
        Get ingredient by ID.

        Raises:
            HTTPException: If ingredient not found
        """
        result = await session.execute(
            select(Ingredient).where(Ingredient.ingredient_id == ingredient_id)
        )
        ingredient = result.scalar_one_or_none()

        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")

        return ingredient

    # ========================================================================
    # Fridge Item Management
    # ========================================================================

    @staticmethod
    async def add_item_to_fridge(
        fridge_id: UUID,
        request: FridgeItemAddRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> FridgeItem:
        """
        Add an ingredient to a fridge.

        Args:
            fridge_id: ID of the fridge
            request: Item data (ingredient_id, quantity, expiry_date)
            current_user_id: ID of current user (for permission check)
            session: Database session

        Returns:
            Created FridgeItem

        Raises:
            HTTPException: If no access, ingredient not found, or invalid data
        """
        # Check user has access to fridge
        await FridgeService._check_fridge_access(fridge_id, current_user_id, session)

        # Verify ingredient exists
        ingredient = await InventoryService.get_ingredient(request.ingredient_id, session)

        # Validate expiry date is in the future
        if request.expiry_date <= date.today():
            raise HTTPException(
                status_code=400,
                detail="Expiry date must be in the future"
            )

        # Create fridge item
        new_item = FridgeItem(
            fridge_id=fridge_id,
            ingredient_id=request.ingredient_id,
            quantity=request.quantity,
            entry_date=date.today(),
            expiry_date=request.expiry_date
        )
        session.add(new_item)
        await session.commit()
        await session.refresh(new_item)

        # Update meal plan statuses after inventory change
        from services.procurement_service import ProcurementService
        await ProcurementService.update_meal_plan_statuses(fridge_id, session)

        return new_item

    @staticmethod
    async def get_fridge_items(
        fridge_id: UUID,
        current_user_id: UUID,
        session: AsyncSession
    ) -> List[FridgeItemResponse]:
        """
        Get all items in a fridge, sorted by expiry date (FIFO order).

        Args:
            fridge_id: ID of the fridge
            current_user_id: ID of current user (for permission check)
            session: Database session

        Returns:
            List of fridge items with ingredient details, sorted by expiry (earliest first)
        """
        # Check user has access to fridge
        await FridgeService._check_fridge_access(fridge_id, current_user_id, session)

        # Query items with ingredient details, sorted by expiry date (FIFO)
        query = (
            select(FridgeItem, Ingredient)
            .join(Ingredient, FridgeItem.ingredient_id == Ingredient.ingredient_id)
            .where(FridgeItem.fridge_id == fridge_id)
            .order_by(FridgeItem.expiry_date.asc(), FridgeItem.entry_date.asc())
        )
        result = await session.execute(query)
        rows = result.all()

        # Build response with calculated fields
        today = date.today()
        items = []
        for fridge_item, ingredient in rows:
            days_until_expiry = (fridge_item.expiry_date - today).days

            items.append(
                FridgeItemResponse(
                    fridge_item_id=fridge_item.fridge_item_id,
                    fridge_id=fridge_item.fridge_id,
                    ingredient_id=ingredient.ingredient_id,
                    ingredient_name=ingredient.name,
                    standard_unit=ingredient.standard_unit,
                    quantity=fridge_item.quantity,
                    entry_date=fridge_item.entry_date,
                    expiry_date=fridge_item.expiry_date,
                    days_until_expiry=days_until_expiry
                )
            )

        return items

    @staticmethod
    async def update_fridge_item(
        fridge_id: UUID,
        item_id: int,
        request: FridgeItemUpdateRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> FridgeItem:
        """
        Update a fridge item's quantity or expiry date.

        Only owners can update items.
        """
        # Check user is owner
        await FridgeService._check_fridge_owner(fridge_id, current_user_id, session)

        # Get item
        result = await session.execute(
            select(FridgeItem).where(
                and_(
                    FridgeItem.fridge_item_id == item_id,
                    FridgeItem.fridge_id == fridge_id
                )
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found in this fridge")

        # Update fields if provided
        if request.quantity is not None:
            item.quantity = request.quantity
        if request.expiry_date is not None:
            if request.expiry_date <= date.today():
                raise HTTPException(
                    status_code=400,
                    detail="Expiry date must be in the future"
                )
            item.expiry_date = request.expiry_date

        session.add(item)
        await session.commit()
        await session.refresh(item)

        return item

    @staticmethod
    async def remove_fridge_item(
        fridge_id: UUID,
        item_id: int,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """
        Remove an item from a fridge.

        Members and owners can remove items.
        """
        # Check user has access
        await FridgeService._check_fridge_access(fridge_id, current_user_id, session)

        # Get item
        result = await session.execute(
            select(FridgeItem).where(
                and_(
                    FridgeItem.fridge_item_id == item_id,
                    FridgeItem.fridge_id == fridge_id
                )
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found in this fridge")

        # Delete item
        await session.delete(item)
        await session.commit()

        # Update meal plan statuses after inventory change
        from services.procurement_service import ProcurementService
        await ProcurementService.update_meal_plan_statuses(fridge_id, session)

    # ========================================================================
    # FIFO Consumption Logic
    # ========================================================================

    @staticmethod
    async def consume_ingredient(
        fridge_id: UUID,
        request: ConsumeRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> ConsumeResponse:
        """
        Consume an ingredient from the fridge using FIFO logic.

        FIFO Algorithm:
        1. Get all items of the ingredient sorted by expiry_date (earliest first)
        2. Consume from earliest expiring items first
        3. Update or delete items as quantities are consumed
        4. Return summary of consumption

        Args:
            fridge_id: ID of the fridge
            request: Consumption request (ingredient_id, quantity)
            current_user_id: ID of current user (for permission check)
            session: Database session

        Returns:
            ConsumeResponse with consumption details

        Raises:
            HTTPException: If insufficient quantity available
        """
        # Check user has access
        await FridgeService._check_fridge_access(fridge_id, current_user_id, session)

        # Get ingredient details
        ingredient = await InventoryService.get_ingredient(request.ingredient_id, session)

        # Get all items of this ingredient in the fridge, sorted by expiry (FIFO)
        query = (
            select(FridgeItem)
            .where(
                and_(
                    FridgeItem.fridge_id == fridge_id,
                    FridgeItem.ingredient_id == request.ingredient_id
                )
            )
            .order_by(FridgeItem.expiry_date.asc(), FridgeItem.entry_date.asc())
        )
        result = await session.execute(query)
        items = result.scalars().all()

        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"No {ingredient.name} found in this fridge"
            )

        # Calculate total available quantity
        total_available = sum(item.quantity for item in items)

        if total_available < request.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity. Requested: {request.quantity} {ingredient.standard_unit}, "
                       f"Available: {total_available} {ingredient.standard_unit}"
            )

        # FIFO Consumption: Consume from earliest expiring items first
        remaining_to_consume = request.quantity
        items_consumed_count = 0

        for item in items:
            if remaining_to_consume <= 0:
                break

            if item.quantity <= remaining_to_consume:
                # Consume entire item
                remaining_to_consume -= item.quantity
                await session.delete(item)
                items_consumed_count += 1
            else:
                # Partially consume item
                item.quantity -= remaining_to_consume
                remaining_to_consume = Decimal(0)
                session.add(item)
                items_consumed_count += 1

        await session.commit()

        # Update meal plan statuses after inventory change
        from services.procurement_service import ProcurementService
        await ProcurementService.update_meal_plan_statuses(fridge_id, session)

        # Calculate remaining quantity after consumption
        remaining_quantity = total_available - request.quantity

        return ConsumeResponse(
            ingredient_name=ingredient.name,
            requested_quantity=request.quantity,
            consumed_quantity=request.quantity,
            remaining_quantity=remaining_quantity,
            items_consumed=items_consumed_count,
            message=f"Successfully consumed {request.quantity} {ingredient.standard_unit} of {ingredient.name} using FIFO"
        )
