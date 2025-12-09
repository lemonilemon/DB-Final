from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.procurement import Partner, ExternalProduct, ShoppingListItem, StoreOrder, OrderItem
from models.inventory import Ingredient, FridgeItem
from models.recipe import Recipe, RecipeRequirement, MealPlan
from schemas.procurement import (
    PartnerCreateRequest,
    PartnerResponse,
    ExternalProductCreateRequest,
    ExternalProductResponse,
    ShoppingListAddRequest,
    ShoppingListItemResponse,
    OrderResponse,
    OrderItemResponse,
    CreateOrdersResponse,
    OrderUpdateStatusRequest,
    AvailabilityCheckResponse,
    IngredientAvailability,
    ProductRecommendation,
    ProductRecommendationsResponse,
    CreateOrderRequest,
)
from core.config import ORDER_STATUS_PENDING


class ProcurementService:
    """Service for procurement operations."""

    # ========================================================================
    # Partner Management
    # ========================================================================

    @staticmethod
    async def create_partner(
        request: PartnerCreateRequest,
        session: AsyncSession
    ) -> Partner:
        """Create a new partner (supplier)."""
        new_partner = Partner(
            partner_name=request.partner_name,
            contract_date=request.contract_date,
            avg_shipping_days=request.avg_shipping_days,
            credit_score=request.credit_score
        )
        session.add(new_partner)
        await session.commit()
        await session.refresh(new_partner)
        return new_partner

    @staticmethod
    async def get_all_partners(session: AsyncSession) -> List[PartnerResponse]:
        """Get all partners."""
        result = await session.execute(
            select(Partner).order_by(Partner.partner_name)
        )
        partners = result.scalars().all()
        return [PartnerResponse.model_validate(p) for p in partners]

    @staticmethod
    async def get_partner(partner_id: int, session: AsyncSession) -> Partner:
        """Get partner by ID."""
        result = await session.execute(
            select(Partner).where(Partner.partner_id == partner_id)
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        return partner

    # ========================================================================
    # External Product Management
    # ========================================================================

    @staticmethod
    async def create_external_product(
        request: ExternalProductCreateRequest,
        session: AsyncSession
    ) -> ExternalProduct:
        """
        Create a new external product.
        Links an ingredient to a partner with pricing.
        """
        # Verify partner exists
        await ProcurementService.get_partner(request.partner_id, session)

        # Verify ingredient exists
        result = await session.execute(
            select(Ingredient).where(Ingredient.ingredient_id == request.ingredient_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Ingredient not found")

        # Check if product with this composite key (partner_id, external_sku) already exists
        existing = await session.execute(
            select(ExternalProduct).where(
                (ExternalProduct.partner_id == request.partner_id) &
                (ExternalProduct.external_sku == request.external_sku)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{request.external_sku}' already exists for partner {request.partner_id}"
            )

        # Create product
        new_product = ExternalProduct(
            external_sku=request.external_sku,
            partner_id=request.partner_id,
            ingredient_id=request.ingredient_id,
            product_name=request.product_name,
            current_price=request.current_price,
            selling_unit=request.selling_unit
        )
        session.add(new_product)
        await session.commit()
        await session.refresh(new_product)
        return new_product

    @staticmethod
    async def get_external_products(
        session: AsyncSession,
        ingredient_id: int = None,
        partner_id: int = None
    ) -> List[ExternalProductResponse]:
        """
        Get external products with filtering options.
        Returns products with partner and ingredient details.
        """
        query = (
            select(ExternalProduct, Partner, Ingredient)
            .join(Partner, ExternalProduct.partner_id == Partner.partner_id)
            .join(Ingredient, ExternalProduct.ingredient_id == Ingredient.ingredient_id)
        )

        if ingredient_id:
            query = query.where(ExternalProduct.ingredient_id == ingredient_id)
        if partner_id:
            query = query.where(ExternalProduct.partner_id == partner_id)

        query = query.order_by(ExternalProduct.product_name)

        result = await session.execute(query)
        rows = result.all()

        products = []
        for product, partner, ingredient in rows:
            products.append(
                ExternalProductResponse(
                    external_sku=product.external_sku,
                    partner_id=product.partner_id,
                    partner_name=partner.partner_name,
                    ingredient_id=product.ingredient_id,
                    ingredient_name=ingredient.name,
                    standard_unit=ingredient.standard_unit,
                    product_name=product.product_name,
                    current_price=product.current_price,
                    selling_unit=product.selling_unit,
                    unit_quantity=product.unit_quantity
                )
            )

        return products

    # ========================================================================
    # Shopping List Management
    # ========================================================================

    @staticmethod
    async def add_to_shopping_list(
        request: ShoppingListAddRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """Add or update item in user's shopping list."""
        # Verify ingredient exists
        result = await session.execute(
            select(Ingredient).where(Ingredient.ingredient_id == request.ingredient_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Ingredient not found")

        # Check if already in list
        existing = await session.execute(
            select(ShoppingListItem).where(
                and_(
                    ShoppingListItem.user_id == current_user_id,
                    ShoppingListItem.ingredient_id == request.ingredient_id
                )
            )
        )
        existing_item = existing.scalar_one_or_none()

        if existing_item:
            # Update quantity and needed_by
            existing_item.quantity_to_buy = request.quantity_to_buy
            existing_item.needed_by = request.needed_by
            existing_item.added_date = date.today()
            session.add(existing_item)
        else:
            # Create new
            new_item = ShoppingListItem(
                user_id=current_user_id,
                ingredient_id=request.ingredient_id,
                quantity_to_buy=request.quantity_to_buy,
                added_date=date.today(),
                needed_by=request.needed_by
            )
            session.add(new_item)

        await session.commit()

    @staticmethod
    async def get_shopping_list(
        current_user_id: UUID,
        session: AsyncSession
    ) -> List[ShoppingListItemResponse]:
        """Get user's shopping list with product availability."""
        # Get shopping list items with ingredient details
        query = (
            select(ShoppingListItem, Ingredient)
            .join(Ingredient, ShoppingListItem.ingredient_id == Ingredient.ingredient_id)
            .where(ShoppingListItem.user_id == current_user_id)
            .order_by(ShoppingListItem.added_date.desc())
        )
        result = await session.execute(query)
        rows = result.all()

        items = []
        for list_item, ingredient in rows:
            # Count available products for this ingredient
            product_count_result = await session.execute(
                select(func.count(ExternalProduct.external_sku))
                .where(ExternalProduct.ingredient_id == list_item.ingredient_id)
            )
            product_count = product_count_result.scalar()

            items.append(
                ShoppingListItemResponse(
                    user_id=list_item.user_id,
                    ingredient_id=list_item.ingredient_id,
                    ingredient_name=ingredient.name,
                    standard_unit=ingredient.standard_unit,
                    quantity_to_buy=list_item.quantity_to_buy,
                    added_date=list_item.added_date,
                    needed_by=list_item.needed_by,
                    available_products=product_count
                )
            )

        return items

    @staticmethod
    async def remove_from_shopping_list(
        ingredient_id: int,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """Remove item from shopping list."""
        result = await session.execute(
            select(ShoppingListItem).where(
                and_(
                    ShoppingListItem.user_id == current_user_id,
                    ShoppingListItem.ingredient_id == ingredient_id
                )
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Item not in shopping list")

        await session.delete(item)
        await session.commit()

    # ========================================================================
    # Order Management with Split-by-Partner Logic
    # ========================================================================

    @staticmethod
    async def create_orders_from_shopping_list(
        current_user_id: UUID,
        session: AsyncSession
    ) -> CreateOrdersResponse:
        """
        Create orders from shopping list with AUTOMATIC SPLIT-BY-PARTNER logic.

        Algorithm:
        1. Get all items in user's shopping list
        2. For each ingredient, find cheapest external product
        3. Group products by partner
        4. Create one StoreOrder per partner
        5. Add OrderItems with price snapshots (deal_price)
        6. Calculate expected delivery dates
        7. Clear shopping list

        Returns:
            Details of all created orders grouped by partner
        """
        # Get shopping list
        shopping_list = await ProcurementService.get_shopping_list(current_user_id, session)

        if not shopping_list:
            raise HTTPException(
                status_code=400,
                detail="Shopping list is empty"
            )

        # Group items by partner (split orders)
        # partner_id -> list of (ingredient, quantity, product)
        orders_by_partner: Dict[int, List[tuple]] = defaultdict(list)

        # For each item in shopping list, find cheapest product
        for list_item in shopping_list:
            # Get all products for this ingredient, sorted by price
            products_result = await session.execute(
                select(ExternalProduct, Partner)
                .join(Partner, ExternalProduct.partner_id == Partner.partner_id)
                .where(ExternalProduct.ingredient_id == list_item.ingredient_id)
                .order_by(ExternalProduct.current_price.asc())
            )
            products = products_result.all()

            if not products:
                raise HTTPException(
                    status_code=400,
                    detail=f"No products available for ingredient '{list_item.ingredient_name}'"
                )

            # Choose cheapest product
            cheapest_product, partner = products[0]

            # Add to partner's order
            orders_by_partner[partner.partner_id].append({
                'ingredient_name': list_item.ingredient_name,
                'quantity_needed': list_item.quantity_to_buy,
                'product': cheapest_product,
                'partner': partner
            })

        # Create one StoreOrder per partner
        created_orders = []
        total_amount = Decimal(0)

        for partner_id, items in orders_by_partner.items():
            partner = items[0]['partner']  # Get partner from first item

            # Calculate total price for this order
            order_total = sum(
                item['product'].current_price * int(item['quantity_needed'])
                for item in items
            )

            # Calculate expected arrival
            expected_arrival = date.today() + timedelta(days=partner.avg_shipping_days)

            # Create StoreOrder
            new_order = StoreOrder(
                user_id=current_user_id,
                partner_id=partner_id,
                order_date=datetime.utcnow(),
                expected_arrival=expected_arrival,
                total_price=order_total,
                order_status=ORDER_STATUS_PENDING
            )
            session.add(new_order)
            await session.flush()  # Get order_id

            # Create OrderItems
            order_items_responses = []
            for item in items:
                product = item['product']
                quantity = int(item['quantity_needed'])

                order_item = OrderItem(
                    order_id=new_order.order_id,
                    external_sku=product.external_sku,
                    partner_id=partner_id,
                    quantity=quantity,
                    deal_price=product.current_price  # Price snapshot!
                )
                session.add(order_item)

                order_items_responses.append(
                    OrderItemResponse(
                        external_sku=product.external_sku,
                        product_name=product.product_name,
                        partner_name=partner.partner_name,
                        quantity=quantity,
                        deal_price=product.current_price,
                        subtotal=product.current_price * quantity
                    )
                )

            created_orders.append(
                OrderResponse(
                    order_id=new_order.order_id,
                    user_id=new_order.user_id,
                    partner_id=new_order.partner_id,
                    partner_name=partner.partner_name,
                    order_date=new_order.order_date,
                    expected_arrival=new_order.expected_arrival,
                    total_price=new_order.total_price,
                    order_status=new_order.order_status,
                    items=order_items_responses
                )
            )

            total_amount += order_total

        # Clear shopping list
        await session.execute(
            select(ShoppingListItem).where(ShoppingListItem.user_id == current_user_id)
        )
        delete_result = await session.execute(
            select(ShoppingListItem).where(ShoppingListItem.user_id == current_user_id)
        )
        items_to_delete = delete_result.scalars().all()
        for item in items_to_delete:
            await session.delete(item)

        await session.commit()

        return CreateOrdersResponse(
            orders_created=len(created_orders),
            total_partners=len(orders_by_partner),
            total_amount=total_amount,
            orders=created_orders,
            message=f"Successfully created {len(created_orders)} orders from {len(orders_by_partner)} partners"
        )

    @staticmethod
    async def get_user_orders(
        current_user_id: UUID,
        session: AsyncSession
    ) -> List[OrderResponse]:
        """Get all orders for current user."""
        # Get orders with partner details
        orders_result = await session.execute(
            select(StoreOrder, Partner)
            .join(Partner, StoreOrder.partner_id == Partner.partner_id)
            .where(StoreOrder.user_id == current_user_id)
            .order_by(StoreOrder.order_date.desc())
        )
        orders = orders_result.all()

        order_responses = []
        for order, partner in orders:
            # Get order items
            items_result = await session.execute(
                select(OrderItem, ExternalProduct)
                .join(ExternalProduct,
                      (OrderItem.partner_id == ExternalProduct.partner_id) &
                      (OrderItem.external_sku == ExternalProduct.external_sku))
                .where(OrderItem.order_id == order.order_id)
            )
            items = items_result.all()

            item_responses = []
            for order_item, product in items:
                item_responses.append(
                    OrderItemResponse(
                        external_sku=order_item.external_sku,
                        product_name=product.product_name,
                        partner_name=partner.partner_name,
                        quantity=order_item.quantity,
                        deal_price=order_item.deal_price,
                        subtotal=order_item.deal_price * order_item.quantity
                    )
                )

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

    @staticmethod
    async def cancel_order(
        order_id: int,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """
        Cancel a pending order (users can only cancel their own pending orders).

        Uses pessimistic locking (SELECT FOR UPDATE) to prevent race conditions.
        """
        from core.order_status import OrderStatusManager

        # Use pessimistic locking to prevent concurrent status changes
        result = await session.execute(
            select(StoreOrder)
            .where(
                and_(
                    StoreOrder.order_id == order_id,
                    StoreOrder.user_id == current_user_id
                )
            )
            .with_for_update()  # Lock the row until transaction completes
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # After acquiring lock, re-check status (might have changed)
        # If concurrent transaction already changed status, validation will fail
        OrderStatusManager.validate_transition(
            current_status=order.order_status,
            new_status="Cancelled",
            role="user"
        )

        order.order_status = "Cancelled"
        session.add(order)
        await session.commit()

    @staticmethod
    async def confirm_delivery(
        order_id: int,
        current_user_id: UUID,
        session: AsyncSession
    ) -> int:
        """
        Confirm order delivery (users can mark their own shipped orders as delivered).

        When marked as delivered:
        - Order items are automatically added to fridge inventory
        - Quantities are converted from selling units to standard units
        - Expiry dates are set (delivery date + 7 days)
        - Meal plan statuses are updated

        Uses pessimistic locking to prevent race conditions.

        Returns:
            Number of items added to fridge
        """
        from core.order_status import OrderStatusManager

        # Use pessimistic locking to prevent concurrent status changes
        result = await session.execute(
            select(StoreOrder)
            .where(
                and_(
                    StoreOrder.order_id == order_id,
                    StoreOrder.user_id == current_user_id
                )
            )
            .with_for_update()  # Lock the row until transaction completes
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # After acquiring lock, re-check status
        OrderStatusManager.validate_transition(
            current_status=order.order_status,
            new_status="Delivered",
            role="user"
        )

        # Update status
        order.order_status = "Delivered"
        session.add(order)

        # Add items to fridge automatically
        items_added = await ProcurementService.add_delivered_order_to_fridge(
            order, session
        )

        # Update meal plan statuses for this fridge
        if order.fridge_id:
            await ProcurementService.update_meal_plan_statuses(
                order.fridge_id, session
            )

        await session.commit()

        return items_added

    @staticmethod
    async def add_delivered_order_to_fridge(
        order: StoreOrder,
        session: AsyncSession
    ) -> int:
        """
        Add delivered order items to the fridge inventory.

        Process:
        1. Get all order items
        2. Convert selling units to standard units
        3. Create fridge_item records with expiry dates
        4. Add to fridge

        Returns:
            Number of fridge items created
        """
        from models.inventory import FridgeItem

        # Check if order has a fridge (nullable FK)
        if not order.fridge_id:
            # Order placed without fridge association (e.g., fridge was deleted)
            return 0

        # Get all order items
        order_items_result = await session.execute(
            select(OrderItem, ExternalProduct)
            .join(
                ExternalProduct,
                and_(
                    OrderItem.partner_id == ExternalProduct.partner_id,
                    OrderItem.external_sku == ExternalProduct.external_sku
                )
            )
            .where(OrderItem.order_id == order.order_id)
        )
        order_items = order_items_result.all()

        items_created = 0
        today = date.today()

        for order_item, product in order_items:
            # Convert selling_unit to standard_unit
            standard_quantity = order_item.quantity * product.unit_quantity

            # Set expiry date based on ingredient type
            # Default: 7 days for perishables, can be enhanced with ingredient-specific logic
            expiry_date = today + timedelta(days=7)

            # Create fridge item
            fridge_item = FridgeItem(
                fridge_id=order.fridge_id,
                ingredient_id=product.ingredient_id,
                quantity=standard_quantity,
                entry_date=today,
                expiry_date=expiry_date
            )
            session.add(fridge_item)
            items_created += 1

        await session.flush()  # Flush to database
        return items_created

    @staticmethod
    async def admin_update_order_status(
        order_id: int,
        request: OrderUpdateStatusRequest,
        session: AsyncSession
    ) -> StoreOrder:
        """
        [Admin] Update order status with state machine validation.

        When status is changed to "Delivered", automatically adds items to fridge.
        """
        try:
            from core.order_status import OrderStatusManager

            result = await session.execute(
                select(StoreOrder).where(StoreOrder.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            # Validate transition using state machine (admin role)
            OrderStatusManager.validate_transition(
                current_status=order.order_status,
                new_status=request.order_status,
                role="admin"
            )

            old_status = order.order_status
            order.order_status = request.order_status
            session.add(order)

            # If order is being marked as delivered, add items to fridge
            if request.order_status == "Delivered" and old_status != "Delivered":
                items_added = await ProcurementService.add_delivered_order_to_fridge(
                    order, session
                )

                # Update meal plan statuses for this fridge (new inventory may make plans "Ready")
                if order.fridge_id:
                    await ProcurementService.update_meal_plan_statuses(
                        order.fridge_id, session
                    )

            await session.commit()

            return order
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")

    # ========================================================================
    # Availability Check
    # ========================================================================

    @staticmethod
    async def check_recipe_availability(
        recipe_id: int,
        fridge_id: UUID,
        needed_by: date,
        session: AsyncSession,
        exclude_plan_id: Optional[int] = None
    ) -> AvailabilityCheckResponse:
        """
        Check if ingredients are available for a recipe using timeline simulation.
        """
        try:
            # Get recipe requirements
            requirements_result = await session.execute(
                select(RecipeRequirement, Ingredient)
                .join(Ingredient, RecipeRequirement.ingredient_id == Ingredient.ingredient_id)
                .where(RecipeRequirement.recipe_id == recipe_id)
            )
            requirements = requirements_result.all()

            if not requirements:
                raise HTTPException(status_code=404, detail="Recipe not found or has no requirements")

            # Get all users who have access to this fridge
            from models.fridge import FridgeAccess

            fridge_users_result = await session.execute(
                select(FridgeAccess.user_id)
                .where(FridgeAccess.fridge_id == fridge_id)
            )
            fridge_user_ids = [row[0] for row in fridge_users_result.all()]

            # Get meal plans within 14 days
            today = date.today()
            cutoff_date = today + timedelta(days=14)

            # Build query
            query = select(MealPlan).where(
                and_(
                    MealPlan.user_id.in_(fridge_user_ids),
                    MealPlan.planned_date >= datetime.combine(today, datetime.min.time()),
                    MealPlan.planned_date <= datetime.combine(cutoff_date, datetime.max.time())
                )
            )

            # Exclude specific plan if requested (to avoid double counting during updates)
            if exclude_plan_id:
                query = query.where(MealPlan.plan_id != exclude_plan_id)

            query = query.order_by(MealPlan.planned_date.asc())

            meal_plans_result = await session.execute(query)
            meal_plans = meal_plans_result.scalars().all()

            missing_ingredients = []

            for requirement, ingredient in requirements:
                # Get current fridge items (batches with quantities and expiry dates)
                items_result = await session.execute(
                    select(FridgeItem)
                    .where(
                        and_(
                            FridgeItem.fridge_id == fridge_id,
                            FridgeItem.ingredient_id == requirement.ingredient_id,
                            FridgeItem.expiry_date >= today
                        )
                    )
                    .order_by(FridgeItem.expiry_date.asc())  # Sort by expiry (for FIFO)
                )
                items = items_result.scalars().all()

                # Initialize batches (list of [quantity, expiry_date])
                batches = [[item.quantity, item.expiry_date] for item in items]

                # Get pending/shipped orders for this ingredient (within 14 days)
                from models.procurement import StoreOrder, OrderItem

                pending_orders_result = await session.execute(
                    select(OrderItem, StoreOrder, ExternalProduct)
                    .join(StoreOrder, OrderItem.order_id == StoreOrder.order_id)
                    .join(
                        ExternalProduct,
                        and_(
                            OrderItem.partner_id == ExternalProduct.partner_id,
                            OrderItem.external_sku == ExternalProduct.external_sku
                        )
                    )
                    .where(
                        and_(
                            ExternalProduct.ingredient_id == requirement.ingredient_id,
                            StoreOrder.fridge_id == fridge_id,
                            StoreOrder.order_status.in_(["Pending", "Processing", "Shipped"]),
                            StoreOrder.expected_arrival.isnot(None),
                            StoreOrder.expected_arrival >= today,
                            StoreOrder.expected_arrival <= cutoff_date
                        )
                    )
                    .order_by(StoreOrder.expected_arrival.asc())  # Sort by arrival date
                )

                # Collect arrival events (add to batches on arrival date)
                arrival_events = []  # List of (arrival_date, quantity_in_standard_unit, expiry_date)
                for order_item, order, product in pending_orders_result.all():
                    # Convert selling_unit to standard_unit
                    standard_quantity = order_item.quantity * product.unit_quantity

                    # Assume ingredients expire 7 days after arrival (configurable)
                    assumed_expiry = order.expected_arrival + timedelta(days=7)

                    arrival_events.append((
                        order.expected_arrival,
                        standard_quantity,
                        assumed_expiry
                    ))

                # Collect consumption events
                consumption_events = []  # List of (date, quantity_to_consume)

                # Event 1: Future meal plan consumptions
                for meal_plan in meal_plans:
                    plan_req_result = await session.execute(
                        select(RecipeRequirement)
                        .where(
                            and_(
                                RecipeRequirement.recipe_id == meal_plan.recipe_id,
                                RecipeRequirement.ingredient_id == requirement.ingredient_id
                            )
                        )
                    )
                    plan_req = plan_req_result.scalar_one_or_none()

                    if plan_req:
                        plan_date = meal_plan.planned_date.date() if isinstance(meal_plan.planned_date, datetime) else meal_plan.planned_date
                        consumption_events.append((plan_date, plan_req.quantity_needed))

                # Event 2: This recipe's consumption at needed_by
                consumption_events.append((needed_by, requirement.quantity_needed))

                # Merge arrival and consumption events
                all_events = []
                for date_obj, qty in consumption_events:
                    all_events.append(("consume", date_obj, qty))
                for date_obj, qty, expiry in arrival_events:
                    all_events.append(("arrive", date_obj, qty, expiry))

                # Sort all events by date chronologically
                all_events.sort(key=lambda x: x[1])

                # Simulate timeline with FIFO consumption and arrivals
                current_quantity = Decimal(0)
                min_quantity = Decimal(0)
                first_shortage_date = None

                for event in all_events:
                    event_type = event[0]
                    event_date = event[1]

                    if event_type == "arrive":
                        # Arrival event: Add new batch to inventory
                        arrival_quantity = event[2]
                        arrival_expiry = event[3]
                        batches.append([arrival_quantity, arrival_expiry])
                        # Re-sort batches by expiry (maintain FIFO order)
                        batches.sort(key=lambda x: x[1])
                        continue

                    # Consumption event
                    quantity_to_consume = event[2]
                    # Remove expired batches before this event
                    batches = [[qty, exp] for qty, exp in batches if exp >= event_date]

                    # Calculate total available before consumption
                    current_quantity = sum(qty for qty, _ in batches)

                    # Consume using FIFO (earliest expiry first)
                    remaining = quantity_to_consume
                    new_batches = []

                    for qty, exp in batches:
                        if remaining <= 0:
                            # No more to consume, keep this batch
                            new_batches.append([qty, exp])
                        elif qty <= remaining:
                            # Consume entire batch
                            remaining -= qty
                        else:
                            # Partially consume batch
                            new_batches.append([qty - remaining, exp])
                            remaining = Decimal(0)

                    batches = new_batches

                    # Calculate quantity after consumption
                    current_quantity = sum(qty for qty, _ in batches)

                    # If consumption failed (couldn't get enough), quantity goes negative
                    if remaining > 0:
                        current_quantity -= remaining

                    # Track minimum quantity and when it first goes negative
                    if current_quantity < min_quantity:
                        min_quantity = current_quantity
                        if current_quantity < 0 and first_shortage_date is None:
                            first_shortage_date = event_date

                # Only add to missing ingredients if there's a shortage
                if min_quantity < 0:
                    shortage = abs(min_quantity)

                    missing_ingredients.append(
                        IngredientAvailability(
                            ingredient_id=ingredient.ingredient_id,
                            ingredient_name=ingredient.name,
                            standard_unit=ingredient.standard_unit,
                            shortage=shortage,
                            needed_by=first_shortage_date
                        )
                    )

            all_available = len(missing_ingredients) == 0

            return AvailabilityCheckResponse(
                all_available=all_available,
                missing_ingredients=missing_ingredients,
                message=f"All ingredients available" if all_available else f"{len(missing_ingredients)} ingredient(s) insufficient"
            )
        except Exception as e:
            return AvailabilityCheckResponse(
                all_available=False,
                missing_ingredients=[],
                message=f"Error checking availability: {str(e)}"
            )

    @staticmethod
    async def update_meal_plan_statuses(
        fridge_id: UUID,
        session: AsyncSession
    ) -> None:
        """
        Update status of all meal plans for users with access to this fridge.

        Status values:
        - "Planned": >14 days away
        - "Ready": All ingredients available (within 14 days)
        - "Insufficient": Missing ingredients (within 14 days)
        - "Finished": Already cooked (set manually)
        - "Canceled": User canceled (set manually)
        """
        from models.fridge import FridgeAccess

        # Get all users with access to this fridge
        fridge_users_result = await session.execute(
            select(FridgeAccess.user_id)
            .where(FridgeAccess.fridge_id == fridge_id)
        )
        fridge_user_ids = [row[0] for row in fridge_users_result.all()]

        # Get all meal plans for these users (excluding Finished and Canceled)
        today = date.today()
        cutoff_date = today + timedelta(days=14)

        meal_plans_result = await session.execute(
            select(MealPlan)
            .where(
                and_(
                    MealPlan.user_id.in_(fridge_user_ids),
                    MealPlan.status.not_in(["Finished", "Canceled"])
                )
            )
        )
        meal_plans = meal_plans_result.scalars().all()

        # Update status for each meal plan
        for plan in meal_plans:
            plan_date = plan.planned_date.date() if isinstance(plan.planned_date, datetime) else plan.planned_date

            # Check if planned date is >14 days away
            if plan_date > cutoff_date:
                plan.status = "Planned"
            else:
                # Check availability
                try:
                    availability = await ProcurementService.check_recipe_availability(
                        recipe_id=plan.recipe_id,
                        fridge_id=fridge_id,
                        needed_by=plan_date,
                        session=session,
                        exclude_plan_id=plan.plan_id
                    )

                    if availability.all_available:
                        plan.status = "Ready"
                    else:
                        plan.status = "Insufficient"
                except Exception as e:
                    print(f"Error checking availability: {e}")
                    # If recipe not found or other error, mark as Planned
                    plan.status = "Planned"

            session.add(plan)

        await session.commit()

    # ========================================================================
    # Product Recommendations
    # ========================================================================

    @staticmethod
    async def get_product_recommendations(
        ingredient_id: int,
        quantity_needed: Decimal,
        needed_by: date,
        session: AsyncSession
    ) -> ProductRecommendationsResponse:
        """
        Get product recommendations for an ingredient with delivery validation.

        Returns all products that sell this ingredient, with:
        - Expected arrival date (today + avg_shipping_days)
        - Whether it arrives in time (expected_arrival <= needed_by)
        - Cheapest option that arrives in time
        """
        # Get ingredient
        ingredient_result = await session.execute(
            select(Ingredient).where(Ingredient.ingredient_id == ingredient_id)
        )
        ingredient = ingredient_result.scalar_one_or_none()

        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")

        # Get all products for this ingredient
        products_result = await session.execute(
            select(ExternalProduct, Partner)
            .join(Partner, ExternalProduct.partner_id == Partner.partner_id)
            .where(ExternalProduct.ingredient_id == ingredient_id)
            .order_by(ExternalProduct.current_price.asc())  # Cheapest first
        )
        products = products_result.all()

        if not products:
            raise HTTPException(
                status_code=404,
                detail=f"No products available for ingredient '{ingredient.name}'"
            )

        # Build recommendations - only include products that arrive in time
        today = date.today()
        recommendations = []

        for product, partner in products:
            expected_arrival = today + timedelta(days=partner.avg_shipping_days)

            # Only include if it arrives in time
            if expected_arrival <= needed_by:
                recommendations.append(
                    ProductRecommendation(
                        external_sku=product.external_sku,
                        partner_id=partner.partner_id,
                        partner_name=partner.partner_name,
                        product_name=product.product_name,
                        current_price=product.current_price,
                        selling_unit=product.selling_unit,
                        unit_quantity=product.unit_quantity,
                        standard_unit=ingredient.standard_unit,
                        avg_shipping_days=partner.avg_shipping_days,
                        expected_arrival=expected_arrival
                    )
                )

        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail=f"No products can arrive by {needed_by} for {ingredient.name}"
            )

        return ProductRecommendationsResponse(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient.name,
            quantity_needed=quantity_needed,
            needed_by=needed_by,
            products=recommendations,
            message=f"Found {len(recommendations)} product(s) that arrive by {needed_by}"
        )

    # ========================================================================
    # User-Selected Order Creation
    # ========================================================================

    @staticmethod
    async def create_order(
        request: CreateOrderRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> OrderResponse:
        """
        Create an order with user-selected products (frontend-driven).

        Unlike create_orders_from_shopping_list which auto-selects cheapest,
        this accepts explicit product selections from the user/frontend.
        """
        from services.fridge_service import FridgeService

        # Check fridge access
        await FridgeService._check_fridge_access(
            request.fridge_id, current_user_id, session
        )

        if not request.items:
            raise HTTPException(status_code=400, detail="Order must have at least one item")

        # Get all products and validate
        products_map = {}  # (partner_id, sku) -> (product, partner)
        for item in request.items:
            product_result = await session.execute(
                select(ExternalProduct, Partner)
                .join(Partner, ExternalProduct.partner_id == Partner.partner_id)
                .where(
                    (ExternalProduct.partner_id == item.partner_id) &
                    (ExternalProduct.external_sku == item.external_sku)
                )
            )
            product_row = product_result.one_or_none()

            if not product_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product '{item.external_sku}' not found for partner {item.partner_id}"
                )

            products_map[(item.partner_id, item.external_sku)] = product_row

        # All products must be from the same partner
        partners = set(partner.partner_id for _, partner in products_map.values())
        if len(partners) > 1:
            raise HTTPException(
                status_code=400,
                detail="All products in an order must be from the same partner"
            )

        # Get the partner
        _, partner = list(products_map.values())[0]

        # Calculate total price
        total_price = Decimal(0)
        for item in request.items:
            product, _ = products_map[(item.partner_id, item.external_sku)]
            total_price += product.current_price * item.quantity

        # Calculate expected arrival
        expected_arrival = date.today() + timedelta(days=partner.avg_shipping_days)

        # Create StoreOrder
        new_order = StoreOrder(
            user_id=current_user_id,
            partner_id=partner.partner_id,
            fridge_id=request.fridge_id,
            order_date=datetime.utcnow(),
            expected_arrival=expected_arrival,
            total_price=total_price,
            order_status=ORDER_STATUS_PENDING
        )
        session.add(new_order)
        await session.flush()  # Get order_id

        # Create OrderItems
        order_items_responses = []
        for item in request.items:
            product, _ = products_map[(item.partner_id, item.external_sku)]

            order_item = OrderItem(
                order_id=new_order.order_id,
                external_sku=item.external_sku,
                partner_id=partner.partner_id,
                quantity=item.quantity,
                deal_price=product.current_price  # Price snapshot
            )
            session.add(order_item)

            order_items_responses.append(
                OrderItemResponse(
                    external_sku=product.external_sku,
                    product_name=product.product_name,
                    partner_name=partner.partner_name,
                    quantity=item.quantity,
                    deal_price=product.current_price,
                    subtotal=product.current_price * item.quantity
                )
            )

        await session.commit()
        await session.refresh(new_order)

        # Update meal plan statuses after order creation (pending order may make plans Ready)
        if request.fridge_id:
            await ProcurementService.update_meal_plan_statuses(request.fridge_id, session)

        return OrderResponse(
            order_id=new_order.order_id,
            user_id=new_order.user_id,
            partner_id=new_order.partner_id,
            partner_name=partner.partner_name,
            order_date=new_order.order_date,
            expected_arrival=new_order.expected_arrival,
            total_price=new_order.total_price,
            order_status=new_order.order_status,
            items=order_items_responses
        )
