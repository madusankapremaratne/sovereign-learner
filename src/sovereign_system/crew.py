from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
import os
from dotenv import load_dotenv

load_dotenv()
from typing import Any, Type, List, Optional, Dict
from pydantic import BaseModel, Field

from sovereign_system.tools.presidio_tools import PresidioScanTool
from sovereign_system.tools.semantic_tools import IntentAbstractorTool, ContextRestorerTool, AdversarialAuditTool
from sovereign_system.tools.competency_tools import CompetencyEvidenceTool
from sovereign_system.tools.privacy_tools import PrivacyScanTool
from sovereign_system.tools.guardrail_tools import OutputSanitizerTool, SafetyAuditTool, ZoneValidationTool

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
    def cloud_llm_gemini(self):
        return LLM(model="gemini/gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

    @property
    def cloud_llm_groq(self):
        return LLM(model="groq/openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY"))

    # Agents
    @agent
    def sovereign_manager(self) -> Agent:
        return Agent(config=self.agents_config['sovereign_manager'], llm=self.local_llm, tools=[SafetyAuditTool(), ZoneValidationTool()], verbose=False, max_iter=2)

    @agent
    def semantic_generalizer(self) -> Agent:
        return Agent(config=self.agents_config['semantic_generalizer'], llm=self.local_llm, tools=[PresidioScanTool(), IntentAbstractorTool(), AdversarialAuditTool()], verbose=False, max_iter=3)

    @agent
    def recontextualizer(self) -> Agent:
        return Agent(config=self.agents_config['recontextualizer'], llm=self.local_llm, tools=[ContextRestorerTool(), OutputSanitizerTool()], verbose=True, max_iter=3)

    @agent
    def cloud_researcher(self) -> Agent:
        return Agent(config=self.agents_config['cloud_researcher'], llm=self.cloud_llm_gemini, verbose=False, max_iter=3)

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

    def kickoff(self, inputs: Dict[str, Any]) -> Any:
        """
        Custom kickoff logic with 'Sovereign Early-Exit'.
        If the Governor (Routing Task) classifies a query as Zone 0 (Blocked),
        the system halts immediately to prevent cloud leakage and save quota.
        """
        user_query = inputs.get("user_query", "")

        # 0. Deterministic Zero-Trust Safety Scan (Phase 0)
        # Prevents toxic/harmful content from even reaching the local router
        from sovereign_system.security.guard import guard
        is_unsafe, reason = guard.is_unsafe(user_query)
        if is_unsafe:
            print(f"  🚨 DETERMINISTIC BLOCK: Policy violation found ({reason}). Stopping.")
            return type('Output', (), {'raw': f'REJECTED: Policy Violation Detected by Sovereign Governance ({reason}).'})()
        
        # 1. Routing (Local Agentic Audit)
        governor = self.sovereign_manager()
        router_task = self.routing_task()
        router_task.agent = governor
        router_task.description = router_task.description.format(**inputs)
        
        print(f"  [Sovereign Governance] Routing query...")
        route_output = governor.execute_task(router_task)
        
        # Parse zone robustly using regex to avoid false positives on '0' in the reason
        import re
        zone = 3
        zone_match = re.search(r'"zone"\s*:\s*(\d)', str(route_output), re.IGNORECASE)
        if zone_match:
            zone = int(zone_match.group(1))
        elif "zone 0" in str(route_output).lower() or "blocked" in str(route_output).lower():
            zone = 0
        elif "zone 1" in str(route_output).lower():
            zone = 1
        elif "zone 2" in str(route_output).lower():
            zone = 2
            
        if zone == 0:
            print(f"  🚨 SECURITY BLOCK: Zone 0 detected. Stopping pipeline.")
            return type('Output', (), {'raw': 'REJECTED: Policy Violation Detected by Sovereign Governance.'})()
        
        # 2. Pre-processing (Local)
        architect = self.semantic_generalizer()
        pre_task = self.pre_processing_task()
        pre_task.agent = architect
        pre_task.description = pre_task.description.format(**inputs)
        
        print(f"  [Semantic Architect] Generalizing intent...")
        pre_output = architect.execute_task(pre_task)
        
        # Extract generalized query and mapping for downstream
        gen_query = ""
        mapping = "{}"
        if "SANITIZED:" in pre_output:
            gen_query = pre_output.split("SANITIZED:")[1].split("MAPPING:")[0].strip()
        if "MAPPING:" in pre_output:
            mapping = pre_output.split("MAPPING:")[1].split("COVERAGE:")[0].strip()

        # 3. Cloud Research (Gemini)
        # Add a delay to protect Gemini Free Tier quota (429 prevention)
        import time
        time.sleep(5)
        
        researcher = self.cloud_researcher()
        cloud_task = self.cloud_knowledge_task()
        cloud_task.agent = researcher
        cloud_task.description = f"Researcher knowledge for: {gen_query}"
        
        print(f"  [Cloud Researcher] Querying domain knowledge...")
        cloud_output = researcher.execute_task(cloud_task)
        
        # 4. Response Processing (Local)
        finalizer = self.recontextualizer()
        final_task = self.response_processing_task()
        final_task.agent = finalizer
        final_task.description = f"1. Restore context to: {cloud_output}\n2. Using mapping: {mapping}"
        
        print(f"  [Final Answer Composer] Recontextualizing...")
        final_answer = finalizer.execute_task(final_task)
        
        # 5. Storage (Background)
        # For simplicity in this refactor, we skip the async storage curator or call it synchronously
        
        return type('Output', (), {'raw': final_answer})()
