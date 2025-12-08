"""
Clean Data Script for NEW Fridge

Truncates all tables in the database to provide a clean slate.
Usage:
    python scripts/clean_data.py
"""

import asyncio
import sys
import os

# Add parent directory to path to allow importing from backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import init_db, async_session_maker

async def clean_data():
    print("=" * 60)
    print("NEW Fridge Data Cleanup")
    print("=" * 60)
    
    # Tables to clean in order (respecting foreign keys, though CASCADE helps)
    # Using CASCADE on parent tables is usually enough, but explicit is safer for clarity
    tables = [
        "order_item",
        "store_order",
        "shopping_list_item",
        "external_product",
        "partner",
        "meal_plan",
        "recipe_review",
        "recipe_step",
        "recipe_requirement",
        "recipe",
        "fridge_item",
        "fridge_access",
        "fridge",
        "ingredient",
        "user"
    ]

    async with async_session_maker() as session:
        for table in tables:
            print(f"Truncating table: {table}...")
            try:
                # Use TRUNCATE ... CASCADE to handle foreign keys efficiently
                await session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))
                await session.commit()
                print(f"✓ Cleared {table}")
            except Exception as e:
                print(f"❌ Error clearing {table}: {e}")
                await session.rollback()

    print("\n✓ Database cleanup complete!")

if __name__ == "__main__":
    asyncio.run(clean_data())
