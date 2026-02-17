
import sys
import os
import json
import random
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath("src"))

from sovereign_system.utils.sovereign_trace_logger import SovereignTracer

def create_traces():
    tracer = SovereignTracer()
    output_dir = "dashboard/traces"
    os.makedirs(output_dir, exist_ok=True)
    
    # ---------------------------------------------------------
    # Scenario 1: Zone 0 (Offline) - "What is the Capital of France"
    # ---------------------------------------------------------
    query_0 = "What is the Capital of France"
    tracer.start_trace(query_id="z0_demo", original_query=query_0)
    
    # Step 1: Manager
    tracer.log_agent(
        agent_name="Sovereign Manager",
        agent_role="Privacy-Aware Query Router",
        input_data=query_0,
        output_data="Zone 0 - Offline/Local Only. Public fact but user requested offline handling.",
        duration_ms=45.0,
        zone=0,
        metadata={"decision": "Zone 0", "reason": "User preference for offline processing"}
    )
    
    # Step 2: Local SLM (Simulated as 'Local High-Speed Inference')
    # Since there's no explicit 'Local SLM' agent in the main list, we'll use a placeholder or generic 'Local Assistant'
    # Actually, usually 'Sovereign Manager' might answer directly or delegate to 'Local Researcher'?
    # Let's say 'Local Researcher' for demo purposes.
    tracer.log_agent(
        agent_name="Local Researcher", 
        agent_role="Offline Knowledge Retrieval",
        input_data=query_0,
        output_data="The capital of France is Paris.",
        duration_ms=120.0,
        zone=0,
        metadata={"model": "Phi-3.5-mini", "source": "local_param_knowledge"}
    )
    
    # Step 3: Curator
    tracer.log_agent(
        agent_name="Evidence Curator",
        agent_role="Learning Record Manager",
        input_data="The capital of France is Paris.",
        output_data="Competency Updated (Local)",
        duration_ms=25.0,
        zone=0,
        metadata={"persisted": True}
    )
    
    tracer.end_trace("The capital of France is Paris.", zone=0, utility_score=1.0)
    save_trace(tracer.traces[-1], "trace_zone_0_latest_demo.json")


    # ---------------------------------------------------------
    # Scenario 2: Zone 1 (High Sensitive) - "How do I optimize my CRISPR Protocol for HEK293 Cells?"
    # ---------------------------------------------------------
    query_1 = "How do I optimize my CRISPR Protocol for HEK293 Cells?"
    tracer.start_trace(query_id="z1_demo", original_query=query_1)
    
    # 1. Sovereign Manager
    tracer.log_agent(
        agent_name="Sovereign Manager",
        agent_role="Privacy-Aware Query Router",
        input_data=query_1,
        output_data="Categorized to Zone 1 - High Sensitivity (biomedical)",
        duration_ms=45.0,
        zone=1,
        metadata={"decision": "Zone 1", "reason": "Detected confidential research terms (CRISPR, HEK293)"}
    )

    # 2. Sensitivity Detector
    tracer.log_agent(
        agent_name="Sensitivity Detector",
        agent_role="Auto-Discovery (Knowledge-Based)", # Matched role name from legal trace
        input_data=query_1,
        output_data="Detected: ['CRISPR Protocol', 'HEK293 Cells']", # Matched format
        duration_ms=80.0,
        zone=1,
        entities_detected=["CRISPR Protocol", "HEK293 Cells"]
    )

    # 3. Semantic Generalizer
    mapping = {'Protocol A': 'CRISPR Protocol', 'Cell B': 'HEK293 Cells'}
    generalized_query = 'How do I optimize "Protocol A" for "Cell B"'
    gen_input = f"Query: {query_1}\nEntities: ['CRISPR Protocol', 'HEK293 Cells']"
    gen_output = f"SANITIZED: {generalized_query}\nMAPPING: {str(mapping)}"
    
    tracer.log_agent(
        agent_name="Semantic Generalizer",
        agent_role="Intent Obfuscation Specialist",
        input_data=gen_input,
        output_data=gen_output,
        duration_ms=210.0,
        privacy_before=1.0, 
        privacy_after=0.1, # Protected
        entities_detected=["CRISPR Protocol", "HEK293 Cells"],
        entities_masked=["Protocol A", "Cell B"],
        mapping=mapping,
        zone=1
    )
    
    # 4. Cloud Researcher
    cloud_resp = 'Optimizing Protocol A for Cell B requires a systematic "checkerboard" titration approach that balances reagent efficiency against cellular toxicity. In our experience, the most frequent failure point is applying a "one-size-fits-all" concentration to a cell line with unique metabolic demands or membrane compositions.'
    
    tracer.log_agent(
        agent_name="Cloud Researcher",
        agent_role="External Knowledge Retrieval", # Matched role
        input_data=generalized_query,
        output_data=cloud_resp,
        duration_ms=1800.0,
        privacy_before=0.1,
        privacy_after=0.1,
        zone=1,
        metadata={"source": "external_llm_sanitized"}
    )
    
    # 5. Trust Enforcer
    tracer.log_agent(
        agent_name="Trust Enforcer",
        agent_role="Trust Boundary Validator",
        input_data=cloud_resp,
        output_data="Validating cloud response against internal safety guidelines... validation successful. No logical inconsistencies or safety violations detected.",
        duration_ms=350.0,
        zone=1,
        privacy_before=0.1,
        privacy_after=0.1
    )
    
    # 6. Recontextualizer
    final_resp = 'Optimizing CRISPR Protocol for HEK293 Cells requires a systematic "checkerboard" titration approach that balances reagent efficiency against cellular toxicity. In our experience, the most frequent failure point is applying a "one-size-fits-all" concentration to a cell line with unique metabolic demands or membrane compositions.'
    recon_input = f"Response: {cloud_resp[:50]}...\nMapping: {str(mapping)}"
    
    tracer.log_agent(
        agent_name="Recontextualizer",
        agent_role="Response Re-contextualization Specialist",
        input_data=recon_input,
        output_data=final_resp,
        duration_ms=120.0,
        privacy_before=0.1,
        privacy_after=1.0, # Restored
        mapping=mapping, # Explicitly adding mapping here too
        zone=1
    )
    
    # 7. Competency Tracker
    tracer.log_agent(
        agent_name="Competency Tracker",
        agent_role="Learning Evidence Aggregator",
        input_data=final_resp,
        output_data="Tracking variable utilization: CRISPR Protocol (active), HEK293 Cells (active). Updating vector V_Portfolio.",
        duration_ms=40.0,
        privacy_before=1.0,
        privacy_after=1.0,
        zone=1
    )
    
    # 8. Evidence Curator
    tracer.log_agent(
        agent_name="Evidence Curator",
        agent_role="Competency Evidence Curator", # Matched role roughly
        input_data="Full Trace Data",
        output_data="Data securely stored in local vector DB [Collection: research_logs].",
        duration_ms=50.0,
        privacy_before=1.0,
        privacy_after=1.0,
        zone=1
    )
    
    tracer.end_trace(final_resp, zone=1, utility_score=0.98)
    save_trace(tracer.traces[-1], "trace_zone_1_latest_demo.json")


    # ---------------------------------------------------------
    # Scenario 3: Zone 2 (Semi-Private) - "What are the common side effects of chemotherapy?"
    # ---------------------------------------------------------
    query_2 = "What are the common side effects of chemotherapy?"
    tracer.start_trace(query_id="z2_demo", original_query=query_2)
    
    tracer.log_agent(
        agent_name="Sovereign Manager",
        agent_role="Privacy-Aware Query Router",
        input_data=query_2,
        output_data="Zone 2 - Trusted External. Medical topic but general knowledge.",
        duration_ms=40.0,
        zone=2,
        metadata={"decision": "Zone 2", "reason": "Sensitive domain (Medical) but generic query"}
    )
    
    # Zone 2 might skip heavy generalization but use Trusted Cloud (e.g., specific compliant LLM)
    # Or it runs mild PII scanning.
    tracer.log_agent(
        agent_name="Sensitivity Detector",
        agent_role="PII and Sensitivity Detection Specialist",
        input_data=query_2,
        output_data="Detected: 'chemotherapy' (Medical). No personal PII found.",
        duration_ms=80.0,
        zone=2
    )

    cloud_resp_2 = "Common side effects include fatigue, nausea, hair loss, and increased risk of infection."
    tracer.log_agent(
        agent_name="Cloud Researcher",
        agent_role="External Knowledge Retrieval",
        input_data=query_2,
        output_data=cloud_resp_2,
        duration_ms=1200.0,
        privacy_before=0.8, # Slightly exposed but trusted
        privacy_after=0.8,
        zone=2,
        metadata={"model": "HIPAA-Compliant-LLM", "source": "trusted_cloud"}
    )
    
    tracer.log_agent(
        agent_name="Evidence Curator",
        agent_role="Learning Record Manager",
        input_data=cloud_resp_2,
        output_data="Competency Updated",
        duration_ms=30.0,
        zone=2
    )
    
    tracer.end_trace(cloud_resp_2, zone=2, utility_score=0.98)
    save_trace(tracer.traces[-1], "trace_zone_2_latest_demo.json")


    # ---------------------------------------------------------
    # Scenario 4: Zone 3 (Public) - "What is the latest Python Version."
    # ---------------------------------------------------------
    query_3 = "What is the latest Python Version."
    tracer.start_trace(query_id="z3_demo", original_query=query_3)
    
    tracer.log_agent(
        agent_name="Sovereign Manager",
        agent_role="Privacy-Aware Query Router",
        input_data=query_3,
        output_data="Zone 3 - Public Information",
        duration_ms=35.0,
        zone=3,
        metadata={"decision": "Zone 3", "reason": "Public technical query, no sensitivity"}
    )
    
    cloud_resp_3 = "As of late 2025/early 2026, the latest stable version of Python is Python 3.14."
    tracer.log_agent(
        agent_name="Cloud Researcher",
        agent_role="External Knowledge Retrieval",
        input_data=query_3,
        output_data=cloud_resp_3,
        duration_ms=900.0,
        privacy_before=1.0, # Public info, so effectively 1.0 (no loss of private info) or 0.0 (fully exposed)?
        # Usually for public info, no privacy is LOST because no private info existed. So score = 1.0 (Safe).
        privacy_after=1.0,
        zone=3,
        metadata={"model": "Llama-3.3-70b", "source": "public_web"}
    )
    
    tracer.log_agent(
        agent_name="Evidence Curator",
        agent_role="Learning Record Manager",
        input_data=cloud_resp_3,
        output_data="Competency Updated",
        duration_ms=25.0,
        zone=3
    )
    
    tracer.end_trace(cloud_resp_3, zone=3, utility_score=1.0)
    save_trace(tracer.traces[-1], "trace_zone_3_latest_demo.json")

    print("✅ All demo traces generated successfully.")

def save_trace(trace, filename):
    import os
    import json
    filepath = os.path.join("dashboard/traces", filename)
    with open(filepath, 'w') as f:
        json.dump(trace.to_dict(), f, indent=2)
    print(f"Saved {filepath}")

if __name__ == "__main__":
    create_traces()
