try:
    from crewai import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    from mock_crew import Agent
    ChatOpenAI = None
import os


class EvaluatorCrewAgent:
    """CrewAI-compatible evaluator agent definition."""

    def __init__(self):
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        else:
            self.llm = None

    def create_agent(self):
        return Agent(
            role="Quality Evaluator",
            goal="Review quizzes and feedback for quality; reject and regenerate low-quality outputs",
            backstory=(
                "You are a strict instructional-quality reviewer. You check structure, clarity, "
                "actionability, and alignment before employees see AI-generated content."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],
        )
