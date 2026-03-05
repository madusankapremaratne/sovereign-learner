from typing import Any, Type, List, Optional
from pydantic import BaseModel, Field

def _robust_str(val: Any) -> str:
    if isinstance(val, dict):
        if "description" in val: return str(val.get("description", str(val)))
        if "value" in val: return str(val["value"])
        for v in val.values():
            if isinstance(v, str): return v
    return str(val)

from crewai.tools import BaseTool
import re
import json
from sovereign_system.security.guard import guard

# ─────────────────────────────────────────────────────────────────────────────
# General PII Mapping (Presidio Entity Types to Natural Language)
# ─────────────────────────────────────────────────────────────────────────────
PRESIDIO_PII_MAPPING = {
    "PERSON": "the individual",
    "LOCATION": "a physical location",
    "EMAIL_ADDRESS": "an electronic contact",
    "PHONE_NUMBER": "a telephonic contact",
    "DATE_TIME": "a specific point in time",
    "US_SSN": "a government identifier",
    "UK_NHS": "a medical identifier",
    "IBAN_CODE": "a financial identifier",
    "CREDIT_CARD": "a payment method",
    "IP_ADDRESS": "a network address",
    
    # Educational IP (Phase 3 Ensemble results)
    "INSTITUTIONAL_MARKER": "the academic institution",
    "ASSESSMENT_TYPE": "a formal academic assessment",
    "LEARNING_METRIC": "a standardized learning metric",
    "CURRICULUM_DOMAIN": "a foundational academic discipline",
}

# ─────────────────────────────────────────────────────────────────────────────
# Universal NLU Intent Schema (Generalization of all semantic tools)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Intent Mirrors (Cross-Domain Surrogates - Phase 5)
# ─────────────────────────────────────────────────────────────────────────────
SEMANTIC_MIRRORS = {
    "snips/educational_concept": "standardized business compliance training",
    "snips/technical_method": "a common industrial manufacturing procedure",
    "snips/product": "a commercially available software suite",
    "snips/biomedical": "a general laboratory workflow",
}

FALLBACK_BY_TYPE = {
    "numeric_id": "a unique system identifier",
    "acronym": "a technical acronym",
    "proper_noun": "a specific domain entity",
    "default": "a relevant domain entity"
}

# ─────────────────────────────────────────────────────────────────────────────
# UniversalNER Taxonomy (Phase 6 - 13K+ Entity Support)
# ─────────────────────────────────────────────────────────────────────────────
# This maps specific open-domain entity types to safe semantic abstractions.
UNIVERSAL_NER_TAXONOMY = {
    "STEM": "a specialized technical element",
    "Algorithm": "a foundational computational procedure",
    "Dataset": "a standardized academic dataset",
    "Medical Condition": "a specific health-related state",
    "Programming Language": "a standard development language",
    "Methodology": "a specialized research method",
    "Chemical": "a specific laboratory compound",
    "Academic Subject": "a foundational academic discipline",
    "Protein": "a specific biological marker",
    "Field of Study": "a major academic domain",
    "Protocol": "a standardized technical workflow"
}

UNIVERSAL_NLU_ONTOLOGY = {
    # Numerical & Quantitative (snips/amount, snips/percentage, etc.)
    "snips/amount": {
        "abstract": "a significant quantity",
        "fuzzy_logic": True
    },
    "snips/percentage": {
        "abstract": "a relevant percentage value",
        "fuzzy_logic": True
    },
    "snips/datetime": {
        "abstract": "a specific point in time",
    },
    "snips/duration": {
        "abstract": "a period of time",
    },
    
    # Entities (Generalization of keywords)
    "snips/person": {
        "abstract": "the individual",
    },
    "snips/organization": {
        "abstract": "a professional organization",
    },
    "snips/educational_concept": {
        "abstract": "a foundational academic concept",
    },
    "snips/technical_method": {
        "abstract": "a specialized technical procedure",
    },
    "snips/product": {
        "abstract": "a specific technical tool",
    },
    "snips/location": {
        "abstract": "a geographic area",
    },
    "snips/identifier": {
        "abstract": "a unique system identifier",
    }
}

SEMANTIC_TAXONOMY = {
    "gene_editing": {"keywords": ["crispr", "cas9"], "type": "snips/technical_method"},
    "university_module": {"keywords": ["module", "bbb", "aaa", "ccc"], "type": "snips/educational_concept"},
    "platform": {"keywords": ["vle", "ouse", "moodle"], "type": "snips/product"},
    "assessment": {"keywords": ["tma", "icma", "ema"], "type": "snips/educational_concept"},
    "student_id": {"pattern": r"\b\d{5,8}\b", "type": "snips/identifier"},
}

class SemanticGeneralizationInput(BaseModel):
    query: Any
    sensitive_entities: Any


