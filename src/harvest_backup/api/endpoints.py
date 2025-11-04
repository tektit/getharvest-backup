"""Endpoint definitions for Harvest API v2."""

from dataclasses import dataclass


@dataclass
class Endpoint:
    """API endpoint definition."""

    path: str
    name: str
    has_list: bool = True
    has_detail: bool = True
    has_nested: bool = False
    nested_paths: list[str] | None = None


# All Harvest API v2 endpoints
ENDPOINTS: dict[str, Endpoint] = {
    "clients": Endpoint(path="/v2/clients", name="clients"),
    "contacts": Endpoint(path="/v2/contacts", name="contacts"),
    "projects": Endpoint(
        path="/v2/projects",
        name="projects",
        has_nested=True,
        nested_paths=[
            "/v2/projects/{id}/user_assignments",
            "/v2/projects/{id}/task_assignments",
        ],
    ),
    "tasks": Endpoint(path="/v2/tasks", name="tasks"),
    "time_entries": Endpoint(path="/v2/time_entries", name="time_entries"),
    "users": Endpoint(
        path="/v2/users",
        name="users",
        has_nested=True,
        nested_paths=[
            "/v2/users/{id}/billable_rates",
            "/v2/users/{id}/cost_rates",
            "/v2/users/{id}/project_assignments",
            "/v2/users/{id}/teammates",
        ],
    ),
    "users_me": Endpoint(
        path="/v2/users/me",
        name="users_me",
        has_list=False,
        has_detail=False,
    ),
    "users_me_project_assignments": Endpoint(
        path="/v2/users/me/project_assignments",
        name="users_me_project_assignments",
        has_detail=False,
    ),
    "expenses": Endpoint(path="/v2/expenses", name="expenses"),
    "expense_categories": Endpoint(path="/v2/expense_categories", name="expense_categories"),
    "invoices": Endpoint(
        path="/v2/invoices",
        name="invoices",
        # Note: PDFs are downloaded via client links (public URLs, no auth required)
        # Format: https://{subdomain}.harvestapp.com/client/invoices/{client_key}.pdf
        # The client_key is available in the invoice JSON data
    ),
    "invoice_item_categories": Endpoint(
        path="/v2/invoice_item_categories", name="invoice_item_categories"
    ),
    "estimates": Endpoint(
        path="/v2/estimates",
        name="estimates",
        # Note: PDFs are downloaded via client links (public URLs, no auth required)
        # Format: https://{subdomain}.harvestapp.com/client/estimates/{client_key}.pdf
        # The client_key is available in the estimate JSON data
    ),
    "estimate_item_categories": Endpoint(
        path="/v2/estimate_item_categories", name="estimate_item_categories"
    ),
    "roles": Endpoint(path="/v2/roles", name="roles"),
    "company": Endpoint(
        path="/v2/company",
        name="company",
        has_list=False,
        has_detail=False,
    ),
}


def get_endpoint(name: str) -> Endpoint | None:
    """Get endpoint by name.

    Args:
        name: Endpoint name

    Returns:
        Endpoint definition or None if not found
    """
    return ENDPOINTS.get(name)
