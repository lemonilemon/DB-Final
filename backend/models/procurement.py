from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel, Relationship


class Partner(SQLModel, table=True):
    """
    Partner (supplier) table.

    Matches schema:
    - partner_id: BIGINT identity primary key
    - partner_name: Supplier name (max 50 chars)
    - contract_date: When partnership started
    - avg_shipping_days: Average delivery time
    - credit_score: Reliability score (0-100)
    """
    __tablename__ = "partner"

    partner_id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    partner_name: str = Field(
        max_length=50,
        nullable=False
    )
    contract_date: date = Field(
        nullable=False
    )
    avg_shipping_days: int = Field(
        nullable=False,
        gt=0
    )
    credit_score: int = Field(
        nullable=False,
        ge=0,
        le=100
    )

    # Relationships
    # external_products: list["ExternalProduct"] = Relationship(back_populates="partner")
    # store_orders: list["StoreOrder"] = Relationship(back_populates="partner")


class ExternalProduct(SQLModel, table=True):
    """
    External product catalog - products sold by partners.

    Matches schema:
    - external_sku: Product SKU (primary key)
    - partner_id: Foreign key to partner
    - ingredient_id: Link to internal ingredient
    - product_name: Display name (max 100 chars)
    - current_price: Current selling price
    - selling_unit: Unit as sold (e.g., "Bottle", "Pack")
    """
    __tablename__ = "external_product"

    external_sku: str = Field(
        max_length=50,
        primary_key=True
    )
    partner_id: int = Field(
        foreign_key="partner.partner_id",
        nullable=False,
        ondelete="RESTRICT"
    )
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id",
        nullable=False,
        ondelete="RESTRICT"
    )
    product_name: str = Field(
        max_length=100,
        nullable=False
    )
    current_price: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        gt=0
    )
    selling_unit: str = Field(
        max_length=20,
        nullable=False
    )

    # Relationships
    # partner: Optional[Partner] = Relationship(back_populates="external_products")
    # ingredient: Optional["Ingredient"] = Relationship(back_populates="external_products")
    # order_items: list["OrderItem"] = Relationship(back_populates="product")


class ShoppingListItem(SQLModel, table=True):
    """
    Shopping list (cart) - per-user ingredient wishlist.

    Matches schema:
    - user_id: Foreign key to user (composite PK)
    - ingredient_id: Foreign key to ingredient (composite PK)
    - quantity_to_buy: Desired quantity in standard_unit
    - added_date: When added to cart
    """
    __tablename__ = "shopping_list_item"

    user_id: UUID = Field(
        foreign_key="user.user_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id",
        primary_key=True,
        ondelete="RESTRICT"
    )
    quantity_to_buy: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        gt=0
    )
    added_date: date = Field(
        nullable=False
    )

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="shopping_list")
    # ingredient: Optional["Ingredient"] = Relationship(back_populates="shopping_list_items")


class StoreOrder(SQLModel, table=True):
    """
    Store order - represents an order placed with a partner.

    Matches schema:
    - order_id: BIGINT identity primary key
    - user_id: Foreign key to user
    - partner_id: Foreign key to partner (key for split orders)
    - order_date: When order was placed
    - expected_arrival: Calculated delivery date
    - total_price: Order total
    - order_status: Order state (max 15 chars)
    """
    __tablename__ = "store_order"

    order_id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    user_id: UUID = Field(
        foreign_key="user.user_id",
        nullable=False,
        ondelete="RESTRICT"
    )
    partner_id: int = Field(
        foreign_key="partner.partner_id",
        nullable=False,
        ondelete="RESTRICT"
    )
    order_date: datetime = Field(
        nullable=False
    )
    expected_arrival: Optional[date] = Field(
        default=None
    )
    total_price: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        ge=0
    )
    order_status: str = Field(
        max_length=15,
        nullable=False
    )

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="orders")
    # partner: Optional[Partner] = Relationship(back_populates="store_orders")
    # items: list["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    """
    Order item - line items in a store order.

    Matches schema:
    - order_id: Foreign key to store_order (composite PK)
    - external_sku: Foreign key to external_product (composite PK)
    - partner_id: Foreign key to partner
    - quantity: Number of units ordered
    - deal_price: Price snapshot at order time
    """
    __tablename__ = "order_item"

    order_id: int = Field(
        foreign_key="store_order.order_id",
        primary_key=True,
        ondelete="CASCADE"
    )
    external_sku: str = Field(
        foreign_key="external_product.external_sku",
        primary_key=True,
        ondelete="RESTRICT"
    )
    partner_id: int = Field(
        foreign_key="partner.partner_id",
        nullable=False
    )
    quantity: int = Field(
        nullable=False,
        gt=0
    )
    deal_price: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False
    )

    # Relationships
    # order: Optional[StoreOrder] = Relationship(back_populates="items")
    # product: Optional[ExternalProduct] = Relationship(back_populates="order_items")
