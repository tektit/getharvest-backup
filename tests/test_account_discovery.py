"""Tests for account discovery."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from harvest_backup.api.accounts import discover_accounts
from tests.fixtures.sample_responses import SAMPLE_ACCOUNTS_RESPONSE


@pytest.mark.asyncio
async def test_discover_accounts() -> None:
    """Test account discovery filters Harvest accounts."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=SAMPLE_ACCOUNTS_RESPONSE)
    # Mock get_company for each account
    mock_client.get_company = AsyncMock(return_value={"full_domain": "testcompany.harvestapp.com"})

    accounts = await discover_accounts(mock_client)

    # Should filter out Forecast account
    assert len(accounts) == 2
    assert all(account.product == "harvest" for account in accounts)
    assert accounts[0].id == 12345
    assert accounts[0].name == "Test Company"
    assert accounts[1].id == 67890
    assert accounts[1].name == "Another Company"
    # Check that company_data and subdomain were populated
    assert accounts[0].company_data is not None
    assert accounts[0].subdomain == "testcompany"
    assert accounts[1].company_data is not None
    assert accounts[1].subdomain == "testcompany"


@pytest.mark.asyncio
async def test_discover_accounts_no_harvest() -> None:
    """Test account discovery when no Harvest accounts exist."""
    response = {
        "user": {"id": 1, "first_name": "John", "last_name": "Doe", "email": "[email protected]"},
        "accounts": [{"id": 99999, "name": "Forecast Account", "product": "forecast"}],
    }

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=response)
    # No need to mock get_company since no harvest accounts will be found

    accounts = await discover_accounts(mock_client)

    assert len(accounts) == 0

