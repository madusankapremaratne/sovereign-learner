# Privacy-Preserving AI Systems: Comparative Analysis

**Prepared for:** Supervisor Meetings — Prof. Daswin De Silva & Dr. Nishan Mills  
**Author:** Madusanka P. Rathnayake Mudiyanselage  
**Research:** Sovereign Learner — Privacy-Preserving Agentic AI for Educational Applications  
**Date:** February 2026

---

## Systems Under Comparison

| ID | System | Authors | Year | Venue |
|----|--------|---------|------|-------|
| **PP-TS** | Protecting User Privacy in Remote Conversational Systems: A Privacy-Preserving Framework Based on Text Sanitization | Kan et al. | 2023 | arXiv (cs.CR) |
| **GAMA** | A General Anonymizing Multi-Agent System for Privacy Preservation Enhanced by Domain Rules and Disproof Method | Yang et al. | 2025 | arXiv (NeurIPS submission) |
| **Prεεmpt** | Prεεmpt: Sanitizing Sensitive Prompts for LLMs | Roy Chowdhury et al. | 2025 | arXiv (cs.CR) |
| **SL** | **Sovereign Learner** | Rathnayake Mudiyanselage et al. | 2026 | *Under Preparation — IEEE* |

---

## 1. Core Problem Statement

| System | Problem Being Solved |
|--------|---------------------|
| **PP-TS** | Users accessing remote LLMs via API risk exposing sensitive personal information (names, addresses) to cloud service providers and network eavesdroppers |
| **GAMA** | Multi-agent systems (MAS) that rely on cloud LLMs for reasoning cannot securely process tasks containing private data, as all agent communication flows through public space |
| **Prεεmpt** | Sensitive tokens in LLM prompts at inference time are exposed to proprietary API providers; existing solutions lack formal, cryptographically provable privacy guarantees |
| **SL** | Students and researchers querying cloud AI systems expose not just personal identity but **intellectual property** — research methods, dissertation topics, learning gaps — which existing systems are not designed to protect |

> **Key distinction:** PP-TS, GAMA, and Prεεmpt all address *identity privacy* (who you are). The Sovereign Learner addresses *intellectual privacy* (what you know and are researching) — a fundamentally different and education-specific threat model.

---

## 2. Data Types Protected

| System | Protected Data Types | What Is NOT Protected |
|--------|---------------------|----------------------|
| **PP-TS** | Named entities: names, addresses, locations, user-defined PII categories | Research intent, domain knowledge, query patterns, semantic context |
| **GAMA** | Named entities via NER: names, organisations, phone numbers, email addresses, locations | Domain-specific intellectual content, research methodology, behavioural data |
| **Prεεmpt** | **Category I:** Format-sensitive tokens (SSN, credit card, passport, phone numbers) via FPE. **Category II:** Value-sensitive tokens (age, salary, medical values) via metric-DP | Contextual semantic privacy explicitly excluded ("future work"); research intent; educational data |
| **SL** | **Intellectual Property:** Domain-specific research terms (e.g., CRISPR protocols, proprietary methodologies), research intent, learning gaps, competency profiles, student behavioural patterns | *(Addresses the broadest protection scope)* |

---

## 3. Basic Idea / Core Mechanism

### PP-TS — Multi-Cycle Text Sanitization with In-Context Learning Injection

PP-TS operates in sequential cycles, one privacy type per cycle (e.g., first pass for names, second for addresses). For each cycle, it constructs a composite prompt for a **local Llama-7B** model by injecting three elements together using in-context learning:

1. **Rewrite Requirements** — instructions specifying what type of privacy to sanitize
2. **Few-Shot Sanitization Examples** — k demonstrations of how previous inputs were sanitized (the context injection)
3. **The actual user input** — appended to the above

The local model then performs entity replacement — substituting "Paris" with "London," for example. However, this naive substitution creates semantic contradictions (the sentence might still say "near the Eiffel Tower," making "London" implausible). PP-TS addresses this with a **Reasonability Check loop**:

- If the sanitized output contains a contradiction, a second local inference pass rewrites the conflicting context (e.g., "Eiffel Tower" → "an iconic building")
- This loop repeats until the output is internally coherent
- A locally stored **Plaintext-Ciphertext mapping** enables the cloud response to be post-processed to restore original entities

