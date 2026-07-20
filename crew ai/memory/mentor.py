"""
Adaptive AI Mentor — personalizes onboarding using digital memory + RAG context.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class AdaptiveMentor:
    """Generates mentor insights and personalized roadmaps from memory + RAG."""

    def generate_insights(
        self,
        employee: Dict[str, Any],
        memory: Dict[str, Any],
        rag_context: str = "",
        progress: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        weak = memory.get("weak_topics") or []
        strong = memory.get("strong_topics") or []
        style = memory.get("preferred_learning_style") or "mixed"
        risk = memory.get("risk_level") or "low"

        next_modules: List[str] = []
        if weak:
            next_modules.extend([f"Deep dive: {t}" for t in weak[:3]])
        else:
            next_modules.append(f"Advanced {employee.get('department', 'role')} excellence track")

        if style == "visual_video":
            modality = "Prioritize short training videos and visual SOPs."
        elif style == "quiz_practice":
            modality = "Use spaced retrieval quizzes and scenario drills."
        else:
            modality = "Blend reading, video, and practice quizzes."

        predictions = []
        if risk == "high":
            predictions.append("Likely to need manager check-in within 7 days.")
        if memory.get("confidence_score", 0.5) < 0.6:
            predictions.append("May struggle with policy/compliance assessments.")
        if not predictions:
            predictions.append("On track to complete onboarding on schedule.")

        recommendations = list(memory.get("recommended_next_modules") or [])
        if rag_context and "No relevant" not in rag_context:
            recommendations.append("Review retrieved handbook/policy excerpts before next quiz.")

        return {
            "mentor_summary": (
                f"As your adaptive mentor, I've reviewed {employee.get('name', 'your')} learning profile. "
                f"Strengths: {', '.join(strong[:3]) or 'building foundations'}. "
                f"Focus areas: {', '.join(weak[:3]) or 'continue steady progress'}. "
                f"{modality}"
            ),
            "learning_style": style,
            "risk_level": risk,
            "confidence_score": memory.get("confidence_score", 0.5),
            "engagement_score": memory.get("engagement_score", 0.0),
            "skip_topics": list(strong)[:5],
            "reinforce_topics": list(weak)[:5],
            "next_modules": next_modules,
            "predictions": predictions,
            "recommendations": recommendations[:8],
            "personalized_roadmap": memory.get("personalized_roadmap") or [],
            "rag_grounded": "No relevant" not in (rag_context or ""),
        }
