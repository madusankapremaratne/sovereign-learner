#!/usr/bin/env python3
import os
import subprocess
import time
import sys
import argparse
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
#  EXPERIMENT CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

EXPERIMENTS = [
    {
        "id": "EXP01",
        "name": "Semantic Generalization",
        "path": "experiments/exp01_semantic_generalization/exp01_semantic_generalization.py",
        "type": "python"
    },
    {
        "id": "EXP02",
        "name": "Hybrid Learning (Passive)",
        "path": "experiments/exp02_hybrid_learning/exp02a_passive_struggle.py",
        "type": "python"
    },
    {
        "id": "EXP03",
        "name": "Model Diversity",
        "path": "experiments/exp03_model_diversity/exp03_model_diversity.py",
        "type": "python"
    },
    {
        "id": "EXP04",
        "name": "Agentic Evaluation",
        "path": "experiments/exp04_agentic_evaluation/exp04_agentic_evaluation.py",
        "type": "python"
    },
    {
        "id": "EXP05",
        "name": "Baseline Comparison",
        "path": "experiments/exp05_baseline_comparison/exp05_baseline_comparison.py",
        "type": "python"
    },
    {
        "id": "EXP06",
        "name": "Red Teaming",
        "path": "experiments/exp06_red_teaming/exp06_red_team.yaml",
        "type": "promptfoo"
    },
    {
        "id": "EXP07",
        "name": "Complex Query Decomposition",
        "path": "experiments/exp07_complex_query_decomposition/exp07_complex_query_decomposition.py",
        "type": "python"
    }
]

# ──────────────────────────────────────────────────────────────────────────────
#  CORE RUNNER LOGIC
# ──────────────────────────────────────────────────────────────────────────────

def run_command(cmd_list, env=None):
    """Executes a command and returns status + duration."""
    start_time = time.time()
    try:
        process = subprocess.run(
            cmd_list,
            env=env,
            check=True,
            capture_output=False # Stream output to console
        )
        status = "✅ PASSED"
    except subprocess.CalledProcessError:
        status = "❌ FAILED"
    except Exception as e:
        status = f"⚠️ ERROR ({str(e)})"
    
    duration = time.time() - start_time
    return status, duration

def main():
    parser = argparse.ArgumentParser(description="Sovereign Learner - Master Experiment Runner")
    parser.add_argument("--n", type=int, help="Number of samples (overrides internal defaults for most scripts)")
    parser.add_argument("--dry-run", action="store_true", help="Run with dry-run flags where supported")
    parser.add_argument("--id", type=str, help="Run only a specific experiment (e.g. EXP05)")
    args = parser.parse_args()

    # Setup Environment
    cwd = os.getcwd()
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{cwd}:{cwd}/src:{env.get('PYTHONPATH', '')}"

    print("\n" + "="*80)
    print("  SOVEREIGN LEARNER: GLOBAL EXPERIMENT SUITE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    results = []
    
    # Filter if specific ID requested
    target_exps = [e for e in EXPERIMENTS if e["id"] == args.id] if args.id else EXPERIMENTS

    if not target_exps:
        print(f"Error: Experiment '{args.id}' not found.")
        return

    for exp in target_exps:
        print(f"\n🚀 [RUNNING] {exp['id']}: {exp['name']}")
        print(f"   Path: {exp['path']}")
        print("-" * 40)

        cmd = []
        if exp["type"] == "python":
            cmd = [sys.executable, exp["path"]]
            if args.n:
                cmd.extend(["--n", str(args.n)])
            if args.dry_run:
                cmd.append("--dry-run")
        elif exp["type"] == "promptfoo":
            cmd = ["npx", "promptfoo", "eval", "-c", exp["path"]]
            # Note: promptfoo doesn't natively take --n or --dry-run the same way, 
            # but we could add flags if needed.
        
        status, duration = run_command(cmd, env=env)
        
        results.append({
            "id": exp["id"],
            "name": exp["name"],
            "status": status,
            "duration": f"{duration:.1f}s"
        })

    # Output Summary Table
    print("\n" + "="*80)
    print("  EXPERIMENT SUMMARY REPORT")
    print("="*80)
    print(f"{'ID':<10} {'Name':<35} {'Status':<15} {'Duration':<10}")
    print("-" * 80)
    for res in results:
        print(f"{res['id']:<10} {res['name']:<35} {res['status']:<15} {res['duration']:<10}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