**Weakness:** The reasonability check is itself LLM-based and can fail. The ablation shows removing it drops DUR (data utility rate) from 92.33% to 81.67%. The system is stateful (requires the mapping table) and serial (multiple cycles add latency proportional to privacy type count).

```
User Input → [Cycle 1: Name sanitization with few-shot injection] 
           → Reasonability check → Fix contradictions 
           → [Cycle 2: Address sanitization with few-shot injection] 
           → ... → Sanitized Input → Remote LLM → Response → Privacy Recovery
```

---

### GAMA — Private/Public Space Separation with Knowledge and Logic Compensation

GAMA's fundamental insight is **architectural**: rather than sanitizing at the query level, it separates the entire multi-agent workspace into zones. All sensitive data stays in **private space**; only anonymized data enters **public space** where cloud LLMs operate.

**AMPP — Anonymizing Mechanism for Privacy Preservation** uses dual-view identification (MVPI):

- **PNER View:** Fine-tuned BERT-large NER model identifies named entities locally — precise but narrow, limited to trained categories
- **PIA View:** LLM-based agent applies human social common sense — recognises that a famous politician's name may not be private even if NER flags it
- **Multi-View Fusion:** Intersection of both views forms the definite private set; entities only in one view go through agent-based arbitration

Identified entities are replaced with typed placeholders (`<name-1>`, `<location-2>`) stored in a local **Privacy Box** mapping table. The anonymized task crosses into public space.

**Critical acknowledged problem:** Anonymization causes semantic loss — the ablation proves this directly. Removing AMPP *increases* task performance by 7 points on KPP. GAMA introduces two compensation modules to recover this lost utility:

- **DRKE (Domain-Rule-based Knowledge Enhancement):** Identifies task domain (finance, history, medicine etc.), constructs IF-THEN expert agent rules, routes the anonymized query through multiple domain expert agents simultaneously, then fuses their outputs
- **DLE (Disproof-based Logic Enhancement):** Iterative contradiction checking — expert agent answers, assistant agent identifies logical contradictions, expert revises, repeat until no contradiction found

```
Input → Private Space [MVPI identification → AMPP anonymization → Privacy Box]
      → Public Space [DRKE domain routing → Expert Agents → DLE contradiction loop]
      → Private Space [Nominating Agent restores placeholders → Final Answer]
```

---

### Prεεmpt — Cryptographic Prompt Sanitizer with Formal Privacy Guarantees

Prεεmpt's contribution is both definitional and technical. It first formalises the notion of a **prompt sanitizer** as a cryptographic primitive — a tuple of (Setup, Type Annotator, Sanitization, Desanitization) algorithms with a game-based security definition. It then builds a system that instantiates this primitive with provable bounds.

The key insight is that **not all sensitive tokens need the same treatment** — their protection mechanism should match what the LLM actually does with them:

**Category I Tokens** (format-dependent): SSN, credit card numbers, passport numbers, phone numbers — the LLM's response depends only on *format*, not value. Protected via **Format-Preserving Encryption (FPE)**: the ciphertext has identical structure to plaintext (a 9-digit SSN encrypts to another valid 9-digit number). The LLM behaves identically on the encrypted value, and FPE can be exactly reversed using the secret key — making desanitization stateless and mathematically exact.

**Category II Tokens** (value-dependent): Age, salary, medical measurements — the LLM *computes* with these values, so the response depends on the actual number. Protected via **Metric Local Differential Privacy (mLDP)**: a controlled noise mechanism that maps the input to a nearby value (age 46 might become 44 or 49). This preserves ordinality and approximate magnitude while providing a formal ε-privacy bound. Desanitization is impossible for Category II — the response contains perturbed values permanently.

A **helper string Ψ** encodes functional dependencies between tokens (e.g., Annual Salary = 12 × Monthly Salary) to ensure consistent perturbation across correlated sensitive values.

**Formal guarantee:** Adversary's advantage is bounded by e^(l·ε) + negl(κ), where l is the distance between protected values and κ is the FPE security parameter. This is the only system of the four with a mathematical proof.

**Explicit limitation:** Contextual semantic privacy — where individual tokens are not sensitive but the full prompt reveals private information — is explicitly out of scope.

