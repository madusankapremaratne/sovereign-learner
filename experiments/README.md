# Sovereign Learner - Experiments

This directory contains all experimental validations of the Sovereign Learner privacy-preserving AI architecture.

## 📁 Experiment Files

| File | Description | Status |
|------|-------------|--------|
| `exp01_semantic_generalization.py` | IP Protection & Utility Preservation | ✅ Complete |
| `exp02a_passive_struggle.py` | Passive Struggle Detection (Local vs Cloud) | ✅ Complete |
| `exp02b_complex_query.py` | Complex Query Resolution (Hybrid Effectiveness) | ✅ Complete |
| `exp02c_competency_transfer.py` | Competency Vector Portability | ✅ Complete |
| `exp03_model_diversity.py` | Architecture Agnosticism Testing | ✅ Complete |
| `exp04_agentic_evaluation.py` | Agentic Behavior Metrics | ✅ Complete |
| `exp05_promptfoo_red_team.yaml` | Adversarial Red Team Testing | ✅ Complete |
| `exp05_enhanced_red_team.yaml` | Defense-in-Depth Guardrails Testing | ✅ Complete |
| `exp06_arr_at_scale.py` | ARR at Scale & Degradation Curves | ✅ Complete |
| `exp07_preempt_ppts_comparison.py` | SOTA Baseline (Preempt/PP-TS) | ✅ Complete |
| `exp08_ner_audit.py` | NER Coverage & Precision Audit | ✅ Complete |
| `exp09_gama_mvpi_demo.py` | GAMA Token Limitation Demonstration | ✅ Complete |
| `exp09_gama_sota_comparison.py` | SOTA Baseline (GAMA) | ✅ Complete |
| `exp10_dp_benchmarking.py` | Differential Privacy Benchmarking | ✅ Complete |
| `exp11_red_team.yaml` | Categorized Red Teaming | ✅ Complete |
| `exp12_nelr_scan.py` | Novel Entity Leakage Rate Scan | ✅ Complete |

## 🚀 Quick Start

You can run any of the python experiment scripts directly from the terminal. 

Example:
```bash
cd experiments
python exp01_semantic_generalization.py --cloud --queries 100
python exp02a_passive_struggle.py
```

For Red Team scenarios, we utilize `promptfoo`:
```bash
cd experiments
npm install -g promptfoo
promptfoo eval -c exp11_red_team.yaml
```

*Note: For `EXP08B` (Conservative Routing Fallback validation), the formal tests reside in `../tests/test_conservative_routing_fallback.py` to align with unit testing standards.*

## 📊 Results

Experiment results are stored in:
- `results/` - JSON output files
- `dashboard/` - Visualizations and reports

## 📚 Documentation

For detailed methodology, metrics, and justifications about each experiment, please refer to:
- **Main Documentation Summary:** `../docs/EXPERIMENTS_SUMMARY.md`
- **Theoretical Justifications:** `../docs/THEORETICAL_JUSTIFICATIONS.md`
- **Methodological Choices:** `../docs/METHODOLOGICAL_CHOICES_QUICK_REF.md`

## 🎓 Research Contributions

These experiments provide empirical validation for the Paper v4 improvements requested by reviewers, specifically:
1. **Semantic Generalization** - Privacy-utility tradeoff optimization.
2. **Hybrid Learning** - Scalable local context paired with cloud reasoning.
3. **Adversarial Resiliency (ARR)** - Compound multi-turn leakage resistance (EXP06).
4. **SOTA Comparisons** - Empirical superiority over Preempt (2024), PP-TS (2023), and GAMA (2025).
5. **Differential Privacy Scaling** - Demonstrating token-DP failure states (EXP10).
6. **Novel Entity Leakage Rate (NELR)** - Catching cloud-side hallucination inferences (EXP12).

## 📝 Citation

If you use these experiments in your research, please cite:

```bibtex
@software{sovereign_learner_experiments,
  title = {Sovereign Learner: Privacy-Preserving AI Experiments},
  author = {Sovereign Learner Research Team},
  year = {2026},
  url = {https://github.com/yourusername/sovereign-learner}
}
```

---

**Last Updated:** February 2026  
**Total Experiments:** 12 Core Experiments (plus variations and demos)  
**Status:** ✅ All 12 validated (fully aligns with Paper Improvement Plan v4.0).
