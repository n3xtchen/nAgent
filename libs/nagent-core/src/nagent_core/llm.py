import logging
import tenacity
from .utils import is_retryable_error

logger = logging.getLogger(__name__)

class LLMClient:
    """
    A unified LLM client wrapper that provides a retry mechanism for all LLM API requests.
    This enhances the system's robustness against network fluctuations, rate limits (429),
    and temporary service unavailability (503).
    """
    def __init__(self, client):
        """
        Initialize the LLMClient with the underlying google.genai Client.

        Args:
            client: The google.genai Client instance.
        """
        self.client = client

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception(is_retryable_error),
        before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
        reraise=True,
    )
    def generate_content(self, model: str, contents: str, **kwargs):
        """
        Synchronously generate content with retry mechanism.
        """
        return self.client.models.generate_content(
            model=model,
            contents=contents,
            **kwargs
        )

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception(is_retryable_error),
        before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
        reraise=True,
    )
    async def agenerate_content(self, model: str, contents: str, **kwargs):
        """
        Asynchronously generate content with retry mechanism.
        """
        return await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            **kwargs
        )
