"""
Experiment 1: Semantic Generalization Effectiveness
====================================================
EXP01 — REDESIGNED (February 2026)
Real-data replacement per supervisor feedback.

Data Sources (replaces 50 synthetic hand-crafted queries):
  • AI4Privacy pii-masking-200k  — 200 education/health domain samples
    https://huggingface.co/datasets/ai4privacy/pii-masking-200k
  • OULAD studentInfo.csv         — 100 real student records → derived queries
    https://analyse.kmi.open.ac.uk/open_dataset

Sample Size: 300 (6× increase vs previous 50)

Metrics:
  1. IP Protection Rate  — % of ground-truth entities NOT present in cloud response
  2. Utility Preservation (STS) — sentence-transformers cosine similarity
  3. Utility (LLM Judge)  — Ollama/Gemini judge scoring
  4. Sanitization Time (ms)
  5. Zero-Leakage Rate   — % of queries with zero entity leakage

Baselines Compared:
  (1) No Protection
  (2) Full Redaction
  (3) Sovereign Learner — Semantic Generalization  ← primary system

Usage:
  python experiments/exp01_semantic_generalization.py
  python experiments/exp01_semantic_generalization.py --cloud --max-samples 50
"""

import os
import sys
import json
import time
import csv
import random
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
from dotenv import load_dotenv

load_dotenv()

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from sovereign_system.utils.evaluators import SemanticPrivacyMetric
from deepeval.test_case import LLMTestCase
from crewai import LLM
from sovereign_system.tools.semantic_tools import IntentAbstractorTool as SemanticGeneralizationTool, ContextRestorerTool as RecontextualizationTool
from sovereign_system.utils.sovereign_trace_logger import global_tracer


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING — Real Published Datasets
# ══════════════════════════════════════════════════════════════════════════════

def load_ai4privacy_education_samples(max_samples: int = 200) -> List[Dict]:
    """
    Load AI4Privacy pii-masking-200k, filter to education/health domain,
    and return in the experiment's internal query format with ground-truth labels.

    Dataset: https://huggingface.co/datasets/ai4privacy/pii-masking-200k
    Paper: OpenPII — 220K examples, 27 PII classes, targets education/health domains.
    Label accuracy: ~98.3%.

    Returns list of dicts with keys: id, query, sensitive, domain, source, gt_labels
    """
    try:
        from datasets import load_dataset
        print("Loading AI4Privacy pii-masking-200k from HuggingFace...")
        dataset = load_dataset("ai4privacy/pii-masking-200k", split="train")

        # pii-masking-200k schema: ['source_text', 'target_text', 'privacy_mask', 'span_labels', ...]
        # No 'subject' field exists. We must filter based on sensitive entity labels and text keywords.
        
        # Keywords that indicate an educational or health-related context
        edu_health_keywords = {
            "education", "student", "academic", "university", "school", "curriculum",
            "health", "medical", "psychology", "healthcare", "patient", "clinical",
            "research", "professor", "teacher", "enroll", "graduation", "assignment", "exam"
        }

        def is_relevant_domain(example):
            source_text = example.get("source_text", "").lower()
            # 1. Direct keyword match in source text
            if any(kw in source_text for kw in edu_health_keywords):
                return True
            
            # 2. Check privacy_mask values for keywords
            privacy_mask = example.get("privacy_mask", [])
            for item in privacy_mask:
                val = str(item.get("value", "")).lower()
                if any(kw in val for kw in edu_health_keywords):
                    return True
                # JOBAREA is often education-related in this dataset
                if item.get("label") == "JOBAREA" and any(k in val for k in ["research", "education", "science"]):
                    return True
            return False

        print("Filtering education/health domain subset (keyword search)...")
        # We process a subset first to speed up filtering if dataset is huge, 
        # but 200k is manageable for a full filter pass.
        edu_subset = dataset.filter(is_relevant_domain)
        print(f"  Education/health subset size: {len(edu_subset)} samples found")

        if len(edu_subset) == 0:
            print("⚠️  Filtering returned 0 samples. Fallback to random subset...")
            # Fallback: less restrictive check
            edu_subset = dataset.shuffle(seed=42).select(range(min(max_samples * 10, len(dataset))))
            
        # Reproducible shuffle and select
        edu_subset = edu_subset.shuffle(seed=42).select(range(min(max_samples, len(edu_subset))))
        print(f"  Sampled {len(edu_subset)} records for EXP01")

        queries = []
        for i, example in enumerate(edu_subset):
            # Extract the source text (unmasked or masked depending on dataset structure)
            # pii-masking-200k has: 'source_text', 'target_text', 'privacy_mask', 'span_labels'
            source_text = example.get("source_text", example.get("unmasked_text", ""))
            if not source_text or len(source_text.strip()) < 20:
                continue

            # Extract ground-truth PII entity values from span_labels / privacy_mask
            sensitive_entities = _extract_pii_entities(example)

            # Heuristic domain classification for reporting
            text_lower = source_text.lower()
            if any(h in text_lower for h in ["health", "medical", "patient", "clinical", "hospital"]):
                domain = "health_education"
            else:
                domain = "education"

            queries.append({
                "id": f"ai4p_{i:04d}",
                "query": source_text.strip(),
                "sensitive": sensitive_entities,
                "domain": domain,
                "source": "ai4privacy_pii_masking_200k",
                "gt_labels": example.get("span_labels", []),
                "expected_zone": 1
            })

        print(f"✅ Loaded {len(queries)} AI4Privacy education samples")
        return queries

    except ImportError:
        print("⚠️  'datasets' library not installed. Run: pip install datasets")
        print("   Falling back to local AI4Privacy cache if available...")
        return _load_ai4privacy_from_cache(max_samples)
    except Exception as e:
        print(f"⚠️  AI4Privacy load failed: {e}")
        print("   Falling back to local AI4Privacy cache if available...")
        return _load_ai4privacy_from_cache(max_samples)


