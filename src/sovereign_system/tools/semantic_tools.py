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
        Core Semantic Generalization logic:
        1. Parse sensitive entities
        2. Create abstract placeholders
        3. Build reverse mapping for re-contextualization
        4. Return sanitized query
        """
        entities = [e.strip() for e in sensitive_entities.split(",")]
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
        }
        
        placeholder_counter = {}
        
        for entity in entities:
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
            
            # Replace in query
            sanitized = re.sub(re.escape(entity), placeholder, sanitized, flags=re.IGNORECASE)
        
        return f"SANITIZED: {sanitized}\nMAPPING: {self.placeholder_map}"
    
    def _is_type(self, entity: str, type_hint: str) -> bool:
        """Simple heuristic type detection"""
        type_indicators = {
            "protocol": ["crispr", "pcr", "elisa", "western"],
            "cell": ["hek", "hela", "cho", "293", "cell"],
            "gene": ["brca", "tp53", "egfr", "kras"],
            "compound": ["mg", "ml", "acid", "ase"],
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
        Reverse the Semantic Generalization:
        1. Parse the mapping
        2. Replace placeholders with original terms
        3. Return personalized response
        """
        import ast
        
        # Parse mapping string to dict
        try:
            # Handle string format: "{'Protocol-A': 'CRISPR', 'Cell-A': 'HEK293'}"
            placeholder_map = ast.literal_eval(mapping)
        except:
            # Try to extract from formatted string
            placeholder_map = {}
            pairs = mapping.replace("{", "").replace("}", "").split(",")
            for pair in pairs:
                if ":" in pair:
                    key, val = pair.split(":")
                    placeholder_map[key.strip().strip("'")] = val.strip().strip("'")
        
        # Reverse the mapping and replace
        recontextualized = response
        for placeholder, original in placeholder_map.items():
            recontextualized = re.sub(
                re.escape(placeholder), 
                original, 
                recontextualized, 
                flags=re.IGNORECASE
            )
        
        return f"PERSONALIZED RESPONSE:\n{recontextualized}"