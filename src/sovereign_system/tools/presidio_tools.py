from crewai.tools import BaseTool

def _robust_str(val: Any) -> str:
    if isinstance(val, dict):
        if "description" in val: return str(val.get("description", str(val)))
        for v in val.values():
            if isinstance(v, str): return v
    return str(val)

from typing import Type, List
from pydantic import BaseModel, Field

def _robust_str(val: Any) -> str:
    if isinstance(val, dict):
        if "description" in val: return str(val.get("description", str(val)))
        for v in val.values():
            if isinstance(v, str): return v
    return str(val)

from typing import Any
from sovereign_system.security.guard import guard

class PresidioScanInput(BaseModel):
    text: Any

class PresidioScanTool(BaseTool):
    name: str = "pii_scanner"
    description: str = "Scans text for PII using Microsoft Presidio (Names, IDs, Locations, etc.)"
    args_schema: Type[BaseModel] = PresidioScanInput

    def _run(self, text: Any) -> str:
        # Immortal Robust Conversion
        text = _robust_str(text)

        detections = guard.scan_for_pii(text)
        if not detections:
            return "No obvious PII detected by Presidio."
        
        # Return unique detections
        unique_det = list(set(detections))
        return f"DETECTED PII EXAMPLES: {', '.join(unique_det)}"
