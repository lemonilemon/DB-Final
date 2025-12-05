import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

# MongoDB configuration from environment variables
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
MONGO_HOST = "mongodb"  # docker-compose service name

# MongoDB URL
MONGO_URL = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:27017/"

# Global MongoDB client
mongo_client: Optional[AsyncIOMotorClient] = None


def get_mongo_client() -> AsyncIOMotorClient:
    """
    Get MongoDB client instance.
    Creates a new client if one doesn't exist.
    """
    global mongo_client
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(MONGO_URL)
    return mongo_client


def get_database(db_name: str = "newfridge"):
    """
    Get a specific database from MongoDB.
    Default: 'newfridge' database for logs and analytics.
    """
    client = get_mongo_client()
    return client[db_name]


def get_collection(collection_name: str, db_name: str = "newfridge"):
    """
    Get a specific collection from MongoDB.

    Common collections:
    - activity_logs: User activity tracking
    - api_logs: API request/response logs
    - analytics: Usage analytics and metrics
    - error_logs: Error tracking
    """
    db = get_database(db_name)
    return db[collection_name]


async def init_mongo():
    """
    Initialize MongoDB connection and collections.
    Creates indexes for common queries.
    """
    print("📊 Initializing MongoDB...")

    try:
        client = get_mongo_client()

        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")

        # Get newfridge database
        db = get_database("newfridge")

        # Create collections with indexes

        # Activity logs collection
        activity_logs = db["activity_logs"]
        await activity_logs.create_index([("user_id", 1), ("timestamp", -1)])
        await activity_logs.create_index([("action_type", 1)])

        # API logs collection
        api_logs = db["api_logs"]
        await api_logs.create_index([("timestamp", -1)])
        await api_logs.create_index([("endpoint", 1)])
        await api_logs.create_index([("status_code", 1)])

        # Analytics collection
        analytics = db["analytics"]
        await analytics.create_index([("metric_type", 1), ("date", -1)])

        # Error logs collection
        error_logs = db["error_logs"]
        await error_logs.create_index([("timestamp", -1)])
        await error_logs.create_index([("error_type", 1)])

        print("✅ MongoDB collections and indexes created!")

    except Exception as e:
        print(f"⚠️  MongoDB initialization warning: {e}")


async def close_mongo():
    """
    Close MongoDB connection.
    Call this on application shutdown.
    """
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("✅ MongoDB connection closed.")


# Helper functions for common logging operations

async def log_activity(user_id: str, action_type: str, details: dict):
    """
    Log user activity to MongoDB.

    Example:
        await log_activity(
            user_id="user-123",
            action_type="fridge_item_added",
            details={"fridge_id": "...", "ingredient": "milk", "quantity": 1000}
        )
    """
    from datetime import datetime

    collection = get_collection("activity_logs")
    await collection.insert_one({
        "user_id": user_id,
        "action_type": action_type,
        "details": details,
        "timestamp": datetime.utcnow()
    })


async def log_api_request(endpoint: str, method: str, status_code: int,
                         response_time_ms: float, user_id: Optional[str] = None):
    """
    Log API request to MongoDB.

    Example:
        await log_api_request(
            endpoint="/api/fridges",
            method="GET",
            status_code=200,
            response_time_ms=45.2,
            user_id="user-123"
        )
    """
    from datetime import datetime

    collection = get_collection("api_logs")
    await collection.insert_one({
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "user_id": user_id,
        "timestamp": datetime.utcnow()
    })


async def log_error(error_type: str, message: str, stack_trace: Optional[str] = None,
                   user_id: Optional[str] = None, context: Optional[dict] = None):
    """
    Log error to MongoDB.

    Example:
        await log_error(
            error_type="DatabaseError",
            message="Failed to connect to PostgreSQL",
            stack_trace=traceback.format_exc(),
            context={"endpoint": "/api/users"}
        )
    """
    from datetime import datetime

    collection = get_collection("error_logs")
    await collection.insert_one({
        "error_type": error_type,
        "message": message,
        "stack_trace": stack_trace,
        "user_id": user_id,
        "context": context or {},
        "timestamp": datetime.utcnow()
    })


async def save_analytics(metric_type: str, value: float, dimensions: Optional[dict] = None):
    """
    Save analytics metric to MongoDB.

    Example:
        await save_analytics(
            metric_type="daily_active_users",
            value=150,
            dimensions={"date": "2025-12-05"}
        )
    """
    from datetime import datetime, date

    collection = get_collection("analytics")
    await collection.insert_one({
        "metric_type": metric_type,
        "value": value,
        "dimensions": dimensions or {},
        "date": date.today(),
        "timestamp": datetime.utcnow()
    })
