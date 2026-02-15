import re
from typing import List, Tuple, Optional
from .patterns import JAILBREAK_PATTERNS
try:
    from presidio_analyzer import AnalyzerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

class SovereignGuard:
    """
    Central Guardrail System for Signal Validation.
    Implements Input/Output safety checks with defense-in-depth.
    
    Addresses EXP05 vulnerabilities:
    - Jailbreak/roleplay attacks
    - Chain-of-Thought leakage
    - Zone misclassification
    - Local PII storage
    """
    
    def __init__(self):
        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
        else:
            self.analyzer = None
        
        # CoT patterns to strip from outputs (addresses EXP05 CoT leakage)
        self.cot_patterns = [
            r"Firstly,?\s+I\s+need\s+to\s+.*?(?:\.|$)",
            r"Let me think.*?(?:\.|$)",
            r"Step \d+:.*?(?:\.|$)",
            r"My (thought process|reasoning) is.*?(?:\.|$)",
            r"I'm (thinking|reasoning|analyzing).*?(?:\.|$)",
            r"Internal note:.*?(?:\.|$)",
            r"To (solve|answer) this.*?(?:\.|$)",
            r"\[THINKING:.*?\]",
            r"\[INTERNAL:.*?\]",
            r"<thinking>.*?</thinking>",
        ]

    def validate_input(self, query: str) -> Tuple[bool, str, List[str]]:
        """
        Validates input against Jailbreaks and critical PII.
        Returns: (is_safe, message, detected_threats)
        """
        threats = []
        is_safe = True
        
        # 1. Jailbreak Detection (Enhanced regex patterns)
        for pattern in JAILBREAK_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                threats.append(f"Jailbreak pattern detected: '{match.group()}'")
                is_safe = False
        
        # 2. High-risk PII patterns (SSN, Credit Cards)
        from .patterns import SENSITIVE_PATTERNS
        for pattern in SENSITIVE_PATTERNS:
            match = re.search(pattern, query)
            if match:
                # Don't block, but warn (Zone 0/1 can handle PII)
                threats.append(f"High-risk PII pattern detected: {match.group()[:4]}***")
        
        if not is_safe:
            return False, "🚨 Input rejected: Potential jailbreak/manipulation attempt detected.", threats
            
        return True, "✅ Input validation passed.", threats

    def validate_zone_classification(self, query: str, proposed_zone: int) -> Tuple[bool, str]:
        """
        Validates that zone classification is appropriate for the query content.
        Prevents roleplay attacks from forcing Zone 3 classification.
        
        Returns: (is_valid, reason)
        """
        detected_risks = []
        
        # If Presidio is available, use it for PII detection
        if self.analyzer:
            pii_entities = self.scan_for_pii(query)
            if pii_entities:
                detected_risks.append(f"PII ({len(pii_entities)} entities)")
        
        # Check for sensitive keywords that should never be Zone 3
        sensitive_keywords = [
            r"\bpatient\b", r"\bmedical\b", r"\bID\s*\d+", r"\bSSN\b",
            r"\bproprietary\b", r"\bconfidential\b", r"\bsecret\b",
            r"\bCRISPR\b", r"\bprotocol\b", r"\bresearch\b",
            r"\bclient\b", r"\blegal\b", r"\bcontract\b", r"\bHEK\d*\b"
        ]
        
        for keyword_pattern in sensitive_keywords:
            if re.search(keyword_pattern, query, re.IGNORECASE):
                match = re.search(keyword_pattern, query, re.IGNORECASE).group()
                detected_risks.append(f"Sensitive Term '{match}'")
                
        is_sensitive = len(detected_risks) > 0
        max_allowed_zone = 1 if is_sensitive else 3
        
        if proposed_zone > max_allowed_zone:
            return False, f"Risk detected ({', '.join(detected_risks[:3])}). Max allowed zone is {max_allowed_zone}. Your proposal Zone {proposed_zone} is unsafe."
        
        return True, f"Zone {proposed_zone} is within safe limits (Max: {max_allowed_zone})."

    def sanitize_output(self, text: str) -> str:
        """
        Removes Chain-of-Thought artifacts and internal reasoning from outputs.
        Addresses EXP05 CoT leakage vulnerability.
        
        Returns: Sanitized text
        """
        sanitized = text
        
        # Remove CoT patterns
        for pattern in self.cot_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove common internal markers
        sanitized = re.sub(r"\[Agent:.*?\]", "", sanitized)
        sanitized = re.sub(r"\[Step \d+\]", "", sanitized)
        sanitized = re.sub(r"---internal---.*?---end internal---", "", sanitized, flags=re.DOTALL)
        
        # Clean up extra whitespace
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
        sanitized = re.sub(r"\s{2,}", " ", sanitized)
        sanitized = sanitized.strip()
        
        return sanitized

    def scan_for_pii(self, text: str) -> List[str]:
        """
        Uses Presidio (if available) to find PII entities.
        Returns a list of detected entity types/text.
        """
        results = []
        if self.analyzer:
            analysis = self.analyzer.analyze(text=text, language='en')
            for res in analysis:
                results.append(text[res.start:res.end])
        return results
    
    def scrub_pii_for_storage(self, text: str) -> str:
        """
        Scrubs PII before storing in local competency vectors.
        Addresses EXP05 local storage vulnerability.
        
        Returns: PII-scrubbed text
        """
        scrubbed = text
        
        if self.analyzer:
            # Use Presidio to anonymize
            from presidio_anonymizer import AnonymizerEngine
            anonymizer = AnonymizerEngine()
            
            analysis = self.analyzer.analyze(text=text, language='en')
            anonymized = anonymizer.anonymize(text=text, analyzer_results=analysis)
            scrubbed = anonymized.text
        else:
            # Fallback: Use regex patterns
            from .patterns import SENSITIVE_PATTERNS
            for pattern in SENSITIVE_PATTERNS:
                scrubbed = re.sub(pattern, "[REDACTED]", scrubbed)
        
        return scrubbed

# Singleton instance
guard = SovereignGuard()
