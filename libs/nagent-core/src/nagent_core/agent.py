import logging
import tenacity
from .utils import is_retryable_error, robust_json_parse

logger = logging.getLogger(__name__)

class SimpleAgent:
    def __init__(self, client, system_prompt: str = None, model_name: str = "gemini-2.0-flash"):
        self.client = client
        self.model_name = model_name
        self.system_prompt = (
            system_prompt
            or """回答如下问题：
problem：{user_input}
answer：

请使用中文回答 (Please respond in Chinese).


输出格式：

```json
{{
  "answer": 答案
}}
```
        """
        )

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception(is_retryable_error),
        before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
        reraise=True,
    )
    def query(self, user_input: str):
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                config={"response_mime_type": "application/json"},
                contents=self.system_prompt.format(user_input=user_input),
            )

            result = robust_json_parse(response.text)
            return {"answer": result.get("answer", "No answer found in response.")}
        except Exception as e:
            if is_retryable_error(e):
                raise e
            logger.error(f"Non-retryable error in query: {e}")
            return {"answer": f"Error: {str(e)}"}

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception(is_retryable_error),
        reraise=True,
    )
    async def aquery(self, user_input: str):
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                config={"response_mime_type": "application/json"},
                contents=self.system_prompt.format(user_input=user_input),
            )

            result = robust_json_parse(response.text)
            return {"answer": result.get("answer", "No answer found in response.")}
        except Exception as e:
            if is_retryable_error(e):
                raise e
            logger.error(f"Non-retryable error in aquery: {e}")
            return {"answer": f"Error during aquery: {str(e)}"}
