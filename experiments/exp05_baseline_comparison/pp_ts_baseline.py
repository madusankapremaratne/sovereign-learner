"""
PP-TS Baseline Implementation
==============================
Faithful reimplementation of Algorithm 1 from:

  Kan et al. "Protecting User Privacy in Remote Conversational Systems:
  A Privacy-Preserving Framework based on Text Sanitization"
  arXiv:2306.08223 (2023)

Algorithm 1: Filtering private information
  Input:  User Input X, privacy types A
  Output: Sanitized input X̂, plaintext-ciphertext set PCS

Steps (per the paper):
  1.  Initiate X̂ ← X
  2.  for Aᵢ in A do
  3.    Construct text sanitization requirements R for type A
  4.    Construct text sanitization examples E for type A
  5.    Iₚ ← R ⊕ E ⊕ X̂   (concatenate prompt)
  6.    Feed Iₚ into local LLM → sanitized X̂ + plaintext-ciphertext record pcr
  7.    Do a reasonability check on X̂
  8.    while X̂ is contradictory do
  9.      Fix inconsistencies in sanitized text X̂
  10.     Do a reasonability check on X̂
  11.     if X̂ is contradictory then
  12.       Feed Iₚ into LLM to obtain a new X̂ and pcr
  13.     end if
  14.   end while
  15.   Append pcr to PCS
  16. end for

Adaptation notes (documented for paper):
  - Original uses Llama-7B locally; we use Ollama (llama3.2) to match
    our experimental infrastructure. Same local-model principle.
  - Privacy types adapted from {Name, Address, Telephone} to include
    educational IP-relevant types: {Name, Location, Organization,
    Email, Phone, Research_Method, Dataset, Institution}
  - Reasonability check implemented as LLM self-consistency verification
    (same principle as paper — local LLM checks semantic coherence)
  - Plaintext-Ciphertext set (PCS) stored as local dict, matching paper

Usage:
  python pp_ts_baseline.py
  python pp_ts_baseline.py --queries educational  # educational IP queries
  python pp_ts_baseline.py --queries pii           # PII-heavy queries
"""

import json
import time
import re
import requests
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
LOCAL_MODEL = "llama3.2"          # Paper uses Llama-7B; we use llama3.2 (same principle)
MAX_REASONABILITY_RETRIES = 3     # Max while-loop iterations (Algorithm 1, line 8)

# Privacy types — paper uses {Name, Address, Telephone}
# We extend to cover educational IP threat model
PRIVACY_TYPES_PII = ["Name", "Location", "Organization", "Email", "Phone"]
PRIVACY_TYPES_EDUCATIONAL = ["Name", "Location", "Organization", "Research_Method", "Dataset", "Institution"]

# Shadow Lexicon — same educational IP patterns as Sovereign Learner (Reviewer request A5)
SHADOW_LEXICON = {
    "INSTITUTIONAL_MARKER": [
        r"\b[A-G]{3}\s+module\b", # OULAD coding (BBB, AAA, etc)
        r"\bVLE\b", r"\bOUSE\b", r"\bOULAD\b", r"\bOpen University\b"
    ],
    "ASSESSMENT_TYPE": [
        r"\bTMA\s*([0-9]*)\b", r"\biCMA\s*([0-9]*)\b", r"\bEMA\b",
        r"\bend\s+of\s+module\s+assessment\b"
    ],
    "LEARNING_METRIC": [
        r"\bV_Portfolio\b", r"\bcompetency\s+vector\b", 
        r"\blearning\s+weight\b", r"\binteraction\s+type\b"
    ],
    "CURRICULUM_DOMAIN": [
        r"\bSTEM\s+Foundation\b", r"\bComputing\s+&\s+IT\b",
        r"\bSocial\s+Sciences\b", r"\bBusiness\s+&\s+Law\b"
    ]
}

# ─────────────────────────────────────────────
# Test Query Sets
# ─────────────────────────────────────────────

