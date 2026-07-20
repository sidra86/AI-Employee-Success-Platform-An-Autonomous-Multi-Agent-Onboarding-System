from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    department = Column(String(50), nullable=False)
    position = Column(String(100), nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    onboarding_status = Column(String(20), default="pending")  # pending, in_progress, completed
    
    # Relationships
    quiz_results = relationship("QuizResult", back_populates="employee")
    video_analyses = relationship("VideoAnalysis", back_populates="employee")
    progress_reports = relationship("ProgressReport", back_populates="employee")

class OnboardingModule(Base):
    __tablename__ = "onboarding_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    module_type = Column(String(50), nullable=False)  # quiz, video, reading
    content = Column(Text)
    order_sequence = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    module_id = Column(Integer, ForeignKey("onboarding_modules.id"))
    score = Column(Float, nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    time_taken = Column(Integer)  # in seconds
    completed_at = Column(DateTime, default=datetime.utcnow)
    feedback = Column(Text)
    
    # Relationships
    employee = relationship("Employee", back_populates="quiz_results")
    module = relationship("OnboardingModule")

class VideoAnalysis(Base):
    __tablename__ = "video_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    video_url = Column(String(500), nullable=False)
    transcript = Column(Text)
    engagement_score = Column(Float)
    comprehension_score = Column(Float)
    key_points_covered = Column(Text)
    areas_for_improvement = Column(Text)
    analysis_completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="video_analyses")

class ProgressReport(Base):
    __tablename__ = "progress_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    overall_progress = Column(Float, nullable=False)  # percentage
    modules_completed = Column(Integer, default=0)
    total_modules = Column(Integer, nullable=False)
    average_quiz_score = Column(Float)
    average_engagement = Column(Float)
    recommendations = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="progress_reports")


class EmployeeLearningProfile(Base):
    """Persistent digital memory for Adaptive AI Mentoring."""

    __tablename__ = "employee_learning_profiles"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    weak_topics = Column(Text, default="[]")
    strong_topics = Column(Text, default="[]")
    learning_speed = Column(String(50), default="average")
    completed_modules = Column(Text, default="[]")
    previous_feedback = Column(Text, default="[]")
    engagement_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.5)
    preferred_learning_style = Column(String(50), default="mixed")
    common_mistakes = Column(Text, default="[]")
    recommended_next_modules = Column(Text, default="[]")
    quiz_history = Column(Text, default="[]")
    risk_level = Column(String(20), default="low")
    personalized_roadmap = Column(Text, default="[]")
    last_updated = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", backref="learning_profile")


class KnowledgeDocument(Base):
    """Metadata for uploaded RAG knowledge documents."""

    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(255))
    category = Column(String(100), default="general")
    chunk_count = Column(Integer, default=0)
    storage_path = Column(String(500))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100), default="admin")


class AgentExecutionLog(Base):
    """Persisted observability traces for agent workflows."""

    __tablename__ = "agent_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(64), index=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    workflow = Column(String(100), default="onboarding")
    status = Column(String(20), default="ok")
    duration_ms = Column(Float)
    agents_run = Column(Text)
    tools_used = Column(Text)
    total_tokens_estimate = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    summary_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
