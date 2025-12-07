"""
SQLModel database models for NEW Fridge.

Import all models here to ensure they're registered with SQLModel.metadata.
This is critical for SQLAlchemy to know about all tables when creating/querying.
"""

# User models
from models.user import User, UserRoleEnum

# Fridge models
from models.fridge import Fridge, FridgeAccess

# Inventory models
from models.inventory import Ingredient, FridgeItem

# Procurement models
from models.procurement import (
    Partner,
    ExternalProduct,
    ShoppingListItem,
    StoreOrder,
    OrderItem
)

# Recipe models
from models.recipe import (
    Recipe,
    RecipeRequirement,
    RecipeStep,
    RecipeReview,
    MealPlan
)

__all__ = [
    # User
    "User",
    "UserRoleEnum",
    # Fridge
    "Fridge",
    "FridgeAccess",
    # Inventory
    "Ingredient",
    "FridgeItem",
    # Procurement
    "Partner",
    "ExternalProduct",
    "ShoppingListItem",
    "StoreOrder",
    "OrderItem",
    # Recipe
    "Recipe",
    "RecipeRequirement",
    "RecipeStep",
    "RecipeReview",
    "MealPlan",
]
