
import pytest
from sovereign_system.security.guard import SovereignGuard, guard

class TestZoneValidation:
    """
    Test suite for Zone Validation logic in SovereignGuard.
    Ensures that sensitive queries are correctly restricted to secure zones (0-1)
    and public queries are allowed in open zones (2-3).
    """

    def test_high_sensitivity_crispr(self):
        """Test that CRISPR-related queries are restricted to Zone 1 max."""
        query = "How do I optimize my CRISPR protocol for HEK293 cells?"
        
        # Case 1: Proposing Zone 1 (Valid)
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone=1)
        assert is_valid is True, f"Zone 1 should be valid for sensitive query. Reason: {reason}"
        assert "Zone 1 is within safe limits" in reason

        # Case 2: Proposing Zone 3 (Invalid - too open)
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone=3)
        assert is_valid is False, "Zone 3 should be invalid for sensitive query"
        assert "Risk detected" in reason
        assert "Max allowed zone is 1" in reason
        assert "Sensitive Term 'CRISPR'" in reason or "Sensitive Term 'HEK293'" in reason

    def test_high_sensitivity_pii_keywords(self):
        """Test that PII-related keywords (SSN, Patient) force Zone 1."""
        sensitive_queries = [
            "What is the patient diagnosis for ID 12345?",
            "Can you process this medical record?",
            "My social security number (SSN) is invalid."
        ]
        
        for q in sensitive_queries:
            # Should fail for Zone 3
            is_valid, reason = guard.validate_zone_classification(q, proposed_zone=3)
            assert is_valid is False, f"Query '{q}' should be restricted from Zone 3"
            assert "Max allowed zone is 1" in reason

            # Should pass for Zone 1
            is_valid, reason = guard.validate_zone_classification(q, proposed_zone=1)
            assert is_valid is True

    def test_low_sensitivity_general_knowledge(self):
        """Test that general knowledge queries are allowed in Zone 3."""
        safe_queries = [
            "What is the capital of France?",
            "Explain loop quantum gravity.",
            "Write a python script to sort a list."
        ]

        for q in safe_queries:
            # Should pass for Zone 3
            is_valid, reason = guard.validate_zone_classification(q, proposed_zone=3)
            assert is_valid is True, f"Query '{q}' should be allowed in Zone 3. Reason: {reason}"
            assert "Zone 3 is within safe limits (Max: 3)" in reason

    def test_proprietary_terms(self):
        """Test detection of business-sensitive terms."""
        query = "Review this proprietary contract for client X."
        
        # Zone 2 (Optimistic Local) might be rejected if strict, but logic says max=1 if sensitive.
        # Let's check Zone 2.
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone=2)
        assert is_valid is False, "Proprietary/Contract/Client terms should restrict to Zone 1"
        assert "Max allowed zone is 1" in reason

    def test_zone_0_always_valid(self):
        """Zone 0 (Offline/Air-gapped) should be valid for anything."""
        # Even the most sensitive query
        query = "Here is the nuclear launch code: 000000."
        
        # Zone 0 is <= Max Allowed (1), so it passes.
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone=0)
        assert is_valid is True