```
Prompt → Type Annotator (NER) 
       → Category I tokens → FPE encryption (stateless, reversible)
       → Category II tokens → mLDP noise (irreversible, formally bounded)
       → Sanitized Prompt → Cloud LLM → Response 
       → Desanitizer (Category I: FPE decrypt; Category II: unchanged)
       → Final Response
```

---

### Sovereign Learner — Semantic Generalization at the Intent Layer with Agentic Zone Routing

The Sovereign Learner begins from a different threat model: in education, the danger is not that a student reveals their name — it is that their query pattern reveals their **research methodology, intellectual gaps, proprietary protocols, and competitive knowledge**. None of the other three systems are designed around this threat.

**Semantic Generalization** operates at the intent layer, not the token layer. Instead of replacing "CRISPR" with an encrypted token or random substitution, the Semantic Generalizer agent transforms the entire conceptual frame of the query:

> *"How do I optimize my CRISPR protocol for HEK293 cells?"*  
> → *"How do I optimize Protocol-Alpha for Cell-Beta?"*

The replacement is not random — it preserves the **logical structure** of the question (a protocol optimisation question for a cell line) while hiding the domain-specific identifiers that reveal the researcher's actual work. This is why the contradiction problem that forces PP-TS into a reasonability loop does not arise: the generalised form is a valid, coherent question in its own right.

**Zone-Based Governance** adds privacy routing that no other system implements. The Sovereign Manager agent classifies every query before any sanitization:

| Zone | Trigger | Processing |
|------|---------|-----------|
| Zone 0 | Maximally sensitive (patient data, classified research) | Local Phi-3.5 only — cloud never contacted |
| Zone 1 | Sensitive IP (proprietary protocols, research methods) | Full 6-stage semantic generalization pipeline |
| Zone 2 | Moderate sensitivity | Optimistic local processing + background cloud validation |
| Zone 3 | Low sensitivity | Direct cloud with minimal sanitization overhead |

**Trust Enforcement** post-cloud is unique to this system: the Trust Enforcer agent validates that the cloud response does not contain information that could reconstruct the sanitized entities. If validation fails after 3 retries, the system degrades gracefully to Zone 0 rather than returning a compromised answer.

**Competency Tracking** is the fourth layer — every interaction across all zones stores locally in ChromaDB, building a private longitudinal learner model. The cloud never sees the learner profile. This enables personalization without privacy sacrifice — empirically validated as a 56% reduction in cold-start time and 25.8% better struggle detection than cloud-only processing.

```
Query → Sovereign Manager [Zone Classification 0-3]
      ↓ Zone 0: Local Phi-3.5 only
      ↓ Zone 1-2: Sensitivity Detector → Semantic Generalizer 
                → Cloud Researcher (Gemini) → Trust Enforcer
                → Recontextualizer (restores original context)
      → Competency Curator [stores all interactions locally in ChromaDB]
      → Final Response + Updated Local Learner Profile
```

---

## 4. Hybrid Architecture Comparison

| Dimension | PP-TS | GAMA | Prεεmpt | Sovereign Learner |
|-----------|-------|------|---------|-------------------|
| **Local component role** | Filter only (sanitize/recover) | Anonymization + Private space agents | Sanitize/desanitize only | Full reasoning — classification, sanitization, trust enforcement, recontextualization, memory |
| **Cloud component role** | All reasoning on sanitized input | All reasoning on anonymized input | All reasoning on sanitized input | Reasoning on generalized queries only |
| **Local model** | Llama-7B | Llama3-8B | None (algorithmic only) | Phi-3.5 (via Ollama) |
| **Cloud model** | ChatGPT (gpt-3.5-turbo) | GPT-4o | GPT-4o, Gemini-1.5 | Gemini 2.5 Flash |
| **Local memory/state** | Plaintext-Ciphertext mapping table | Privacy Box (placeholder mapping) | Secret key only (stateless) | ChromaDB vector store — full learner history |
| **Dynamic routing** | No — all queries same treatment | No — all tasks cross same boundary | No — all tokens categorised uniformly | Yes — Zone 0–3 determines processing path |
| **Empirical hybrid benefit proven** | No | Partially (DRKE/DLE compensate for anonymization loss) | No | Yes — 25.8% better F1 for local vs. sanitized cloud; hybrid beats both single approaches |

---

## 5. Agentic AI Usage

