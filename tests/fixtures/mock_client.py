"""Mock API client for testing with sample data."""

import logging
from collections.abc import AsyncIterator
from typing import Any

logger = logging.getLogger(__name__)

# Import sample responses - these don't depend on the real client
from tests.fixtures.sample_responses import (
    SAMPLE_ACCOUNTS_RESPONSE,
    SAMPLE_CLIENTS_RESPONSE,
    SAMPLE_COMPANY_RESPONSE,
    SAMPLE_COMPANY_RESPONSE_2,
    SAMPLE_CONTACTS_RESPONSE,
    SAMPLE_ESTIMATE_ITEM_CATEGORIES_RESPONSE,
    SAMPLE_ESTIMATE_PDF_CONTENT,
    SAMPLE_ESTIMATES_RESPONSE,
    SAMPLE_EXPENSE_CATEGORIES_RESPONSE,
    SAMPLE_EXPENSES_RESPONSE,
    SAMPLE_INVOICE_ITEM_CATEGORIES_RESPONSE,
    SAMPLE_INVOICE_PDF_CONTENT,
    SAMPLE_INVOICES_RESPONSE,
    SAMPLE_PROJECT_TASK_ASSIGNMENTS_RESPONSE,
    SAMPLE_PROJECT_USER_ASSIGNMENTS_RESPONSE,
    SAMPLE_PROJECTS_RESPONSE,
    SAMPLE_ROLES_RESPONSE,
    SAMPLE_TASKS_RESPONSE,
    SAMPLE_TIME_ENTRIES_RESPONSE,
    SAMPLE_USER_BILLABLE_RATES_RESPONSE,
    SAMPLE_USER_COST_RATES_RESPONSE,
    SAMPLE_USER_PROJECT_ASSIGNMENTS_RESPONSE,
    SAMPLE_USER_TEAMMATES_RESPONSE,
    SAMPLE_USERS_ME_PROJECT_ASSIGNMENTS_RESPONSE,
    SAMPLE_USERS_ME_RESPONSE,
    SAMPLE_USERS_RESPONSE,
)


