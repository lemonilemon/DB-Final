"""
Complete Behavioral Data Generator for MongoDB Analytics

Generates realistic historical data for:
1. user_behavior - User actions (login, search, view_recipe, cook, etc.)
2. search_queries - Recipe/ingredient searches
3. api_usage - API performance monitoring
"""

import os
import sys

# Add /app to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)


import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from mongodb import init_mongo, get_database
# from app.mongodb import init_mongo, get_database

from database import init_db, async_session_maker
from models.user import User
from models.recipe import Recipe


# ============================================================================
# Configuration
# ============================================================================

DAYS_TO_GENERATE = 30
NUM_ACTIVE_USERS = 50

# Common search terms
SEARCH_TERMS = [
    "pasta", "chicken", "salad", "soup", "rice", "egg", "beef", "fish",
    "vegetable", "dessert", "breakfast", "lunch", "dinner", "quick", "easy"
]

# User action types with weights (higher = more common)
USER_ACTIONS = [
    ("login", 20),
    ("search_recipe", 15),
    ("view_recipe", 25),
    ("cook_recipe", 5),
    ("create_order", 3),
    ("view_fridge", 10),
]

# API endpoints with realistic usage patterns
API_ENDPOINTS = [
    # High traffic endpoints
    ("/api/fridges", "GET", 30),
    ("/api/ingredients", "GET", 25),
    ("/api/recipes", "GET", 20),
    ("/api/products", "GET", 15),

    # Medium traffic endpoints
    ("/api/fridges/{id}/items", "GET", 12),
    ("/api/recipes/{id}", "GET", 10),
    ("/api/shopping-list", "GET", 8),
    ("/api/orders", "GET", 6),
    ("/api/meal-plans", "GET", 5),

    # Write operations
    ("/api/fridges/{id}/items", "POST", 8),
    ("/api/shopping-list", "POST", 6),
    ("/api/recipes", "POST", 2),
    ("/api/orders", "POST", 4),
    ("/api/meal-plans", "POST", 3),

    # Update/Delete operations
    ("/api/fridges/{id}/items/{item_id}", "PUT", 3),
    ("/api/fridges/{id}/items/{item_id}", "DELETE", 3),
    ("/api/shopping-list/{id}", "DELETE", 4),
    ("/api/orders/{id}/status", "PUT", 2),

    # Analytics endpoints
    ("/api/analytics/user/activity", "GET", 4),
    ("/api/analytics/search/trends", "GET", 3),

    # Admin endpoints
    ("/api/admin/users", "GET", 1),
    ("/api/admin/orders/{id}/status", "PUT", 1),
]


# ============================================================================
# Helper Functions
# ============================================================================

def random_timestamp(start_date, end_date):
    """Generate random timestamp between start and end dates."""
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)


def generate_response_time(endpoint: str, method: str, status_code: int) -> float:
    """Generate realistic response time based on endpoint complexity."""
    if "GET" in method:
        base = random.uniform(20, 80)
    else:
        base = random.uniform(50, 150)

    if "analytics" in endpoint:
        base += random.uniform(100, 300)
    elif "orders" in endpoint or "meal-plans" in endpoint:
        base += random.uniform(30, 100)

    if status_code >= 400:
        base *= 0.6

    variation = random.uniform(0.8, 1.5)
    return round(base * variation, 2)


def generate_status_code(endpoint: str, method: str) -> int:
    """Generate realistic status codes with weighted distribution."""
    weights = [85, 8, 5, 2]  # 200, 400, 404, 500
    codes = [200, 400, 404, 500]

    if "admin" in endpoint:
        weights = [70, 15, 10, 5]

    if method in ["POST", "PUT"]:
        weights = [80, 12, 5, 3]

    return random.choices(codes, weights=weights)[0]


# ============================================================================
# Main Generator
# ============================================================================