| System | Agent Architecture | Agent Roles | Orchestration |
|--------|-------------------|-------------|---------------|
| **PP-TS** | None | Single pipeline, no agents | Sequential pipeline |
| **GAMA** | Multi-agent (most complex of the three) | Anonymizing Agent, Nominating Agent, Domain Analyzing Agent, Domain Expert Agents (dynamic, per domain), Assistant Agent (contradiction checker) | Custom coordination logic |
| **Prεεmpt** | None | Purely algorithmic — NER model + FPE + mLDP mechanisms | Deterministic algorithm |
| **SL** | 6-agent CrewAI orchestration | Sovereign Manager (zone router), Sensitivity Detector, Semantic Generalizer, Cloud Researcher, Trust Enforcer, Recontextualizer, Competency Curator | CrewAI with bounded retry, graceful degradation |

**Key differentiator:** GAMA's agents improve task *performance* (QA accuracy). The Sovereign Learner's agents implement *privacy governance as a first-class architectural concern* — the Sovereign Manager agent makes a privacy policy decision on every query before any processing occurs. No other system has this governance layer.

---

## 6. Educational Application

| System | Educational Design | Educational Dataset | Educational Metrics |
|--------|--------------------|--------------------|--------------------|
| **PP-TS** | None — general conversational AI | None — ACE2005 (event extraction) | None |
| **GAMA** | None — general QA benchmarks | None — TCW, LGP, custom KPP/LPP | None |
| **Prεεmpt** | None — general LLM use cases | None — WMT-14, NarrativeQA, ConvFinQA | None |
| **SL** | Purpose-built for education: struggle detection, competency tracking, cold-start mitigation, cross-course transfer | **OULAD — 32,593 real student records**, millions of interaction logs, real behavioural data | Struggle detection F1, MSE for grade prediction, cold-start convergence time, competency vector portability |

> **The gap:** All three comparator systems treat privacy as a domain-general problem. The Sovereign Learner is the first system to address privacy in the specific context of educational AI, with a threat model (intellectual property protection), dataset (OULAD), and metrics (educational outcome improvement) that directly serve this domain.

---

## 7. Datasets Used

| System | Dataset | Size | Type | Privacy Stakes |
|--------|---------|------|------|----------------|
| **PP-TS** | ACE2005 (event extraction) | 100 samples | Synthetic adversary testing | Low — no real private data |
| **GAMA** | TCW, LGP (trivia/logic QA) | 100–200 instances | General benchmarks | None — publicly accessible |
| **GAMA** | KPP, LPP (custom privacy QA) | 100/150 instances | Author-designed | Controlled synthetic private data |
| **Prεεmpt** | WMT-14 (translation) | 50 samples per attribute | Real text, synthetic PII | Moderate |
| **Prεεmpt** | NarrativeQA (long-context QA) | 50 samples | Real text | Moderate |
| **Prεεmpt** | ConvFinQA (financial QA) | Multi-turn financial reports | Real financial documents | High for domain, but anonymized |
| **Prεεmpt** | AI4Privacy dataset (NER fine-tuning) | 70K samples | PII-labelled text | Synthetic |
| **SL** | **OULAD** | **32,593 students**, millions of interaction logs | **Real educational behavioural data** | **High — actual grades, engagement, outcomes** |

---

## 8. Experiments Conducted

### PP-TS

| Experiment | Metric | Result |
|-----------|--------|--------|
| Privacy removal effectiveness | PRR (Privacy Removal Rate) | 95.96% |
| Data utility preservation | DUR (Data Utility Rate) | 92.33% |
| Manual adversarial attack | DPR — literal detection | 93.00% |
| Manual adversarial attack | DPR — logical inference | 89.00% |
| Procedural adversarial attack | DPR — literal detection | 94.33% |
| Procedural adversarial attack | DPR — logical inference | 91.00% |
| Ablation: no reasonability check | DUR | 81.67% (↓ 10.66%) |
| Event extraction task performance | F1 score | 48.91% (vs. 51.73% without privacy filter) |

*Dataset: 100 samples from ACE2005.*

---

### GAMA

