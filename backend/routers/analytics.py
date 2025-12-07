"""
Analytics router for behavior insights and usage statistics.
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Query, Depends

from schemas.behavior import (
    UserActivityStats,
    APIEndpointStats,
    SearchTrendsStats
)
from services.behavior_service import BehaviorService
from core.dependencies import get_current_user_id


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


# ============================================================================
# User Behavior Analytics
# ============================================================================

@router.get(
    "/user/activity",
    response_model=UserActivityStats,
    summary="Get user activity statistics"
)
async def get_user_activity_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get aggregated activity statistics for the current user.

    Returns:
    - Total actions count
    - Actions broken down by type
    - Most viewed recipes
    - Most cooked recipes
    """
    return await BehaviorService.get_user_activity_stats(
        user_id=current_user_id,
        days=days
    )


@router.get(
    "/user/recent-actions",
    response_model=List[Dict[str, Any]],
    summary="Get recent user actions"
)
async def get_recent_actions(
    limit: int = Query(50, ge=1, le=200, description="Number of recent actions to retrieve"),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get the most recent actions performed by the current user."""
    return await BehaviorService.get_recent_user_actions(
        user_id=current_user_id,
        limit=limit
    )


# ============================================================================
# API Usage Analytics
# ============================================================================

@router.get(
    "/api/endpoint-stats",
    response_model=APIEndpointStats,
    summary="Get API endpoint statistics"
)
async def get_endpoint_stats(
    endpoint: str = Query(..., description="API endpoint path (e.g., /api/recipes)"),
    method: str = Query(..., description="HTTP method (GET, POST, etc.)"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get performance and usage statistics for a specific API endpoint.

    Returns:
    - Total requests
    - Average response time
    - Success rate
    - Status code distribution
    """
    return await BehaviorService.get_api_endpoint_stats(
        endpoint=endpoint,
        method=method,
        days=days
    )


# ============================================================================
# Search Analytics
# ============================================================================

@router.get(
    "/search/trends",
    response_model=SearchTrendsStats,
    summary="Get search trends"
)
async def get_search_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get search trends and popular queries.

    Returns:
    - Top search queries
    - Queries by type
    - Average results per query
    """
    return await BehaviorService.get_search_trends(days=days)


# ============================================================================
# Admin Maintenance (Optional)
# ============================================================================

# Uncomment if you want to expose log cleanup endpoint
# from core.dependencies import get_current_admin_user
#
# @router.post(
#     "/admin/cleanup-logs",
#     summary="Clean up old logs"
# )
# async def cleanup_old_logs(
#     days_to_keep: int = Query(90, ge=30, le=365, description="Keep logs from last N days"),
#     current_user: User = Depends(get_current_admin_user)
# ):
#     """Clean up old behavior logs (admin only)."""
#     deleted_count = await BehaviorService.clear_old_logs(days_to_keep)
#     return {
#         "message": f"Successfully cleaned up {deleted_count} old log entries",
#         "days_kept": days_to_keep
#     }
