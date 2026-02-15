
import os
import sys
from dotenv import load_dotenv

# Setup path
project_root = os.getcwd()
sys.path.insert(0, os.path.join(project_root, "src"))

# Load env
load_dotenv(".env")

try:
    from sovereign_system.crew import SovereignSystem
    
    print("🚀 Initializing Sovereign System for End-to-End Verification...")
    
    # Initialize system without tracer first
    sovereign_system = SovereignSystem()
    sovereign_crew = sovereign_system.crew()
    
    query = "How do I optimize my CRISPR protocol for HEK293 cells?"
    print(f"\n📝 Test Query: {query}")
    print("⏳ Starting execution (this may take a minute)...")
    
    result = sovereign_crew.kickoff(inputs={'user_query': query})
    
    print("\n✅ Execution Successful!")
    print("\n--- Final Result ---")
    print(result)
    print("--------------------")

except Exception as e:
    print(f"\n❌ Execution Failed: {e}")
    import traceback
    traceback.print_exc()