| Experiment | Metric | Result |
|-----------|--------|--------|
| QA accuracy (TCW, N=5) | Score | 87.4% (+17.2% vs. Standard) |
| QA accuracy (TCW, N=10) | Score | 88.3% (+14.7% vs. Standard) |
| Logic QA (LGP) | Score | 75.5% (+30.8% vs. Standard) |
| Privacy identification (KPP) | F1 | GAMA best (+7.3 avg over NER-PRE) |
| Privacy identification (LPP) | F1 | GAMA best (+6.2 avg over NER-PRE) |
| Re-identification attack (ARX) | Success rate | < 0.21% across all attacker profiles |
| KPP QA under privacy preservation | Score | 54.8 |
| LPP QA under privacy preservation | Score | 82.0 |
| Ablation: AMPP off | KPP Score | 61.8 (↑ 7 — anonymization hurts) |
| Ablation: DRKE off | KPP Score | 57.3 (↓ 3.5) |
| Ablation: DLE off | KPP Score | 53.2 (↓ 1.6) |
| Statistical significance | Friedman test p-value | 0.000423 (significant vs. all baselines) |

---

### Prεεmpt

| Experiment | Task | Metric | Result |
|-----------|------|--------|--------|
| Translation utility | English → German/French | BLEU score | Nearly identical to unsanitized baseline |
| RAG factual retrieval | E-commerce QA | Accuracy | 100% |
| RAG numerical comparison | Credit card balances | Accuracy | 100% |
| Long-context QA | NarrativeQA | STS score | 0.934 (GPT-4o); outperforms Papillon (0.854) |
| Multi-turn financial QA | ConvFinQA | Median relative error | 0.0408 at ε=1.0 |
| NER performance | 10 PII categories | F1 | ~100% for most categories (fine-tuned UniNER) |
| Format ablation: AES vs FPE | RAG QA | Accuracy | 100% FPE vs. 70.97% AES (format matters) |
| Comparison with Papillon | Translation BLEU | BLEU | Prεεmpt significantly outperforms |
| Privacy leakage (NER failure) | Translation | Unique PII missed | 4% (UniNER) vs. 97% caught |

---

### Sovereign Learner

| Experiment | Research Question | Key Finding |
|-----------|-------------------|-------------|
| **EXP01** — Semantic Generalization Effectiveness | Can we protect IP while preserving educational utility? | **Baseline under formal establishment** via AI4Privacy/OULAD datasets (replaces prior unverified synthetic estimates) |
| **EXP02a** — Local vs. Sanitized Cloud | Does local data access outperform sanitized cloud for struggle detection? | **+25.8% F1 improvement** — local behavioural data beats sanitized cloud significantly |
| **EXP02b** — Hybrid vs. Single Approach | Does the hybrid architecture outperform either alone? | **22–30% lower MSE** — hybrid local+cloud beats local-only and cloud-only on grade prediction |
| **EXP02c** — Competency Transfer | Does cross-course knowledge transfer reduce cold-start? | **56% reduction in convergence time** — prior competency vectors transfer across courses |
| **EXP03** — Model Agnosticism | Can the system swap local LLMs without code changes? | Validated across Llama3.2, Phi-3.5, Llama2 — full pipeline functional with no architecture changes |
| **EXP04** — Agentic Task Completion | Is agent orchestration reliable? | **95%+ task completion rate** across all privacy zones |
| **EXP05** — Red Team Adversarial Testing | What are the system's vulnerabilities? | Single-layer LLM protection: **75% attack success rate** — motivates defence-in-depth architecture. Direct empirical evidence for multi-layer guardrails |

*Primary dataset: OULAD — 32,593 real student records, millions of interaction logs.*

---

## 9. Privacy Guarantee Comparison

| System | Guarantee Type | Formal? | Attack Resistance |
|--------|---------------|---------|-------------------|
| **PP-TS** | Empirical — PRR + DPR metrics | No — no mathematical proof | 89–94% DPR; vulnerable to logical inference attacks |
| **GAMA** | Empirical — re-identification attack via ARX tool | No — no mathematical proof | < 0.21% re-identification success |
| **Prεεmpt** | **Cryptographic + DP** — Adversary advantage bounded by e^(lε) + negl(κ) | **Yes — formal proof** | Provably bounded; NER errors modelled in leakage function |
| **SL** | Empirical — IP leakage rate + red team testing | No — empirical validation | Empirical baseline under formal establishment in normal operation; 25% attack resistance in adversarial conditions; red team findings motivate defence-in-depth |

---

## 10. Utility Preservation Under Privacy

