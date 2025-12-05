from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from core.dependencies import get_current_user_id
from schemas.inventory import (
    IngredientCreateRequest,
    IngredientResponse,
    FridgeItemAddRequest,
    FridgeItemUpdateRequest,
    FridgeItemResponse,
    ConsumeRequest,
    ConsumeResponse,
    MessageResponse,
)
from services.inventory_service import InventoryService


# ============================================================================
# Ingredient Router
# ============================================================================

ingredient_router = APIRouter(prefix="/api/ingredients", tags=["Ingredients"])


@ingredient_router.post(
    "",
    response_model=IngredientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ingredient"
)
async def create_ingredient(
    request: IngredientCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new ingredient.

    - **name**: Unique ingredient name
    - **standard_unit**: Must be 'g' (grams), 'ml' (milliliters), or 'pcs' (pieces)
    - **shelf_life_days**: Default shelf life in days
    """
    ingredient = await InventoryService.create_ingredient(request, session)
    return IngredientResponse.model_validate(ingredient)


@ingredient_router.get(
    "",
    response_model=List[IngredientResponse],
    summary="List all ingredients"
)
async def list_ingredients(
    search: Optional[str] = Query(None, description="Search by ingredient name"),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all ingredients, optionally filtered by search term.

    - Use **search** parameter to filter by ingredient name
    - Returns all ingredients sorted alphabetically
    """
    return await InventoryService.get_all_ingredients(session, search)


@ingredient_router.get(
    "/{ingredient_id}",
    response_model=IngredientResponse,
    summary="Get ingredient details"
)
async def get_ingredient(
    ingredient_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed information about a specific ingredient.
    """
    ingredient = await InventoryService.get_ingredient(ingredient_id, session)
    return IngredientResponse.model_validate(ingredient)


# ============================================================================
# Fridge Inventory Router
# ============================================================================

inventory_router = APIRouter(prefix="/api/fridges", tags=["Fridge Inventory"])


@inventory_router.post(
    "/{fridge_id}/items",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to fridge"
)
async def add_item_to_fridge(
    fridge_id: UUID,
    request: FridgeItemAddRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Add an ingredient to a fridge.

    - Must have access to the fridge (Owner or Member)
    - Specify quantity in the ingredient's **standard_unit**
    - Expiry date must be in the future
    - Multiple entries of the same ingredient with different expiry dates are allowed (for FIFO)
    """
    item = await InventoryService.add_item_to_fridge(
        fridge_id, request, current_user_id, session
    )

    # Get ingredient name for response
    ingredient = await InventoryService.get_ingredient(request.ingredient_id, session)

    return MessageResponse(
        message="Item added to fridge",
        detail=f"Added {request.quantity} {ingredient.standard_unit} of {ingredient.name}"
    )


@inventory_router.get(
    "/{fridge_id}/items",
    response_model=List[FridgeItemResponse],
    summary="List fridge items (FIFO order)"
)
async def list_fridge_items(
    fridge_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all items in a fridge.

    - Must have access to the fridge
    - **Sorted by expiry date** (earliest first) - FIFO order
    - Shows days until expiry for each item
    - Items expiring soon appear first
    """
    return await InventoryService.get_fridge_items(fridge_id, current_user_id, session)


@inventory_router.put(
    "/{fridge_id}/items/{item_id}",
    response_model=MessageResponse,
    summary="Update fridge item"
)
async def update_fridge_item(
    fridge_id: UUID,
    item_id: int,
    request: FridgeItemUpdateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Update a fridge item's quantity or expiry date.

    - **Only Owners** can update items
    - Can update quantity and/or expiry date
    """
    await InventoryService.update_fridge_item(
        fridge_id, item_id, request, current_user_id, session
    )

    return MessageResponse(
        message="Item updated successfully",
        detail=f"Updated item #{item_id}"
    )


@inventory_router.delete(
    "/{fridge_id}/items/{item_id}",
    response_model=MessageResponse,
    summary="Remove item from fridge"
)
async def remove_fridge_item(
    fridge_id: UUID,
    item_id: int,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Remove an item from the fridge.

    - Members and Owners can remove items
    - Completely removes the item entry
    """
    await InventoryService.remove_fridge_item(
        fridge_id, item_id, current_user_id, session
    )

    return MessageResponse(
        message="Item removed from fridge",
        detail=f"Removed item #{item_id}"
    )


@inventory_router.post(
    "/{fridge_id}/consume",
    response_model=ConsumeResponse,
    summary="Consume ingredient (FIFO)"
)
async def consume_ingredient(
    fridge_id: UUID,
    request: ConsumeRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Consume an ingredient from the fridge using **FIFO logic**.

    **FIFO Algorithm:**
    - Consumes from items with earliest expiry date first
    - Automatically manages multiple batches
    - Updates or removes items as they're consumed
    - Returns detailed consumption report

    **Example:**
    - Fridge has 500ml expiring Dec 10 and 1000ml expiring Dec 15
    - Consume 750ml → Uses all 500ml from Dec 10 + 250ml from Dec 15
    - Remaining: 750ml expiring Dec 15
    """
    return await InventoryService.consume_ingredient(
        fridge_id, request, current_user_id, session
    )