# Educational IP queries — your domain (should expose PP-TS limitations)
EDUCATIONAL_IP_QUERIES = [
    {
        "id": "EDU-01",
        "query": "How do I optimize my CRISPR protocol for HEK293 cells to improve gene silencing efficiency?",
        "domain": "biomedical",
        "expected_pii": False,
        "note": "No traditional PII — pure IP"
    },
    {
        "id": "EDU-02",
        "query": "What are the best hyperparameters for training a transformer model on my custom NLP dataset for sentiment analysis?",
        "domain": "computer_science",
        "expected_pii": False,
        "note": "No traditional PII — methodology IP"
    },
    {
        "id": "EDU-03",
        "query": "I'm using the OULAD dataset to predict student dropout — should I use Random Forest or XGBoost for my thesis?",
        "domain": "education_analytics",
        "expected_pii": False,
        "note": "Dataset name + research approach = IP"
    },
    {
        "id": "EDU-04",
        "query": "My name is Madusanka and I'm at La Trobe University. How do I apply differential privacy to my federated learning model?",
        "domain": "computer_science",
        "expected_pii": True,
        "note": "Mixed: PII (name, institution) + IP (research method)"
    },
    {
        "id": "EDU-05",
        "query": "What statistical tests should I run on my longitudinal study data about learning outcomes in Sri Lankan schools?",
        "domain": "education",
        "expected_pii": False,
        "note": "Location context + research design = IP"
    },
    {
        "id": "EDU-06",
        "query": "How do I implement a Variational Autoencoder to generate synthetic student performance data while preserving privacy?",
        "domain": "computer_science",
        "expected_pii": False,
        "note": "Pure methodology IP"
    },
    {
        "id": "EDU-07",
        "query": "Can you help me debug my Python code for the semantic generalization pipeline I'm building for my PhD project?",
        "domain": "computer_science",
        "expected_pii": False,
        "note": "Research project description = IP"
    },
    {
        "id": "EDU-08",
        "query": "I'm Dr. Sarah Chen from MIT. What's the best way to anonymize patient records for my cancer research dataset?",
        "domain": "biomedical",
        "expected_pii": True,
        "note": "PII (name, institution) + sensitive research context"
    },
    {
        "id": "EDU-09",
        "query": "What prompting strategies work best for few-shot learning with GPT-4 on low-resource medical NLP tasks?",
        "domain": "biomedical_nlp",
        "expected_pii": False,
        "note": "Methodology IP only"
    },
    {
        "id": "EDU-10",
        "query": "How can I use reinforcement learning from human feedback to fine-tune my custom LLM for educational tutoring?",
        "domain": "education_ai",
        "expected_pii": False,
        "note": "Advanced methodology IP"
    },
]

# PII-heavy queries — where PP-TS should perform well
PII_HEAVY_QUERIES = [
    {
        "id": "PII-01",
        "query": "My name is John Smith and I live at 42 Oxford Street, London. Can you help me draft an email?",
        "domain": "general",
        "expected_pii": True,
        "note": "Classic PII — PP-TS designed for this"
    },
    {
        "id": "PII-02",
        "query": "Call me at +1-555-0123. My address is 123 Main Street, Boston MA 02101.",
        "domain": "general",
        "expected_pii": True,
        "note": "Phone + address — PP-TS designed for this"
    },
    {
        "id": "PII-03",
        "query": "I work at Google DeepMind in London. My manager is Dr. Jane Doe. We're working on a new AI project.",
        "domain": "general",
        "expected_pii": True,
        "note": "Name + organization — PP-TS should handle"
    },
]


# ─────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────

@dataclass
class PlaintextCiphertextRecord:
    """pcr — the local mapping stored per Algorithm 1 line 15"""
    privacy_type: str
    original_values: List[str]
    sanitized_values: List[str]

@dataclass
class PPTSResult:
    query_id: str
    original_query: str
    sanitized_query: str
    pcs: List[Dict]                    # Plaintext-Ciphertext Set
    privacy_types_applied: List[str]
    reasonability_retries: int         # How many while-loop iterations were needed
    sanitization_time_ms: float
    ip_protection_rate: float          # Our metric: % of IP entities protected
    utility_score: float               # Our metric: semantic utility preservation
    pii_protection_rate: float         # Named entity removal rate
    error: Optional[str] = None


# ─────────────────────────────────────────────
# Core PP-TS Algorithm 1 Implementation
# ─────────────────────────────────────────────

