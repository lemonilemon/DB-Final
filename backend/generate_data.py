"""
Generate realistic test data for NEW Fridge database.

Focuses on core tables with high-quality, realistic data.
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Import database connection
from database import init_db, async_session_maker

# Import models
from models import (
    User, Fridge, FridgeAccess, Ingredient, FridgeItem,
    Partner, ExternalProduct, StoreOrder, OrderItem,
    Recipe, RecipeRequirement, RecipeStep
)

# Initialize Faker
fake = Faker()

# Real ingredient data
INGREDIENTS = [
    # Vegetables
    ("Tomato", "g", 7), ("Onion", "g", 14), ("Carrot", "g", 14),
    ("Potato", "g", 21), ("Lettuce", "g", 7), ("Cucumber", "g", 7),
    ("Bell Pepper", "g", 7), ("Broccoli", "g", 7), ("Spinach", "g", 5),
    ("Cabbage", "g", 14), ("Garlic", "g", 30), ("Ginger", "g", 21),

    # Fruits
    ("Apple", "pcs", 14), ("Banana", "pcs", 7), ("Orange", "pcs", 10),
    ("Grape", "g", 7), ("Strawberry", "g", 5), ("Lemon", "pcs", 21),

    # Dairy
    ("Milk", "ml", 7), ("Cheese", "g", 21), ("Yogurt", "ml", 14),
    ("Butter", "g", 30), ("Eggs", "pcs", 21), ("Cream", "ml", 7),

    # Meat & Seafood
    ("Chicken Breast", "g", 2), ("Pork Chop", "g", 2),
    ("Beef Steak", "g", 3), ("Ground Beef", "g", 2),
    ("Salmon", "g", 2), ("Shrimp", "g", 2),

    # Grains & Staples
    ("Rice", "g", 365), ("Pasta", "g", 365), ("Bread", "pcs", 7),
    ("Flour", "g", 180), ("Noodles", "g", 365),

    # Condiments
    ("Salt", "g", 365), ("Pepper", "g", 365), ("Sugar", "g", 365),
    ("Soy Sauce", "ml", 365), ("Olive Oil", "ml", 365), ("Vinegar", "ml", 365),
]

# Real recipes
RECIPES = [
    {
        "name": "Scrambled Eggs",
        "description": "Quick and easy breakfast",
        "time": 10,
        "ingredients": {"Eggs": 2, "Butter": 10, "Salt": 2, "Pepper": 1},
        "steps": ["Beat eggs in a bowl", "Melt butter in pan", "Cook eggs while stirring", "Serve hot"]
    },
    {
        "name": "Spaghetti Carbonara",
        "description": "Classic Italian pasta",
        "time": 25,
        "ingredients": {"Pasta": 200, "Eggs": 2, "Cheese": 50, "Pepper": 2},
        "steps": ["Boil pasta", "Mix eggs and cheese", "Drain pasta", "Mix with egg mixture", "Serve immediately"]
    },
    {
        "name": "Chicken Stir Fry",
        "description": "Quick Asian-style dish",
        "time": 20,
        "ingredients": {"Chicken Breast": 300, "Soy Sauce": 30, "Garlic": 10, "Ginger": 10, "Bell Pepper": 100},
        "steps": ["Cut chicken into pieces", "Heat oil in wok", "Stir fry chicken", "Add vegetables", "Add sauce and serve"]
    },
    {
        "name": "Caesar Salad",
        "description": "Fresh and healthy",
        "time": 15,
        "ingredients": {"Lettuce": 200, "Cheese": 30, "Bread": 2},
        "steps": ["Wash and chop lettuce", "Toast bread for croutons", "Mix with dressing", "Top with cheese"]
    },
]


async def create_users(session: AsyncSession, count=100):
    """Create realistic users."""
    print(f"Creating {count} users...")
    users = []

    for i in range(count):
        base_username = fake.user_name()
        # Reserve space for index number (e.g., "99" = 2 chars, "999" = 3 chars)
        max_base_length = 20 - len(str(i)) if i > 0 else 20
        username = f"{base_username[:max_base_length]}{i}" if i > 0 else base_username[:20]

        # Ensure unique email by adding index
        email_parts = fake.email().split('@')
        unique_email = f"{email_parts[0]}{i}@{email_parts[1]}"

        user = User(
            user_name=username,
            email=unique_email,
            password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfZl3w3aCK",  # "password123"
            status="Active",
            role="Admin" if i < 3 else "User"
        )
        users.append(user)

    session.add_all(users)
    await session.commit()
    print(f"✓ Created {len(users)} users (3 admins, {len(users)-3} regular users)")
    return users


async def create_ingredients(session: AsyncSession):
    """Create ingredient catalog."""
    print(f"Creating {len(INGREDIENTS)} ingredients...")
    ingredients = []

    for name, unit, shelf_life in INGREDIENTS:
        ingredient = Ingredient(
            name=name,
            standard_unit=unit,
            shelf_life_days=shelf_life
        )
        ingredients.append(ingredient)

    session.add_all(ingredients)
    await session.commit()
    await session.refresh(ingredients[0])
    print(f"✓ Created {len(ingredients)} ingredients")
    return ingredients


async def create_fridges(session: AsyncSession, users, count=50):
    """Create fridges with shared access."""
    print(f"Creating {count} fridges...")
    fridges = []
    accesses = []

    fridge_names = ["Home Fridge", "Work Fridge", "Dorm Fridge", "Garage Fridge", "Office Fridge"]

    for i in range(count):
        # Create fridge
        fridge = Fridge(
            fridge_name=f"{random.choice(fridge_names)} #{i+1}",
            description=fake.sentence() if random.random() > 0.5 else None
        )
        session.add(fridge)
        await session.flush()

        # Owner
        owner = random.choice(users)
        accesses.append(FridgeAccess(
            fridge_id=fridge.fridge_id,
            user_id=owner.user_id,
            access_role="Owner"
        ))

        # Add 0-2 members
        num_members = random.randint(0, 2)
        available_users = [u for u in users if u.user_id != owner.user_id]
        for member in random.sample(available_users, min(num_members, len(available_users))):
            accesses.append(FridgeAccess(
                fridge_id=fridge.fridge_id,
                user_id=member.user_id,
                access_role="Member"
            ))

        fridges.append(fridge)

    session.add_all(accesses)
    await session.commit()
    print(f"✓ Created {len(fridges)} fridges with {len(accesses)} access permissions")
    return fridges


async def create_fridge_items(session: AsyncSession, fridges, ingredients, count=1000):
    """Create fridge inventory items."""
    print(f"Creating {count} fridge items...")

    batch_size = 500
    total_created = 0

    for batch_num in range(0, count, batch_size):
        items = []
        for _ in range(min(batch_size, count - batch_num)):
            fridge = random.choice(fridges)
            ingredient = random.choice(ingredients)

            # Realistic quantities
            if ingredient.standard_unit == "g":
                qty = random.choice([100, 200, 500, 1000])
            elif ingredient.standard_unit == "ml":
                qty = random.choice([250, 500, 1000])
            else:  # pcs
                qty = random.randint(1, 12)

            # Dates
            days_ago = random.randint(0, 14)
            entry_date = datetime.now().date() - timedelta(days=days_ago)
            expiry_date = entry_date + timedelta(days=ingredient.shelf_life_days)

            items.append(FridgeItem(
                fridge_id=fridge.fridge_id,
                ingredient_id=ingredient.ingredient_id,
                quantity=Decimal(str(qty)),
                entry_date=entry_date,
                expiry_date=expiry_date
            ))

        session.add_all(items)
        await session.commit()
        total_created += len(items)
        print(f"  Progress: {total_created}/{count}")

    print(f"✓ Created {total_created} fridge items")


async def create_recipes(session: AsyncSession, users, ingredients):
    """Create realistic recipes."""
    print(f"Creating {len(RECIPES)} recipes...")

    ing_map = {ing.name: ing for ing in ingredients}
    recipes = []

    for recipe_data in RECIPES:
        # Create recipe
        recipe = Recipe(
            owner_id=random.choice(users).user_id,
            recipe_name=recipe_data["name"],
            description=recipe_data["description"],
            cooking_time=recipe_data["time"],
            status="Approved"
        )
        session.add(recipe)
        await session.flush()

        # Add ingredients
        for ing_name, qty in recipe_data["ingredients"].items():
            if ing_name in ing_map:
                session.add(RecipeRequirement(
                    recipe_id=recipe.recipe_id,
                    ingredient_id=ing_map[ing_name].ingredient_id,
                    quantity_needed=Decimal(str(qty))
                ))

        # Add steps
        for i, step_text in enumerate(recipe_data["steps"], 1):
            session.add(RecipeStep(
                recipe_id=recipe.recipe_id,
                step_number=i,
                description=step_text
            ))

        recipes.append(recipe)

    await session.commit()
    print(f"✓ Created {len(recipes)} recipes")
    return recipes


async def create_partners(session: AsyncSession, ingredients, num_partners=10):
    """Create partners and products."""
    print(f"Creating {num_partners} partners...")

    partner_names = [
        "FreshMart", "Sunny Foods", "Green Valley", "Ocean Harvest",
        "Farm Direct", "Quality Meats", "Dairy Best", "Organic Plus",
        "Local Market", "Fresh Express"
    ]

    partners = []
    products = []

    for name in partner_names[:num_partners]:
        partner = Partner(
            partner_name=name,
            contract_date=datetime.now().date() - timedelta(days=random.randint(30, 500)),
            avg_shipping_days=random.randint(1, 5),
            credit_score=random.randint(70, 100)
        )
        partners.append(partner)

    session.add_all(partners)
    await session.commit()
    await session.refresh(partners[0])

    # Create products
    for partner in partners:
        # Each partner sells 15-25 ingredients
        num_products = random.randint(15, 25)
        for ingredient in random.sample(ingredients, num_products):
            # Generate realistic SKU based on ingredient name (partners can use their own SKU systems)
            # Convert ingredient name to SKU-friendly format (uppercase, no spaces)
            ingredient_sku_part = ingredient.name.upper().replace(" ", "-")
            sku = f"{ingredient_sku_part}"

            # Generate realistic selling_unit and unit_quantity based on ingredient type
            if ingredient.standard_unit == "g":
                # Weight-based: 100g, 250g, 500g, 1kg packages
                package_size = random.choice([100, 250, 500, 1000])
                selling_unit = f"{package_size}g Pack"
                unit_quantity = package_size
            elif ingredient.standard_unit == "ml":
                # Volume-based: 250ml, 500ml, 1L, 2L bottles
                package_size = random.choice([250, 500, 1000, 2000])
                if package_size >= 1000:
                    selling_unit = f"{package_size//1000}L Bottle"
                else:
                    selling_unit = f"{package_size}ml Bottle"
                unit_quantity = package_size
            else:  # pcs
                # Count-based: 1pc, 6-pack, 12-pack
                package_size = random.choice([1, 6, 12])
                if package_size == 1:
                    selling_unit = "1 piece"
                else:
                    selling_unit = f"{package_size}-Pack"
                unit_quantity = package_size

            products.append(ExternalProduct(
                external_sku=sku,
                partner_id=partner.partner_id,
                ingredient_id=ingredient.ingredient_id,
                product_name=f"{ingredient.name} {selling_unit} - {partner.partner_name}",
                current_price=Decimal(str(round(random.uniform(2.99, 49.99), 2))),
                selling_unit=selling_unit,
                unit_quantity=Decimal(str(unit_quantity))
            ))

    session.add_all(products)
    await session.commit()
    print(f"✓ Created {len(partners)} partners with {len(products)} products")
    return partners, products


async def create_orders(session: AsyncSession, users, partners, products, count=200):
    """Create store orders."""
    print(f"Creating {count} orders...")

    statuses = ["Pending", "Paid", "Shipped", "Delivered", "Cancelled"]
    orders = []
    order_items = []

    for _ in range(count):
        user = random.choice(users)
        partner = random.choice(partners)

        # Get fridges that this user has access to
        result = await session.execute(
            text("SELECT fridge_id FROM fridge_access WHERE user_id = :user_id"),
            {"user_id": user.user_id}
        )
        user_fridges = result.fetchall()

        if not user_fridges:
            continue  # Skip if user has no fridge access

        fridge_id = random.choice(user_fridges)[0]

        order_date = datetime.now() - timedelta(days=random.randint(0, 90))
        expected_arrival = order_date.date() + timedelta(days=partner.avg_shipping_days)

        order = StoreOrder(
            user_id=user.user_id,
            partner_id=partner.partner_id,
            fridge_id=fridge_id,
            order_date=order_date,
            expected_arrival=expected_arrival,
            total_price=Decimal("0"),
            order_status=random.choice(statuses)
        )
        session.add(order)
        await session.flush()

        # Add 1-4 items
        partner_products = [p for p in products if p.partner_id == partner.partner_id]
        num_items = random.randint(1, 4)
        total = Decimal("0")

        for product in random.sample(partner_products, min(num_items, len(partner_products))):
            qty = random.randint(1, 5)
            price = product.current_price

            order_items.append(OrderItem(
                order_id=order.order_id,
                external_sku=product.external_sku,
                partner_id=partner.partner_id,
                quantity=qty,
                deal_price=price
            ))
            total += price * qty

        order.total_price = total
        orders.append(order)

    session.add_all(order_items)
    await session.commit()
    print(f"✓ Created {len(orders)} orders with {len(order_items)} items")


async def main():
    """Generate all test data."""
    print("\n" + "="*60)
    print("NEW Fridge - Test Data Generator")
    print("="*60 + "\n")

    await init_db()

    async with async_session_maker() as session:
        users = await create_users(session, count=500)
        ingredients = await create_ingredients(session)
        fridges = await create_fridges(session, users, count=200)
        await create_fridge_items(session, fridges, ingredients, count=50000)
        recipes = await create_recipes(session, users, ingredients)
        partners, products = await create_partners(session, ingredients, num_partners=10)
        await create_orders(session, users, partners, products, count=10000)

    print("\n" + "="*60)
    print("✓ Data generation complete!")
    print("="*60)
    print("\nSummary:")
    print("  • 500 users (3 admins)")
    print("  • 41 ingredients")
    print("  • 200 fridges")
    print("  • 50,000 fridge items")
    print("  • 4 recipes")
    print("  • 10 partners")
    print("  • ~200 products")
    print("  • 10,000 orders")
    print("  • ~25,000 order items")
    print("\nTotal: ~85,000+ records\n")


if __name__ == "__main__":
    asyncio.run(main())
