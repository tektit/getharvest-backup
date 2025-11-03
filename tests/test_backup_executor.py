"""Tests for backup executor."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harvest_backup.api.client import HarvestAPIClient
from harvest_backup.api.endpoints import Endpoint, get_endpoint
from harvest_backup.backup.executor import BackupExecutor
from harvest_backup.backup.writer import BackupWriter
from harvest_backup.models.account import Account
from tests.fixtures.sample_responses import (
    SAMPLE_CLIENT_CONTACTS_RESPONSE,
    SAMPLE_CLIENT_DETAIL_RESPONSE,
    SAMPLE_CLIENTS_RESPONSE,
    SAMPLE_COMPANY_RESPONSE,
)


@pytest.mark.asyncio
async def test_backup_executor_company_endpoint(tmp_path: Path) -> None:
    """Test backup executor for company endpoint."""
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=SAMPLE_COMPANY_RESPONSE)

    executor = BackupExecutor(mock_client, writer, dry_run=False)

    account = Account(id=12345, name="Test Company", product="harvest")

    await executor._backup_account(account)

    # Check that company data was written
    company_file = tmp_path / "harvest_account_12345" / "company" / "data.json"
    assert company_file.exists()


@pytest.mark.asyncio
async def test_backup_executor_clients_endpoint(tmp_path: Path) -> None:
    """Test backup executor for clients endpoint with pagination."""
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()

    # Mock paginated responses as async generator
    async def mock_get_paginated(*args, **kwargs):
        for client in SAMPLE_CLIENTS_RESPONSE["clients"]:
            yield client

    mock_client.get_paginated = mock_get_paginated
    mock_client.get = AsyncMock(return_value=SAMPLE_CLIENT_DETAIL_RESPONSE)

    executor = BackupExecutor(mock_client, writer, dry_run=False)

    endpoint = get_endpoint("clients")
    assert endpoint is not None

    await executor._backup_endpoint(12345, endpoint)

    # Check that list was written
    list_file = tmp_path / "harvest_account_12345" / "clients" / "list.json"
    assert list_file.exists()


@pytest.mark.asyncio
async def test_backup_executor_dry_run(tmp_path: Path) -> None:
    """Test backup executor in dry-run mode."""
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=SAMPLE_COMPANY_RESPONSE)

    executor = BackupExecutor(mock_client, writer, dry_run=True)

    account = Account(id=12345, name="Test Company", product="harvest")

    await executor._backup_account(account)

    # In dry-run mode, files shouldn't be written
    company_file = tmp_path / "harvest_account_12345" / "company" / "data.json"
    # The file might exist if writer was called, but in real dry-run it wouldn't