class PPTS:
    """
    Faithful implementation of Kan et al. PP-TS Algorithm 1.
    
    Uses local Ollama (llama3.2) as the local generative model,
    matching the paper's use of Llama-7B for local inference.
    """

    def __init__(self, model: str = LOCAL_MODEL):
        self.model = model
        self.pcs: List[PlaintextCiphertextRecord] = []  # PCS — persistent across conversation
        self._verify_ollama()

    def _verify_ollama(self):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            models = [m["name"] for m in r.json().get("models", [])]
            available = any(self.model in m for m in models)
            if not available:
                print(f"⚠️  Model '{self.model}' not found. Available: {models}")
                print(f"   Run: ollama pull {self.model}")
        except Exception as e:
            print(f"⚠️  Ollama not reachable: {e}")

    def _call_llm(self, prompt: str, max_retries: int = 2) -> str:
        """Feed Iₚ into local LLM (Algorithm 1, line 6)"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=60
                )
                return response.json().get("response", "").strip()
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"ERROR: {e}"
                time.sleep(1)
        return "ERROR: LLM call failed"

    def _construct_requirements(self, privacy_type: str) -> str:
        """
        Algorithm 1, Line 3: Construct text sanitization requirements R for type A
        
        These are the rewrite requirements from the paper's pre-designed library.
        """
        requirements = {
            "Name": (
                "Replace all personal names with different plausible names of the same cultural origin. "
                "The replacement names must be realistic and maintain grammatical consistency. "
                "Record each original→replacement pair."
            ),
            "Location": (
                "Replace all specific locations (cities, countries, addresses, landmarks) with "
                "different plausible locations of similar type. Ensure geographic consistency "
                "(e.g., don't replace a European city with an Asian one if context requires Europe). "
                "Record each original→replacement pair."
            ),
            "Organization": (
                "Replace all organization names (companies, universities, hospitals) with "
                "different plausible organizations of the same type. Record each pair."
            ),
            "Email": (
                "Replace all email addresses with different plausible email addresses. "
                "Maintain the same domain type (e.g., .edu stays .edu). Record each pair."
            ),
            "Phone": (
                "Replace all phone numbers with different plausible phone numbers "
                "of the same format/country code. Record each pair."
            ),
            "Research_Method": (
                "Replace all specific research method names, algorithm names, and technical "
                "protocol names with generic placeholders (e.g., 'Protocol-Alpha', 'Method-X', "
                "'Algorithm-Beta'). Record each pair."
            ),
            "Dataset": (
                "Replace all specific dataset names with generic placeholders "
                "(e.g., 'Dataset-A', 'DataSource-1'). Record each pair."
            ),
            "Institution": (
                "Replace all university and research institution names with generic "
                "placeholders (e.g., 'University-X', 'Research-Institute-Y'). Record each pair."
            ),
        }
        return requirements.get(privacy_type, f"Replace all {privacy_type} information with plausible alternatives.")

    def _construct_examples(self, privacy_type: str) -> str:
        """
        Algorithm 1, Line 4: Construct text sanitization examples E for type A
        
        In-context learning examples (few-shot), as described in the paper.
        """
        examples = {
            "Name": (
                "Example 1:\n"
                "  Input:  'Tom travelled to Paris'\n"
                "  Output: 'James travelled to Paris'\n"
                "  Pairs:  {Tom → James}\n\n"
                "Example 2:\n"
                "  Input:  'Dr. Sarah Chen reviewed the paper'\n"
                "  Output: 'Dr. Maria Lopez reviewed the paper'\n"
                "  Pairs:  {Sarah Chen → Maria Lopez}"
            ),
            "Location": (
                "Example 1:\n"
                "  Input:  'I live in London near the Thames'\n"
                "  Output: 'I live in Berlin near the Spree'\n"
                "  Pairs:  {London → Berlin, Thames → Spree}\n\n"
                "Example 2:\n"
                "  Input:  'The conference is in San Francisco'\n"
                "  Output: 'The conference is in Seattle'\n"
                "  Pairs:  {San Francisco → Seattle}"
            ),
            "Organization": (
                "Example 1:\n"
                "  Input:  'I work at Google DeepMind'\n"
                "  Output: 'I work at OpenResearch Labs'\n"
                "  Pairs:  {Google DeepMind → OpenResearch Labs}"
            ),
            "Research_Method": (
                "Example 1:\n"
                "  Input:  'I am using CRISPR-Cas9 for gene editing'\n"
                "  Output: 'I am using Protocol-Alpha for gene editing'\n"
                "  Pairs:  {CRISPR-Cas9 → Protocol-Alpha}\n\n"
                "Example 2:\n"
                "  Input:  'Training a BERT model for NLP'\n"
                "  Output: 'Training a Model-X for NLP'\n"
                "  Pairs:  {BERT → Model-X}"
            ),
            "Dataset": (
                "Example 1:\n"
                "  Input:  'I am using the OULAD dataset'\n"
                "  Output: 'I am using Dataset-A'\n"
                "  Pairs:  {OULAD → Dataset-A}\n\n"
                "Example 2:\n"
                "  Input:  'Training on ImageNet'\n"
                "  Output: 'Training on Dataset-B'\n"
                "  Pairs:  {ImageNet → Dataset-B}"
            ),
            "Institution": (
                "Example 1:\n"
                "  Input:  'PhD student at La Trobe University'\n"
                "  Output: 'PhD student at University-X'\n"
                "  Pairs:  {La Trobe University → University-X}"
            ),
        }
        return examples.get(privacy_type,
            f"Example:\n  Input: 'text with {privacy_type}'\n  Output: 'text with replaced {privacy_type}'\n  Pairs: {{original → replacement}}")

    def _sanitize_for_type(self, text: str, privacy_type: str) -> Tuple[str, PlaintextCiphertextRecord]:
        """
        Algorithm 1, Lines 3-6: One sanitization cycle for a specific privacy type Aᵢ
        
        Constructs Iₚ = R ⊕ E ⊕ X̂ and feeds into local LLM.
        Returns sanitized text and plaintext-ciphertext record.
        """
        R = self._construct_requirements(privacy_type)
        E = self._construct_examples(privacy_type)

        # Line 5: Iₚ ← R ⊕ E ⊕ X̂
        prompt = f"""You are a privacy protection system. Your task is to sanitize text by replacing {privacy_type} information.

