import json
import logging
import os
import argparse
from typing import List, Dict, Tuple
from tqdm import tqdm

try:
    from presidio_analyzer import AnalyzerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NELRScanner:
    """
    Experiment 12: Novel Entity Leakage Rate (NELR) Post-hoc Scan
    
    Identifies 'Response-Induced Leakage' where the cloud model introduces 
    sensitive entities in its response that were absent from the sanitized query.
    Detects Hallucinations and Semantic Inferences.
    """
    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
        else:
            logging.warning("Presidio not available. NELR scan will use fallback keyword matching.")
            self.analyzer = None

    def scan_response(self, response: str, original_entities: List[str]) -> Tuple[List[str], bool]:
        """Scans a single response for novel entities not in the original mapping."""
        detected = []
        if self.analyzer:
            analysis = self.analyzer.analyze(text=response, language='en')
            # Extract unique texts
            detected = list(set([response[res.start:res.end] for res in analysis]))
        else:
            # Fallback simple scan
            import re
            sensitive_patterns = [r"\bSSN\b", r"\bHEK\d*\b", r"\bpatient\b"]
            for pat in sensitive_patterns:
                matches = re.findall(pat, response, re.IGNORECASE)
                detected.extend(matches)
        
        novel_entities = [ent for ent in detected if ent not in original_entities]
        return novel_entities, len(novel_entities) > 0

    def run_scan(self):
        logging.info("Starting Novel Entity Leakage Rate (NELR) Scan...")
        total_responses = 0
        leakage_count = 0
        novel_entities_found = []

        # Find result json files
        for filename in os.listdir(self.results_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Assuming data is a list of query execution results
                    for record in tqdm(data, desc=f"Scanning {filename}"):
                        total_responses += 1
                        cloud_response = record.get("cloud_response", "")
                        original_entities = record.get("original_entities", [])
                        
                        novel_entities, has_leakage = self.scan_response(cloud_response, original_entities)
                        
                        if has_leakage:
                            leakage_count += 1
                            novel_entities_found.extend(novel_entities)
                            
                except Exception as e:
                    logging.error(f"Error processing {filename}: {e}")
        
        nelr_rate = (leakage_count / total_responses) * 100 if total_responses > 0 else 0
        
        logging.info("-" * 40)
        logging.info(f"NELR Scan Complete")
        logging.info(f"Total Responses Scanned: {total_responses}")
        logging.info(f"Responses with Novel Leakage: {leakage_count}")
        logging.info(f"NELR (Novel Entity Leakage Rate): {nelr_rate:.2f}%")
        logging.info(f"Sample Novel Entities: {list(set(novel_entities_found))[:10]}")
        logging.info("-" * 40)
        
        # Save report
        report_path = os.path.join(self.results_dir, "exp12_nelr_report.json")
        with open(report_path, 'w') as f:
            json.dump({
                "total_responses": total_responses,
                "leakage_count": leakage_count,
                "nelr_percentage": nelr_rate,
                "novel_entities_found": list(set(novel_entities_found))
            }, f, indent=4)
        logging.info(f"Report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EXP12 NELR Scan")
    parser.add_argument("--results-dir", type=str, default="../results", help="Directory with execution results")
    args = parser.parse_args()
    
    scanner = NELRScanner(args.results_dir)
    scanner.run_scan()
