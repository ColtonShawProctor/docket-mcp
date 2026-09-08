class DocketMcpError(Exception):
    """Base class for every error this package raises on purpose."""


class ApiKeyMissingError(DocketMcpError):
    """Raised when no Regulations.gov API key is configured."""


class MalformedIdError(DocketMcpError):
    """Raised for IDs that cannot possibly be valid, before any request is sent."""


class NotFoundError(DocketMcpError):
    """Raised when the API reports that the requested resource does not exist."""


class UpstreamError(DocketMcpError):
    """Raised when the API answers with a status this client cannot handle."""

    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        message = f"Regulations.gov returned HTTP {status_code}"
        if detail:
            message += f": {detail}"
        super().__init__(message)
