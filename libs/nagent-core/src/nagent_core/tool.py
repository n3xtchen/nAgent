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
