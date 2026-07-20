try:
    from crewai import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    from mock_crew import Agent
    ChatOpenAI = None
import os


class PlannerCrewAgent:
    """CrewAI-compatible planner agent definition."""

    def __init__(self):
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.2,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        else:
            self.llm = None

    def create_agent(self):
        return Agent(
            role="Onboarding Planner / Orchestrator",
            goal="Decide which specialized agents should run next for each employee",
            backstory=(
                "You coordinate multi-agent onboarding workflows. You inspect employee memory, "
                "department requirements, and knowledge-base context, then emit an ordered plan."
            ),
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],
        )
