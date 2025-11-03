"""Account data models."""

from typing import Literal

from pydantic import BaseModel, Field


class Account(BaseModel):
    """Harvest account model."""

    id: int = Field(..., description="Account ID")
    name: str = Field(..., description="Account name")
    product: Literal["harvest", "forecast"] = Field(..., description="Product type")


class User(BaseModel):
    """User model from accounts API."""

    id: int = Field(..., description="User ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str = Field(..., description="Email address")


class AccountsResponse(BaseModel):
    """Response from the accounts API endpoint."""

    user: User = Field(..., description="Current user")
    accounts: list[Account] = Field(..., description="List of accounts")

