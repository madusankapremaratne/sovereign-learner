
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath("src"))

from sovereign_system.crew import SovereignSystem
from sovereign_system.utils.sovereign_trace_logger import SovereignTracer

def run_demo_traces():
    # Define targets
    targets = [
        {
            "filename": "trace_zone_0_latest_demo.json",
            "query": "What is the Capital of France",
            "id": "z0_demo"
        },
        {
            "filename": "trace_zone_1_latest_demo.json",
            "query": "How do I optimize my CRISPR protocol for HEK293 cells?",
            "id": "z1_demo"
        },
        {
            "filename": "trace_zone_2_latest_demo.json",
            "query": "What are the common side effects of chemotherapy?",
            "id": "z2_demo"
        },
        {
            "filename": "trace_zone_3_latest_demo.json",
            "query": "What is the latest Python Version.",
            "id": "z3_demo"
        }
    ]

    tracer = SovereignTracer()
    output_dir = "dashboard/traces"
    os.makedirs(output_dir, exist_ok=True)

    for target in targets:
        print(f"\nExample: {target['filename']}")
        print(f"Query: {target['query']}")
        
        # Start a fresh trace
        tracer.start_trace(query_id=target['id'], original_query=target['query'])
        
        # Init system with tracer
        system = SovereignSystem(tracer=tracer)
        
        inputs = {
            'query': target['query'],
            'user_query': target['query'],
            'current_year': str(datetime.now().year)
        }
        
        try:
            # Run the crew
            # Note: We are running the crew. The agents will execute.
            # The callback in crew.py will log steps to our tracer.
            print("Kickoff crew...")
            result = system.crew().kickoff(inputs=inputs)
            print("Crew finished.")
            
            # Analyze zone from trace
            trace = tracer.current_trace
            zone = 1 # default
            
            if trace and trace.steps:
                # Try to find Sovereign Manager decision
                for step in trace.steps:
                    if "Sovereign Manager" in step.agent_name:
                        output_lower = step.output_data.lower()
                        if "zone 3" in output_lower: zone = 3
                        elif "zone 2" in output_lower: zone = 2
                        elif "zone 1" in output_lower: zone = 1
                        elif "zone 0" in output_lower: zone = 0
                        break
            
            # End trace
            tracer.end_trace(final_response=str(result), zone=zone, utility_score=0.95)
            
            # Save to specific filename
            last_trace = tracer.traces[-1]
            trace_dict = last_trace.to_dict()
            
            filepath = os.path.join(output_dir, target['filename'])
            with open(filepath, 'w') as f:
                json.dump(trace_dict, f, indent=2)
            
            print(f"✅ Saved trace to {filepath} (Detected Zone: {zone})")

        except Exception as e:
            print(f"❌ Error running {target['query']}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_demo_traces()