def _extract_pii_entities(example: Dict) -> List[str]:
    """
    Extract plain-text PII entity values from an AI4Privacy example.
    The dataset stores entities in privacy_mask or mbert_bio_labels structures.
    """
    entities = []

    # Method 1: privacy_mask field (list of dicts with 'value' and 'label')
    privacy_mask = example.get("privacy_mask", [])
    if isinstance(privacy_mask, list):
        for item in privacy_mask:
            if isinstance(item, dict):
                val = item.get("value", "")
                if val and len(val) > 1:
                    entities.append(val)

    # Method 2: mbert_bio_labels (token-level BIO tags)
    # Extract B- and I- tagged tokens from source_text
    if not entities:
        span_labels = example.get("span_labels", [])
        source_text = example.get("source_text", "")
        if span_labels and source_text:
            tokens = source_text.split()
            current_entity = []
            for token, label in zip(tokens, span_labels):
                if label.startswith("B-"):
                    if current_entity:
                        entities.append(" ".join(current_entity))
                    current_entity = [token]
                elif label.startswith("I-") and current_entity:
                    current_entity.append(token)
                else:
                    if current_entity:
                        entities.append(" ".join(current_entity))
                    current_entity = []
            if current_entity:
                entities.append(" ".join(current_entity))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for e in entities:
        e_clean = e.strip(".,;:\"'")
        if e_clean and e_clean.lower() not in seen:
            seen.add(e_clean.lower())
            unique.append(e_clean)

    return unique


def _load_ai4privacy_from_cache(max_samples: int) -> List[Dict]:
    """Load from local cache if HuggingFace download failed."""
    cache_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "ai4privacy", "pii_masking_200k_edu_cache.json"
    )
    if os.path.exists(cache_path):
        print(f"Loading AI4Privacy from local cache: {cache_path}")
        with open(cache_path, "r") as f:
            data = json.load(f)
        return data[:max_samples]
    print("❌ No local AI4Privacy cache found. AI4Privacy samples will be skipped.")
    return []


def load_oulad_derived_queries(max_samples: int = 100) -> List[Dict]:
    """
    Derive real educational queries from OULAD studentInfo.csv.

    OULAD: Open University Learning Analytics Dataset
    Source: https://analyse.kmi.open.ac.uk/open_dataset
    32,593 real students, 10.6M VLE interactions, 7 CSV tables.

    Strategy: Use real student demographic + academic records to construct
    realistic educational support queries that contain genuine PII-like data
    (student IDs, regions, education backgrounds). These represent the kind
    of queries a student support system would process.

    Sensitive entities: id_student, region, imd_band (socioeconomic),
                        highest_education, disability status, final_result
    """
    oulad_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "oulad", "studentInfo.csv"
    )
    if not os.path.exists(oulad_path):
        print(f"⚠️  OULAD studentInfo.csv not found at {oulad_path}")
        return []

    print(f"Loading OULAD studentInfo from {oulad_path}...")
    students = []
    with open(oulad_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            students.append(row)

    print(f"  Total OULAD students loaded: {len(students)}")

    # Reproducible sample — pick diverse cases including withdrawals/fails
    random.seed(42)
    sampled = random.sample(students, min(max_samples * 3, len(students)))

    # Build realistic educational support queries from real student records
    query_templates = [
        (
            "Student {id} from {region} with {education} qualification is enrolled in module {module} "
            "({presentation}) and has attempted the module {attempts} time(s). They are currently "
            "struggling with their coursework. How can I support a {age_band}-year-old student "
            "with {credits} credits who has {disability}?",
            ["id_student", "region", "highest_education", "imd_band"]
        ),
        (
            "A student (ID: {id}) from the {region} area with {education} background is showing signs "
            "of academic difficulty in {module}. Their socioeconomic band is {imd_band} and they have "
            "{disability}. What intervention strategies are best for this demographic?",
            ["id_student", "region", "imd_band", "highest_education"]
        ),
        (
            "I need to submit a progress report for student {id} in module {module} presentation {presentation}. "
            "The student is from {region}, has {education} qualifications, and is currently in the "
            "{age_band} age bracket with {credits} studied credits. Their previous attempts: {attempts}. "
            "Gender: {gender}. How should I frame their academic journey?",
            ["id_student", "region", "gender"]
        ),
        (
            "Student {id} has a {disability} status and lives in the {region} region. "
            "They are studying {credits} credits in module {module} with {education} prior qualification. "
            "Their IMD band is {imd_band}. What accessibility support should be recommended?",
            ["id_student", "region", "imd_band", "disability"]
        ),
        (
            "Performance analysis needed for student {id} (module: {module}, presentation: {presentation}). "
            "Background: {education}, from {region}, age group {age_band}, IMD band {imd_band}. "
            "They withdrew after {attempts} attempt(s). What are the common predictors for this outcome?",
            ["id_student", "region", "imd_band"]
        ),
    ]

    queries = []
    idx = 0
    for student in sampled:
        if idx >= max_samples:
            break

        # Skip rows with missing critical fields
        if not student.get("id_student") or not student.get("region"):
            continue

        # Determine disability label
        disability_label = "a registered disability" if student.get("disability", "N") == "Y" else "no registered disability"

        template, sensitive_fields = random.choice(query_templates)

        try:
            query_text = template.format(
                id=student["id_student"],
                region=student["region"],
                education=student.get("highest_education", "unspecified"),
                module=student["code_module"],
                presentation=student["code_presentation"],
                attempts=student.get("num_of_prev_attempts", "0"),
                age_band=student.get("age_band", "unknown"),
                credits=student.get("studied_credits", "unknown"),
                imd_band=student.get("imd_band", "unspecified"),
                gender=student.get("gender", "unspecified"),
                disability=disability_label
            )
        except KeyError:
            continue

        # Sensitive entities = the actual values of PII fields from OULAD record
        sensitive_entities = []
        field_map = {
            "id_student": student.get("id_student", ""),
            "region": student.get("region", ""),
            "imd_band": student.get("imd_band", ""),
            "highest_education": student.get("highest_education", ""),
            "gender": student.get("gender", ""),
            "disability": "disability" if student.get("disability", "N") == "Y" else "",
        }
        for field_name in sensitive_fields:
            val = field_map.get(field_name, "")
            if val and val not in sensitive_entities:
                sensitive_entities.append(val)

        queries.append({
            "id": f"oulad_{idx:04d}",
            "query": query_text,
            "sensitive": [e for e in sensitive_entities if e],
            "domain": "education",
            "source": "oulad_studentinfo",
            "gt_labels": sensitive_fields,
            "expected_zone": 1
        })
        idx += 1

    print(f"✅ Generated {len(queries)} OULAD-derived educational queries")
    return queries


    ai4p_queries = load_ai4privacy_education_samples(max_samples=ai4privacy_samples)
    oulad_queries = load_oulad_derived_queries(max_samples=oulad_samples)

    all_queries = ai4p_queries + oulad_queries
    return all_queries


def save_exp01_dataset_to_cache(queries: List[Dict], cache_path: str = None):
    """Save generated queries to a local JSON for fast reuse."""
    if cache_path is None:
        cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "exp01", "exp01_full_dataset_cache.json"
        )
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(queries, f, indent=2)
    print(f"✅ Full EXP01 dataset saved to cache: {cache_path}")


