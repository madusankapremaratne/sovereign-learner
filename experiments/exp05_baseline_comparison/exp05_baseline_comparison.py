import os
import json
import time
import pandas as pd
import re
from typing import List, Dict
from experiments.exp05_baseline_comparison.oulad_query_builder import OULADQueryBuilder
from experiments.exp05_baseline_comparison.pp_ts_baseline import PPTSSystem
from experiments.exp05_baseline_comparison.gama_baseline import GAMASystem
from experiments.exp05_baseline_comparison.preempt_baseline import PreemptSystem
from experiments.exp05_baseline_comparison.ai4privacy_baseline import AI4PrivacySystem
from sovereign_system.crew import SovereignSystem
import requests

class BaselineComparisonExperiment:
    """
    EXP 05: Baseline Comparison
    Compares Sovereign Learner against SOTA and traditional baselines.
    """
    
    def __init__(self, n_queries: int = 50, dry_run: bool = False):
        self.n_queries = n_queries
        self.dry_run = dry_run
        self.query_builder = OULADQueryBuilder()
        self.results = []
        self.model = "ollama/llama3.2"
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Initialize baseline systems
        self.pp_ts = PPTSSystem()
        self.gama = GAMASystem()
        self.preempt = PreemptSystem()
        self.ai4p = AI4PrivacySystem()

    def run(self):
        print("\n" + "="*60)
        print("EXP 05: BASELINE COMPARISON EXPERIMENT")
        print(f"Dataset: OULAD (Stratified, N={self.n_queries})")
        print("="*60)
        
        queries = self.query_builder.build(n=self.n_queries)
        
        baselines = [
            "BL-01: No Protection",
            "BL-02: Full Redaction",
            "BL-03: Preempt (2024)",
            "BL-04: PP-TS (2023)",
            "BL-05: GAMA (2025)",
            "BL-06: AI4Privacy NER",
            "BL-07: Sovereign Learner"
        ]
        
        for q_idx, query_info in enumerate(queries):
            print(f"\n[{q_idx+1}/{self.n_queries}] Student: {query_info['student_id']} | Module: {query_info['module']}")
            query_text = query_info['query']
            
            case_results = {"query_id": query_info['query_id'], "original": query_text, "baselines": {}}
            
            # BL-01: No Protection
            case_results["baselines"]["BL-01"] = self._run_bl01(query_text)
            
            # BL-02: Full Redaction
            case_results["baselines"]["BL-02"] = self._run_bl02(query_text)
            
            # BL-03: Preempt (Simulated: Targets only specific keywords like Name, Age, Money)
            case_results["baselines"]["BL-03"] = self._run_bl03(query_text)
            
            # BL-04: PP-TS (LLM Rewriting for standard NLP entities)
            case_results["baselines"]["BL-04"] = self._run_bl04(query_text)
            
            # BL-05: GAMA (BERT-NER + LLM Judgment)
            case_results["baselines"]["BL-05"] = self._run_bl05(query_text)
            
            # BL-06: AI4Privacy (DNN-based PII detection)
            case_results["baselines"]["BL-06"] = self._run_bl06(query_text)
            
            # BL-07: Sovereign Learner (Actual Pipeline)
            case_results["baselines"]["BL-07"] = self._run_bl07(query_text)
            
            # Evaluate all outputs
            for bl_id, bl_data in case_results["baselines"].items():
                print(f"  Evaluating {bl_id}...")
                metrics = self._evaluate(query_text, bl_data["processed"], query_info['sensitive_fields'])
                bl_data.update(metrics)
            
            self.results.append(case_results)
            
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
        # Preempt (2024) - Entity-layer mDP
        sanitized = self.preempt.sanitize(text)
        return {"processed": sanitized, "method": "Preempt (2024)"}

    def _run_bl04(self, text: str) -> Dict:
        # PP-TS (2023) - LLM Rewriting
        sanitized = self.pp_ts.sanitize(text)
        return {"processed": sanitized, "method": "PP-TS (Kan et al.)"}

    def _run_bl05(self, text: str) -> Dict:
        # GAMA (2025) - BERT+LLM
        sanitized = self.gama.sanitize(text)
        return {"processed": sanitized, "method": "GAMA-AMPP"}

    def _run_bl06(self, text: str) -> Dict:
        # AI4Privacy - 54 category NER
        sanitized = self.ai4p.sanitize(text)
        return {"processed": sanitized, "method": "AI4Privacy (piiranha-v1)"}

    def _run_bl07(self, text: str) -> Dict:
        # Actual Sovereign Learner System
        if self.dry_run:
            return {"processed": "[Sovereign Sanitized Output]", "method": "Sovereign Learner"}
        
        system = SovereignSystem()
        result = system.crew().kickoff(inputs={"user_query": text})
        return {"processed": str(result), "method": "Sovereign Learner"}

    def _evaluate(self, original: str, processed: str, sensitive_fields: List[Dict]) -> Dict:
        # 1. Field Exposure Rate (Deterministic)
        exposed_count = 0
        for field in sensitive_fields:
            if field['value'] in processed:
                exposed_count += 1
        exposure_rate = exposed_count / len(sensitive_fields) if sensitive_fields else 0
        
        # 2. IP Protection Rate (LLM Adversary)
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
            response = requests.post(self.ollama_url, json=payload, timeout=30)
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5, help="Number of queries to run")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (local simulation)")
    args = parser.parse_args()
    
    exp = BaselineComparisonExperiment(n_queries=args.n, dry_run=args.dry_run)
    exp.run()
