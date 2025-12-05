from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.procurement import Partner, ExternalProduct, ShoppingListItem, StoreOrder, OrderItem
from models.inventory import Ingredient
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

        # Check if SKU already exists
        existing = await session.execute(
            select(ExternalProduct).where(ExternalProduct.external_sku == request.external_sku)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{request.external_sku}' already exists"
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
                    product_name=product.product_name,
                    current_price=product.current_price,
                    selling_unit=product.selling_unit
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
            # Update quantity
            existing_item.quantity_to_buy = request.quantity_to_buy
            session.add(existing_item)
        else:
            # Create new
            new_item = ShoppingListItem(
                user_id=current_user_id,
                ingredient_id=request.ingredient_id,
                quantity_to_buy=request.quantity_to_buy,
                added_date=date.today()
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
                .join(ExternalProduct, OrderItem.external_sku == ExternalProduct.external_sku)
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
    async def update_order_status(
        order_id: int,
        request: OrderUpdateStatusRequest,
        current_user_id: UUID,
        session: AsyncSession
    ) -> None:
        """Update order status (user can update their own orders)."""
        result = await session.execute(
            select(StoreOrder).where(
                and_(
                    StoreOrder.order_id == order_id,
                    StoreOrder.user_id == current_user_id
                )
            )
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order.order_status = request.order_status
        session.add(order)
        await session.commit()
