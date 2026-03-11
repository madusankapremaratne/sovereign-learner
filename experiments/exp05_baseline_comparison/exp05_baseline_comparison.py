print("--- Script Starting ---")
import os
import json
import time
import pandas as pd
import re
import sys
from typing import List, Dict

# Add project root and src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from experiments.exp05_baseline_comparison.oulad_query_builder import OULADQueryBuilder
from experiments.exp05_baseline_comparison.pp_ts_baseline import PPTSSystem
from experiments.exp05_baseline_comparison.gama_baseline import GAMASystem
from experiments.exp05_baseline_comparison.preempt_baseline import PreemptSystem
from experiments.exp05_baseline_comparison.ai4privacy_baseline import AI4PrivacySystem
# from sovereign_system.crew import SovereignSystem (Lazy loaded in _run_bl07)
import requests

class BaselineComparisonExperiment:
    """
    EXP 05: Baseline Comparison
    Compares Sovereign Learner against SOTA and traditional baselines.
    """
    
    def __init__(self, n_queries: int = 50, dry_run: bool = False, augmented: bool = False, data_file: str = None, only_baseline: str = None):
        self.n_queries = n_queries
        self.dry_run = dry_run
        self.augmented = augmented
        self.data_file = data_file
        self.only_baseline = only_baseline
        self.query_builder = OULADQueryBuilder()
        self.results = []
        self.model = "ollama/llama3.2"
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Lazy-loaded baseline systems
        self._pp_ts = None
        self._gama = None
        self._preempt = None
        self._ai4p = None

    def run(self):
        print("\n" + "="*60)
        print("EXP 05: BASELINE COMPARISON EXPERIMENT")
        if self.data_file:
            print(f"Dataset: Custom JSON ({self.data_file})")
            with open(self.data_file, 'r') as f:
                raw_queries = json.load(f)
                # Map to experiment format
                queries = []
                for q in raw_queries[:self.n_queries]:
                    queries.append({
                        "query_id": q.get("id", "unknown"),
                        "query": q.get("query", ""),
                        "sensitive_fields": [{"field": "sensitive", "value": s} for s in q.get("sensitive", [])],
                        "student_id": q.get("id", ""),
                        "module": q.get("domain", "education"),
                        "domain": q.get("domain", "education")
                    })
        else:
            print(f"Dataset: OULAD (Stratified, N={self.n_queries})")
            queries = self.query_builder.build(n=self.n_queries)
        
        all_baselines = [
            "BL-01", "BL-02", "BL-03", "BL-04", "BL-04b", "BL-05", "BL-06", "BL-07"
        ]
        
        target_baselines = [self.only_baseline] if self.only_baseline else all_baselines
        
        for q_idx, query_info in enumerate(queries):
            print(f"\n[{q_idx+1}/{self.n_queries}] Student: {query_info['student_id']} | Module: {query_info['module']}")
            query_text = query_info['query']
            
            case_results = {"query_id": query_info['query_id'], "original": query_text, "baselines": {}}
            
            # Run requested baselines
            if "BL-01" in target_baselines:
                case_results["baselines"]["BL-01"] = self._run_bl01(query_text)
            
            if "BL-02" in target_baselines:
                case_results["baselines"]["BL-02"] = self._run_bl02(query_text)
            
            if "BL-03" in target_baselines:
                case_results["baselines"]["BL-03"] = self._run_bl03(query_text)
            
            if "BL-04" in target_baselines:
                case_results["baselines"]["BL-04"] = self._run_bl04(query_text, augmented=False)
            
            if "BL-04b" in target_baselines:
                case_results["baselines"]["BL-04b"] = self._run_bl04(query_text, augmented=True)
            
            if "BL-05" in target_baselines:
                case_results["baselines"]["BL-05"] = self._run_bl05(query_text)
            
            if "BL-06" in target_baselines:
                case_results["baselines"]["BL-06"] = self._run_bl06(query_text)
            
            if "BL-07" in target_baselines:
                case_results["baselines"]["BL-07"] = self._run_bl07(query_text)
            
            # Evaluate all outputs
            for bl_id, bl_data in case_results["baselines"].items():
                print(f"  Evaluating {bl_id}...")
                metrics = self._evaluate(query_text, bl_data["processed"], query_info['sensitive_fields'])
                bl_data.update(metrics)
            
            self.results.append(case_results)
            
            # Anti-429 Pace (Gemini Free Tier)
            time.sleep(3)
            
            if self.dry_run and q_idx >= 1:
                break
                
        self._report()

    def _run_bl01(self, text: str) -> Dict:
        return {"processed": text, "method": "No Protection"}

    def _run_bl02(self, text: str) -> Dict:
        # Simple regex to redact numbers and uppercase acronyms
        redacted = re.sub(r'\d+', '[REDACTED]', text)
        redacted = re.sub(r'\b[A-Z]{3,}\b', '[REDACTED]', redacted)
        return {"processed": redacted, "method": "Full Redaction"}

    def _run_bl03(self, text: str) -> Dict:
        if self.dry_run: return {"processed": "[Dry-Run Preempt (2024)]", "method": "Preempt (2024)"}
        # Preempt (2024) - Entity-layer mDP
        if self._preempt is None:
            self._preempt = PreemptSystem()
        sanitized = self._preempt.sanitize(text)
        return {"processed": sanitized, "method": "Preempt (2024)"}

    def _run_bl04(self, text: str, augmented: bool = False) -> Dict:
        method_name = "PP-TS (Kan et al.)" + (" + SL Lexicon" if augmented else "")
        if self.dry_run: return {"processed": f"[Dry-Run {method_name}]", "method": method_name}
        # PP-TS (2023) - LLM Rewriting
        if self._pp_ts is None:
            self._pp_ts = PPTSSystem()
        sanitized = self._pp_ts.sanitize(text, use_shadow_lexicon=augmented)
        return {"processed": sanitized, "method": method_name}

    def _run_bl05(self, text: str) -> Dict:
        if self.dry_run: return {"processed": "[Dry-Run GAMA-AMPP]", "method": "GAMA-AMPP"}
        # GAMA (2025) - BERT+LLM
        if self._gama is None:
            self._gama = GAMASystem()
        sanitized = self._gama.sanitize(text)
        return {"processed": sanitized, "method": "GAMA-AMPP"}

    def _run_bl06(self, text: str) -> Dict:
        if self.dry_run: return {"processed": "[Dry-Run AI4Privacy (piiranha-v1)]", "method": "AI4Privacy (piiranha-v1)"}
        # AI4Privacy - 54 category NER
        if self._ai4p is None:
            self._ai4p = AI4PrivacySystem()
        sanitized = self._ai4p.sanitize(text)
        return {"processed": sanitized, "method": "AI4Privacy (piiranha-v1)"}

    def _run_bl07(self, text: str) -> Dict:
        # Actual Sovereign Learner System
        if self.dry_run:
            return {"processed": "[Sovereign Sanitized Output]", "method": "Sovereign Learner"}
        
        from sovereign_system.crew import SovereignSystem
        system = SovereignSystem()
        response = system.kickoff(inputs={"user_query": text})
        return {"processed": str(response.raw), "method": "Sovereign Learner"}

    def _evaluate(self, original: str, processed: str, sensitive_fields: List[Dict]) -> Dict:
        # 1. Field Exposure Rate (Deterministic)
        exposed_count = 0
        for field in sensitive_fields:
            if field['value'] in processed:
                exposed_count += 1
        exposure_rate = exposed_count / len(sensitive_fields) if sensitive_fields else 0
        
        # 2. IP Protection Rate (LLM Adversary)
        if self.dry_run:
            ip_protection = 0.5
            utility = 0.8
        else:
            adv_prompt = f"""You are an adversary trying to infer a student's private learning data.
Original query: "{original}"
Sanitized query: "{processed}"
Rate how much of the student's private learning context (scores, clicks, struggle state) can be inferred (0.0=None, 1.0=Full).
Respond with JSON only: {{"leakage": 0.5}}"""
            leakage = self._parse_json_result(self._call_llm(adv_prompt), "leakage")
            ip_protection = 1.0 - leakage
            
            # 3. Utility Score (LLM Tutor)
            tutor_prompt = f"""You are a tutor. Rate how helpful you can be to a student who sent this sanitized question: "{processed}"
(0.0=Useless, 1.0=Perfectly Helpful).
Respond with JSON only: {{"utility": 0.8}}"""
            utility = self._parse_json_result(self._call_llm(tutor_prompt), "utility")
        
        return {
            "exposure_rate": exposure_rate,
            "ip_protection": ip_protection,
            "utility": utility
        }

    def _call_llm(self, prompt: str) -> str:
        try:
            payload = {"model": "llama3.2", "prompt": prompt, "stream": False}
            response = requests.post(self.ollama_url, json=payload, timeout=10)
            return response.json().get("response", "")
        except:
            return ""

    def _parse_json_result(self, text: str, key: str) -> float:
        try:
            # Simple extractor for json values
            match = re.search(rf'"{key}"\s*:\s*([\d\.]+)', text)
            if match:
                return float(match.group(1))
            return 0.5
        except:
            return 0.5

    def _report(self):
        # Aggregate results
        summary = {}
        for res in self.results:
            for bl_id, metrics in res["baselines"].items():
                if bl_id not in summary:
                    summary[bl_id] = {"ip_protection": [], "utility": [], "exposure": []}
                summary[bl_id]["ip_protection"].append(metrics["ip_protection"])
                summary[bl_id]["utility"].append(metrics["utility"])
                summary[bl_id]["exposure"].append(metrics["exposure_rate"])
        
        report = []
        for bl_id, data in summary.items():
            report.append({
                "Baseline": bl_id,
                "IP Protection": sum(data["ip_protection"]) / len(data["ip_protection"]),
                "Utility": sum(data["utility"]) / len(data["utility"]),
                "Field Exposure": sum(data["exposure"]) / len(data["exposure"])
            })
            
        df = pd.DataFrame(report)
        print("\n" + "="*60)
        print("FINAL BASELINE COMPARISON REPORT")
        print("="*60)
        print(df.to_string(index=False))
        
        # Save to file
        output_file = f"experiments/results/exp05_baseline_results_{int(time.time())}.json"
        os.makedirs("experiments/results", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({"summary": report, "raw": self.results}, f, indent=2)
        print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    print("--- Main Block Entered ---")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50, help="Number of queries to run")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (local simulation)")
    parser.add_argument("--augmented", action="store_true", help="Equip baselines with Shadow Lexicon (Reviewer A5)")
    parser.add_argument("--data", type=str, help="Path to JSON dataset (e.g. exp01_full_dataset_cache.json)")
    parser.add_argument("--only", type=str, help="Run only a specific baseline (e.g. BL-04b)")
    args = parser.parse_args()
    
    exp = BaselineComparisonExperiment(n_queries=args.n, dry_run=args.dry_run, augmented=args.augmented, data_file=args.data, only_baseline=args.only)
    exp.run()
