"""
Simple Behavioral Data Generator for MongoDB

Generates simulated user activity logs for analytics demonstration.
"""

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from mongodb import init_mongo, get_collection
from database import init_db, async_session_maker
from models.user import User
from models.recipe import Recipe


# Common search terms
SEARCH_TERMS = [
    "pasta", "chicken", "salad", "soup", "rice", "egg", "beef", "fish",
    "vegetable", "dessert", "breakfast", "lunch", "dinner", "quick", "easy"
]

# Action types with weights (higher = more common)
ACTIONS = [
    ("login", 20),
    ("search_recipe", 15),
    ("view_recipe", 25),
    ("cook_recipe", 5),
    ("create_order", 3),
    ("view_fridge", 10),
]


async def generate_behavioral_data():
    """Main function to generate behavioral data"""
    print("=" * 60)
    print("🚀 Starting behavioral data generation...")
    print("=" * 60)

    # Initialize database connections
    await init_db()
    await init_mongo()

    async with async_session_maker() as session:
        # Step 1: Get users and recipes from PostgreSQL
        print("\n📊 Step 1: Fetching users and recipes...")
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        recipes_result = await session.execute(select(Recipe).limit(100))
        recipes = recipes_result.scalars().all()

        print(f"   ✓ Found {len(users)} users")
        print(f"   ✓ Found {len(recipes)} recipes")

    # Step 2: Get MongoDB collections
    activity_logs = get_collection("activity_logs")
    search_queries = get_collection("search_queries")

    # Clear existing data
    print("\n🗑️  Step 2: Clearing existing behavioral data...")
    await activity_logs.delete_many({})
    await search_queries.delete_many({})
    print("   ✓ Cleared")

    # Step 3: Generate activity logs
    print("\n📝 Step 3: Generating activity logs...")
    activity_count = 0
    search_count = 0

    # Generate data for past 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    # Generate 10-30 actions per user
    for user in users[:50]:  # Use only first 50 users to keep it simple
        num_actions = random.randint(10, 30)

        for _ in range(num_actions):
            # Random timestamp within past 30 days
            random_seconds = random.randint(0, 30 * 24 * 3600)
            action_time = start_date + timedelta(seconds=random_seconds)

            # Choose action type based on weights
            action_type = random.choices(
                [a[0] for a in ACTIONS],
                weights=[a[1] for a in ACTIONS]
            )[0]

            # Generate different logs based on action type
            if action_type == "login":
                log = {
                    "timestamp": action_time,
                    "action_type": "login",
                    "user_id": str(user.user_id),
                    "metadata": {
                        "user_name": user.user_name,
                        "role": user.role
                    }
                }
                await activity_logs.insert_one(log)
                activity_count += 1

            elif action_type == "search_recipe":
                search_term = random.choice(SEARCH_TERMS)
                results_count = random.randint(1, 15)

                # Insert to activity_logs
                log = {
                    "timestamp": action_time,
                    "action_type": "search",
                    "user_id": str(user.user_id),
                    "resource_type": "recipe",
                    "metadata": {
                        "query": search_term,
                        "results_count": results_count
                    }
                }
                await activity_logs.insert_one(log)
                activity_count += 1

                # Insert to search_queries
                query = {
                    "timestamp": action_time,
                    "user_id": str(user.user_id),
                    "query_type": "recipe",
                    "query_text": search_term,
                    "results_count": results_count
                }
                await search_queries.insert_one(query)
                search_count += 1

            elif action_type == "view_recipe":
                recipe = random.choice(recipes)
                log = {
                    "timestamp": action_time,
                    "action_type": "view_recipe",
                    "user_id": str(user.user_id),
                    "resource_type": "recipe",
                    "resource_id": str(recipe.recipe_id),
                    "metadata": {
                        "recipe_name": recipe.recipe_name,
                        "cooking_time": recipe.cooking_time
                    }
                }
                await activity_logs.insert_one(log)
                activity_count += 1

            elif action_type == "cook_recipe":
                recipe = random.choice(recipes)
                log = {
                    "timestamp": action_time,
                    "action_type": "cook_recipe",
                    "user_id": str(user.user_id),
                    "resource_type": "recipe",
                    "resource_id": str(recipe.recipe_id),
                    "metadata": {
                        "recipe_name": recipe.recipe_name,
                        "ingredients_consumed": random.randint(3, 8)
                    }
                }
                await activity_logs.insert_one(log)
                activity_count += 1

            elif action_type == "create_order":
                log = {
                    "timestamp": action_time,
                    "action_type": "create_order",
                    "user_id": str(user.user_id),
                    "resource_type": "order",
                    "resource_id": str(random.randint(1000, 9999)),
                    "metadata": {
                        "partner_name": random.choice(["FreshMart", "SuperStore", "QuickShop"]),
                        "total_price": f"{random.uniform(20, 200):.2f}",
                        "items_count": random.randint(1, 5)
                    }
                }
                await activity_logs.insert_one(log)
                activity_count += 1

            elif action_type == "view_fridge":
                log = {
                    "timestamp": action_time,
                    "action_type": "view_inventory",
                    "user_id": str(user.user_id),
                    "resource_type": "fridge",
                    "metadata": {
                        "items_count": random.randint(5, 20)
                    }
                }
                await activity_logs.insert_one(log)
                activity_count += 1

        # Progress indicator
        if (users.index(user) + 1) % 10 == 0:
            print(f"   Processed {users.index(user) + 1} users...")

    print(f"\n✅ Complete!")
    print(f"   📊 Generated {activity_count} activity logs")
    print(f"   🔍 Generated {search_count} search queries")

    # Step 4: Verify data
    print("\n📈 Step 4: Verifying data...")
    total_activity = await activity_logs.count_documents({})
    total_search = await search_queries.count_documents({})

    print(f"   ✓ activity_logs: {total_activity} records")
    print(f"   ✓ search_queries: {total_search} records")

    # Step 5: Show statistics
    print("\n📊 Statistics:")

    # Most common action types
    pipeline = [
        {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_actions = await activity_logs.aggregate(pipeline).to_list(length=5)
    print("\n   Most common actions:")
    for action in top_actions:
        print(f"      • {action['_id']}: {action['count']} times")

    # Most popular search terms
    pipeline = [
        {"$group": {"_id": "$query_text", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_searches = await search_queries.aggregate(pipeline).to_list(length=5)
    print("\n   Most popular searches:")
    for search in top_searches:
        print(f"      • {search['_id']}: {search['count']} times")

    print("\n" + "=" * 60)
    print("✨ Behavioral data generation complete!")
    print("=" * 60)
    print("\n💡 Tip: View the data in Mongo Express:")
    print("   URL: http://localhost:8081")
    print("   Database: newfridge")
    print("   Collections: activity_logs, search_queries")
    print()


if __name__ == "__main__":
    asyncio.run(generate_behavioral_data())
