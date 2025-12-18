"""Custom exceptions for the application."""


class TelegramScraperError(Exception):
    """Base exception for Telegram Scraper."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(TelegramScraperError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(TelegramScraperError):
    """Raised when user is not authorized."""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message)


class NotFoundError(TelegramScraperError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str = "Resource", identifier: str | None = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message)


class ValidationError(TelegramScraperError):
    """Raised when validation fails."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message)


class TelegramSessionError(TelegramScraperError):
    """Raised when Telegram session operations fail."""

    def __init__(self, message: str = "Telegram session error"):
        super().__init__(message)


class ScrapingError(TelegramScraperError):
    """Raised when scraping operations fail."""

    def __init__(self, message: str = "Scraping failed"):
        super().__init__(message)
