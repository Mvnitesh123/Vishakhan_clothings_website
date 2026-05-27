from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class UserSignupSchema(BaseModel):
    """
    Example schema for User Signup.
    Validates that username is provided, email is valid, and password meets criteria.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit.')
        return v

class ProductQuerySchema(BaseModel):
    """
    Example schema for querying products via GET parameters.
    """
    category: Optional[str] = Field(None, max_length=100)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    sort_by: Optional[str] = Field("price_asc", pattern="^(price_asc|price_desc|newest)$")
