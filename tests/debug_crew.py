
import sys
import os
from crewai import Crew

# Setup path to match dashboard environment
project_root = os.getcwd()
sys.path.insert(0, os.path.join(project_root, "src"))

try:
    from sovereign_system.crew import SovereignSystem
    
    print("Instantiating System...")
    sys_instance = SovereignSystem()
    
    print("Checking Tasks...")
    tasks = sys_instance.tasks
    print(f"Number of tasks found: {len(tasks)}")
    
    for t in tasks:
        print(f"- Task: {t.description[:20]}...")
        # Check if we can access the task details
        
    print("Checking direct method access...")
    if hasattr(sys_instance, 'routing_task'):
        print("✅ routing_task method exists")
        t = sys_instance.routing_task()
        print(f"routing_task returns: {type(t)}")
    else:
        print("❌ routing_task method MISSING")

except Exception as e:
    print(f"❌ Error during debug: {e}")
    import traceback
    traceback.print_exc()
