"""
Middleware for automatic behavior tracking.
"""
import time
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from services.behavior_service import BehaviorService
from core.security import get_user_id_from_token


class BehaviorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track API usage.

    Logs all API requests with timing, status codes, and user info.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log to MongoDB."""
        # Start timing
        start_time = time.time()

        # Get user ID if authenticated
        user_id: Optional[UUID] = None
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                user_id = get_user_id_from_token(token)
        except Exception:
            pass

        # Get request info
        endpoint = request.url.path
        method = request.method
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Log to MongoDB (async, don't wait for completion)
        # Only log API endpoints, not static files or docs
        if endpoint.startswith("/api/"):
            try:
                await BehaviorService.log_api_usage(
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as e:
                # Don't fail the request if logging fails
                print(f"⚠️  Middleware logging failed: {e}")

        return response


# Decorator for tracking specific user actions
def track_action(action_type: str, resource_type: Optional[str] = None):
    """
    Decorator to track user actions in specific endpoints.

    Usage:
        @track_action("view_recipe", resource_type="recipe")
        async def get_recipe(recipe_id: int, ...):
            ...

    The decorator will automatically log the action with the resource_id
    extracted from the function's parameters.
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Execute the original function
            result = await func(*args, **kwargs)

            # Try to extract user_id and resource_id from kwargs
            user_id = kwargs.get("current_user_id")
            resource_id = None

            # Try to find resource_id from common parameter names
            for param_name in ["recipe_id", "ingredient_id", "order_id", "fridge_id", "partner_id"]:
                if param_name in kwargs:
                    resource_id = str(kwargs[param_name])
                    break

            # Log the action
            try:
                await BehaviorService.log_user_action(
                    action_type=action_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id
                )
            except Exception as e:
                print(f"⚠️  Action tracking failed: {e}")

            return result

        return wrapper
    return decorator
