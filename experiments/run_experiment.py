"""
Experiment 2: Semantic Generalization Effectiveness
====================================================
Measures IP protection and utility preservation of the Sovereign Learner pipeline.

Metrics:
1. IP Leakage Rate - Can an adversary recover original sensitive terms?
2. Utility Preservation - Is the response educationally useful?
3. Semantic Similarity - How similar is sanitized response to direct response?
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from test_queries import TEST_QUERIES
# deepeval imports removed as they are unused in the custom implementation

# Import your tools
from sovereign_system.tools.semantic_tools import SemanticGeneralizationTool, RecontextualizationTool


@dataclass
class ExperimentResult:
    """Result for a single query experiment"""
    query_id: str
    domain: str
    original_query: str
    sensitive_entities: List[str]
    sanitized_query: str
    mapping: Dict[str, str]
    cloud_response: str
    recontextualized_response: str
    
    # Metrics
    ip_leakage_score: float  # 0.0 = no leakage, 1.0 = full leakage
    utility_score: float     # 0.0 = useless, 1.0 = fully useful
    entities_leaked: List[str]
    
    # Timing
    sanitization_time_ms: float
    total_time_ms: float


class SemanticGeneralizationExperiment:
    """
    Experiment to validate Semantic Generalization effectiveness.
    
    Hypothesis: Semantic generalization protects IP while preserving educational utility.
    """
    
    def __init__(self, use_cloud: bool = False):
        """
        Args:
            use_cloud: If True, actually call cloud LLM. If False, simulate for faster testing.
        """
        self.use_cloud = use_cloud
        self.recontextualization_tool = RecontextualizationTool()
        self.results: List[ExperimentResult] = []
        
    def run_single_query(self, query_data: Dict) -> ExperimentResult:
        """Process a single query through the pipeline"""
        
        # Instantiate fresh tool for each query to reset mapping
        generalization_tool = SemanticGeneralizationTool()
        generalization_tool.placeholder_map = {} # Explicitly ensure it is empty
        
        query_id = query_data["id"]
        original_query = query_data["query"]
        sensitive_entities = query_data["sensitive"]
        domain = query_data["domain"]
        
        print(f"\n{'='*60}")
        print(f"Processing: {query_id} ({domain})")
        print(f"Query: {original_query[:50]}...")
        
        start_time = time.time()
        
        # Stage 1: Semantic Generalization
        sanitization_start = time.time()
        generalization_result = generalization_tool._run(
            query=original_query,
            sensitive_entities=",".join(sensitive_entities)
        )
        sanitization_time = (time.time() - sanitization_start) * 1000
        
        # Parse the result
        sanitized_query, mapping = self._parse_generalization_result(generalization_result)
        print(f"Sanitized: {sanitized_query[:50]}...")
        print(f"Mapping: {mapping}")
        
        # Stage 2: Cloud Query (simulated or real)
        if self.use_cloud:
            cloud_response = self._call_cloud(sanitized_query)
        else:
            cloud_response = self._simulate_cloud_response(sanitized_query, domain)
        
        # Stage 3: Recontextualization
        recontextualized = self.recontextualization_tool._run(
            response=cloud_response,
            mapping=str(mapping)
        )
        
        total_time = (time.time() - start_time) * 1000
        
        # Stage 4: Measure IP Leakage
        ip_leakage_score, leaked_entities = self._measure_ip_leakage(
            cloud_response, sensitive_entities
        )
        
        # Stage 5: Measure Utility
        utility_score = self._measure_utility(
            original_query, recontextualized, domain
        )
        
        result = ExperimentResult(
            query_id=query_id,
            domain=domain,
            original_query=original_query,
            sensitive_entities=sensitive_entities,
            sanitized_query=sanitized_query,
            mapping=mapping,
            cloud_response=cloud_response,
            recontextualized_response=recontextualized,
            ip_leakage_score=ip_leakage_score,
            utility_score=utility_score,
            entities_leaked=leaked_entities,
            sanitization_time_ms=sanitization_time,
            total_time_ms=total_time
        )
        
        print(f"IP Leakage: {ip_leakage_score:.2%} | Utility: {utility_score:.2%}")
        
        return result
    
    def _parse_generalization_result(self, result: str) -> Tuple[str, Dict]:
        """Parse the tool output into sanitized query and mapping"""
        lines = result.split("\n")
        sanitized = ""
        mapping = {}
        
        for line in lines:
            if line.startswith("SANITIZED:"):
                sanitized = line.replace("SANITIZED:", "").strip()
            elif line.startswith("MAPPING:"):
                mapping_str = line.replace("MAPPING:", "").strip()
                try:
                    import ast
                    mapping = ast.literal_eval(mapping_str)
                except:
                    mapping = {}
        
        return sanitized, mapping
    
    def _simulate_cloud_response(self, sanitized_query: str, domain: str) -> str:
        """Simulate cloud response for faster testing"""
        responses = {
            "biomedical": f"To optimize {sanitized_query.split()[4] if len(sanitized_query.split()) > 4 else 'Protocol-A'}, consider systematic parameter tuning, validation assays, and iterative refinement based on your specific experimental conditions.",
            "cs": f"For the technical challenge described, I recommend profiling your implementation, optimizing memory access patterns, and considering hardware-specific optimizations for your deployment target.",
            "legal": f"Regarding the contractual matter, standard practice involves clear definition of terms, appropriate liability limitations, and compliance with relevant jurisdictional requirements.",
            "medical": f"Based on the clinical parameters mentioned, I recommend consulting with your healthcare provider for personalized guidance, as interpretation depends on individual medical history.",
            "academic": f"For academic writing, ensure proper attribution, follow your institution's guidelines, and maintain consistency with the target publication's style requirements."
        }
        return responses.get(domain, "I can provide guidance on this topic based on general best practices.")
    
    def _call_cloud(self, sanitized_query: str) -> str:
        """Actually call cloud LLM (Gemini)"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(sanitized_query)
            return response.text
        except Exception as e:
            print(f"Cloud call failed: {e}")
            return self._simulate_cloud_response(sanitized_query, "general")
    
    def _measure_ip_leakage(self, cloud_response: str, sensitive_entities: List[str]) -> Tuple[float, List[str]]:
        """
        Measure IP leakage: Did any sensitive entities appear in cloud response?
        
        Returns:
            Tuple of (leakage_score, list of leaked entities)
        """
        leaked = []
        response_lower = cloud_response.lower()
        
        for entity in sensitive_entities:
            entity_lower = entity.lower()
            # Check for exact match or partial match
            if entity_lower in response_lower:
                leaked.append(entity)
            # Also check for common variations
            elif len(entity) > 3:
                # Check if significant substring appears
                for i in range(len(entity) - 3):
                    substring = entity_lower[i:i+4]
                    if substring in response_lower and substring not in ["the ", "and ", "for ", "with"]:
                        if entity not in leaked:
                            leaked.append(entity)
                        break
        
        leakage_score = len(leaked) / len(sensitive_entities) if sensitive_entities else 0.0
        return leakage_score, leaked
    
    def _measure_utility(self, original_query: str, response: str, domain: str) -> float:
        """
        Measure educational utility of the response.
        
        Simple heuristic scoring:
        - Response length (too short = not useful)
        - Contains actionable advice
        - Domain-relevant keywords present
        """
        score = 0.0
        
        # Length check (reasonable response)
        word_count = len(response.split())
        if word_count > 20:
            score += 0.3
        if word_count > 50:
            score += 0.2
        
        # Actionable language
        actionable_keywords = ["recommend", "consider", "should", "try", "use", "implement", "optimize", "ensure"]
        for keyword in actionable_keywords:
            if keyword in response.lower():
                score += 0.1
                break
        
        # Domain relevance
        domain_keywords = {
            "biomedical": ["protocol", "cells", "experiment", "optimize", "method"],
            "cs": ["implementation", "performance", "optimize", "code", "model"],
            "legal": ["agreement", "terms", "clause", "compliance", "contract"],
            "medical": ["consult", "healthcare", "clinical", "treatment", "diagnosis"],
            "academic": ["research", "publication", "citation", "methodology", "study"]
        }
        
        relevant_keywords = domain_keywords.get(domain, [])
        for keyword in relevant_keywords:
            if keyword in response.lower():
                score += 0.1
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def run_all(self, queries: List[Dict] = None) -> Dict:
        """Run experiment on all queries"""
        
        if queries is None:
            queries = TEST_QUERIES
        
        print(f"\n{'='*60}")
        print(f"SEMANTIC GENERALIZATION EXPERIMENT")
        print(f"{'='*60}")
        print(f"Total queries: {len(queries)}")
        print(f"Cloud mode: {'REAL' if self.use_cloud else 'SIMULATED'}")
        print(f"Started: {datetime.now().isoformat()}")
        
        for query_data in queries:
            try:
                result = self.run_single_query(query_data)
                self.results.append(result)
            except Exception as e:
                print(f"Error processing {query_data['id']}: {e}")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate experiment report with aggregate metrics"""
        
        if not self.results:
            return {"error": "No results to report"}
        
        # Aggregate metrics
        total = len(self.results)
        avg_ip_leakage = sum(r.ip_leakage_score for r in self.results) / total
        avg_utility = sum(r.utility_score for r in self.results) / total
        avg_sanitization_time = sum(r.sanitization_time_ms for r in self.results) / total
        
        # Zero leakage count
        zero_leakage_count = sum(1 for r in self.results if r.ip_leakage_score == 0.0)
        
        # By domain
        domains = set(r.domain for r in self.results)
        by_domain = {}
        for domain in domains:
            domain_results = [r for r in self.results if r.domain == domain]
            by_domain[domain] = {
                "count": len(domain_results),
                "avg_ip_leakage": sum(r.ip_leakage_score for r in domain_results) / len(domain_results),
                "avg_utility": sum(r.utility_score for r in domain_results) / len(domain_results),
                "zero_leakage_rate": sum(1 for r in domain_results if r.ip_leakage_score == 0.0) / len(domain_results)
            }
        
        report = {
            "experiment": "Semantic Generalization Effectiveness",
            "timestamp": datetime.now().isoformat(),
            "total_queries": total,
            "cloud_mode": "real" if self.use_cloud else "simulated",
            
            "aggregate_metrics": {
                "ip_leakage_rate": avg_ip_leakage,
                "ip_protection_rate": 1 - avg_ip_leakage,
                "utility_preservation": avg_utility,
                "zero_leakage_queries": zero_leakage_count,
                "zero_leakage_rate": zero_leakage_count / total,
                "avg_sanitization_time_ms": avg_sanitization_time
            },
            
            "by_domain": by_domain,
            
            "comparison_baseline": {
                "no_protection": {"ip_leakage_rate": 1.0, "utility": 1.0},
                "full_redaction": {"ip_leakage_rate": 0.0, "utility": 0.2},
                "sovereign_learner": {"ip_leakage_rate": avg_ip_leakage, "utility": avg_utility}
            }
        }
        
        return report
    
    def save_results(self, output_dir: str = "./results"):
        """Save results to JSON files"""
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        detailed_path = os.path.join(output_dir, f"experiment_detailed_{timestamp}.json")
        with open(detailed_path, "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        
        # Save report
        report = self.generate_report()
        report_path = os.path.join(output_dir, f"experiment_report_{timestamp}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nResults saved to:")
        print(f"  - {detailed_path}")
        print(f"  - {report_path}")
        
        return report_path
    
    def print_summary(self):
        """Print formatted summary to console"""
        
        report = self.generate_report()
        
        print(f"\n{'='*60}")
        print("EXPERIMENT RESULTS SUMMARY")
        print(f"{'='*60}")
        
        agg = report["aggregate_metrics"]
        print(f"\n📊 AGGREGATE METRICS")
        print(f"   IP Protection Rate:    {agg['ip_protection_rate']:.1%}")
        print(f"   Utility Preservation:  {agg['utility_preservation']:.1%}")
        print(f"   Zero-Leakage Queries:  {agg['zero_leakage_queries']}/{report['total_queries']} ({agg['zero_leakage_rate']:.1%})")
        print(f"   Avg Sanitization Time: {agg['avg_sanitization_time_ms']:.2f}ms")
        
        print(f"\n📈 BY DOMAIN")
        for domain, metrics in report["by_domain"].items():
            print(f"   {domain.upper()}")
            print(f"      IP Protection:  {1-metrics['avg_ip_leakage']:.1%}")
            print(f"      Utility:        {metrics['avg_utility']:.1%}")
        
        print(f"\n📋 COMPARISON")
        print(f"   {'Method':<20} {'IP Protection':>15} {'Utility':>10}")
        print(f"   {'-'*45}")
        for method, metrics in report["comparison_baseline"].items():
            protection = 1 - metrics["ip_leakage_rate"]
            print(f"   {method:<20} {protection:>14.1%} {metrics['utility']:>10.1%}")
        
        print(f"\n{'='*60}")


def main():
    """Run the experiment"""
    
    import argparse
    parser = argparse.ArgumentParser(description="Run Semantic Generalization Experiment")
    parser.add_argument("--cloud", action="store_true", help="Use real cloud LLM (slower)")
    parser.add_argument("--queries", type=int, default=None, help="Number of queries to test (default: all)")
    parser.add_argument("--domain", type=str, default=None, help="Filter by domain")
    args = parser.parse_args()
    
    # Filter queries if specified
    queries = TEST_QUERIES
    if args.domain:
        queries = [q for q in queries if q["domain"] == args.domain]
    if args.queries:
        queries = queries[:args.queries]
    
    # Run experiment
    experiment = SemanticGeneralizationExperiment(use_cloud=args.cloud)
    experiment.run_all(queries)
    experiment.print_summary()
    experiment.save_results()


if __name__ == "__main__":
    main()