from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel, Relationship


class Recipe(SQLModel, table=True):
    """
    Recipe table - user-created recipes.

    Matches schema:
    - recipe_id: BIGINT identity primary key
    - owner_id: Foreign key to user (recipe creator)
    - recipe_name: Name of the recipe (max 100 chars)
    - description: Recipe description/notes
    - cooking_time: Time in minutes
    - status: Recipe state (max 10 chars, default 'Pending')
    - created_at: When recipe was created (like article timestamp)
    - updated_at: When recipe was last modified
    """
    __tablename__ = "recipe"

    recipe_id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    owner_id: UUID = Field(
        foreign_key="user.user_id",
        nullable=False,
        ondelete="RESTRICT"
    )
    recipe_name: str = Field(
        max_length=100,
        nullable=False
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500
    )
    cooking_time: Optional[int] = Field(
        default=None,
        gt=0
    )
    status: str = Field(
        max_length=10,
        nullable=False,
        default="Published"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )

    # Relationships
    # owner: Optional["User"] = Relationship(back_populates="recipes")
    # requirements: list["RecipeRequirement"] = Relationship(back_populates="recipe")
    # steps: list["RecipeStep"] = Relationship(back_populates="recipe")
    # reviews: list["RecipeReview"] = Relationship(back_populates="recipe")
    # meal_plans: list["MealPlan"] = Relationship(back_populates="recipe")


class RecipeRequirement(SQLModel, table=True):
    """
    Recipe requirement - ingredients needed for a recipe.

    Matches schema:
    - recipe_id: Foreign key to recipe (composite PK)
    - ingredient_id: Foreign key to ingredient (composite PK)
    - quantity_needed: Amount in standard_unit
    """
    __tablename__ = "recipe_requirement"

    recipe_id: int = Field(
        foreign_key="recipe.recipe_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id",
        primary_key=True,
        ondelete="RESTRICT"
    )
    quantity_needed: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        gt=0
    )

    # Relationships
    # recipe: Optional[Recipe] = Relationship(back_populates="requirements")
    # ingredient: Optional["Ingredient"] = Relationship(back_populates="recipe_requirements")


class RecipeStep(SQLModel, table=True):
    """
    Recipe step - cooking instructions.

    Matches schema:
    - recipe_id: Foreign key to recipe (composite PK)
    - step_number: Step sequence number (composite PK)
    - description: Instruction text (max 1000 chars)
    """
    __tablename__ = "recipe_step"

    recipe_id: int = Field(
        foreign_key="recipe.recipe_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    step_number: int = Field(
        primary_key=True
    )
    description: str = Field(
        max_length=1000,
        nullable=False
    )

    # Relationships
    # recipe: Optional[Recipe] = Relationship(back_populates="steps")


class RecipeReview(SQLModel, table=True):
    """
    Recipe review - user ratings and comments.

    Matches schema:
    - user_id: Foreign key to user (composite PK)
    - recipe_id: Foreign key to recipe (composite PK)
    - rating: Score 1-5
    - comment: Optional text (max 500 chars)
    - review_date: When review was posted
    """
    __tablename__ = "recipe_review"

    user_id: UUID = Field(
        foreign_key="user.user_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    recipe_id: int = Field(
        foreign_key="recipe.recipe_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    rating: int = Field(
        nullable=False,
        ge=1,
        le=5
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=500
    )
    review_date: datetime = Field(
        nullable=False
    )

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="recipe_reviews")
    # recipe: Optional[Recipe] = Relationship(back_populates="reviews")


class MealPlan(SQLModel, table=True):
    """
    Meal plan - scheduled recipes.

    Matches schema:
    - plan_id: BIGINT identity primary key
    - user_id: Foreign key to user
    - recipe_id: Foreign key to recipe
    - planned_date: When user plans to cook
    - status: Meal plan status
      - "Planned": Too far in future (>14 days)
      - "Ready": All ingredients available
      - "Insufficient": Missing ingredients
      - "Finished": Recipe has been cooked
      - "Canceled": User canceled the plan
    """
    __tablename__ = "meal_plan"

    plan_id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    user_id: UUID = Field(
        foreign_key="user.user_id",
        nullable=False,
        ondelete="CASCADE"
    )
    recipe_id: int = Field(
        foreign_key="recipe.recipe_id",
        nullable=False,
        ondelete="CASCADE"
    )
    planned_date: datetime = Field(
        nullable=False
    )
    status: str = Field(
        max_length=30,
        nullable=False,
        default="Planned"
    )

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="meal_plans")
    # recipe: Optional[Recipe] = Relationship(back_populates="meal_plans")
