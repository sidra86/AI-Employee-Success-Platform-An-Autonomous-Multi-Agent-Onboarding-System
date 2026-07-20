from fastapi import FastAPI, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database.database import get_db, init_db
from database.models import (
    Employee,
    OnboardingModule,
    QuizResult,
    VideoAnalysis,
    ProgressReport,
    KnowledgeDocument,
    AgentExecutionLog,
    EmployeeLearningProfile,
)
from app.crew_orchestrator import OnboardingCrew
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime

from rag.pipeline import get_rag_pipeline
from memory.service import get_memory_service
from observability.tracer import get_recent_traces
from tools.base import get_tool_registry
from tools.notification_tools import EMAIL_OUTBOX

# Initialize FastAPI app
app = FastAPI(
    title="Adaptive AI Employee Success Platform",
    version="2.0.0",
    description="Autonomous multi-agent onboarding with RAG, digital memory, and adaptive mentoring",
)

# Mount static files and templates
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database
init_db()

# Initialize CrewAI orchestrator
crew = OnboardingCrew()
rag = get_rag_pipeline()
memory_service = get_memory_service()


# Pydantic models for API
class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str
    position: str


class QuizRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    num_questions: int = 10


class VideoAnalysisRequest(BaseModel):
    video_url: str
    learning_objectives: Optional[str] = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    k: int = 5
    category: Optional[str] = None


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse(request, "index.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard showing all employees and their progress"""
    employees = db.query(Employee).all()
    insights = memory_service.manager_insights(db)
    recent_traces = (
        db.query(AgentExecutionLog)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "employees": employees,
            "insights": insights,
            "recent_traces": recent_traces,
            "rag_stats": rag.stats(),
        },
    )


@app.get("/insights", response_class=HTMLResponse)
async def manager_insights(request: Request, db: Session = Depends(get_db)):
    """Manager insights dashboard"""
    employees = db.query(Employee).all()
    insights = memory_service.manager_insights(db)
    profiles = db.query(EmployeeLearningProfile).all()
    profile_map = {p.employee_id: memory_service.as_dict(p) for p in profiles}
    traces = (
        db.query(AgentExecutionLog)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(30)
        .all()
    )
    completed = len([e for e in employees if e.onboarding_status == "completed"])
    completion_rate = round((completed / len(employees)) * 100, 1) if employees else 0
    return templates.TemplateResponse(
        request,
        "insights.html",
        {
            "employees": employees,
            "insights": insights,
            "profile_map": profile_map,
            "traces": traces,
            "completion_rate": completion_rate,
            "in_memory_traces": get_recent_traces(10),
        },
    )


