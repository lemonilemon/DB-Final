from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from core.dependencies import get_current_user_id, require_admin
from models.user import User
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
    AvailabilityCheckResponse,
    ProductRecommendationsResponse,
    CreateOrderRequest,
)
from services.procurement_service import ProcurementService
from services.behavior_service import BehaviorService


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


@product_router.get(
    "/recommendations",
    response_model=ProductRecommendationsResponse,
    summary="Get product recommendations with delivery validation"
)
async def get_product_recommendations(
    ingredient_id: int = Query(..., description="Ingredient to buy"),
    quantity_needed: Decimal = Query(..., gt=0, description="Quantity needed"),
    needed_by: date = Query(..., description="Date when ingredient is needed"),
    session: AsyncSession = Depends(get_session)
):
    """
    Get product recommendations for an ingredient with delivery date validation.

    **Returns:**
    - All products that sell this ingredient
    - Expected arrival date (today + avg_shipping_days)
    - Whether each product arrives in time (expected_arrival <= needed_by)
    - Recommended option (cheapest that arrives in time)

    **Example:**
    - Need 500ml milk by Dec 15
    - FreshMart: $45, arrives Dec 9 (2 days) ✓ In time
    - SuperStore: $42, arrives Dec 10 (3 days) ✓ In time (RECOMMENDED - cheapest)
    - SlowMart: $40, arrives Dec 20 (13 days) ✗ Too late
    """
    return await ProcurementService.get_product_recommendations(
        ingredient_id, quantity_needed, needed_by, session
    )


# ============================================================================
# Availability Check Router
# ============================================================================

availability_router = APIRouter(prefix="/api/availability", tags=["Availability Check"])


@availability_router.get(
    "/check",
    response_model=AvailabilityCheckResponse,
    summary="Check ingredient availability for recipe"
)
async def check_availability(
    recipe_id: int = Query(..., description="Recipe to check"),
    fridge_id: UUID = Query(..., description="Fridge to check"),
    needed_by: date = Query(..., description="Date when ingredients are needed"),
    session: AsyncSession = Depends(get_session)
):
    """
    Check if all ingredients for a recipe are available in the fridge.

    **Considers:**
    - Current fridge inventory
    - Expiration dates (items expiring before needed_by are excluded)
    - Future consumption (TODO: subtract ingredients from other meal plans)

    **Use cases:**
    - Frontend calls this when creating a meal plan
    - Frontend calls this after consuming/removing items
    - Shows what needs to be ordered

    **Example:**
    - Meal plan for Dec 15
    - Recipe needs 500ml milk, 4 eggs
    - Fridge has 200ml milk (expires Dec 12), 6 eggs (expires Dec 20)
    - Result: Milk insufficient (need 300ml more)
    """
    return await ProcurementService.check_recipe_availability(
        recipe_id, fridge_id, needed_by, session
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
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order with user-selected products"
)
async def create_order(
    request: CreateOrderRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create an order with user-selected products.

    **Frontend-driven workflow:**
    1. Frontend checks availability (GET /api/availability/check)
    2. Frontend gets recommendations (GET /api/products/recommendations)
    3. User selects which products to order
    4. Frontend calls this endpoint with selected products

    **Example:**
    ```json
    {
      "fridge_id": "123...",
      "items": [
        {"external_sku": "FM-MILK-1L", "quantity": 2},
        {"external_sku": "SS-EGGS-12", "quantity": 1}
      ]
    }
    ```

    **Result:**
    - Creates ONE order with all selected products
    - Saves price snapshots (deal_price)
    - Calculates expected delivery date
    """
    order = await ProcurementService.create_order(request, current_user_id, session)

    # Log order creation
    await BehaviorService.log_user_action(
        action_type="create_order",
        user_id=current_user_id,
        resource_type="order",
        resource_id=str(order.order_id),
        metadata={
            "partner_id": order.partner_id,
            "partner_name": order.partner_name,
            "total_price": str(order.total_price),
            "items_count": len(order.items),
            "fridge_id": str(request.fridge_id)
        }
    )

    return order


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


# ============================================================================
# Admin Order Router (Admin-only operations)
# ============================================================================

admin_order_router = APIRouter(prefix="/api/admin/orders", tags=["Admin - Orders"])


@admin_order_router.put(
    "/{order_id}/status",
    response_model=MessageResponse,
    summary="[Admin] Update any order status"
)
async def admin_update_order_status(
    order_id: int,
    request: OrderUpdateStatusRequest,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    **[Admin Only]** Update the status of ANY order.

    Valid statuses:
    - Pending
    - Processing
    - Shipped
    - Delivered
    - Cancelled

    Use this to manage orders on behalf of users or handle customer service issues.
    """
    from sqlalchemy import select, update
    from models.procurement import StoreOrder

    # Check if order exists
    result = await session.execute(
        select(StoreOrder).where(StoreOrder.order_id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update status
    await session.execute(
        update(StoreOrder)
        .where(StoreOrder.order_id == order_id)
        .values(order_status=request.order_status)
    )
    await session.commit()

    return MessageResponse(
        message="Order status updated by admin",
        detail=f"Order #{order_id} (User: {order.user_id}) → {request.order_status}"
    )


@admin_order_router.get(
    "",
    response_model=List[OrderResponse],
    summary="[Admin] View all orders"
)
async def admin_get_all_orders(
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, description="Filter by order status")
):
    """
    **[Admin Only]** View all orders in the system with optional filtering.

    - Filter by user_id to see a specific user's orders
    - Filter by status to see orders in a specific state
    """
    from sqlalchemy import select, and_
    from models.procurement import StoreOrder, OrderItem, Partner, ExternalProduct
    from schemas.procurement import OrderItemResponse

    # Build query
    query = (
        select(StoreOrder, Partner)
        .join(Partner, StoreOrder.partner_id == Partner.partner_id)
        .order_by(StoreOrder.order_date.desc())
    )

    if user_id:
        query = query.where(StoreOrder.user_id == user_id)
    if status_filter:
        query = query.where(StoreOrder.order_status == status_filter)

    result = await session.execute(query)
    orders = result.all()

    order_responses = []
    for order, partner in orders:
        # Get order items
        items_result = await session.execute(
            select(OrderItem, ExternalProduct)
            .join(ExternalProduct, OrderItem.external_sku == ExternalProduct.external_sku)
            .where(OrderItem.order_id == order.order_id)
        )
        items = items_result.all()

        item_responses = [
            OrderItemResponse(
                external_sku=item.external_sku,
                product_name=product.product_name,
                partner_name=partner.partner_name,
                quantity=item.quantity,
                deal_price=item.deal_price,
                subtotal=item.deal_price * item.quantity
            )
            for item, product in items
        ]

        order_responses.append(
            OrderResponse(
                order_id=order.order_id,
                user_id=order.user_id,
                partner_id=order.partner_id,
                partner_name=partner.partner_name,
                order_date=order.order_date,
                expected_arrival=order.expected_arrival,
                total_price=order.total_price,
                order_status=order.order_status,
                items=item_responses
            )
        )

    return order_responses
