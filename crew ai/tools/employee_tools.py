"""Employee and progress lookup tools."""

from __future__ import annotations

import json
from typing import Any, Optional

from tools.base import BaseTool


class EmployeeLookupTool(BaseTool):
    name = "employee_lookup"
    description = "Search employee records by id, email, or name"

    def run(self, employee_id: Optional[int] = None, email: Optional[str] = None, name: Optional[str] = None, **_: Any) -> str:
        from database.database import SessionLocal
        from database.models import Employee

        db = SessionLocal()
        try:
            q = db.query(Employee)
            if employee_id:
                emp = q.filter(Employee.id == int(employee_id)).first()
                employees = [emp] if emp else []
            elif email:
                employees = q.filter(Employee.email == email).all()
            elif name:
                employees = q.filter(Employee.name.ilike(f"%{name}%")).all()
            else:
                employees = q.limit(20).all()
            payload = [
                {
                    "id": e.id,
                    "name": e.name,
                    "email": e.email,
                    "department": e.department,
                    "position": e.position,
                    "onboarding_status": e.onboarding_status,
                }
                for e in employees
                if e
            ]
            return json.dumps({"employees": payload, "count": len(payload)})
        finally:
            db.close()


class ProgressRetrievalTool(BaseTool):
    name = "progress_retrieval"
    description = "Retrieve quiz scores, progress reports, and learning memory for an employee"

    def run(self, employee_id: int, **_: Any) -> str:
        from database.database import SessionLocal
        from database.models import QuizResult, ProgressReport
        from memory.service import get_memory_service

        db = SessionLocal()
        try:
            quizzes = (
                db.query(QuizResult)
                .filter(QuizResult.employee_id == int(employee_id))
                .order_by(QuizResult.completed_at.desc())
                .limit(20)
                .all()
            )
            reports = (
                db.query(ProgressReport)
                .filter(ProgressReport.employee_id == int(employee_id))
                .order_by(ProgressReport.generated_at.desc())
                .limit(5)
                .all()
            )
            memory = get_memory_service().as_dict(
                get_memory_service().get_or_create_profile(db, int(employee_id))
            )
            return json.dumps(
                {
                    "quiz_results": [
                        {
                            "score": q.score,
                            "total_questions": q.total_questions,
                            "correct_answers": q.correct_answers,
                            "completed_at": q.completed_at.isoformat() if q.completed_at else None,
                        }
                        for q in quizzes
                    ],
                    "progress_reports": [
                        {
                            "overall_progress": r.overall_progress,
                            "modules_completed": r.modules_completed,
                            "total_modules": r.total_modules,
                            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                        }
                        for r in reports
                    ],
                    "memory": memory,
                }
            )
        finally:
            db.close()
