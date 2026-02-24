from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class AIOpsException(Exception):
    """Base exception for AIOps Service"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ElasticsearchConnectionError(AIOpsException):
    """Raised when Elasticsearch is unreachable or queries fail"""
    def __init__(self, message: str = "Elasticsearch connection failed"):
        super().__init__(message, status_code=503)

class LLMAnalysisError(AIOpsException):
    """Raised when LLM Analysis fails or times out"""
    def __init__(self, message: str = "LLM analysis failed"):
        super().__init__(message, status_code=502)

class DiscordWebhookError(AIOpsException):
    """Raised when sending a webhook to Discord fails permanently"""
    def __init__(self, message: str = "Discord notification failed"):
        super().__init__(message, status_code=502)

# Global FastAPI exception handler
async def aiops_exception_handler(request: Request, exc: AIOpsException):
    logger.error(f"Global Error Handler caught {exc.__class__.__name__}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )
