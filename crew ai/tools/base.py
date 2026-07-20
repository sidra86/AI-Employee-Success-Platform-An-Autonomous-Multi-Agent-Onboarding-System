"""Base tool abstractions for agent tool-calling."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool"

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        raise NotImplementedError

    def as_dict(self) -> Dict[str, str]:
        return {"name": self.name, "description": self.description}


class ToolRegistry:
    """Registry + executor with optional observability hooks."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [t.as_dict() for t in self._tools.values()]

    def execute(self, name: str, tracer=None, **kwargs: Any) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"Tool not found: {name}"
        started = time.time()
        if tracer is not None:
            with tracer.span(name, kind="tool", args=list(kwargs.keys())) as span:
                try:
                    result = tool.run(**kwargs)
                    span.metadata["result_preview"] = str(result)[:240]
                    return result
                except Exception as exc:
                    span.finish(status="error", error=str(exc))
                    raise
        try:
            return tool.run(**kwargs)
        except Exception as exc:
            return f"Tool error ({name}): {exc}"
        finally:
            _ = started


_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        from tools.employee_tools import EmployeeLookupTool, ProgressRetrievalTool
        from tools.knowledge_tools import DocumentRetrievalTool, KnowledgeSearchTool, PolicyAccessTool
        from tools.report_tools import ReportGenerationTool
        from tools.notification_tools import MockEmailTool

        _registry = ToolRegistry()
        for tool in (
            EmployeeLookupTool(),
            ProgressRetrievalTool(),
            DocumentRetrievalTool(),
            KnowledgeSearchTool(),
            PolicyAccessTool(),
            ReportGenerationTool(),
            MockEmailTool(),
        ):
            _registry.register(tool)
    return _registry
