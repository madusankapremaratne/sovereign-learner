"""
Prεεmpt Baseline Implementation (2024/2025)
=========================================
Faithful implementation using the official 'preempt' library logic.

Paper: "Prϵϵmpt: Sanitizing Sensitive Prompts for LLMs"
Mechanism: 
  - Format-Preserving Encryption (FPE) for structured tokens (Names, IDs).
  - Metric Differential Privacy (mDP) for value-dependent tokens (Age, Money).

This implementation uses the 'preempt' library's Sanitizer but substitutes
the heavy NER model requirement with an Ollama-based NER extractor to 
ensure stability in the experimental environment while maintaining 
the cryptographic transformation logic.
"""

import os
import json
import re
import requests
from typing import List, Dict, Any, Optional
from preempt.sanitizer import Sanitizer

class PreemptNERMock:
    """
    Simulates the NER component of Prεεmpt using Ollama.
    The paper mentions using Llama-3-8B or UniNER; we use Ollama llama3.2
    to extract entities in the format the 'preempt' library expects.
    """
    def __init__(self, model="llama3.2", ollama_url="http://localhost:11434/api/generate"):
        self.model = model
        self.ollama_url = ollama_url

    def extract(self, prompts: List[str], entity_type: str) -> Dict[str, List[List[str]]]:
        """
        Extracts entities from a list of prompts.
        Returns a dict: {entity_type: [[val1, val2], [val3], ...]}
        """
        results = []
        for text in prompts:
            prompt = f"""Extract all {entity_type} entities from the text below.
Respond ONLY with a JSON list of strings.
Example: ["John Doe", "Jane Smith"]
If none, respond with [].

Text: {text}"""
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0}
                }
                response = requests.post(self.ollama_url, json=payload, timeout=30)
                raw_resp = response.json().get("response", "[]")
                # Extract list using regex
                match = re.search(r'\[.*\]', raw_resp, re.DOTALL)
                if match:
                    entities = json.loads(match.group())
                else:
                    entities = []
                
                if not isinstance(entities, list):
                    entities = []
                
                # Clean entities (remove currency symbols for Money, etc.)
                if entity_type == 'Money':
                    entities = [e.replace('$', '').replace(',', '').strip() for e in entities if e]
                elif entity_type == 'Age':
                    # Extract just digits
                    entities = ["".join(filter(str.isdigit, e)) for e in entities if e]
                
                entities = [str(e) for e in entities if e]
                results.append(entities)
            except Exception as e:
                print(f"Preempt NER Error: {e}")
                results.append([])
        
        return {entity_type: results}

class PreemptSystem:
    """
    Prεεmpt Baseline using the 'preempt' library's Sanitizer.
    """
    def __init__(self, model="llama3.2", ollama_url="http://localhost:11434/api/generate"):
        # Initialize the Mock NER
        self.ner = PreemptNERMock(model=model, ollama_url=ollama_url)
        
        # Initialize the official Sanitizer with paper-standard keys/tweaks
        # In a real deployment, these would be user-specific.
        self.sanitizer = Sanitizer(
            self.ner, 
            key="EF4359D8D580AA4F7F036D6F04FC6A94", 
            tweak="D8E7920AFA330A73"
        )

    def sanitize(self, text: str) -> str:
        """
        Applies Prεεmpt sanitization (FPE + mDP).
        We process Name (FPE), Money (mDP), and Age (mDP).
        """
        # Ensure we are working with a list for the library
        inputs = [text]
        
        try:
            # 1. Sanitize Names (FPE)
            # The library uses FF3-1 cipher for format preservation.
            sanitized, _ = self.sanitizer.encrypt(
                inputs, 
                entity='Name', 
                use_fpe=True, 
                use_mdp=False
            )
            
            # 2. Sanitize Money (mDP)
            # Epsilon=1.0 is standard for balanced privacy/utility in these papers.
            sanitized, _ = self.sanitizer.encrypt(
                sanitized, 
                entity='Money', 
                epsilon=1.0, 
                use_fpe=False, 
                use_mdp=True
            )
            
            # 3. Sanitize Age (mDP)
            sanitized, _ = self.sanitizer.encrypt(
                sanitized, 
                entity='Age', 
                epsilon=1.0, 
                use_fpe=False, 
                use_mdp=True
            )
            
            return sanitized[0]
            
        except Exception as e:
            print(f"Preempt Sanitization Error: {e}")
            return text

if __name__ == "__main__":
    # Test the implementation
    preempt = PreemptSystem()
    test_text = "My name is John Doe, I am 25 years old and I have $1200 in my account."
    result = preempt.sanitize(test_text)
    print(f"Original: {test_text}")
    print(f"Sanitized: {result}")
    
    # Debug extraction
    print("\nDebug Extraction:")
    for ent in ['Name', 'Money', 'Age']:
        ext = preempt.ner.extract([test_text], ent)
        print(f"  {ent}: {ext[ent]}")
