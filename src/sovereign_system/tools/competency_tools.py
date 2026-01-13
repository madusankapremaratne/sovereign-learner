from crewai.tools import BaseTool
from typing import Type, Union, Any
from pydantic import BaseModel, Field
import chromadb
import uuid
from datetime import datetime
import os

class CompetencyEvidenceInput(BaseModel):
    query: str = Field(..., description="The original query or interaction subject")
    response: str = Field(..., description="The final response provided to the learner")
    zone: Union[int, str] = Field(..., description="Privacy zone used (0-3)")
    interaction_type: str = Field("active", description="Type of interaction: 'active' (explicit questions) or 'passive' (browsing)")

class CompetencyEvidenceTool(BaseTool):
    name: str = "evidence_curator"
    description: str = "Stores learning interactions in a local vector database (ChromaDB) to build the learner's competency profile."
    args_schema: Type[BaseModel] = CompetencyEvidenceInput

    def _run(self, query: str, response: str, zone: Union[int, str], interaction_type: str = "active") -> str:
        """
        Store the interaction in ChromaDB with appropriate weighting.
        """
        # Type conversion for zone
        try:
            zone_int = int(zone)
        except:
            zone_int = 3 # Default to safest/lowest sensitivity if parsing fails
            
        # Determine weight based on interaction type
        weight = 1.0 if interaction_type.lower() == "active" else 0.2
        
        # Ensure directory exists
        db_path = "./knowledge/chroma_db"
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize persistent client
        client = chromadb.PersistentClient(path=db_path)
        
        # Get or create collection
        collection = client.get_or_create_collection(name="competency_vectors")
        
        # Create unique ID and timestamp
        doc_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create document content
        document_text = f"Query: {query}\nResponse: {response}"
        
        # Add to DB
        collection.add(
            documents=[document_text],
            metadatas=[{
                "zone": zone_int,
                "type": interaction_type,
                "weight": weight,
                "timestamp": timestamp
            }],
            ids=[doc_id]
        )
        
        return f"SUCCESS: Evidence stored in ChromaDB.\nID: {doc_id}\nWeight: {weight}\nZone: {zone_int}\nPath: {db_path}"
