import sys
import os

# Ensure the project root and src are in sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "src"))

# Inject is_offline_mode into huggingface_hub BEFORE any other imports
try:
    import huggingface_hub
    if not hasattr(huggingface_hub, 'is_offline_mode'):
        def is_offline_mode():
            return os.environ.get("HF_HUB_OFFLINE", "0") in ("1", "true", "yes")
        huggingface_hub.is_offline_mode = is_offline_mode
        print("  🔧 Injected 'is_offline_mode' into huggingface_hub")
except ImportError:
    pass

# Now import the experiment class
from experiments.exp05_baseline_comparison.exp05_baseline_comparison import BaselineComparisonExperiment
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50, help="Number of queries to run")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    args = parser.parse_args()
    
    exp = BaselineComparisonExperiment(n_queries=args.n, dry_run=args.dry_run)
    exp.run()
