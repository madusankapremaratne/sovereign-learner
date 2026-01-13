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
        SovereignSystem().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