async def generate_all_behavioral_data():
    """Generate all behavioral data for MongoDB analytics."""
    print("=" * 70)
    print("Complete Behavioral Data Generator")
    print("=" * 70)

    # Initialize connections
    await init_db()
    await init_mongo()

    # Get data from PostgreSQL
    async with async_session_maker() as session:
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        recipes_result = await session.execute(select(Recipe).limit(100))
        recipes = recipes_result.scalars().all()

    print(f"✓ Found {len(users)} users")
    print(f"✓ Found {len(recipes)} recipes")

    # Get MongoDB collections
    db = get_database()
    user_behavior = db.user_behavior
    search_queries = db.search_queries
    api_usage = db.api_usage

    # Clear existing data
    await user_behavior.delete_many({})
    await search_queries.delete_many({})
    await api_usage.delete_many({})
    print("✓ Cleared existing data from all collections")

    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=DAYS_TO_GENERATE)

    # Select active users
    active_users = random.sample(users[:100], min(NUM_ACTIVE_USERS, len(users)))

    # Statistics tracking
    stats = {
        "user_behavior": 0,
        "search_queries": 0,
        "api_usage": 0,
        "actions_by_type": {},
        "searches_by_term": {},
        "endpoints_by_path": {}
    }

    print()
    print("=" * 70)
    print("Generating behavioral data...")
    print("=" * 70)

    # ========================================================================
    # Generate data for each active user
    # ========================================================================

    for idx, user in enumerate(active_users, 1):
        num_actions = random.randint(10, 30)

        if idx % 10 == 0:
            print(f"  Processing user {idx}/{len(active_users)}...")

        for _ in range(num_actions):
            timestamp = random_timestamp(start_date, end_date)

            # Choose action type
            action_type, _ = random.choices(
                USER_ACTIONS,
                weights=[a[1] for a in USER_ACTIONS]
            )[0]

            # Track action stats
            stats["actions_by_type"][action_type] = stats["actions_by_type"].get(action_type, 0) + 1

            # ================================================================
            # 1. Generate user_behavior log
            # ================================================================

            behavior_log = {
                "user_id": str(user.user_id),
                "action_type": action_type,
                "timestamp": timestamp,
                "metadata": {}
            }

            if action_type == "login":
                behavior_log["metadata"] = {
                    "user_name": user.user_name,
                    "role": user.role
                }

            elif action_type == "search_recipe":
                search_term = random.choice(SEARCH_TERMS)
                results_count = random.randint(1, 15)

                behavior_log["resource_type"] = "recipe"
                behavior_log["metadata"] = {
                    "query": search_term,
                    "results": results_count
                }

                # Also create search_queries entry
                search_log = {
                    "user_id": str(user.user_id),
                    "query_type": "recipe",
                    "query_text": search_term,
                    "results_count": results_count,
                    "timestamp": timestamp,
                    "filters": {}
                }
                await search_queries.insert_one(search_log)
                stats["search_queries"] += 1
                stats["searches_by_term"][search_term] = stats["searches_by_term"].get(search_term, 0) + 1

            elif action_type == "view_recipe":
                if recipes:
                    recipe = random.choice(recipes)
                    behavior_log["resource_type"] = "recipe"
                    behavior_log["resource_id"] = str(recipe.recipe_id)
                    behavior_log["metadata"] = {
                        "recipe_name": recipe.recipe_name,
                        "cooking_time": recipe.cooking_time
                    }

            elif action_type == "cook_recipe":
                if recipes:
                    recipe = random.choice(recipes)
                    behavior_log["resource_type"] = "recipe"
                    behavior_log["resource_id"] = str(recipe.recipe_id)
                    behavior_log["metadata"] = {
                        "recipe_name": recipe.recipe_name,
                        "fridge_id": str(user.user_id),  # Simplified
                        "ingredients_consumed": random.randint(3, 8)
                    }

            elif action_type == "create_order":
                behavior_log["resource_type"] = "order"
                behavior_log["metadata"] = {
                    "total_amount": round(random.uniform(20, 150), 2),
                    "items_count": random.randint(1, 8)
                }

            elif action_type == "view_fridge":
                behavior_log["resource_type"] = "fridge"
                behavior_log["metadata"] = {
                    "items_count": random.randint(5, 30)
                }

            await user_behavior.insert_one(behavior_log)
            stats["user_behavior"] += 1

            # ================================================================
            # 2. Generate api_usage log for this action
            # ================================================================

            # Map action to API endpoint
            endpoint_mapping = {
                "login": ("/api/auth/login", "POST"),
                "search_recipe": ("/api/recipes", "GET"),
                "view_recipe": ("/api/recipes/{id}", "GET"),
                "cook_recipe": ("/api/recipes/{id}/cook", "POST"),
                "create_order": ("/api/orders", "POST"),
                "view_fridge": ("/api/fridges/{id}/items", "GET"),
            }

            if action_type in endpoint_mapping:
                endpoint, method = endpoint_mapping[action_type]
                status_code = generate_status_code(endpoint, method)
                response_time_ms = generate_response_time(endpoint, method, status_code)

                api_log = {
                    "endpoint": endpoint,
                    "method": method,
                    "user_id": str(user.user_id),
                    "status_code": status_code,
                    "response_time_ms": response_time_ms,
                    "timestamp": timestamp,
                    "ip_address": f"192.168.{random.randint(1, 255)}.{hash(str(user.user_id)) % 255}",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                await api_usage.insert_one(api_log)
                stats["api_usage"] += 1
                endpoint_key = f"{method} {endpoint}"
                stats["endpoints_by_path"][endpoint_key] = stats["endpoints_by_path"].get(endpoint_key, 0) + 1

    # ========================================================================
    # Generate additional API usage (background requests)
    # ========================================================================

    print("  Generating additional API usage logs...")

    for _ in range(random.randint(500, 1000)):
        timestamp = random_timestamp(start_date, end_date)
        user = random.choice(active_users)

        endpoint, method, _ = random.choices(
            API_ENDPOINTS,
            weights=[ep[2] for ep in API_ENDPOINTS]
        )[0]

        status_code = generate_status_code(endpoint, method)
        response_time_ms = generate_response_time(endpoint, method, status_code)

        api_log = {
            "endpoint": endpoint,
            "method": method,
            "user_id": str(user.user_id),
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "timestamp": timestamp,
            "ip_address": f"192.168.{random.randint(1, 255)}.{hash(str(user.user_id)) % 255}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        await api_usage.insert_one(api_log)
        stats["api_usage"] += 1
        endpoint_key = f"{method} {endpoint}"
        stats["endpoints_by_path"][endpoint_key] = stats["endpoints_by_path"].get(endpoint_key, 0) + 1

    # ========================================================================
    # Generate anonymous API usage
    # ========================================================================

    print("  Generating anonymous API requests...")

    for _ in range(random.randint(100, 300)):
        timestamp = random_timestamp(start_date, end_date)

        public_endpoints = [
            ("/api/recipes", "GET"),
            ("/api/ingredients", "GET"),
            ("/", "GET"),
            ("/health", "GET"),
        ]
        endpoint, method = random.choice(public_endpoints)

        status_code = generate_status_code(endpoint, method)
        response_time_ms = generate_response_time(endpoint, method, status_code)

        api_log = {
            "endpoint": endpoint,
            "method": method,
            "user_id": "anonymous",  # Anonymous
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "timestamp": timestamp,
            "ip_address": f"203.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "user_agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"
        }

        await api_usage.insert_one(api_log)
        stats["api_usage"] += 1

    # ========================================================================
    # Print Summary
    # ========================================================================

    print()
    print("=" * 70)
    print("✅ Complete!")
    print("=" * 70)
    print(f"📊 Generated Data:")
    print(f"   • User Behavior Logs:  {stats['user_behavior']:,}")
    print(f"   • Search Queries:      {stats['search_queries']:,}")
    print(f"   • API Usage Logs:      {stats['api_usage']:,}")
    print(f"   • Total:               {sum([stats['user_behavior'], stats['search_queries'], stats['api_usage']]):,}")
    print()

    # Most common actions
    print("📈 Most Common User Actions:")
    sorted_actions = sorted(stats["actions_by_type"].items(), key=lambda x: x[1], reverse=True)
    for action, count in sorted_actions[:5]:
        print(f"   • {action:20} {count:4} times")
    print()

    # Most popular searches
    print("🔍 Most Popular Searches:")
    sorted_searches = sorted(stats["searches_by_term"].items(), key=lambda x: x[1], reverse=True)
    for term, count in sorted_searches[:5]:
        print(f"   • {term:20} {count:4} times")
    print()

    # Most accessed endpoints
    print("🌐 Most Accessed API Endpoints:")
    sorted_endpoints = sorted(stats["endpoints_by_path"].items(), key=lambda x: x[1], reverse=True)
    for endpoint, count in sorted_endpoints[:5]:
        print(f"   • {endpoint:45} {count:4} calls")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(generate_all_behavioral_data())
