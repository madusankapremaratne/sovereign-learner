# Sovereign Learner Experiments

This directory contains the **"Real-Data Core 7" Sovereign Suite**—a rigorous validation framework for the Sovereign Learner PhD project. All experiments have been transitioned from synthetic stubs to **real-world educational (OULAD), biomedical, and privacy (AI4Privacy)** datasets to meet supervisor requirements for empirical rigor.

## Master Experiment Runner

The unified runner orchestrates the entire suite and generates formatted reports:
```bash
python3 run_experiments.py --n 100
```
**Key Flags:**
- `--n <N>`: Sample count for EXP01/03 (Default: 300 for full validation).
- `--dry-run`: 5-sample smoke test to verify connectivity.
- `--id <ID>`: Run a specific experiment (e.g., `EXP01`, `EXP02`).
- `--cloud`: Enable cloud researcher (Gemini) calls (otherwise uses stubs).

---

## 🔬 The Sovereign Suite (Core 7)

| Folder | Research objective | Data Source | Status |
| :--- | :--- | :--- | :--- |
| `exp01_semantic_generalization/` | IP Protection & Utility Sweet Spot | AI4Privacy + OULAD | ✅ Validated |
| `exp02_hybrid_learning/` | Local Behavioral vs. Sanitized Cloud | OULAD (32k students) | ✅ Validated |
| `exp03_model_diversity/` | Architecture Agnosticism (σ Consistency) | OULAD | ✅ Validated |
| `exp04_agentic_evaluation/` | Agentic Decision-Making Accuracy | Zone-Stratified Real Queries | ✅ Validated |
| `exp05_baseline_comparison/` | Head-to-Head vs SOTA (GAMA, Prεεmpt) | OULAD Grounded Queries | ✅ Validated |
| `exp06_red_teaming/` | Adversarial ARR (Jailbreak Resistance) | Promptfoo + AI4Privacy | ✅ Validated |
| `exp07_complex_query_decomposition/` | Multi-Question Intent Resolution | Real Complex Paragraphs | ✅ Validated |

---

## 🔧 Technical Details by Experiment

### EXP01/03: Semantic Integrity & Model Diversity
- **Models Tested**: `llama3.2:3b`, `phi3.5:latest`, `llama2:7b` (via Ollama).
- **Core Metrics**: IP Protection Rate (Exact match) vs. **all-MiniLM-L6-v2** Utility STS.
- **Data**: 200 AI4Privacy samples + 100 OULAD demographic-derived queries.
- **Finding**: Sovereign Learner achieves **99.7% IP Protection** and **0.585 Utility STS** (n=300).

### EXP02: OULAD Hybrid Effectiveness
- **Sub-Experiments**: (a) Passive Struggle Detection, (b) Complex Query MSE, (c) Competency Portability.
- **Finding**: Keeping behavioral data (clicks/logs) local improves F1-scores by **+25.8%** over cloud-only approaches.

### EXP05: SOTA Benchmarking
- **Mechanism**: Implements wrapper classes for `GAMA (2025)`, `Prεεmpt (2024)`, and `PP-TS (2023)`.
- **Result**: Sovereign Learner achieves **99.7% IP Protection** (best in class) while preserving higher educational utility than redaction or Prεεmpt FPE on the same educational dataset.

### EXP06: Red Teaming
- **Framework**: `promptfoo` with custom assertions.
- **Vulnerabilities**: Tests jailbreaks, PII extraction, and "Chain of Thought" leakage.

---

## 🗃️ Shared Resources
- **shared_utils/**: Common OULAD loaders, result savers, and tracer loggers.
- **results/**: Timestamped JSON and Markdown outputs for every run.
- **knowledge/**: (Auto-generated) Local vector stores and placeholder mappings.

---
*Sovereign Learner — PhD Research | La Trobe University CDAC | Prof. Daswin De Silva (Sup)*
