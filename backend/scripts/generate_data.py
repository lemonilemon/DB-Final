"""
Data Generation Script for NEW Fridge Final Project

Generates realistic test data:
- Small tables: 100-1000 rows
- Large tables: 10,000-100,000 rows

Usage:
    python scripts/generate_data.py
"""

import asyncio
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from faker import Faker

from database import init_db, get_async_session_context
from models import (
    User, UserRole, Fridge, FridgeAccess, Ingredient, FridgeItem,
    Partner, ExternalProduct, ShoppingListItem, StoreOrder, OrderItem,
    Recipe, RecipeRequirement, RecipeStep, RecipeReview, MealPlan
)
from core.security import get_password_hash

fake = Faker()

# Data configuration
NUM_USERS = 500
NUM_FRIDGES = 300
NUM_INGREDIENTS = 150
NUM_RECIPES = 800
NUM_PARTNERS = 20
NUM_PRODUCTS = 800
NUM_FRIDGE_ITEMS = 50000  # LARGE TABLE
NUM_MEAL_PLANS = 20000    # LARGE TABLE
NUM_REVIEWS = 10000       # LARGE TABLE
NUM_ORDERS = 8000
NUM_ORDER_ITEMS = 25000


# Realistic data
CATEGORIES = [
    "Dairy", "Protein", "Vegetables", "Fruits", "Grains",
    "Condiments", "Beverages", "Snacks", "Frozen", "Bakery"
]

UNITS = ["ml", "g", "unit", "kg", "L", "oz", "lb", "piece"]

INGREDIENT_NAMES = [
    # Dairy
    "Milk", "Cheese", "Yogurt", "Butter", "Cream", "Sour Cream",
    # Protein
    "Eggs", "Chicken Breast", "Ground Beef", "Salmon", "Tofu", "Bacon",
    "Pork Chops", "Turkey", "Shrimp", "Tuna",
    # Vegetables
    "Tomato", "Onion", "Garlic", "Carrot", "Broccoli", "Spinach",
    "Lettuce", "Bell Pepper", "Cucumber", "Potato", "Mushroom",
    # Fruits
    "Apple", "Banana", "Orange", "Strawberry", "Blueberry", "Lemon",
    # Grains
    "Rice", "Pasta", "Bread", "Flour", "Oats", "Quinoa",
    # Condiments
    "Soy Sauce", "Olive Oil", "Salt", "Pepper", "Ketchup", "Mustard",
    "Mayo", "Hot Sauce", "Vinegar", "Sugar", "Honey",
    # Beverages
    "Orange Juice", "Coffee", "Tea", "Soda", "Beer", "Wine",
    # Snacks
    "Chips", "Cookies", "Crackers", "Nuts", "Chocolate",
    # Frozen
    "Ice Cream", "Frozen Peas", "Frozen Pizza",
    # Bakery
    "Bagel", "Muffin", "Croissant"
]

RECIPE_NAMES = [
    "Scrambled Eggs", "Fried Rice", "Chicken Stir Fry", "Spaghetti Carbonara",
    "Caesar Salad", "Grilled Salmon", "Beef Tacos", "Vegetable Curry",
    "Pancakes", "French Toast", "Omelette", "Club Sandwich",
    "Chicken Soup", "Beef Stew", "Chili", "Mac and Cheese",
    "Pizza Margherita", "Lasagna", "Pad Thai", "Sushi Rolls",
    "Burrito Bowl", "Greek Salad", "Caprese Salad", "Tomato Soup",
    "Grilled Cheese", "BLT Sandwich", "Quesadilla", "Nachos",
    "Fish and Chips", "Shepherd's Pie", "Meatloaf", "Pot Roast"
]

PARTNER_NAMES = [
    "SuperMart", "FreshFoods", "QuickStop", "MegaStore", "ValueMarket",
    "OrganicPlus", "FarmFresh", "CityGrocer", "BulkBuy", "PrimeFood",
    "HealthMart", "GreenGrocer", "LocalMarket", "FastMart", "SaveMore",
    "TopChoice", "BestBuy Groceries", "FreshExpress", "DailyMart", "EcoStore"
]


async def generate_users(session):
    """Generate realistic users"""
    print(f"Generating {NUM_USERS} users...")
    users = []

    # Create general role
    general_role = UserRole(role_name="General User")
    session.add(general_role)
    await session.flush()

    for i in range(NUM_USERS):
        user = User(
            user_id=uuid4(),
            user_name=fake.user_name() + str(i),  # Ensure unique
            email=fake.email(),
            password=get_password_hash("password123"),  # Same password for testing
            status="Active"
        )
        session.add(user)
        users.append(user)

        if i % 100 == 0:
            await session.flush()
            print(f"  Created {i} users...")

    await session.flush()
    print(f"✓ Created {len(users)} users")
    return users


