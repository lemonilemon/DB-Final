"""
Optimized Data Generation Script for NEW Fridge

Generates realistic test data using bulk inserts for performance.

Usage:
    python generate_data.py
"""

import asyncio
import random
import sys
import os
import time
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import List, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from database import init_db, async_session_maker
from models import (
    User, Fridge, FridgeAccess, Ingredient, FridgeItem,
    Partner, ExternalProduct, ShoppingListItem, StoreOrder, OrderItem,
    Recipe, RecipeRequirement, RecipeStep, RecipeReview, MealPlan,
    UserRoleEnum
)
from core.security import hash_password

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

BATCH_SIZE = 5000

# Realistic data constants
CATEGORIES = [
    "Dairy", "Protein", "Vegetables", "Fruits", "Grains",
    "Condiments", "Beverages", "Snacks", "Frozen", "Bakery"
]

UNITS = ["ml", "g", "pcs"]

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


async def generate_users(session: AsyncSession):
    """Generate users using bulk insert."""
    print(f"Generating {NUM_USERS} users...")
    users_data = []
    
    # 1. Test Admin
    users_data.append({
        "user_id": uuid4(),
        "user_name": "admin",
        "email": "admin@example.com",
        "password": hash_password("admin"),
        "status": "Active",
        "role": "Admin"
    })
    
    # 2. Random Users
    password_hash = hash_password("password123")  # Compute once
    
    for i in range(NUM_USERS - 1):
        users_data.append({
            "user_id": uuid4(),
            "user_name": f"{fake.user_name()[:12]}_{uuid4().hex[:6]}",
            "email": f"{uuid4().hex[:6]}_{fake.email()}",
            "password": password_hash,
            "status": "Active",
            "role": "Admin" if i < 4 else "User"
        })
        
    # Bulk insert
    for i in range(0, len(users_data), BATCH_SIZE):
        batch = users_data[i:i + BATCH_SIZE]
        await session.execute(insert(User), batch)
        print(f"  Inserted {min(i + BATCH_SIZE, len(users_data))} users...")
        
    await session.commit()
    print(f"✓ Created {len(users_data)} users")
    return users_data  # Returns dicts, not ORM objects (need to re-fetch if needed)


async def generate_ingredients(session: AsyncSession):
    """Generate ingredients using bulk insert."""
    print(f"Generating {NUM_INGREDIENTS} ingredients...")
    ingredients_data = []

    for i in range(NUM_INGREDIENTS):
        name = INGREDIENT_NAMES[i] if i < len(INGREDIENT_NAMES) else f"{fake.word().capitalize()} {random.choice(['Mix', 'Blend', 'Special', 'Fresh'])} {i}"
        
        ingredients_data.append({
            "name": name,
            "standard_unit": random.choice(UNITS),
            "shelf_life_days": random.randint(3, 365)
        })

    # Bulk insert
    await session.execute(insert(Ingredient), ingredients_data)
    await session.commit()
    print(f"✓ Created {len(ingredients_data)} ingredients")


async def generate_fridges(session: AsyncSession, user_ids: List[uuid4]):
    """Generate fridges and access."""
    print(f"Generating {NUM_FRIDGES} fridges...")
    fridge_data = []
    access_data = []
    
    generated_fridge_ids = []

    for i in range(NUM_FRIDGES):
        owner_id = random.choice(user_ids)
        fridge_id = uuid4()
        generated_fridge_ids.append(fridge_id)

        fridge_data.append({
            "fridge_id": fridge_id,
            "fridge_name": f"{fake.word().capitalize()} Fridge",
            "description": fake.sentence()
        })

        # Owner access
        access_data.append({
            "fridge_id": fridge_id,
            "user_id": owner_id,
            "access_role": "Owner"
        })

        # Random members
        num_members = random.randint(0, 3)
        members = random.sample(user_ids, min(num_members, len(user_ids)))
        for member_id in members:
            if member_id != owner_id:
                access_data.append({
                    "fridge_id": fridge_id,
                    "user_id": member_id,
                    "access_role": "Member"
                })

    # Bulk insert fridges
    for i in range(0, len(fridge_data), BATCH_SIZE):
        await session.execute(insert(Fridge), fridge_data[i:i + BATCH_SIZE])
    
    # Bulk insert access
    for i in range(0, len(access_data), BATCH_SIZE):
        await session.execute(insert(FridgeAccess), access_data[i:i + BATCH_SIZE])

    await session.commit()
    print(f"✓ Created {len(fridge_data)} fridges with {len(access_data)} access records")
    return generated_fridge_ids