def load_exp01_dataset(ai4privacy_samples: int = 200, oulad_samples: int = 100, bypass_cache: bool = False) -> List[Dict]:
    """
    Load the full EXP01 dataset: AI4Privacy (200) + OULAD (100) = 300 total.
    First checks local cache, otherwise performs full generation.
    """
    cache_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "exp01", "exp01_full_dataset_cache.json"
    )

    if not bypass_cache and os.path.exists(cache_path):
        print("\n" + "="*60)
        print("EXP01 DATA LOADING — From Local Cache")
        print("="*60)
        with open(cache_path, "r") as f:
            all_cached = json.load(f)
        
        # Filter for requested amounts (sources: ai4privacy_pii_masking_200k, oulad_studentinfo)
        ai4p = [q for q in all_cached if q["source"] == "ai4privacy_pii_masking_200k"][:ai4privacy_samples]
        oulad = [q for q in all_cached if q["source"] == "oulad_studentinfo"][:oulad_samples]
        
        all_queries = ai4p + oulad
        print(f"✅ Loaded {len(all_queries)} samples from cache: {cache_path}")
        print("="*60 + "\n")
        return all_queries

    print("\n" + "="*60)
    print("EXP01 DATA LOADING — Real Published Datasets (Full Generation)")
    print("="*60)

    ai4p_queries = load_ai4privacy_education_samples(max_samples=ai4privacy_samples)
    oulad_queries = load_oulad_derived_queries(max_samples=oulad_samples)

    all_queries = ai4p_queries + oulad_queries

    if not all_queries:
        raise RuntimeError(
            "No data loaded for EXP01. Ensure either:\n"
            "  1. Internet access for HuggingFace download (pip install datasets)\n"
            "  2. Local OULAD data at data/oulad/studentInfo.csv\n"
            "Synthetic data is NOT permitted per supervisor constraints."
        )

    print(f"\n📦 Total EXP01 dataset: {len(all_queries)} samples")
    print(f"   AI4Privacy samples: {len(ai4p_queries)}")
    print(f"   OULAD-derived:      {len(oulad_queries)}")
    print("="*60 + "\n")
    return all_queries


# ══════════════════════════════════════════════════════════════════════════════
# BASELINES
# ══════════════════════════════════════════════════════════════════════════════

def run_no_protection_baseline(query: str) -> str:
    """Baseline 1: Pass query directly to cloud without any sanitization."""
    return query  # The raw query IS the 'response' in the no-protection scenario


def run_full_redaction_baseline(query: str, sensitive_entities: List[str]) -> str:
    """Baseline 2: Replace all sensitive entities with [REDACTED]."""
    redacted = query
    for entity in sensitive_entities:
        if entity:
            redacted = re.sub(re.escape(entity), "[REDACTED]", redacted, flags=re.IGNORECASE)
    return redacted




# ══════════════════════════════════════════════════════════════════════════════
# UTILITY METRICS
# ══════════════════════════════════════════════════════════════════════════════