@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page(request: Request, db: Session = Depends(get_db)):
    docs = (
        db.query(KnowledgeDocument)
        .order_by(KnowledgeDocument.uploaded_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "knowledge.html",
        {"documents": docs, "rag_stats": rag.stats(), "tools": get_tool_registry().list_tools()},
    )


@app.post("/employees/")
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """Create a new employee"""
    db_employee = Employee(
        name=employee.name,
        email=employee.email,
        department=employee.department,
        position=employee.position,
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    # Seed empty learning profile
    memory_service.get_or_create_profile(db, db_employee.id)
    return {
        "id": db_employee.id,
        "name": db_employee.name,
        "email": db_employee.email,
        "department": db_employee.department,
        "position": db_employee.position,
        "onboarding_status": db_employee.onboarding_status,
        "start_date": db_employee.start_date.isoformat() if db_employee.start_date else None,
    }


@app.get("/employees/{employee_id}", response_class=HTMLResponse)
async def employee_detail(request: Request, employee_id: int, db: Session = Depends(get_db)):
    """Employee detail page"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    quiz_results = db.query(QuizResult).filter(QuizResult.employee_id == employee_id).all()
    video_analyses = db.query(VideoAnalysis).filter(VideoAnalysis.employee_id == employee_id).all()
    progress_reports = (
        db.query(ProgressReport).filter(ProgressReport.employee_id == employee_id).all()
    )
    profile = memory_service.get_or_create_profile(db, employee_id)
    memory = memory_service.as_dict(profile)
    traces = (
        db.query(AgentExecutionLog)
        .filter(AgentExecutionLog.employee_id == employee_id)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(10)
        .all()
    )
    latest_progress = progress_reports[-1].overall_progress if progress_reports else 0

    # Timeline events
    timeline = []
    timeline.append(
        {
            "label": "Joined",
            "at": employee.start_date.isoformat() if employee.start_date else None,
            "type": "join",
        }
    )
    for q in quiz_results:
        timeline.append(
            {
                "label": f"Quiz score {q.score}",
                "at": q.completed_at.isoformat() if q.completed_at else None,
                "type": "quiz",
            }
        )
    for v in video_analyses:
        timeline.append(
            {
                "label": f"Video engagement {v.engagement_score}",
                "at": v.analysis_completed_at.isoformat() if v.analysis_completed_at else None,
                "type": "video",
            }
        )
    for t in traces:
        timeline.append(
            {
                "label": f"Agent run ({t.status})",
                "at": t.created_at.isoformat() if t.created_at else None,
                "type": "agent",
            }
        )
    timeline = sorted([e for e in timeline if e.get("at")], key=lambda x: x["at"])

    return templates.TemplateResponse(
        request,
        "employee_detail.html",
        {
            "employee": employee,
            "quiz_results": quiz_results,
            "video_analyses": video_analyses,
            "progress_reports": progress_reports,
            "memory": memory,
            "traces": traces,
            "timeline": timeline,
            "completion_percentage": latest_progress,
        },
    )


@app.post("/generate-quiz/")
async def generate_quiz(quiz_request: QuizRequest):
    """Generate a quiz using CrewAI"""
    try:
        result = crew.generate_quiz(
            topic=quiz_request.topic,
            difficulty=quiz_request.difficulty,
            num_questions=quiz_request.num_questions,
        )
        return {"success": True, "quiz": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-video/")
async def analyze_video(video_request: VideoAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze a video using CrewAI"""
    try:
        result = crew.analyze_video(
            video_url=video_request.video_url,
            learning_objectives=video_request.learning_objectives,
        )
        return {"success": True, "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/employees/{employee_id}/start-onboarding")
async def start_onboarding(employee_id: int, db: Session = Depends(get_db)):
    """Start the complete autonomous onboarding process for an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    modules = get_onboarding_modules(employee.department)
    employee.onboarding_status = "in_progress"
    db.commit()

    try:
        employee_data = {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "position": employee.position,
        }

        results = crew.run_complete_onboarding(employee_data, modules, db=db)
        save_onboarding_results(db, employee_id, results)
        employee.onboarding_status = "completed"
        db.commit()
        return {"success": True, "results": results}
    except Exception as e:
        employee.onboarding_status = "pending"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/onboarding-form/{employee_id}", response_class=HTMLResponse)
async def onboarding_form(request: Request, employee_id: int, db: Session = Depends(get_db)):
    """Show onboarding form for an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return templates.TemplateResponse(request, "onboarding_form.html", {"employee": employee})


@app.post("/submit-quiz/{employee_id}")
async def submit_quiz(
    employee_id: int,
    quiz_data: str = Form(...),
    db: Session = Depends(get_db),
):
    """Submit quiz results"""
    try:
        quiz_result_data = json.loads(quiz_data)

        quiz_result = QuizResult(
            employee_id=employee_id,
            module_id=1,
            score=quiz_result_data.get("score", 0),
            total_questions=quiz_result_data.get("total_questions", 0),
            correct_answers=quiz_result_data.get("correct_answers", 0),
            time_taken=quiz_result_data.get("time_taken", 0),
            feedback=quiz_result_data.get("feedback", ""),
        )

        db.add(quiz_result)
        db.commit()

        # Update digital memory from quiz submission
        memory_service.update_from_onboarding_results(
            db,
            employee_id,
            {
                "quizzes": [
                    {
                        "topic": quiz_result_data.get("topic", "Submitted Quiz"),
                        "score": quiz_result_data.get("score", 0),
                        "difficulty": quiz_result_data.get("difficulty", "medium"),
                    }
                ]
            },
        )

        return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Knowledge / RAG --------------------
@app.post("/api/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    category: str = Form("general"),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    filename = file.filename or "document.pdf"
    try:
        if filename.lower().endswith(".pdf"):
            result = rag.ingest_pdf(content, filename=filename, category=category, title=title)
        else:
            text = content.decode("utf-8", errors="ignore")
            result = rag.ingest_text(
                text, filename=filename, category=category, title=title, source_type="text"
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = KnowledgeDocument(
        document_id=result["document_id"],
        filename=result["filename"],
        title=result.get("title"),
        category=result.get("category", category),
        chunk_count=result.get("chunk_count", 0),
        storage_path=result.get("storage_path"),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"success": True, "document": result, "id": doc.id}


@app.post("/api/knowledge/search")
async def search_knowledge(body: KnowledgeSearchRequest):
    hits = rag.retrieve(query=body.query, k=body.k, category=body.category)
    return {"success": True, "results": hits, "context": rag.build_context(body.query, body.k, body.category)}


@app.get("/api/knowledge/stats")
async def knowledge_stats():
    return rag.stats()


@app.delete("/api/knowledge/{document_id}")
async def delete_knowledge(document_id: str, db: Session = Depends(get_db)):
    deleted_chunks = rag.delete_document(document_id)
    db.query(KnowledgeDocument).filter(KnowledgeDocument.document_id == document_id).delete()
    db.commit()
    return {"success": True, "deleted_chunks": deleted_chunks}


# -------------------- Memory / Observability APIs --------------------
@app.get("/api/employees/{employee_id}/memory")
async def get_employee_memory(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    profile = memory_service.get_or_create_profile(db, employee_id)
    return memory_service.as_dict(profile)


@app.get("/api/insights")
async def api_insights(db: Session = Depends(get_db)):
    return memory_service.manager_insights(db)


@app.get("/api/traces")
async def api_traces(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(AgentExecutionLog)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "trace_id": r.trace_id,
            "employee_id": r.employee_id,
            "workflow": r.workflow,
            "status": r.status,
            "duration_ms": r.duration_ms,
            "agents_run": json.loads(r.agents_run or "[]"),
            "tools_used": json.loads(r.tools_used or "[]"),
            "total_tokens_estimate": r.total_tokens_estimate,
            "error_count": r.error_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "summary": json.loads(r.summary_json) if r.summary_json else None,
        }
        for r in rows
    ]


@app.get("/api/tools")
async def api_tools():
    return get_tool_registry().list_tools()


@app.get("/api/notifications/outbox")
async def api_email_outbox():
    return EMAIL_OUTBOX[:50]


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Adaptive AI Employee Success Platform",
        "version": "2.0.0",
        "rag": rag.stats(),
    }


def get_onboarding_modules(department: str) -> List[dict]:
    """Get onboarding modules based on department"""
    base_modules = [
        {
            "type": "quiz",
            "topic": "Company Policies and Code of Conduct",
            "difficulty": "medium",
            "num_questions": 10,
        },
        {
            "type": "video",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "objectives": "Understanding company culture and values",
        },
    ]

    department_specific = {
        "Engineering": [
            {
                "type": "quiz",
                "topic": "Software Development Best Practices",
                "difficulty": "medium",
                "num_questions": 15,
            }
        ],
        "Sales": [
            {
                "type": "quiz",
                "topic": "Sales Processes and CRM Usage",
                "difficulty": "medium",
                "num_questions": 12,
            }
        ],
        "HR": [
            {
                "type": "quiz",
                "topic": "Employment Law and HR Policies",
                "difficulty": "medium",
                "num_questions": 20,
            }
        ],
    }

    modules = base_modules.copy()
    if department in department_specific:
        modules.extend(department_specific[department])

    return modules


def save_onboarding_results(db: Session, employee_id: int, results: dict):
    """Save onboarding results to database"""
    for quiz in results.get("quizzes", []):
        quiz_result = QuizResult(
            employee_id=employee_id,
            module_id=1,
            score=quiz.get("score", 0),
            total_questions=len(quiz.get("questions", [])),
            correct_answers=quiz.get("correct_answers", 0),
            feedback=json.dumps(quiz),
        )
        db.add(quiz_result)

    for video in results.get("video_analyses", []):
        video_analysis = VideoAnalysis(
            employee_id=employee_id,
            video_url="sample_url",
            transcript=video.get("transcript", ""),
            engagement_score=video.get("engagement_score", 0),
            comprehension_score=video.get("comprehension_score", 0),
            key_points_covered=json.dumps(video.get("key_points", [])),
            areas_for_improvement=json.dumps(video.get("areas_for_improvement", [])),
        )
        db.add(video_analysis)

    if results.get("progress_report"):
        progress = results["progress_report"]
        progress_report = ProgressReport(
            employee_id=employee_id,
            overall_progress=progress.get("overall_progress", 0),
            modules_completed=len(results.get("quizzes", []))
            + len(results.get("video_analyses", [])),
            total_modules=len(results.get("quizzes", []))
            + len(results.get("video_analyses", [])),
            recommendations=json.dumps(progress.get("recommendations", [])),
        )
        db.add(progress_report)

    db.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
