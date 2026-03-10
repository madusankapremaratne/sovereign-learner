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

from sovereign_system.security.guard import guard

class ZoneValidationInput(BaseModel):
    query: Any
    proposed_zone: int = Field(..., description=None)
    ner_confidence: float = Field(1.0, description=None)

class ZoneValidationTool(BaseTool):
    """
    Validates zone classification to prevent roleplay attacks from 
    forcing inappropriate zone assignments (e.g., Zone 3 for sensitive queries).
    Also supports Conservative Routing Fallback under NER uncertainty.
    
    Addresses EXP05 Critical Vulnerability & EXP08B Conservative Routing.
    """
    name: str = "zone_validator"
    description: str = (
        "Validate if a specific zone (0-3) is safe for a query. "
        "Input: query string, proposed_zone int, and optionally ner_confidence float. "
        "Use this tool before finalizing any classification to enforce privacy rules."
    )
    args_schema: Type[BaseModel] = ZoneValidationInput

    def _run(self, query: Any, proposed_zone: int, ner_confidence: float = 1.0) -> str:
        # Immortal Robust Conversion & Type Casting
        query = _robust_str(query)
        try:
            proposed_zone = int(_robust_str(proposed_zone))
            ner_confidence = float(_robust_str(ner_confidence))
        except (ValueError, TypeError):
            # Fallback for LLM hallucinations in types
            proposed_zone = 3
            ner_confidence = 1.0

        is_valid, reason = guard.validate_zone_classification(query, proposed_zone, ner_confidence)
        
        if not is_valid:
            if "NER uncertainty" in reason:
                return f"⚠️ SAFETY OVERRIDE: {reason}\nSuggested Action: Re-route to Zone 0 to ensure local data sovereignty."
            return f"⚠️ ZONE VALIDATION FAILED: {reason}\nSuggested Action: Try a different lower-risk zone."
        
        return f"✅ Zone {proposed_zone} VALIDATED. VALIDATION COMPLETE. STOP using this tool. FINAL ANSWER: Zone {proposed_zone}."


class OutputSanitizerInput(BaseModel):
    text: Any
    sensitive_entities: Any
    placeholders: str = ""

class OutputSanitizerTool(BaseTool):
    """
    Sanitizes output by removing Chain-of-Thought artifacts and internal reasoning.
    
    Addresses EXP05 Vulnerability: CoT leakage exposing internal processing.
    """
    name: str = "output_sanitizer"
    description: str = (
        "Removes internal reasoning artifacts, chain-of-thought patterns, and "
        "agent metadata from outputs before presenting to the user. "
        "Can also scrub specific entities and placeholders if provided."
    )
    args_schema: Type[BaseModel] = OutputSanitizerInput

    def _run(self, text: Any, sensitive_entities: str = "", placeholders: str = "") -> str:
        # Immortal Robust Conversion
        text = _robust_str(text)
        sensitive_entities = _robust_str(sensitive_entities)
        placeholders = _robust_str(placeholders)

        entities = [e.strip() for e in sensitive_entities.split(",")] if sensitive_entities else []
        placeholders_list = [p.strip() for p in placeholders.split(",")] if placeholders else []
        
        sanitized = guard.sanitize_output(text, entities, placeholders_list)
        return f"SANITIZED OUTPUT: {sanitized}\n\nSTOP using this tool. Use this output as your Final Answer."


class PIIScrubberInput(BaseModel):
    text: Any

class PIIScrubberTool(BaseTool):
    """
    Scrubs PII from text before storing in local competency vectors.
    
    Addresses EXP05 Vulnerability: Local PII storage in competency vectors.
    """
    name: str = "pii_scrubber"
    description: str = (
        "Removes or anonymizes PII from text before storing in local ChromaDB. "
        "Ensures that even local storage maintains privacy protection. "
        "Uses Presidio if available, falls back to regex patterns."
    )
    args_schema: Type[BaseModel] = PIIScrubberInput

    def _run(self, text: Any) -> str:
        # Immortal Robust Conversion
        text = _robust_str(text)

        scrubbed = guard.scrub_pii_for_storage(text)
        return f"SCRUBBED TEXT: {scrubbed}\n\nSTOP using this tool. Proceed to storage."

class SafetyAuditInput(BaseModel):
    query: Any

class SafetyAuditTool(BaseTool):
    """
    Performs a deterministic safety scan for policy violations.
    
    Addresses EXP06 (Red Teaming) categories: Violence, Illegal Acts, Discrimination.
    """
    name: str = "safety_auditor"
    description: str = (
        "Scan a query for harmful intent, violence, illegal acts, discrimination, "
        "or other policy violations. Returns 'UNSAFE' with reason if violation found, "
        "otherwise 'SAFE'. Use this as the very first step in classification."
    )
    args_schema: Type[BaseModel] = SafetyAuditInput

    def _run(self, query: Any) -> str:
        # Immortal Robust Conversion
        query = _robust_str(query)

        is_unsafe, reason = guard.is_unsafe(query)
        if is_unsafe:
            return f"🚨 UNSAFE: Policy violation detected - {reason}. Suggested Action: Classify as Zone 0 (BLOCKED)."
        return "✅ SAFE: No deterministic safety violations detected."
