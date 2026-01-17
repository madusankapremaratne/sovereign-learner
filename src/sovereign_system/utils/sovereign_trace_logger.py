"""
SovereignTrace - Explainability Logger for Agentic AI
======================================================
Captures the journey of a query through the Sovereign Learner pipeline.
Analogous to SHAP for agentic systems.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import json
import os


@dataclass
class AgentStep:
    """Single step in the agent pipeline"""
    agent_name: str
    agent_role: str
    input_data: str
    output_data: str
    duration_ms: float
    privacy_score_before: float  # 0-1, how much sensitive info remains
    privacy_score_after: float
    entities_detected: List[str] = field(default_factory=list)
    entities_masked: List[str] = field(default_factory=list)
    mapping: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    zone: Optional[int] = None
    status: str = "success"  # success, warning, error


@dataclass
class SovereignTrace:
    """
    Complete trace of a query through the Sovereign Learner pipeline.
    Provides SHAP-like explainability for agentic AI systems.
    """
    query_id: str
    original_query: str
    steps: List[AgentStep] = field(default_factory=list)
    final_response: str = ""
    total_duration_ms: float = 0.0
    zone_used: int = 1
    privacy_protection_score: float = 0.0
    utility_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_step(self, step: AgentStep):
        """Add a step to the trace"""
        self.steps.append(step)
        self.total_duration_ms += step.duration_ms
    
    def calculate_privacy_score(self) -> float:
        """
        Calculate overall privacy protection score.
        Logic: The protection score is determined by how protected the data was 
        WHEN IT LEFT local custody (i.e., at the Cloud Researcher step).
        It is NOT the final score, because the final score is 1.0 (restored for user).
        """""
        if not self.steps:
            return 0.0
        
        # Find the minimum privacy score (maximum protection) achieved during the flow
        # This usually happens at the Cloud Researcher step
        min_exposure = 1.0
        for step in self.steps:
            if step.privacy_score_after < min_exposure:
                min_exposure = step.privacy_score_after
                
        # If we never reduced exposure, score is 0. If we reduced to 0.1, score is 0.9.
        self.privacy_protection_score = 1.0 - min_exposure
        return self.privacy_protection_score
    
    def get_agent_contributions(self) -> Dict[str, float]:
        """
        Get each agent's contribution to the Sovereign Privacy Workflow.
        Calculates a score based on:
        1. Privacy Delta: Active reduction of exposure (Primary)
        2. Safe Custody: Maintaining protection during processing (Secondary)
        3. Policy Decision: Strategic routing decisions (Base)
        """
        contributions = {}
        
        for step in self.steps:
            # 1. Active Protection (Delta)
            # How much did this agent strictly reduce exposure?
            privacy_delta = max(0, step.privacy_score_before - step.privacy_score_after)
            
            # 2. Safe Custody (Maintenance)
            # If data was protected (score < 0.9), keeping it safe helps.
            # We give credit for operating on sensitive data without leaking.
            custody_score = 0.0
            if step.privacy_score_before < 0.9:
                # Check if they maintained it (didn't increase exposure significantly)
                if step.privacy_score_after <= step.privacy_score_before + 0.1:
                    # Credit proportional to sensitivity (lower score = higher risk/credit)
                    custody_score = 0.15 * (1.0 - step.privacy_score_before)
            
            # 3. Policy Decisions (Manager)
            # The manager gets credit for identifying the zone correctly
            policy_score = 0.0
            if "Manager" in step.agent_name:
                policy_score = 0.15
            
            # 4. Secure Re-integration (Recontextualizer)
            # Restoring data safely to the user is a critical step
            restoration_score = 0.0
            if "Recontextualizer" in step.agent_name and step.privacy_score_after > step.privacy_score_before:
                restoration_score = 0.2
                
            total_contribution = privacy_delta + custody_score + policy_score + restoration_score
            contributions[step.agent_name] = total_contribution
        
        return contributions
    
    def get_timeline(self) -> List[Dict]:
        """Get timeline data for visualization"""
        timeline = []
        cumulative_time = 0
        
        for step in self.steps:
            timeline.append({
                "agent": step.agent_name,
                "start_ms": cumulative_time,
                "duration_ms": step.duration_ms,
                "end_ms": cumulative_time + step.duration_ms
            })
            cumulative_time += step.duration_ms
        
        return timeline
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "query_id": self.query_id,
            "original_query": self.original_query,
            "steps": [asdict(s) for s in self.steps],
            "final_response": self.final_response,
            "total_duration_ms": self.total_duration_ms,
            "zone_used": self.zone_used,
            "privacy_protection_score": self.privacy_protection_score,
            "utility_score": self.utility_score,
            "created_at": self.created_at,
            "agent_contributions": self.get_agent_contributions(),
            "timeline": self.get_timeline()
        }
    
    def save(self, output_dir: str = "./traces"):
        """Save trace to JSON file"""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"trace_{self.query_id}.json")
        
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return filepath


class SovereignTracer:
    """
    Tracer that wraps the Sovereign Learner pipeline to capture execution data.
    """
    
    def __init__(self):
        self.current_trace: Optional[SovereignTrace] = None
        self.traces: List[SovereignTrace] = []
    
    def start_trace(self, query_id: str, original_query: str) -> SovereignTrace:
        """Start a new trace"""
        self.current_trace = SovereignTrace(
            query_id=query_id,
            original_query=original_query
        )
        return self.current_trace
    
    def log_agent(
        self,
        agent_name: str,
        agent_role: str,
        input_data: str,
        output_data: str,
        duration_ms: float,
        privacy_before: float = 1.0,
        privacy_after: float = 1.0,
        entities_detected: List[str] = None,
        entities_masked: List[str] = None,
        mapping: Dict[str, str] = None,
        zone: int = None,
        metadata: Dict = None
    ):
        """Log an agent execution step"""
        if not self.current_trace:
            # Auto-start trace if none exists (fallback)
            self.start_trace(
                query_id=f"auto_{int(datetime.now().timestamp())}", 
                original_query=input_data
            )
        
        step = AgentStep(
            agent_name=agent_name,
            agent_role=agent_role,
            input_data=str(input_data),
            output_data=str(output_data),
            duration_ms=duration_ms,
            privacy_score_before=privacy_before,
            privacy_score_after=privacy_after,
            entities_detected=entities_detected or [],
            entities_masked=entities_masked or [],
            mapping=mapping or {},
            zone=zone,
            metadata=metadata or {}
        )
        
        self.current_trace.add_step(step)
        return step
    
    def end_trace(self, final_response: str, zone: int = 1, utility_score: float = 0.0):
        """End the current trace"""
        if not self.current_trace:
            return None
        
        self.current_trace.final_response = final_response
        self.current_trace.zone_used = zone
        self.current_trace.utility_score = utility_score
        self.current_trace.calculate_privacy_score()
        
        self.traces.append(self.current_trace)
        
        completed_trace = self.current_trace
        self.current_trace = None
        
        # Auto-save
        try:
            # We want to save to the dashboard traces folder if possible
            # Assuming we are running from root or src
            # Try to resolve dashboard/traces relative to current working dir
            # But safer to just save to ./dashboard/traces
            dashboard_traces = os.path.join(os.getcwd(), "dashboard", "traces")
            completed_trace.save(dashboard_traces)
        except Exception as e:
            print(f"Failed to auto-save trace: {e}")
        
        return completed_trace
    
    def get_all_traces(self) -> List[SovereignTrace]:
        """Get all completed traces"""
        return self.traces

# Global Singleton for easy import across modules
global_tracer = SovereignTracer()

def create_demo_trace(query: str = "How do I optimize my CRISPR protocol for HEK293 cells?") -> SovereignTrace:
    """
    Create a demonstration trace for testing the dashboard.
    In production, this would be captured from actual pipeline execution.
    """
    import hashlib
    import random
    
    query_id = hashlib.md5(f"{query}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
    
    tracer = SovereignTracer()
    trace = tracer.start_trace(query_id, query)
    
    # 1. Sovereign Manager
    tracer.log_agent(
        agent_name="Sovereign Manager",
        agent_role="Privacy-Aware Query Router",
        input_data=query,
        output_data="Zone 1 - High Sensitivity Research Query",
        duration_ms=45.2,
        privacy_before=1.0,
        privacy_after=1.0,  # No modification yet
        zone=1,
        metadata={
            "decision": "Zone 1",
            "confidence": 0.98,
            "reason": "Detected proprietary research terms (CRISPR, HEK293)"
        }
    )
    
    # 2. Semantic Generalizer
    mapping = {'Protocol-Alpha': 'CRISPR', 'Cell-Beta': 'HEK293'}
    sanitized_query = "How do I optimize my Protocol-Alpha protocol for Cell-Beta cells?"
    
    tracer.log_agent(
        agent_name="Semantic Generalizer",
        agent_role="Intent Obfuscation Specialist",
        input_data=f"Query: {query}\nEntities: ['CRISPR', 'HEK293']",
        output_data=f"SANITIZED: {sanitized_query}\nMAPPING: {mapping}",
        duration_ms=120.5,
        privacy_before=1.0,
        privacy_after=0.1,  # High privacy protection
        entities_detected=["CRISPR", "HEK293"],
        entities_masked=["Protocol-Alpha", "Cell-Beta"],
        mapping=mapping,
        zone=1,
        metadata={"strategy": "generalization_substitution"}
    )
    
    # 3. Cloud Researcher (Simulated)
    cloud_response = "Optimizing Protocol-Alpha for Cell-Beta typically requires adjusting transfection reagents, carefully monitoring incubation times, and validating with appropriate controls."
    
    tracer.log_agent(
        agent_name="Cloud Researcher",
        agent_role="External Knowledge Retrieval",
        input_data=sanitized_query,
        output_data=cloud_response,
        duration_ms=1540.2,  # Simulated network latency
        privacy_before=0.1,
        privacy_after=0.1,
        zone=1,
        metadata={"model": "gemini-pro", "source": "external_api"}
    )
    
    # 4. Recontextualizer
    final_response = "Optimizing CRISPR for HEK293 typically requires adjusting transfection reagents, carefully monitoring incubation times, and validating with appropriate controls."
    
    tracer.log_agent(
        agent_name="Recontextualizer",
        agent_role="Response Re-contextualization Specialist",
        input_data=f"Response: {cloud_response}\nMapping: {mapping}",
        output_data=final_response,
        duration_ms=85.6,
        privacy_before=0.1,
        privacy_after=1.0,  # Restored for user
        mapping=mapping,
        zone=1,
        metadata={"replacements_made": 2}
    )
    
    # 5. Evidence Curator
    tracer.log_agent(
        agent_name="Evidence Curator",
        agent_role="Learning Record Manager",
        input_data=final_response,
        output_data="Competency Updated: vector_db_id_8823",
        duration_ms=32.1,
        privacy_before=1.0,
        privacy_after=1.0,
        zone=1,
        metadata={
            "utility": 0.95,
            "leakage": 0.0,
            "persisted": True
        }
    )
    
    tracer.end_trace(final_response, zone=1, utility_score=0.95)
    return tracer.traces[0]
