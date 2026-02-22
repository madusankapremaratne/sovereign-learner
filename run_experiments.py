import os
import sys
import time
import subprocess
import argparse
from typing import List, Dict, Any
from prettytable import PrettyTable
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

EXPERIMENTS = [
    {"id": "EXP01", "name": "Semantic Generalization", "cmd": [sys.executable, "experiments/exp01_semantic_generalization.py", "--cloud", "--queries", "10"]},
    {"id": "EXP02A", "name": "Passive Struggle Detection", "cmd": [sys.executable, "experiments/exp02a_passive_struggle.py"]},
    {"id": "EXP02B", "name": "Complex Query Resolution", "cmd": [sys.executable, "experiments/exp02b_complex_query.py"]},
    {"id": "EXP02C", "name": "Competency Portability", "cmd": [sys.executable, "experiments/exp02c_competency_transfer.py"]},
    {"id": "EXP03", "name": "Model Diversity", "cmd": [sys.executable, "experiments/exp03_model_diversity.py"]},
    {"id": "EXP04", "name": "Agentic Evaluation", "cmd": [sys.executable, "experiments/exp04_agentic_evaluation.py"]},
    {"id": "EXP05", "name": "Promptfoo Red Team", "cmd": ["npx", "promptfoo", "eval", "-c", "experiments/exp05_promptfoo_red_team.yaml"]},
    {"id": "EXP05_ENH", "name": "Enhanced Red Team", "cmd": ["npx", "promptfoo", "eval", "-c", "experiments/exp05_enhanced_red_team.yaml"]},
    {"id": "EXP06", "name": "ARR at Scale", "cmd": [sys.executable, "experiments/exp06_arr_at_scale.py"]},
    {"id": "EXP07", "name": "Preempt & PP-TS comparison", "cmd": [sys.executable, "experiments/exp07_preempt_ppts_comparison.py"]},
    {"id": "EXP08", "name": "NER Coverage Audit", "cmd": [sys.executable, "experiments/exp08_ner_audit.py"]},
    {"id": "EXP08_TEST", "name": "Routing Guardrail Test", "cmd": [sys.executable, "-m", "pytest", "tests/test_conservative_routing_fallback.py"]},
    {"id": "EXP09", "name": "GAMA Comparison", "cmd": [sys.executable, "experiments/exp09_gama_sota_comparison.py"]},
    {"id": "EXP10", "name": "DP Benchmarking", "cmd": [sys.executable, "experiments/exp10_dp_benchmarking.py"]},
    {"id": "EXP11", "name": "Scale Red Teaming", "cmd": ["npx", "promptfoo", "eval", "-c", "experiments/exp11_red_team.yaml"]},
    {"id": "EXP12", "name": "NELR Scan", "cmd": [sys.executable, "experiments/exp12_nelr_scan.py"]},
]

def main():
    parser = argparse.ArgumentParser(description="Run Sovereign Learner Experiments")
    parser.add_argument("--dry-run", action="store_true", help="Print the execution plan without running")
    parser.add_argument("--exp", type=str, help="Comma separated list of experiment IDs to run")
    args = parser.parse_args()

    to_run = EXPERIMENTS
    if args.exp:
        target_ids = [e.strip() for e in args.exp.split(',')]
        to_run = [e for e in EXPERIMENTS if e["id"] in target_ids]

        if not to_run:
            logging.error(f"No valid experiments found for IDs: {args.exp}")
            sys.exit(1)

    if args.dry_run:
        logging.info("DRY RUN: The following experiments would be executed:")
        for idx, exp in enumerate(to_run, 1):
            logging.info(f"  {idx}. [{exp['id']}] {exp['name']}")
            logging.info(f"     Command: {' '.join(exp['cmd'])}")
        return

    results = []
    
    logging.info("==================================================")
    logging.info("🚀 SOVEREIGN LEARNER: EXPERIMENTAL SUITE RUNNER")
    logging.info("==================================================")
    
    for idx, exp in enumerate(to_run, 1):
        logging.info(f"\n[{idx}/{len(to_run)}] Running {exp['id']}: {exp['name']}")
        logging.info(f"Command: {' '.join(exp['cmd'])}")
        
        start_time = time.time()
        try:
            # Execute command
            process = subprocess.run(exp['cmd'], check=False)
            status = "✅ Success" if process.returncode == 0 else f"❌ Failed ({process.returncode})"
        except Exception as e:
            logging.error(f"Error running {exp['id']}: {str(e)}")
            status = "❌ Error"
            
        duration = time.time() - start_time
            
        results.append({
            "ID": exp['id'],
            "Experiment": exp['name'],
            "Status": status,
            "Duration": f"{duration:.2f}s"
        })
        
    # Print Final Table
    logging.info("\n" + "="*60)
    logging.info("📊 OVERALL EXPERIMENT RESULTS SUMMARY")
    logging.info("="*60)
    
    table = PrettyTable()
    table.field_names = ["ID", "Experiment", "Status", "Duration"]
    table.align = "l"
    
    for res in results:
        table.add_row([res["ID"], res["Experiment"], res["Status"], res["Duration"]])
        
    logging.info("\n" + str(table))
    logging.info("\nAll requested experiments have been executed.")

if __name__ == "__main__":
    main()
