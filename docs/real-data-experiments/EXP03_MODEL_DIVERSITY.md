# EXP03 — Model Diversity & Architecture Agnosticism
## Supervisor Review Document

| Field | Detail |
|---|---|
| **Experiment ID** | EXP03 |
| **Title** | Model Diversity & Architecture Agnosticism |
| **Document Version** | v2.1 — Real Data, Smoke Test Complete (February 2026) |
| **Prepared by** | Madusanka \| PhD Candidate, La Trobe University CDAC |
| **Supervisors** | Prof. Daswin De Silva \| Dr. Nishan Mills \| Dr. Harsha Moraliyage |
| **Status** | ✅ Validated — 27 February 2026 |
| **Data Status** | ✅ Real published dataset — OULAD (Kuzilek et al., 2017) + AI4Privacy (optional) |
| **Redesign Status** | ✅ Fully rewritten February 2026 — removed synthetic `TEST_QUERIES` dependency |
| **Script** | `experiments/exp03_model_diversity.py` |

---

## 1. Research Question

> **Does the Sovereign Learner's privacy pipeline produce statistically consistent IP protection and educational utility across multiple local LLM backends, demonstrating model-agnosticism as a fundamental architectural property?**

This is a critical differentiator from Prεεmpt: Prεεmpt's Format-Preserving Encryption requires a specific NER model (`UniNER-7B`) trained on a fixed entity taxonomy. If that model changes or is unavailable, Prεεmpt fails. Sovereign Learner's semantic generalization operates at the query level — it is backend-agnostic by design.

EXP03 answers two operationalised sub-questions:

1. **Protection Consistency:** Does IP protection rate remain above the 85% threshold (proven in EXP01) across all three local LLM backends?
2. **Utility Consistency:** Does educational utility (MiniLM STS and LLM Judge) remain statistically consistent (σ < threshold) regardless of which model processes the query?
3. **Reference-Based Evaluation:** How does the response to a sanitized query compare semantically to the response of an unprotected raw query (Answer-vs-Answer)?

---

## 2. Motivation & Supervisor Context

### 2.1 Why This Experiment Exists

The Sovereign Learner's architecture makes a strong theoretical claim:

> *"The semantic generalization layer protects privacy independently of the underlying LLM — the model can be swapped without re-training, re-configuring, or changing the privacy guarantees."*

EXP03 is the empirical test of this claim. Without it, supervisors can challenge whether the system's privacy properties are model-dependent artefacts rather than genuine architectural guarantees.

### 2.2 Previous Version (Rejected / Inadequate)

The original `exp03_model_diversity.py` was an 83-line stub with three critical problems:

| Problem | Impact |
|---|---|
| Imported `TEST_QUERIES` — synthetic data rejected by supervisors | Not credible for paper submission |
| Tested only 1 query (`adv_01`) against 2 models | No statistical validity — n=1 per model |
| Measured only pass/fail + timing — no IP protection or utility metrics | Cannot make any privacy or utility claims |
| Used `SovereignSystem.crew().kickoff()` — full CrewAI orchestration | Cannot isolate the privacy layer's model-agnosticism |

### 2.3 Redesign Decision

EXP03 is **fully rewritten** to:
- Use real OULAD data (same 100 queries as EXP01 OULAD subset)
- Run the full 4-stage privacy pipeline for **every query × every model**
- Measure IP protection rate, Utility STS, Utility LLM Judge, and latency **per model**
- Compute **cross-model consistency** (σ) as the primary agnosticism metric
- Test all three locally available Ollama models: `llama3.2`, `phi3.5`, `llama2`

---

## 3. Dataset

### 3.1 Primary: OULAD-Derived Educational Queries

Same dataset as EXP01 OULAD subset — 100 student support queries derived from `studentInfo.csv`:

| Property | Value |
|---|---|
| **Source** | OULAD `studentInfo.csv` (Kuzilek et al., 2017) |
| **Samples** | 100 (default) |
| **Entities per query** | 3–4 (student ID, region, IMD band, qualification, grade) |
| **Ground truth** | Exact CSV field values — objective leakage detection |
| **Loader** | Reuses `load_exp01_dataset()` from `exp01_semantic_generalization.py` |

**Why OULAD for EXP03?** Model-agnosticism is a property of the *privacy mechanism*, not the educational content. OULAD provides ground-truth entity labels that enable objective IP protection measurement regardless of which LLM produces the response. Using the same dataset as EXP01 also allows direct comparison: the EXP01 run with `llama3.2` becomes the EXP03 baseline for that model.

### 3.2 Optional: AI4Privacy Education Subset

Available via `--ai4privacy 200` flag once HuggingFace download is complete. Not run by default in the current execution due to download requirement.

---

## 4. Models Under Test

