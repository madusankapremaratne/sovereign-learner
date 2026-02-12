from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sovereign_system.security.guard import guard

class ZoneValidationInput(BaseModel):
    query: str = Field(..., description="The original query to validate")
    proposed_zone: int = Field(..., description="The proposed privacy zone (0-3)")

class ZoneValidationTool(BaseTool):
    """
    Validates zone classification to prevent roleplay attacks from 
    forcing inappropriate zone assignments (e.g., Zone 3 for sensitive queries).
    
    Addresses EXP05 Critical Vulnerability: Jailbreak via roleplay causing 
    Zone 3 misclassification for sensitive queries.
    """
    name: str = "zone_validator"
    description: str = (
        "Validates that the proposed privacy zone is appropriate for the query content. "
        "Prevents manipulation attacks that try to force Zone 3 classification for sensitive data. "
        "Returns validation result and recommendation."
    )
    args_schema: Type[BaseModel] = ZoneValidationInput

    def _run(self, query: str, proposed_zone: int) -> str:
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone)
        
        if not is_valid:
            return f"⚠️ ZONE VALIDATION FAILED: {reason}"
        
        return f"✅ Zone {proposed_zone} validated: {reason}"


class OutputSanitizerInput(BaseModel):
    text: str = Field(..., description="The output text to sanitize")

class OutputSanitizerTool(BaseTool):
    """
    Sanitizes output by removing Chain-of-Thought artifacts and internal reasoning.
    
    Addresses EXP05 Vulnerability: CoT leakage exposing internal processing.
    """
    name: str = "output_sanitizer"
    description: str = (
        "Removes internal reasoning artifacts, chain-of-thought patterns, and "
        "agent metadata from outputs before presenting to the user. "
        "Prevents information leakage about the system's internal workings."
    )
    args_schema: Type[BaseModel] = OutputSanitizerInput

    def _run(self, text: str) -> str:
        sanitized = guard.sanitize_output(text)
        return sanitized


class PIIScrubberInput(BaseModel):
    text: str = Field(..., description="The text to scrub before storage")

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

    def _run(self, text: str) -> str:
        scrubbed = guard.scrub_pii_for_storage(text)
        return scrubbed
