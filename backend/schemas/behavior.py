"""
Schemas for behavior tracking in MongoDB.

These Pydantic models define the structure of behavior data stored in MongoDB.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# User Behavior Tracking
# ============================================================================

class UserBehaviorLog(BaseModel):
    """Log of user actions and interactions."""
    user_id: Optional[UUID] = Field(None, description="User performing the action (None if anonymous)")
    action_type: str = Field(..., description="Type of action (e.g., 'login', 'view_recipe', 'cook_recipe')")
    resource_type: Optional[str] = Field(None, description="Type of resource (e.g., 'recipe', 'ingredient', 'order')")
    resource_id: Optional[str] = Field(None, description="ID of the resource (if applicable)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context data")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "action_type": "cook_recipe",
                "resource_type": "recipe",
                "resource_id": "42",
                "timestamp": "2025-12-07T10:30:00",
                "metadata": {
                    "fridge_id": "987e4567-e89b-12d3-a456-426614174000",
                    "ingredients_consumed": 5
                }
            }
        }


# ============================================================================
# API Usage Tracking
# ============================================================================

class APIUsageLog(BaseModel):
    """Log of API endpoint usage."""
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    user_id: Optional[UUID] = Field(None, description="User making the request")
    status_code: int = Field(..., description="HTTP response status code")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    request_size: Optional[int] = Field(None, description="Request body size in bytes")
    response_size: Optional[int] = Field(None, description="Response body size in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/recipes/42",
                "method": "GET",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "status_code": 200,
                "response_time_ms": 45.2,
                "timestamp": "2025-12-07T10:30:00",
                "ip_address": "192.168.1.100"
            }
        }


# ============================================================================
# Search Query Tracking
# ============================================================================

class SearchQueryLog(BaseModel):
    """Log of search queries."""
    user_id: Optional[UUID] = Field(None, description="User performing the search")
    query_type: str = Field(..., description="Type of search (e.g., 'recipe', 'ingredient')")
    query_text: str = Field(..., description="Search query text")
    results_count: int = Field(..., description="Number of results returned")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Applied filters")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "query_type": "recipe",
                "query_text": "pasta",
                "results_count": 15,
                "timestamp": "2025-12-07T10:30:00",
                "filters": {"cooking_time_max": 30}
            }
        }


# ============================================================================
# Aggregate Statistics (Read Models)
# ============================================================================

class UserActivityStats(BaseModel):
    """Aggregated user activity statistics."""
    user_id: UUID
    period_start: datetime
    period_end: datetime
    total_actions: int
    actions_by_type: Dict[str, int]
    most_viewed_recipes: list[Dict[str, Any]]
    most_cooked_recipes: list[Dict[str, Any]]


class APIEndpointStats(BaseModel):
    """Aggregated API endpoint statistics."""
    endpoint: str
    method: str
    period_start: datetime
    period_end: datetime
    total_requests: int
    avg_response_time_ms: float
    success_rate: float
    status_code_distribution: Dict[str, int]


class SearchTrendsStats(BaseModel):
    """Search trends and popular queries."""
    period_start: datetime
    period_end: datetime
    top_queries: list[Dict[str, Any]]
    queries_by_type: Dict[str, int]
    avg_results_per_query: float
