"""
Autonomous onboarding orchestrator.

Preserves legacy OnboardingCrew APIs while adding:
Planner → RAG → specialized agents → Evaluator → Mentor → Memory → Notifications
with full observability tracing and tool-calling.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    from crewai import Crew, Process
except ImportError:
    from mock_crew import Crew, Process

from agents.quiz_generator import QuizGeneratorAgent
from agents.video_analyzer import VideoAnalyzerAgent
from agents.progress_tracker import ProgressTrackerAgent
from agents.feedback_agent import FeedbackAgent
from agents.mentor_agent import MentorAgent
from agents.planner_crew_agent import PlannerCrewAgent
from agents.evaluator_crew_agent import EvaluatorCrewAgent
from tasks.onboarding_tasks import OnboardingTasks
from planner.planner_agent import PlannerAgent
from evaluator.evaluator_agent import EvaluatorAgent
from memory.service import get_memory_service
from memory.mentor import AdaptiveMentor
from rag.pipeline import get_rag_pipeline
from tools.base import get_tool_registry
from observability.tracer import get_tracer, store_trace

load_dotenv()


class OnboardingCrew:
    def __init__(self):
        self.quiz_generator = QuizGeneratorAgent().create_agent()
        self.video_analyzer = VideoAnalyzerAgent().create_agent()
        self.progress_tracker = ProgressTrackerAgent().create_agent()
        self.feedback_agent = FeedbackAgent().create_agent()
        self.mentor_agent = MentorAgent().create_agent()
        self.planner_crew_agent = PlannerCrewAgent().create_agent()
        self.evaluator_crew_agent = EvaluatorCrewAgent().create_agent()

        self.planner = PlannerAgent()
        self.evaluator = EvaluatorAgent()
        self.mentor = AdaptiveMentor()
        self.memory = get_memory_service()
        self.rag = get_rag_pipeline()
        self.tools = get_tool_registry()

    # ------------------------------------------------------------------
    # Legacy single-agent APIs (kept for existing routes)
    # ------------------------------------------------------------------
    def generate_quiz(self, topic, difficulty="medium", num_questions=10, rag_context: str = ""):
        grounded = rag_context or self.tools.execute(
            "document_retrieval", query=topic, k=4
        )
        task = OnboardingTasks.quiz_generation_task(
            agent=self.quiz_generator,
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
        )
        # Enrich description with RAG context for mock/real crews
        task.description = (
            task.description
            + f"\n\nUse this company knowledge context:\n{grounded[:2000]}"
        )
        crew = Crew(
            agents=[self.quiz_generator],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )
        result = self._parse_json_result(crew.kickoff())
        # Attach synthetic score for memory when missing
        if "score" not in result:
            result["score"] = 78.0
        result["topic"] = result.get("topic") or topic
        result["difficulty"] = result.get("difficulty") or difficulty
        return result

    def analyze_video(self, video_url, learning_objectives=None):
        task = OnboardingTasks.video_analysis_task(
            agent=self.video_analyzer,
            video_url=video_url,
            learning_objectives=learning_objectives,
        )
        crew = Crew(
            agents=[self.video_analyzer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )
        return self._parse_json_result(crew.kickoff())

    def track_progress(self, employee_id, quiz_data, video_data):
        task = OnboardingTasks.progress_tracking_task(
            agent=self.progress_tracker,
            employee_id=employee_id,
            quiz_data=quiz_data,
            video_data=video_data,
        )
        crew = Crew(
            agents=[self.progress_tracker],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )
        return self._parse_json_result(crew.kickoff())

    def generate_feedback(self, employee_data, performance_summary, rag_context: str = ""):
        task = OnboardingTasks.feedback_generation_task(
            agent=self.feedback_agent,
            employee_data=employee_data,
            performance_summary=performance_summary,
        )
        if rag_context:
            task.description += f"\n\nPolicy/handbook context:\n{rag_context[:1500]}"
        crew = Crew(
            agents=[self.feedback_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )
        return self._parse_json_result(crew.kickoff())

    # ------------------------------------------------------------------
    # Autonomous planned workflow
    # ------------------------------------------------------------------
    def run_complete_onboarding(self, employee_data, modules, db=None):
        """
        Planner-driven autonomous onboarding with RAG, tools, evaluator, mentor, memory.
        Optional SQLAlchemy `db` session enables persistent digital memory.
        """
        tracer = get_tracer("autonomous_onboarding", employee_id=employee_data.get("id"))
        results: Dict[str, Any] = {
            "employee": employee_data,
            "plan": None,
            "rag_context": "",
            "quizzes": [],
            "video_analyses": [],
            "progress_report": None,
            "feedback": None,
            "evaluations": {},
            "mentor_insights": None,
            "memory": None,
            "notifications": [],
            "tools_invoked": [],
            "trace": None,
        }

        try:
            with tracer.span("load_memory", kind="agent"):
                memory_snapshot: Dict[str, Any] = {}
                if db is not None and employee_data.get("id"):
                    profile = self.memory.get_or_create_profile(db, employee_data["id"])
                    memory_snapshot = self.memory.as_dict(profile)
                    # Tool call for progress context
                    progress_json = self.tools.execute(
                        "progress_retrieval",
                        tracer=tracer,
                        employee_id=employee_data["id"],
                    )
                    results["tools_invoked"].append("progress_retrieval")
                    tracer.record_tokens(
                        prompt=tracer.estimate_tokens_from_text(progress_json),
                        completion=0,
                    )
                results["memory"] = memory_snapshot

            # Personalize modules using digital memory
            personalized_modules = self.memory.personalize_modules(memory_snapshot, modules)

            with tracer.span("planner", kind="planner"):
                plan = self.planner.create_plan(
                    employee_data, personalized_modules, memory_snapshot
                )
                results["plan"] = plan
                tracer.log(plan.get("rationale", "Plan created"))

            for step in plan.get("steps", []):
                agent_name = step.get("agent")
                action = step.get("action")

                if agent_name == "rag_retriever" or action == "retrieve_knowledge":
                    with tracer.span("rag_retriever", kind="agent"):
                        query = (
                            f"{employee_data.get('department', '')} "
                            f"{employee_data.get('position', '')} onboarding policies handbook"
                        )
                        context = self.tools.execute(
                            "document_retrieval", tracer=tracer, query=query, k=5
                        )
                        policy = self.tools.execute(
                            "policy_access",
                            tracer=tracer,
                            topic=f"{employee_data.get('department')} policies",
                        )
                        results["tools_invoked"].extend(["document_retrieval", "policy_access"])
                        results["rag_context"] = f"{context}\n\n{policy}"
                        tracer.record_tokens(
                            prompt=tracer.estimate_tokens_from_text(query),
                            completion=tracer.estimate_tokens_from_text(results["rag_context"]),
                        )

                elif agent_name == "planner" and action == "generate_plan":
                    # Already created; keep for explicit plan step visibility
                    tracer.log("Plan already materialized by PlannerAgent")

                elif agent_name == "mentor" and action == "risk_intervention_plan":
                    with tracer.span("risk_intervention", kind="agent"):
                        results.setdefault("risk_intervention", {
                            "priority": "high",
                            "actions": [
                                "Assign buddy mentor",
                                "Reduce first-week quiz difficulty",
                                "Schedule manager check-in",
                            ],
                        })

                elif agent_name == "quiz_generator":
                    with tracer.span("quiz_generator", kind="agent"):
                        for module in personalized_modules:
                            if module.get("type") != "quiz":
                                continue
                            topic = module["topic"]

                            def _gen(t=topic, m=module):
                                return self.generate_quiz(
                                    topic=t,
                                    difficulty=m.get("difficulty", "medium"),
                                    num_questions=m.get("num_questions", 10),
                                    rag_context=results["rag_context"],
                                )

                            raw_quiz = _gen()
                            gated = self.evaluator.ensure_quiz_quality(raw_quiz, regenerate_fn=_gen)
                            results["quizzes"].append(gated["quiz"])
                            results["evaluations"].setdefault("quizzes", []).append(gated["evaluation"])
                            tracer.record_tokens(prompt=400, completion=600)

                elif agent_name == "video_analyzer":
                    with tracer.span("video_analyzer", kind="agent"):
                        for module in personalized_modules:
                            if module.get("type") != "video":
                                continue
                            video_result = self.analyze_video(
                                video_url=module["url"],
                                learning_objectives=module.get("objectives"),
                            )
                            results["video_analyses"].append(video_result)
                            tracer.record_tokens(prompt=300, completion=400)

                elif agent_name == "progress_tracker":
                    with tracer.span("progress_tracker", kind="agent"):
                        if results["quizzes"] or results["video_analyses"]:
                            progress_report = self.track_progress(
                                employee_id=employee_data["id"],
                                quiz_data=results["quizzes"],
                                video_data=results["video_analyses"],
                            )
                            results["progress_report"] = progress_report
                            report_json = self.tools.execute(
                                "report_generation",
                                tracer=tracer,
                                employee_id=employee_data.get("id"),
                                employee_name=employee_data.get("name", "Employee"),
                                metrics=progress_report,
                            )
                            results["tools_invoked"].append("report_generation")
                            results["generated_report"] = self._parse_json_result(report_json)
                            tracer.record_tokens(prompt=350, completion=450)

                elif agent_name == "feedback_agent":
                    with tracer.span("feedback_agent", kind="agent"):
                        if results.get("progress_report"):
                            def _fb():
                                return self.generate_feedback(
                                    employee_data=employee_data,
                                    performance_summary=results["progress_report"],
                                    rag_context=results["rag_context"],
                                )

                            raw_fb = _fb()
                            gated_fb = self.evaluator.ensure_feedback_quality(
                                raw_fb, regenerate_fn=_fb
                            )
                            results["feedback"] = gated_fb["feedback"]
                            results["evaluations"]["feedback"] = gated_fb["evaluation"]
                            tracer.record_tokens(prompt=350, completion=500)

                elif agent_name == "evaluator" and action == "evaluate_outputs":
                    with tracer.span("evaluator", kind="evaluator"):
                        # Final sweep already done per artifact; summarize
                        quiz_evals = results["evaluations"].get("quizzes", [])
                        fb_eval = results["evaluations"].get("feedback")
                        results["evaluations"]["summary"] = {
                            "quizzes_passed": all(e.get("passed", True) for e in quiz_evals)
                            if quiz_evals
                            else True,
                            "feedback_passed": (fb_eval or {}).get("passed", True),
                            "avg_quiz_quality": round(
                                sum(e.get("quality_score", 0) for e in quiz_evals) / len(quiz_evals), 3
                            )
                            if quiz_evals
                            else None,
                        }

                elif agent_name == "mentor":
                    with tracer.span("mentor", kind="agent"):
                        insights = self.mentor.generate_insights(
                            employee=employee_data,
                            memory=memory_snapshot,
                            rag_context=results.get("rag_context", ""),
                            progress=results.get("progress_report"),
                        )
                        results["mentor_insights"] = insights
                        tracer.record_tokens(prompt=300, completion=400)

                elif agent_name == "memory":
                    with tracer.span("persist_memory", kind="agent"):
                        if db is not None and employee_data.get("id"):
                            updated = self.memory.update_from_onboarding_results(
                                db, employee_data["id"], results
                            )
                            results["memory"] = updated

                elif agent_name == "notifier":
                    with tracer.span("notifier", kind="agent"):
                        email = employee_data.get("email") or "employee@example.com"
                        subject = "Your Adaptive Onboarding Plan Is Ready"
                        body = (
                            f"Hi {employee_data.get('name', 'there')},\n\n"
                            f"Your personalized onboarding roadmap is ready.\n"
                            f"Risk level: {(results.get('mentor_insights') or {}).get('risk_level', 'n/a')}\n"
                            f"Next modules: {', '.join((results.get('mentor_insights') or {}).get('next_modules', []))}\n"
                        )
                        notice = self.tools.execute(
                            "mock_email",
                            tracer=tracer,
                            to=email,
                            subject=subject,
                            body=body,
                        )
                        results["tools_invoked"].append("mock_email")
                        results["notifications"].append(self._parse_json_result(notice))

            summary = tracer.finish(status="ok")
            results["trace"] = summary
            store_trace(summary)
            self._persist_trace(db, summary)
            return results

        except Exception as exc:
            summary = tracer.finish(status="error", error=str(exc))
            results["trace"] = summary
            results["error"] = str(exc)
            store_trace(summary)
            self._persist_trace(db, summary)
            raise

    def _persist_trace(self, db, summary: Dict[str, Any]) -> None:
        if db is None:
            return
        try:
            from database.models import AgentExecutionLog

            log = AgentExecutionLog(
                trace_id=summary.get("trace_id"),
                employee_id=summary.get("employee_id"),
                workflow=summary.get("workflow"),
                status=summary.get("status"),
                duration_ms=summary.get("duration_ms"),
                agents_run=json.dumps(summary.get("agents_run") or []),
                tools_used=json.dumps(summary.get("tools_used") or []),
                total_tokens_estimate=summary.get("total_tokens_estimate") or 0,
                error_count=summary.get("error_count") or 0,
                summary_json=json.dumps(summary, default=str),
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()

    def _parse_json_result(self, result):
        """Parse JSON from crew result"""
        try:
            if isinstance(result, dict):
                return result
            result_str = str(result)
            start = result_str.find("{")
            end = result_str.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(result_str[start:end])
            return {"raw_result": result_str}
        except json.JSONDecodeError:
            return {"raw_result": str(result)}
        except Exception as e:
            return {"error": str(e), "raw_result": str(result)}