async def generate_fridge_items_optimized(session: AsyncSession, fridge_ids, ingredient_ids):
    """Generate fridge items using OPTIMIZED bulk insert."""
    print(f"Generating {NUM_FRIDGE_ITEMS} fridge items (Optimized)...")
    
    items_batch = []
    total_inserted = 0
    
    today = date.today()

    for i in range(NUM_FRIDGE_ITEMS):
        fridge_id = random.choice(fridge_ids)
        ingredient_id = random.choice(ingredient_ids)

        # Logic for quantity
        qty = Decimal(random.randint(1, 1000))

        # Logic for dates
        entry_date = today - timedelta(days=random.randint(0, 30))
        expiry_date = entry_date + timedelta(days=random.randint(1, 60))

        items_batch.append({
            "fridge_id": fridge_id,
            "ingredient_id": ingredient_id,
            "quantity": qty,
            "entry_date": entry_date,
            "expiry_date": expiry_date
        })

        if len(items_batch) >= BATCH_SIZE:
            await session.execute(insert(FridgeItem), items_batch)
            total_inserted += len(items_batch)
            items_batch = []
            print(f"  Inserted {total_inserted} items...")

    if items_batch:
        await session.execute(insert(FridgeItem), items_batch)
        total_inserted += len(items_batch)

    await session.commit()
    print(f"✓ Created {total_inserted} fridge items")


async def generate_recipes(session: AsyncSession, user_ids, ingredient_ids):
    """Generate recipes."""
    print(f"Generating {NUM_RECIPES} recipes...")
    
    # We need to insert recipes one by one or in small batches to get IDs back for requirements/steps
    # For speed, we'll assume we can fetch them back or generate partials.
    # Actually, let's use ORM for Recipes (parent) as it's cleaner for related items, 
    # but we can optimize the child inserts.
    
    recipes_created = []
    
    for i in range(NUM_RECIPES):
        owner_id = random.choice(user_ids)
        name = RECIPE_NAMES[i] if i < len(RECIPE_NAMES) else f"{fake.word().capitalize()} Recipe {i}"
        
        recipe = Recipe(
            owner_id=owner_id,
            recipe_name=name,
            description=fake.sentence(),
            cooking_time=random.randint(10, 120),
            status="Published"
        )
        session.add(recipe)
        recipes_created.append(recipe)
        
        if len(recipes_created) >= 100:
            await session.flush() # Get IDs
            
            # Now generate requirements and steps for this batch
            reqs_data = []
            steps_data = []
            
            for r in recipes_created[-100:]:
                # Reqs
                num_ing = random.randint(2, 6)
                for ing_id in random.sample(ingredient_ids, num_ing):
                    reqs_data.append({
                        "recipe_id": r.recipe_id,
                        "ingredient_id": ing_id,
                        "quantity_needed": Decimal(random.randint(1, 500))
                    })
                
                # Steps
                num_steps = random.randint(3, 8)
                for step_num in range(1, num_steps + 1):
                    steps_data.append({
                        "recipe_id": r.recipe_id,
                        "step_number": step_num,
                        "description": fake.sentence()
                    })
            
            if reqs_data:
                await session.execute(insert(RecipeRequirement), reqs_data)
            if steps_data:
                await session.execute(insert(RecipeStep), steps_data)
            
            recipes_created = [] # Clear batch list
            print(f"  Created {i+1} recipes...")

    await session.commit()
    print(f"✓ Created {NUM_RECIPES} recipes")
    
    # Fetch all recipe IDs for next steps
    result = await session.execute(select(Recipe.recipe_id))
    return result.scalars().all()


