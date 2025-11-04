"""Tests for authentication error handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from harvest_backup.api.client import HarvestAPIClient
from harvest_backup.api.exceptions import HarvestAuthenticationError


@pytest.mark.asyncio
async def test_authentication_error_extracts_message() -> None:
    """Test that authentication errors extract message from response body."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Mock 401 response with error message in body
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "message": "Invalid authentication credentials",
            "error": "unauthorized",
        }
        mock_response.text = '{"message":"Invalid authentication credentials","error":"unauthorized"}'
        mock_response.reason_phrase = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            with pytest.raises(HarvestAuthenticationError) as exc_info:
                await client.get("/v2/company", account_id=12345)

        # Verify error message was extracted
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(exc_info.value)
        assert exc_info.value.response_body is not None
        assert "unauthorized" in exc_info.value.response_body


@pytest.mark.asyncio
async def test_authentication_error_no_retry() -> None:
    """Test that authentication errors don't retry."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Unauthorized"}
        mock_response.text = '{"message":"Unauthorized"}'
        mock_response.reason_phrase = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token", max_retries=3) as client:
            with pytest.raises(HarvestAuthenticationError):
                await client.get("/v2/company", account_id=12345)

        # Should only be called once (no retries)
        assert mock_client.request.call_count == 1


@pytest.mark.asyncio
async def test_authentication_error_fallback_message() -> None:
    """Test that authentication errors fall back to status text if no message."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Mock 401 response with no error message in body
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Plain text error"
        mock_response.reason_phrase = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        async with HarvestAPIClient("test_token") as client:
            with pytest.raises(HarvestAuthenticationError) as exc_info:
                await client.get("/v2/company", account_id=12345)

        # Should use response text as fallback
        assert exc_info.value.status_code == 401
        assert "Plain text error" in str(exc_info.value) or "Unauthorized" in str(exc_info.value)