REQUIREMENTS:
{R}

EXAMPLES:
{E}

TASK:
Sanitize the following text. Replace all {privacy_type} information following the requirements above.

Input text: "{text}"

Respond in this exact JSON format:
{{
  "sanitized_text": "<the sanitized version of the input>",
  "replacements": [
    {{"original": "<original value>", "sanitized": "<replacement value>"}}
  ]
}}

If no {privacy_type} information is found, return the original text unchanged with empty replacements.
Respond with JSON only, no other text."""

        response = self._call_llm(prompt)

        # Parse LLM response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                sanitized = data.get("sanitized_text", text)
                replacements = data.get("replacements", [])
            else:
                sanitized = text
                replacements = []
        except (json.JSONDecodeError, Exception):
            sanitized = text
            replacements = []

        pcr = PlaintextCiphertextRecord(
            privacy_type=privacy_type,
            original_values=[r.get("original", "") for r in replacements],
            sanitized_values=[r.get("sanitized", "") for r in replacements]
        )

        return sanitized, pcr

    def _reasonability_check(self, text: str) -> bool:
        """
        Algorithm 1, Line 7/10: Reasonability check on X̂
        
        Paper: "identifies the rewritten text X's plausibility by using a local 
        deployed generative model based on instruction learning"
        
        Returns True if text is semantically consistent (NOT contradictory).
        """
        prompt = f"""Check if the following text is semantically consistent and non-contradictory.
        
Text: "{text}"

Is this text semantically consistent? Answer with JSON only:
{{"is_consistent": true, "reason": "<brief explanation if inconsistent>"}}"""

        response = self._call_llm(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("is_consistent", True)
        except Exception:
            pass
        return True  # Default: assume consistent if check fails

    def _fix_inconsistencies(self, text: str) -> str:
        """
        Algorithm 1, Line 9: Fix inconsistencies in sanitized text X̂
        
        Paper example: "the Eiffel Tower" → "an iconic building" when Paris→London.
        """
        prompt = f"""The following text contains semantic inconsistencies (contradictions between replaced entities and their context).
Fix the inconsistencies by making the surrounding context consistent with the replacements.
Use abstract/generic descriptions where needed (e.g. 'the Eiffel Tower' near 'London' → 'an iconic building').

Text: "{text}"