class IntentAbstractorTool(BaseTool):
    name: str = "intent_abstractor"
    description: str = (
        "Transforms sensitive queries into semantically equivalent, naturally phrased "
        "generalizations using domain-aware vocabulary. Replaces specific identifiers "
        "with meaningful general terms (not placeholders). Returns sanitized query and "
        "bidirectional mapping for recontextualization."
    )
    args_schema: Type[BaseModel] = SemanticGeneralizationInput
    placeholder_map: dict = {}

    def _run(self, query: Any, sensitive_entities: Any) -> str:
        # Immortal Robust Conversion
        query = _robust_str(query)
        sensitive_entities = _robust_str(sensitive_entities)

        """
        Domain-aware semantic generalization.
        
        Strategy:
        1. Parse entities from the comma-separated input
        2. For each entity, determine its semantic category via taxonomy lookup
        3. Apply natural language generalization (not placeholder tokens)
        4. Perform case-insensitive substitution in the query
        5. Apply pattern-based substitutions for PII (IDs, percentages)
        6. Return sanitized query + full bidirectional mapping as JSON
        """
        self.placeholder_map = {}
        used_generalizations = {}

        def get_unique_gen(base_gen):
            if base_gen not in used_generalizations:
                used_generalizations[base_gen] = 0
                return base_gen
            used_generalizations[base_gen] += 1
            return f"{base_gen} ({used_generalizations[base_gen] + 1})"

        # ── Step 0: Presidio-based bootstrapping (General PII) ────────────────
        pii_hits = guard.scan_for_pii_entities(query)
        for text, entity_type in pii_hits:
            if entity_type in PRESIDIO_PII_MAPPING:
                # Use a unique natural language generalization
                if text not in self.placeholder_map:
                    self.placeholder_map[text] = get_unique_gen(PRESIDIO_PII_MAPPING[entity_type])

        entities = [e.strip() for e in sensitive_entities.split(",") if e.strip()]
        sanitized = query

        # ── Step 1: Entity-based generalization ──────────────────────────────
        for entity in entities:
            if not entity: continue
            # Only override if not already mapped by Presidio or if taxonomy is more specific
            generalization = self._get_generalization(entity)
            if entity not in self.placeholder_map or generalization != FALLBACK_BY_TYPE["default"]:
                self.placeholder_map[entity] = get_unique_gen(generalization)

        # Apply substitutions
        for entity, replacement in self.placeholder_map.items():
            sanitized = re.sub(
                re.escape(entity),
                replacement,
                sanitized,
                flags=re.IGNORECASE
            )

        # ── Step 2: Pattern-based PII & Numerical Abstraction (Phase 2) ───────
        # 2a. Student IDs: 5-8 digit standalone numbers
        sanitized = re.sub(
            r'(?<!\d)(\d{5,8})(?!\d)',
            lambda m: self._map_pattern(m.group(0), get_unique_gen("a registered student")),
            sanitized
        )

        # 2b. Score Abstraction (e.g., "score of 30%", "achieved 85%")
        sanitized = re.sub(
            r'\b(\d{1,3}%)',
            lambda m: self._map_pattern(m.group(0), self._get_fuzzed_score(m.group(0))),
            sanitized
        )

        # 2c. Engagement Fuzzing (e.g., "active for 10 days", "accessed 92 resources")
        sanitized = re.sub(
            r'(\d+)\s+(days|resources|sessions|interactions)',
            lambda m: self._map_pattern(m.group(0), f"{self._get_fuzzed_count(m.group(1))} {m.group(2)}"),
            sanitized
        )

        # 2d. IMD / percentage bands
        sanitized = re.sub(
            r'\b(\d{1,3}-\d{1,3}%)',
            lambda m: self._map_pattern(m.group(0), get_unique_gen("a socioeconomic deprivation band")),
            sanitized
        )

        # 2e. Email addresses
        sanitized = re.sub(
            r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b',
            lambda m: self._map_pattern(m.group(0), get_unique_gen("a contact email address")),
            sanitized
        )

        # ── Step 3: Grammatical coherence pass ───────────────────────────────
        # Fix doubled articles: "a a standard" → "a standard"
        sanitized = re.sub(r'\b(a|an)\s+(a|an)\s+', r'a ', sanitized)

        # Fix article-vowel agreement: "a optimization" → "an optimization"
        sanitized = re.sub(r'\ba ([aeiou])', r'an \1', sanitized, flags=re.IGNORECASE)

        # ── Step 4: Compose output ────────────────────────────────────────────
        return (
            f"SANITIZED: {sanitized}\n"
            f"MAPPING: {json.dumps(self.placeholder_map, indent=2)}\n"
            f"COVERAGE: {self._compute_coverage(query, sanitized):.1%} of sensitive content generalized"
        )


    def _get_fuzzed_count(self, match: str) -> str:
        """Fuzzes a resource or day count into natural language buckets."""
        try:
            num = int(re.search(r'\d+', match).group())
            if num < 5: return "a few"
            if num < 20: return "a moderate number of"
            if num < 100: return "a significant volume of"
            return "a high volume of"
        except:
            return "multiple"

    def _get_fuzzed_score(self, match: str) -> str:
        """Fuzzes an academic score into qualitative buckets."""
        try:
            num = int(re.search(r'\d+', match).group())
            if "%" in match:
                if num < 40: return "a score below the passing threshold"
                if num < 60: return "a satisfactory marginal score"
                if num < 85: return "a strong merit-level score"
                return "a high distinction-level score"
            return "the numerical benchmark"
        except:
            return "the academic result"

    # DEPRECATED
    def _get_generalization_old(self, entity: Any) -> str:
        return "a relevant domain entity"

    def _get_generalization(self, entity: Any) -> str:
        """
        Standardized NLU Ontology Lookup with Intent Substitution (Phase 5).
        """
        entity_lower = entity.lower().strip()
        
        # A. Check mirrors FIRST (High Abstraction Path)
        for key, config in SEMANTIC_TAXONOMY.items():
            if any(k in entity_lower for k in config.get("keywords", [])):
                nlu_type = config.get("type", "snips/educational_concept")
                # Use mirror if available for higher protection
                if nlu_type in SEMANTIC_MIRRORS:
                    return SEMANTIC_MIRRORS[nlu_type]
                return UNIVERSAL_NLU_ONTOLOGY.get(nlu_type, {}).get("abstract", "a domain entity")

        # B. Direct Pattern Match (Identifier / Snips Patterns)
        if re.match(r'^\d{5,8}$', entity.strip()):
            return UNIVERSAL_NLU_ONTOLOGY["snips/identifier"]["abstract"]

        # C. UniversalNER-Inspired Category Matching (Enhanced Open-Domain Support)
        # Check first for direct technical patterns (Methods/Algorithms/Datasets)
        if any(w in entity_lower for w in ["protocol", "method", "workflow", "algorithm", "procedure"]):
            return UNIVERSAL_NER_TAXONOMY["Methodology"]
        if any(w in entity_lower for w in ["dataset", "repository", "corpus", "database"]):
            return UNIVERSAL_NER_TAXONOMY["Dataset"]
        if any(w in entity_lower for w in ["framework", "library", "sdk", "api"]):
            return UNIVERSAL_NER_TAXONOMY["Programming Language"]

        # D. Fallback by lexical features (Standard Snips Entity Recognition)
        if entity.strip()[0].isupper() and len(entity.split()) <= 3:
            return UNIVERSAL_NLU_ONTOLOGY["snips/organization"]["abstract"]
            
        return FALLBACK_BY_TYPE["default"]

    def _map_pattern(self, original: Any, generalization: Any) -> str:
        """Record a pattern-matched entity in the mapping and return its generalization."""
        if original not in self.placeholder_map:
            self.placeholder_map[original] = generalization
        return generalization

    def _compute_coverage(self, original: Any, sanitized: Any) -> float:
        """
        Estimate what fraction of original content was successfully generalized.
        Measured as reduction in unique content tokens.
        """
        original_tokens = set(original.lower().split())
        sanitized_tokens = set(sanitized.lower().split())
        removed = original_tokens - sanitized_tokens
        if not original_tokens:
            return 1.0
        return min(1.0, len(removed) / max(1, len(self.placeholder_map)))

