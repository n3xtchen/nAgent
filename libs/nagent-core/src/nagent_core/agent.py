import logging
import re
from typing import List, Dict, Any, Optional
from .utils import is_retryable_error, robust_json_parse
from .tool import BaseTool
from .prompt_utils import REACT_PROMPT_TEMPLATE, format_tools_description
from .llm import LLMClient

logger = logging.getLogger(__name__)

class SimpleAgent:
    def __init__(self, client, system_prompt: str = None, model_name: str = "gemini-2.0-flash"):
        self.client = client
        self.llm_client = LLMClient(client)
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

    def query(self, user_input: str):
        try:
            response = self.llm_client.generate_content(
                model=self.model_name,
                config={"response_mime_type": "application/json"},
                contents=self.system_prompt.format(user_input=user_input),
            )

            result = robust_json_parse(response.text)
            return {"answer": result.get("answer", "No answer found in response.")}
        except Exception as e:
            logger.error(f"Error in query: {e}")
            return {"answer": f"Error: {str(e)}"}

    async def aquery(self, user_input: str):
        try:
            response = await self.llm_client.agenerate_content(
                model=self.model_name,
                config={"response_mime_type": "application/json"},
                contents=self.system_prompt.format(user_input=user_input),
            )

            result = robust_json_parse(response.text)
            return {"answer": result.get("answer", "No answer found in response.")}
        except Exception as e:
            logger.error(f"Error in aquery: {e}")
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
        self.llm_client = LLMClient(client)
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
        trace = []

        for i in range(self.max_iterations):
            logger.info(f"Iteration {i+1}/{self.max_iterations}")

            response = self.llm_client.generate_content(
                model=self.model_name,
                contents=full_history,
            )

            generated_text = response.text
            logger.debug(f"LLM Output:\n{generated_text}")
            full_history += generated_text

            # 提取 Thought
            thought_match = re.search(r"Thought:\s*(.*?)(?=\n(Action|Final Answer)|$)", generated_text, re.DOTALL)
            thought = thought_match.group(1).strip() if thought_match else ""

            # 检查是否有最终答案
            if "Final Answer:" in generated_text:
                answer = generated_text.split("Final Answer:")[-1].strip()
                trace.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": None,
                    "observation": None,
                    "final_answer": answer
                })
                return {"answer": answer, "trace": trace}

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

                observation_str_for_trace = str(observation)
                if tool_name == "retrieve":
                    observation_str_for_trace = re.sub(r"内容:.*?(?=\n\n---\n\n|\Z)", "内容: [Content Omitted]", observation_str_for_trace, flags=re.DOTALL)

                trace.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": (tool_name, tool_args),
                    "observation": observation_str_for_trace
                })

                observation_str = f"\nObservation: {observation}\n"
                logger.debug(f"Tool Output: \nObservation: {observation_str_for_trace}\n")
                full_history += observation_str
            else:
                # 如果既没有 Final Answer 也没有 Action，可能模型迷茫了
                logger.warning("LLM output did not contain Action or Final Answer")

                trace.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": None,
                    "observation": "LLM output did not contain Action or Final Answer"
                })

                if i == self.max_iterations - 1:
                    return {
                        "answer": "I'm sorry, I couldn't find an answer within the iteration limit.",
                        "trace": trace
                    }
                full_history += "\nThought: I need to clarify my next step or provide a Final Answer.\n"

        return {
            "answer": "Reached max iterations without a final answer.",
            "trace": trace
        }

    async def aquery(self, user_input: str):
        prompt = self.system_prompt.format(user_input=user_input)
        full_history = prompt
        trace = []

        for i in range(self.max_iterations):
            logger.info(f"Async Iteration {i+1}/{self.max_iterations}")

            response = await self.llm_client.agenerate_content(
                model=self.model_name,
                contents=full_history,
            )

            generated_text = response.text
            logger.debug(f"LLM Output:\n{generated_text}")
            full_history += generated_text

            # 提取 Thought
            thought_match = re.search(r"Thought:\s*(.*?)(?=\n(Action|Final Answer)|$)", generated_text, re.DOTALL)
            thought = thought_match.group(1).strip() if thought_match else ""

            # 检查是否有最终答案
            if "Final Answer:" in generated_text:
                answer = generated_text.split("Final Answer:")[-1].strip()
                trace.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": None,
                    "observation": None,
                    "final_answer": answer
                })
                return {"answer": answer, "trace": trace}

            # 解析动作
            action_info = self._parse_action(generated_text)
            if action_info:
                tool_name, tool_args = action_info
                if tool_name in self.tools:
                    logger.info(f"Calling tool (async): {tool_name} with args: {tool_args}")
                    try:
                        observation = await self.tools[tool_name].arun(tool_args)
                    except Exception as e:
                        observation = f"Error executing tool: {e}"
                else:
                    observation = f"Unknown tool: {tool_name}"

                observation_str_for_trace = str(observation)
                if tool_name == "retrieve":
                    observation_str_for_trace = re.sub(r"内容:.*?(?=\n\n---\n\n|\Z)", "内容: [Content Omitted]", observation_str_for_trace, flags=re.DOTALL)

                trace.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": (tool_name, tool_args),
                    "observation": observation_str_for_trace
                })

                observation_str = f"\nObservation: {observation}\n"
                logger.debug(f"Tool Output: \nObservation: {observation_str_for_trace}\n")
                full_history += observation_str
            else:
                logger.warning("LLM output did not contain Action or Final Answer")

                trace.append({
                    "step": i + 1,
                    "thought": thought,
                    "action": None,
                    "observation": "LLM output did not contain Action or Final Answer"
                })

                if i == self.max_iterations - 1:
                    return {
                        "answer": "I'm sorry, I couldn't find an answer within the iteration limit.",
                        "trace": trace
                    }
                full_history += "\nThought: I need to clarify my next step or provide a Final Answer.\n"

        return {
            "answer": "Reached max iterations without a final answer.",
            "trace": trace
        }