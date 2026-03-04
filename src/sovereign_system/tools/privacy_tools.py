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

from sovereign_system.utils.evaluators import SemanticPrivacyMetric
from deepeval.test_case import LLMTestCase

class PrivacyScanInput(BaseModel):
    original_query: Any
    cloud_response: Any
    sensitive_entities: Any

class PrivacyScanTool(BaseTool):
    name: str = "privacy_scanner"
    description: str = "Scans cloud response for IP leakage using adversarial LLM scoring"
    args_schema: Type[BaseModel] = PrivacyScanInput

    def _run(self, original_query: Any, cloud_response: Any, sensitive_entities: Any) -> str:
        # Immortal Robust Conversion
        original_query = _robust_str(original_query)
        cloud_response = _robust_str(cloud_response)
        sensitive_entities = _robust_str(sensitive_entities)

        # Parse entities
        entities_list = [e.strip() for e in sensitive_entities.split(",")] if isinstance(sensitive_entities, str) else []
        
        # Check 1: Exact String Matching (Fast Fail)
        leaked = []
        response_lower = cloud_response.lower()
        for entity in entities_list:
            if entity.lower() in response_lower:
                leaked.append(entity)
        
        if leaked:
            return f"PRIVACY VIOLATION DETECTED: Found sensitive terms {leaked} in response."

        # Check 2: Adversarial LLM Check
        # We reuse the SemanticPrivacyMetric logic
        metric = SemanticPrivacyMetric(threshold=0.5)
        test_case = LLMTestCase(
            input=original_query,
            actual_output=cloud_response
        )
        
        # This calls the measure method which uses the LLM-as-a-judge
        score = metric.measure(test_case)
        
        if score < 0.5:
             return "PRIVACY VIOLATION DETECTED: Adversarial model reconstructed sensitive intent from the response."
             
        return "PASS: No privacy leakage detected. Response is safe. STOP using this tool. Proceed to final answer."