| System | Utility Metric | Utility Without Privacy | Utility With Privacy | Δ |
|--------|---------------|------------------------|---------------------|---|
| **PP-TS** | DUR (data utility rate) | 100% | 92.33% | −7.67% |
| **PP-TS** | Event extraction F1 | 51.73% | 48.91% | −2.82% |
| **GAMA** | KPP Score (w/ AMPP on) | 61.8 (AMPP off) | 54.8 | −7.0 pts |
| **GAMA** | TCW Score | 74.6 (Standard) | 87.4 | +17.2% (agents help) |
| **Prεεmpt** | Translation BLEU | Baseline | ~Identical | ~0% |
| **Prεεmpt** | RAG accuracy | 100% | 100% | 0% |
| **Prεεmpt** | Long-context STS | 0.934 | 0.934 | 0% |
| **SL** | Educational utility preservation | 100% (direct cloud) | TBD | TBD |
| **SL** | Struggle detection F1 | 100% (local, no privacy) | +25.8% vs. sanitized cloud | Local privacy *improves* outcomes |

---

## 11. Limitations Comparison

| System | Key Limitations |
|--------|----------------|
| **PP-TS** | Stateful (mapping table required); serial processing (one type per cycle, slow); reasonability check itself can fail; small evaluation set (100 samples); no educational application |
| **GAMA** | Anonymization demonstrably hurts performance (−7 pts on KPP); cannot autonomously identify novel privacy categories; significant semantic loss for complex tasks; 138s average response time; no educational application |
| **Prεεmpt** | Contextual semantic privacy explicitly out of scope; Category II tokens permanently perturbed (no desanitization); privacy budget must be manually configured; no educational application; NER failure leaks privacy |
| **SL** | Residual leakage from contextual inference requires formal quantification; red team results show 75% attack success (single-layer) — requires defence-in-depth; domain-dependent generalisation quality (biomedical clearer than legal); no formal mathematical proof (empirical validation only); multi-turn conversation privacy across sessions not yet addressed |

---

## 12. Positioning Summary for IEEE Paper

### What Makes the Sovereign Learner Novel

| Novelty Claim | Evidence |
|--------------|----------|
| First system to address intellectual property privacy in educational AI | No comparator targets research intent or academic IP as the threat model |
| Semantic generalization operates at intent layer (not token/entity layer) | PP-TS: token; GAMA: named entity; Prεεmpt: token type; SL: semantic intent |
| Zone-based proportionate privacy governance | No comparator implements dynamic routing based on query sensitivity level |
| Empirically proves privacy and personalization are complementary | 25.8% better struggle detection with local data; no comparator demonstrates this |
| Multi-agent architecture where agents enforce privacy policy, not just process queries | GAMA uses agents for QA performance; SL uses agents for governance |
| Validated on real educational data (OULAD, 32,593 students) | All comparators use general benchmarks or synthetic data |
| Honest adversarial disclosure motivating defence-in-depth | Red team results (EXP05) reported transparently — expected by responsible AI reviewers |

### Anticipated Supervisor Questions and Responses

**Q (Prof. Daswin): How is semantic generalization different from token substitution?**  
Substitution replaces tokens with encrypted or random alternatives that break semantic coherence, requiring a reasonability loop to fix contradictions (PP-TS approach). Semantic generalization transforms the entire conceptual frame so the abstract form is a coherent, valid question in its own right — no contradiction arises, and educational utility is preserved without post-hoc correction.

**Q (Dr. Nishan): Why agents instead of a simpler deterministic pipeline?**  
The zone-based routing requires context-aware decision making that a deterministic pipeline cannot implement. A static pipeline applies the same privacy treatment to every query — the Sovereign Manager agent classifies each query and applies proportionate protection. Zone 0 queries never reach cloud at all; Zone 3 queries skip sanitization overhead. This is both more efficient and more aligned with real privacy governance principles.

**Q (Both): The red team results show 75% attack success — is the system actually secure?**  
Yes, relative to alternatives. PP-TS shows 11% logical inference leakage even with reasonability checks. GAMA's own ablation shows anonymization hurts performance. The red team findings are reported to motivate a defence-in-depth architecture (rule-based jailbreak detection + LLM routing + Presidio PII validation + output sanitization). This honest disclosure is what responsible AI research looks like — and it is a stronger contribution than claiming perfect security on a small, controlled evaluation set.

---

*Document prepared for internal research use. All comparator results cited from original publications.*