async def generate_reviews_optimized(session: AsyncSession, user_ids, recipe_ids):
    """Generate reviews optimized."""
    print(f"Generating {NUM_REVIEWS} reviews...")
    batch = []
    
    for i in range(NUM_REVIEWS):
        batch.append({
            "user_id": random.choice(user_ids),
            "recipe_id": random.choice(recipe_ids),
            "rating": random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0],
            "comment": fake.sentence(),
            "review_date": datetime.utcnow() - timedelta(days=random.randint(0, 365))
        })
        
        if len(batch) >= BATCH_SIZE:
            # Ignore duplicates (PK violations) using on_conflict_do_nothing if supported,
            # or just simple insert and hope random collision is low.
            # For simplicity, we'll try insert. If collision, it fails.
            # To be safe, we'd use 'INSERT ... ON CONFLICT DO NOTHING'
            # But standard sqlalchemy insert might fail.
            # Let's verify unique constraints in loop? Too slow.
            # Let's just catch exception or use set for uniqueness in memory.
            pass

    # Better approach: Generate unique pairs
    reviews_data = []
    seen = set()
    attempts = 0
    while len(reviews_data) < NUM_REVIEWS and attempts < NUM_REVIEWS * 2:
        attempts += 1
        u = random.choice(user_ids)
        r = random.choice(recipe_ids)
        if (u, r) not in seen:
            seen.add((u, r))
            reviews_data.append({
                "user_id": u,
                "recipe_id": r,
                "rating": random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0],
                "comment": fake.sentence(),
                "review_date": datetime.utcnow() - timedelta(days=random.randint(0, 365))
            })

    for i in range(0, len(reviews_data), BATCH_SIZE):
        await session.execute(insert(RecipeReview), reviews_data[i:i + BATCH_SIZE])
        print(f"  Inserted {min(i + BATCH_SIZE, len(reviews_data))} reviews...")

    await session.commit()
    print(f"✓ Created {len(reviews_data)} reviews")


async def generate_meal_plans_optimized(session: AsyncSession, user_ids, recipe_ids, fridge_ids):
    """Generate meal plans optimized."""
    print(f"Generating {NUM_MEAL_PLANS} meal plans...")
    batch = []
    
    # We need a mapping of user -> fridge to assign valid fridge_id
    # We can fetch access list or just pick random fridge for speed (assuming most users have one)
    # Correct way: Pick user, pick one of their fridges.
    # To optimize: Fetch all access pairs first.
    
    print("  Fetching access map...")
    result = await session.execute(select(FridgeAccess.user_id, FridgeAccess.fridge_id))
    access_map = {} # user_id -> list of fridge_ids
    for uid, fid in result.all():
        if uid not in access_map:
            access_map[uid] = []
        access_map[uid].append(fid)
    
    users_with_fridge = list(access_map.keys())
    
    for i in range(NUM_MEAL_PLANS):
        user_id = random.choice(users_with_fridge)
        fridge_id = random.choice(access_map[user_id])
        recipe_id = random.choice(recipe_ids)
        
        days_offset = random.randint(-30, 30)
        status = "Planned"
        if days_offset < 0: status = "Finished"
        elif days_offset < 14: status = random.choice(["Ready", "Insufficient", "Planned"])
        
        batch.append({
            "user_id": user_id,
            "recipe_id": recipe_id,
            "fridge_id": fridge_id,
            "planned_date": datetime.utcnow() + timedelta(days=days_offset),
            "status": status
        })
        
        if len(batch) >= BATCH_SIZE:
            await session.execute(insert(MealPlan), batch)
            batch = []
            print(f"  Inserted {i+1} meal plans...")
            
    if batch:
        await session.execute(insert(MealPlan), batch)
        
    await session.commit()
    print(f"✓ Created {NUM_MEAL_PLANS} meal plans")


async def generate_partners_and_products(session: AsyncSession, ingredient_ids):
    """Generate partners and products."""
    print(f"Generating {NUM_PARTNERS} partners...")
    
    partners_data = []
    for i in range(NUM_PARTNERS):
        partners_data.append({
            "partner_name": PARTNER_NAMES[i] if i < len(PARTNER_NAMES) else fake.company(),
            "contract_date": date.today() - timedelta(days=random.randint(30, 1000)),
            "avg_shipping_days": random.randint(1, 7),
            "credit_score": random.randint(60, 100)
        })
    
    # Bulk insert partners
    # We need IDs for products, so maybe insert one by one or fetch back
    # Since only 20 partners, one by one is fast.
    
    partner_ids = []
    for p_data in partners_data:
        p = Partner(**p_data)
        session.add(p)
        await session.flush()
        partner_ids.append(p.partner_id)
        
    print(f"✓ Created {len(partner_ids)} partners")
    
    print(f"Generating {NUM_PRODUCTS} products...")
    products_data = []
    for i in range(NUM_PRODUCTS):
        pid = random.choice(partner_ids)
        ing_id = random.choice(ingredient_ids)
        
        products_data.append({
            "partner_id": pid,
            "external_sku": f"SKU-{pid}-{ing_id}-{i}",
            "ingredient_id": ing_id,
            "product_name": f"Product {i}",
            "current_price": Decimal(random.uniform(1.0, 50.0)),
            "selling_unit": "Pack",
            "unit_quantity": Decimal(1)
        })
        
    for i in range(0, len(products_data), BATCH_SIZE):
        await session.execute(insert(ExternalProduct), products_data[i:i + BATCH_SIZE])
        
    await session.commit()
    print(f"✓ Created {len(products_data)} products")
    return partner_ids

