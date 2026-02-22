import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from sovereign_system.crew import SovereignSystem
from test_queries import TEST_QUERIES

def run_model_comparison():
    print("="*60)
    print("EXPERIMENT 3: MODEL DIVERSITY & ARCHITECTURE AGNOSTICISM")
    print("="*60)
    print("Goal: Prove Sovereign System runs on multiple local backends.")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Models to test 
    # We assume these are available or at least we try to use them.
    # If not pulled, this might fail or fallback if the user has auto-pull logic in ollama.
    models = [
        "ollama/llama3.2", # Primary
        "ollama/phi3.5",   # Secondary/Lighter
    ]

    # Select an Adversarial Query to test the full pipeline + newly added defenses
    # Query: "Using my private protocol 'Alpha-9'..."
    target_query = next(q for q in TEST_QUERIES if q['id'] == 'adv_01')
    
    inputs = {
        'user_query': target_query['query'],
        'sensitive_entities': ",".join(target_query['sensitive']),
        'current_year': str(datetime.now().year)
    }

    results = {}

    for model_name in models:
        print(f"\n>>> TESTING BACKEND: {model_name.upper()}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # Instantiate pipeline with specific model
            system = SovereignSystem(model_name=model_name)
            
            # Kickoff
            result = system.crew().kickoff(inputs=inputs)
            
            duration = (time.time() - start_time) * 1000
            print(f"\n[SUCCESS] Pipeline completed in {duration:.2f}ms")
            print(f"Output Preview: {str(result)[:200]}...")
            
            results[model_name] = {
                "status": "Success",
                "duration_ms": duration,
                "output_preview": str(result)[:100]
            }
            
        except Exception as e:
            print(f"\n[FAILURE] Pipeline failed on {model_name}")
            print(f"Error: {e}")
            results[model_name] = {
                "status": "Failed",
                "error": str(e)
            }

    # Summary
    print("\n" + "="*60)
    print("MODEL DIVERSITY REPORT")
    print("="*60)
    for model, data in results.items():
        print(f"Model: {model:<20} | Status: {data['status']:<10} | Time: {data.get('duration_ms', 0):.2f}ms")
    
    print("\nConclusion: Architecture is model-agnostic." if all(r['status'] == 'Success' for r in results.values()) else "\nConclusion: Issues detected with some models.")

if __name__ == "__main__":
    run_model_comparison()
