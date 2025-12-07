"""
MongoDB connection and database management for behavior tracking.
"""
import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure


class MongoDBManager:
    """MongoDB connection manager for async operations."""

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        """Initialize MongoDB connection."""
        mongo_user = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
        mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
        mongo_host = os.getenv("MONGO_HOST", "mongodb")
        mongo_port = os.getenv("MONGO_PORT", "27017")
        mongo_db_name = os.getenv("MONGO_DB_NAME", "newfridge")

        # Build connection URI
        mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}"

        try:
            cls.client = AsyncIOMotorClient(mongo_uri)

            # Test connection
            await cls.client.admin.command('ping')
            print(f"✅ Connected to MongoDB successfully")

            # Get database
            cls.database = cls.client[mongo_db_name]

            # Create indexes for common queries
            await cls._create_indexes()

        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def _create_indexes(cls):
        """Create indexes for behavior collections."""
        if cls.database is None:
            return

        # User behavior collection indexes
        user_behavior = cls.database.user_behavior
        await user_behavior.create_index("user_id")
        await user_behavior.create_index("action_type")
        await user_behavior.create_index("timestamp")
        await user_behavior.create_index([("user_id", 1), ("timestamp", -1)])

        # API usage collection indexes
        api_usage = cls.database.api_usage
        await api_usage.create_index("endpoint")
        await api_usage.create_index("user_id")
        await api_usage.create_index("timestamp")
        await api_usage.create_index([("endpoint", 1), ("timestamp", -1)])

        # Search queries collection indexes
        search_queries = cls.database.search_queries
        await search_queries.create_index("user_id")
        await search_queries.create_index("query_type")
        await search_queries.create_index("timestamp")

        print("✅ MongoDB indexes created")

    @classmethod
    async def close(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("✅ MongoDB connection closed")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get MongoDB database instance."""
        if cls.database is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls.database

    @classmethod
    def get_collection(cls, collection_name: str):
        """Get a specific collection from the database."""
        return cls.get_database()[collection_name]


# Dependency for FastAPI routes
async def get_mongo_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency to get MongoDB database."""
    return MongoDBManager.get_database()
