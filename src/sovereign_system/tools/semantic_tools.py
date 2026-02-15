from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import re

class SemanticGeneralizationInput(BaseModel):
    query: str = Field(..., description="The original sensitive query")
    sensitive_entities: str = Field(..., description="Comma-separated list of sensitive entities")

class SemanticGeneralizationTool(BaseTool):
    name: str = "semantic_generalizer"
    description: str = "Transforms sensitive queries into abstract formulations while preserving logical structure"
    args_schema: Type[BaseModel] = SemanticGeneralizationInput
    
    # Mapping storage (in production, this persists)
    placeholder_map: dict = {}
    
    def _run(self, query: str, sensitive_entities: str) -> str:
        """
        Core Semantic Generalization logic
        """
        # Robust cleanup for list-like strings (e.g. "['A', 'B']")
        cleaned_input = sensitive_entities.replace('[', '').replace(']', '').replace("'", "").replace('"', "")
        entities = [e.strip() for e in cleaned_input.split(",")]
        sanitized = query
        
        # Entity type detection and placeholder generation
        placeholder_patterns = {
            "protocol": "Protocol-X",
            "method": "Method-Y", 
            "cell": "Cell-Type-A",
            "gene": "Gene-B",
            "compound": "Compound-Z",
            "disease": "Condition-C",
            "institution": "Institution-D",
            "project": "Project-E",
            "company": "Company-F",
            "location": "Location-G",
            "dataset": "Dataset-H",
            "hardware": "Hardware-I",
        }
        
        placeholder_counter = {}
        
        for entity in entities:
            # Skip empty entities (detection failures)
            if not entity or entity.strip() == '':
                continue
                
            entity_lower = entity.lower()
            
            # Determine placeholder type
            placeholder_type = "Entity"
            for pattern, placeholder in placeholder_patterns.items():
                if pattern in entity_lower or self._is_type(entity, pattern):
                    placeholder_type = placeholder.split("-")[0]
                    break
            
            # Generate unique placeholder
            if placeholder_type not in placeholder_counter:
                placeholder_counter[placeholder_type] = 0
            placeholder_counter[placeholder_type] += 1
            
            placeholder = f"{placeholder_type}-{chr(64 + placeholder_counter[placeholder_type])}"
            
            # Store mapping for re-contextualization
            self.placeholder_map[placeholder] = entity
            
            # Replace in query (only if entity is non-empty)
            sanitized = re.sub(re.escape(entity), placeholder, sanitized, flags=re.IGNORECASE)
        
        output = f"SANITIZED: {sanitized}\nMAPPING: {self.placeholder_map}"
        
        return output
    
    def _is_type(self, entity: str, type_hint: str) -> bool:
        """Simple heuristic type detection"""
        type_indicators = {
            "protocol": ["crispr", "pcr", "elisa", "western", "alpha", "protocol"],
            "cell": ["hek", "hela", "cho", "293", "cell", "neuron", "cardiomyocyte"],
            "gene": ["brca", "tp53", "egfr", "kras", "p53"],
            "compound": ["mg", "ml", "acid", "ase", "drug", "compound"],
            "company": ["inc", "corp", "ltd", "google", "microsoft", "sequoia", "acme"],
            "project": ["project", "experiment", "study"],
            "hardware": ["gpu", "tpu", "cluster", "sensor", "a100"],
        }
        entity_lower = entity.lower()
        if type_hint in type_indicators:
            return any(ind in entity_lower for ind in type_indicators[type_hint])
        return False

class RecontextualizationInput(BaseModel):
    response: str = Field(..., description="The cloud response containing placeholders")
    mapping: str = Field(..., description="The placeholder mapping from generalization step")

class RecontextualizationTool(BaseTool):
    name: str = "recontextualizer"
    description: str = "Maps generalized cloud responses back to the learner's specific context"
    args_schema: Type[BaseModel] = RecontextualizationInput
    
    def _run(self, response: str, mapping: str) -> str:
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
            

            