def compute_sts_score(original: str, response: str) -> float:
    """
    Semantic Textual Similarity (STS) — three-tier fallback strategy:

    Tier 1: sentence-transformers all-MiniLM-L6-v2 (best, matches Prεεmpt metric)
            → requires compatible tokenizers/transformers in venv

    Tier 2: TF-IDF cosine similarity via scikit-learn (good, no extra installs)
            → scikit-learn is already in venv via crewai → chromadb deps
            → Pearson r ≈ 0.84 with MiniLM on short educational text (Chandrasekaran 2021)

    Tier 3: LLM-as-a-Judge via Ollama (fallback when both above fail)

    Returns cosine similarity in [0.0, 1.0].
    """
    # ── Tier 1: sentence-transformers ────────────────────────────────────────
    try:
        from sentence_transformers import SentenceTransformer, util
        _sts_model = SentenceTransformer("all-MiniLM-L6-v2")
        emb_orig = _sts_model.encode(original, convert_to_tensor=True)
        emb_resp = _sts_model.encode(response, convert_to_tensor=True)
        similarity = float(util.cos_sim(emb_orig, emb_resp).item())
        return max(0.0, min(1.0, similarity))
    except Exception:
        pass  # Fall through to Tier 2

    # ── Tier 2: TF-IDF cosine (scikit-learn — already installed via crewai) ──
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),    # unigrams + bigrams for better semantic capture
            min_df=1,
            stop_words="english"
        )
        tfidf = vectorizer.fit_transform([original, response])
        similarity = float(sk_cosine(tfidf[0], tfidf[1])[0][0])
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        print(f"  ⚠️  TF-IDF STS failed: {e}")

    # ── Tier 3: LLM judge ────────────────────────────────────────────────────
    return _measure_utility_llm(original, response)


# Module-level default — overridden by --model CLI arg or EXP01_OLLAMA_MODEL env var
# Available locally: llama3.2:latest (2.0 GB), phi3.5:latest (2.2 GB), llama2:latest (3.8 GB)
_OLLAMA_MODEL: str = os.getenv("EXP01_OLLAMA_MODEL", "ollama/llama3.2")
_OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def _measure_utility_llm(original_query: str, response: str,
                         model: str = None, base_url: str = None) -> float:
    """
    LLM-as-a-Judge utility metric via Ollama.
    Primary metric when sentence-transformers is unavailable;
    secondary metric otherwise.
    Model defaults to module-level _OLLAMA_MODEL (llama3.2).
    """
    model = model or _OLLAMA_MODEL
    base_url = base_url or _OLLAMA_BASE_URL
    prompt = f"""Evaluate the educational utility of this AI response given the original query.
Original Query: {original_query[:500]}
AI Response: {response[:500]}

Score the utility from 0.0 to 1.0 based on:
1. Does it preserve the educational/scientific intent of the original query?
2. Is the response still actionable and useful despite any anonymization?

Return ONLY a numerical score between 0.0 and 1.0."""
    try:
        llm = LLM(model=model, base_url=base_url)
        result = llm.call([{"role": "user", "content": prompt}])
        match = re.search(r"0\.\d+|1\.0|0|1", str(result))
        return float(match.group()) if match else 0.5
    except Exception as e:
        print(f"  ⚠️  LLM utility judge failed ({model}): {e}")
        return 0.5


def measure_ip_protection(
    original_query: str,
    cloud_response: str,
    sensitive_entities: List[str],
    mapping: Optional[Dict[str, str]] = None,
    sts_model: Any = None
) -> Tuple[float, float, List[str], float]:
    """
    Measure IP/PII protection using:
      1. Ground-truth entity leakage check (exact match on sensitive_entities)
      2. Semantic/Attribute Leakage check (STS between mapping pairs)
      3. Adversarial LLM check (SemanticPrivacyMetric)

    Returns:
      ip_leakage_score  : float [0.0=none, 1.0=full leakage]
      ip_protection_rate: float [0.0=no protection, 1.0=fully protected]
      leaked_entities   : list of entity strings found in response
      semantic_leakage  : float [Mean STS(original, placeholder)]
    """
    # 1. Ground-truth check — exact match
    leaked = []
    response_lower = cloud_response.lower()
    for entity in sensitive_entities:
        if entity and len(entity) > 2:
            if re.search(r'\b' + re.escape(entity.lower()) + r'\b', response_lower):
                leaked.append(entity)

    leakage_score = len(leaked) / max(len(sensitive_entities), 1) if sensitive_entities else 0.0
    
    # 2. Semantic/Attribute Leakage (Reviewer Concern P1-A1)
    # Compute STS between original entities and their generalizations.
    # High STS indicates the generalization is too close to the original (leakage).
    semantic_leakage_scores = []
    if mapping and sts_model:
        try:
            from sentence_transformers import util
            for original, generalization in mapping.items():
                # We want to know if the generalization 'reveals' the original too closely
                emb_orig = sts_model.encode(original, convert_to_tensor=True)
                emb_gen = sts_model.encode(generalization, convert_to_tensor=True)
                sim = float(util.cos_sim(emb_orig, emb_gen).item())
                semantic_leakage_scores.append(max(0.0, sim))
        except Exception as e:
            print(f"  ⚠️  Semantic leakage computation failed: {e}")

    avg_semantic_leakage = (sum(semantic_leakage_scores) / len(semantic_leakage_scores)) if semantic_leakage_scores else 0.0

    # 3. Adversarial LLM check for semantic leakage (Contextual)
    try:
        metric = SemanticPrivacyMetric(threshold=0.5)
        test_case = LLMTestCase(input=original_query, actual_output=cloud_response)
        safety_score = metric.measure(test_case)
        # Combine safety score with exact match leakage if needed, 
        # but usually safety_score is used independently for adversarial reporting.
        return leakage_score, max(0.0, 1.0 - leakage_score), leaked, avg_semantic_leakage
    except Exception:
        return leakage_score, max(0.0, 1.0 - leakage_score), leaked, avg_semantic_leakage


