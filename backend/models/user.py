from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import Enum as SQLEnum


class UserRoleEnum(str, Enum):
    """User role enumeration."""
    USER = "User"
    ADMIN = "Admin"


class User(SQLModel, table=True):
    """
    User account table.

    Matches schema:
    - user_id: UUID primary key
    - user_name: Unique username (max 20 chars)
    - password: Bcrypt hash (60 chars)
    - email: Unique email (max 50 chars)
    - status: Active or Disabled
    - role: User or Admin (single role per user)
    """
    __tablename__ = "user"

    user_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False
    )
    user_name: str = Field(
        max_length=20,
        nullable=False,
        unique=True,
        index=True
    )
    password: str = Field(
        max_length=60,
        nullable=False
    )
    email: str = Field(
        max_length=50,
        nullable=False,
        unique=True,
        index=True
    )
    status: str = Field(
        max_length=10,
        nullable=False,
        default="Active"
    )
    role: str = Field(
        sa_column=Column(
            SQLEnum("User", "Admin", name="user_role_enum", create_type=False),
            nullable=False,
            server_default="User"
        )
    )

    # Relationships (will be populated when other models are created)
    # fridge_access: list["FridgeAccess"] = Relationship(back_populates="user")
    # shopping_list: list["ShoppingListItem"] = Relationship(back_populates="user")
    # orders: list["StoreOrder"] = Relationship(back_populates="user")
    # recipes: list["Recipe"] = Relationship(back_populates="owner")
    # meal_plans: list["MealPlan"] = Relationship(back_populates="user")
    # recipe_reviews: list["RecipeReview"] = Relationship(back_populates="user")
