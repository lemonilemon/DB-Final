from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    """
    User account table.

    Matches schema:
    - user_id: UUID primary key
    - user_name: Unique username (max 20 chars)
    - password: Bcrypt hash (60 chars)
    - email: Unique email (max 50 chars)
    - status: Active or Disabled
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

    # Relationships (will be populated when other models are created)
    # roles: list["UserRole"] = Relationship(back_populates="user")
    # fridge_access: list["FridgeAccess"] = Relationship(back_populates="user")
    # shopping_list: list["ShoppingListItem"] = Relationship(back_populates="user")
    # orders: list["StoreOrder"] = Relationship(back_populates="user")
    # recipes: list["Recipe"] = Relationship(back_populates="owner")
    # meal_plans: list["MealPlan"] = Relationship(back_populates="user")
    # recipe_reviews: list["RecipeReview"] = Relationship(back_populates="user")


class UserRole(SQLModel, table=True):
    """
    User role mapping table (many-to-many: User to Roles).

    Matches schema:
    - user_id: Foreign key to user
    - role: User or Admin
    - Composite primary key (user_id, role)
    """
    __tablename__ = "user_role"

    user_id: UUID = Field(
        foreign_key="user.user_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    role: str = Field(
        max_length=10,
        nullable=False,
        primary_key=True
    )

    # Relationships
    # user: Optional[User] = Relationship(back_populates="roles")