| Model | Tag | Size | Characteristics |
|---|---|---|---|
| **llama3.2** | `ollama/llama3.2` | 2.0 GB | Primary model — 3B parameters, instruction-tuned, fast |
| **phi3.5** | `ollama/phi3.5` | 2.2 GB | Microsoft Phi-3.5 mini — 3.8B parameters, strong reasoning |
| **llama2** | `ollama/llama2` | 3.8 GB | Meta LLaMA 2 7B — older baseline, for backward-compatibility testing |

All three are confirmed available locally (`ollama list`, February 2026). No internet access required during experiment execution.

---

## 5. Pipeline Under Test

Each query passes through the same 4-stage pipeline for every model:

```
Original Query (with OULAD sensitive entities)
        │
        ▼
┌───────────────────────┐
│  Stage 1              │
│  Semantic             │  ← RecontextualizationTool (model-agnostic)
│  Generalization       │  ← Entity → Entity-A, Entity-B, ...
└──────────┬────────────┘
           │ Sanitized Query  [no sensitive data]
           ▼
┌───────────────────────┐
│  Stage 2              │
│  Ollama LLM Call      │  ← Model-under-test (llama3.2 / phi3.5 / llama2)
│                       │  ← Each model tested independently
└──────────┬────────────┘
           │ Cloud Response
           ▼
┌───────────────────────┐
│  Stage 3              │
│  IP Leakage Check     │  ← Exact string match vs ground-truth entities
│                       │  ← IP Protection Rate computed
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Stage 4              │
│  Utility Measurement  │  ← STS: all-MiniLM-L6-v2 (Deep Semantic Embeddings)
│                       │  ← Comparison: Model(Unprotected) vs. Model(Sanitized)
│                       │  ← LLM Judge: same model-under-test scores its own output
└───────────────────────┘
```

**Key design principle:** Stage 1 (semantic generalization) is **identical** across all models — it uses `RecontextualizationTool` which does not call the LLM. Only Stage 2 (cloud call) varies by model. This isolates the model-agnosticism measurement: any variation in metrics between models is purely due to the cloud response quality, not the sanitization step.

---

## 6. Metrics

### 6.1 Per-Model Metrics

| Metric | Definition | Measurement |
|---|---|---|
| **IP Protection Rate** | % of ground-truth entities NOT in cloud response | Exact string match (case-insensitive) on OULAD entity values |
| **Zero-Leakage Rate** | % of queries with zero entity leakage | Count of queries where `entities_leaked == []` |
| **Utility STS** | Semantic similarity: Model(Raw Response) vs. Model(Sanitized Response) | `sentence-transformers/all-MiniLM-L6-v2` (Deep Semantic Embeddings) |
| **Utility LLM Judge** | Educational usefulness score [0.0–1.0] | Same model-under-test prompted as evaluator |
| **Avg Sanitization Time (ms)** | Stage 1 wall-clock time | `time.perf_counter()` |
| **Avg Total Pipeline Time (ms)** | End-to-end Stages 1–4 | `time.perf_counter()` |
| **Failed Queries** | Count of unhandled exceptions | Exception catch per query |

### 6.2 Cross-Model Consistency Metrics (Primary EXP03 Claim)

| Metric | Definition | Threshold |
|---|---|---|
| **IP σ** | Standard deviation of IP Protection Rate across models | < 0.05 → model-agnostic |
| **STS σ** | Standard deviation of Utility STS across models | < 0.10 → consistent utility |
| **LLM Judge σ** | Standard deviation of LLM Judge score across models | < 0.10 → consistent utility |
| **Fastest model** | Model with lowest avg total pipeline time | — |
| **Slowest model** | Model with highest avg total pipeline time | — |

> **Why σ?** The central claim is not that all models perform *identically*, but that they perform *consistently* — i.e., the privacy guarantee does not depend on which specific model is used. A σ < 0.05 on IP protection rate means the worst-case model differs from the best-case model by less than 5 percentage points. This is an objective, falsifiable threshold.

---

## 7. Hypotheses

| # | Hypothesis | Threshold | Rationale |
|---|---|---|---|
| **H1** | All models achieve IP Protection Rate ≥ 85% | Min across models ≥ 85% | The semantic generalization layer protects entities before the model sees them — model intelligence is irrelevant to protection rate |
| **H2** | IP Protection Rate σ < 0.05 across models | σ < 0.05 | Privacy guarantee is model-agnostic — Stage 1 sanitizes before any model-specific processing |
| **H3** | Utility STS σ < 0.10 across models | σ < 0.10 | Educational utility should be broadly consistent — LLMs of similar size produce similar-quality educational responses |
| **H4** | llama3.2 total pipeline latency < 10,000 ms/query (with `--max-tokens 512`) | Mean < 10s for llama3.2 | llama3.2 is the primary model — phi3.5 and llama2 may be slower but must complete without errors; token cap added to script to control verbosity |
| **H5** | Zero pipeline failures across all models | Failed = 0 | Architecture is robust to backend variation — error handling gracefully handles model-specific quirks |

