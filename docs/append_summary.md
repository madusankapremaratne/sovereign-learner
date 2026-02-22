
---

## 📊 Phase 1-4 Experiments: Architecture Reinforcements & Paper Scaling

### ❓ Why These Experiments?
These experiments address critical reviewer critiques regarding empirical comparisons with baseline architectures, the robustness of the system against scale, and the formalization of privacy guarantees beyond simple test-query metrics. 

---

### **EXP06: ARR at Scale & Degradation Curves**
- **File:** `exp06_arr_at_scale.py`
- **Goal:** Formalize privacy metrics by establishing Adversarial Reconstruction Resistance (ARR) across multiple dialog turns.
- **Methodology:** Simulated an adversarial GPT-4 agent trying to reconstruct entities from sanitized strings over 1, 3, 5, 7, and 10 conversational turns.
- **Significance:** Shows that while `ARR(1) = 0.95` (single turn protection is 95%), context leakage compounds over multi-turn interactions, definitively proving the necessity of the Sovereign agent architecture to maintain strict state control across the session.

### **EXP07 & EXP09: SOTA Baseline Comparisons**
- **File:** `exp07_09_sota_comparison.py`
- **Goal:** Benchmark the Sovereign Learner head-to-head against Preempt (2024), PP-TS (2023), and GAMA (2025).
- **Methodology:** Compared Entity Detection Recall, Utility Preservation, and Latency across the simulated educational queries.
- **Significance:** Preempt and PP-TS max out at ~45% recall because their pipelines natively focus only on standard PII (e.g., credit cards) and miss semantic domain IP (e.g., protocol names, cell lines) completely. Sovereign Learner scored 92.5%, asserting SOTA for unstructured IP recognition.

### **EXP08A: NER Coverage & Precision Audit**
- **File:** `exp08a_ner_audit.py`
- **Goal:** Address the exact detection ceiling of the NER (Named Entity Recognition) pipeline across Domain IP endpoints.
- **Methodology:** Checked NER accuracy against a manually annotated 200-document golden truth set.
- **Significance:** Mapped clear F1 score thresholds per educational domain (e.g., Biomedical, CS, Medical, Legal). 

### **EXP08B: Conservative Routing Fallback**
- **File:** `tests/test_guardrails_exp08b.py`
- **Goal:** Handle the "False Negative" risk in NER operations.
- **Methodology:** Introduced a validation guardrail where if NER confidence drops to `< 0.85`, the `Zone Validation Tool` forcefully down-routes the agent into **Zone 0 (Local-only)**.
- **Significance:** Under uncertainty, the system natively fails safe to maximum privacy, blocking Cloud interaction completely.

### **EXP09 Demo: GAMA Token Limitation Demonstration**
- **File:** `exp09_gama_mvpi_demo.py`
- **Goal:** Directly address the C10 reviewer critique that Sovereign Learner maps too closely to the existing GAMA (2025) multi-agent pipeline.
- **Methodology:** Ran generic IP through GAMA's token identification MVPI. 
- **Significance:** Proved empirically that GAMA achieves virtually `0%` recall on deep semantic educational IP because its entity taxonomies are strictly mapped to human-society knowledge (e.g., names and emails).

### **EXP10: Differential Privacy Benchmarking**
- **File:** `exp10_dp_benchmarking.py`
- **Goal:** Plot the Pareto Frontier comparing classic Differential Privacy (DP) against Semantic Generalization.
- **Significance:** Highlights that token-based text-DP often destroys educational Context/Utility for high privacy, whereas Semantic Generalization achieves the optimal balance (Utility vs Privacy Tradeoff) for LLM intent understanding.

### **EXP11A & EXP11B: Corpus Expansion & Categorized Red Teaming**
- **Files:** `scripts/generate_corpus.py` & `experiments/exp11b_red_team.yaml`
- **Goal:** Increase the statistical power by generating a 2,000 query dataset mapping to OULAD distributions, and running 200+ Promptfoo adversarial stress tests.
- **Significance:** Establishes rigorous 95% Confidence Intervals mapped across 5 specific LLM attack categories (Direct Extraction, Protocol Bypass, Chain of Thought Leakage, Multi-turn Inference, System Prompt Injection).

### **EXP12: Novel Entity Leakage Rate (NELR) Scan**
- **File:** `exp12_nelr_scan.py`
- **Goal:** Track "Response-induced Leakage". 
- **Methodology:** Post-hoc NER scan on cloud responses comparing retrieved entities against the original ground truth maps to detect cloud hallucinations.
- **Significance:** Captures specific cases where the cloud LLM correctly guesses the hidden semantic properties from mere context, enabling empirical definition of the NELR metric.
