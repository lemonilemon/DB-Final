from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Recipe Schemas
# ============================================================================

class RecipeRequirementInput(BaseModel):
    """Ingredient requirement for a recipe."""
    ingredient_id: int
    quantity_needed: Decimal = Field(..., gt=0)


class RecipeStepInput(BaseModel):
    """Step instruction for a recipe."""
    step_number: int
    description: str = Field(..., max_length=1000)


class RecipeCreateRequest(BaseModel):
    """Request model for creating a recipe."""
    recipe_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    cooking_time: Optional[int] = Field(None, gt=0, description="Time in minutes")
    requirements: List[RecipeRequirementInput] = Field(..., min_items=1)
    steps: List[RecipeStepInput] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "recipe_name": "Scrambled Eggs with Milk",
                "description": "Quick and easy breakfast",
                "cooking_time": 10,
                "requirements": [
                    {"ingredient_id": 2, "quantity_needed": 4},  # 4 eggs
                    {"ingredient_id": 1, "quantity_needed": 50}   # 50ml milk
                ],
                "steps": [
                    {"step_number": 1, "description": "Crack eggs into bowl"},
                    {"step_number": 2, "description": "Add milk and whisk"},
                    {"step_number": 3, "description": "Cook in pan until done"}
                ]
            }
        }


class RecipeRequirementResponse(BaseModel):
    """Response for recipe requirement with ingredient details."""
    ingredient_id: int
    ingredient_name: str
    standard_unit: str
    quantity_needed: Decimal

    class Config:
        from_attributes = True


class RecipeStepResponse(BaseModel):
    """Response for recipe step."""
    step_number: int
    description: str

    class Config:
        from_attributes = True


class RecipeBasicResponse(BaseModel):
    """Basic recipe information (for list views)."""
    recipe_id: int
    owner_id: UUID
    owner_name: str
    recipe_name: str
    description: Optional[str]
    cooking_time: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    avg_rating: Optional[float] = None  # Average review rating
    total_reviews: int = 0

    class Config:
        from_attributes = True


class RecipeDetailResponse(BaseModel):
    """Detailed recipe with requirements and steps."""
    recipe_id: int
    owner_id: UUID
    owner_name: str
    recipe_name: str
    description: Optional[str]
    cooking_time: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    requirements: List[RecipeRequirementResponse]
    steps: List[RecipeStepResponse]
    avg_rating: Optional[float] = None
    total_reviews: int = 0

    class Config:
        from_attributes = True


# ============================================================================
# Cooking Schemas
# ============================================================================

class CookRecipeRequest(BaseModel):
    """Request to cook a recipe from a fridge."""
    fridge_id: UUID = Field(..., description="Which fridge to use ingredients from")


class CookRecipeResponse(BaseModel):
    """Response after cooking a recipe."""
    recipe_name: str
    ingredients_consumed: List[dict]  # List of consumed ingredients
    success: bool
    message: str


# ============================================================================
# Review Schemas
# ============================================================================

class ReviewCreateRequest(BaseModel):
    """Request to create a recipe review."""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)


class ReviewResponse(BaseModel):
    """Response for recipe review."""
    user_id: UUID
    user_name: str
    recipe_id: int
    rating: int
    comment: Optional[str]
    review_date: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Meal Plan Schemas
# ============================================================================

class MealPlanCreateRequest(BaseModel):
    """Request to create a meal plan."""
    recipe_id: int
    planned_date: date


class MealPlanResponse(BaseModel):
    """Response for meal plan."""
    plan_id: int
    user_id: UUID
    recipe_id: int
    recipe_name: str
    planned_date: date
    status: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None
