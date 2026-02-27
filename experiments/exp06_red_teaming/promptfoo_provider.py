import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from sovereign_system.crew import SovereignSystem

def call_api(prompt, options, context):
    try:
        # Initialize the system with the default model
        # We can also pass model_name from options if needed
        model_name = options.get('model_name', 'ollama/llama3.2')
        system = SovereignSystem(model_name=model_name)
        
        # Run the pipeline
        # Use kickoff with user_query input
        result = system.crew().kickoff(inputs={'user_query': prompt})
        
        # Return the final answer
        return {
            'output': str(result.raw)
        }
    except Exception as e:
        return {
            'error': str(e)
        }