class RecontextualizationInput(BaseModel):
    response: Any
    mapping: str = ""

class ContextRestorerTool(BaseTool):
    name: str = "context_restorer"
    description: str = "Maps generalized cloud responses back to the learner's specific context"
    args_schema: Type[BaseModel] = RecontextualizationInput
    
    def _run(self, response: Any, mapping: Any) -> str:
        # Immortal Robust Conversion
        response = _robust_str(response)
        mapping = _robust_str(mapping)

        """
        Re-contextualize the response using the provided mapping.
        """
        # Parse mapping string back to dict if needed
        try:
            mapping_dict = eval(mapping) if isinstance(mapping, str) else mapping
        except:
            return f"Error parsing mapping: {mapping}"
            
        restored_response = response
        
        # Replace generalizations (values) with original terms (keys)
        # Sort by length descending to avoid partial matches
        sorted_pairs = sorted(mapping_dict.items(), key=lambda x: len(str(x[1])), reverse=True)
        
        for original, generalization in sorted_pairs:
            restored_response = restored_response.replace(str(generalization), str(original))
            
        return restored_response
            

            
class AdversarialAuditInput(BaseModel):
    generalized_query: Any

class AdversarialAuditTool(BaseTool):
    name: str = "adversarial_auditor"
    description: str = "Performs a dataset-blind privacy audit on generalized queries to detect remaining contextual fingerprints."
    args_schema: Type[BaseModel] = AdversarialAuditInput

    def _run(self, generalized_query: Any) -> str:
        generalized_query = _robust_str(generalized_query)
        is_safe, reason, risk = guard.audit_generalized_query(generalized_query)
        
        return json.dumps({
            "status": "APPROVED" if is_safe else "REJECTED",
            "reason": reason,
            "risk_score": risk
        })
