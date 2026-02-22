import unittest
from sovereign_system.security.guard import guard

class TestSovereignGuard(unittest.TestCase):
    
    def test_conservative_routing_low_confidence(self):
        """EXP08B: Fallback kicks in when NER confidence is < 0.85"""
        query = "Can you help optimize Protocol X?"
        ner_confidence = 0.60  # Low confidence
        proposed_zone = 2      # Cloud zone
        
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone, ner_confidence)
        self.assertFalse(is_valid)
        self.assertIn("NER uncertainty", reason)
        self.assertIn("conservative routing applied", reason)
        
    def test_conservative_routing_low_confidence_zone0(self):
        """EXP08B: Zone 0 is allowed even if confidence is low"""
        query = "Can you help optimize Protocol X?"
        ner_confidence = 0.60
        proposed_zone = 0      # Local zone
        
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone, ner_confidence)
        self.assertTrue(is_valid)
        self.assertIn("Zone 0 is validated under NER uncertainty", reason)

    def test_high_confidence_normal_routing(self):
        """Normal routing applies when confidence is high"""
        query = "Can you help me understand basic statistics?"
        ner_confidence = 0.95
        proposed_zone = 3
        
        is_valid, reason = guard.validate_zone_classification(query, proposed_zone, ner_confidence)
        self.assertTrue(is_valid)
        self.assertIn("Zone 3 is within safe limits", reason)

if __name__ == '__main__':
    unittest.main()
