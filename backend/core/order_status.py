"""
Order status state machine and validation.

This module enforces business rules for order status transitions
and role-based permissions.
"""
from typing import Optional
from fastapi import HTTPException


class OrderStatusManager:
    """
    Manages order status transitions with state machine validation.

    Valid statuses:
    - Pending: Order placed, awaiting partner acceptance
    - Processing: Partner is preparing the order
    - Shipped: Order dispatched, in transit
    - Delivered: Order arrived at destination
    - Cancelled: Order cancelled by user or admin
    """

    # Define valid status transitions (state machine)
    VALID_TRANSITIONS = {
        "Pending": ["Processing", "Cancelled"],
        "Processing": ["Shipped", "Cancelled"],
        "Shipped": ["Delivered"],
        "Delivered": [],  # Terminal state
        "Cancelled": []   # Terminal state
    }

    # Role-based permissions
    USER_ALLOWED_TRANSITIONS = {
        "Pending": ["Cancelled"],   # Users can cancel pending orders
        "Shipped": ["Delivered"],   # Users can confirm delivery when package arrives
    }

    PARTNER_ALLOWED_TRANSITIONS = {
        "Pending": ["Processing", "Cancelled"],
        "Processing": ["Shipped", "Cancelled"],
        "Shipped": ["Delivered"],
    }

    # Admin can do any valid transition
    ADMIN_ALLOWED_TRANSITIONS = VALID_TRANSITIONS

    @staticmethod
    def validate_transition(
        current_status: str,
        new_status: str,
        role: str = "user"
    ) -> None:
        """
        Validate if a status transition is allowed for the given role.

        Args:
            current_status: Current order status
            new_status: Desired new status
            role: User role ("user", "partner", "admin")

        Raises:
            HTTPException: If transition is invalid or not allowed for role
        """
        # Check if current status is valid
        if current_status not in OrderStatusManager.VALID_TRANSITIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid current status: {current_status}"
            )

        # Check if new status is valid
        if new_status not in OrderStatusManager.VALID_TRANSITIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {new_status}"
            )

        # Check if transition is allowed in general
        valid_next_statuses = OrderStatusManager.VALID_TRANSITIONS[current_status]
        if new_status not in valid_next_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transition: {current_status} → {new_status}. "
                       f"Valid next statuses: {', '.join(valid_next_statuses) if valid_next_statuses else 'none (terminal state)'}"
            )

        # Check role-based permissions
        if role == "user":
            allowed = OrderStatusManager.USER_ALLOWED_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Users can only cancel pending orders. "
                           f"Contact support or wait for partner to update status."
                )
        elif role == "partner":
            allowed = OrderStatusManager.PARTNER_ALLOWED_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Partner cannot perform this transition: {current_status} → {new_status}"
                )
        # Admin role has no additional restrictions beyond valid transitions

    @staticmethod
    def can_cancel(current_status: str, role: str = "user") -> bool:
        """
        Check if an order can be cancelled in its current status.

        Args:
            current_status: Current order status
            role: User role

        Returns:
            True if cancellation is allowed, False otherwise
        """
        if role == "admin":
            return "Cancelled" in OrderStatusManager.VALID_TRANSITIONS.get(current_status, [])

        if role == "user":
            return current_status == "Pending"

        if role == "partner":
            return current_status in ["Pending", "Processing"]

        return False

    @staticmethod
    def is_terminal(status: str) -> bool:
        """Check if a status is terminal (no further transitions allowed)."""
        return status in ["Delivered", "Cancelled"]

    @staticmethod
    def is_pending_delivery(status: str) -> bool:
        """Check if order is pending delivery (can arrive in the future)."""
        return status in ["Pending", "Processing", "Shipped"]
