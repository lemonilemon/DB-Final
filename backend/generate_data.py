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
from core.security import hash_password

# Import models
from models import (
    User, Fridge, FridgeAccess, Ingredient, FridgeItem,
    Partner, ExternalProduct, StoreOrder, OrderItem,
    Recipe, RecipeRequirement, RecipeStep, RecipeReview, MealPlan
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

# High Quality Handmade Recipes
HANDMADE_RECIPES = [
    {
        "name": "Classic Scrambled Eggs",
        "description": "Fluffy, creamy, and perfect scrambled eggs for a quick breakfast.",
        "time": 10,
        "ingredients": {"Eggs": 3, "Butter": 10, "Salt": 2, "Pepper": 1, "Milk": 30},
        "steps": [
            "Crack the eggs into a bowl and whisk until yolks and whites are combined.",
            "Add milk, salt, and pepper, and whisk again.",
            "Melt butter in a non-stick pan over medium heat.",
            "Pour in the eggs and let them sit for a moment until the edges start to set.",
            "Gently push the eggs across the pan with a spatula to form soft curds.",
            "Cook until the eggs are set but still moist. Serve immediately."
        ]
    },
    {
        "name": "Spaghetti Carbonara",
        "description": "A traditional Italian pasta dish made with eggs, cheese, and pepper. No cream needed!",
        "time": 25,
        "ingredients": {"Pasta": 200, "Eggs": 2, "Cheese": 50, "Pepper": 5, "Salt": 10},
        "steps": [
            "Bring a large pot of salted water to a boil and cook the pasta.",
            "In a bowl, whisk eggs and grated cheese together with plenty of black pepper.",
            "Drain the pasta, reserving some cooking water.",
            "Toss the hot pasta with the egg and cheese mixture quickly so the heat cooks the eggs without scrambling them.",
            "Add a splash of pasta water if needed to create a creamy sauce.",
            "Serve immediately with extra cheese."
        ]
    },
    {
        "name": "Chicken Stir-Fry",
        "description": "A healthy and colorful stir-fry with fresh vegetables and tender chicken.",
        "time": 20,
        "ingredients": {"Chicken Breast": 300, "Soy Sauce": 30, "Garlic": 10, "Ginger": 10, "Bell Pepper": 100, "Broccoli": 100, "Carrot": 50, "Olive Oil": 15},
        "steps": [
            "Slice chicken breast into thin strips.",
            "Chop broccoli, bell pepper, and carrot into bite-sized pieces.",
            "Heat oil in a wok or large pan over high heat.",
            "Add chicken and stir-fry until browned and cooked through. Remove from pan.",
            "Add garlic, ginger, and vegetables to the pan. Stir-fry for 3-5 minutes.",
            "Return chicken to the pan, add soy sauce, and toss everything together.",
            "Serve hot over rice."
        ]
    },
    {
        "name": "Garlic Butter Shrimp",
        "description": "Succulent shrimp cooked in a rich garlic butter sauce.",
        "time": 15,
        "ingredients": {"Shrimp": 300, "Butter": 40, "Garlic": 15, "Lemon": 1, "Salt": 3, "Pepper": 2},
        "steps": [
            "Peel and devein the shrimp.",
            "Melt butter in a skillet over medium heat.",
            "Add minced garlic and cook for 1 minute until fragrant.",
            "Add shrimp in a single layer and cook for 2-3 minutes per side until pink.",
            "Squeeze fresh lemon juice over the shrimp and season with salt and pepper.",
            "Serve immediately."
        ]
    },
    {
        "name": "Hearty Beef Stew",
        "description": "A comforting beef stew with potatoes and carrots, perfect for cold days.",
        "time": 120,
        "ingredients": {"Beef Steak": 500, "Potato": 300, "Carrot": 200, "Onion": 100, "Garlic": 10, "Salt": 5, "Pepper": 3, "Olive Oil": 20},
        "steps": [
            "Cut beef into cubes and season with salt and pepper.",
            "Sear beef in a large pot with oil until browned. Remove beef.",
            "Sauté chopped onions and garlic in the same pot.",
            "Add beef back to the pot along with chopped potatoes and carrots.",
            "Cover with water or broth and bring to a simmer.",
            "Cover and cook on low heat for 1.5 to 2 hours until beef is tender."
        ]
    },
    {
        "name": "Greek Salad",
        "description": "Fresh and crisp salad with cucumber, tomato, and tangy cheese.",
        "time": 10,
        "ingredients": {"Cucumber": 150, "Tomato": 150, "Onion": 30, "Cheese": 50, "Olive Oil": 20, "Vinegar": 10, "Salt": 2},
        "steps": [
            "Chop cucumber and tomato into chunks.",
            "Slice onion thinly.",
            "Combine vegetables in a bowl.",
            "Crumble cheese over the top.",
            "Drizzle with olive oil and vinegar, sprinkle with salt.",
            "Toss gently and serve."
        ]
    },
    {
        "name": "Fried Rice",
        "description": "The perfect way to use leftover rice. Savory and satisfying.",
        "time": 15,
        "ingredients": {"Rice": 400, "Eggs": 2, "Carrot": 50, "Onion": 50, "Soy Sauce": 20, "Garlic": 5, "Olive Oil": 15},
        "steps": [
            "Dice carrots and onions.",
            "Scramble eggs in a pan and set aside.",
            "Heat oil in the pan and sauté onions, carrots, and garlic.",
            "Add cooked rice (preferably cold) and stir-fry to break up clumps.",
            "Stir in soy sauce and cooked eggs.",
            "Cook for another 2 minutes until everything is hot and well combined."
        ]
    },
    {
        "name": "Oven Roasted Vegetables",
        "description": "Simple roasted vegetables that bring out their natural sweetness.",
        "time": 40,
        "ingredients": {"Potato": 200, "Carrot": 200, "Broccoli": 150, "Bell Pepper": 100, "Olive Oil": 30, "Salt": 5, "Pepper": 2, "Garlic": 10},
        "steps": [
            "Preheat oven to 400°F (200°C).",
            "Chop all vegetables into similar-sized pieces.",
            "Toss vegetables in a bowl with olive oil, minced garlic, salt, and pepper.",
            "Spread in a single layer on a baking sheet.",
            "Roast for 30-35 minutes, tossing halfway through, until tender and browned."
        ]
    },
    {
        "name": "Grilled Salmon",
        "description": "Healthy and delicious salmon fillets with a lemon butter glaze.",
        "time": 20,
        "ingredients": {"Salmon": 300, "Lemon": 1, "Butter": 20, "Salt": 3, "Pepper": 2, "Garlic": 5},
        "steps": [
            "Season salmon fillets with salt and pepper.",
            "Melt butter with minced garlic.",
            "Grill or pan-sear salmon for 4-5 minutes per side.",
            "Brush with garlic butter during the last minute of cooking.",
            "Serve with lemon wedges."
        ]
    },
    {
        "name": "Spinach and Cheese Omelet",
        "description": "A protein-packed breakfast with fresh spinach.",
        "time": 12,
        "ingredients": {"Eggs": 3, "Spinach": 50, "Cheese": 30, "Butter": 10, "Salt": 1, "Pepper": 1},
        "steps": [
            "Whisk eggs with salt and pepper.",
            "Sauté spinach in a pan with a little butter until wilted. Remove.",
            "Pour whisked eggs into the pan.",
            "When eggs are mostly set, add spinach and cheese to one half.",
            "Fold the omelet over and cook for another minute until cheese melts."
        ]
    },
    {
        "name": "Pork Chop with Apples",
        "description": "Savory pork chops paired with sweet cooked apples.",
        "time": 25,
        "ingredients": {"Pork Chop": 2, "Apple": 2, "Butter": 20, "Salt": 5, "Pepper": 3, "Sugar": 5},
        "steps": [
            "Season pork chops with salt and pepper.",
            "Sear chops in a skillet until cooked through. Remove and keep warm.",
            "Slice apples and add to the same skillet with butter and a pinch of sugar.",
            "Cook apples until soft and caramelized.",
            "Serve pork chops topped with the apples."
        ]
    },
    {
        "name": "Creamy Potato Soup",
        "description": "Rich and creamy soup, comfort food at its best.",
        "time": 40,
        "ingredients": {"Potato": 400, "Onion": 100, "Cream": 100, "Milk": 200, "Butter": 30, "Salt": 5, "Pepper": 2},
        "steps": [
            "Peel and dice potatoes and onion.",
            "Sauté onion in butter until soft.",
            "Add potatoes and cover with just enough water to submerge.",
            "Simmer until potatoes are very tender.",
            "Mash potatoes in the pot or blend lightly.",
            "Stir in milk and cream, heat through, and season."
        ]
    },
    {
        "name": "Fresh Fruit Salad",
        "description": "A refreshing mix of seasonal fruits.",
        "time": 10,
        "ingredients": {"Apple": 1, "Banana": 1, "Orange": 1, "Strawberry": 100, "Grape": 100, "Lemon": 1},
        "steps": [
            "Chop apple, banana, and orange into bite-sized pieces.",
            "Halve the strawberries and grapes.",
            "Combine all fruit in a large bowl.",
            "Squeeze fresh lemon juice over the fruit to prevent browning and add zest.",
            "Toss well and serve chilled."
        ]
    },
    {
        "name": "Garlic Bread",
        "description": "Crunchy, buttery, garlicky perfection.",
        "time": 15,
        "ingredients": {"Bread": 6, "Butter": 50, "Garlic": 15, "Salt": 2},
        "steps": [
            "Mix softened butter with minced garlic and a pinch of salt.",
            "Spread generously on slices of bread.",
            "Toast in the oven or a toaster oven until golden brown and crispy.",
            "Serve warm."
        ]
    },
    {
        "name": "Simple Tomato Salad",
        "description": "A light side dish letting fresh tomatoes shine.",
        "time": 5,
        "ingredients": {"Tomato": 300, "Onion": 30, "Olive Oil": 15, "Vinegar": 5, "Salt": 2, "Pepper": 1},
        "steps": [
            "Slice tomatoes into wedges.",
            "Slice onion very thinly.",
            "Arrange on a plate.",
            "Drizzle with olive oil and vinegar.",
            "Season with salt and fresh cracked pepper."
        ]
    }
]

REVIEW_COMMENTS = [
    ("Delicious! Will make again.", 5),
    ("Pretty good, but needed more salt.", 4),
    ("Quick and easy, perfect for a weeknight.", 5),
    ("My family loved it!", 5),
    ("Not bad, but the instructions were a bit unclear.", 3),
    ("I didn't have all the ingredients but it still turned out okay.", 4),
    ("Takes longer than the recipe says.", 3),
    ("Absolutely amazing flavor.", 5),
    ("A bit bland for my taste.", 2),
    ("Instructions were easy to follow.", 5),
    ("The texture was a bit off.", 3),
    ("Best version of this I've ever made.", 5),
    ("My kids even ate the vegetables!", 5),
    ("Too oily.", 2),
    ("Adding some chili flakes really improved it.", 4)
]


async def create_users(session: AsyncSession, count=100):
    """Create realistic users."""
    print(f"Creating {count} users...")
    users = []

    # 1. Create specific Test Admin
    admin_user = User(
        user_name="admin",
        email="admin@example.com",
        password=hash_password("admin"),
        status="Active",
        role="Admin"
    )
    users.append(admin_user)

    # 2. Create specific Test User
    regular_user = User(
        user_name="user",
        email="user@example.com",
        password=hash_password("user"),
        status="Active",
        role="User"
    )
    users.append(regular_user)

    # 3. Create random users
    for i in range(count - 2):
        base_username = fake.user_name()
        # Reserve space for index number
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
    print(f"✓ Created {len(users)} users (including 'admin' and 'user')")
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
    print(f"Creating {len(HANDMADE_RECIPES)} recipes...")

    ing_map = {ing.name: ing for ing in ingredients}
    recipes = []

    for recipe_data in HANDMADE_RECIPES:
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
            else:
                print(f"Warning: Ingredient '{ing_name}' not found for recipe '{recipe_data['name']}'")

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


async def create_reviews(session: AsyncSession, users, recipes, count=500):
    """Create recipe reviews."""
    print(f"Creating {count} recipe reviews...")
    
    reviews = []
    # Set of (user_id, recipe_id) to prevent duplicates
    reviewed_pairs = set()

    attempts = 0
    while len(reviews) < count and attempts < count * 3:
        attempts += 1
        user = random.choice(users)
        recipe = random.choice(recipes)
        
        # Don't let users review their own recipes (optional rule, but good for realism)
        if user.user_id == recipe.owner_id:
            continue
            
        if (user.user_id, recipe.recipe_id) in reviewed_pairs:
            continue

        comment, rating = random.choice(REVIEW_COMMENTS)
        
        # Add some randomness to rating
        if random.random() > 0.7:
            rating = max(1, min(5, rating + random.choice([-1, 1])))

        review = RecipeReview(
            user_id=user.user_id,
            recipe_id=recipe.recipe_id,
            rating=rating,
            comment=comment,
            review_date=datetime.now() - timedelta(days=random.randint(0, 180))
        )
        
        reviews.append(review)
        reviewed_pairs.add((user.user_id, recipe.recipe_id))

    session.add_all(reviews)
    await session.commit()
    print(f"✓ Created {len(reviews)} recipe reviews")


async def create_meal_plans(session: AsyncSession, users, recipes, count=1000):
    """Create user meal plans."""
    print(f"Creating {count} meal plans...")

    meal_plans = []
    statuses = ["Planned", "Ready", "Insufficient", "Finished", "Canceled"]

    attempts = 0
    while len(meal_plans) < count and attempts < count * 2:
        attempts += 1
        user = random.choice(users)
        recipe = random.choice(recipes)

        # Get fridges that this user has access to
        result = await session.execute(
            text("SELECT fridge_id FROM fridge_access WHERE user_id = :user_id"),
            {"user_id": user.user_id}
        )
        user_fridges = result.fetchall()

        if not user_fridges:
            continue  # Skip if user has no fridge access

        fridge_id = random.choice(user_fridges)[0]

        # Plan date between -30 days (past) and +30 days (future)
        days_offset = random.randint(-30, 30)
        planned_date = datetime.now() + timedelta(days=days_offset)

        # Determine logical status based on date
        if days_offset < 0:
            status = random.choice(["Finished", "Canceled", "Insufficient"]) # Past
        else:
            status = random.choice(["Planned", "Ready", "Insufficient"]) # Future

        plan = MealPlan(
            user_id=user.user_id,
            recipe_id=recipe.recipe_id,
            fridge_id=fridge_id,
            planned_date=planned_date,
            status=status
        )
        meal_plans.append(plan)

    session.add_all(meal_plans)
    await session.commit()
    print(f"✓ Created {len(meal_plans)} meal plans")


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
        # Generate partner code (first 2-3 letters of partner name)
        partner_code = ''.join([c for c in partner.partner_name if c.isupper() or c.isdigit()])[:3]
        if not partner_code:
            partner_code = partner.partner_name[:3].upper()

        # Each partner sells 15-25 ingredients
        num_products = random.randint(15, 25)
        for ingredient in random.sample(ingredients, num_products):
            # Generate realistic SKU with partner prefix
            ingredient_sku_part = ingredient.name.upper().replace(" ", "-")

            # Generate realistic selling_unit and package code
            if ingredient.standard_unit == "g":
                package_size = random.choice([100, 250, 500, 1000])
                selling_unit = f"{package_size}g Pack"
                unit_quantity = package_size
                package_code = f"{package_size}G"
            elif ingredient.standard_unit == "ml":
                package_size = random.choice([250, 500, 1000, 2000])
                if package_size >= 1000:
                    selling_unit = f"{package_size//1000}L Bottle"
                    package_code = f"{package_size//1000}L"
                else:
                    selling_unit = f"{package_size}ml Bottle"
                    package_code = f"{package_size}ML"
                unit_quantity = package_size
            else:  # pcs
                package_size = random.choice([1, 6, 12])
                if package_size == 1:
                    selling_unit = "1 piece"
                    package_code = "1PC"
                else:
                    selling_unit = f"{package_size}-Pack"
                    package_code = f"{package_size}PK"
                unit_quantity = package_size

            # Create descriptive SKU: PARTNER-INGREDIENT-SIZE
            # Example: FM-MILK-1L, GV-TOMATO-500G, OH-SHRIMP-6PK
            sku = f"{partner_code}-{ingredient_sku_part}-{package_code}"

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
        if not partner_products:
            continue

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
        # New functions
        await create_reviews(session, users, recipes, count=2000)
        await create_meal_plans(session, users, recipes, count=5000)
        
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
    print(f"  • {len(HANDMADE_RECIPES)} recipes")
    print("  • 2,000 recipe reviews")
    print("  • 5,000 meal plans")
    print("  • 10 partners")
    print("  • ~200 products")
    print("  • 10,000 orders")
    print("  • ~25,000 order items")
    print("\nTotal: ~92,000+ records\n")


if __name__ == "__main__":
    asyncio.run(main())