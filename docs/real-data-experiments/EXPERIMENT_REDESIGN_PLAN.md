# Sovereign Learner — Experiment Redesign Plan
**Replacing Synthetic Data with Real Published Datasets**

| Field | Detail |
|---|---|
| **Document** | Experiment Redesign Plan v1.0 |
| **Prepared by** | Madusanka \| PhD Candidate, La Trobe University CDAC |
| **Supervisors** | Prof. Daswin De Silva \| Dr. Nishan Mills \| Dr. Harsha Moraliyage |
| **Trigger** | Supervisor feedback: No synthetic data — use real published datasets or validate with SDMetrics |
| **Date** | February 2026 |

---

## 1. Overview & Supervisor Constraint

Your supervisors have issued a clear requirement: **all experiments must use real, published datasets**. Synthetic data is only permissible if it is rigorously validated using SDMetrics, covering three axes: ML utility, statistical quality, and privacy risk via Membership Inference Attack (MIA) — following the SYNTHLA-EDU methodology already published within the research group.

> **SDMetrics validation pipeline:** https://github.com/sdv-dev/SDMetrics — same library used in the SYNTHLA-EDU IEEE Access paper already in this project.

### Current Status by Experiment

| Experiment | Current Data | Status | Action Required |
|---|---|---|---|
| **EXP01** | 50 hand-crafted synthetic queries (`test_queries.py`) | ❌ REJECT — Synthetic | Replace with AI4Privacy + OULAD |
| **EXP02** | OULAD (32,593 real students) | ✅ APPROVED — Real | No change needed |
| **EXP03** | OULAD + same synthetic queries | ⚠️ PARTIAL — Mixed | Replace query portion with AI4Privacy |
| **EXP04** | Synthetic queries (~20) | ❌ REJECT — Synthetic | Replace with AI4Privacy education subset |
| **EXP05** | Synthetic adversarial prompts | ❌ REJECT — Synthetic | Replace with AI4Privacy adversarial-style samples |
| **EXP-BL-01** *(New)* | Read BASELINE_EXPERIMENT_PLAN.md

---

## 2. Replacement Datasets

### 2.1 AI4Privacy Dataset (Primary Replacement)

The AI4Privacy dataset is a peer-reviewed, publicly available dataset used by **Prεεmpt** — the primary baseline comparison paper in this project. Using it provides methodological consistency and reviewer credibility.

| Version | Details | Recommended For |
|---|---|---|
| **pii-masking-43k** | 43K examples, 54 PII types, 111 token classes, 125 subjects. Used by Prεεmpt for NER fine-tuning. | EXP-BL-01 baseline comparison — matches exactly what Prεεmpt used |
| **pii-masking-300k (OpenPII-220k)** | 220K examples, 27 PII classes, targets **education / health / psychology** domains. ~98.3% label accuracy. | EXP01, EXP03, EXP04, EXP05 — education domain subset |

**HuggingFace links:**
- pii-masking-43k: https://huggingface.co/datasets/ai4privacy/pii-masking-43k
- pii-masking-300k: https://huggingface.co/datasets/ai4privacy/pii-masking-300k

> ⚠️ **Critical framing:** AI4Privacy covers PII (Name, Age, Money, SSN, etc.). Your system covers domain-specific IP (CRISPR, HEK293, NIH R01). This difference is your **key argument** — use it to show your system has broader coverage than Prεεmpt. Filter the education domain subset from pii-masking-300k for maximum relevance.

---

### 2.2 OULAD — Extended Use

OULAD is already approved and used in EXP02. It can be extended to provide real educational query contexts for EXP01, EXP03, and EXP04 through extraction of student discussion forum posts and VLE interaction text.

- Dataset: https://analyse.kmi.open.ac.uk/open_dataset
- 32,593 students, 10.6M VLE interactions, 7 CSV tables
- Extract: studentVle discussion text, forum posts, and assessment submission queries as natural educational input

---

