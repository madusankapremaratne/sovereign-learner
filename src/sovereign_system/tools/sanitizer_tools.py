from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import re
import json

class OutputSanitizerInput(BaseModel):
    response: str = Field(..., description="The final recontextualized response to be delivered to the user")
    sensitive_entities: str = Field(..., description="Comma-separated list of original sensitive entities to ensure are NOT in the output")
    placeholders: str = Field(..., description="Comma-separated list of placeholders used during sanitization to ensure are NOT in the output")

class OutputSanitizerTool(BaseTool):
    name: str = "output_sanitizer"
    description: str = "Performs a final 'Zero-Leak' sweep of the response to remove metadata, thoughts, or leaked PII before delivery."
    args_schema: Type[BaseModel] = OutputSanitizerInput
    
    def _run(self, response: str, sensitive_entities: str, placeholders: str) -> str:
        """
        Final sanitization sweep.
        """
        # 1. Clean inputs
        entities = [e.strip() for e in sensitive_entities.split(",") if e.strip()]
        placeholders_list = [p.strip() for p in placeholders.split(",") if p.strip()]
        
        sanitized = response
        
        # 2. Block 'Thought' and 'Metadata' blocks if they exist in text
        # This prevents CoT leakage if the model outputs thoughts
        sanitized = re.sub(r"(?i)thought:.*?\n", "", sanitized)
        sanitized = re.sub(r"(?i)metadata:.*?\n", "", sanitized)
        sanitized = re.sub(r"(?i)mapping:.*?\n", "", sanitized)

        # 3. Detect and Scrub JSON
        try:
            # Try to find JSON block in the string
            json_match = re.search(r"(\{.*\})", sanitized, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                cleaned_data = self._scrub_dict(data, entities, placeholders_list)
                # If the entire response was JSON, return cleaned JSON
                if sanitized.strip() == json_str:
                    return json.dumps(cleaned_data, indent=2)
                # If JSON was part of text, replace it
                sanitized = sanitized.replace(json_str, json.dumps(cleaned_data, indent=2))
        except:
            pass # Not valid JSON or can't parse

        # 4. Final String Sweep for verbatim leaks
        for entity in entities:
            if len(entity) > 2: # Avoid over-scrubbing single characters
                sanitized = re.sub(re.escape(entity), "[SANITISED]", sanitized, flags=re.IGNORECASE)
        
        for placeholder in placeholders_list:
            sanitized = re.sub(re.escape(placeholder), "[REDACTED]", sanitized, flags=re.IGNORECASE)

        return sanitized

    def _scrub_dict(self, data: dict, entities: list, placeholders: list) -> dict:
        """Recursively scrub sensitive data from dictionary/list."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                # Scrub keys if they match entities or placeholders
                new_key = k
                for entity in entities:
                    if entity.lower() in k.lower():
                        new_key = "[KEY_SCRUBBED]"
                        break
                
                new_dict[new_key] = self._scrub_dict(v, entities, placeholders)
            return new_dict
        elif isinstance(data, list):
            return [self._scrub_dict(item, entities, placeholders) for item in data]
        elif isinstance(data, str):
            scrubbed_val = data
            for entity in entities:
                if len(entity) > 2:
                    scrubbed_val = re.sub(re.escape(entity), "[SANITISED]", scrubbed_val, flags=re.IGNORECASE)
            for placeholder in placeholders:
                scrubbed_val = re.sub(re.escape(placeholder), "[REDACTED]", scrubbed_val, flags=re.IGNORECASE)
            return scrubbed_val
        else:
            return data
