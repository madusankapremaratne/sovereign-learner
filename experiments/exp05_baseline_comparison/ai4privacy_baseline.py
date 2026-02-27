import torch
from transformers import pipeline
import re

class AI4PrivacySystem:
    """
    AI4Privacy NER (piiranha-v1)
    Mechanism: 17-category DNN-based PII detection.
    Model: iiiorg/piiranha-v1-detect-personal-information
    """
    def __init__(self, model_id="iiiorg/piiranha-v1-detect-personal-information"):
        self.model_id = model_id
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = 0
        else:
            self.device = -1
        # Lazy load to avoid hanging during experiment init
        self._classifier = None

    @property
    def classifier(self):
        if self._classifier is None:
            print(f"  Loading AI4Privacy model: {self.model_id}...")
            self._classifier = pipeline(
                "token-classification", 
                model=self.model_id, 
                aggregation_strategy="simple",
                device=self.device
            )
        return self._classifier

    def sanitize(self, text: str) -> str:
        """
        Redacts PII detected by piiranha-v1.
        """
        try:
            results = self.classifier(text)
            # Sort results in reverse order of start position to redact without breaking offsets
            results = sorted(results, key=lambda x: x['start'], reverse=True)
            
            sanitized = text
            for res in results:
                start = res['start']
                end = res['end']
                label = res['entity_group'].upper().replace(" ", "_")
                sanitized = sanitized[:start] + f"<{label}>" + sanitized[end:]
            
            return sanitized
        except Exception as e:
            print(f"AI4Privacy Error: {e}")
            return text

if __name__ == "__main__":
    ai4p = AI4PrivacySystem()
    test = "My SSN is 123-445 and I'm studying AAA."
    print(f"Original: {test}")
    print(f"Sanitized: {ai4p.sanitize(test)}")