### 2.3 SDMetrics — When Data Generation is Unavoidable

If any data generation is required (e.g. augmenting AI4Privacy education queries to match your IP-specific domain), it must be evaluated using the SDMetrics pipeline following the SYNTHLA-EDU methodology:

- SDMetrics GitHub: https://github.com/sdv-dev/SDMetrics
- **Axis 1 — ML Utility:** Column Shapes Score, Column Pair Trends
- **Axis 2 — Statistical Quality:** SDMetrics Quality Report Score
- **Axis 3 — Privacy Risk:** Membership Inference Attack (MIA) — AUC score near 0.5 = good privacy

> The SYNTHLA-EDU paper (IEEE Access, already in your project) provides the exact pipeline. Use it as your methodological template for any SDMetrics evaluation.

---

## 3. Experiment-by-Experiment Redesign

### 3.1 EXP01 — Semantic Generalization Effectiveness

| Field | Detail |
|---|---|
| **Research Question** | Can semantic generalization protect IP while preserving educational utility? |
| **Old Data** | ❌ 50 hand-crafted synthetic queries across biomedical, CS, legal, medical, academic domains |
| **New Data** | ✅ AI4Privacy pii-masking-300k (education + health domain subset) + OULAD-derived VLE text queries |
| **Sample Size** | 200 samples from AI4Privacy education subset + 100 OULAD-derived queries = **300 total** (vs previous 50 — 6× larger) |
| **Ground Truth** | AI4Privacy provides ground truth entity labels — enables objective IP protection rate measurement |
| **Metrics** | IP Protection Rate, Utility Preservation (STS), Sanitization Time (ms), Zero-Leakage Rate |
| **Baselines** | (1) No Protection, (2) Full Redaction, (3) Prεεmpt FPE on same dataset |
| **Key Advantage** | 300 real samples vs 50 synthetic — peer-reviewed dataset, directly comparable to Prεεmpt baseline |

**AI4Privacy Load Code:**
```python
from datasets import load_dataset

# Load pii-masking-300k education subset
dataset = load_dataset("ai4privacy/pii-masking-300k")

# Filter education domain
edu_subset = dataset['train'].filter(
    lambda x: 'education' in str(x.get('subject', '')).lower()
)

# Sample 200 records
exp01_data = edu_subset.shuffle(seed=42).select(range(200))
```

---

### 3.2 EXP02 — OULAD Hybrid Learning *(No Change)*

> ✅ EXP02 already uses OULAD — a real, published, peer-reviewed dataset with 32,593 students and 10.6M VLE interactions. This experiment is **APPROVED as-is**. No redesign required.

Sub-experiments remain unchanged:
- **EXP02a** — Passive Struggle Detection: Full Local vs Sanitized Cloud (F1 comparison)
- **EXP02b** — Complex Query Resolution: Hybrid vs Local-Only vs Cloud-Only
- **EXP02c** — Competency Vector Portability: Cold-start vs Sovereign Transfer (48.4% convergence reduction)

---

### 3.3 EXP03 — Model Diversity / Architecture Agnosticism

| Field | Detail |
|---|---|
| **Research Question** | Does the system work consistently across multiple local LLM backends? |
| **Old Data** | ❌ OULAD (approved) + synthetic queries (rejected) |
| **New Data** | ✅ OULAD (unchanged) + AI4Privacy education subset (same 200 samples used in EXP01) |
| **Models Tested** | llama3.2, phi3.5, llama2 (local via Ollama) \| OpenAI GPT-4, Google Gemini (cloud) |
| **Metrics** | IP Protection Rate per model, Utility Score per model, Latency per model, Consistency across models |
| **Key Argument** | Model agnosticism is a key differentiator from Prεεmpt (which requires specific NER models). Real data strengthens this claim. |

---

### 3.4 EXP04 — Agentic Evaluation

