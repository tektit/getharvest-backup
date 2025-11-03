"""Account discovery for Harvest API."""

import logging

from harvest_backup.api.client import HarvestAPIClient
from harvest_backup.models.account import Account, AccountsResponse

logger = logging.getLogger(__name__)


async def discover_accounts(client: HarvestAPIClient) -> list[Account]:
    """Discover all Harvest accounts for the authenticated user.

    Args:
        client: Harvest API client

    Returns:
        List of Harvest accounts (excluding Forecast accounts)
    """
    logger.info("Discovering Harvest accounts...")
    # Pass None as account_id to use accounts API endpoint
    response_data = await client.get("", account_id=None)
    accounts_response = AccountsResponse(**response_data)

    # Filter to only Harvest accounts
    harvest_accounts = [account for account in accounts_response.accounts if account.product == "harvest"]

    logger.info(f"Found {len(harvest_accounts)} Harvest account(s)")
    for account in harvest_accounts:
        logger.info(f"  - Account {account.id}: {account.name}")

    return harvest_accounts

