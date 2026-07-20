"""
Mock CrewAI implementation for demonstration purposes
This allows the system to work without requiring CrewAI installation
"""

import json
import random
from datetime import datetime

class MockAgent:
    def __init__(self, role, goal, backstory, **kwargs):
        self.role = role
        self.goal = goal
        self.backstory = backstory
    
    def __str__(self):
        return f"MockAgent({self.role})"

class MockTask:
    def __init__(self, description, agent, expected_output, **kwargs):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
    
    def __str__(self):
        return f"MockTask({self.description[:50]}...)"

class MockCrew:
    def __init__(self, agents, tasks, **kwargs):
        self.agents = agents
        self.tasks = tasks
    
    def kickoff(self):
        """Mock crew execution that returns realistic demo data"""
        # Simulate different types of responses based on task content
        task_desc = self.tasks[0].description.lower()
        
        if ("plan" in task_desc and "orchestr" in task_desc) or "execution plan" in task_desc:
            return self._generate_mock_plan()
        elif "evaluat" in task_desc or "quality gate" in task_desc:
            return self._generate_mock_evaluation()
        elif "mentor" in task_desc:
            return self._generate_mock_mentor()
        elif "quiz" in task_desc:
            return self._generate_mock_quiz()
        elif "video" in task_desc:
            return self._generate_mock_video_analysis()
        elif "progress" in task_desc:
            return self._generate_mock_progress_report()
        elif "feedback" in task_desc:
            return self._generate_mock_feedback()
        else:
            return self._generate_mock_quiz()
    
    def _generate_mock_plan(self):
        return json.dumps({
            "steps": [
                "rag_retriever",
                "quiz_generator",
                "video_analyzer",
                "progress_tracker",
                "feedback_agent",
                "evaluator",
                "mentor",
                "memory"
            ],
            "rationale": "Standard adaptive onboarding plan with quality gates and mentoring."
        })

    def _generate_mock_evaluation(self):
        return json.dumps({
            "quality_score": 0.86,
            "passed": True,
            "issues": [],
            "notes": "Outputs meet instructional quality standards."
        })

    def _generate_mock_mentor(self):
        return json.dumps({
            "mentor_summary": "Personalized mentor roadmap ready based on digital memory.",
            "next_modules": ["Policy deep dive", "Role-specific scenarios"],
            "predictions": ["On track for timely completion"],
            "recommendations": ["Schedule peer shadowing", "Reinforce weak quiz topics"]
        })
    
    def _generate_mock_quiz(self):
        """Generate a mock quiz response"""
        questions = [
            {
                "id": 1,
                "type": "multiple_choice",
                "question": "What is the company's policy on remote work?",
                "options": ["Fully remote", "Hybrid model", "Office only", "Flexible arrangement"],
                "correct_answer": "Hybrid model",
                "explanation": "The company follows a hybrid model allowing both remote and office work."
            },
            {
                "id": 2,
                "type": "multiple_choice",
                "question": "How often should you update your password?",
                "options": ["Every 30 days", "Every 90 days", "Every 6 months", "Once a year"],
                "correct_answer": "Every 90 days",
                "explanation": "Company policy requires password updates every 90 days for security."
            },
            {
                "id": 3,
                "type": "multiple_choice",
                "question": "What is the process for requesting time off?",
                "options": ["Email manager", "Use HR portal", "Submit paper form", "Call HR"],
                "correct_answer": "Use HR portal",
                "explanation": "All time-off requests should be submitted through the HR portal."
            }
        ]
        
        return json.dumps({
            "quiz_title": "Company Onboarding Quiz",
            "topic": "Company Policies",
            "difficulty": "medium",
            "questions": questions
        })
    
    def _generate_mock_video_analysis(self):
        """Generate a mock video analysis response"""
        return json.dumps({
            "key_points": [
                "Company culture and values",
                "Team collaboration best practices",
                "Communication guidelines",
                "Professional development opportunities"
            ],
            "engagement_score": round(random.uniform(7.0, 9.5), 1),
            "comprehension_score": round(random.uniform(7.5, 9.0), 1),
            "areas_for_improvement": [
                "Time management skills",
                "Technical proficiency",
                "Team communication"
            ],
            "effectiveness_score": round(random.uniform(8.0, 9.2), 1),
            "recommendations": [
                "Review key concepts covered in the video",
                "Practice the demonstrated techniques",
                "Schedule follow-up sessions for complex topics"
            ],
            "summary": "The training video effectively covers essential onboarding topics with good engagement potential."
        })
    
    def _generate_mock_progress_report(self):
        """Generate a mock progress report"""
        return json.dumps({
            "overall_progress": round(random.uniform(65.0, 95.0), 1),
            "strengths": [
                "Quick learning ability",
                "Strong communication skills",
                "Good attention to detail"
            ],
            "improvement_areas": [
                "Technical skills development",
                "Process familiarity",
                "Time management"
            ],
            "learning_velocity": random.choice(["above_average", "average", "excellent"]),
            "predicted_completion": "2024-12-15",
            "risk_factors": [
                "Complex technical concepts may need additional support"
            ],
            "recommendations": [
                "Continue with current learning pace",
                "Focus on practical applications",
                "Schedule mentoring sessions"
            ],
            "summary": "Employee is progressing well through the onboarding process with strong foundational understanding."
        })
    
    def _generate_mock_feedback(self):
        """Generate mock personalized feedback"""
        return json.dumps({
            "positive_feedback": "Excellent progress on completing the onboarding modules. Your quiz scores demonstrate strong understanding of company policies and procedures.",
            "improvement_areas": [
                {
                    "area": "Technical Skills",
                    "suggestion": "Consider taking additional technical training courses",
                    "resources": ["Online tutorials", "Internal training sessions", "Mentorship program"]
                },
                {
                    "area": "Process Knowledge",
                    "suggestion": "Shadow experienced team members to learn workflows",
                    "resources": ["Process documentation", "Team shadowing", "Q&A sessions"]
                }
            ],
            "motivational_message": "You're doing great! Your dedication to learning and positive attitude are valuable assets to our team.",
            "next_steps": [
                "Complete remaining onboarding modules",
                "Schedule one-on-one with manager",
                "Join team meetings and projects"
            ],
            "timeline": "Expected to complete onboarding within 2 weeks",
            "overall_message": "Keep up the excellent work! You're well on your way to becoming a valuable team member."
        })

# Mock the CrewAI imports
def Agent(**kwargs):
    return MockAgent(**kwargs)

def Task(**kwargs):
    return MockTask(**kwargs)

def Crew(**kwargs):
    return MockCrew(**kwargs)

class Process:
    sequential = "sequential"
