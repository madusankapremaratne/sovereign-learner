
import sys
import os
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from sovereign_system.crew import SovereignSystem

# Load env vars
load_dotenv()

def call_sovereign_pipeline(query: str):
    """
    Adapter for Promptfoo to call the Sovereign System.
    """
    inputs = {
        'query': query,
        'current_year': '2026'
    }
    
    try:
        # We need to capture the output, but CrewAI is chatty.
        # Ideally, we'd hook into the result.
        crew_instance = SovereignSystem().crew()
        result = crew_instance.kickoff(inputs=inputs)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

def call_api(prompt, options, context):
    """
    Promptfoo provider interface implementation.
    """
    result = call_sovereign_pipeline(prompt)
    return {
        "output": result
    }

