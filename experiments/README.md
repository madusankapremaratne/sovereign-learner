# Sovereign Learner - Experiments

This directory contains all experimental validations of the Sovereign Learner privacy-preserving AI architecture.

## 📁 Experiment Files

| File | Size | Description |
|------|------|-------------|
| `exp01_semantic_generalization.py` | 28K | IP Protection & Utility Preservation |
| `exp02_oulad_hybrid_learning.py` | 32K | Real-World Dataset Validation (OULAD) |
| `exp03_model_diversity.py` | 2.7K | Architecture Agnosticism Testing |
| `exp04_agentic_evaluation.py` | 10K | Agentic Behavior Metrics |
| `exp05_promptfoo_red_team.yaml` | 1.4K | Adversarial Red Team Testing |
| `exp05_enhanced_red_team.yaml` | 3.2K | Defense-in-Depth Guardrails Testing |

## 🚀 Quick Start

### EXP01: Semantic Generalization
```bash
cd experiments
python exp01_semantic_generalization.py --cloud --queries 100
```

### EXP02: OULAD Hybrid Learning
```bash
cd experiments
python exp02_oulad_hybrid_learning.py
```

### EXP03: Model Diversity
```bash
cd experiments
python exp03_model_diversity.py
```

### EXP04: Agentic Evaluation
```bash
cd experiments
python exp04_agentic_evaluation.py
```

### EXP05: Promptfoo Red Team
```bash
cd experiments
npm install -g promptfoo
promptfoo eval -c exp05_promptfoo_red_team.yaml
```

## 📊 Results

Experiment results are stored in:
- `results/` - JSON output files
- `dashboard/` - Visualizations and reports

## 📚 Documentation

For detailed information about each experiment, see:
- **Main Documentation:** `../EXPERIMENTS_SUMMARY.md`
- **Trace Analysis:** `../TRACE_ANALYSIS_REPORT.md`
- **Red Team Analysis:** `../dashboard/red_team_analysis.md`

## 🎯 Experiment Summary

| Experiment | Status | Key Finding |
|------------|--------|-------------|
| **EXP01** | ✅ Complete | 95% IP protection, 92% utility |
| **EXP02** | ✅ Complete | +25% F1 with local data |
| **EXP03** | ✅ Complete | Model-agnostic architecture |
| **EXP04** | ✅ Complete | 95%+ task completion |
| **EXP05** | ⚠️ Vulnerabilities Found | 25% attack resistance |
| **EXP05 Enhanced** | ✅ Complete | 93% attack resistance (+68%) |

## 🔬 Prerequisites

### Python Dependencies
```bash
pip install pandas numpy scikit-learn crewai deepeval google-generativeai python-dotenv
```

### External Services
- **Ollama** - Local LLM runtime (`ollama pull llama3.2`)
- **Google Gemini** - Cloud LLM (optional, set `GOOGLE_API_KEY`)
- **OpenAI API** - DeepEval metrics (optional, set `OPENAI_API_KEY`)

### Datasets
- **OULAD** - Download from [Open University Learning Analytics](https://analyse.kmi.open.ac.uk/open_dataset)
  - Place in `../data/oulad/`
- **Synthetic Queries** - Auto-generated (1,000+ queries)

## 📈 Running All Experiments

```bash
# Run all experiments sequentially
./run_all_experiments.sh

# Or run individually as needed
```

## 🎓 Research Contributions

These experiments provide empirical validation for:
1. **Semantic Generalization** - Privacy-utility tradeoff optimization
2. **Hybrid Learning** - Local context + cloud reasoning
3. **Architecture Flexibility** - Model-agnostic design
4. **Agentic Correctness** - Zone-aware decision making
5. **Security Limitations** - Need for defense-in-depth (EXP05)
6. **Defense-in-Depth** - 93% attack resistance with guardrails (EXP05 Enhanced)

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

## 📧 Contact

For questions about experiments, please open an issue or contact the research team.

---

**Last Updated:** 2026-02-12  
**Total Experiments:** 6 (EXP01-05 + EXP05 Enhanced)  
**Status:** ✅ 5 validated, ✅ 1 enhanced (EXP05: 25% → 93% attack resistance)
