from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
from sovereign_system.utils.evaluators import SemanticPrivacyMetric
from deepeval.test_case import LLMTestCase

class PrivacyScanInput(BaseModel):
    original_query: str = Field(..., description="The original user query intent")
    cloud_response: str = Field(..., description="The response received from the cloud")
    sensitive_entities: List[str] = Field(..., description="List of sensitive entities to protect")

class PrivacyScanTool(BaseTool):
    name: str = "privacy_scanner"
    description: str = "Scans cloud response for IP leakage using adversarial LLM scoring"
    args_schema: Type[BaseModel] = PrivacyScanInput

    def _run(self, original_query: str, cloud_response: str, sensitive_entities: List[str]) -> str:
        # Check 1: Exact String Matching (Fast Fail)
        leaked = []
        response_lower = cloud_response.lower()
        for entity in sensitive_entities:
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
