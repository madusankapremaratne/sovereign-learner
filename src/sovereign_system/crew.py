from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
import os
from sovereign_system.tools.semantic_tools import SemanticGeneralizationTool, RecontextualizationTool
from sovereign_system.tools.competency_tools import CompetencyEvidenceTool
from sovereign_system.tools.privacy_tools import PrivacyScanTool

@CrewBase
class SovereignSystem():
    agents_config = os.path.join(os.path.dirname(__file__), 'config/agents.yaml')
    tasks_config = os.path.join(os.path.dirname(__file__), 'config/tasks.yaml')
    
    def __init__(self, model_name: str = "ollama/llama3.2"):
        self.model_name = model_name
        self.local_url = "http://localhost:11434"

    @property
    def local_llm(self):
        return LLM(model=self.model_name, base_url=self.local_url)

    @property
    def worker_llm(self):
        # Allow worker model customization or stick to lighter model
        return LLM(model="ollama/phi3.5", base_url=self.local_url)

    @property
    def cloud_llm(self):
        return LLM(model="gemini/gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

    @agent
    def sovereign_manager(self) -> Agent:
        return Agent(config=self.agents_config['sovereign_manager'], llm=self.local_llm, verbose=True)

    @agent
    def sensitivity_detector(self) -> Agent:
        return Agent(config=self.agents_config['sensitivity_detector'], llm=self.worker_llm, verbose=True)

    
    @agent
    def semantic_generalizer(self) -> Agent:
        return Agent(
            config=self.agents_config['semantic_generalizer'],
            llm=self.local_llm,
            tools=[SemanticGeneralizationTool()],
            verbose=True
        )

    @agent
    def recontextualizer(self) -> Agent:
        return Agent(
            config=self.agents_config['recontextualizer'],
            llm=self.local_llm,
            tools=[RecontextualizationTool()],
            verbose=True
        )

    @agent
    def competency_tracker(self) -> Agent:
        return Agent(
            config=self.agents_config['competency_tracker'],
            llm=self.worker_llm,
            tools=[CompetencyEvidenceTool()],
            verbose=True
        )

    @agent
    def cloud_researcher(self) -> Agent:
        # This agent gets the Cloud LLM
        return Agent(config=self.agents_config['cloud_researcher'], llm=self.cloud_llm, verbose=True)

    @agent
    def trust_enforcer(self) -> Agent:
        return Agent(
            config=self.agents_config['trust_enforcer'], 
            llm=self.local_llm, 
            tools=[PrivacyScanTool()],
            verbose=True
        )


    # --- TASKS ---
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
    def execute_cloud_query(self) -> Task:
        return Task(config=self.tasks_config['execute_cloud_query'])

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
            process=Process.sequential, # Correct: Privacy requires a strict pipe
            verbose=True,
        )