async def generate_ingredients(session):
    """Generate ingredient catalog"""
    print(f"Generating {NUM_INGREDIENTS} ingredients...")
    ingredients = []

    for i in range(NUM_INGREDIENTS):
        if i < len(INGREDIENT_NAMES):
            name = INGREDIENT_NAMES[i]
        else:
            name = f"{fake.word().capitalize()} {random.choice(['Mix', 'Blend', 'Special', 'Fresh'])}"

        ingredient = Ingredient(
            name=name,
            standard_unit=random.choice(UNITS),
            category=random.choice(CATEGORIES)
        )
        session.add(ingredient)
        ingredients.append(ingredient)

    await session.flush()
    print(f"✓ Created {len(ingredients)} ingredients")
    return ingredients


async def generate_fridges(session, users):
    """Generate fridges with owners"""
    print(f"Generating {NUM_FRIDGES} fridges...")
    fridges = []

    for i in range(NUM_FRIDGES):
        owner = random.choice(users)

        fridge = Fridge(
            fridge_id=uuid4(),
            creator_id=owner.user_id,
            fridge_name=f"{fake.word().capitalize()} Fridge",
            description=fake.sentence()
        )
        session.add(fridge)

        # Owner access
        access = FridgeAccess(
            fridge_id=fridge.fridge_id,
            user_id=owner.user_id,
            role="Owner"
        )
        session.add(access)

        # Add 1-3 members randomly
        num_members = random.randint(0, 3)
        members = random.sample(users, min(num_members, len(users)))
        for member in members:
            if member.user_id != owner.user_id:
                member_access = FridgeAccess(
                    fridge_id=fridge.fridge_id,
                    user_id=member.user_id,
                    role="Member"
                )
                session.add(member_access)

        fridges.append(fridge)

        if i % 100 == 0:
            await session.flush()
            print(f"  Created {i} fridges...")

    await session.flush()
    print(f"✓ Created {len(fridges)} fridges with members")
    return fridges


async def generate_fridge_items(session, fridges, ingredients):
    """Generate LARGE dataset of fridge items (50,000+)"""
    print(f"Generating {NUM_FRIDGE_ITEMS} fridge items...")
    items = []

    for i in range(NUM_FRIDGE_ITEMS):
        fridge = random.choice(fridges)
        ingredient = random.choice(ingredients)

        # Realistic quantities based on unit
        if ingredient.standard_unit in ["ml", "L"]:
            quantity = Decimal(random.randint(100, 2000))
        elif ingredient.standard_unit in ["g", "kg"]:
            quantity = Decimal(random.randint(50, 1000))
        else:  # units, pieces
            quantity = Decimal(random.randint(1, 20))

        # Entry date: within last 30 days
        entry_date = date.today() - timedelta(days=random.randint(0, 30))

        # Expiry date: 1-60 days from entry
        expiry_date = entry_date + timedelta(days=random.randint(1, 60))

        item = FridgeItem(
            fridge_id=fridge.fridge_id,
            ingredient_id=ingredient.ingredient_id,
            quantity=quantity,
            entry_date=entry_date,
            expiry_date=expiry_date
        )
        session.add(item)
        items.append(item)

        if i % 1000 == 0:
            await session.flush()
            print(f"  Created {i} fridge items...")

    await session.flush()
    print(f"✓ Created {len(items)} fridge items")
    return items


