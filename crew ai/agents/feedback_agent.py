try:
    from crewai import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    from mock_crew import Agent
    ChatOpenAI = None
import os

class FeedbackAgent:
    def __init__(self):
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.6,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.llm = None
        
    def create_agent(self):
        return Agent(
            role="Personalized Feedback Specialist",
            goal="Provide constructive, personalized feedback to help employees improve their onboarding experience",
            backstory="""You are an experienced HR professional and learning coach who excels at 
            providing motivational and actionable feedback. You understand how to communicate 
            constructively while maintaining employee engagement and confidence.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[]
        )
    
    def generate_feedback_prompt(self, employee_data, performance_data, learning_style=None):
        style_text = f"\nLearning Style: {learning_style}" if learning_style else ""
        
        return f"""
        Generate personalized, constructive feedback for an employee based on their onboarding performance:
        
        Employee Information: {employee_data}
        Performance Data: {performance_data}
        {style_text}
        
        Provide feedback that includes:
        1. Positive reinforcement for achievements
        2. Specific areas for improvement with actionable steps
        3. Motivational messaging
        4. Customized learning resources or next steps
        5. Timeline expectations
        6. Encouragement and support
        
        Tone: Professional, supportive, and encouraging
        
        Format as JSON:
        {{
            "positive_feedback": "Specific achievements and strengths",
            "improvement_areas": [
                {{
                    "area": "Area name",
                    "suggestion": "Specific actionable step",
                    "resources": ["resource1", "resource2"]
                }}
            ],
            "motivational_message": "Encouraging message",
            "next_steps": ["step1", "step2"],
            "timeline": "Expected timeline for improvement",
            "overall_message": "Comprehensive feedback summary"
        }}
        """
