"""
Performance Testing Script - Before and After Indexing

Tests common query patterns to measure index impact.
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session_maker, init_db
from models import FridgeItem, MealPlan, StoreOrder, OrderItem, RecipeRequirement


async def time_query(session: AsyncSession, description: str, query):
    """Execute a query and measure time."""
    start = time.time()

    if isinstance(query, str):
        result = await session.execute(text(query))
    else:
        result = await session.execute(query)

    rows = result.fetchall()
    elapsed = time.time() - start

    print(f"  {description}")
    print(f"    Time: {elapsed*1000:.2f}ms | Rows: {len(rows)}")
    return elapsed


async def run_performance_tests():
    """Run performance tests on common queries."""
    print("=" * 70)
    print("DATABASE PERFORMANCE TEST")
    print("=" * 70)

    await init_db()

    async with async_session_maker() as session:
        print("\n📊 Running performance tests...\n")

        # Test 1: Find all fridge items for a specific fridge (common in inventory view)
        print("1️⃣  Query: Find all items in a fridge (foreign key lookup)")
        query1 = """
        SELECT * FROM fridge_item
        WHERE fridge_id = (SELECT fridge_id FROM fridge LIMIT 1 OFFSET 5)
        """
        t1 = await time_query(session, "No index on fridge_item.fridge_id", query1)

        # Test 2: Find items by ingredient (common in availability check)
        print("\n2️⃣  Query: Find all fridge items for an ingredient")
        query2 = """
        SELECT * FROM fridge_item
        WHERE ingredient_id = (SELECT ingredient_id FROM ingredient LIMIT 1 OFFSET 10)
        """
        t2 = await time_query(session, "No index on fridge_item.ingredient_id", query2)

        # Test 3: Find meal plans for a user+fridge (common in meal plan view)
        print("\n3️⃣  Query: Find meal plans for user and fridge")
        query3 = """
        SELECT * FROM meal_plan
        WHERE user_id = (SELECT user_id FROM "user" LIMIT 1 OFFSET 3)
        AND fridge_id = (SELECT fridge_id FROM fridge LIMIT 1 OFFSET 2)
        """
        t3 = await time_query(session, "No index on meal_plan(user_id, fridge_id)", query3)

        # Test 4: Find meal plans by date range (common in calendar view)
        print("\n4️⃣  Query: Find meal plans in date range")
        today = datetime.now().date()
        query4 = f"""
        SELECT * FROM meal_plan
        WHERE planned_date BETWEEN '{today}' AND '{today + timedelta(days=7)}'
        """
        t4 = await time_query(session, "No index on meal_plan.planned_date", query4)

        # Test 5: Find orders for a user (common in order history)
        print("\n5️⃣  Query: Find orders for a user")
        query5 = """
        SELECT * FROM store_order
        WHERE user_id = (SELECT user_id FROM "user" LIMIT 1 OFFSET 5)
        """
        t5 = await time_query(session, "No index on store_order.user_id", query5)

        # Test 6: Find items expiring soon (common in waste prevention)
        print("\n6️⃣  Query: Find items expiring in next 7 days")
        query6 = f"""
        SELECT * FROM fridge_item
        WHERE expiry_date BETWEEN '{today}' AND '{today + timedelta(days=7)}'
        """
        t6 = await time_query(session, "No index on fridge_item.expiry_date", query6)

        # Test 7: Find recipe requirements (common in recipe view)
        print("\n7️⃣  Query: Find ingredients for recipes")
        query7 = """
        SELECT * FROM recipe_requirement
        WHERE recipe_id = (SELECT recipe_id FROM recipe LIMIT 1 OFFSET 20)
        """
        t7 = await time_query(session, "No index on recipe_requirement.recipe_id", query7)

        # Test 8: Join query - meal plans with recipe names
        print("\n8️⃣  Query: Join meal plans with recipes")
        query8 = """
        SELECT mp.*, r.recipe_name
        FROM meal_plan mp
        JOIN recipe r ON mp.recipe_id = r.recipe_id
        WHERE mp.status = 'Insufficient'
        LIMIT 100
        """
        t8 = await time_query(session, "Join without index on meal_plan.recipe_id", query8)

        total_time = t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8

        print("\n" + "=" * 70)
        print(f"TOTAL TIME: {total_time*1000:.2f}ms")
        print("=" * 70)

        return total_time


async def create_indexes():
    """Create strategic indexes."""
    print("\n" + "=" * 70)
    print("CREATING INDEXES")
    print("=" * 70)

    indexes = [
        ("idx_fridge_item_fridge", "CREATE INDEX IF NOT EXISTS idx_fridge_item_fridge ON fridge_item(fridge_id)"),
        ("idx_fridge_item_ingredient", "CREATE INDEX IF NOT EXISTS idx_fridge_item_ingredient ON fridge_item(ingredient_id)"),
        ("idx_fridge_item_expiry", "CREATE INDEX IF NOT EXISTS idx_fridge_item_expiry ON fridge_item(expiry_date)"),
        ("idx_meal_plan_user_fridge", "CREATE INDEX IF NOT EXISTS idx_meal_plan_user_fridge ON meal_plan(user_id, fridge_id)"),
        ("idx_meal_plan_date", "CREATE INDEX IF NOT EXISTS idx_meal_plan_date ON meal_plan(planned_date)"),
        ("idx_meal_plan_recipe", "CREATE INDEX IF NOT EXISTS idx_meal_plan_recipe ON meal_plan(recipe_id)"),
        ("idx_meal_plan_status", "CREATE INDEX IF NOT EXISTS idx_meal_plan_status ON meal_plan(status)"),
        ("idx_store_order_user", "CREATE INDEX IF NOT EXISTS idx_store_order_user ON store_order(user_id)"),
        ("idx_store_order_fridge", "CREATE INDEX IF NOT EXISTS idx_store_order_fridge ON store_order(fridge_id)"),
        ("idx_order_item_order", "CREATE INDEX IF NOT EXISTS idx_order_item_order ON order_item(order_id)"),
        ("idx_recipe_requirement_recipe", "CREATE INDEX IF NOT EXISTS idx_recipe_requirement_recipe ON recipe_requirement(recipe_id)"),
        ("idx_recipe_requirement_ingredient", "CREATE INDEX IF NOT EXISTS idx_recipe_requirement_ingredient ON recipe_requirement(ingredient_id)"),
    ]

    async with async_session_maker() as session:
        for name, sql in indexes:
            start = time.time()
            await session.execute(text(sql))
            elapsed = time.time() - start
            print(f"✓ {name} ({elapsed*1000:.2f}ms)")
        await session.commit()

    print("\n✓ All indexes created!")


async def drop_indexes():
    """Drop the test indexes."""
    print("\n" + "=" * 70)
    print("DROPPING INDEXES")
    print("=" * 70)

    indexes = [
        "idx_fridge_item_fridge",
        "idx_fridge_item_ingredient",
        "idx_fridge_item_expiry",
        "idx_meal_plan_user_fridge",
        "idx_meal_plan_date",
        "idx_meal_plan_recipe",
        "idx_meal_plan_status",
        "idx_store_order_user",
        "idx_store_order_fridge",
        "idx_order_item_order",
        "idx_recipe_requirement_recipe",
        "idx_recipe_requirement_ingredient",
    ]

    async with async_session_maker() as session:
        for name in indexes:
            await session.execute(text(f"DROP INDEX IF EXISTS {name}"))
            print(f"✓ Dropped {name}")
        await session.commit()

    print("\n✓ All test indexes dropped!")


async def main():
    """Main performance test runner."""
    print("\n🔍 PERFORMANCE COMPARISON TEST")
    print("This will test query performance before and after adding indexes\n")

    # Test 1: Without indexes
    print("\n" + "🅰️ " * 35)
    print("PHASE 1: BASELINE (CURRENT STATE)")
    print("🅰️ " * 35)
    await drop_indexes()  # Ensure clean state
    time_before = await run_performance_tests()

    # Add indexes
    await create_indexes()

    # Test 2: With indexes
    print("\n" + "🅱️ " * 35)
    print("PHASE 2: WITH INDEXES")
    print("🅱️ " * 35)
    time_after = await run_performance_tests()

    # Summary
    improvement = ((time_before - time_after) / time_before) * 100
    speedup = time_before / time_after if time_after > 0 else 0

    print("\n" + "=" * 70)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Before indexing:  {time_before*1000:.2f}ms")
    print(f"After indexing:   {time_after*1000:.2f}ms")
    print(f"Improvement:      {improvement:.1f}%")
    print(f"Speed-up:         {speedup:.2f}x faster")
    print("=" * 70)

    if improvement > 0:
        print("\n✅ Indexes improved performance!")
    else:
        print("\n⚠️  No improvement detected (dataset may be too small)")


if __name__ == "__main__":
    asyncio.run(main())
