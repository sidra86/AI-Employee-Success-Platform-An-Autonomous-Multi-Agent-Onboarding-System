"""Report generation tool."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from tools.base import BaseTool


class ReportGenerationTool(BaseTool):
    name = "report_generation"
    description = "Generate a structured onboarding/manager report from employee metrics"

    def run(
        self,
        employee_id: Optional[int] = None,
        employee_name: str = "Employee",
        metrics: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> str:
        metrics = metrics or {}
        report = {
            "title": f"Onboarding Success Report — {employee_name}",
            "generated_at": datetime.utcnow().isoformat(),
            "employee_id": employee_id,
            "completion_percentage": metrics.get("overall_progress", 0),
            "strengths": metrics.get("strengths", []),
            "improvement_areas": metrics.get("improvement_areas", []),
            "risk_factors": metrics.get("risk_factors", []),
            "recommendations": metrics.get("recommendations", []),
            "summary": metrics.get(
                "summary",
                "Automated report generated from latest agent workflow outputs.",
            ),
        }
        return json.dumps(report, indent=2)
