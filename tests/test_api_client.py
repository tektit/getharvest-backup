"""Tests for API client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from harvest_backup.api.client import HarvestAPIClient, RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter() -> None:
    """Test rate limiter waits when limit is reached."""
    limiter = RateLimiter(max_requests=2, time_window=1.0)

    # First two requests should pass immediately
    await limiter.wait_if_needed()
    await limiter.wait_if_needed()

    # Third request should wait
    start_time = asyncio.get_event_loop().time()
    await limiter.wait_if_needed()
    elapsed = asyncio.get_event_loop().time() - start_time

    # Should have waited at least 1 second
    assert elapsed >= 0.9  # Allow small margin


@pytest.mark.asyncio
async def test_api_client_init() -> None:
    """Test API client initialization."""
    client = HarvestAPIClient("test_token")
    assert client.access_token == "test_token"
    assert client.user_agent == "HarvestBackupTool/0.1.0"
    await client.close()


@pytest.mark.asyncio
async def test_api_client_context_manager() -> None:
    """Test API client as context manager."""
    async with HarvestAPIClient("test_token") as client:
        assert client.access_token == "test_token"
    # Client should be closed after context exit


@pytest.mark.asyncio
async def test_api_client_get_success() -> None:
    """Test successful GET request."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            result = await client.get("/v2/company", account_id=12345)

        assert result == {"data": "test"}


@pytest.mark.asyncio
async def test_api_client_retry_on_429() -> None:
    """Test retry on 429 rate limit error."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # First call returns 429, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers.get.return_value = "1"
        mock_response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=MagicMock(), response=mock_response_429
        )

        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {"data": "test"}
        mock_response_success.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=[mock_response_429, mock_response_success])
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token", max_retries=3) as client:
            result = await client.get("/v2/company", account_id=12345)

        assert result == {"data": "test"}
        assert mock_client.request.call_count == 2


@pytest.mark.asyncio
async def test_api_client_paginated() -> None:
    """Test paginated endpoint iteration."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # First page
        mock_response_page1 = MagicMock()
        mock_response_page1.json.return_value = {
            "clients": [{"id": 1}, {"id": 2}],
            "links": {"next": "http://example.com/page=2"},
        }
        mock_response_page1.raise_for_status = MagicMock()

        # Second page
        mock_response_page2 = MagicMock()
        mock_response_page2.json.return_value = {
            "clients": [{"id": 3}],
            "links": {},
        }
        mock_response_page2.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=[mock_response_page1, mock_response_page2])
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            items = []
            async for item in client.get_paginated("/v2/clients", account_id=12345):
                items.append(item)

        assert len(items) == 3
        assert items[0]["id"] == 1
        assert items[1]["id"] == 2
        assert items[2]["id"] == 3


@pytest.mark.asyncio
async def test_api_client_get_binary() -> None:
    """Test binary data retrieval."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.content = b"PDF content here"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            result = await client.get_binary("/v2/invoices/123.pdf", account_id=12345)

        assert result == b"PDF content here"

