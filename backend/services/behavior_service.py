"""
Service for tracking and analyzing user behavior in MongoDB.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from mongodb import get_database
from schemas.behavior import (
    UserBehaviorLog,
    APIUsageLog,
    SearchQueryLog,
    UserActivityStats,
    APIEndpointStats,
    SearchTrendsStats
)


class BehaviorService:
    """Service for logging and analyzing user behavior."""

    # ========================================================================
    # User Behavior Logging
    # ========================================================================

    @staticmethod
    async def log_user_action(
        action_type: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a user action to MongoDB.

        Args:
            action_type: Type of action (e.g., 'login', 'view_recipe', 'cook_recipe')
            user_id: User performing the action (None if anonymous)
            resource_type: Type of resource (e.g., 'recipe', 'ingredient')
            resource_id: ID of the resource
            metadata: Additional context data
        """
        try:
            db = get_database()
            collection = db.user_behavior

            log_entry = UserBehaviorLog(
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )

            await collection.insert_one(log_entry.model_dump(mode='json'))

        except Exception as e:
            # Don't fail the main request if logging fails
            print(f"⚠️  Failed to log user action: {e}")

    @staticmethod
    async def log_api_usage(
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """Log API endpoint usage."""
        try:
            db = get_database()
            collection = db.api_usage

            log_entry = APIUsageLog(
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                status_code=status_code,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                request_size=request_size,
                response_size=response_size
            )

            await collection.insert_one(log_entry.model_dump(mode='json'))

        except Exception as e:
            print(f"⚠️  Failed to log API usage: {e}")

    @staticmethod
    async def log_search_query(
        query_type: str,
        query_text: str,
        results_count: int,
        user_id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Log a search query."""
        try:
            db = get_database()
            collection = db.search_queries

            log_entry = SearchQueryLog(
                user_id=user_id,
                query_type=query_type,
                query_text=query_text,
                results_count=results_count,
                timestamp=datetime.utcnow(),
                filters=filters or {}
            )

            await collection.insert_one(log_entry.model_dump(mode='json'))

        except Exception as e:
            print(f"⚠️  Failed to log search query: {e}")

    # ========================================================================
    # Analytics & Aggregations
    # ========================================================================

    @staticmethod
    async def get_user_activity_stats(
        user_id: UUID,
        days: int = 30
    ) -> UserActivityStats:
        """
        Get aggregated user activity statistics for the past N days.

        Returns action counts, most viewed/cooked recipes, etc.
        """
        db = get_database()
        collection = db.user_behavior

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        # Aggregate actions by type
        pipeline = [
            {
                "$match": {
                    "user_id": str(user_id),
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": "$action_type",
                    "count": {"$sum": 1}
                }
            }
        ]

        actions_cursor = collection.aggregate(pipeline)
        actions_by_type = {doc["_id"]: doc["count"] async for doc in actions_cursor}
        total_actions = sum(actions_by_type.values())

        # Get most viewed recipes
        view_pipeline = [
            {
                "$match": {
                    "user_id": str(user_id),
                    "action_type": "view_recipe",
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": "$resource_id",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]

        viewed_cursor = collection.aggregate(view_pipeline)
        most_viewed = [
            {"recipe_id": doc["_id"], "views": doc["count"]}
            async for doc in viewed_cursor
        ]

        # Get most cooked recipes
        cook_pipeline = [
            {
                "$match": {
                    "user_id": str(user_id),
                    "action_type": "cook_recipe",
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": "$resource_id",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]

        cooked_cursor = collection.aggregate(cook_pipeline)
        most_cooked = [
            {"recipe_id": doc["_id"], "times_cooked": doc["count"]}
            async for doc in cooked_cursor
        ]

        return UserActivityStats(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            total_actions=total_actions,
            actions_by_type=actions_by_type,
            most_viewed_recipes=most_viewed,
            most_cooked_recipes=most_cooked
        )

    @staticmethod
    async def get_api_endpoint_stats(
        endpoint: str,
        method: str,
        days: int = 7
    ) -> APIEndpointStats:
        """Get statistics for a specific API endpoint."""
        db = get_database()
        collection = db.api_usage

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "endpoint": endpoint,
                    "method": method,
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_requests": {"$sum": 1},
                    "avg_response_time": {"$avg": "$response_time_ms"},
                    "success_count": {
                        "$sum": {
                            "$cond": [{"$lt": ["$status_code", 400]}, 1, 0]
                        }
                    }
                }
            }
        ]

        cursor = collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if not result:
            # No data for this endpoint
            return APIEndpointStats(
                endpoint=endpoint,
                method=method,
                period_start=period_start,
                period_end=period_end,
                total_requests=0,
                avg_response_time_ms=0.0,
                success_rate=0.0,
                status_code_distribution={}
            )

        stats = result[0]
        total_requests = stats["total_requests"]
        success_count = stats["success_count"]

        # Get status code distribution
        status_pipeline = [
            {
                "$match": {
                    "endpoint": endpoint,
                    "method": method,
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": "$status_code",
                    "count": {"$sum": 1}
                }
            }
        ]

        status_cursor = collection.aggregate(status_pipeline)
        status_distribution = {
            str(doc["_id"]): doc["count"]
            async for doc in status_cursor
        }

        return APIEndpointStats(
            endpoint=endpoint,
            method=method,
            period_start=period_start,
            period_end=period_end,
            total_requests=total_requests,
            avg_response_time_ms=stats["avg_response_time"],
            success_rate=(success_count / total_requests * 100) if total_requests > 0 else 0.0,
            status_code_distribution=status_distribution
        )

    @staticmethod
    async def get_search_trends(days: int = 30) -> SearchTrendsStats:
        """Get search trends and popular queries."""
        db = get_database()
        collection = db.search_queries

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        # Get top queries
        top_queries_pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": {
                        "query_type": "$query_type",
                        "query_text": "$query_text"
                    },
                    "count": {"$sum": 1},
                    "avg_results": {"$avg": "$results_count"}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]

        top_cursor = collection.aggregate(top_queries_pipeline)
        top_queries = [
            {
                "query_type": doc["_id"]["query_type"],
                "query_text": doc["_id"]["query_text"],
                "search_count": doc["count"],
                "avg_results": doc["avg_results"]
            }
            async for doc in top_cursor
        ]

        # Get queries by type
        type_pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": "$query_type",
                    "count": {"$sum": 1}
                }
            }
        ]

        type_cursor = collection.aggregate(type_pipeline)
        queries_by_type = {
            doc["_id"]: doc["count"]
            async for doc in type_cursor
        }

        # Average results per query
        avg_pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": period_start, "$lte": period_end}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_results": {"$avg": "$results_count"}
                }
            }
        ]

        avg_cursor = collection.aggregate(avg_pipeline)
        avg_result = await avg_cursor.to_list(length=1)
        avg_results_per_query = avg_result[0]["avg_results"] if avg_result else 0.0

        return SearchTrendsStats(
            period_start=period_start,
            period_end=period_end,
            top_queries=top_queries,
            queries_by_type=queries_by_type,
            avg_results_per_query=avg_results_per_query
        )

    # ========================================================================
    # Utility Methods
    # ========================================================================

    @staticmethod
    async def get_recent_user_actions(
        user_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent actions for a user."""
        db = get_database()
        collection = db.user_behavior

        cursor = collection.find(
            {"user_id": str(user_id)}
        ).sort("timestamp", -1).limit(limit)

        results = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for doc in results:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
                
        return results

    @staticmethod
    async def clear_old_logs(days_to_keep: int = 90):
        """
        Clean up old logs (optional maintenance task).

        Remove logs older than specified days to manage storage.
        """
        db = get_database()
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Clear old user behavior logs
        result1 = await db.user_behavior.delete_many(
            {"timestamp": {"$lt": cutoff_date}}
        )

        # Clear old API usage logs
        result2 = await db.api_usage.delete_many(
            {"timestamp": {"$lt": cutoff_date}}
        )

        # Clear old search query logs
        result3 = await db.search_queries.delete_many(
            {"timestamp": {"$lt": cutoff_date}}
        )

        total_deleted = result1.deleted_count + result2.deleted_count + result3.deleted_count

        print(f"✅ Cleaned up {total_deleted} old log entries (older than {days_to_keep} days)")

        return total_deleted