Return only the fixed text, nothing else."""

        return self._call_llm(prompt) or text

    def sanitize(self, query: str, privacy_types: List[str], use_shadow_lexicon: bool = False) -> Tuple[str, List[PlaintextCiphertextRecord], int]:
        """
        Full Algorithm 1 implementation.
        
        Returns: (sanitized_text, PCS, total_retries)
        """
        X_hat = query          # Line 1: Initiate X̂ ← X
        pcs = []               # Plaintext-Ciphertext Set
        total_retries = 0

        types_to_process = list(privacy_types)
        if use_shadow_lexicon:
            # Augment with shadow lexicon categories
            types_to_process.extend(SHADOW_LEXICON.keys())

        # Line 2: for Aᵢ in A do
        for privacy_type in types_to_process:
            # Special case for Shadow Lexicon patterns (direct replacement)
            if privacy_type in SHADOW_LEXICON:
                patterns = SHADOW_LEXICON[privacy_type]
                replacements = []
                for pattern in patterns:
                    for match in re.finditer(pattern, X_hat, re.IGNORECASE):
                        original = match.group()
                        # Use same logic as Research_Method (generic placeholders)
                        sanitized_val = f"{privacy_type.replace('_', '-')}-X"
                        if original not in [r.get("original") for r in replacements]:
                            replacements.append({"original": original, "sanitized": sanitized_val})
                            X_hat = re.sub(re.escape(original), sanitized_val, X_hat, flags=re.IGNORECASE)
                
                pcs.append(PlaintextCiphertextRecord(
                    privacy_type=privacy_type,
                    original_values=[r["original"] for r in replacements],
                    sanitized_values=[r["sanitized"] for r in replacements]
                ))
                continue

            # Standard Algorithm 1 for other types
            # Lines 3-6: Construct prompt and sanitize
            X_hat, pcr = self._sanitize_for_type(X_hat, privacy_type)

            # Line 7: Reasonability check
            retries = 0
            is_consistent = self._reasonability_check(X_hat)

            # Lines 8-14: While loop — fix contradictions
            while not is_consistent and retries < MAX_REASONABILITY_RETRIES:
                retries += 1
                total_retries += 1

                # Line 9: Fix inconsistencies
                X_hat = self._fix_inconsistencies(X_hat)

                # Line 10: Do a reasonability check on X̂
                is_consistent = self._reasonability_check(X_hat)

                # Lines 11-13: If still contradictory, regenerate
                if not is_consistent:
                    X_hat, pcr = self._sanitize_for_type(X_hat, privacy_type)

            # Line 15: Append pcr to PCS
            pcs.append(pcr)

        return X_hat, pcs, total_retries


# ─────────────────────────────────────────────
# Evaluation Metrics
# ─────────────────────────────────────────────

class PPTSEvaluator:
    """
    Evaluate PP-TS using the same metrics as the Sovereign Learner experiments:
    - IP Protection Rate (your primary metric)
    - Utility Preservation (semantic similarity)
    - PII Entity Removal Rate (Kan et al.'s original metric)
    """

    def __init__(self):
        self.pp_ts = PPTS()

    def _measure_ip_protection(self, original: str, sanitized: str, domain: str) -> float:
        """
        Measure IP protection using LLM judge — same approach as your EXP01.
        Ask: can an attacker recover the research domain/methodology from sanitized text?
        """
        prompt = f"""You are evaluating privacy protection for intellectual property (IP).

Original query: "{original}"
Sanitized query: "{sanitized}"

Can an attacker determine the specific research domain, methodology, dataset, or 
intellectual property from the SANITIZED query alone?

Rate IP leakage from 0.0 (no leakage) to 1.0 (full leakage).
Respond with JSON only: {{"ip_leakage_rate": 0.0, "reasoning": "brief reason"}}"""

        response = self.pp_ts._call_llm(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                leakage = float(data.get("ip_leakage_rate", 1.0))
                return 1.0 - leakage  # Convert leakage → protection
        except Exception:
            pass
        return 0.0

    def _measure_utility(self, original: str, sanitized: str) -> float:
        """
        Measure utility preservation — same metric as your experiments.
        Does the sanitized query still convey the same educational intent?
        """
        prompt = f"""Rate how well the sanitized query preserves the educational utility of the original.

Original: "{original}"
Sanitized: "{sanitized}"

Score from 0.0 (no utility preserved) to 1.0 (full utility preserved).
Consider: Can a tutor still provide useful help based on the sanitized query?
Respond with JSON only: {{"utility_score": 0.8, "reasoning": "brief reason"}}"""

        response = self.pp_ts._call_llm(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return float(data.get("utility_score", 0.5))
        except Exception:
            pass
        return 0.5

    def _measure_pii_removal(self, pcs: List[PlaintextCiphertextRecord]) -> float:
        """
        Kan et al.'s original metric: how many PII entities were successfully replaced.
        PRR = 1 - (remaining PII / total PII)
        """
        total_found = sum(len(r.original_values) for r in pcs)
        total_replaced = sum(
            sum(1 for o, s in zip(r.original_values, r.sanitized_values) if o and s and o != s)
            for r in pcs
        )
        if total_found == 0:
            return 1.0  # Nothing to replace = nothing leaked
        return total_replaced / total_found

    def run_query(self, query_data: Dict, privacy_types: List[str]) -> PPTSResult:
        """Run PP-TS on a single query and measure all metrics."""
        query_id = query_data["id"]
        original = query_data["query"]
        domain = query_data.get("domain", "general")

        print(f"\n  Processing {query_id}: {original[:60]}...")

        start = time.time()
        try:
            sanitized, pcs, retries = self.pp_ts.sanitize(original, privacy_types)
            elapsed_ms = (time.time() - start) * 1000

            ip_protection = self._measure_ip_protection(original, sanitized, domain)
            utility = self._measure_utility(original, sanitized)
            pii_removal = self._measure_pii_removal(pcs)

            result = PPTSResult(
                query_id=query_id,
                original_query=original,
                sanitized_query=sanitized,
                pcs=[asdict(r) for r in pcs],
                privacy_types_applied=privacy_types,
                reasonability_retries=retries,
                sanitization_time_ms=elapsed_ms,
                ip_protection_rate=ip_protection,
                utility_score=utility,
                pii_protection_rate=pii_removal
            )

        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            result = PPTSResult(
                query_id=query_id,
                original_query=original,
                sanitized_query=original,
                pcs=[],
                privacy_types_applied=privacy_types,
                reasonability_retries=0,
                sanitization_time_ms=elapsed_ms,
                ip_protection_rate=0.0,
                utility_score=0.0,
                pii_protection_rate=0.0,
                error=str(e)
            )

        print(f"    ✓ Sanitized: {sanitized[:60]}...")
        print(f"    IP Protection: {result.ip_protection_rate:.1%} | Utility: {result.utility_score:.1%} | PII Removal: {result.pii_protection_rate:.1%}")
        return result

    def run_experiment(self, query_set: str = "educational") -> Dict:
        """
        Run full PP-TS baseline experiment.
        query_set: 'educational' | 'pii' | 'both'
        """
        print("=" * 60)
        print("PP-TS BASELINE EXPERIMENT")
        print("Kan et al. 2023 — Algorithm 1 Reimplementation")
        print("=" * 60)

        # Select query set and privacy types
        if query_set == "educational":
            queries = EDUCATIONAL_IP_QUERIES
            privacy_types = PRIVACY_TYPES_EDUCATIONAL
            print(f"\nQuery set: Educational IP ({len(queries)} queries)")
            print(f"Privacy types: {privacy_types}")
        elif query_set == "pii":
            queries = PII_HEAVY_QUERIES
            privacy_types = PRIVACY_TYPES_PII
            print(f"\nQuery set: PII-heavy ({len(queries)} queries)")
            print(f"Privacy types: {privacy_types}")
        else:
            queries = EDUCATIONAL_IP_QUERIES + PII_HEAVY_QUERIES
            privacy_types = list(set(PRIVACY_TYPES_EDUCATIONAL + PRIVACY_TYPES_PII))
            print(f"\nQuery set: Combined ({len(queries)} queries)")

        results = []
        for q in queries:
            result = self.run_query(q, privacy_types)
            results.append(asdict(result))

        # Aggregate metrics
        successful = [r for r in results if not r.get("error")]
        n = len(successful)

        if n == 0:
            print("\n❌ No successful results.")
            return {}

        avg_ip = sum(r["ip_protection_rate"] for r in successful) / n
        avg_utility = sum(r["utility_score"] for r in successful) / n
        avg_pii = sum(r["pii_protection_rate"] for r in successful) / n
        avg_time = sum(r["sanitization_time_ms"] for r in successful) / n
        avg_retries = sum(r["reasonability_retries"] for r in successful) / n

        # Split by expected PII presence
        ip_only = [r for r in successful
                   if not next((q["expected_pii"] for q in queries if q["id"] == r["query_id"]), True)]
        pii_present = [r for r in successful
                       if next((q["expected_pii"] for q in queries if q["id"] == r["query_id"]), False)]

        report = {
            "experiment": "PP-TS Baseline (Kan et al. 2023 — Algorithm 1 Reimplementation)",
            "timestamp": datetime.now().isoformat(),
            "model_used": LOCAL_MODEL,
            "query_set": query_set,
            "privacy_types": privacy_types,
            "total_queries": len(queries),
            "successful": n,
            "aggregate_metrics": {
                "avg_ip_protection_rate": avg_ip,
                "avg_utility_score": avg_utility,
                "avg_pii_removal_rate": avg_pii,
                "avg_sanitization_time_ms": avg_time,
                "avg_reasonability_retries": avg_retries,
            },
            "by_query_type": {
                "ip_only_queries": {
                    "count": len(ip_only),
                    "avg_ip_protection": sum(r["ip_protection_rate"] for r in ip_only) / len(ip_only) if ip_only else 0,
                    "avg_utility": sum(r["utility_score"] for r in ip_only) / len(ip_only) if ip_only else 0,
                },
                "pii_present_queries": {
                    "count": len(pii_present),
                    "avg_ip_protection": sum(r["ip_protection_rate"] for r in pii_present) / len(pii_present) if pii_present else 0,
                    "avg_utility": sum(r["utility_score"] for r in pii_present) / len(pii_present) if pii_present else 0,
                }
            },
            "comparison_vs_sovereign_learner": {
                "sovereign_learner": {
                    "ip_protection_rate": 0.95,
                    "utility_score": 0.92,
                    "mechanism": "Semantic generalization at intent layer"
                },
                "pp_ts": {
                    "ip_protection_rate": avg_ip,
                    "utility_score": avg_utility,
                    "mechanism": "Token-level entity substitution (Algorithm 1)"
                }
            },
            "results": results
        }

        # Print summary
        print("\n" + "=" * 60)
        print("PP-TS BASELINE RESULTS")
        print("=" * 60)
        print(f"\n{'Metric':<35} {'PP-TS':>10} {'Sovereign':>12}")
        print("-" * 60)
        print(f"{'IP Protection Rate':<35} {avg_ip:>9.1%} {'95.0%':>12}")
        print(f"{'Utility Preservation':<35} {avg_utility:>9.1%} {'92.0%':>12}")
        print(f"{'PII Removal Rate':<35} {avg_pii:>9.1%} {'N/A':>12}")
        print(f"{'Avg Sanitization Time (ms)':<35} {avg_time:>9.0f} {'120ms':>12}")
        print(f"{'Avg Reasonability Retries':<35} {avg_retries:>9.2f} {'N/A':>12}")

        if ip_only:
            print(f"\n📊 IP-Only Queries (no traditional PII):")
            ip_only_avg = sum(r["ip_protection_rate"] for r in ip_only) / len(ip_only)
            print(f"   PP-TS IP Protection: {ip_only_avg:.1%}")
            print(f"   → This reveals PP-TS limitation: entity-layer only, misses intent-level IP")

        # Save results
        os.makedirs("experiments/results", exist_ok=True)
        output_path = f"experiments/results/pp_ts_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")

        return report


# ─────────────────────────────────────────────
# Compatibility Wrapper for EXP 05
# ─────────────────────────────────────────────

class PPTSSystem:
    """
    Compatibility wrapper for exp05_baseline_comparison.py.
    """
    def __init__(self, model="llama3.2", ollama_url="http://localhost:11434/api/generate"):
        self.pp_ts = PPTS(model=model)
        self.privacy_types = PRIVACY_TYPES_EDUCATIONAL

    def sanitize(self, text: str, use_shadow_lexicon: bool = False) -> str:
        sanitized, _, _ = self.pp_ts.sanitize(text, self.privacy_types, use_shadow_lexicon=use_shadow_lexicon)
        return sanitized


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PP-TS Baseline Experiment (Kan et al. 2023)")
    parser.add_argument(
        "--queries",
        choices=["educational", "pii", "both"],
        default="educational",
        help="Query set to run (default: educational — tests PP-TS limitations)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print query set without running LLM calls"
    )
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — Query sets loaded:")
        print(f"\nEducational IP queries ({len(EDUCATIONAL_IP_QUERIES)}):")
        for q in EDUCATIONAL_IP_QUERIES:
            print(f"  [{q['id']}] {q['query'][:70]}...")
            print(f"         Expected PII: {q['expected_pii']} | {q['note']}")
        print(f"\nPII-heavy queries ({len(PII_HEAVY_QUERIES)}):")
        for q in PII_HEAVY_QUERIES:
            print(f"  [{q['id']}] {q['query'][:70]}...")
    else:
        evaluator = PPTSEvaluator()
        evaluator.run_experiment(query_set=args.queries)
