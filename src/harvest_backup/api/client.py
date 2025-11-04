"""API client for Harvest API v2 with rate limiting and pagination."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from time import time

import httpx

from harvest_backup.api.exceptions import HarvestAuthenticationError

# Constants
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 15.0
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0
MAX_PAGINATION_PER_PAGE = 2000
ERROR_MESSAGE_MAX_LENGTH = 200

# Define VERBOSE log level (between DEBUG and INFO)
VERBOSE = 15
logging.addLevelName(VERBOSE, "VERBOSE")


def verbose(self, message, *args, **kwargs):
    """Log a message with severity 'VERBOSE'."""
    if self.isEnabledFor(VERBOSE):
        self._log(VERBOSE, message, args, **kwargs)


logging.Logger.verbose = verbose

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(
        self,
        max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS,
        time_window: float = DEFAULT_RATE_LIMIT_WINDOW,
    ) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times: list[float] = []
        self.lock = asyncio.Lock()

    async def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        async with self.lock:
            now = time()
            # Remove requests older than time_window
            self.request_times = [t for t in self.request_times if now - t < self.time_window]

            if len(self.request_times) >= self.max_requests:
                # Calculate wait time until oldest request expires
                oldest_request = min(self.request_times)
                wait_time = self.time_window - (now - oldest_request) + 0.1  # Small buffer
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                # Clean up again after waiting
                now = time()
                self.request_times = [t for t in self.request_times if now - t < self.time_window]

            # Record this request
            self.request_times.append(time())


class HarvestAPIClient:
    """Client for Harvest API v2."""

    BASE_URL = "https://api.harvestapp.com"
    ACCOUNTS_URL = "https://id.getharvest.com/api/v2/accounts"

    def __init__(
        self,
        access_token: str,
        user_agent: str = "HarvestBackupTool/0.1.0",
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        """Initialize Harvest API client.

        Args:
            access_token: Personal Access Token
            user_agent: User-Agent header value
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.access_token = access_token
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limiter = RateLimiter()

        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": user_agent,
            },
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    def _extract_error_from_dict(self, data: dict, keys: list[str]) -> str | None:
        """Extract error message from dictionary using given keys.

        Args:
            data: Dictionary to search
            keys: List of keys to try

        Returns:
            Error message string or None if not found
        """
        for key in keys:
            if key not in data:
                continue
            value = data[key]
            if isinstance(value, str):
                return value
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, dict):
                # Try nested keys
                nested_result = self._extract_error_from_dict(value, ["message", "error", "detail"])
                if nested_result:
                    return nested_result
        return None

    def _extract_error_message(self, response: httpx.Response) -> str:
        """Extract error message from API response.

        Args:
            response: HTTP response

        Returns:
            Error message string
        """
        try:
            data = response.json()
            if isinstance(data, dict):
                error_msg = self._extract_error_from_dict(
                    data, ["message", "error", "error_description", "detail"]
                )
                if error_msg:
                    return error_msg
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback to status text or response text
        if response.text:
            return response.text[:ERROR_MESSAGE_MAX_LENGTH]
        return response.reason_phrase or f"HTTP {response.status_code}"

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
        per_page = params.get("per_page", MAX_PAGINATION_PER_PAGE)
        page_info = f" page={page}"
        if per_page != MAX_PAGINATION_PER_PAGE:
            page_info += f" per_page={per_page}"
        return page_info

    async def _handle_http_error(
        self, error: httpx.HTTPStatusError, attempt: int, delay: float
    ) -> tuple[bool, float]:
        """Handle HTTP status errors and determine if retry is needed.

        Args:
            error: HTTP status error
            attempt: Current attempt number
            delay: Current delay for retry

        Returns:
            Tuple of (should_retry, new_delay)
        """
        status_code = error.response.status_code

        if status_code == 429:
            # Rate limit error - wait for Retry-After header or use delay
            retry_after = error.response.headers.get("Retry-After")
            wait_time = float(retry_after) if retry_after else delay
            logger.warning(f"Rate limited (429), waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            return True, delay * 2  # Exponential backoff

        if status_code in (401, 403):
            # Authentication errors - don't retry
            error_message = self._extract_error_message(error.response)
            raise HarvestAuthenticationError(
                error.response.status_code,
                error_message,
                response_body=error.response.text,
            )

        if status_code >= 500:
            # Server errors - retry
            if attempt < self.max_retries:
                logger.warning(f"Server error {status_code}, retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
                return True, delay * 2
            raise

        # Other client errors - don't retry
        raise

    async def _handle_network_error(
        self, error: httpx.NetworkError | httpx.TimeoutException, attempt: int, delay: float
    ) -> tuple[bool, float]:
        """Handle network errors and determine if retry is needed.

        Args:
            error: Network or timeout error
            attempt: Current attempt number
            delay: Current delay for retry

        Returns:
            Tuple of (should_retry, new_delay)
        """
        if attempt < self.max_retries:
            logger.warning(f"Network error, retrying in {delay:.2f}s: {error}")
            await asyncio.sleep(delay)
            return True, delay * 2
        raise

    async def _request(
        self,
        method: str,
        url: str,
        account_id: int | None = None,
        params: dict | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request with rate limiting and retries.

        Args:
            method: HTTP method
            url: Request URL
            account_id: Harvest account ID (for Harvest API endpoints)
            params: Query parameters
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        await self.rate_limiter.wait_if_needed()

        headers = kwargs.pop("headers", {})
        if account_id is not None:
            headers["Harvest-Account-Id"] = str(account_id)

        request_kwargs = {
            "method": method,
            "url": url,
            "params": params,
            "headers": headers,
            **kwargs,
        }

        delay = self.retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(**request_kwargs)
                response.raise_for_status()

                page_info = self._format_page_info(params)
                logger.verbose(f"{method} {url}{page_info} OK")

                return response
            except httpx.HTTPStatusError as e:
                last_exception = e
                should_retry, delay = await self._handle_http_error(e, attempt, delay)
                if should_retry:
                    continue
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_exception = e
                should_retry, delay = await self._handle_network_error(e, attempt, delay)
                if should_retry:
                    continue

        if last_exception:
            raise last_exception
        raise httpx.HTTPError("Request failed after retries")

    def _extract_items_from_response(self, data: dict) -> list | dict:
        """Extract items list from API response.

        Harvest API returns items either directly as a list, or wrapped in a key.
        This method detects the structure dynamically.

        Args:
            data: Response data dictionary

        Returns:
            Items list or single item dict
        """
        # If data itself is a list, return it
        if isinstance(data, list):
            return data

        # Look for list values in the dictionary (skip metadata fields)
        metadata_fields = {"page", "per_page", "total_pages", "total_entries", "links", "next_page"}
        for key, value in data.items():
            if key not in metadata_fields and isinstance(value, list):
                return value

        # If no list found, return the whole dict (might be a single item)
        return data

    def _has_next_page(self, data: dict) -> bool:
        """Check if response has a next page.

        Args:
            data: Response data dictionary

        Returns:
            True if there's a next page
        """
        if data.get("next_page") is not None:
            return True
        links = data.get("links", {})
        return isinstance(links, dict) and links.get("next") is not None

    async def get_paginated(
        self,
        endpoint: str,
        account_id: int,
        params: dict | None = None,
    ) -> AsyncIterator[dict]:
        """Get all pages of a paginated endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/v2/clients")
            account_id: Harvest account ID
            params: Query parameters (page and per_page will be overridden)

        Yields:
            Individual items from all pages
        """
        if params is None:
            params = {}

        page = 1

        while True:
            request_params = {**params, "page": page, "per_page": MAX_PAGINATION_PER_PAGE}
            response = await self._request(
                "GET", f"{self.BASE_URL}{endpoint}", account_id, request_params
            )
            data = response.json()

            items = self._extract_items_from_response(data)

            if isinstance(items, list):
                for item in items:
                    yield item
            else:
                # Single item response
                yield items

            if self._has_next_page(data):
                page += 1
            else:
                break

    async def get(
        self, endpoint: str, account_id: int | None = None, params: dict | None = None
    ) -> dict:
        """GET request to API endpoint.

        Args:
            endpoint: API endpoint path
            account_id: Harvest account ID (None for accounts API)
            params: Query parameters

        Returns:
            JSON response
        """
        if account_id is None:
            # Use accounts API
            url = self.ACCOUNTS_URL
        else:
            url = f"{self.BASE_URL}{endpoint}"

        response = await self._request("GET", url, account_id, params)
        return response.json()

    async def get_binary(
        self, endpoint: str, account_id: int, params: dict | None = None
    ) -> tuple[bytes, str | None]:
        """GET request for binary data (e.g., PDFs).

        Args:
            endpoint: API endpoint path
            account_id: Harvest account ID
            params: Query parameters

        Returns:
            Tuple of (binary response content, content_type)
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = await self._request("GET", url, account_id, params)
        content_type = response.headers.get("content-type", "").lower()
        return response.content, content_type

    async def get_company(self, account_id: int) -> dict:
        """Get company data for an account.

        Args:
            account_id: Harvest account ID

        Returns:
            Company data dictionary (includes full_domain and base_uri)
        """
        return await self.get("/v2/company", account_id)

    async def download_client_link(self, url: str) -> bytes:
        """Download a client link (public URL, no authentication required).

        Args:
            url: Full URL to download

        Returns:
            Binary content

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        # Client links are public and don't require authentication
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
            follow_redirects=True,
        ) as no_auth_client:
            response = await no_auth_client.get(url)
            response.raise_for_status()

            # Log successful request at VERBOSE level
            logger.verbose(f"GET {url} OK")

            return response.content
