from crewai.tools import BaseTool
from typing import Type, Union, Any
from pydantic import BaseModel, Field
import chromadb
import uuid
from datetime import datetime
import os
import time
from sovereign_system.utils.sovereign_trace_logger import global_tracer

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
        start_ts = time.time()
        
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
        
        output = f"SUCCESS: Evidence stored in ChromaDB.\nID: {doc_id}\nWeight: {weight}\nZone: {zone_int}\nPath: {db_path}"
        
        # Log to global trace
        duration = (time.time() - start_ts) * 1000
        
        try:
            global_tracer.log_agent(
                agent_name="Evidence Curator",
                agent_role="Competency Evidence Curator",
                input_data=f"Query: {query}\nResponse: {response[:100]}...",
                output_data=output,
                duration_ms=duration,
                privacy_before=0.0, # Assumed fully restored by now
                privacy_after=0.0,
                zone=zone_int,
                metadata={
                    "storage": "ChromaDB (local)",
                    "evidence_id": doc_id,
                    "weight": weight,
                    "interaction_type": interaction_type
                }
            )
            
            # Since this is the last step, end the trace
            global_tracer.end_trace(response, zone=zone_int, utility_score=0.9)
            
        except Exception as e:
            print(f"Tracing error: {e}")
            
        return output