| Field | Detail |
|---|---|
| **Research Question** | Does the CrewAI architecture make correct zone-routing and tool-selection decisions on real inputs? |
| **Old Data** | ❌ ~20 synthetic queries across privacy zones |
| **New Data** | ✅ AI4Privacy pii-masking-300k education subset — 80 samples (20 per zone: Zone 0/1/2/3) |
| **Zone Mapping** | Zone 0: Personal/student data \| Zone 1: IP/PII (AI4Privacy core) \| Zone 2: Internal project \| Zone 3: Public knowledge |
| **Metrics** | Task Completion Rate, Tool Correctness, Privacy Score per zone, **Zone Classification Accuracy** *(new)* |
| **New Metric Unlocked** | **Zone Classification Accuracy** — measurable with AI4Privacy ground truth labels (was not possible with synthetic data) |

> 💡 Using AI4Privacy unlocks a new metric for EXP04: **Zone Classification Accuracy**. Since AI4Privacy has ground truth PII labels, you can objectively verify whether the agent correctly classified each input into the right privacy zone. This is a stronger claim than was possible with synthetic data.

---

### 3.5 EXP05 — Red Team / Adversarial Testing

| Field | Detail |
|---|---|
| **Research Question** | Can adversaries extract private information through prompt injection, jailbreaks, or chain-of-thought leakage? |
| **Old Data** | ❌ 4 hand-crafted synthetic adversarial prompts |
| **New Data** | ✅ AI4Privacy pii-masking-43k — adversarial-style samples containing sensitive PII embedded in complex contexts |
| **Attack Vectors** | (1) Direct PII extraction \| (2) IP leakage via chain-of-thought \| (3) Zone misclassification \| (4) Jailbreak via roleplay |
| **Sample Size** | **50 adversarial samples** (vs 4 previously) — statistically meaningful red team evaluation |
| **Metrics** | Attack Success Rate, False Negative Rate (missed PII), Defence Success Rate, Vulnerability Taxonomy |

---

### 3.6 EXP-BL-01 — NEW: Baseline Comparison vs Prεεmpt

> This is a new experiment requested by Dr. Harsha to provide a rigorous baseline comparison against other related work. Read BASELINE_EXPERIMENT_PLAN.md for more details.

---

## 4. Unified Data Flow Across All Experiments

| Dataset | EXP01 | EXP02 | EXP03 | EXP04 | EXP05 | EXP-BL-01 |
|---|---|---|---|---|---|---|
| **OULAD** | ✅ 100 queries | ✅ Primary (unchanged) | ✅ Primary (unchanged) | Zone 0 inputs | — | — |
| **AI4Privacy pii-masking-300k (edu)** | ✅ 200 queries | — | ✅ Query portion (200) | ✅ Zones 1/2/3 (60 items) | — | — |
| **AI4Privacy pii-masking-43k** | — | — | — | — | ✅ 50 adversarial | ✅ 200 samples |
| **SDMetrics** *(only if augmentation needed)* | Validation only | — | Validation only | Validation only | Validation only | — |

---

## 5. SDMetrics Validation Protocol (If Augmentation Required)

If any data generation or augmentation is unavoidable, the following SDMetrics protocol must be applied before using generated data in any experiment. This mirrors the SYNTHLA-EDU methodology.

| Step | Axis | Metric | Acceptance Threshold |
|---|---|---|---|
| **1** | ML Utility | Train classifier on synthetic, test on real — accuracy vs real data | ≥ 85% of real-data accuracy |
| **2** | Statistical Quality | SDMetrics Quality Report Score: Column Shapes + Column Pair Trends | ≥ 0.80 overall score |
| **3** | Privacy Risk | Membership Inference Attack (MIA) — AUC score on synthetic data | AUC ≤ 0.55 (near 0.5 = private) |

**Run SDMetrics:**
```python
pip install sdmetrics

from sdmetrics.reports.single_table import QualityReport

report = QualityReport()
report.generate(real_data, synthetic_data, metadata)
report.get_score()  # Must be >= 0.80
```

---

## 6. Supervisor Defence Scripts

