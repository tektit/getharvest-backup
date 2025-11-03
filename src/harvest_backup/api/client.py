"""API client for Harvest API v2 with rate limiting and pagination."""

import asyncio
import logging
from collections.abc import AsyncIterator
from time import time

import httpx

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests (100 requests per 15 seconds)."""

    def __init__(self, max_requests: int = 100, time_window: float = 15.0) -> None:
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
        max_retries: int = 3,
        retry_delay: float = 1.0,
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
            timeout=httpx.Timeout(30.0),
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
        # Wait for rate limit
        await self.rate_limiter.wait_if_needed()

        # Prepare headers
        headers = kwargs.pop("headers", {})
        if account_id is not None:
            headers["Harvest-Account-Id"] = str(account_id)

        # Prepare request
        request_kwargs = {
            "method": method,
            "url": url,
            "params": params,
            "headers": headers,
            **kwargs,
        }

        # Retry logic with exponential backoff
        delay = self.retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(**request_kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code == 429:
                    # Rate limit error - wait for Retry-After header or use delay
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        wait_time = float(retry_after)
                    else:
                        wait_time = delay
                    logger.warning(f"Rate limited (429), waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                    delay *= 2  # Exponential backoff
                    continue
                elif e.response.status_code in (401, 403):
                    # Authentication errors - don't retry
                    logger.error(f"Authentication error: {e.response.status_code}")
                    raise
                elif e.response.status_code >= 500:
                    # Server errors - retry
                    if attempt < self.max_retries:
                        logger.warning(f"Server error {e.response.status_code}, retrying in {delay:.2f}s")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    raise
                else:
                    # Other client errors - don't retry
                    raise
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Network error, retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise httpx.HTTPError("Request failed after retries")

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
        per_page = 2000  # Maximum per Harvest API (as per OpenAPI spec)

        while True:
            request_params = {**params, "page": page, "per_page": per_page}
            response = await self._request("GET", f"{self.BASE_URL}{endpoint}", account_id, request_params)
            data = response.json()

            # Extract items (Harvest API returns items directly or in a key)
            items = data
            if isinstance(data, dict):
                # Some endpoints wrap items in a key (e.g., "clients", "time_entries")
                # Try common keys, or use the whole dict if it's the item itself
                # Check all possible response keys from the API
                for key in [
                    "clients",
                    "contacts",
                    "time_entries",
                    "projects",
                    "tasks",
                    "users",
                    "expenses",
                    "invoices",
                    "estimates",
                    "estimate_item_categories",
                    "invoice_item_categories",
                    "expense_categories",
                    "roles",
                    "company",
                    "user_assignments",
                    "task_assignments",
                ]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break

            if isinstance(items, list):
                for item in items:
                    yield item
            else:
                # Single item response
                yield items

            # Check for next page
            # Harvest API provides both next_page (number) and links.next (URL)
            # Check both for compatibility
            next_page = data.get("next_page")
            links = data.get("links", {})
            links_next = isinstance(links, dict) and links.get("next")

            if next_page is not None or links_next:
                page += 1
            else:
                break

    async def get(self, endpoint: str, account_id: int | None = None, params: dict | None = None) -> dict:
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

    async def get_binary(self, endpoint: str, account_id: int, params: dict | None = None) -> bytes:
        """GET request for binary data (e.g., PDFs).

        Args:
            endpoint: API endpoint path
            account_id: Harvest account ID
            params: Query parameters

        Returns:
            Binary response content
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = await self._request("GET", url, account_id, params)
        return response.content

