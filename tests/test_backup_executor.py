"""Tests for backup executor."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from harvest_backup.api.endpoints import Endpoint, get_endpoint
from harvest_backup.backup.executor import BackupExecutor
from harvest_backup.backup.writer import BackupWriter
from harvest_backup.models.account import Account
from tests.fixtures.sample_responses import (
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

    executor = BackupExecutor(mock_client, writer)

    account = Account(id=12345, name="Test Company", product="harvest", company_data=SAMPLE_COMPANY_RESPONSE)

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

    executor = BackupExecutor(mock_client, writer)

    endpoint = get_endpoint("clients")
    assert endpoint is not None

    account = Account(id=12345, name="Test Company", product="harvest")
    await executor._backup_endpoint(account, endpoint)

    # Check that list was written
    list_file = tmp_path / "harvest_account_12345" / "clients" / "list.json"
    assert list_file.exists()


@pytest.mark.asyncio
async def test_backup_executor_company_endpoint_with_data(tmp_path: Path) -> None:
    """Test backup executor for company endpoint with company_data."""
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=SAMPLE_COMPANY_RESPONSE)

    executor = BackupExecutor(mock_client, writer)

    account = Account(id=12345, name="Test Company", product="harvest", company_data=SAMPLE_COMPANY_RESPONSE)

    await executor._backup_account(account)

    # Check that company data was written
    company_file = tmp_path / "harvest_account_12345" / "company" / "data.json"
    assert company_file.exists()


@pytest.mark.asyncio
async def test_backup_pdfs_skips_unchanged(tmp_path: Path) -> None:
    """Test that PDF backup skips downloading unchanged PDFs."""
    import hashlib
    import json
    
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()
    
    # Create sample invoice data
    invoice = {
        "id": 100,
        "client_key": "abc123def456",
        "subject": "Test Invoice",
        "amount": 100.0,
        # Exclude only updated_at from hash (created_at is included)
    }
    
    # Calculate hash for the invoice (exclude only updated_at, not created_at)
    item_for_hash = {k: v for k, v in invoice.items() if k not in ("updated_at",)}
    item_json = json.dumps(item_for_hash, sort_keys=True, ensure_ascii=False)
    json_hash = hashlib.sha256(item_json.encode("utf-8")).hexdigest()
    
    # Pre-create the PDF file with matching hash
    writer.write_binary(
        12345, "invoices", "100", "100.pdf", b"%PDF-1.4\nfake pdf", content_hash=json_hash
    )
    
    executor = BackupExecutor(mock_client, writer)
    
    # Mock download_client_link (should not be called)
    mock_client.download_client_link = AsyncMock()
    
    # Mock paginated to return invoice
    async def mock_get_paginated(*args, **kwargs):
        yield invoice
    
    mock_client.get_paginated = mock_get_paginated
    
    # Mock endpoint
    endpoint = get_endpoint("invoices")
    assert endpoint is not None
    
    account = Account(id=12345, name="Test Company", product="harvest", subdomain="testcompany")
    # Backup endpoint - should skip PDF download
    await executor._backup_endpoint(account, endpoint)
    
    # Verify download_client_link was never called (PDF was skipped)
    assert not mock_client.download_client_link.called


@pytest.mark.asyncio
async def test_backup_pdfs_downloads_changed(tmp_path: Path) -> None:
    """Test that PDF backup downloads PDFs when hash doesn't match."""
    import hashlib
    import json
    
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()
    
    # Create sample invoice data
    invoice = {
        "id": 100,
        "client_key": "abc123def456",
        "subject": "Test Invoice Updated",
        "amount": 150.0,
    }
    
    # Calculate hash for the invoice (exclude only updated_at, not created_at)
    item_for_hash = {k: v for k, v in invoice.items() if k not in ("updated_at",)}
    item_json = json.dumps(item_for_hash, sort_keys=True, ensure_ascii=False)
    json_hash = hashlib.sha256(item_json.encode("utf-8")).hexdigest()
    
    # Pre-create the PDF file with OLD hash (different)
    old_hash = "old_hash_value_12345"
    writer.write_binary(
        12345, "invoices", "100", "100.pdf", b"%PDF-1.4\nold pdf", content_hash=old_hash
    )
    
    executor = BackupExecutor(mock_client, writer)
    
    # Mock download to return PDF content
    mock_client.download_client_link = AsyncMock(return_value=b"%PDF-1.4\nnew pdf content")
    
    # Mock paginated to return invoice
    async def mock_get_paginated(*args, **kwargs):
        yield invoice
    
    mock_client.get_paginated = mock_get_paginated
    
    # Mock endpoint
    endpoint = get_endpoint("invoices")
    assert endpoint is not None
    
    account = Account(id=12345, name="Test Company", product="harvest", subdomain="testcompany")
    # Backup endpoint - should download PDF
    await executor._backup_endpoint(account, endpoint)
    
    # Verify download was called
    assert mock_client.download_client_link.called
    call_args = mock_client.download_client_link.call_args[0][0]
    assert "testcompany.harvestapp.com" in call_args
    assert "abc123def456.pdf" in call_args


