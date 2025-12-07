from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator


class UserRegisterRequest(BaseModel):
    """
    Request schema for user registration.
    """
    user_name: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Username (3-20 characters)"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (minimum 8 characters)"
    )

    @validator('user_name')
    def username_alphanumeric(cls, v):
        """Ensure username contains only alphanumeric characters and underscores."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v


class UserLoginRequest(BaseModel):
    """
    Request schema for user login.
    """
    user_name: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """
    Response schema for successful authentication.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: UUID = Field(..., description="User ID")
    user_name: str = Field(..., description="Username")
    role: str = Field(..., description="User role (User or Admin)")


class UserResponse(BaseModel):
    """
    Response schema for user information.
    """
    user_id: UUID
    user_name: str
    email: str
    status: str
    role: str = "User"

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """
    Generic message response.
    """
    message: str
    detail: Optional[str] = None
