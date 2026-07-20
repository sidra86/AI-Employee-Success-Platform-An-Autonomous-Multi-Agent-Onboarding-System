try:
    from crewai import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    from mock_crew import Agent
    ChatOpenAI = None
import os

class QuizGeneratorAgent:
    def __init__(self):
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.llm = None
        
    def create_agent(self):
        return Agent(
            role="Quiz Generation Specialist",
            goal="Create comprehensive and engaging quizzes for employee onboarding based on training materials and company policies",
            backstory="""You are an expert instructional designer with years of experience in creating 
            effective assessments. You specialize in generating quizzes that test both knowledge retention 
            and practical application of concepts. Your quizzes are known for being fair, comprehensive, 
            and aligned with learning objectives.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[]
        )
    
    def generate_quiz_prompt(self, topic, difficulty="medium", num_questions=10):
        return f"""
        Generate a comprehensive quiz on the topic: {topic}
        
        Requirements:
        - Difficulty level: {difficulty}
        - Number of questions: {num_questions}
        - Include multiple choice, true/false, and short answer questions
        - Provide correct answers and explanations
        - Ensure questions test both theoretical knowledge and practical application
        - Include scenario-based questions where appropriate
        
        Format the output as JSON with the following structure:
        {{
            "quiz_title": "Quiz Title",
            "topic": "{topic}",
            "difficulty": "{difficulty}",
            "questions": [
                {{
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "Question text",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "Explanation for the correct answer"
                }}
            ]
        }}
        """
