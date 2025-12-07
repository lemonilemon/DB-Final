from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Partner Schemas
# ============================================================================

class PartnerCreateRequest(BaseModel):
    """Request model for creating a partner."""
    partner_name: str = Field(..., min_length=1, max_length=50)
    contract_date: date
    avg_shipping_days: int = Field(..., gt=0)
    credit_score: int = Field(..., ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "partner_name": "FreshMart Wholesale",
                "contract_date": "2025-01-01",
                "avg_shipping_days": 3,
                "credit_score": 85
            }
        }


class PartnerResponse(BaseModel):
    """Response model for partner."""
    partner_id: int
    partner_name: str
    contract_date: date
    avg_shipping_days: int
    credit_score: int

    class Config:
        from_attributes = True


# ============================================================================
# External Product Schemas
# ============================================================================

class ExternalProductCreateRequest(BaseModel):
    """Request model for creating an external product."""
    external_sku: str = Field(..., max_length=50)
    partner_id: int
    ingredient_id: int
    product_name: str = Field(..., max_length=100)
    current_price: Decimal = Field(..., gt=0)
    selling_unit: str = Field(..., max_length=20, description="e.g., 'Bottle', 'Pack', '1L'")

    class Config:
        json_schema_extra = {
            "example": {
                "external_sku": "FM-MILK-1L",
                "partner_id": 1,
                "ingredient_id": 1,
                "product_name": "Fresh Milk 1L",
                "current_price": 4.99,
                "selling_unit": "1L Bottle"
            }
        }


class ExternalProductResponse(BaseModel):
    """Response model for external product with partner/ingredient details."""
    external_sku: str
    partner_id: int
    partner_name: str
    ingredient_id: int
    ingredient_name: str
    product_name: str
    current_price: Decimal
    selling_unit: str

    class Config:
        from_attributes = True


# ============================================================================
# Shopping List Schemas
# ============================================================================

class ShoppingListAddRequest(BaseModel):
    """Request model for adding item to shopping list."""
    ingredient_id: int
    quantity_to_buy: Decimal = Field(..., gt=0, description="Quantity in standard unit")

    class Config:
        json_schema_extra = {
            "example": {
                "ingredient_id": 1,
                "quantity_to_buy": 2000
            }
        }


class ShoppingListItemResponse(BaseModel):
    """Response model for shopping list item."""
    user_id: UUID
    ingredient_id: int
    ingredient_name: str
    standard_unit: str
    quantity_to_buy: Decimal
    added_date: date
    available_products: int  # Count of products offering this ingredient

    class Config:
        from_attributes = True


# ============================================================================
# Order Schemas
# ============================================================================

class OrderItemResponse(BaseModel):
    """Response model for order item."""
    external_sku: str
    product_name: str
    partner_name: str
    quantity: int
    deal_price: Decimal
    subtotal: Decimal  # quantity * deal_price


class OrderResponse(BaseModel):
    """Response model for store order with items."""
    order_id: int
    user_id: UUID
    partner_id: int
    partner_name: str
    order_date: datetime
    expected_arrival: Optional[date]
    total_price: Decimal
    order_status: str
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class CreateOrdersResponse(BaseModel):
    """Response after creating orders from shopping list."""
    orders_created: int
    total_partners: int
    total_amount: Decimal
    orders: List[OrderResponse]
    message: str


class OrderUpdateStatusRequest(BaseModel):
    """Request to update order status."""
    order_status: str = Field(..., description="New status: Pending, Processing, Shipped, Delivered, Cancelled")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None


# ============================================================================
# Availability Check Schemas
# ============================================================================

class IngredientAvailability(BaseModel):
    """Availability status for a single ingredient (only returned if insufficient)."""
    ingredient_id: int
    ingredient_name: str
    standard_unit: str
    shortage: Decimal  # Minimum amount needed to fix entire timeline
    needed_by: date  # Earliest date when shortage occurs (order must arrive before this)

    class Config:
        from_attributes = True


class AvailabilityCheckResponse(BaseModel):
    """Response for ingredient availability check."""
    all_available: bool
    missing_ingredients: List[IngredientAvailability]
    message: str


# ============================================================================
# Product Recommendation Schemas
# ============================================================================

class ProductRecommendation(BaseModel):
    """Product recommendation (sorted by price, only shows products that arrive in time)."""
    external_sku: str
    partner_id: int
    partner_name: str
    product_name: str
    current_price: Decimal
    selling_unit: str
    avg_shipping_days: int
    expected_arrival: date  # order_date + avg_shipping_days

    class Config:
        from_attributes = True


class ProductRecommendationsResponse(BaseModel):
    """Response for product recommendations."""
    ingredient_id: int
    ingredient_name: str
    quantity_needed: Decimal
    needed_by: Optional[date]
    products: List[ProductRecommendation]
    message: str


# ============================================================================
# New Order Creation Schemas
# ============================================================================

class OrderItemCreateRequest(BaseModel):
    """Request to add a product to order."""
    external_sku: str
    quantity: int = Field(..., gt=0)


class CreateOrderRequest(BaseModel):
    """Request to create order with user-selected products."""
    fridge_id: UUID
    items: List[OrderItemCreateRequest] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "fridge_id": "123e4567-e89b-12d3-a456-426614174000",
                "items": [
                    {"external_sku": "FM-MILK-1L", "quantity": 2},
                    {"external_sku": "SS-EGGS-12", "quantity": 1}
                ]
            }
        }
