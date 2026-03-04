from crewai.tools import BaseTool

def _robust_str(val: Any) -> str:
    if isinstance(val, dict):
        if "description" in val: return str(val.get("description", str(val)))
        for v in val.values():
            if isinstance(v, str): return v
    return str(val)

from typing import Type, Optional
from pydantic import BaseModel, Field

def _robust_str(val: Any) -> str:
    if isinstance(val, dict):
        if "description" in val: return str(val.get("description", str(val)))
        for v in val.values():
            if isinstance(v, str): return v
    return str(val)

from typing import Any
import re
import json

# ─────────────────────────────────────────────────────────────────────────────
# Domain-aware semantic generalisation taxonomy
# Each entry: (detection_keywords, generalized_form_template)
# The template uses {entity} where the original term's category is implied.
# ─────────────────────────────────────────────────────────────────────────────
SEMANTIC_TAXONOMY = {
    # ── Molecular Biology & Biomedical ────────────────────────────────────────
    "gene_editing_tool": {
        "keywords": ["crispr", "cas9", "cas12", "talen", "zinc finger", "base editor"],
        "generalization": "a precision gene-editing technique",
        "category": "biomedical_method"
    },
    "cell_line": {
        "keywords": ["hek293", "hela", "jurkat", "mcf7", "cho", "vero", "cos7",
                     "nih 3t3", "pc12", "k562", "u937", "thp-1"],
        "generalization": "a standard mammalian cell line",
        "category": "biological_model"
    },
    "cancer_cell_line": {
        "keywords": ["hct116", "a549", "u87", "t47d", "lncap", "pc3", "skbr3"],
        "generalization": "a human cancer cell line",
        "category": "biological_model"
    },
    "model_organism": {
        "keywords": ["c. elegans", "drosophila", "zebrafish", "danio", "xenopus",
                     "arabidopsis", "mus musculus"],
        "generalization": "a standard model organism",
        "category": "biological_model"
    },
    "molecular_assay": {
        "keywords": ["pcr", "elisa", "western blot", "flow cytometry", "rna-seq",
                     "chip-seq", "atac-seq", "immunofluorescence", "ihc", "facs"],
        "generalization": "a standard molecular assay",
        "category": "biomedical_method"
    },
    "drug_compound": {
        "keywords": ["rapamycin", "doxorubicin", "imatinib", "gleevec", "taxol",
                     "paclitaxel", "tamoxifen", "metformin"],
        "generalization": "an experimental pharmacological compound",
        "category": "chemical_entity"
    },
    "gene_or_protein": {
        "keywords": ["tp53", "brca1", "brca2", "egfr", "vegf", "her2", "akt",
                     "mtor", "ras", "myc", "p53", "stat3"],
        "generalization": "a key signalling gene or protein",
        "category": "molecular_entity"
    },
    "viral_vector": {
        "keywords": ["aav", "lentiviral", "adenoviral", "retroviral", "baculovirus"],
        "generalization": "a viral delivery vector",
        "category": "biomedical_method"
    },

    # ── Research Grants & Funding ─────────────────────────────────────────────
    "nih_grant": {
        "keywords": ["nih r01", "nih r21", "nih r15", "nih k99", "nih u01", "nih p01"],
        "generalization": "a federal research grant",
        "category": "funding_mechanism"
    },
    "nsf_grant": {
        "keywords": ["nsf grant", "nsf award", "nsf career", "nsf reu"],
        "generalization": "a national science foundation award",
        "category": "funding_mechanism"
    },
    "eu_grant": {
        "keywords": ["horizon 2020", "horizon europe", "erc grant", "marie curie"],
        "generalization": "a European research funding scheme",
        "category": "funding_mechanism"
    },

    # ── Research Institutions & Companies ────────────────────────────────────
    "pharma_company": {
        "keywords": ["pfizer", "moderna", "astrazeneca", "genentech", "novartis",
                     "roche", "merck", "johnson & j", "bayer", "sanofi"],
        "generalization": "a major pharmaceutical company",
        "category": "institution"
    },
    "tech_company": {
        "keywords": ["google deepmind", "openai", "anthropic", "meta ai", "microsoft research",
                     "ibm research", "nvidia research"],
        "generalization": "a leading AI research organisation",
        "category": "institution"
    },

    # ── Computer Science & AI ─────────────────────────────────────────────────
    "specific_llm": {
        "keywords": ["gpt-4", "gpt4", "claude", "gemini", "llama", "mistral",
                     "falcon", "phi-3", "qwen"],
        "generalization": "a large language model",
        "category": "ai_system"
    },
    "ml_framework": {
        "keywords": ["pytorch", "tensorflow", "jax", "keras", "huggingface",
                     "scikit-learn", "xgboost", "lightgbm"],
        "generalization": "a machine learning framework",
        "category": "software_tool"
    },
    "hardware_accelerator": {
        "keywords": ["h100", "a100", "v100", "rtx 4090", "tpu v4", "tpu v5",
                     "nvidia", "amd mi300"],
        "generalization": "a high-performance computing accelerator",
        "category": "hardware"
    },
    "algorithm": {
        "keywords": ["transformer", "bert", "gpt", "vae", "gan", "diffusion model",
                     "reinforcement learning", "ppo", "sac", "dqn"],
        "generalization": "a deep learning architecture",
        "category": "ai_method"
    },
    "database_system": {
        "keywords": ["chromadb", "pinecone", "weaviate", "qdrant", "milvus",
                     "postgres", "mongodb", "redis", "elasticsearch"],
        "generalization": "a database management system",
        "category": "software_tool"
    },

    # ── Legal & Financial ─────────────────────────────────────────────────────
    "law_firm": {
        "keywords": ["skadden", "latham", "kirkland", "weil gotshal", "sullivan & cromwell"],
        "generalization": "a major law firm",
        "category": "institution"
    },
    "legal_jurisdiction": {
        "keywords": ["gdpr", "ccpa", "hipaa", "ferpa", "coppa", "pipeda"],
        "generalization": "a data privacy regulation",
        "category": "legal_framework"
    },
    "financial_instrument": {
        "keywords": ["series a", "series b", "ipo", "spac", "convertible note",
                     "safe agreement"],
        "generalization": "an equity financing instrument",
        "category": "financial_entity"
    },

    # ── Education & Student Data ───────────────────────────────────────────────
    "student_id": {
        "keywords": [],  # Handled by pattern matching below
        "pattern": r"\b\d{5,8}\b",
        "generalization": "a registered student",
        "category": "pii_identity"
    },
    "geographic_region": {
        "keywords": ["east anglian", "west midlands", "south east", "north west",
                     "yorkshire", "scotland", "wales", "london region"],
        "generalization": "a regional area",
        "category": "pii_location"
    },
    "imd_band": {
        "keywords": [],
        "pattern": r"\b\d{1,2}-\d{1,2}%",
        "generalization": "a socioeconomic deprivation band",
        "category": "pii_demographic"
    },

    # ── Proprietary Methods (catch-all for domain-specific terms) ─────────────
    "synthesis_protocol": {
        "keywords": ["protocol", "procedure", "synthesis route", "workflow",
                     "pipeline", "assay protocol", "treatment regimen"],
        "generalization": "a proprietary research procedure",
        "category": "method"
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Fallback generalizations by grammatical context
# Used when no taxonomy match is found
# ─────────────────────────────────────────────────────────────────────────────
FALLBACK_BY_TYPE = {
    "numeric_id":    "a unique identifier",
    "proper_noun":   "a domain-specific entity",
    "acronym":       "a specialized technique",
    "compound":      "a research-specific term",
    "default":       "a relevant domain entity",
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
        entities = [e.strip() for e in sensitive_entities.split(",") if e.strip()]
        sanitized = query

        # ── Step 1: Entity-based generalization ──────────────────────────────
        for entity in entities:
            generalization = self._get_generalization(entity)
            self.placeholder_map[entity] = generalization

            # Replace all occurrences (case-insensitive)
            sanitized = re.sub(
                re.escape(entity),
                generalization,
                sanitized,
                flags=re.IGNORECASE
            )

        # ── Step 2: Pattern-based PII sweeps (catches anything missed) ───────
        # Student IDs: 5-8 digit standalone numbers
        sanitized = re.sub(
            r'(?<!\d)(\d{5,8})(?!\d)',
            lambda m: self._map_pattern(m.group(0), "a registered student"),
            sanitized
        )

        # IMD / percentage bands like "10-20%" or "90-100%"
        sanitized = re.sub(
            r'\b(\d{1,3}-\d{1,3}%)',
            lambda m: self._map_pattern(m.group(0), "a socioeconomic deprivation band"),
            sanitized
        )

        # Email addresses
        sanitized = re.sub(
            r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b',
            lambda m: self._map_pattern(m.group(0), "a contact email address"),
            sanitized
        )

        # ── Step 3: Grammatical coherence pass ───────────────────────────────
        # Fix doubled articles: "a a standard" → "a standard"
        sanitized = re.sub(r'\b(a|an)\s+(a|an)\s+', r'a ', sanitized)

        # Fix article-vowel agreement: "a optimization" → "an optimization"
        sanitized = re.sub(r'\ba ([aeiou])', r'an \1', sanitized, flags=re.IGNORECASE)

        # ── Step 4: Compose output ────────────────────────────────────────────
        output = {
            "sanitized_query": sanitized,
            "mapping": self.placeholder_map,
            "entity_count": len(self.placeholder_map),
            "generalization_coverage": self._compute_coverage(query, sanitized)
        }

        return (
            f"SANITIZED: {sanitized}\n"
            f"MAPPING: {json.dumps(self.placeholder_map, indent=2)}\n"
            f"COVERAGE: {output['generalization_coverage']:.1%} of sensitive content generalized"
        )

    def _get_generalization(self, entity: Any) -> str:
        """
        Look up the most semantically appropriate generalization for an entity.
        Tries taxonomy keyword match first, then pattern match, then fallback.
        """
        entity_lower = entity.lower().strip()

        # ── Taxonomy keyword match ────────────────────────────────────────────
        for category, config in SEMANTIC_TAXONOMY.items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword in entity_lower or entity_lower in keyword:
                    return config["generalization"]

        # ── Pattern-based detection ───────────────────────────────────────────
        if re.match(r'^\d{5,8}$', entity.strip()):
            return FALLBACK_BY_TYPE["numeric_id"]

        if re.match(r'^[A-Z]{2,6}[0-9]*$', entity.strip()):
            # Looks like an acronym (e.g. "HEK293", "CRISPR", "VEGF")
            return FALLBACK_BY_TYPE["acronym"]

        if entity.strip()[0].isupper() and len(entity.split()) <= 3:
            # Capitalised proper noun
            return FALLBACK_BY_TYPE["proper_noun"]

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
        
        # Replace placeholders with original terms
        for placeholder, original in mapping_dict.items():
            restored_response = restored_response.replace(placeholder, original)
            
        return restored_response
            

            