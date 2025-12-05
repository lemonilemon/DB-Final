from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================

class FridgeCreateRequest(BaseModel):
    """Request model for creating a new fridge."""
    fridge_name: str = Field(..., min_length=1, max_length=50, description="Name of the fridge")
    description: Optional[str] = Field(None, max_length=200, description="Optional description")


class FridgeUpdateRequest(BaseModel):
    """Request model for updating fridge information."""
    fridge_name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class AddMemberRequest(BaseModel):
    """Request model for adding a member to a fridge."""
    user_name: str = Field(..., min_length=3, max_length=20, description="Username to add")
    role: str = Field(..., description="Role: 'Owner' or 'Member'")

    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "john_doe",
                "role": "Member"
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class FridgeMemberResponse(BaseModel):
    """Response model for a fridge member."""
    user_id: UUID
    user_name: str
    email: str
    role: str  # Owner or Member

    class Config:
        from_attributes = True


class FridgeBasicResponse(BaseModel):
    """Basic fridge information (for list views)."""
    fridge_id: UUID
    fridge_name: str
    description: Optional[str]
    your_role: str  # The current user's role in this fridge

    class Config:
        from_attributes = True


class FridgeDetailResponse(BaseModel):
    """Detailed fridge information with members."""
    fridge_id: UUID
    fridge_name: str
    description: Optional[str]
    your_role: str
    members: List[FridgeMemberResponse]

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
    detail: Optional[str] = None
