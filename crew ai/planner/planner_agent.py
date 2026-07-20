"""
Planner Agent — decides the next specialized agents to run for an employee.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class PlannerAgent:
    """
    Produces an ordered execution plan for the autonomous onboarding workflow.
    Does not execute agents itself — the orchestrator follows the plan.
    """

    DEFAULT_STEPS = [
        {"agent": "rag_retriever", "action": "retrieve_knowledge", "reason": "Ground plan in company documents"},
        {"agent": "planner", "action": "generate_plan", "reason": "Personalize module sequence"},
        {"agent": "quiz_generator", "action": "generate_quizzes", "reason": "Assess knowledge gaps"},
        {"agent": "video_analyzer", "action": "analyze_videos", "reason": "Evaluate training engagement"},
        {"agent": "progress_tracker", "action": "track_progress", "reason": "Compute learning metrics"},
        {"agent": "feedback_agent", "action": "generate_feedback", "reason": "Personalized coaching notes"},
        {"agent": "evaluator", "action": "evaluate_outputs", "reason": "Quality-gate quizzes and feedback"},
        {"agent": "mentor", "action": "mentor_insights", "reason": "Update adaptive mentor roadmap"},
        {"agent": "memory", "action": "persist_memory", "reason": "Save digital learning profile"},
        {"agent": "notifier", "action": "notify_stakeholders", "reason": "Mock email to employee/manager"},
    ]

    def create_plan(
        self,
        employee_data: Dict[str, Any],
        modules: List[Dict[str, Any]],
        memory: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        memory = memory or {}
        steps = [dict(s) for s in self.DEFAULT_STEPS]

        has_quiz = any(m.get("type") == "quiz" for m in modules)
        has_video = any(m.get("type") == "video" for m in modules)

        if not has_quiz:
            steps = [s for s in steps if s["agent"] != "quiz_generator"]
        if not has_video:
            steps = [s for s in steps if s["agent"] != "video_analyzer"]

        # High-risk employees get an extra remedial planning note
        if memory.get("risk_level") == "high":
            steps.insert(
                2,
                {
                    "agent": "mentor",
                    "action": "risk_intervention_plan",
                    "reason": "Employee flagged as high risk — prioritize remediation",
                },
            )

        # Strong performers can skip redundant video analysis emphasis
        if (memory.get("confidence_score") or 0) > 0.85 and has_quiz:
            for s in steps:
                if s["agent"] == "quiz_generator":
                    s["reason"] = "Accelerate with harder quizzes; employee already confident"

        return {
            "employee_id": employee_data.get("id"),
            "employee_name": employee_data.get("name"),
            "department": employee_data.get("department"),
            "module_count": len(modules),
            "memory_aware": bool(memory),
            "risk_level": memory.get("risk_level", "unknown"),
            "steps": steps,
            "rationale": (
                f"Planned {len(steps)} agent steps for {employee_data.get('name')} "
                f"in {employee_data.get('department')} based on digital memory and module mix."
            ),
        }
