"""
Persistent digital memory service for Adaptive AI Mentoring.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from database.models import EmployeeLearningProfile, QuizResult, ProgressReport


def _loads(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _dumps(value: Any) -> str:
    return json.dumps(value, default=str)


class MemoryService:
    """CRUD + update helpers for EmployeeLearningProfile."""

    def get_or_create_profile(self, db: Session, employee_id: int) -> EmployeeLearningProfile:
        profile = (
            db.query(EmployeeLearningProfile)
            .filter(EmployeeLearningProfile.employee_id == employee_id)
            .first()
        )
        if profile:
            return profile
        profile = EmployeeLearningProfile(employee_id=employee_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def as_dict(self, profile: EmployeeLearningProfile) -> Dict[str, Any]:
        return {
            "employee_id": profile.employee_id,
            "weak_topics": _loads(profile.weak_topics, []),
            "strong_topics": _loads(profile.strong_topics, []),
            "learning_speed": profile.learning_speed or "average",
            "completed_modules": _loads(profile.completed_modules, []),
            "previous_feedback": _loads(profile.previous_feedback, []),
            "engagement_score": profile.engagement_score or 0.0,
            "confidence_score": profile.confidence_score or 0.5,
            "preferred_learning_style": profile.preferred_learning_style or "mixed",
            "common_mistakes": _loads(profile.common_mistakes, []),
            "recommended_next_modules": _loads(profile.recommended_next_modules, []),
            "quiz_history": _loads(profile.quiz_history, []),
            "risk_level": profile.risk_level or "low",
            "personalized_roadmap": _loads(profile.personalized_roadmap, []),
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else None,
        }

    def update_from_onboarding_results(
        self,
        db: Session,
        employee_id: int,
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        profile = self.get_or_create_profile(db, employee_id)
        memory = self.as_dict(profile)

        quiz_history = memory["quiz_history"]
        weak = set(memory["weak_topics"])
        strong = set(memory["strong_topics"])
        completed = list(memory["completed_modules"])
        feedback_log = list(memory["previous_feedback"])
        mistakes = list(memory["common_mistakes"])

        for quiz in results.get("quizzes", []):
            topic = quiz.get("topic") or quiz.get("quiz_title") or "general"
            score = float(quiz.get("score", 70))
            # If score not present, estimate from mock structure
            if "score" not in quiz and quiz.get("questions"):
                score = 75.0
            entry = {
                "topic": topic,
                "score": score,
                "difficulty": quiz.get("difficulty", "medium"),
                "at": datetime.utcnow().isoformat(),
            }
            quiz_history.append(entry)
            completed.append(topic)
            if score < 70:
                weak.add(topic)
                strong.discard(topic)
                mistakes.append({"topic": topic, "issue": "Low quiz score", "score": score})
            else:
                strong.add(topic)
                weak.discard(topic)

        for video in results.get("video_analyses", []):
            eng = float(video.get("engagement_score", 7.5))
            memory["engagement_score"] = round(
                (memory["engagement_score"] * 0.6) + (eng / 10.0 * 0.4), 3
            ) if memory["engagement_score"] else round(eng / 10.0, 3)

        progress = results.get("progress_report") or {}
        overall = float(progress.get("overall_progress", 70))
        velocity = progress.get("learning_velocity", memory["learning_speed"])
        memory["learning_speed"] = velocity
        memory["confidence_score"] = round(min(1.0, overall / 100.0), 3)

        if results.get("feedback"):
            feedback_log.append(
                {
                    "at": datetime.utcnow().isoformat(),
                    "feedback": results["feedback"],
                }
            )

        # Risk heuristic
        if len(weak) >= 3 or memory["confidence_score"] < 0.55:
            risk = "high"
        elif len(weak) >= 1 or memory["confidence_score"] < 0.7:
            risk = "medium"
        else:
            risk = "low"

        # Recommendations from weak topics
        recommendations = [f"Reinforce: {t}" for t in list(weak)[:5]]
        if not recommendations:
            recommendations = ["Advance to role-specific deep-dive modules"]

        roadmap = []
        for t in list(weak)[:3]:
            roadmap.append({"module": t, "action": "remedial_quiz", "priority": "high"})
        for t in list(strong)[:2]:
            roadmap.append({"module": t, "action": "skip_or_accelerate", "priority": "low"})
        if results.get("mentor_insights", {}).get("next_modules"):
            for m in results["mentor_insights"]["next_modules"]:
                roadmap.append({"module": m, "action": "recommended", "priority": "medium"})

        profile.weak_topics = _dumps(list(weak))
        profile.strong_topics = _dumps(list(strong))
        profile.learning_speed = str(velocity)
        profile.completed_modules = _dumps(list(dict.fromkeys(completed)))
        profile.previous_feedback = _dumps(feedback_log[-20:])
        profile.engagement_score = memory["engagement_score"]
        profile.confidence_score = memory["confidence_score"]
        profile.common_mistakes = _dumps(mistakes[-30:])
        profile.recommended_next_modules = _dumps(recommendations)
        profile.quiz_history = _dumps(quiz_history[-50:])
        profile.risk_level = risk
        profile.personalized_roadmap = _dumps(roadmap)
        profile.last_updated = datetime.utcnow()

        # Learning style inference
        if memory["engagement_score"] >= 0.8:
            profile.preferred_learning_style = "visual_video"
        elif len(quiz_history) > len(results.get("video_analyses", [])):
            profile.preferred_learning_style = "quiz_practice"
        else:
            profile.preferred_learning_style = profile.preferred_learning_style or "mixed"

        db.commit()
        db.refresh(profile)
        return self.as_dict(profile)

    def personalize_modules(
        self,
        memory: Dict[str, Any],
        base_modules: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Skip mastered topics; boost difficulty / extras for weak areas."""
        strong = set(memory.get("strong_topics") or [])
        weak = set(memory.get("weak_topics") or [])
        personalized: List[Dict[str, Any]] = []

        for module in base_modules:
            topic = module.get("topic") or module.get("objectives") or ""
            # Skip quiz modules employee already masters
            if module.get("type") == "quiz" and any(s.lower() in topic.lower() for s in strong):
                continue
            adapted = dict(module)
            if module.get("type") == "quiz":
                if any(w.lower() in topic.lower() for w in weak):
                    adapted["difficulty"] = "hard"
                    adapted["num_questions"] = max(int(module.get("num_questions", 10)), 15)
                    adapted["remedial"] = True
                elif memory.get("confidence_score", 0.5) > 0.8:
                    adapted["difficulty"] = "hard"
                elif memory.get("confidence_score", 0.5) < 0.55:
                    adapted["difficulty"] = "easy"
            personalized.append(adapted)

        # Add remedial quizzes for weak topics not covered
        covered = " ".join(m.get("topic", "") for m in personalized).lower()
        for topic in list(weak)[:2]:
            if topic.lower() not in covered:
                personalized.insert(
                    0,
                    {
                        "type": "quiz",
                        "topic": f"Remedial: {topic}",
                        "difficulty": "medium",
                        "num_questions": 8,
                        "remedial": True,
                    },
                )
        return personalized or base_modules

    def manager_insights(self, db: Session) -> Dict[str, Any]:
        profiles = db.query(EmployeeLearningProfile).all()
        at_risk = []
        gaps: Dict[str, int] = {}
        for p in profiles:
            mem = self.as_dict(p)
            if mem["risk_level"] in ("high", "medium"):
                at_risk.append(
                    {
                        "employee_id": p.employee_id,
                        "risk_level": mem["risk_level"],
                        "weak_topics": mem["weak_topics"],
                        "confidence_score": mem["confidence_score"],
                        "recommendations": mem["recommended_next_modules"],
                    }
                )
            for topic in mem["weak_topics"]:
                gaps[topic] = gaps.get(topic, 0) + 1

        top_gaps = sorted(gaps.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            "profiles_tracked": len(profiles),
            "employees_needing_assistance": at_risk,
            "knowledge_gaps": [{"topic": t, "employees_affected": c} for t, c in top_gaps],
            "avg_confidence": round(
                sum((p.confidence_score or 0) for p in profiles) / len(profiles), 3
            )
            if profiles
            else 0,
            "avg_engagement": round(
                sum((p.engagement_score or 0) for p in profiles) / len(profiles), 3
            )
            if profiles
            else 0,
        }


_memory: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    global _memory
    if _memory is None:
        _memory = MemoryService()
    return _memory
