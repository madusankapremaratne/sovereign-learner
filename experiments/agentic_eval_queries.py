
"""
Agentic Evaluation Queries
=========================
Categorized test queries for evaluating the Sovereign Learner pipeline.
Maps to the 4 privacy zones + edge cases.
"""

TEST_QUERIES = [
    # ---------------------------------------------------------
    # ZONE 0 - OFFLINE / TRIVIAL
    # Expected: Handled locally by Sovereign Manager, no cloud
    # ---------------------------------------------------------
    {
        "id": "z0_01",
        "category": "Zone 0 (Offline)",
        "query": "What's my current GPA?",
        "expected_zone": 0,
        "sensitive_entities": []
    },
    {
        "id": "z0_02",
        "category": "Zone 0 (Offline)",
        "query": "List my submitted assignments for this semester.",
        "expected_zone": 0,
        "sensitive_entities": []
    },
    {
        "id": "z0_03",
        "category": "Zone 0 (Offline)",
        "query": "When is the deadline for CS101?",
        "expected_zone": 0,
        "sensitive_entities": []
    },
    {
        "id": "z0_04",
        "category": "Zone 0 (Offline)",
        "query": "Show me my learning progress dashboard.",
        "expected_zone": 0,
        "sensitive_entities": []
    },
    
    # ---------------------------------------------------------
    # ZONE 1 - SOVEREIGN / HIGH SENSITIVITY
    # Expected: Full sanitization pipeline (Manager -> Detector -> Generalizer -> Cloud -> Recontextualizer)
    # ---------------------------------------------------------
    {
        "id": "z1_01",
        "category": "Zone 1 (Sovereign)",
        "query": "How do I optimize my CRISPR protocol for HEK293 cells?",
        "expected_zone": 1,
        "sensitive_entities": ["CRISPR", "HEK293"]
    },
    {
        "id": "z1_02",
        "category": "Zone 1 (Sovereign)",
        "query": "My novel sorting algorithm 'QuickSort-X' is failing on large datasets.",
        "expected_zone": 1,
        "sensitive_entities": ["QuickSort-X"]
    },
    {
        "id": "z1_03",
        "category": "Zone 1 (Sovereign)",
        "query": "Patient 4453 showing severe reaction to drug formulation Alpha-9.",
        "expected_zone": 1,
        "sensitive_entities": ["Patient 4453", "Alpha-9"]
    },
    {
        "id": "z1_04",
        "category": "Zone 1 (Sovereign)",
        "query": "What are the optimal hyperparameters for our proprietary model 'DeepSovereign'?",
        "expected_zone": 1,
        "sensitive_entities": ["DeepSovereign"]
    },
    {
        "id": "z1_05",
        "category": "Zone 1 (Sovereign)",
        "query": "Troubleshoot connection failure in unseen prototype device 'NeuralLink-V1'.",
        "expected_zone": 1,
        "sensitive_entities": ["NeuralLink-V1"]
    },

    # ---------------------------------------------------------
    # ZONE 2 - OPTIMISTIC / PARTIAL SENSITIVITY
    # Expected: Partial/Contextual sanitization
    # ---------------------------------------------------------
    {
        "id": "z2_01",
        "category": "Zone 2 (Optimistic)",
        "query": "Explain gradient descent for my ML assignment.",
        "expected_zone": 2,
        "sensitive_entities": [] 
    },
    {
        "id": "z2_02",
        "category": "Zone 2 (Optimistic)",
        "query": "How do transformers implement attention mechanisms?",
        "expected_zone": 2,
        "sensitive_entities": []
    },
    {
        "id": "z2_03",
        "category": "Zone 2 (Optimistic)",
        "query": "Best practices for writing secure Python code.",
        "expected_zone": 2,
        "sensitive_entities": []
    },
    {
        "id": "z2_04",
        "category": "Zone 2 (Optimistic)",
        "query": "Compare React and Vue for frontend development.",
        "expected_zone": 2,
        "sensitive_entities": []
    },
    {
        "id": "z2_05",
        "category": "Zone 2 (Optimistic)",
        "query": "What are the common side effects of chemotherapy?",
        "expected_zone": 2,
        "sensitive_entities": []
    },

    # ---------------------------------------------------------
    # ZONE 3 - DIRECT / GENERAL KNOWLEDGE
    # Expected: Direct cloud access, minimal overhead
    # ---------------------------------------------------------
    {
        "id": "z3_01",
        "category": "Zone 3 (Direct)",
        "query": "What is photosynthesis?",
        "expected_zone": 3,
        "sensitive_entities": []
    },
    {
        "id": "z3_02",
        "category": "Zone 3 (Direct)",
        "query": "Who wrote 'The Great Gatsby'?",
        "expected_zone": 3,
        "sensitive_entities": []
    },
    {
        "id": "z3_03",
        "category": "Zone 3 (Direct)",
        "query": "Capital of France?",
        "expected_zone": 3,
        "sensitive_entities": []
    },
    {
        "id": "z3_04",
        "category": "Zone 3 (Direct)",
        "query": "Convert 100 degrees Fahrenheit to Celsius.",
        "expected_zone": 3,
        "sensitive_entities": []
    },
    {
        "id": "z3_05",
        "category": "Zone 3 (Direct)",
        "query": "Define 'algorithm'.",
        "expected_zone": 3,
        "sensitive_entities": []
    },

    # ---------------------------------------------------------
    # EDGE CASES - PII + IP MIX
    # Expected: Strict Zone 1 behavior
    # ---------------------------------------------------------
    {
        "id": "edge_01",
        "category": "Edge Case",
        "query": "My supervisor Dr. Smith's CRISPR method is showing off-target effects.",
        "expected_zone": 1,
        "sensitive_entities": ["Dr. Smith", "CRISPR"]
    },
    {
        "id": "edge_02",
        "category": "Edge Case",
        "query": "Regarding project 'BlueSky', send the report to ceo@company.com.",
        "expected_zone": 1,
        "sensitive_entities": ["BlueSky", "ceo@company.com"]
    },
    {
        "id": "edge_03",
        "category": "Edge Case",
        "query": "How does the 'Apollo' architecture handle user ID 998877?",
        "expected_zone": 1,
        "sensitive_entities": ["Apollo", "998877"]
    },
]
