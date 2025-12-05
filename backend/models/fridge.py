from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship


class Fridge(SQLModel, table=True):
    """
    Fridge table.

    Matches schema:
    - fridge_id: UUID primary key
    - fridge_name: Name of the fridge (max 30 chars)

    Note: is_shared is removed; inferred from fridge_access table
    """
    __tablename__ = "fridge"

    fridge_id: UUID = Field(
        default_factory=lambda: __import__('uuid').uuid4(),
        primary_key=True,
        nullable=False
    )
    fridge_name: str = Field(
        max_length=30,
        nullable=False
    )

    # Relationships
    # access_list: list["FridgeAccess"] = Relationship(back_populates="fridge")
    # items: list["FridgeItem"] = Relationship(back_populates="fridge")


class FridgeAccess(SQLModel, table=True):
    """
    Fridge access control table.
    Defines which users can access which fridges and their role.

    Matches schema:
    - user_id: Foreign key to user
    - fridge_id: Foreign key to fridge
    - access_role: Owner or Member
    - Composite primary key (user_id, fridge_id)
    """
    __tablename__ = "fridge_access"

    user_id: UUID = Field(
        foreign_key="user.user_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    fridge_id: UUID = Field(
        foreign_key="fridge.fridge_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    access_role: str = Field(
        max_length=10,
        nullable=False
    )

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="fridge_access")
    # fridge: Optional[Fridge] = Relationship(back_populates="access_list")
