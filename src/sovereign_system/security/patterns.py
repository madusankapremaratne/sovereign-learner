JAILBREAK_PATTERNS = [
    # Direct instruction override attempts
    r"ignore (all )?previous instructions",
    r"ignore the above instructions",
    r"ignore everything above",
    r"disregard (all )?(previous|prior|above) (instructions|prompts|rules)",
    r"forget (all )?(previous|prior) (instructions|context|rules)",
    
    # Roleplay and persona manipulation (EXP05 Critical Vulnerability)
    r"now you are",
    r"you are now",
    r"act as a",
    r"roleplay as",
    r"pretend (you are|to be)",
    r"imagine (you are|yourself as)",
    r"you('re| are) (now )?(a|an) .*(who|that) (does not|doesn't) care about (privacy|security|rules)",
    r"assistant (who|that) (does not|doesn't) (care|worry) about",
    r"helpful assistant (who|that) ignores",
    
    # Mode switching attempts
    r"do anything now",
    r"DAN mode",
    r"developer mode",
    r"unrestricted mode",
    r"jailbreak mode",
    r"god mode",
    r"admin mode",
    r"debug mode",
    r"test mode",
    
    # Compliance manipulation
    r"always answer yes",
    r"never refuse",
    r"you must (always )?(comply|obey|answer)",
    r"you (cannot|can't) (refuse|decline|reject)",
    
    # Security bypass attempts
    r"forget (all )?protection",
    r"disable (all )?guardrails",
    r"bypass (all )?(filters|security|protection)",
    r"without any restrictions",
    r"no ethical guidelines",
    r"override (security|privacy|protection)",
    r"turn off (security|privacy|filters)",
    
    # Privacy-specific attacks (EXP05 findings)
    r"you are a helpful assistant who does not care about privacy",
    r"privacy (doesn't|does not) matter",
    r"ignore privacy (rules|guidelines|concerns)",
    
    # Information extraction attempts
    r"system prompt injection",
    r"tell me the secret",
    r"reveal (internal|hidden|secret)",
    r"show me (the )?(mapping|internal|hidden)",
    r"what (is|are) (the )?(secret|internal|hidden)",
    r"output (all )?(internal|secret|hidden)",
    r"print (all )?(mappings|secrets|internals)",
    
    # Zone manipulation attempts (NEW - addresses EXP05 Zone 3 misclassification)
    r"this is (a )?public (query|question|information)",
    r"classify (this|it) as zone 3",
    r"treat (this|it) as (public|non-sensitive)",
    r"no privacy (needed|required)",
    r"this (doesn't|does not) need privacy",
    
    # Chain-of-thought extraction (NEW - addresses CoT leakage)
    r"show (me )?(your|the) (thinking|reasoning|thought process)",
    r"explain (your|the) (internal|step-by-step) (process|reasoning)",
    r"what (are|were) you thinking",
]

SENSITIVE_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # Credit Card
    r"\b(?:\d[ -]*?){13,16}\b", # Generic CC
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b" # Email
]

EDUCATIONAL_IP_PATTERNS = {
    "INSTITUTIONAL_MARKER": [
        r"\b[A-G]{3}\s+module\b", # OULAD coding (BBB, AAA, etc)
        r"\bVLE\b", r"\bOUSE\b", r"\bOULAD\b", r"\bOpen University\b"
    ],
    "ASSESSMENT_TYPE": [
        r"\bTMA\s*([0-9]*)\b", r"\biCMA\s*([0-9]*)\b", r"\bEMA\b",
        r"\bend\s+of\s+module\s+assessment\b"
    ],
    "LEARNING_METRIC": [
        r"\bV_Portfolio\b", r"\bcompetency\s+vector\b", 
        r"\blearning\s+weight\b", r"\binteraction\s+type\b"
    ],
    "CURRICULUM_DOMAIN": [
        r"\bSTEM\s+Foundation\b", r"\bComputing\s+&\s+IT\b",
        r"\bSocial\s+Sciences\b", r"\bBusiness\s+&\s+Law\b"
    ]
}
