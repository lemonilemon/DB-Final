from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlmodel import Field, SQLModel, Relationship


class Ingredient(SQLModel, table=True):
    """
    Ingredient table - represents standardized ingredients.

    Matches schema:
    - ingredient_id: BIGINT identity primary key
    - name: Unique ingredient name (max 50 chars)
    - standard_unit: g, ml, or pcs
    - shelf_life_days: Default shelf life in days
    """
    __tablename__ = "ingredient"

    ingredient_id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    name: str = Field(
        max_length=50,
        nullable=False,
        unique=True,
        index=True
    )
    standard_unit: str = Field(
        max_length=10,
        nullable=False
    )
    shelf_life_days: int = Field(
        nullable=False,
        gt=0
    )

    # Relationships
    # fridge_items: list["FridgeItem"] = Relationship(back_populates="ingredient")
    # external_products: list["ExternalProduct"] = Relationship(back_populates="ingredient")
    # shopping_list_items: list["ShoppingListItem"] = Relationship(back_populates="ingredient")
    # recipe_requirements: list["RecipeRequirement"] = Relationship(back_populates="ingredient")


class FridgeItem(SQLModel, table=True):
    """
    Fridge item table - tracks ingredient inventory in fridges.

    Matches schema:
    - fridge_item_id: BIGINT identity primary key
    - fridge_id: Foreign key to fridge
    - ingredient_id: Foreign key to ingredient
    - quantity: Current quantity in standard_unit
    - entry_date: When item was added
    - expiry_date: When item expires (for FIFO)
    """
    __tablename__ = "fridge_item"

    fridge_item_id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    fridge_id: UUID = Field(
        foreign_key="fridge.fridge_id",
        nullable=False,
        ondelete="CASCADE"
    )
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id",
        nullable=False,
        ondelete="RESTRICT"
    )
    quantity: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        ge=0
    )
    entry_date: date = Field(
        nullable=False
    )
    expiry_date: date = Field(
        nullable=False
    )

    # Relationships
    # fridge: Optional["Fridge"] = Relationship(back_populates="items")
    # ingredient: Optional[Ingredient] = Relationship(back_populates="fridge_items")
