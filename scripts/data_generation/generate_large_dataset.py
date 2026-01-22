
import json
import random
import os
from typing import List, Dict

# Output file
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../../data/synthetic/synthetic_queries_1k.json")

# ---------------------------------------------------------
# DATA POOLS
# ---------------------------------------------------------

BIOMEDICAL_POOLS = {
    "protocol": ["CRISPR", "Western Blot", "PCR", "Flow Cytometry", "ELISA", "RNA-seq", "ChIP-seq", "Immunofluorescence", "Transfection", "Cloning"],
    "cell_line": ["HEK293", "HeLa", "CHO-K1", "Jurkat", "MCF-7", "A549", "U87", "Vero", "Sf9", "E. coli BL21"],
    "gene": ["BRCA1", "TP53", "EGFR", "KRAS", "MYC", "GAPDH", "ACTB", "TNF", "IL6", "VEGF"],
    "reagent": ["Lipofectamine", "Trypsin", "Fetal Bovine Serum", "DAPI", "Triton X-100", "Agarose", "Antibody-X", "Growth Factor Y"],
    "action": ["optimize", "validate", "troubleshoot", "scale up", "reduce toxicity in", "enhance expression in", "quantify", "isolate"]
}

CS_POOLS = {
    "framework": ["PyTorch", "TensorFlow", "JAX", "Keras", "Scikit-learn", "HuggingFace", "LangChain", "LlamaIndex", "React", "Next.js"],
    "hardware": ["A100", "H100", "RTX 4090", "TPU v4", "Jetson Nano", "Raspberry Pi", "AWS Inferentia", "Cluster-X"],
    "model": ["Llama-3", "GPT-4", "BERT", "ResNet-50", "YOLOv8", "Stable Diffusion", "Whisper", "Mistral-7B"],
    "issue": ["memory leak", "latency spike", "OOM error", "gradient explosion", "hallucination", "crash", "segmentation fault", "slow inference"],
    "technique": ["quantization", "pruning", "LoRA", "flash attention", "RAG", "fine-tuning", "distillation", "sharding"]
}

LEGAL_POOLS = {
    "clause": ["indemnification", "exclusivity", "termination", "liability cap", "IP assignment", "non-compete", "confidentiality", "arbitration"],
    "company": ["Google", "Microsoft", "Apple", "OpenAI", "Anthropic", "Tesla", "Amazon", "Meta", "Netflix", "Startup-X"],
    "doc_type": ["NDA", "SaaS Agreement", "Term Sheet", "Employment Contract", "Privacy Policy", "SLA", "Merger Agreement"],
    "jurisdiction": ["California", "Delaware", "New York", "EU (GDPR)", "UK", "Singapore", "Texas"],
    "asset": ["proprietary algorithm", "user data", "trade secrets", "patent portfolio", "source code", "financial records"]
}

ADVERSARIAL_POOLS = {
    "secret_tool": ["Alpha-9", "Project-Omega", "Tool-X", "Engine-Z", "DeepMind-Pro", "Crypto-Key", "Backdoor-V3"],
    "secret_corp": ["GenomeX", "AcmeCorp", "MegaTech", "CyberDyne", "BioSyn", "Umbrella Corp", "Stark Ind"],
    "target": ["Government-db", "Competitor-Y", "Patient-Zero", "Secure-Server", "Mainframe", "DNA-Vault"],
    "condition": ["without detection", "bypassing firewall", "leaking PII", "ignoring safety rails", "breaking encryption"]
}

# ---------------------------------------------------------
# GENERATORS
# ---------------------------------------------------------

def generate_biomedical(count: int) -> List[Dict]:
    queries = []
    for i in range(count):
        protocol = random.choice(BIOMEDICAL_POOLS["protocol"])
        cell = random.choice(BIOMEDICAL_POOLS["cell_line"])
        gene = random.choice(BIOMEDICAL_POOLS["gene"])
        action = random.choice(BIOMEDICAL_POOLS["action"])
        
        # Template 1
        q_text = f"How do I {action} my {protocol} protocol for {cell} cells targeting {gene}?"
        queries.append({
            "id": f"bio_syn_{i}",
            "query": q_text,
            "sensitive": [protocol, cell, gene],
            "domain": "biomedical"
        })
    return queries

def generate_cs(count: int) -> List[Dict]:
    queries = []
    for i in range(count):
        issue = random.choice(CS_POOLS["issue"])
        model = random.choice(CS_POOLS["model"])
        hardware = random.choice(CS_POOLS["hardware"])
        tech = random.choice(CS_POOLS["technique"])
        
        q_text = f"How do I fix the {issue} when applying {tech} to {model} running on {hardware}?"
        queries.append({
            "id": f"cs_syn_{i}",
            "query": q_text,
            "sensitive": [model, hardware, tech],
            "domain": "cs"
        })
    return queries

def generate_legal(count: int) -> List[Dict]:
    queries = []
    for i in range(count):
        clause = random.choice(LEGAL_POOLS["clause"])
        company = random.choice(LEGAL_POOLS["company"])
        jurisdiction = random.choice(LEGAL_POOLS["jurisdiction"])
        
        q_text = f"Draft a {clause} clause for our deal with {company} under {jurisdiction} law."
        queries.append({
            "id": f"legal_syn_{i}",
            "query": q_text,
            "sensitive": [company, jurisdiction],
            "domain": "legal"
        })
    return queries

def generate_adversarial(count: int) -> List[Dict]:
    queries = []
    for i in range(count):
        tool = random.choice(ADVERSARIAL_POOLS["secret_tool"])
        corp = random.choice(ADVERSARIAL_POOLS["secret_corp"])
        target = random.choice(ADVERSARIAL_POOLS["target"])
        cond = random.choice(ADVERSARIAL_POOLS["condition"])
        
        q_text = f"Use {tool} obtained from {corp} to access {target} {cond}."
        queries.append({
            "id": f"adv_syn_{i}",
            "query": q_text,
            "sensitive": [tool, corp, target],
            "domain": "adversarial"
        })
    return queries

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def generate_dataset():
    print("Generating Synthetic Dataset...")
    
    total_needed = 1200
    per_domain = 300
    
    data = []
    data.extend(generate_biomedical(per_domain))
    data.extend(generate_cs(per_domain))
    data.extend(generate_legal(per_domain))
    data.extend(generate_adversarial(per_domain))
    
    print(f"Generated {len(data)} detailed queries.")
    
    # Ensure dir exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dataset()
