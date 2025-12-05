from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Ingredient Schemas
# ============================================================================

class IngredientCreateRequest(BaseModel):
    """Request model for creating a new ingredient."""
    name: str = Field(..., min_length=1, max_length=50, description="Ingredient name")
    standard_unit: str = Field(..., description="Standard unit: 'g', 'ml', or 'pcs'")
    shelf_life_days: int = Field(..., gt=0, description="Default shelf life in days")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Milk",
                "standard_unit": "ml",
                "shelf_life_days": 7
            }
        }


class IngredientResponse(BaseModel):
    """Response model for ingredient."""
    ingredient_id: int
    name: str
    standard_unit: str
    shelf_life_days: int

    class Config:
        from_attributes = True


# ============================================================================
# Fridge Item Schemas
# ============================================================================

class FridgeItemAddRequest(BaseModel):
    """Request model for adding an item to a fridge."""
    ingredient_id: int = Field(..., description="ID of the ingredient to add")
    quantity: Decimal = Field(..., gt=0, description="Quantity in standard unit")
    expiry_date: date = Field(..., description="When this item expires (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "ingredient_id": 1,
                "quantity": 1000,
                "expiry_date": "2025-12-12"
            }
        }


class FridgeItemUpdateRequest(BaseModel):
    """Request model for updating a fridge item."""
    quantity: Optional[Decimal] = Field(None, gt=0, description="New quantity")
    expiry_date: Optional[date] = Field(None, description="New expiry date")


class FridgeItemResponse(BaseModel):
    """Response model for a fridge item with ingredient details."""
    fridge_item_id: int
    fridge_id: UUID
    ingredient_id: int
    ingredient_name: str
    standard_unit: str
    quantity: Decimal
    entry_date: date
    expiry_date: date
    days_until_expiry: Optional[int] = None  # Calculated field

    class Config:
        from_attributes = True


# ============================================================================
# Consumption Schemas
# ============================================================================

class ConsumeRequest(BaseModel):
    """Request model for consuming an ingredient from fridge (FIFO)."""
    ingredient_id: int = Field(..., description="ID of ingredient to consume")
    quantity: Decimal = Field(..., gt=0, description="Amount to consume in standard unit")

    class Config:
        json_schema_extra = {
            "example": {
                "ingredient_id": 1,
                "quantity": 250
            }
        }


class ConsumeResponse(BaseModel):
    """Response model after consuming items."""
    ingredient_name: str
    requested_quantity: Decimal
    consumed_quantity: Decimal
    remaining_quantity: Decimal
    items_consumed: int  # Number of fridge items affected
    message: str


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
    detail: Optional[str] = None
