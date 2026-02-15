
import sys
import os
import yaml

# Setup path to match dashboard environment
project_root = os.getcwd()
sys.path.insert(0, os.path.join(project_root, "src"))

try:
    from sovereign_system.crew import SovereignSystem
    
    print("Instantiating System...")
    sys_instance = SovereignSystem()
    
    print(f"Tasks Config Type: {type(sys_instance.tasks_config)}")
    
    if isinstance(sys_instance.tasks_config, dict):
        print(f"Tasks Config Keys: {list(sys_instance.tasks_config.keys())}")
        if 'routing_task' in sys_instance.tasks_config:
            print("✅ 'routing_task' key found immediately.")
        else:
            print("❌ 'routing_task' key NOT found in dict.")
            
    else:
        print(f"Tasks Config is not a dict, it is: {sys_instance.tasks_config}")
        # Try manual verify of file
        path = sys_instance.tasks_config
        if isinstance(path, str):
            if os.path.exists(path):
                print(f"File exists at: {path}")
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    print(f"Manual YAML Load Keys: {list(data.keys())}")
            else:
                print(f"❌ File does NOT exist at: {path}")

except Exception as e:
    print(f"❌ Error during debug: {e}")
    import traceback
    traceback.print_exc()