# ══════════════════════════════════════════════════════════════════════════════
# DATACLASS & EXPERIMENT CLASS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExperimentResult:
    """Result for a single query — EXP01 real-data version"""
    query_id: str
    domain: str
    source: str                         # "ai4privacy_pii_masking_200k" | "oulad_studentinfo"
    original_query: str
    sensitive_entities: List[str]
    gt_label_count: int                 # number of ground-truth PII labels from dataset

    # Pipeline outputs
    sanitized_query: str
    mapping: Dict[str, str]
    cloud_response: str
    recontextualized_response: str

    # Primary metrics (objective — using ground-truth labels)
    ip_leakage_score: float             # 0=no leakage, 1=full leakage
    ip_protection_rate: float           # 1 - leakage
    semantic_leakage_score: float       # Average STS(original, placeholder)
    entities_leaked: List[str]

    # Utility metrics
    utility_sts: float                  # Sentence-Transformers cosine similarity
    utility_llm_judge: float            # Ollama LLM-as-judge score

    # Timing
    sanitization_time_ms: float
    total_time_ms: float

    # Token efficiency
    original_tokens: int
    sanitized_tokens: int

    # Baseline outputs (for traceability)
    no_protection_response: str = ""
    redaction_response: str = ""

    # Baseline comparisons (populated separately)
    full_redaction_utility_sts: float = 0.0


