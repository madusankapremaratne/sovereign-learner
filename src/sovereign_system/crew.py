from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
import os
from sovereign_system.tools.semantic_tools import SemanticGeneralizationTool, RecontextualizationTool
from sovereign_system.tools.competency_tools import CompetencyEvidenceTool

# --- LLM CONFIGURATIONS ---
# Local "Sovereign" LLM
local_llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
# Faster Local "Worker" LLM (Optional: if you want to use Phi-3.5 for simpler tasks)
worker_llm = LLM(model="ollama/phi3.5", base_url="http://localhost:11434")
# Cloud LLM (The one causing your 404 - Ensure API KEY is in .env)
cloud_llm = LLM(model="gemini/gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

@CrewBase
class SovereignSystem():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def sovereign_manager(self) -> Agent:
        return Agent(config=self.agents_config['sovereign_manager'], llm=local_llm, verbose=True)

    @agent
    def sensitivity_detector(self) -> Agent:
        return Agent(config=self.agents_config['sensitivity_detector'], llm=worker_llm, verbose=True)

    
    @agent
    def semantic_generalizer(self) -> Agent:
        return Agent(
            config=self.agents_config['semantic_generalizer'],
            llm=local_llm,
            tools=[SemanticGeneralizationTool()],
            verbose=True
        )

    @agent
    def recontextualizer(self) -> Agent:
        return Agent(
            config=self.agents_config['recontextualizer'],
            llm=local_llm,
            tools=[RecontextualizationTool()],
            verbose=True
        )

    @agent
    def competency_tracker(self) -> Agent:
        return Agent(
            config=self.agents_config['competency_tracker'],
            llm=worker_llm,
            tools=[CompetencyEvidenceTool()],
            verbose=True
        )

    @agent
    def cloud_researcher(self) -> Agent:
        # This agent gets the Cloud LLM
        return Agent(config=self.agents_config['cloud_researcher'], llm=cloud_llm, verbose=True)

    @agent
    def trust_enforcer(self) -> Agent:
        return Agent(config=self.agents_config['trust_enforcer'], llm=local_llm, verbose=True)


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