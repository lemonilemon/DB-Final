from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from core.dependencies import get_current_user_id
from schemas.procurement import (
    PartnerCreateRequest,
    PartnerResponse,
    ExternalProductCreateRequest,
    ExternalProductResponse,
    ShoppingListAddRequest,
    ShoppingListItemResponse,
    OrderResponse,
    CreateOrdersResponse,
    OrderUpdateStatusRequest,
    MessageResponse,
)
from services.procurement_service import ProcurementService


# ============================================================================
# Partner Router
# ============================================================================

partner_router = APIRouter(prefix="/api/partners", tags=["Partners"])


@partner_router.post(
    "",
    response_model=PartnerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new partner"
)
async def create_partner(
    request: PartnerCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new partner (supplier/store).

    - **partner_name**: Name of the store/supplier
    - **contract_date**: Partnership start date
    - **avg_shipping_days**: Average delivery time
    - **credit_score**: Reliability rating (0-100)
    """
    partner = await ProcurementService.create_partner(request, session)
    return PartnerResponse.model_validate(partner)


@partner_router.get(
    "",
    response_model=List[PartnerResponse],
    summary="List all partners"
)
async def list_partners(
    session: AsyncSession = Depends(get_session)
):
    """Get all partners/suppliers."""
    return await ProcurementService.get_all_partners(session)


# ============================================================================
# External Product Router
# ============================================================================

product_router = APIRouter(prefix="/api/products", tags=["External Products"])


@product_router.post(
    "",
    response_model=ExternalProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create external product"
)
async def create_product(
    request: ExternalProductCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new external product (links ingredient to partner with price).

    - **external_sku**: Unique product identifier
    - **partner_id**: Which partner sells this
    - **ingredient_id**: Which ingredient this represents
    - **current_price**: Current selling price
    - **selling_unit**: How it's sold (e.g., "1L Bottle", "6-Pack")
    """
    product = await ProcurementService.create_external_product(request, session)

    # Get full response with partner/ingredient details
    products = await ProcurementService.get_external_products(session)
    created = next(p for p in products if p.external_sku == product.external_sku)
    return created


@product_router.get(
    "",
    response_model=List[ExternalProductResponse],
    summary="List external products"
)
async def list_products(
    ingredient_id: Optional[int] = Query(None, description="Filter by ingredient"),
    partner_id: Optional[int] = Query(None, description="Filter by partner"),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all external products with optional filters.

    - Filter by ingredient to see all stores selling it
    - Filter by partner to see their catalog
    - No filters = all products
    """
    return await ProcurementService.get_external_products(
        session, ingredient_id, partner_id
    )


# ============================================================================
# Shopping List Router
# ============================================================================

shopping_list_router = APIRouter(prefix="/api/shopping-list", tags=["Shopping List"])


@shopping_list_router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to shopping list"
)
async def add_to_shopping_list(
    request: ShoppingListAddRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Add or update item in your shopping list (cart).

    - If ingredient already in list, updates quantity
    - Quantity is in the ingredient's standard unit
    """
    await ProcurementService.add_to_shopping_list(request, current_user_id, session)

    return MessageResponse(
        message="Item added to shopping list",
        detail=f"Added ingredient #{request.ingredient_id}"
    )


@shopping_list_router.get(
    "",
    response_model=List[ShoppingListItemResponse],
    summary="View shopping list"
)
async def get_shopping_list(
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Get your shopping list.

    - Shows how many products are available for each ingredient
    - Ready to be converted into orders
    """
    return await ProcurementService.get_shopping_list(current_user_id, session)


@shopping_list_router.delete(
    "/{ingredient_id}",
    response_model=MessageResponse,
    summary="Remove item from shopping list"
)
async def remove_from_shopping_list(
    ingredient_id: int,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Remove an ingredient from your shopping list."""
    await ProcurementService.remove_from_shopping_list(
        ingredient_id, current_user_id, session
    )

    return MessageResponse(
        message="Item removed from shopping list",
        detail=f"Removed ingredient #{ingredient_id}"
    )


# ============================================================================
# Order Router
# ============================================================================

order_router = APIRouter(prefix="/api/orders", tags=["Orders"])


@order_router.post(
    "/create-from-list",
    response_model=CreateOrdersResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create orders from shopping list (SPLIT BY PARTNER)"
)
async def create_orders_from_shopping_list(
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Convert shopping list into orders with **automatic split-by-partner logic**.

    **How it works:**
    1. For each ingredient in your shopping list, finds cheapest product
    2. **Automatically groups products by partner**
    3. **Creates one order per partner** (split orders!)
    4. Saves price snapshots (deal_price)
    5. Calculates delivery dates
    6. Clears your shopping list

    **Example:**
    - Shopping list: Milk, Eggs, Bread
    - Milk cheapest at FreshMart
    - Eggs & Bread cheapest at SuperStore
    - **Result: 2 orders** (one to FreshMart, one to SuperStore)
    """
    return await ProcurementService.create_orders_from_shopping_list(
        current_user_id, session
    )


@order_router.get(
    "",
    response_model=List[OrderResponse],
    summary="View your orders"
)
async def get_orders(
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all your orders sorted by date (newest first).

    - Shows order details, items, and status
    - Includes expected arrival dates
    """
    return await ProcurementService.get_user_orders(current_user_id, session)


@order_router.put(
    "/{order_id}/status",
    response_model=MessageResponse,
    summary="Update order status"
)
async def update_order_status(
    order_id: int,
    request: OrderUpdateStatusRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Update the status of your order.

    Valid statuses: Pending, Processing, Shipped, Delivered, Cancelled
    """
    await ProcurementService.update_order_status(
        order_id, request, current_user_id, session
    )

    return MessageResponse(
        message="Order status updated",
        detail=f"Order #{order_id} status: {request.order_status}"
    )
