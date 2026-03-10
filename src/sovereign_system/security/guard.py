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
        Validates input against Jailbreaks, toxicity, and critical PII.
        Returns: (is_safe, message, detected_threats)
        """
        threats = []
        is_safe = True
        
        # 1. Jailbreak Detection
        for pattern in JAILBREAK_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                threats.append(f"Jailbreak pattern detected: '{match.group()}'")
                is_safe = False
        
        # 2. Toxicity / Harmful Intent (New for EXP06)
        from .patterns import TOXICITY_PATTERNS
        for pattern in TOXICITY_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                threats.append(f"Safety violation: '{match.group()}' detected.")
                is_safe = False

        # 3. High-risk PII patterns
        from .patterns import SENSITIVE_PATTERNS
        for pattern in SENSITIVE_PATTERNS:
            match = re.search(pattern, query)
            if match:
                threats.append(f"High-risk PII pattern detected: {match.group()[:4]}***")
        
        if not is_safe:
            return False, "🚨 Input rejected: Potential policy violation or manipulation detected.", threats
            
        return True, "✅ Input validation passed.", threats

    def is_unsafe(self, query: str) -> Tuple[bool, str]:
        """Simple deterministic safety check for agents to use."""
        safe, msg, threats = self.validate_input(query)
        if not safe:
            return True, "; ".join(threats)
        return False, "Clean"

    def validate_zone_classification(self, query: str, proposed_zone: int, ner_confidence: float = 1.0) -> Tuple[bool, str]:
        """
        Validates that zone classification is appropriate for the query content.
        Prevents roleplay attacks from forcing Zone 3 classification.
        Also evaluates NER confidence for Conservative Routing Fallback (EXP08B).
        
        Returns: (is_valid, reason)
        """
        detected_risks = []
        
        # Conservative Routing Fallback: If NER confidence is too low, enforce Zone 0
        if ner_confidence < 0.85:
            if proposed_zone != 0:
                return False, f"NER uncertainty (confidence {ner_confidence:.2f} < 0.85) — conservative routing applied. Max allowed zone is 0."
            return True, "Zone 0 is validated under NER uncertainty."
            
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

    def sanitize_output(self, text: str, sensitive_entities: List[str] = None, placeholders: List[str] = None) -> str:
        """
        Removes Chain-of-Thought artifacts and internal reasoning from outputs.
        Addresses EXP05 CoT leakage vulnerability.
        Recursively scrubs JSON metadata for leaked PII or placeholders.
        
        Returns: Sanitized text
        """
        sanitized = text
        entities = sensitive_entities or []
        placeholders_list = placeholders or []
        
        # 1. Remove CoT patterns
        for pattern in self.cot_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # 2. Remove common internal markers and "Mental Model" artifacts
        internal_markers = [
            r"\[Agent:.*?\]", r"\[Step \d+\]", r"\[THOUGHT:.*?\]",
            r"---internal---.*?---end internal---",
            r"(?i)thought:.*?\n", r"(?i)metadata:.*?\n", r"(?i)mapping:.*?\n",
            r"(?i)prompt:.*?\n", r"(?i)reasoning:.*?\n"
        ]
        for marker in internal_markers:
            sanitized = re.sub(marker, "", sanitized, flags=re.DOTALL)
        
        # 3. Detect and Scrub JSON structures
        try:
            # Look for JSON blocks
            json_match = re.search(r"(\{.*\})", sanitized, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                import json
                data = json.loads(json_str)
                cleaned_data = self._recursive_scrub(data, entities, placeholders_list)
                
                # Replace original JSON with cleaned JSON
                cleaned_json_str = json.dumps(cleaned_data, indent=2)
                sanitized = sanitized.replace(json_str, cleaned_json_str)
        except:
            pass # Fail gracefully if not valid JSON

        # 4. Final String Sweep for verbatim leaks (Zero-Leak Policy)
        # Avoid scrubbing if entity too short
        for entity in entities:
            if len(entity) > 3:
                sanitized = re.sub(re.escape(entity), "[SANITISED]", sanitized, flags=re.IGNORECASE)
        
        for placeholder in placeholders_list:
            if len(placeholder) > 2:
                sanitized = re.sub(re.escape(placeholder), "[REDACTED]", sanitized, flags=re.IGNORECASE)
        
        # 5. Clean up extra whitespace
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
        sanitized = re.sub(r"\s{2,}", " ", sanitized)
        sanitized = sanitized.strip()
        
        return sanitized

    def _recursive_scrub(self, data, entities: List[str], placeholders: List[str]):
        """Helper to recursively scrub dictionaries and lists."""
        import json
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                # Scrub keys
                new_key = k
                k_lower = k.lower()
                if any(e.lower() in k_lower for e in entities) or any(p.lower() in k_lower for p in placeholders):
                    new_key = f"scrubbed_key_{len(new_dict)}"
                new_dict[new_key] = self._recursive_scrub(v, entities, placeholders)
            return new_dict
        elif isinstance(data, list):
            return [self._recursive_scrub(item, entities, placeholders) for item in data]
        elif isinstance(data, str):
            val = data
            for e in entities:
                if len(e) > 3:
                    val = re.sub(re.escape(e), "[SANITISED]", val, flags=re.IGNORECASE)
            for p in placeholders:
                if len(p) > 2:
                    val = re.sub(re.escape(p), "[REDACTED]", val, flags=re.IGNORECASE)
            return val
        return data

    def scan_for_pii(self, text: str) -> List[str]:
        """
        Uses Presidio (if available) to find PII entities.
        Returns a list of detected entity strings.
        """
        results = []
        if self.analyzer:
            analysis = self.analyzer.analyze(text=text, language='en')
            for res in analysis:
                results.append(text[res.start:res.end])
        return results

    def scan_for_pii_entities(self, text: str) -> List[Tuple[str, str]]:
        """
        Presidio-aware PII detection with type metadata.
        Returns: List[(entity_text, entity_type)]
        """
        results = []
        if self.analyzer:
            analysis = self.analyzer.analyze(text=text, language='en')
            for res in analysis:
                results.append((text[res.start:res.end], res.entity_type))
        
        # Add Educational IP scan results
        ip_hits = self.scan_for_educational_ip(text)
        results.extend(ip_hits)
        
        return results
    
    def scan_for_educational_ip(self, text: str) -> List[Tuple[str, str]]:
        """
        Ensemble Sensitivity pass for Institutional IP.
        """
        from .patterns import EDUCATIONAL_IP_PATTERNS
        hits = []
        for category, patterns in EDUCATIONAL_IP_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    hits.append((match.group(), category))
        return hits
    
    def audit_generalized_query(self, text: str) -> Tuple[bool, str, float]:
        """
        Dataset-Blind Adversarial Audit (Phase 4).
        Evaluates structural entropy and information density to prevent 
        Contextual Fingerprinting without institutional bias.
        
        Returns: (is_safe, reason, risk_score)
        """
        risk_score = 0.0
        reasons = []

        # 1. Numerical Fingerprint Test (High-precision numbers are risky)
        high_precision = re.findall(r'\b\d{2,}\.?\d*\b', text)
        if high_precision:
            risk_score += len(high_precision) * 0.2
            reasons.append(f"Found {len(high_precision)} high-precision numbers.")

        # 2. Case-Cluster Test (Undetected Proper Nouns / Acronyms)
        proper_nouns = re.findall(r'\b[A-Z]{2,}\b|\b[A-Z][a-z]{3,}\s+[A-Z][a-z]{3,}\b', text)
        if proper_nouns:
            risk_score += len(proper_nouns) * 0.15
            reasons.append(f"Found {len(proper_nouns)} potentially sensitive proper nouns/acronyms.")

        # 3. Structural Entropy (Keyword density)
        words = text.split()
        if len(words) > 0:
            tech_density = len(proper_nouns) / len(words)
            if tech_density > 0.4:
                risk_score += 0.3
                reasons.append(f"High technical entropy ({tech_density:.1%}) suggests fingerprinting.")

        is_safe = risk_score < 0.7
        status_msg = "PASSED: Query is structurally generalized." if is_safe else f"REJECTED: {'; '.join(reasons)}"
        
        return is_safe, status_msg, min(1.0, risk_score)

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
