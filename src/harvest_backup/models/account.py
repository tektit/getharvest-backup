"""Account data models."""

from typing import Literal

from pydantic import BaseModel


class Account(BaseModel):
    """Harvest account model."""

    id: int
    name: str
    product: Literal["harvest", "forecast"]
    company_data: dict | None = None  # Company data fetched from /v2/company endpoint
    subdomain: str | None = None  # Account subdomain extracted from company_data


class User(BaseModel):
    """User model from accounts API."""

    id: int
    first_name: str
    last_name: str
    email: str


class AccountsResponse(BaseModel):
    """Response from the accounts API endpoint."""

    user: User
    accounts: list[Account]
