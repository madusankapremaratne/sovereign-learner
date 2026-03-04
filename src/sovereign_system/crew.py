from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
import os
from typing import Any, Type, List, Optional
from pydantic import BaseModel, Field

from sovereign_system.tools.presidio_tools import PresidioScanTool
from sovereign_system.tools.semantic_tools import IntentAbstractorTool, ContextRestorerTool, AdversarialAuditTool
from sovereign_system.tools.competency_tools import CompetencyEvidenceTool
from sovereign_system.tools.privacy_tools import PrivacyScanTool
from sovereign_system.tools.guardrail_tools import OutputSanitizerTool

@CrewBase
class SovereignSystem():
    agents_config = os.path.join(os.path.dirname(__file__), 'config/agents.yaml')
    tasks_config = os.path.join(os.path.dirname(__file__), 'config/tasks.yaml')
    
    def __init__(self, model_name: str = "ollama/llama3.2", tracer=None):
        self.model_name = model_name
        self.local_url = "http://localhost:11434"
        self.tracer = tracer

    @property
    def local_llm(self):
        return LLM(model=self.model_name, base_url=self.local_url)

    @property
    def worker_llm(self):
        return LLM(model=self.model_name, base_url=self.local_url)

    @property
    def cloud_llm(self):
        return LLM(model="groq/openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY"))

    # Agents
    @agent
    def sovereign_manager(self) -> Agent:
        return Agent(config=self.agents_config['sovereign_manager'], llm=self.local_llm, verbose=False, max_iter=2)

    @agent
    def semantic_generalizer(self) -> Agent:
        return Agent(config=self.agents_config['semantic_generalizer'], llm=self.local_llm, tools=[PresidioScanTool(), IntentAbstractorTool(), AdversarialAuditTool()], verbose=False, max_iter=3)

    @agent
    def recontextualizer(self) -> Agent:
        return Agent(config=self.agents_config['recontextualizer'], llm=self.local_llm, tools=[ContextRestorerTool(), OutputSanitizerTool()], verbose=True, max_iter=3)

    @agent
    def cloud_researcher(self) -> Agent:
        return Agent(config=self.agents_config['cloud_researcher'], llm=self.cloud_llm, verbose=False, max_iter=3)

    @agent
    def evidence_curator(self) -> Agent:
        return Agent(config=self.agents_config['evidence_curator'], llm=self.worker_llm, tools=[CompetencyEvidenceTool()], verbose=False, max_iter=1)

    # Tasks
    @task
    def routing_task(self) -> Task:
        return Task(config=self.tasks_config['routing_task'])

    @task
    def pre_processing_task(self) -> Task:
        return Task(config=self.tasks_config['pre_processing_task'])

    @task
    def cloud_knowledge_task(self) -> Task:
        return Task(config=self.tasks_config['cloud_knowledge_task'])

    @task
    def response_processing_task(self) -> Task:
        return Task(config=self.tasks_config['response_processing_task'])

    @task
    def data_sovereignty_task(self) -> Task:
        return Task(config=self.tasks_config['data_sovereignty_task'], async_execution=True)

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=None,
            share_crew=False
        )
