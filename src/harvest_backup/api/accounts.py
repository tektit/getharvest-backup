"""Account discovery for Harvest API."""

import logging

from harvest_backup.api.client import HarvestAPIClient
from harvest_backup.models.account import Account, AccountsResponse

logger = logging.getLogger(__name__)

HARVEST_DOMAIN_SUFFIX = ".harvestapp.com"


def _extract_subdomain_from_data(company_data: dict) -> str:
    """Extract subdomain from company data.

    Args:
        company_data: Company data dictionary

    Returns:
        Subdomain string

    Raises:
        ValueError: If subdomain cannot be extracted
    """
    # Try full_domain first
    if full_domain := company_data.get("full_domain"):
        return full_domain.replace(HARVEST_DOMAIN_SUFFIX, "")

    # Try base_uri as fallback
    if base_uri := company_data.get("base_uri"):
        # Extract from https://{subdomain}.harvestapp.com
        return base_uri.replace("https://", "").replace(HARVEST_DOMAIN_SUFFIX, "")

    raise ValueError(
        "Could not extract subdomain from company data (missing full_domain and base_uri)"
    )


async def discover_accounts(client: HarvestAPIClient) -> list[Account]:
    """Discover all Harvest accounts for the authenticated user and fetch company data.

    Args:
        client: Harvest API client

    Returns:
        List of Harvest accounts (excluding Forecast accounts) with company_data and subdomain populated
    """
    logger.info("Discovering Harvest accounts...")
    # Pass None as account_id to use accounts API endpoint
    response_data = await client.get("", account_id=None)
    accounts_response = AccountsResponse(**response_data)

    # Filter to only Harvest accounts
    harvest_accounts = [
        account for account in accounts_response.accounts if account.product == "harvest"
    ]

    logger.info(f"Found {len(harvest_accounts)} Harvest account(s)")
    for account in harvest_accounts:
        logger.info(f"  - Account {account.id}: {account.name}")
        account.company_data = await client.get_company(account.id)
        account.subdomain = _extract_subdomain_from_data(account.company_data)
        logger.debug(f"Fetched company data for account {account.id}: {account.subdomain}")

    return harvest_accounts
