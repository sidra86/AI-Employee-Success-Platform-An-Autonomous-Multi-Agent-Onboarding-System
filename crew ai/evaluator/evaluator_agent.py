"""
Evaluator Agent — reviews quizzes and feedback; triggers regeneration when quality is low.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class EvaluatorAgent:
    """Heuristic quality gate (LLM-ready) for generated onboarding artifacts."""

    MIN_QUIZ_SCORE = 0.6
    MIN_FEEDBACK_SCORE = 0.55
    MAX_REGENERATIONS = 2

    def evaluate_quiz(self, quiz: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        score = 1.0
        questions = quiz.get("questions") or []
        if not questions:
            issues.append("No questions present")
            score -= 0.5
        elif len(questions) < 3:
            issues.append("Too few questions")
            score -= 0.2
        for q in questions:
            if not q.get("question"):
                issues.append("Empty question text")
                score -= 0.1
            if q.get("type") == "multiple_choice" and len(q.get("options") or []) < 2:
                issues.append("Multiple choice missing options")
                score -= 0.1
            if not q.get("correct_answer") and q.get("type") != "short_answer":
                issues.append("Missing correct answer")
                score -= 0.1
            if not q.get("explanation"):
                score -= 0.05
        if not quiz.get("topic") and not quiz.get("quiz_title"):
            issues.append("Missing topic/title")
            score -= 0.1
        score = max(0.0, min(1.0, score))
        return {
            "artifact": "quiz",
            "quality_score": round(score, 3),
            "passed": score >= self.MIN_QUIZ_SCORE,
            "issues": issues,
        }

    def evaluate_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        score = 1.0
        if not isinstance(feedback, dict):
            return {
                "artifact": "feedback",
                "quality_score": 0.0,
                "passed": False,
                "issues": ["Feedback is not a dictionary"],
            }

        # Normalize raw LLM dumps into a usable structure
        if feedback.get("raw_result") and not feedback.get("positive_feedback"):
            feedback = {
                "positive_feedback": str(feedback.get("raw_result"))[:500],
                "overall_message": str(feedback.get("raw_result"))[:300],
                "next_steps": ["Continue onboarding modules"],
                "motivational_message": "Keep going — your mentor is adapting to your progress.",
                "improvement_areas": [],
            }

        if not feedback.get("positive_feedback") and not feedback.get("overall_message"):
            issues.append("Missing affirmative feedback")
            score -= 0.3
        if not feedback.get("improvement_areas") and not feedback.get("next_steps"):
            issues.append("Missing actionable guidance")
            score -= 0.25
        if not feedback.get("motivational_message"):
            score -= 0.05

        improvements = feedback.get("improvement_areas")
        if isinstance(improvements, list) and improvements:
            score += 0.05

        score = max(0.0, min(1.0, score))
        if score < self.MIN_FEEDBACK_SCORE and (
            feedback.get("positive_feedback") or feedback.get("next_steps")
        ):
            score = max(score, self.MIN_FEEDBACK_SCORE)
            issues.append("Soft-passed with available coaching content")

        return {
            "artifact": "feedback",
            "quality_score": round(score, 3),
            "passed": score >= self.MIN_FEEDBACK_SCORE,
            "issues": issues,
        }

    def ensure_quiz_quality(
        self,
        quiz: Dict[str, Any],
        regenerate_fn: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        evaluation = self.evaluate_quiz(quiz)
        attempts = 0
        history = [evaluation]
        current = quiz
        while not evaluation["passed"] and regenerate_fn and attempts < self.MAX_REGENERATIONS:
            attempts += 1
            current = dict(regenerate_fn())
            current["regenerated"] = True
            current["regeneration_attempt"] = attempts
            evaluation = self.evaluate_quiz(current)
            history.append(evaluation)
        return {
            "quiz": current,
            "evaluation": evaluation,
            "attempts": attempts,
            "history": history,
        }

    def ensure_feedback_quality(
        self,
        feedback: Dict[str, Any],
        regenerate_fn: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        evaluation = self.evaluate_feedback(feedback)
        attempts = 0
        history = [evaluation]
        current = feedback if isinstance(feedback, dict) else {}
        while not evaluation["passed"] and regenerate_fn and attempts < self.MAX_REGENERATIONS:
            attempts += 1
            current = dict(regenerate_fn())
            current["regenerated"] = True
            current["regeneration_attempt"] = attempts
            evaluation = self.evaluate_feedback(current)
            history.append(evaluation)

        if not evaluation["passed"]:
            current = {
                **(current if isinstance(current, dict) else {}),
                "positive_feedback": current.get("positive_feedback")
                or "Solid progress through the onboarding track.",
                "improvement_areas": current.get("improvement_areas")
                or [{"area": "Practice", "suggestion": "Revisit weak topics with remedial quizzes"}],
                "motivational_message": current.get("motivational_message")
                or "Your adaptive mentor will keep personalizing your path.",
                "next_steps": current.get("next_steps")
                or ["Review mentor roadmap", "Complete recommended modules"],
                "overall_message": current.get("overall_message")
                or "Keep building momentum — you are on track.",
                "evaluator_fallback": True,
            }
            evaluation = self.evaluate_feedback(current)
            history.append(evaluation)

        return {
            "feedback": current,
            "evaluation": evaluation,
            "attempts": attempts,
            "history": history,
        }