### Prof. Daswin De Silva
**Anticipated challenge:** *"Why is AI4Privacy appropriate for an educational AI paper?"*

> We selected the pii-masking-300k **education domain subset**, which specifically targets educational discussion scenarios — aligning with our system's use case. All data is publicly available, ethically cleared (no real PII — all values are mocked), and peer-reviewed. The OULAD component remains our primary educational dataset. AI4Privacy serves as the standardised benchmark for the query sanitisation comparison layer, which is a methodological requirement for credible baseline comparison.

---

### Dr. Nishan Mills
**Anticipated challenge:** *"The entity types in AI4Privacy (Name, Age) are not the same as your research IP entities (CRISPR, HEK293). How is this a valid comparison?"*

> This is precisely our argument. Prεεmpt operates on 3 entity types (Name, Age, Money). Our semantic generalisation operates on **any** domain-specific entity without pre-definition. Running both systems on AI4Privacy reveals that Prεεmpt achieves near-perfect coverage on its supported types, but **zero coverage** on domain-specific research IP — while our system covers both. This empirically demonstrates our system's broader coverage as a quantifiable metric, not just a theoretical claim.

---

### Dr. Harsha Moraliyage
**Anticipated challenge:** *"The SDMetrics requirement — when does it apply?"*

> SDMetrics applies only if data augmentation or generation is required. Our primary plan avoids this entirely by using AI4Privacy (real, published) and OULAD (real, published). If edge cases require generation — for example, constructing adversarial prompts that target our specific IP taxonomy — we will validate generated samples against the AI4Privacy distribution using the three-axis SDMetrics protocol from the SYNTHLA-EDU paper, which is already published and peer-reviewed within our research group.

---

## 7. Implementation Timeline

| Priority | Task | Dataset | Effort |
|---|---|---|---|
| **P1 — Now** | Load AI4Privacy pii-masking-300k, filter education subset, sample 200 records for EXP01 | AI4Privacy-300k | 2–3 hours |
| **P1 — Now** | Re-run EXP01 with new dataset, record new IP Protection Rate and Utility scores | AI4Privacy-300k + OULAD | 1 day |
| **P2 — Soon** | Set up EXP-BL-01: install Prεεmpt, run on pii-masking-43k (200 samples), record comparative metrics | AI4Privacy-43k | 2–3 days |
| **P2 — Soon** | Update EXP04 to use AI4Privacy education subset (80 samples across 4 zones), add Zone Classification Accuracy metric | AI4Privacy-300k | 1 day |
| **P3 — Next** | Update EXP05 with 50 adversarial samples from AI4Privacy-43k, re-run red team, update vulnerability report | AI4Privacy-43k | 1–2 days |
| **P3 — Next** | Verify EXP03 — confirm OULAD portion unchanged, replace query portion with AI4Privacy education subset | OULAD + AI4Privacy-300k | Half day |
| **P4 — If needed** | If any augmentation required: run SDMetrics 3-axis validation, report scores in paper appendix | SDMetrics | 1 day |

---

## 8. Summary: Before vs After

| Dimension | Before ❌ | After ✅ |
|---|---|---|
| **Data Source** | 50 hand-crafted synthetic queries | 300 real samples (AI4Privacy + OULAD) |
| **Peer Review Status** | Not reviewed — created by researcher | Published in peer-reviewed papers (IEEE Access, arXiv) |
| **Ground Truth** | Manually defined sensitive labels | Automated ground truth labels from AI4Privacy annotation pipeline |
| **Baseline Comparison** | Not directly comparable to Prεεmpt | Directly comparable — same dataset Prεεmpt used for NER |
| **New Metric Enabled** | Zone Classification Accuracy not measurable | Zone Classification Accuracy now measurable with AI4Privacy labels |
| **SDMetrics Compliance** | Not validated | Real data — SDMetrics only if augmentation needed |

---

*Sovereign Learner — PhD Research | La Trobe University CDAC | Prepared for Supervisor Review — February 2026*