async def generate_recipes(session, users, ingredients):
    """Generate recipes with requirements and steps"""
    print(f"Generating {NUM_RECIPES} recipes...")
    recipes = []

    for i in range(NUM_RECIPES):
        owner = random.choice(users)

        # Recipe name
        if i < len(RECIPE_NAMES):
            name = RECIPE_NAMES[i]
        else:
            name = f"{fake.word().capitalize()} {random.choice(['Delight', 'Special', 'Supreme', 'Classic'])}"

        recipe = Recipe(
            owner_id=owner.user_id,
            recipe_name=name,
            description=fake.sentence(),
            cooking_time=random.randint(10, 120),
            status="Published",
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
            updated_at=datetime.utcnow()
        )
        session.add(recipe)
        await session.flush()  # Get recipe_id

        # Add 2-6 ingredients
        num_ingredients = random.randint(2, 6)
        recipe_ingredients = random.sample(ingredients, num_ingredients)

        for ing in recipe_ingredients:
            if ing.standard_unit in ["ml", "L"]:
                qty = Decimal(random.randint(50, 500))
            elif ing.standard_unit in ["g", "kg"]:
                qty = Decimal(random.randint(50, 500))
            else:
                qty = Decimal(random.randint(1, 10))

            req = RecipeRequirement(
                recipe_id=recipe.recipe_id,
                ingredient_id=ing.ingredient_id,
                quantity_needed=qty
            )
            session.add(req)

        # Add 3-8 steps
        num_steps = random.randint(3, 8)
        for step_num in range(1, num_steps + 1):
            step = RecipeStep(
                recipe_id=recipe.recipe_id,
                step_number=step_num,
                description=fake.sentence()
            )
            session.add(step)

        recipes.append(recipe)

        if i % 100 == 0:
            await session.flush()
            print(f"  Created {i} recipes...")

    await session.flush()
    print(f"✓ Created {len(recipes)} recipes with requirements and steps")
    return recipes


async def generate_reviews(session, users, recipes):
    """Generate LARGE dataset of reviews (10,000+)"""
    print(f"Generating {NUM_REVIEWS} reviews...")
    reviews = []

    for i in range(NUM_REVIEWS):
        user = random.choice(users)
        recipe = random.choice(recipes)

        # Skip if already reviewed
        # (In production would check, but for speed we'll allow duplicates)

        # Realistic rating distribution (more 4-5 stars)
        rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0]

        review = RecipeReview(
            user_id=user.user_id,
            recipe_id=recipe.recipe_id,
            rating=rating,
            comment=fake.sentence() if random.random() > 0.3 else None,
            review_date=datetime.utcnow() - timedelta(days=random.randint(0, 365))
        )
        session.add(review)
        reviews.append(review)

        if i % 1000 == 0:
            await session.flush()
            print(f"  Created {i} reviews...")

    await session.flush()
    print(f"✓ Created {len(reviews)} reviews")
    return reviews


async def generate_meal_plans(session, users, recipes):
    """Generate LARGE dataset of meal plans (20,000+)"""
    print(f"Generating {NUM_MEAL_PLANS} meal plans...")
    plans = []

    for i in range(NUM_MEAL_PLANS):
        user = random.choice(users)
        recipe = random.choice(recipes)

        # Mix of past, present, and future plans
        days_offset = random.randint(-365, 60)  # 1 year past to 2 months future
        planned_date = datetime.combine(
            date.today() + timedelta(days=days_offset),
            datetime.min.time()
        )

        # Status based on date
        if days_offset < -1:
            # Past plans - mostly finished
            status = random.choices(
                ["Finished", "Canceled"],
                weights=[85, 15]
            )[0]
        elif days_offset > 14:
            status = "Planned"  # Too far
        else:
            # Near future - mix of statuses
            status = random.choices(
                ["Ready", "Insufficient", "Planned"],
                weights=[50, 30, 20]
            )[0]

        plan = MealPlan(
            user_id=user.user_id,
            recipe_id=recipe.recipe_id,
            planned_date=planned_date,
            status=status
        )
        session.add(plan)
        plans.append(plan)

        if i % 1000 == 0:
            await session.flush()
            print(f"  Created {i} meal plans...")

    await session.flush()
    print(f"✓ Created {len(plans)} meal plans")
    return plans


async def generate_partners(session):
    """Generate partners/suppliers"""
    print(f"Generating {NUM_PARTNERS} partners...")
    partners = []

    for i in range(NUM_PARTNERS):
        partner = Partner(
            partner_name=PARTNER_NAMES[i] if i < len(PARTNER_NAMES) else fake.company(),
            contract_date=date.today() - timedelta(days=random.randint(30, 1000)),
            avg_shipping_days=random.randint(1, 7),
            credit_score=random.randint(60, 100)
        )
        session.add(partner)
        partners.append(partner)

    await session.flush()
    print(f"✓ Created {len(partners)} partners")
    return partners


