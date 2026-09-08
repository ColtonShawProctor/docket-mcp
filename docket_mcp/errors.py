class DocketMcpError(Exception):
    """Base class for every error this package raises on purpose."""


class ApiKeyMissingError(DocketMcpError):
    """Raised when no Regulations.gov API key is configured."""