class MockHarvestAPIClient:
    """Mock API client that returns sample data instead of making real API calls.
    
    This class implements the same interface as HarvestAPIClient but uses
    mock/test data instead of making real HTTP requests.
    """

    BASE_URL = "https://api.harvestapp.com"
    ACCOUNTS_URL = "https://id.getharvest.com/api/v2/accounts"

    def __init__(self, access_token: str = "test_token", user_agent: str = "HarvestBackupTool/0.1.0") -> None:
        """Initialize mock client."""
        self.access_token = access_token
        self.user_agent = user_agent
        self._response_map: dict[str, Any] = {}
        # Rate limiter is not needed for mock client, but we can add a no-op one
        self.rate_limiter = None  # type: ignore

    def _get_response_for_endpoint(self, endpoint: str, account_id: int | None = None) -> dict | list:
        """Get mock response for an endpoint."""
        # Check for nested resources first (they have specific path patterns)
        if "/user_assignments" in endpoint:
            return SAMPLE_PROJECT_USER_ASSIGNMENTS_RESPONSE
        if "/task_assignments" in endpoint:
            return SAMPLE_PROJECT_TASK_ASSIGNMENTS_RESPONSE
        if "/billable_rates" in endpoint:
            return SAMPLE_USER_BILLABLE_RATES_RESPONSE
        if "/cost_rates" in endpoint:
            return SAMPLE_USER_COST_RATES_RESPONSE
        if "/project_assignments" in endpoint and "/users/" in endpoint:
            return SAMPLE_USER_PROJECT_ASSIGNMENTS_RESPONSE
        if "/teammates" in endpoint:
            return SAMPLE_USER_TEAMMATES_RESPONSE

        # Map endpoint paths to sample responses
        endpoint_map: dict[str, dict | list] = {
            # Company endpoint
            "/v2/company": SAMPLE_COMPANY_RESPONSE if account_id == 12345 else SAMPLE_COMPANY_RESPONSE_2,
            # List endpoints
            "/v2/clients": SAMPLE_CLIENTS_RESPONSE,
            "/v2/contacts": SAMPLE_CONTACTS_RESPONSE,
            "/v2/projects": SAMPLE_PROJECTS_RESPONSE,
            "/v2/tasks": SAMPLE_TASKS_RESPONSE,
            "/v2/time_entries": SAMPLE_TIME_ENTRIES_RESPONSE,
            "/v2/users": SAMPLE_USERS_RESPONSE,
            "/v2/users/me": SAMPLE_USERS_ME_RESPONSE,
            "/v2/users/me/project_assignments": SAMPLE_USERS_ME_PROJECT_ASSIGNMENTS_RESPONSE,
            "/v2/expenses": SAMPLE_EXPENSES_RESPONSE,
            "/v2/expense_categories": SAMPLE_EXPENSE_CATEGORIES_RESPONSE,
            "/v2/invoices": SAMPLE_INVOICES_RESPONSE,
            "/v2/invoice_item_categories": SAMPLE_INVOICE_ITEM_CATEGORIES_RESPONSE,
            "/v2/estimates": SAMPLE_ESTIMATES_RESPONSE,
            "/v2/estimate_item_categories": SAMPLE_ESTIMATE_ITEM_CATEGORIES_RESPONSE,
            "/v2/roles": SAMPLE_ROLES_RESPONSE,
        }

        return endpoint_map.get(endpoint, {})

    def _format_page_info(self, params: dict | None) -> str:
        """Format pagination info for logging.
        
        Args:
            params: Request parameters
            
        Returns:
            Formatted page info string
        """
        if not params or "page" not in params:
            return ""
        page = params.get("page", 1)
        per_page = params.get("per_page", 2000)
        page_info = f" page={page}"
        if per_page != 2000:
            page_info += f" per_page={per_page}"
        return page_info

    async def get(self, endpoint: str, account_id: int | None = None, params: dict | None = None) -> dict:
        """Mock GET request."""
        # Handle accounts API (empty endpoint with account_id=None)
        if endpoint == "" and account_id is None:
            url = self.ACCOUNTS_URL
            logger.verbose(f"GET {url} OK")
            return SAMPLE_ACCOUNTS_RESPONSE
        
        # Build URL for logging
        if account_id is None:
            url = self.ACCOUNTS_URL
        else:
            url = f"{self.BASE_URL}{endpoint}"
        
        page_info = self._format_page_info(params)
        logger.verbose(f"GET {url}{page_info} OK")
        
        response = self._get_response_for_endpoint(endpoint, account_id)
        if isinstance(response, list):
            return {"items": response}
        return response

    async def get_paginated(
        self, endpoint: str, account_id: int, params: dict | None = None
    ) -> AsyncIterator[dict]:
        """Mock paginated GET request."""
        url = f"{self.BASE_URL}{endpoint}"
        page_info = self._format_page_info(params)
        logger.verbose(f"GET {url}{page_info} OK")
        
        response = self._get_response_for_endpoint(endpoint, account_id)

        # Extract items from response
        items: list[dict] = []
        if isinstance(response, dict):
            # Look for list values in the response
            for key, value in response.items():
                if isinstance(value, list) and key not in ("links", "per_page", "total_pages", "total_entries", "page"):
                    items = value
                    break
        elif isinstance(response, list):
            items = response

        # Yield items
        for item in items:
            yield item

    async def get_company(self, account_id: int) -> dict:
        """Mock get company data."""
        url = f"{self.BASE_URL}/v2/company"
        logger.verbose(f"GET {url} OK")
        return self._get_response_for_endpoint("/v2/company", account_id)  # type: ignore[return-value]

    async def download_client_link(self, url: str) -> bytes:
        """Mock download client link (PDF)."""
        logger.verbose(f"GET {url} OK")
        
        # Return different PDFs based on URL (invoices vs estimates)
        if "/invoices/" in url:
            # Extract client_key from URL to match with invoice data
            # URL format: https://{subdomain}.harvestapp.com/client/invoices/{client_key}.pdf
            if "abc123def456" in url:  # Matches SAMPLE_INVOICES_RESPONSE client_key
                return SAMPLE_INVOICE_PDF_CONTENT
            # Default invoice PDF
            return SAMPLE_INVOICE_PDF_CONTENT
        elif "/estimates/" in url:
            # Extract client_key from URL to match with estimate data
            # URL format: https://{subdomain}.harvestapp.com/client/estimates/{client_key}.pdf
            if "xyz789ghi012" in url:  # Matches SAMPLE_ESTIMATES_RESPONSE client_key
                return SAMPLE_ESTIMATE_PDF_CONTENT
            # Default estimate PDF
            return SAMPLE_ESTIMATE_PDF_CONTENT
        else:
            # Unknown PDF type, return generic PDF
            return b"%PDF-1.4\nfake pdf content for testing"

    async def close(self) -> None:
        """Mock close - no-op."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