@pytest.mark.asyncio
async def test_backup_pdfs_downloads_missing(tmp_path: Path) -> None:
    """Test that PDF backup downloads PDFs when file doesn't exist."""
    import hashlib
    import json
    
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()
    
    # Create sample invoice data
    invoice = {
        "id": 100,
        "client_key": "abc123def456",
        "subject": "Test Invoice",
        "amount": 100.0,
    }
    
    # Calculate hash for the invoice (exclude only updated_at, not created_at)
    item_for_hash = {k: v for k, v in invoice.items() if k not in ("updated_at",)}
    item_json = json.dumps(item_for_hash, sort_keys=True, ensure_ascii=False)
    json_hash = hashlib.sha256(item_json.encode("utf-8")).hexdigest()
    
    # Don't create the PDF file - it should be downloaded
    
    executor = BackupExecutor(mock_client, writer)
    
    # Mock download to return PDF content
    mock_client.download_client_link = AsyncMock(return_value=b"%PDF-1.4\nnew pdf content")
    
    # Mock paginated to return invoice
    async def mock_get_paginated(*args, **kwargs):
        yield invoice
    
    mock_client.get_paginated = mock_get_paginated
    
    # Mock endpoint
    endpoint = get_endpoint("invoices")
    assert endpoint is not None
    
    account = Account(id=12345, name="Test Company", product="harvest", subdomain="testcompany")
    # Backup endpoint - should download PDF
    await executor._backup_endpoint(account, endpoint)
    
    # Verify download was called
    assert mock_client.download_client_link.called
    
    # Verify PDF was written
    pdf_file = tmp_path / "harvest_account_12345" / "invoices" / "artifacts" / "100.pdf"
    assert pdf_file.exists()
    assert pdf_file.read_bytes() == b"%PDF-1.4\nnew pdf content"


@pytest.mark.asyncio
async def test_backup_pdfs_no_subdomain(tmp_path: Path) -> None:
    """Test that PDF backup skips when subdomain is not available."""
    writer = BackupWriter(tmp_path)
    mock_client = MagicMock()
    
    # Create sample invoice data
    invoice = {
        "id": 100,
        "client_key": "abc123def456",
        "subject": "Test Invoice",
        "amount": 100.0,
    }
    
    # Mock paginated to return invoice
    async def mock_get_paginated(*args, **kwargs):
        yield invoice
    
    mock_client.get_paginated = mock_get_paginated
    
    executor = BackupExecutor(mock_client, writer)
    
    # Mock download_client_link (should not be called)
    mock_client.download_client_link = AsyncMock()
    
    # Mock endpoint
    endpoint = get_endpoint("invoices")
    assert endpoint is not None
    
    # Account without subdomain - should skip PDF download
    account = Account(id=12345, name="Test Company", product="harvest")
    # Backup endpoint - should skip PDF download
    await executor._backup_endpoint(account, endpoint)
    
    # Verify download was never called
    assert not mock_client.download_client_link.called