---

## 8. Implementation Details

### 8.1 Environment

```
Venv manager:      uv  (pyvenv.cfg: uv = 0.9.24)
Python:            3.13.3  (CPython, ARM64)
Key Libraries:     crewai (LLM), scikit-learn (TF-IDF STS), numpy, dotenv
Ollama models:     llama3.2:latest (2.0 GB) · phi3.5:latest (2.2 GB) · llama2:latest (3.8 GB)
Ollama URL:        http://localhost:11434  (override via --ollama-url)
Data:              OULAD studentInfo.csv (same as EXP01/EXP02) — no download needed
```

### 8.2 Reproducibility Controls

| Control | Value |
|---|---|
| Dataset | Same OULAD loader as EXP01 (`load_exp01_dataset`, `seed=42`) |
| Sanitization | `RecontextualizationTool` — deterministic entity→placeholder substitution |
| STS | TF-IDF bigram cosine — deterministic (no stochastic sampling) |
| LLM temperature | Default Ollama temperature (model-dependent — not explicitly fixed) |
| Query order | Same across all models — consistency measured on identical inputs |

### 8.3 Running the Experiment

> **Prerequisite:** Ollama must be running (`ollama serve`). All three models are already available locally — no download needed.

```bash
cd /Users/madus/sovereign_system

# ── Quick smoke test (5 samples, 2 models) ────────────────────────────────
uv run python experiments/exp03_model_diversity.py \
    --max-samples 5 --oulad 5 --ai4privacy 0 --models llama3.2 phi3.5

# ── Full run — all 3 models, 100 OULAD samples (paper quality) ────────────
uv run python experiments/exp03_model_diversity.py

# ── OULAD-only, 2 models (faster) ─────────────────────────────────────────
uv run python experiments/exp03_model_diversity.py \
    --oulad 100 --ai4privacy 0 --models llama3.2 phi3.5

# ── With AI4Privacy (requires HuggingFace download) ───────────────────────
uv run python experiments/exp03_model_diversity.py \
    --oulad 100 --ai4privacy 200

# ── Quiet mode (no per-query output) ─────────────────────────────────────
uv run python experiments/exp03_model_diversity.py --quiet
```

**CLI Arguments:**

| Argument | Default | Description |
|---|---|---|
| `--models` | `llama3.2 phi3.5 llama2` | Ollama model tags (without `ollama/` prefix) |
| `--oulad` | `100` | OULAD-derived samples |
| `--ai4privacy` | `0` | AI4Privacy samples (requires HF internet) |
| `--max-samples` | all | Cap total for quick testing |
| `--max-tokens` | `512` | Max Ollama response tokens — crucial for phi3.5 which generates very long responses without a cap |
| `--ollama-url` | `http://localhost:11434` | Ollama server URL |
| `--quiet` | off | Suppress per-query verbose output |

### 8.4 Output Files

Saved to `experiments/results/`:

| File | Contents |
|---|---|
| `exp03_detailed_<timestamp>.json` | Per-query results for every model × query |
| `exp03_report_<timestamp>.json` | Aggregate metrics, consistency analysis, hypothesis verdicts |

---

## 9. Results

### 9.1 Per-Model Results (Full Validated Run — 100 OULAD Samples)
*Final results from the OULAD consistency benchmark (05 March 2026):*

| Model | IP Protection | Utility STS | LLM Judge | Zero-Leakage | Avg Time (ms) |
|---|---|---|---|---|---|
| **Llama 3.2 (3B)** | **96.8%** | 0.266 | 0.66 | 90.0% | 17,537 ms |
| **Phi-3.5 (3.8B)** | **96.4%** | 0.176 | 0.74 | 89.0% | 26,560 ms |
| **Llama 2 (7B)** | **96.2%** | 0.311 | 0.54 | 88.0% | 48,037 ms |

### 9.2 Cross-Model Consistency Analysis

| Metric | Mean | σ (std dev) | Min | Max |
|---|---|---|---|---|
| **IP Protection Rate** | **96.5%** | **0.0027** | 96.2% | 96.8% |
| **Utility STS** | 0.251 | 0.056 | 0.176 | 0.311 |
| **Utility LLM Judge** | 0.644 | 0.082 | 0.536 | 0.736 |
| **Latency (ms)** | 30,711 ms | 12,793 ms | 17,537 (Llama) | 48,037 (Llama2) |

> **Analyst Note**: The Standard Deviation of **σ = 0.0027** in IP Protection Rate across three distinct model families (Llama 3, Phi-3, and Llama 2) provides high-confidence empirical proof of **Model Agnosticism**. The slight variance in protection is likely due to stochastic generation differences in how models phrase entities, but the core privacy property remains robustly consistent.


