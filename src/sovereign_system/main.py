#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from sovereign_system.crew import SovereignSystem

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'query': 'How do I optimize my CRISPR protocol for HEK293?',
        'current_year': str(datetime.now().year)
    }

    try:
        # Pre-flight Security Check (Guardrails)
        from sovereign_system.security.guard import guard
        is_safe, msg, threats = guard.validate_input(inputs['query'])
        
        if not is_safe:
            print(f"🚨 SECURITY ALERT: {msg}")
            print(f"Threats: {threats}")
            return # Block execution

        SovereignSystem().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

