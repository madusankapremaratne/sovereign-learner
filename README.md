# 🛡️ Sovereign Learner System

**A Privacy-First, Agentic AI Framework for Sovereign Learning**

[![Status](https://img.shields.io/badge/Status-Research-blue)]()
[![Python](https://img.shields.io/badge/Python-3.10+-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

The **Sovereign Learner System** is an advanced multi-agent architecture that enables users to leverage state-of-the-art Cloud LLMs (like Google Gemini) while maintaining complete data sovereignty and privacy. It acts as a **Privacy Firewall** for your intellect.

---

## 🎯 Core Concept

> **"You are what you query."** 

In the age of AI, your queries reveal your knowledge gaps, research interests, and sensitive contexts. This system ensures that private information (medical protocols, proprietary research, PII) **never leaves your local machine** in raw form.

### The Semantic Generalization Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Original  │ ──▶ │  Sanitized   │ ──▶ │   Cloud     │
│   Query     │     │  Query       │     │   Response  │
│  (Private)  │     │  (Generic)   │     │  (Generic)  │
└─────────────┘     └──────────────┘     └─────────────┘
       │                                         │
       │                                         ▼
       │            ┌──────────────────────────────┐
       └───────────▶│  Recontextualized Response   │
                    │       (Private Context)      │
                    └──────────────────────────────┘
```

**Example:**
- **Original:** "How do I optimize my CRISPR protocol for HEK293 cells?"
- **Sanitized:** "How do I optimize my Protocol-Alpha for Cell-Beta?"
- **Cloud Response:** "Optimize Protocol-Alpha by adjusting reagents..."
- **Recontextualized:** "Optimize CRISPR by adjusting reagents..."

---

## 🏆 Key Features

### ✅ Privacy Protection
- **95% IP Protection Rate** with 92% utility preservation (EXP01)
- **Zone-based routing** (0-3) for granular privacy control
- **Local-first architecture** - sensitive data never leaves your device
- **Semantic generalization** - entities masked before cloud access

### ✅ Real-World Performance
- **25% better** struggle detection with local data (EXP02)
- **15-30% error reduction** with hybrid approach (EXP02)
- **40-60% faster** convergence with competency transfer (EXP02)

### ✅ Architecture Flexibility
- **Model-agnostic** - works with multiple LLM backends (EXP03)
- **Plug-and-play** - swap local/cloud models seamlessly
- **Extensible** - easy to add new agents and tools

### ✅ Agentic Correctness
- **95%+ task completion** across all zones (EXP04)
- **100% tool correctness** - agents use right tools for each zone
- **Automatic sensitivity detection** - no manual labeling required

### ⚠️ Known Limitations
- **25% attack resistance** under adversarial testing (EXP05)
- **Critical jailbreak vulnerability** discovered
- **Requires defense-in-depth** - LLM-only privacy insufficient

---

## 🧠 Architecture

### Multi-Agent System (CrewAI)

```
┌──────────────────────────────────────────────────────────┐
│                  Sovereign Manager                       │
│         (Privacy-Aware Query Router)                     │
│              Zone 0 │ Zone 1 │ Zone 2 │ Zone 3          │
└──────────────┬───────────────────────────────────────────┘
               │
    ┌──────────┴──────────┬──────────────┬──────────────┐
    │                     │              │              │
┌───▼────┐      ┌────────▼─────┐   ┌────▼────┐   ┌────▼────┐
│ Local  │      │ Sensitivity  │   │ Cloud   │   │ Cloud   │
│ Knowledge│    │  Detector    │   │ (Partial│   │ (Direct)│
│ Base   │      └──────┬───────┘   │ Sanit.) │   └─────────┘
└────────┘             │           └─────────┘
                       │
              ┌────────▼─────────┐
              │ Semantic         │
              │ Generalizer      │
              │ (Entity Masking) │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Cloud Researcher │
              │ (Gemini 2.5)     │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Trust Enforcer   │
              │ (Validation)     │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Recontextualizer │
              │ (Restore Context)│
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Evidence Curator │
              │ (ChromaDB Store) │
              └──────────────────┘
```

### Agent Roles

| Agent | Role | Zone | Model |
|-------|------|------|-------|
| **Sovereign Manager** | Privacy-aware routing | All | Local (Llama 3.2) |
| **Sensitivity Detector** | PII/PHI/IP detection | 1, 2 | Local (Llama 3.2) |
| **Semantic Generalizer** | Entity masking | 1 | Local (Llama 3.2) |
| **Cloud Researcher** | Knowledge retrieval | 1, 2, 3 | Cloud (Gemini 2.5) |
| **Trust Enforcer** | Response validation | 1, 2 | Local (Llama 3.2) |
| **Recontextualizer** | Context restoration | 1 | Local (Llama 3.2) |
| **Evidence Curator** | Learning record manager | All | Local (Llama 3.2) |

---

## 🛡️ Privacy Zones

| Zone | Description | Privacy | Latency | Use Case |
|------|-------------|---------|---------|----------|
| **Zone 0** | Offline/Local Only | 100% | ~61ms | Personal thoughts, highly sensitive PII |
| **Zone 1** | Sovereign (Sanitized) | 90% | ~1,456ms | Professional research, proprietary code, PHI |
| **Zone 2** | Opaque (Partial) | 50% | ~1,149ms | Internal projects, moderate sensitivity |
| **Zone 3** | Public (Direct) | 0% | ~873ms | Weather, facts, public knowledge |

---

## 🔬 Experimental Validation

### 5 Comprehensive Experiments

| Experiment | Focus | Key Finding | Status |
|------------|-------|-------------|--------|
| **EXP01** | IP Protection & Utility | 95% protection, 92% utility | ✅ Validated |
| **EXP02** | Real-World Dataset (OULAD) | +25% F1 with local data | ✅ Validated |
| **EXP03** | Architecture Agnosticism | Works with multiple LLMs | ✅ Validated |
| **EXP04** | Agentic Behavior | 95%+ task completion | ✅ Validated |
| **EXP05** | Adversarial Red Team | 25% attack resistance | ⚠️ Critical Findings |

**📊 Detailed Results:** See [EXPERIMENTS_SUMMARY.md](EXPERIMENTS_SUMMARY.md)

---

## 🛠️ Technology Stack

### Core Framework
- **Orchestration:** [CrewAI](https://crewai.com) - Multi-agent coordination
- **Local LLM:** [Ollama](https://ollama.com) - Privacy shield (Llama 3.2, Phi-3.5)
- **Cloud LLM:** Google Gemini 2.5 Flash - Deep knowledge
- **Memory:** [ChromaDB](https://www.trychroma.com/) - Local vector store
- **Language:** Python 3.10+

### Evaluation & Testing
- **DeepEval** - Agentic metrics (task completion, tool correctness)
- **Promptfoo** - Adversarial red team testing
- **Presidio** - PII detection (proposed for defense-in-depth)

### Data & ML
- **Pandas, NumPy, Scikit-learn** - Data processing and ML
- **OULAD Dataset** - Real-world educational data validation

---

## 📋 Prerequisites

1. **Python 3.10+** installed
2. **Ollama** installed and running
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull models
   ollama pull llama3.2
   ollama pull phi3.5
   ```
3. **Google API Key** for Gemini access
4. **Node.js** (optional, for Promptfoo red teaming)

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/madusankapremaratne/sovereign-learner.git
cd sovereign-learner
```

### 2. Install Dependencies
```bash
# Using uv (recommended)
uv sync

# OR using pip
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL=ollama/llama3.2
API_BASE=http://localhost:11434
```

### 4. Setup OULAD Dataset (Optional)
```bash
mkdir -p data/oulad
# Download OULAD from https://analyse.kmi.open.ac.uk/open_dataset
# Place CSV files in data/oulad/
```

### 5. Run the System
```bash
# Start Ollama (if not running)
ollama serve

# Run the crew
crewai run

# OR run directly
python src/sovereign_system/main.py
```

---

## 📂 Project Structure

```
sovereign_system/
├── 📄 README.md                          # This file
├── 📄 EXPERIMENTS_SUMMARY.md             # Detailed experiment documentation
├── 📄 TRACE_ANALYSIS_REPORT.md           # Trace analysis and metrics
├── 📄 PRESENTATION_RESULTS.md            # Key results for presentations
│
├── 📁 src/sovereign_system/              # Core system code
│   ├── config/
│   │   ├── agents.yaml                   # Agent definitions
│   │   └── tasks.yaml                    # Task workflows
│   ├── tools/
│   │   ├── semantic_tools.py             # Generalization & recontextualization
│   │   ├── competency_tools.py           # ChromaDB interactions
│   │   └── cloud_tools.py                # Cloud LLM integration
│   ├── utils/
│   │   ├── sovereign_trace_logger.py     # Trace logging system
│   │   └── evaluators.py                 # Privacy metrics
│   ├── crew.py                           # Main crew orchestration
│   └── main.py                           # Entry point
│
├── 📁 experiments/                       # All experiments (EXP01-05)
│   ├── README.md                         # Experiments quick reference
│   ├── exp01_semantic_generalization.py  # IP protection validation
│   ├── exp02_oulad_hybrid_learning.py    # Real-world dataset testing
│   ├── exp03_model_diversity.py          # Architecture agnosticism
│   ├── exp04_agentic_evaluation.py       # Agentic behavior metrics
│   ├── exp05_promptfoo_red_team.yaml     # Adversarial testing
│   ├── results/                          # Experiment outputs
│   └── dashboard/                        # Visualizations (1,238 traces)
│
├── 📁 data/                              # Datasets
│   ├── oulad/                            # OULAD dataset (gitignored)
│   └── synthetic/                        # Generated test queries
│
├── 📁 knowledge/                         # Local persistent memory
│   ├── chroma_db/                        # Vector embeddings
│   └── user_preference.txt               # User profile (local only)
│
├── 📁 dashboard/                         # Analysis and reports
│   ├── red_team_analysis.md              # Security findings
│   └── traces/                           # 1,238 trace files
│
└── 📁 scripts/                           # Utility scripts
    └── data_generation/                  # Synthetic data generators
```

---

## 🎯 Usage Examples

### Example 1: Biomedical Research (Zone 1)
```python
query = "How do I optimize my CRISPR protocol for HEK293 cells?"

# System automatically:
# 1. Detects sensitive entities: CRISPR, HEK293
# 2. Sanitizes: "Protocol-Alpha", "Cell-Beta"
# 3. Queries cloud with sanitized version
# 4. Recontextualizes response with original entities
# 5. Stores in local competency vector

# Result: Full privacy + cloud knowledge
```

### Example 2: Medical Query (Zone 1)
```python
query = "Patient John Doe (ID: 88221) has elevated HbA1c. Interpretation?"

# System:
# 1. Detects PII: John Doe, 88221, HbA1c
# 2. Masks: Person-A, ID-X, Biomarker-Y
# 3. Gets generic medical advice from cloud
# 4. Restores context locally
# 5. PII never sent to cloud
```

### Example 3: Public Knowledge (Zone 3)
```python
query = "What is the capital of France?"

# System:
# 1. Classifies as Zone 3 (public)
# 2. Sends directly to cloud
# 3. Returns answer immediately
# 4. No sanitization needed
```

---

## 🔄 Running Experiments

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

### EXP05: Red Team Testing
```bash
cd experiments
npm install -g promptfoo
promptfoo eval -c exp05_promptfoo_red_team.yaml
```

**📊 See [experiments/README.md](experiments/README.md) for detailed instructions**

---

## 📊 Performance Benchmarks

### Latency by Zone
| Zone | Avg Latency | Privacy Overhead | Use Case |
|------|-------------|------------------|----------|
| Zone 0 | 61ms | 0ms (local only) | Personal data |
| Zone 1 | 1,456ms | ~200ms (sanitization) | Sensitive research |
| Zone 2 | 1,149ms | ~100ms (partial) | Internal projects |
| Zone 3 | 873ms | 0ms (direct) | Public knowledge |

### Privacy vs Utility Tradeoff
```
Privacy Protection: ████████████████████░ 95%
Utility Preservation: ████████████████████░ 92%
Attack Resistance: ██████░░░░░░░░░░░░░░░ 25% (adversarial)
```

---

## 🔐 Security Considerations

### ✅ Strengths (from EXP04)
- System prompt injection resistance
- Zone 1 classification for PII
- Core privacy mechanisms functional
- 95%+ task completion in normal flows

### ⚠️ Vulnerabilities (from EXP05)
1. **Critical:** Jailbreak via roleplay (Zone misclassification)
2. **Medium:** Chain-of-thought leakage (exposes internals)
3. **Medium:** Local PII storage risk (competency vectors)

### 🛡️ Recommended Mitigations
1. **Immediate:** Implement jailbreak detection (regex patterns)
2. **High Priority:** Add Presidio validation layer
3. **Medium Priority:** Strip CoT artifacts from outputs
4. **Medium Priority:** Sanitize local storage before embedding

**📚 See [dashboard/red_team_analysis.md](dashboard/red_team_analysis.md) for details**

---

## 📈 Trace Analysis

The system generates comprehensive traces for every query:

- **Total Traces Available:** 1,238 files
- **Trace Categories:**
  - Ad-hoc runs (6 traces)
  - Demo scenarios (7 traces)
  - Synthetic tests (1,200+ traces)

**Example Trace Structure:**
```json
{
  "query_id": "18f70d5d",
  "original_query": "How do I optimize my CRISPR protocol?",
  "zone_used": 1,
  "privacy_protection_score": 0.9,
  "utility_score": 0.95,
  "total_duration_ms": 1823.6,
  "steps": [
    {"agent_name": "Sovereign Manager", "duration_ms": 45.2},
    {"agent_name": "Semantic Generalizer", "duration_ms": 120.5},
    {"agent_name": "Cloud Researcher", "duration_ms": 1540.2},
    {"agent_name": "Recontextualizer", "duration_ms": 85.6}
  ]
}
```

**📊 See [TRACE_ANALYSIS_REPORT.md](TRACE_ANALYSIS_REPORT.md) for full analysis**

---

## 🎓 Research Contributions

### Novel Approaches

1. **Semantic Generalization**
   - Entity-aware sanitization with reversible mapping
   - Utility preservation while protecting IP
   - First system to achieve 95% protection with 92% utility

2. **Hybrid Learning Architecture**
   - Local context + cloud reasoning
   - Zone-based routing for privacy-utility optimization
   - 25% better performance than cloud-only approaches

3. **Competency Portability**
   - Cross-course transfer learning
   - 40-60% cold-start reduction
   - Privacy-preserving personalization

4. **Agentic Privacy Framework**
   - Zone-aware tool selection
   - Automatic sensitivity detection
   - Multi-layer defense architecture

### Key Insight
> **"Agentic privacy is necessary but not sufficient."**

While LLM-based privacy protection achieves 95%+ effectiveness in normal scenarios, adversarial testing reveals a 75% attack success rate, demonstrating the need for defense-in-depth combining LLM routing, rule-based validation, and PII detection frameworks.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | This file - project overview |
| [EXPERIMENTS_SUMMARY.md](EXPERIMENTS_SUMMARY.md) | Detailed experiment documentation (5 experiments) |
| [THEORETICAL_JUSTIFICATIONS.md](THEORETICAL_JUSTIFICATIONS.md) | **NEW!** Defense of metrics (F1, MSE) & algorithms (Random Forest vs XGBoost) |
| [METHODOLOGICAL_CHOICES_QUICK_REF.md](METHODOLOGICAL_CHOICES_QUICK_REF.md) | **NEW!** Quick cheat sheet for design choices |
| [TRACE_ANALYSIS_REPORT.md](TRACE_ANALYSIS_REPORT.md) | Analysis of 1,238 traces with metrics |
| [PRESENTATION_RESULTS.md](PRESENTATION_RESULTS.md) | Key results for presentations |
| [experiments/README.md](experiments/README.md) | Experiments quick reference |
| [dashboard/red_team_analysis.md](dashboard/red_team_analysis.md) | Security findings from EXP05 |

---

## 🤝 Contributing

Contributions are welcome! Areas of interest:

1. **Defense-in-Depth Implementation**
   - Presidio integration
   - Rule-based jailbreak detection
   - Output sanitization

2. **Additional Experiments**
   - EXP06: Enhanced adversarial defense
   - EXP07: Scalability testing
   - EXP08: Domain adaptation
   - EXP09: Federated learning

3. **Performance Optimization**
   - Parallel agent execution
   - Caching strategies
   - Latency reduction

4. **Domain Extensions**
   - Healthcare (HIPAA compliance)
   - Finance (regulatory requirements)
   - Legal (attorney-client privilege)

---

## 📝 Citation

If you use this system in your research, please cite:

```bibtex
@software{sovereign_learner_2026,
  title = {Sovereign Learner: A Privacy-First Agentic AI Framework},
  author = {Premaratne, Madusanka},
  year = {2026},
  url = {https://github.com/madusankapremaratne/sovereign-learner},
  note = {Comprehensive experimental validation with 5 experiments}
}
```

---

## 📧 Contact

- **Author:** Madusanka Premaratne
- **Email:** madusankapremaratne@gmail.com
- **GitHub:** [@madusankapremaratne](https://github.com/madusankapremaratne)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **CrewAI** - Multi-agent orchestration framework
- **Ollama** - Local LLM runtime
- **Google Gemini** - Cloud LLM capabilities
- **OULAD** - Open University Learning Analytics Dataset
- **Promptfoo** - Red team testing framework
- **DeepEval** - Agentic evaluation metrics

---

## 🎯 Project Status

**Current Version:** Research Prototype  
**Last Updated:** 2026-02-01  
**Total Experiments:** 5 (7 sub-experiments)  
**Validation Status:** ✅ 4 validated, ⚠️ 1 reveals critical security gaps  
**Next Steps:** Implement defense-in-depth architecture (EXP06)

---

**Built with ❤️ for Data Sovereignty and Privacy-Preserving AI**

*"Your data, your knowledge, your sovereignty."*