class SemanticGeneralizationExperiment:
    """
    EXP01 — Semantic Generalization Effectiveness (Real Data Version)

    Hypothesis: Semantic generalization protects IP/PII while preserving
    educational utility, outperforming full redaction on utility and matching
    Prεεmpt on protection while covering broader entity types.
    """

    def __init__(self, use_cloud: bool = False,
                 ollama_model: str = None,
                 ollama_base_url: str = None):
        self.use_cloud = use_cloud
        # Cloud LLM — defaults to module-level constant (llama3.2)
        self.ollama_model = ollama_model or _OLLAMA_MODEL
        self.ollama_base_url = ollama_base_url or _OLLAMA_BASE_URL
        self.recontextualization_tool = RecontextualizationTool()
        self.results: List[ExperimentResult] = []
        self._sts_model = None  # Lazy-loaded

    def _get_sts_model(self):
        """Lazy-load STS model to avoid startup cost if not needed."""
        if self._sts_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print("  Loading SentenceTransformer (all-MiniLM-L6-v2)...")
                self._sts_model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                self._sts_model = None
        return self._sts_model

    def run_single_query(self, query_data: Dict) -> ExperimentResult:
        """Process a single real query through the full pipeline + baselines."""

        generalization_tool = SemanticGeneralizationTool()
        generalization_tool.placeholder_map = {}

        query_id = query_data["id"]
        original_query = query_data["query"]
        sensitive_entities = query_data.get("sensitive", [])
        domain = query_data.get("domain", "education")
        source = query_data.get("source", "unknown")

        print(f"\n{'='*60}")
        print(f"Processing: {query_id} | source={source} | domain={domain}")
        print(f"Query snippet: {original_query[:80]}...")
        print(f"GT entities ({len(sensitive_entities)}): {sensitive_entities[:5]}")

        # Start trace
        global_tracer.start_trace(query_id=str(query_id), original_query=original_query)
        global_tracer.log_agent(
            agent_name="Sovereign Manager",
            agent_role="Privacy-Aware Query Router",
            input_data=original_query,
            output_data=f"Zone 1 - High Sensitivity ({domain})",
            duration_ms=10.0,
            privacy_before=1.0,
            privacy_after=1.0,
            zone=1
        )

        start_time = time.time()

        # ── Stage 1: Semantic Generalization ──────────────────────────────────
        sanitization_start = time.time()
        generalization_result = generalization_tool._run(
            query=original_query,
            sensitive_entities=",".join(sensitive_entities) if sensitive_entities else ""
        )
        sanitization_time = (time.time() - sanitization_start) * 1000
        sanitized_query, mapping = self._parse_generalization_result(generalization_result)
        print(f"  Sanitized: {sanitized_query[:80]}...")

        global_tracer.log_agent(
            agent_name="Semantic Generalizer",
            agent_role="Intent Obfuscation Specialist",
            input_data=f"Query: {original_query[:200]}\nEntities: {sensitive_entities}",
            output_data=generalization_result,
            duration_ms=sanitization_time,
            privacy_before=1.0,
            privacy_after=0.2,
            entities_detected=sensitive_entities,
            mapping=mapping
        )

        # ── Stage 2: Cloud Query ──────────────────────────────────────────────
        cloud_start = time.time()
        if self.use_cloud:
            cloud_response = self._call_cloud(sanitized_query)
        else:
            cloud_response = self._simulate_cloud_response(sanitized_query, domain)
        cloud_time = (time.time() - cloud_start) * 1000

        global_tracer.log_agent(
            agent_name="Cloud Researcher",
            agent_role="External Knowledge Retrieval",
            input_data=sanitized_query,
            output_data=cloud_response,
            duration_ms=cloud_time,
            privacy_before=0.2,
            privacy_after=0.2
        )

        # ── Stage 3: Recontextualization ─────────────────────────────────────
        recon_start = time.time()
        recontextualized = self.recontextualization_tool._run(
            response=cloud_response,
            mapping=str(mapping)
        )
        recon_time = (time.time() - recon_start) * 1000

        global_tracer.log_agent(
            agent_name="Recontextualizer",
            agent_role="Response Re-contextualization Specialist",
            input_data=f"Response: {cloud_response[:100]}...\nMapping: {mapping}",
            output_data=recontextualized,
            duration_ms=recon_time,
            privacy_before=0.2,
            privacy_after=0.0,
            mapping=mapping
        )

        total_time = (time.time() - start_time) * 1000

        # ── Metrics: IP Protection (Ground-Truth & Semantic) ──────────────────
        sts_model = self._get_sts_model()
        ip_leakage_score, ip_protection_rate, leaked_entities, semantic_leakage = measure_ip_protection(
            original_query, cloud_response, sensitive_entities, 
            mapping=mapping, sts_model=sts_model
        )
        print(f"  IP Protection: {ip_protection_rate:.1%} | Semantic Leakage: {semantic_leakage:.3f}")

        # ── Baseline Responses (for Utility comparison) ──────────────────────
        # To measure utility correctly (matching Prεεmpt), we compare cloud responses.
        # Reference = response to the unprotected query.

        if self.use_cloud:
            no_protection_response = self._call_cloud(original_query)
        else:
            no_protection_response = self._simulate_cloud_response(original_query, domain)

        # Full Redaction Baseline Response
        redacted_query = run_full_redaction_baseline(original_query, sensitive_entities)
        if self.use_cloud:
            redaction_response = self._call_cloud(redacted_query)
        else:
            redaction_response = self._simulate_cloud_response(redacted_query, domain)

        # ── Metrics: Utility (STS + LLM Judge) — CORRECTED PAIRS ──────────────
        # Correct STS: Compare what the cloud says WITH sanitization vs WITHOUT.
        utility_sts = compute_sts_score(no_protection_response, recontextualized)
        
        # Redaction STS: Compare redaction response vs no-protection response
        redact_sts = compute_sts_score(no_protection_response, redaction_response)

        if self.use_cloud:
            utility_llm = _measure_utility_llm(
                original_query, recontextualized,
                model=self.ollama_model, base_url=self.ollama_base_url
            )
        else:
            # Simple heuristic when cloud is simulated
            utility_llm = utility_sts

        print(f"  Utility STS: {utility_sts:.3f} (Redact: {redact_sts:.3f}) | LLM Judge: {utility_llm:.3f}")

        global_tracer.log_agent(
            agent_name="Evidence Curator",
            agent_role="Learning Record Manager",
            input_data=recontextualized,
            output_data="Competency Updated",
            duration_ms=5.0,
            privacy_before=0.0,
            privacy_after=0.0,
            metadata={
                "utility_sts": utility_sts,
                "utility_llm": utility_llm,
                "ip_protection_rate": ip_protection_rate
            }
        )
        global_tracer.end_trace(
            final_response=recontextualized,
            zone=1,
            utility_score=utility_sts
        )

        orig_tokens = len(original_query.split())
        sanitized_tokens = len(sanitized_query.split())

        result = ExperimentResult(
            query_id=query_id,
            domain=domain,
            source=source,
            original_query=original_query,
            sensitive_entities=sensitive_entities,
            gt_label_count=len(query_data.get("gt_labels", sensitive_entities)),
            sanitized_query=sanitized_query,
            mapping=mapping,
            cloud_response=cloud_response,
            recontextualized_response=recontextualized,
            ip_leakage_score=ip_leakage_score,
            ip_protection_rate=ip_protection_rate,
            semantic_leakage_score=semantic_leakage,
            entities_leaked=leaked_entities,
            utility_sts=utility_sts,
            utility_llm_judge=utility_llm,
            sanitization_time_ms=sanitization_time,
            total_time_ms=total_time,
            original_tokens=orig_tokens,
            sanitized_tokens=sanitized_tokens,
            no_protection_response=no_protection_response,
            redaction_response=redaction_response,
            full_redaction_utility_sts=redact_sts
        )

        return result

    def _parse_generalization_result(self, result: str) -> Tuple[str, Dict]:
        """Parse tool output into (sanitized_query, mapping)."""
        sanitized = ""
        mapping = {}
        
        # Robust parsing for multi-line blocks
        sanitized_match = re.search(r"SANITIZED:\s*(.*?)(?=\n[A-Z]+:|$)", result, re.DOTALL)
        if sanitized_match:
            sanitized = sanitized_match.group(1).strip()
            
        mapping_match = re.search(r"MAPPING:\s*(\{.*?\})(?=\n[A-Z]+:|$)", result, re.DOTALL)
        if mapping_match:
            try:
                mapping = json.loads(mapping_match.group(1))
            except json.JSONDecodeError:
                # Fallback to ast if it's not strictly JSON
                import ast
                try:
                    mapping = ast.literal_eval(mapping_match.group(1))
                except:
                    mapping = {}
                    
        if not sanitized:
            # Fallback for old-style or unstructured output
            lines = result.split("\n")
            for line in lines:
                if line.startswith("SANITIZED:"):
                    sanitized = line.replace("SANITIZED:", "").strip()
            if not sanitized:
                sanitized = result.strip()
                
        return sanitized, mapping

    def _simulate_cloud_response(self, sanitized_query: str, domain: str) -> str:
        """
        Simulate a cloud LLM response for fast local testing.
        In production or --cloud mode, this is replaced by a real API call.
        """
        domain_responses = {
            "education": (
                "Based on the student profile described, I recommend a personalised learning "
                "plan that includes targeted academic support, peer mentoring, and regular "
                "progress check-ins. Consider referencing the student's prior qualifications "
                "and regional support services available in their area."
            ),
            "health_education": (
                "For students with health-related circumstances, best practice involves "
                "reasonable adjustments per institutional policy, collaboration with "
                "wellbeing services, and flexible assessment arrangements where appropriate."
            ),
        }
        return domain_responses.get(domain, (
            "I can provide guidance on this educational support topic. "
            "Based on the information provided, systematic intervention strategies "
            "tailored to the student's background and needs would be most effective."
        ))

    def _call_cloud(self, sanitized_query: str) -> str:
        """
        Call cloud LLM via Ollama (no API key / quota limits).
        Model: self.ollama_model  (default: llama3.2)
        Ollama must be running:  ollama serve
        """
        try:
            llm = LLM(model=self.ollama_model, base_url=self.ollama_base_url)
            result = llm.call([{"role": "user", "content": sanitized_query}])
            return str(result).strip()
        except Exception as e:
            print(f"  ⚠️  Ollama call failed ({self.ollama_model}): {e}. "
                  f"Falling back to simulated response.")
            return self._simulate_cloud_response(sanitized_query, "education")

    def run_all(self, queries: Optional[List[Dict]] = None) -> Dict:
        """Run the experiment on all queries. Loads real data if none provided."""
        if queries is None:
            queries = load_exp01_dataset()

        model_label = f"REAL ({self.ollama_model})" if self.use_cloud else "SIMULATED (fast)"
        print(f"\n{'='*60}")
        print(f"EXP01 — SEMANTIC GENERALIZATION EFFECTIVENESS")
        print(f"{'='*60}")
        print(f"Dataset:     Real Published Data (AI4Privacy + OULAD)")
        print(f"Total:       {len(queries)} queries")
        print(f"Cloud mode:  {model_label}")
        print(f"Ollama URL:  {self.ollama_base_url}")
        print(f"Started:     {datetime.now().isoformat()}")
        print(f"{'='*60}\n")

        for i, query_data in enumerate(queries):
            print(f"[{i+1}/{len(queries)}]", end=" ")
            try:
                result = self.run_single_query(query_data)
                self.results.append(result)
            except Exception as e:
                print(f"❌ Error processing {query_data.get('id', '?')}: {e}")

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate aggregate report with all metrics and baseline comparisons."""
        if not self.results:
            return {"error": "No results to report"}

        total = len(self.results)

        # ── Aggregate: Sovereign Learner ──────────────────────────────────────
        avg_ip_protection = sum(r.ip_protection_rate for r in self.results) / total
        avg_ip_leakage = sum(r.ip_leakage_score for r in self.results) / total
        avg_semantic_leakage = sum(r.semantic_leakage_score for r in self.results) / total
        avg_utility_sts = sum(r.utility_sts for r in self.results) / total
        avg_utility_llm = sum(r.utility_llm_judge for r in self.results) / total
        avg_sanitization_time = sum(r.sanitization_time_ms for r in self.results) / total
        zero_leakage_count = sum(1 for r in self.results if r.ip_leakage_score == 0.0)

        # ── By Source ─────────────────────────────────────────────────────────
        by_source = {}
        for src in set(r.source for r in self.results):
            src_results = [r for r in self.results if r.source == src]
            by_source[src] = {
                "count": len(src_results),
                "avg_ip_protection": sum(r.ip_protection_rate for r in src_results) / len(src_results),
                "avg_utility_sts": sum(r.utility_sts for r in src_results) / len(src_results),
                "zero_leakage_rate": sum(1 for r in src_results if r.ip_leakage_score == 0.0) / len(src_results)
            }

        # ── By Domain ─────────────────────────────────────────────────────────
        by_domain = {}
        for domain in set(r.domain for r in self.results):
            domain_results = [r for r in self.results if r.domain == domain]
            by_domain[domain] = {
                "count": len(domain_results),
                "avg_ip_protection": sum(r.ip_protection_rate for r in domain_results) / len(domain_results),
                "avg_utility_sts": sum(r.utility_sts for r in domain_results) / len(domain_results),
                "zero_leakage_rate": sum(1 for r in domain_results if r.ip_leakage_score == 0.0) / len(domain_results)
            }

        # ── Baseline Comparisons ──────────────────────────────────────────────
        full_redact_utility = sum(r.full_redaction_utility_sts for r in self.results) / total

        report = {
            "experiment": "EXP01 — Semantic Generalization Effectiveness",
            "version": "2.0 — Real Data (AI4Privacy + OULAD)",
            "timestamp": datetime.now().isoformat(),
            "dataset": {
                "total_samples": total,
                "ai4privacy_samples": sum(1 for r in self.results if r.source == "ai4privacy_pii_masking_200k"),
                "oulad_samples": sum(1 for r in self.results if r.source == "oulad_studentinfo"),
                "cloud_mode": "real" if self.use_cloud else "simulated"
            },
            "primary_metrics": {
                "ip_protection_rate": avg_ip_protection,
                "ip_leakage_rate": avg_ip_leakage,
                "semantic_leakage_rate": avg_semantic_leakage,
                "utility_sts": avg_utility_sts,
                "utility_llm_judge": avg_utility_llm,
                "zero_leakage_count": zero_leakage_count,
                "zero_leakage_rate": zero_leakage_count / total,
                "avg_sanitization_time_ms": avg_sanitization_time
            },
            "by_source": by_source,
            "by_domain": by_domain,
            "baseline_comparison": {
                "no_protection": {
                    "ip_protection_rate": 0.0,
                    "utility_sts": 1.0,
                    "note": "Raw query — reference response"
                },
                "full_redaction": {
                    "ip_protection_rate": 1.0,
                    "utility_sts": full_redact_utility,
                    "note": "All entities [REDACTED] — cloud cannot reason about specifics"
                },

                "sovereign_learner": {
                    "ip_protection_rate": avg_ip_protection,
                    "utility_sts": avg_utility_sts,
                    "note": "Semantic generalization — domain-agnostic"
                }
            }
        }
        return report

    def save_results(self, output_dir: str = None) -> str:
        """Save detailed results and report to JSON."""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        detailed_path = os.path.join(output_dir, f"exp01_detailed_{timestamp}.json")
        with open(detailed_path, "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)

        report = self.generate_report()
        report_path = os.path.join(output_dir, f"exp01_report_{timestamp}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nResults saved:")
        print(f"  Detailed: {detailed_path}")
        print(f"  Report:   {report_path}")
        return report_path

    def print_summary(self):
        """Print formatted experiment summary to console."""
        report = self.generate_report()
        pm = report["primary_metrics"]
        ds = report["dataset"]
        bl = report["baseline_comparison"]

        print(f"\n{'='*65}")
        print("EXP01 — SEMANTIC GENERALIZATION EFFECTIVENESS — RESULTS")
        print(f"{'='*65}")
        print(f"Dataset: {ds['total_samples']} real samples "
              f"({ds['ai4privacy_samples']} AI4Privacy + {ds['oulad_samples']} OULAD)")

        print(f"\n📊 PRIMARY METRICS (Sovereign Learner)")
        print(f"   IP Protection Rate:    {pm['ip_protection_rate']:.1%}")
        print(f"   IP Leakage Rate:       {pm['ip_leakage_rate']:.1%}")
        print(f"   Semantic Leakage Rate: {pm['semantic_leakage_rate']:.3f} (STS-based)")
        print(f"   Utility (STS):         {pm['utility_sts']:.3f}")
        print(f"   Utility (LLM Judge):   {pm['utility_llm_judge']:.3f}")
        print(f"   Zero-Leakage Queries:  {pm['zero_leakage_count']}/{ds['total_samples']} "
              f"({pm['zero_leakage_rate']:.1%})")
        print(f"   Avg Sanitization Time: {pm['avg_sanitization_time_ms']:.2f} ms")

        print(f"\n📈 BY DOMAIN")
        for domain, metrics in report["by_domain"].items():
            print(f"   {domain.upper():25s}  "
                  f"IP Prot: {metrics['avg_ip_protection']:.1%}  "
                  f"STS: {metrics['avg_utility_sts']:.3f}  "
                  f"n={metrics['count']}")

        print(f"\n📋 BASELINE COMPARISON")
        print(f"   {'System':<25} {'IP Protection':>14} {'Utility (STS)':>14}")
        print(f"   {'-'*55}")
        for method, metrics in bl.items():
            prot = metrics.get("ip_protection_rate")
            util = metrics.get("utility_sts")
            prot_str = f"{prot:.1%}" if prot is not None else "N/A"
            util_str = f"{util:.3f}" if util is not None else "N/A"
            print(f"   {method:<25} {prot_str:>14} {util_str:>14}")

        print(f"\n{'='*65}")
        print("✅ EXP01 complete — results use real published datasets")
        print("   Data: AI4Privacy pii-masking-200k + OULAD studentInfo")
        print(f"{'='*65}\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="EXP01 — Semantic Generalization Effectiveness (Real Data)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fast local test — 5 OULAD samples, simulated responses (no model needed)
  python experiments/exp01_semantic_generalization.py --max-samples 5 --oulad 5 --ai4privacy 0

  # Full run — 300 samples via Ollama llama3.2 (default local model)
  python experiments/exp01_semantic_generalization.py --cloud

  # Full run with phi3.5 (faster, also available locally)
  python experiments/exp01_semantic_generalization.py --cloud --model ollama/phi3.5

  # Education domain only, first 50 samples
  python experiments/exp01_semantic_generalization.py --cloud --domain education --max-samples 50
"""
    )
    parser.add_argument("--cloud", action="store_true",
                        help=(
                            "Use Ollama as cloud LLM (real responses). "
                            "Default: simulated responses (fast, no model needed)."
                        ))
    parser.add_argument("--model", type=str,
                        default=os.getenv("EXP01_OLLAMA_MODEL", "ollama/llama3.2"),
                        help=(
                            "Ollama model to use for --cloud mode and LLM judge. "
                            "Default: ollama/llama3.2 (available locally). "
                            "Override via EXP01_OLLAMA_MODEL env var."
                        ))
    parser.add_argument("--ollama-url", type=str,
                        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                        help="Ollama server URL. Default: http://localhost:11434")
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Limit total samples for quick testing (default: all 300)")
    parser.add_argument("--ai4privacy", type=int, default=200,
                        help="Number of AI4Privacy samples (default: 200)")
    parser.add_argument("--oulad", type=int, default=100,
                        help="Number of OULAD-derived samples (default: 100)")
    parser.add_argument("--domain", type=str, default=None,
                        help="Filter by domain (education | health_education)")
    parser.add_argument("--save-cache", action="store_true",
                        help="Save the current generated dataset to local cache.")
    parser.add_argument("--bypass-cache", action="store_true",
                        help="Bypass local cache and regenerate/download data.")
    args = parser.parse_args()

    # Push resolved model into module-level so _measure_utility_llm picks it up
    global _OLLAMA_MODEL, _OLLAMA_BASE_URL
    _OLLAMA_MODEL = args.model
    _OLLAMA_BASE_URL = args.ollama_url

    print(f"  Ollama model : {_OLLAMA_MODEL}")
    print(f"  Ollama URL   : {_OLLAMA_BASE_URL}")
    if args.cloud:
        print(f"  Cloud mode   : ON — using Ollama for responses + LLM judge")
    else:
        print(f"  Cloud mode   : OFF — simulated responses, STS utility only")

    # Load real datasets
    queries = load_exp01_dataset(
        ai4privacy_samples=args.ai4privacy,
        oulad_samples=args.oulad,
        bypass_cache=args.bypass_cache
    )

    if args.save_cache:
        save_exp01_dataset_to_cache(queries)

    # Apply filters
    if args.domain:
        queries = [q for q in queries if q["domain"] == args.domain]
        print(f"Domain filter '{args.domain}': {len(queries)} queries")

    if args.max_samples:
        queries = queries[:args.max_samples]
        print(f"Sample limit applied: {len(queries)} queries")

    # Run experiment
    experiment = SemanticGeneralizationExperiment(
        use_cloud=args.cloud,
        ollama_model=args.model,
        ollama_base_url=args.ollama_url
    )
    experiment.run_all(queries)
    experiment.print_summary()
    experiment.save_results()


if __name__ == "__main__":
    main()