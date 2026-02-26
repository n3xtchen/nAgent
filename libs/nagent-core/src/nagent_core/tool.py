from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseTool(ABC):
    """
    Agent 工具的基类。
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        同步运行工具。
        """
        pass

    async def arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        异步运行工具。默认调用同步版本。
        """
        return self.run(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)

class CalculatorTool(BaseTool):
    """
    A simple calculator tool that can evaluate mathematical expressions.
    """
    def __init__(self, name: str = "calculator", description: str = "执行数学计算。输入应该是一个数学表达式，例如 '2 + 2' 或 '10 / 2 * 5'"):
        super().__init__(name, description)

    def run(self, expression: str) -> str:
        """
        Evaluate the mathematical expression.
        """
        try:
            # Basic safety: only allow numbers and basic operators
            import re
            # Remove whitespace
            expression = expression.replace(" ", "")
            if not re.match(r"^[0-9+\-*/().]+$", expression):
                return "错误: 表达式包含非法字符。仅允许数字和运算符 (+, -, *, /, (, ), .)。"

            # Using eval with limited globals and locals for some safety
            result = eval(expression, {"__builtins__": None}, {})
            return str(result)
        except Exception as e:
            return f"错误: 无法计算表达式。{str(e)}"

class PythonInterpreterTool(BaseTool):
    """
    A tool that can execute Python code and return the output.
    """
    def __init__(self, name: str = "python_interpreter", description: str = "执行 Python 代码。输入应该是合法的 Python 代码字符串。代码应该使用 print() 输出结果。"):
        super().__init__(name, description)

    def run(self, code: str) -> str:
        """
        Execute the Python code and capture the output.
        """
        import sys
        import io
        import contextlib

        # Remove potential markdown code blocks
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]

        code = code.strip()

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                # Use a shared dictionary for globals and locals to allow multiline code and side effects
                exec_globals = {}
                exec(code, exec_globals)
                result = output.getvalue()
                return result if result else "代码执行成功，但没有输出。"
            except Exception as e:
                return f"执行出错: {str(e)}"

class WebSearchTool(BaseTool):
    """
    A mock web search tool.
    """
    def __init__(self, name: str = "web_search", description: str = "在互联网上搜索信息。"):
        super().__init__(name, description)

    def run(self, query: str) -> str:
        """
        Mock implementation of web search.
        """
        return f"针对 '{query}' 的搜索结果 (模拟):\n1. 这是关于 '{query}' 的第一个相关网页内容摘要。\n2. 这是关于 '{query}' 的第二个相关网页内容摘要。\n注：目前 WebSearchTool 处于模拟模式，如需真实搜索请集成搜索引擎 API (如 Google Custom Search 或 Serper)。"
