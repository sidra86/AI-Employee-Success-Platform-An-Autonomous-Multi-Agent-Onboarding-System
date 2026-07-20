"""Agent tool-calling layer."""

from .base import BaseTool, ToolRegistry, get_tool_registry
from .employee_tools import EmployeeLookupTool, ProgressRetrievalTool
from .knowledge_tools import DocumentRetrievalTool, KnowledgeSearchTool, PolicyAccessTool
from .report_tools import ReportGenerationTool
from .notification_tools import MockEmailTool

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "get_tool_registry",
    "EmployeeLookupTool",
    "ProgressRetrievalTool",
    "DocumentRetrievalTool",
    "KnowledgeSearchTool",
    "PolicyAccessTool",
    "ReportGenerationTool",
    "MockEmailTool",
]
