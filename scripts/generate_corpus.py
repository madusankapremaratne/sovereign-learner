import json
import logging
import random
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CorpusGenerator:
    """
    Phase 2 (EXP11A): Corpus Expansion Tool
    
    Generates educational queries mapping to OULAD distributions.
    Scales the evaluation set from 500 to 2,000 queries.
    """
    def __init__(self, target_size: int = 2000):
        self.target_size = target_size
        self.domains = ["biomedical", "cs", "legal", "medical"]
        
    def generate_synthetic_query(self, domain: str) -> dict:
        """Mock LLM API Generation for synthetic domains"""
        # In a real run, this hits gpt-4o or ollama to generate queries based on prompts.
        entity = random.choice(["John Doe", "Dr. Smith", "OULAD Dataset v3", "Cas9-G", "AlphaSort"])
        topic = random.choice(["optimization", "data leak", "contract dispute", "clinical trial bias"])
        return {
            "query": f"Can you analyze the {topic} relating to {entity} in the {domain} department?",
            "domain": domain,
            "expected_entities": [entity],
            "sensitivity_type": "DomainIP" if "Cas9" in entity else "PII"
        }

    def run(self):
        logging.info(f"Generating {self.target_size} synthetic educational queries...")
        queries = []
        
        per_domain = self.target_size // len(self.domains)
        
        for domain in self.domains:
            logging.info(f"Generating {per_domain} queries for '{domain}' domain.")
            for _ in range(per_domain):
                queries.append(self.generate_synthetic_query(domain))
        
        # Save Corpus
        os.makedirs("../data", exist_ok=True)
        out_path = "../data/expanded_corpus_2000.json"
        with open(out_path, 'w') as f:
            json.dump(queries, f, indent=4)
            
        logging.info(f"Corpus Expansion Complete! Saved to {out_path}")
        logging.info("Next Step: Ensure Human-in-the-Loop review for 10% of generated queries.")

if __name__ == "__main__":
    generator = CorpusGenerator(target_size=2000)
    generator.run()
