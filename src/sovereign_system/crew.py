"""
Sovereign System Crew

This module defines the SovereignSystem crew, a privacy-first multi-agent system
designed to handle sensitive queries through a sovereign processing pipeline.
It manages a team of agents responsible for sensitivity classification,
entity detection, semantic generalization, trust enforcement, and competency tracking.
"""
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from sovereign_system.tools.semantic_tools import SemanticGeneralizationTool, RecontextualizationTool
from sovereign_system.tools.competency_tools import CompetencyEvidenceTool

@CrewBase
class SovereignSystem():
    """
    SovereignSystem Crew

    This class orchestrates the privacy-preserving agent workflow. It defines
    the agents and tasks required to process queries according to their sensitivity
    zones (0-3), ensuring that sensitive data is protected via semantic generalization
    and local validation before (or instead of) interacting with cloud models.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def sovereign_manager(self) -> Agent:
        return Agent(config=self.agents_config['sovereign_manager'], verbose=True)

    @agent
    def sensitivity_detector(self) -> Agent:
        return Agent(config=self.agents_config['sensitivity_detector'], verbose=True)

    @agent
    def semantic_generalizer(self) -> Agent:
        return Agent(
            config=self.agents_config['semantic_generalizer'],
            tools=[SemanticGeneralizationTool()],
            verbose=True
        )

    @agent
    def trust_enforcer(self) -> Agent:
        return Agent(config=self.agents_config['trust_enforcer'], verbose=True)

    @agent
    def recontextualizer(self) -> Agent:
        return Agent(
            config=self.agents_config['recontextualizer'],
            tools=[RecontextualizationTool()],
            verbose=True
        )

    @agent
    def competency_tracker(self) -> Agent:
        return Agent(
            config=self.agents_config['competency_tracker'],
            tools=[CompetencyEvidenceTool()],
            verbose=True
        )

    @task
    def classify_sensitivity(self) -> Task:
        return Task(config=self.tasks_config['classify_sensitivity'])

    @task
    def detect_sensitive_entities(self) -> Task:
        return Task(config=self.tasks_config['detect_sensitive_entities'])

    @task
    def generalize_query(self) -> Task:
        return Task(config=self.tasks_config['generalize_query'])

    @task
    def validate_response(self) -> Task:
        return Task(config=self.tasks_config['validate_response'])

    @task
    def recontextualize_response(self) -> Task:
        return Task(config=self.tasks_config['recontextualize_response'])

    @task
    def update_competency(self) -> Task:
        return Task(config=self.tasks_config['update_competency'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # CRITICAL: Sequential for privacy!
            verbose=True,
        )