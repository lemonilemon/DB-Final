from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import init_db, close_db, get_session
from mongodb import init_mongo, close_mongo, get_collection
from models import (
    User, UserRole, Fridge, FridgeAccess, Ingredient, FridgeItem,
    Partner, ExternalProduct, ShoppingListItem, StoreOrder, OrderItem,
    Recipe, RecipeRequirement, RecipeStep, RecipeReview, MealPlan
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Initialize databases
    print("🚀 Starting NEW Fridge Backend...")
    print("📦 Initializing PostgreSQL tables...")
    await init_db()
    print("✅ PostgreSQL initialized successfully!")

    print("📊 Initializing MongoDB...")
    await init_mongo()
    print("✅ MongoDB initialized successfully!")

    yield

    # Shutdown: Close database connections
    print("🛑 Shutting down...")
    await close_db()
    await close_mongo()
    print("✅ All database connections closed.")


# Create FastAPI app with lifespan manager
app = FastAPI(
    title="NEW Fridge API",
    description="Smart inventory and procurement management system",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def read_root():
    """Root endpoint - health check"""
    return {
        "message": "Hello from NEW Fridge Backend!",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health/postgres")
async def health_postgres(session: AsyncSession = Depends(get_session)):
    """
    PostgreSQL health check - tests async connection and queries User table.
    """
    try:
        # Try to query the user table
        result = await session.execute(select(User))
        users = result.scalars().all()
        return {
            "status": "success",
            "database": "PostgreSQL",
            "message": "Connection successful",
            "user_count": len(users)
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "PostgreSQL",
            "message": str(e)
        }


@app.get("/health/mongo")
async def health_mongo():
    """
    MongoDB health check - tests connection and queries collections.
    """
    try:
        # Get activity logs collection and count documents
        activity_logs = get_collection("activity_logs")
        count = await activity_logs.count_documents({})

        return {
            "status": "success",
            "database": "MongoDB",
            "message": "Connection successful",
            "activity_log_count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "MongoDB",
            "message": str(e)
        }


@app.get("/health")
async def health_all(session: AsyncSession = Depends(get_session)):
    """
    Complete health check - tests both PostgreSQL and MongoDB.
    """
    postgres_ok = False
    mongo_ok = False
    errors = []

    # Check PostgreSQL
    try:
        result = await session.execute(select(User))
        users = result.scalars().all()
        postgres_ok = True
    except Exception as e:
        errors.append(f"PostgreSQL: {str(e)}")

    # Check MongoDB
    try:
        activity_logs = get_collection("activity_logs")
        await activity_logs.count_documents({})
        mongo_ok = True
    except Exception as e:
        errors.append(f"MongoDB: {str(e)}")

    return {
        "status": "healthy" if (postgres_ok and mongo_ok) else "degraded",
        "databases": {
            "postgres": "connected" if postgres_ok else "error",
            "mongodb": "connected" if mongo_ok else "error"
        },
        "errors": errors if errors else None
    }