async def generate_products(session, partners, ingredients):
    """Generate external products"""
    print(f"Generating {NUM_PRODUCTS} products...")
    products = []

    for i in range(NUM_PRODUCTS):
        partner = random.choice(partners)
        ingredient = random.choice(ingredients)

        # Price varies by partner and ingredient
        base_price = Decimal(random.uniform(1.0, 50.0))

        product = ExternalProduct(
            external_sku=f"{partner.partner_name[:2].upper()}-{ingredient.name[:4].upper()}-{i}",
            partner_id=partner.partner_id,
            ingredient_id=ingredient.ingredient_id,
            product_name=f"{ingredient.name} - {partner.partner_name}",
            current_price=round(base_price, 2),
            selling_unit=f"1 {ingredient.standard_unit}"
        )
        session.add(product)
        products.append(product)

        if i % 100 == 0:
            await session.flush()
            print(f"  Created {i} products...")

    await session.flush()
    print(f"✓ Created {len(products)} products")
    return products


async def generate_orders(session, users, partners, products):
    """Generate store orders with items"""
    print(f"Generating {NUM_ORDERS} orders...")
    orders = []

    for i in range(NUM_ORDERS):
        user = random.choice(users)
        partner = random.choice(partners)

        # Order date: within last year
        order_date = datetime.utcnow() - timedelta(days=random.randint(0, 365))
        expected_arrival = order_date.date() + timedelta(days=partner.avg_shipping_days)

        # Status based on date
        days_ago = (datetime.utcnow() - order_date).days
        if days_ago > partner.avg_shipping_days + 5:
            status = "Delivered"
        elif days_ago > partner.avg_shipping_days:
            status = random.choice(["Shipped", "Delivered"])
        elif days_ago > 1:
            status = random.choice(["Processing", "Shipped"])
        else:
            status = "Pending"

        # Get products from this partner
        partner_products = [p for p in products if p.partner_id == partner.partner_id]
        if not partner_products:
            continue

        # Add 1-5 items
        num_items = random.randint(1, 5)
        order_items_list = random.sample(partner_products, min(num_items, len(partner_products)))

        total_price = Decimal(0)

        order = StoreOrder(
            user_id=user.user_id,
            partner_id=partner.partner_id,
            order_date=order_date,
            expected_arrival=expected_arrival,
            total_price=Decimal(0),  # Will update
            order_status=status
        )
        session.add(order)
        await session.flush()  # Get order_id

        # Add order items
        for product in order_items_list:
            quantity = random.randint(1, 5)
            subtotal = product.current_price * quantity
            total_price += subtotal

            order_item = OrderItem(
                order_id=order.order_id,
                external_sku=product.external_sku,
                partner_id=partner.partner_id,
                quantity=quantity,
                deal_price=product.current_price
            )
            session.add(order_item)

        order.total_price = total_price
        session.add(order)
        orders.append(order)

        if i % 100 == 0:
            await session.flush()
            print(f"  Created {i} orders...")

    await session.flush()
    print(f"✓ Created {len(orders)} orders")
    return orders


async def main():
    """Generate all data"""
    print("=" * 60)
    print("NEW Fridge Data Generation Script")
    print("=" * 60)
    print()

    # Initialize database
    await init_db()

    async with get_async_session_context() as session:
        # Generate data in order (respecting foreign keys)
        users = await generate_users(session)
        ingredients = await generate_ingredients(session)
        fridges = await generate_fridges(session, users)

        # LARGE TABLE 1: Fridge Items (50,000+)
        await generate_fridge_items(session, fridges, ingredients)

        recipes = await generate_recipes(session, users, ingredients)

        # LARGE TABLE 2: Reviews (10,000+)
        await generate_reviews(session, users, recipes)

        # LARGE TABLE 3: Meal Plans (20,000+)
        await generate_meal_plans(session, users, recipes)

        partners = await generate_partners(session)
        products = await generate_products(session, partners, ingredients)
        orders = await generate_orders(session, users, partners, products)

        await session.commit()

    print()
    print("=" * 60)
    print("✓ Data generation complete!")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  Users:         {NUM_USERS:,}")
    print(f"  Fridges:       {NUM_FRIDGES:,}")
    print(f"  Ingredients:   {NUM_INGREDIENTS:,}")
    print(f"  Fridge Items:  {NUM_FRIDGE_ITEMS:,} ⭐ LARGE TABLE")
    print(f"  Recipes:       {NUM_RECIPES:,}")
    print(f"  Reviews:       {NUM_REVIEWS:,} ⭐ LARGE TABLE")
    print(f"  Meal Plans:    {NUM_MEAL_PLANS:,} ⭐ LARGE TABLE")
    print(f"  Partners:      {NUM_PARTNERS:,}")
    print(f"  Products:      {NUM_PRODUCTS:,}")
    print(f"  Orders:        {NUM_ORDERS:,}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
