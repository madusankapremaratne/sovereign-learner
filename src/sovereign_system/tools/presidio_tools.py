from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
from sovereign_system.security.guard import guard

class PresidioScanInput(BaseModel):
    text: str = Field(..., description="The text to scan for PII (can be query or response)")

class PresidioScanTool(BaseTool):
    name: str = "pii_scanner"
    description: str = "Scans text for PII using Microsoft Presidio (Names, IDs, Locations, etc.)"
    args_schema: Type[BaseModel] = PresidioScanInput

    def _run(self, text: str) -> str:
        detections = guard.scan_for_pii(text)
        if not detections:
            return "No obvious PII detected by Presidio."
        
        # Return unique detections
        unique_det = list(set(detections))
        return f"DETECTED PII EXAMPLES: {', '.join(unique_det)}"
