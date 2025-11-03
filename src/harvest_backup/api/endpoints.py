"""Endpoint definitions for Harvest API v2."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Endpoint:
    """API endpoint definition."""

    path: str
    name: str
    has_list: bool = True
    has_detail: bool = True
    has_nested: bool = False
    nested_paths: list[str] | None = None
    has_pdf: bool = False
    pdf_path: str | None = None


# All Harvest API v2 endpoints
ENDPOINTS: list[Endpoint] = [
    Endpoint(
        path="/v2/clients",
        name="clients",
    ),
    Endpoint(
        path="/v2/contacts",
        name="contacts",
    ),
    Endpoint(
        path="/v2/projects",
        name="projects",
        nested_paths=[
            "/v2/projects/{id}/user_assignments",
            "/v2/projects/{id}/task_assignments",
        ],
    ),
    Endpoint(
        path="/v2/tasks",
        name="tasks",
    ),
    Endpoint(
        path="/v2/time_entries",
        name="time_entries",
    ),
    Endpoint(
        path="/v2/users",
        name="users",
        nested_paths=[
            "/v2/users/{id}/billable_rates",
            "/v2/users/{id}/cost_rates",
            "/v2/users/{id}/project_assignments",
            "/v2/users/{id}/teammates",
        ],
    ),
    Endpoint(
        path="/v2/users/me",
        name="users_me",
        has_list=False,
        has_detail=False,
    ),
    Endpoint(
        path="/v2/users/me/project_assignments",
        name="users_me_project_assignments",
        has_detail=False,
    ),
    Endpoint(
        path="/v2/expenses",
        name="expenses",
    ),
    Endpoint(
        path="/v2/expense_categories",
        name="expense_categories",
    ),
    Endpoint(
        path="/v2/invoices",
        name="invoices",
        has_pdf=True,
        pdf_path="/v2/invoices/{id}.pdf",
    ),
    Endpoint(
        path="/v2/invoice_item_categories",
        name="invoice_item_categories",
    ),
    Endpoint(
        path="/v2/estimates",
        name="estimates",
        has_pdf=True,
        pdf_path="/v2/estimates/{id}.pdf",
    ),
    Endpoint(
        path="/v2/estimate_item_categories",
        name="estimate_item_categories",
    ),
    Endpoint(
        path="/v2/roles",
        name="roles",
    ),
    Endpoint(
        path="/v2/company",
        name="company",
        has_list=False,
        has_detail=False,
    ),
]


def get_endpoint(name: str) -> Endpoint | None:
    """Get endpoint by name.

    Args:
        name: Endpoint name

    Returns:
        Endpoint definition or None if not found
    """
    for endpoint in ENDPOINTS:
        if endpoint.name == name:
            return endpoint
    return None


def get_all_endpoints() -> list[Endpoint]:
    """Get all endpoint definitions.

    Returns:
        List of all endpoints
    """
    return ENDPOINTS

