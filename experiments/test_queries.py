
"""
Test Queries Dataset for Semantic Generalization Experiment
============================================================
50 queries across 5 domains to validate IP protection + utility preservation
"""

TEST_QUERIES = [
    # ===========================================
    # BIOMEDICAL RESEARCH (15 queries)
    # ===========================================
    {
        "id": "bio_01",
        "query": "How do I optimize my CRISPR protocol for HEK293 cells?",
        "sensitive": ["CRISPR", "HEK293"],
        "domain": "biomedical"
    },
    {
        "id": "bio_02",
        "query": "What's the best transfection method for CHO-K1 cells?",
        "sensitive": ["CHO-K1"],
        "domain": "biomedical"
    },
    {
        "id": "bio_03",
        "query": "How do I increase EGFR expression in my HeLa experiment?",
        "sensitive": ["EGFR", "HeLa"],
        "domain": "biomedical"
    },
    {
        "id": "bio_04",
        "query": "What concentration of Lipofectamine 3000 works best for primary neurons?",
        "sensitive": ["Lipofectamine 3000", "primary neurons"],
        "domain": "biomedical"
    },
    {
        "id": "bio_05",
        "query": "How do I validate BRCA1 knockout efficiency in MCF-7 cells?",
        "sensitive": ["BRCA1", "MCF-7"],
        "domain": "biomedical"
    },
    {
        "id": "bio_06",
        "query": "What's the optimal MOI for AAV9 transduction in cardiomyocytes?",
        "sensitive": ["AAV9", "cardiomyocytes"],
        "domain": "biomedical"
    },
    {
        "id": "bio_07",
        "query": "How do I reduce off-target effects in my Cas9-based gene editing?",
        "sensitive": ["Cas9"],
        "domain": "biomedical"
    },
    {
        "id": "bio_08",
        "query": "What's the best protocol for isolating exosomes from patient serum samples?",
        "sensitive": ["exosomes", "patient serum"],
        "domain": "biomedical"
    },
    {
        "id": "bio_09",
        "query": "How do I maintain pluripotency in my iPSC differentiation protocol?",
        "sensitive": ["iPSC"],
        "domain": "biomedical"
    },
    {
        "id": "bio_10",
        "query": "What antibody dilution works best for TP53 Western blot in A549 cells?",
        "sensitive": ["TP53", "A549"],
        "domain": "biomedical"
    },
    {
        "id": "bio_11",
        "query": "How do I optimize my CAR-T construct for CD19 targeting?",
        "sensitive": ["CAR-T", "CD19"],
        "domain": "biomedical"
    },
    {
        "id": "bio_12",
        "query": "What's the best fixation method for confocal imaging of mitochondria?",
        "sensitive": ["mitochondria", "confocal"],
        "domain": "biomedical"
    },
    {
        "id": "bio_13",
        "query": "How do I validate my shRNA knockdown of KRAS in pancreatic organoids?",
        "sensitive": ["shRNA", "KRAS", "pancreatic organoids"],
        "domain": "biomedical"
    },
    {
        "id": "bio_14",
        "query": "What's the optimal passage number for maintaining SH-SY5Y neuroblastoma cells?",
        "sensitive": ["SH-SY5Y", "neuroblastoma"],
        "domain": "biomedical"
    },
    {
        "id": "bio_15",
        "query": "How do I reduce immunogenicity in my mRNA vaccine formulation?",
        "sensitive": ["mRNA vaccine"],
        "domain": "biomedical"
    },

    # ===========================================
    # COMPUTER SCIENCE / AI RESEARCH (15 queries)
    # ===========================================
    {
        "id": "cs_01",
        "query": "How do I fix the memory leak in my CUDA kernel for TensorRT inference?",
        "sensitive": ["CUDA", "TensorRT"],
        "domain": "cs"
    },
    {
        "id": "cs_02",
        "query": "What's the best way to optimize my BERT fine-tuning on domain-specific data?",
        "sensitive": ["BERT"],
        "domain": "cs"
    },
    {
        "id": "cs_03",
        "query": "How do I implement gradient checkpointing for my LLaMA fine-tuning?",
        "sensitive": ["LLaMA"],
        "domain": "cs"
    },
    {
        "id": "cs_04",
        "query": "What's the optimal batch size for distributed training on 8x A100 GPUs?",
        "sensitive": ["A100"],
        "domain": "cs"
    },
    {
        "id": "cs_05",
        "query": "How do I reduce hallucinations in my RAG pipeline using ChromaDB?",
        "sensitive": ["RAG", "ChromaDB"],
        "domain": "cs"
    },
    {
        "id": "cs_06",
        "query": "What's the best tokenizer configuration for multilingual T5 training?",
        "sensitive": ["T5"],
        "domain": "cs"
    },
    {
        "id": "cs_07",
        "query": "How do I implement LoRA adapters for Stable Diffusion XL?",
        "sensitive": ["LoRA", "Stable Diffusion XL"],
        "domain": "cs"
    },
    {
        "id": "cs_08",
        "query": "What's the optimal learning rate schedule for GPT-2 pretraining?",
        "sensitive": ["GPT-2"],
        "domain": "cs"
    },
    {
        "id": "cs_09",
        "query": "How do I debug NaN losses in my PyTorch transformer implementation?",
        "sensitive": ["PyTorch", "transformer"],
        "domain": "cs"
    },
    {
        "id": "cs_10",
        "query": "What's the best way to quantize my Whisper model for edge deployment?",
        "sensitive": ["Whisper"],
        "domain": "cs"
    },
    {
        "id": "cs_11",
        "query": "How do I optimize vLLM inference for my Mistral-7B deployment?",
        "sensitive": ["vLLM", "Mistral-7B"],
        "domain": "cs"
    },
    {
        "id": "cs_12",
        "query": "What's the optimal chunk size for my LangChain document processing?",
        "sensitive": ["LangChain"],
        "domain": "cs"
    },
    {
        "id": "cs_13",
        "query": "How do I implement flash attention in my custom CUDA kernel?",
        "sensitive": ["flash attention", "CUDA"],
        "domain": "cs"
    },
    {
        "id": "cs_14",
        "query": "What's the best embedding model for my Pinecone vector search?",
        "sensitive": ["Pinecone"],
        "domain": "cs"
    },
    {
        "id": "cs_15",
        "query": "How do I reduce inference latency in my ONNX Runtime deployment?",
        "sensitive": ["ONNX Runtime"],
        "domain": "cs"
    },

    # ===========================================
    # LEGAL / BUSINESS (10 queries)
    # ===========================================
    {
        "id": "legal_01",
        "query": "How should I structure the IP clause for our Series A with Sequoia?",
        "sensitive": ["Series A", "Sequoia"],
        "domain": "legal"
    },
    {
        "id": "legal_02",
        "query": "What's the best way to negotiate the liquidation preference with Andreessen Horowitz?",
        "sensitive": ["liquidation preference", "Andreessen Horowitz"],
        "domain": "legal"
    },
    {
        "id": "legal_03",
        "query": "How do I structure employee stock options for my YCombinator startup?",
        "sensitive": ["stock options", "YCombinator"],
        "domain": "legal"
    },
    {
        "id": "legal_04",
        "query": "What indemnification clauses should I include in our Microsoft partnership?",
        "sensitive": ["indemnification", "Microsoft"],
        "domain": "legal"
    },
    {
        "id": "legal_05",
        "query": "How do I protect our trade secrets when hiring from Google?",
        "sensitive": ["trade secrets", "Google"],
        "domain": "legal"
    },
    {
        "id": "legal_06",
        "query": "What's the standard vesting schedule for co-founders at seed stage?",
        "sensitive": ["vesting", "seed stage"],
        "domain": "legal"
    },
    {
        "id": "legal_07",
        "query": "How should I structure the data processing agreement for GDPR compliance?",
        "sensitive": ["GDPR"],
        "domain": "legal"
    },
    {
        "id": "legal_08",
        "query": "What's the best approach to patent our novel algorithm before publishing?",
        "sensitive": ["patent", "algorithm"],
        "domain": "legal"
    },
    {
        "id": "legal_09",
        "query": "How do I negotiate exclusivity terms with our Salesforce integration?",
        "sensitive": ["exclusivity", "Salesforce"],
        "domain": "legal"
    },
    {
        "id": "legal_10",
        "query": "What non-compete terms are enforceable for employees in California?",
        "sensitive": ["non-compete", "California"],
        "domain": "legal"
    },

    # ===========================================
    # MEDICAL / CLINICAL (5 queries)
    # ===========================================
    {
        "id": "med_01",
        "query": "I'm patient John Smith, ID 78432. How do I interpret my HbA1c results of 7.2%?",
        "sensitive": ["John Smith", "78432", "HbA1c", "7.2%"],
        "domain": "medical"
    },
    {
        "id": "med_02",
        "query": "What are the contraindications for Metformin given my eGFR of 45?",
        "sensitive": ["Metformin", "eGFR", "45"],
        "domain": "medical"
    },
    {
        "id": "med_03",
        "query": "How should I adjust my Warfarin dose with an INR of 3.8?",
        "sensitive": ["Warfarin", "INR", "3.8"],
        "domain": "medical"
    },
    {
        "id": "med_04",
        "query": "What's the recommended Humira dosing for my Crohn's disease?",
        "sensitive": ["Humira", "Crohn's disease"],
        "domain": "medical"
    },
    {
        "id": "med_05",
        "query": "How do I interpret my positive ANA test with 1:640 titer?",
        "sensitive": ["ANA", "1:640"],
        "domain": "medical"
    },

    # ===========================================
    # EDUCATIONAL / ACADEMIC (5 queries)
    # ===========================================
    {
        "id": "edu_01",
        "query": "How do I cite the unpublished findings from Professor Chen's lab at Stanford?",
        "sensitive": ["Professor Chen", "Stanford", "unpublished"],
        "domain": "academic"
    },
    {
        "id": "edu_02",
        "query": "What's the best way to structure my thesis chapter on MIT's quantum computing research?",
        "sensitive": ["MIT", "quantum computing"],
        "domain": "academic"
    },
    {
        "id": "edu_03",
        "query": "How do I respond to Reviewer 2's criticism of our Nature submission?",
        "sensitive": ["Reviewer 2", "Nature"],
        "domain": "academic"
    },
    {
        "id": "edu_04",
        "query": "What statistical test should I use for my Oxford longitudinal study data?",
        "sensitive": ["Oxford", "longitudinal study"],
        "domain": "academic"
    },
    {
        "id": "edu_05",
        "query": "How do I acknowledge the NIH R01 grant in my publication?",
        "sensitive": ["NIH", "R01"],
        "domain": "academic"
    },
]

# Summary statistics
DOMAIN_COUNTS = {
    "biomedical": 15,
    "cs": 15,
    "legal": 10,
    "medical": 5,
    "academic": 5
}

def get_queries_by_domain(domain: str) -> list:
    """Filter queries by domain"""
    return [q for q in TEST_QUERIES if q["domain"] == domain]

def get_all_sensitive_entities() -> list:
    """Extract all unique sensitive entities"""
    entities = []
    for q in TEST_QUERIES:
        entities.extend(q["sensitive"])
    return list(set(entities))

if __name__ == "__main__":
    print(f"Total queries: {len(TEST_QUERIES)}")
    print(f"Domains: {DOMAIN_COUNTS}")
    print(f"Unique sensitive entities: {len(get_all_sensitive_entities())}")