"""Tests for pagination handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harvest_backup.api.client import HarvestAPIClient


@pytest.mark.asyncio
async def test_pagination_multiple_pages() -> None:
    """Test pagination across multiple pages."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Page 1 with next link
        mock_response_page1 = MagicMock()
        mock_response_page1.json.return_value = {
            "clients": [{"id": 1}, {"id": 2}],
            "per_page": 2,
            "total_pages": 3,
            "page": 1,
            "links": {"next": "http://example.com/clients?page=2"},
        }
        mock_response_page1.raise_for_status = MagicMock()

        # Page 2 with next link
        mock_response_page2 = MagicMock()
        mock_response_page2.json.return_value = {
            "clients": [{"id": 3}, {"id": 4}],
            "per_page": 2,
            "total_pages": 3,
            "page": 2,
            "links": {"next": "http://example.com/clients?page=3"},
        }
        mock_response_page2.raise_for_status = MagicMock()

        # Page 3 without next link
        mock_response_page3 = MagicMock()
        mock_response_page3.json.return_value = {
            "clients": [{"id": 5}],
            "per_page": 2,
            "total_pages": 3,
            "page": 3,
            "links": {},
        }
        mock_response_page3.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=[mock_response_page1, mock_response_page2, mock_response_page3])
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            items = []
            async for item in client.get_paginated("/v2/clients", account_id=12345):
                items.append(item)

        assert len(items) == 5
        assert items[0]["id"] == 1
        assert items[4]["id"] == 5


@pytest.mark.asyncio
async def test_pagination_single_page() -> None:
    """Test pagination with single page."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "clients": [{"id": 1}, {"id": 2}],
            "per_page": 100,
            "total_pages": 1,
            "page": 1,
            "links": {},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            items = []
            async for item in client.get_paginated("/v2/clients", account_id=12345):
                items.append(item)

        assert len(items) == 2
        assert items[0]["id"] == 1
        assert items[1]["id"] == 2


@pytest.mark.asyncio
async def test_pagination_empty_response() -> None:
    """Test pagination with empty response."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "clients": [],
            "per_page": 100,
            "total_pages": 1,
            "page": 1,
            "links": {},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            items = []
            async for item in client.get_paginated("/v2/clients", account_id=12345):
                items.append(item)

        assert len(items) == 0