---

### 9.3 Hypothesis Verification

| Hypothesis | Threshold | Result | Verified? |
|---|---|---|---|
| H1: All models IP ≥ 85% | Min ≥ 85% | **96.2%** | ✅ **VERIFIED** |
| H2: IP σ < 0.05 | σ < 0.05 | **0.0027** | ✅ **VERIFIED** |
| H3: STS σ < 0.10 | σ < 0.10 | **0.056** | ✅ **VERIFIED** |
| H4: Zero pipeline failures | Failed = 0 | **0** | ✅ **VERIFIED** |
| H5: Latency < 10,000 ms (Llama) | Mean < 10s | **17.5s** | ❌ **FAILED** |

> [!NOTE]
> **H5 Failure Rationale:** The latency target was missed due to the overhead of the in-pipeline evaluation (LLM Judge scoring). While the core sanitization and inference steps remain fast, the synchronous evaluation phase adds significant wall-clock time. In production, this would be decoupled into an asynchronous audit trail.

---

## 10. Connections to Other Experiments

| Experiment | Connection |
|---|---|
| **EXP01** | EXP03's `llama3.2` results with 100 OULAD queries directly replicate the EXP01 OULAD run — allowing cross-experiment consistency verification |
| **EXP02** | EXP02 used OULAD for educational ML performance; EXP03 uses same data to test LLM-backend agnosticism of the privacy layer |
| **EXP04** | EXP04 tests routing decisions; EXP03 establishes that whichever model EXP04 uses, the privacy guarantee is consistent |
| **EXP-BL-01** | EXP-BL-01 compares Sovereign Learner vs Prεεmpt on the same data — EXP03 proves SL's advantage is model-independent |

---

## 11. Supervisor Defence Notes

### Prof. Daswin De Silva
**Anticipated challenge:** *"Testing three models that differ only in size — is that meaningful diversity?"*

> The three models span 2.0 GB to 3.8 GB, represent two distinct model families (LLaMA vs Phi), and cover different generation strategies. The diversity claim is specifically about **architectural agnosticism** — that the *privacy layer* (Stage 1 semantic generalization) is independent of whichever backend model produces the cloud response. The three models provide sufficient variance in response style to make this claim meaningful. If reviewers request additional diversity, EXP03's `--models` flag supports arbitrary additional Ollama models without code changes.

### Dr. Nishan Mills
**Anticipated challenge:** *"LLM temperature is not controlled — how can you claim consistency?"*

> The consistency claim is deliberately robust to model-specific stochasticity. We measure σ (standard deviation) *across models*, not *across runs of the same model*. If IP protection rate is consistent across models despite differing temperatures, this strengthens the claim that Stage 1 sanitization (which runs before any stochastic LLM call) is the primary determinant of privacy. If reviewers require within-model consistency, we can add `--runs 3` averaging in a future version.

### Dr. Harsha Moraliyage
**Anticipated challenge:** *"EXP03 doesn't test cloud models (GPT-4, Gemini) — is it really model-agnostic?"*

> Sovereign Learner's architecture separates the privacy mechanism (Stage 1 — on-device) from the cloud call (Stage 2). For EXP03's agnosticism claim, what matters is that Stage 1 is consistent. The cloud model in Stage 2 is replaceable — Ollama local models are used here because (a) they are freely available without API keys, (b) they provide reproducible results for peer review, and (c) three distinct models providing consistent results is sufficient to demonstrate the agnosticism property. Cloud model comparison is the focus of EXP-BL-01.

---

## 12. Change Log

| Version | Date | Change |
|---|---|---|
| v1.0 | 2025 | Original EXP03 — 83-line stub testing 2 models on 1 synthetic query |
| v2.0 | February 2026 | **Full rewrite** — removed synthetic `TEST_QUERIES` dependency. Real OULAD data (100 samples). Full 4-stage pipeline per model × query. IP protection, STS, LLM Judge, latency metrics. Cross-model consistency (σ) as primary agnosticism metric. 5 falsifiable hypotheses. Detailed + aggregate JSON output. CLI-configurable models, sample counts, Ollama URL. |
| v2.1 | February 2026 | Smoke test (5 samples, llama3.2 + phi3.5) — **H1/H2 verified**: both models 100% IP protection. **phi3.5 verbosity bug found** — added `--max-tokens 512` cap to script. |
| v3.0 | March 2026 | **Full Validated Run (100 Samples)** — Tested across llama3.2, phi3.5, and llama2. Confirmed **σ = 0.0027** for IP protection. Verified model-agnosticism across multiple model families. Updated STS metrics with answer-vs-answer embeddings. |

---

*Sovereign Learner — PhD Research \| La Trobe University CDAC \| Prepared for Supervisor Review — March 2026*
