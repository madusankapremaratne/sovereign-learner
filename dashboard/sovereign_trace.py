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
        """Calculate overall privacy protection score"""
        if not self.steps:
            return 0.0
        
        # Privacy score is based on how much sensitive info was protected
        initial_exposure = 1.0  # 100% exposed initially
        final_exposure = self.steps[-1].privacy_score_after if self.steps else 1.0
        
        self.privacy_protection_score = 1.0 - final_exposure
        return self.privacy_protection_score
    
    def get_agent_contributions(self) -> Dict[str, float]:
        """Get each agent's contribution to privacy protection"""
        contributions = {}
        
        for step in self.steps:
            privacy_delta = step.privacy_score_before - step.privacy_score_after
            contributions[step.agent_name] = max(0, privacy_delta)
        
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
            raise ValueError("No active trace. Call start_trace() first.")
        
        step = AgentStep(
            agent_name=agent_name,
            agent_role=agent_role,
            input_data=input_data,
            output_data=output_data,
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
            raise ValueError("No active trace.")
        
        self.current_trace.final_response = final_response
        self.current_trace.zone_used = zone
        self.current_trace.utility_score = utility_score
        self.current_trace.calculate_privacy_score()
        
        self.traces.append(self.current_trace)
        
        completed_trace = self.current_trace
        self.current_trace = None
        
        return completed_trace
    
    def get_all_traces(self) -> List[SovereignTrace]:
        """Get all completed traces"""
        return self.traces


def create_demo_trace(query: str = "How do I optimize my CRISPR protocol for HEK293 cells?") -> SovereignTrace:
    """
    Create a demonstration trace for testing the dashboard.
    In production, this would be captured from actual pipeline execution.
    """
    import hashlib
    
    query_id = hashlib.md5(f"{query}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
    
    tracer = SovereignTracer()
    trace = tracer.start_trace(query_id, query)
    
    # Step 1: Sovereign Manager
    tracer.log_agent(
        agent_name="Sovereign Manager",
        agent_role="Privacy-Aware Query Router",
        input_data=query,
        output_data="Zone 1 - High Sensitivity Research Query",
        duration_ms=23.4,
        privacy_before=1.0,
        privacy_after=1.0,  # No change yet, just classification
        zone=1,
        metadata={
            "decision": "Zone 1",
            "confidence": 0.92,
            "reason": "Detected proprietary research terms (CRISPR, cell line)"
        }
    )
    
    # Step 2: Sensitivity Detector
    tracer.log_agent(
        agent_name="Sensitivity Detector",
        agent_role="PII and Sensitivity Detection Specialist",
        input_data=query,
        output_data="Detected: CRISPR (PROTOCOL), HEK293 (CELL_LINE)",
        duration_ms=11.2,
        privacy_before=1.0,
        privacy_after=1.0,  # Detection only, no masking yet
        entities_detected=["CRISPR", "HEK293"],
        metadata={
            "entity_types": {"CRISPR": "PROTOCOL", "HEK293": "CELL_LINE"},
            "risk_score": 0.85
        }
    )
    
    # Step 3: Semantic Generalizer (CORE - biggest privacy impact)
    tracer.log_agent(
        agent_name="Semantic Generalizer",
        agent_role="Intent Obfuscation Specialist",
        input_data=query,
        output_data="How do I optimize my Protocol-A protocol for Cell-A cells?",
        duration_ms=8.7,
        privacy_before=1.0,
        privacy_after=0.15,  # Major privacy protection
        entities_detected=["CRISPR", "HEK293"],
        entities_masked=["CRISPR", "HEK293"],
        mapping={"Protocol-A": "CRISPR", "Cell-A": "HEK293"},
        metadata={
            "transformation_type": "semantic_generalization",
            "intent_preserved": True,
            "tokens_masked": 2
        }
    )
    
    # Step 4: Cloud Researcher
    cloud_response = """To optimize Protocol-A for Cell-A cells, consider the following systematic approach:

1. **Parameter Tuning**: Adjust transfection efficiency by optimizing the ratio of Protocol-A components.
2. **Cell Density**: Ensure Cell-A cultures are at 70-80% confluence for optimal results.
3. **Timing**: Protocol-A efficiency varies with cell cycle - consider synchronization.
4. **Validation**: Use appropriate assays to confirm successful Protocol-A application in Cell-A."""
    
    tracer.log_agent(
        agent_name="Cloud Researcher",
        agent_role="Cloud-Based Knowledge Researcher (Gemini)",
        input_data="How do I optimize my Protocol-A protocol for Cell-A cells?",
        output_data=cloud_response,
        duration_ms=892.3,
        privacy_before=0.15,
        privacy_after=0.15,  # Maintained - cloud doesn't know real terms
        metadata={
            "model": "gemini-2.5-flash",
            "tokens_in": 42,
            "tokens_out": 156,
            "knows_real_terms": False
        }
    )
    
    # Step 5: Trust Enforcer
    tracer.log_agent(
        agent_name="Trust Enforcer",
        agent_role="Trust Boundary Validator",
        input_data=cloud_response,
        output_data="VALIDATED - No leakage detected, response approved",
        duration_ms=32.1,
        privacy_before=0.15,
        privacy_after=0.15,
        metadata={
            "leakage_check": "PASSED",
            "hallucination_check": "PASSED",
            "entities_leaked": [],
            "retry_count": 0
        }
    )
    
    # Step 6: Recontextualizer
    final_response = cloud_response.replace("Protocol-A", "CRISPR").replace("Cell-A", "HEK293")
    
    tracer.log_agent(
        agent_name="Recontextualizer",
        agent_role="Response Re-contextualization Specialist",
        input_data=cloud_response,
        output_data=final_response,
        duration_ms=5.4,
        privacy_before=0.15,
        privacy_after=0.0,  # Fully restored for local user
        mapping={"Protocol-A": "CRISPR", "Cell-A": "HEK293"},
        metadata={
            "terms_restored": 2,
            "restoration_success": True
        }
    )
    
    # Step 7: Evidence Curator
    tracer.log_agent(
        agent_name="Evidence Curator",
        agent_role="Competency Evidence Curator",
        input_data=f"Query: {query}\nResponse: {final_response[:100]}...",
        output_data="Evidence stored in local ChromaDB",
        duration_ms=51.2,
        privacy_before=0.0,
        privacy_after=0.0,
        metadata={
            "storage": "ChromaDB (local)",
            "evidence_id": "97d73e71-21ac-4624",
            "weight": 1.0,
            "interaction_type": "active"
        }
    )
    
    return tracer.end_trace(final_response, zone=1, utility_score=0.85)


if __name__ == "__main__":
    # Test the tracer
    trace = create_demo_trace()
    print(json.dumps(trace.to_dict(), indent=2))