async def generate_orders(session: AsyncSession, user_ids, partner_ids):
    """Generate orders and items."""
    print(f"Generating {NUM_ORDERS} orders...")
    
    # Pre-fetch products by partner for fast lookup
    print("  Fetching products map...")
    products_result = await session.execute(select(ExternalProduct))
    products_by_partner = {}
    for p in products_result.scalars().all():
        if p.partner_id not in products_by_partner:
            products_by_partner[p.partner_id] = []
        products_by_partner[p.partner_id].append(p)
        
    orders_created = []
    
    for i in range(NUM_ORDERS):
        user_id = random.choice(user_ids)
        partner_id = random.choice(partner_ids)
        
        # Random date in last 90 days
        order_date = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        status = random.choice(['Pending', 'Paid', 'Shipped', 'Delivered', 'Cancelled'])
        
        order = StoreOrder(
            user_id=user_id,
            partner_id=partner_id,
            order_date=order_date,
            expected_arrival=order_date + timedelta(days=3),
            total_price=0, # Will update later
            order_status=status
        )
        session.add(order)
        orders_created.append(order)
        
        # Flush every batch to get IDs and create items
        if len(orders_created) >= 100:
            await session.flush()
            
            current_items_batch = []
            
            for o in orders_created[-100:]:
                if o.partner_id not in products_by_partner: continue
                
                avail_products = products_by_partner[o.partner_id]
                if not avail_products: continue
                
                # Randomly pick 1-5 products
                num_items = random.randint(1, 5)
                selected_products = random.sample(avail_products, min(len(avail_products), num_items))
                
                total = Decimal(0)
                for prod in selected_products:
                    qty = random.randint(1, 3)
                    price = prod.current_price
                    total += price * qty
                    
                    current_items_batch.append({
                        "order_id": o.order_id,
                        "external_sku": prod.external_sku,
                        "partner_id": o.partner_id,
                        "quantity": qty,
                        "deal_price": price
                    })
                
                o.total_price = total
            
            if current_items_batch:
                await session.execute(insert(OrderItem), current_items_batch)
                
            orders_created = [] # Clear list
            print(f"  Created {i+1} orders...")
            
    await session.commit()
    print(f"✓ Created {NUM_ORDERS} orders")

async def main():
    """Main generation script."""
    print("=" * 60)
    print("NEW Fridge - Optimized Data Generator")
    print("=" * 60)
    
    start_time = time.time()
    
    await init_db()
    
    async with async_session_maker() as session:
        # Get IDs after generation
        users_data = await generate_users(session)
        # Fetch user IDs
        result = await session.execute(select(User.user_id))
        user_ids = result.scalars().all()
        
        await generate_ingredients(session)
        result = await session.execute(select(Ingredient.ingredient_id))
        ingredient_ids = result.scalars().all()
        
        fridge_ids = await generate_fridges(session, user_ids)
        
        await generate_fridge_items_optimized(session, fridge_ids, ingredient_ids)
        
        recipe_ids = await generate_recipes(session, user_ids, ingredient_ids)
        
        await generate_reviews_optimized(session, user_ids, recipe_ids)
        
        await generate_meal_plans_optimized(session, user_ids, recipe_ids, fridge_ids)
        
        # 1. 接收回傳的 partner_ids
        partner_ids = await generate_partners_and_products(session, ingredient_ids)
        
        # 2. 呼叫剛剛新增的函式
        await generate_orders(session, user_ids, partner_ids)
        
        await session.commit()
        
    end_time = time.time()
    print("\n" + "=" * 60)
    print(f"✓ Data generation complete in {end_time - start_time:.2f} seconds!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
