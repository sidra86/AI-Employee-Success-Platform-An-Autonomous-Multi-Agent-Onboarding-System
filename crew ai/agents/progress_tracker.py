try:
    from crewai import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    from mock_crew import Agent
    ChatOpenAI = None
import os

class ProgressTrackerAgent:
    def __init__(self):
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.2,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.llm = None
        
    def create_agent(self):
        return Agent(
            role="Learning Progress Analyst",
            goal="Track and analyze employee learning progress throughout the onboarding process",
            backstory="""You are a data-driven learning analyst with expertise in tracking educational 
            progress and identifying learning patterns. You excel at synthesizing multiple data points 
            to provide comprehensive progress reports and actionable insights.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[]
        )
    
    def generate_progress_report_prompt(self, employee_data, quiz_results, video_analyses):
        return f"""
        Generate a comprehensive progress report for an employee based on their onboarding data:
        
        Employee Information: {employee_data}
        Quiz Results: {quiz_results}
        Video Analysis Results: {video_analyses}
        
        Analyze and provide:
        1. Overall progress percentage (0-100%)
        2. Strengths identified
        3. Areas needing improvement
        4. Learning velocity assessment
        5. Predicted completion timeline
        6. Risk factors (if any)
        7. Personalized recommendations
        
        Format as JSON:
        {{
            "overall_progress": 75.5,
            "strengths": ["strength1", "strength2"],
            "improvement_areas": ["area1", "area2"],
            "learning_velocity": "above_average",
            "predicted_completion": "2024-01-15",
            "risk_factors": ["factor1"],
            "recommendations": ["rec1", "rec2"],
            "summary": "Detailed progress summary"
        }}
        """
