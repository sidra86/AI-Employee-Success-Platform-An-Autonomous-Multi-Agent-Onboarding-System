try:
    from crewai import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    from mock_crew import Agent
    ChatOpenAI = None
import os


class MentorAgent:
    """Adaptive AI Mentor agent wrapper (CrewAI-compatible)."""

    def __init__(self):
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.5,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        else:
            self.llm = None

    def create_agent(self):
        return Agent(
            role="Adaptive AI Mentor",
            goal="Personalize onboarding using digital memory, RAG context, and learning analytics",
            backstory=(
                "You are a persistent AI mentor that remembers every employee's quiz history, "
                "weak topics, strengths, engagement, and preferred learning style. You create "
                "personalized roadmaps and predict who may struggle."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],
        )
