# Sovereign Learner Experiments

This directory contains the experimental suite for the Sovereign Learner PhD project. Experiments are organized into subfolders based on their research objective.

## Master Experiment Runner

Instead of running individual scripts, use the unified runner from the root directory:
```bash
python3 run_experiments.py --n 10
```
Flags:
- `--n <N>`: Set sample count (overrides internal defaults).
- `--dry-run`: Fast verification mode.
- `--id <EXPID>`: Run a specific experiment (e.g., `EXP05`).

---

## Experiment Directory Structure

| Folder | Research Objective | Status |
| :--- | :--- | :--- |
| `exp01_semantic_generalization/` | Zone 1 & 2 Semantic Mapping Accuracy | ✅ Validated |
| `exp02_hybrid_learning/` | Hybrid Learning (OULAD Struggle/Complex Queries) | ✅ Validated |
| `exp03_model_diversity/` | Architecture Agnosticism (LLaMA/Mistral/Gemma) | ✅ Validated |
| `exp04_agentic_evaluation/` | Agentic Workflow & Reasoning Metrics | ✅ Validated |
| `exp05_baseline_comparison/` | SOTA Baseline Comparison (GAMA, PP-TS, Prεεmpt, AI4Privacy) | ✅ Validated |
| `exp06_red_teaming/` | Red Teaming (Promptfoo Jailbreak Resistance) | ✅ Validated |
| `exp07_complex_query_decomposition/` | Complex Multi-Question Decomposition v1 vs v2 | ✅ Validated |
| `shared_utils/` | Shared data loaders and query builders | ✅ Active |

## Key Scripts by Experiment

### EXP 05: Baseline Comparison
- **Main Script**: `exp05_baseline_comparison/exp05_baseline_comparison.py`
- **Baselines**: `preempt_baseline.py`, `pp_ts_baseline.py`, `gama_baseline.py`, `ai4privacy_baseline.py`
- **Mechanism**: Statistical head-to-head against 4 SOTA privacy frameworks.

### EXP 06: Red Teaming
- **Config**: `exp06_red_teaming/exp06_red_team.yaml`
- **Tool**: Promptfoo-based automated adversarial testing.

### EXP 07: Complex Query Decomposition
- **Main Script**: `exp07_complex_query_decomposition/exp07_complex_query_decomposition.py`
- **Mechanism**: Paragraph splitting, shared entity mapping, and reassembly stress tests.

## Shared Resources
- **OULAD Loader**: `shared_utils/oulad_utils.py`
- **Results Folder**: `experiments/results/` (JSON and Markdown reports)
