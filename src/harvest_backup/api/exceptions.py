"""Custom exceptions for Harvest API."""


class HarvestAuthenticationError(Exception):
    """Exception raised for authentication errors (401, 403)."""

    def __init__(self, status_code: int, message: str, response_body: str | None = None) -> None:
        """Initialize authentication error.

        Args:
            status_code: HTTP status code (401 or 403)
            message: Error message
            response_body: Full response body for additional context
        """
        self.status_code = status_code
        self.response_body = response_body
        error_type = "Unauthorized" if status_code == 401 else "Forbidden"
        super().__init__(f"{error_type} ({status_code}): {message}")

