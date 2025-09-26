from abc import ABC, abstractmethod

from pydantic import BaseModel


class ToolResult:
    """工具执行结果类"""

    def __init__(self, name: str, content: str, success: bool):
        self.name = name
        self.content = content
        self.success = success


class BaseTool(ABC, BaseModel):
    """工具类基类，定义统一接口"""

    name: str
    description: str
    parameters: dict

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具的具体操作，子类需要实现这个方法"""
        pass
