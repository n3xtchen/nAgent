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
