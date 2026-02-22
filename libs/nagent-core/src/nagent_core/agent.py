import logging
import tenacity
import re
from typing import List, Dict, Any, Optional
from .utils import is_retryable_error, robust_json_parse
from .tool import BaseTool
from .prompt_utils import REACT_PROMPT_TEMPLATE, format_tools_description

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

class ReActAgent:
    def __init__(
        self,
        client,
        tools: List[BaseTool],
        model_name: str = "gemini-2.0-flash",
        max_iterations: int = 5,
    ):
        self.client = client
        self.tools = {tool.name: tool for tool in tools}
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.system_prompt = REACT_PROMPT_TEMPLATE.format(
            tools_description=format_tools_description(tools),
            user_input="{user_input}"
        )

    def _parse_action(self, text: str) -> Optional[tuple[str, str]]:
        """
        解析 Action: tool_name(args) 格式
        """
        match = re.search(r"Action:\s*(\w+)\((.*)\)", text)
        if match:
            return match.group(1), match.group(2)
        return None

    def query(self, user_input: str):
        prompt = self.system_prompt.format(user_input=user_input)
        full_history = prompt

        for i in range(self.max_iterations):
            logger.info(f"Iteration {i+1}/{self.max_iterations}")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_history,
            )

            generated_text = response.text
            logger.debug(f"LLM Output:\n{generated_text}")
            full_history += generated_text

            # 检查是否有最终答案
            if "Final Answer:" in generated_text:
                answer = generated_text.split("Final Answer:")[-1].strip()
                return {"answer": answer}

            # 解析动作
            action_info = self._parse_action(generated_text)
            if action_info:
                tool_name, tool_args = action_info
                if tool_name in self.tools:
                    logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                    try:
                        # 简单处理参数，这里假设参数是字符串
                        observation = self.tools[tool_name].run(tool_args)
                    except Exception as e:
                        observation = f"Error executing tool: {e}"
                else:
                    observation = f"Unknown tool: {tool_name}"

                observation_str = f"\nObservation: {observation}\n"
                logger.debug(f"Tool Output: {observation_str}")
                full_history += observation_str
            else:
                # 如果既没有 Final Answer 也没有 Action，可能模型迷茫了
                logger.warning("LLM output did not contain Action or Final Answer")
                if i == self.max_iterations - 1:
                    return {"answer": "I'm sorry, I couldn't find an answer within the iteration limit."}
                full_history += "\nThought: I need to clarify my next step or provide a Final Answer.\n"

        return {"answer": "Reached max iterations without a final answer."}
