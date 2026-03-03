# Implementation Plan: Sovereign Learner (Paper Improvements)

**Date:** February 2026
**Version:** 1.0 (Aligns with Paper Improvement Plan v4.0)

## 1. Project Architecture Overview

The Sovereign Learner is an agentic, privacy-preserving system designed for educational AI. It utilizes a **hybrid local/cloud architecture** orchestrated by **CrewAI**.

### Core Workflow:
1.  **Sovereign Manager (Local):** Routes queries to specific zones (0–3) based on sensitivity.
2.  **Sensitivity Detector (Local):** Uses Microsoft Presidio and domain-specific NER to identify PII and sensitive educational IP (e.g., protocols, methods).
3.  **Semantic Generalizer (Local):** Obfuscates sensitive entities using type-safe placeholders (e.g., `Protocol-A`) and maintains a local mapping.
4.  **Cloud Researcher (Cloud):** Processes the sanitized query using a high-capacity LLM (e.g., GPT-4o, Gemini 1.5 Pro).
5.  **Trust Enforcer (Local):** Scans cloud responses for residual leakage (CoT, PII) before surfacing to the user.
6.  **Re-contextualizer (Local):** Swaps placeholders back with original entities using the local mapping.
7.  **Sovereign Trace (Dashboard):** A monitoring layer that tracks privacy exposure and latency across each stage.

---

## 2. Areas for Improvement (Critique Addressing)

Based on the `paper_improvement_plan.md`, the following areas require immediate technical and empirical reinforcement:

*   **Formalization of Metrics:** Transition from vague privacy claims to **Adversarial Reconstruction Resistance (ARR)** and **Novel Entity Leakage Rate (NELR)**.
*   **NER Robustness:** Mitigation of NER false negatives through a **Conservative Routing Fallback** (routing to Zone 0/Local-only when confidence is low).
*   **Empirical Comparisons:** Moving from qualitative descriptions to head-to-head benchmarking against **Preempt (2024)**, **PP-TS (2023)**, and **GAMA (2025)**.
*   **Statistical Power:** Scaling the evaluation corpus from 500 to **2,000 queries** and the Red Team from 40 to **200+ prompts**.
*   **Transparency:** Explicitly reporting the **Privacy Waterfall** (per-stage gain) and **Resource Footprint** (latency/memory).

---

## 3. Implementation Plan for Experiments

### Phase 1: Metric Foundation & Lightweight Scans (Weeks 1-2)
*   **EXP12: NELR Post-hoc Scan:**
    *   Develop a script to run NER on existing `results/` JSON files to detect entities in cloud responses not present in the original sanitized query.
    *   Quantify "Hallucinated Leakage".
*   **EXP08: NER Coverage Audit:**
    *   Benchmark the current NER pipeline (spaCy + Presidio) against a manually annotated golden set of 200 educational documents.
    *   Calculate Precision, Recall, and F1 by domain (CS, Bio, Legal, Med).
*   **GAMA Reproduction (C10):**
    *   Implement a lightweight version of GAMA's `MVPI` (Multi-View Privacy Identification) and run 20 educational queries to prove its ~0% recall for domain-specific IP.

### Phase 2: System Enhancements & Scaling (Weeks 2-3)
*   **Corpus Expansion (Data Gen):**
    *   Use a generator LLM to synthesize 1,500 additional queries mirroring the OULAD domain distribution.
    *   Conduct human-in-the-loop validation for 10% of generated queries.
*   **Conservative Routing Fallback (Guardrail):**
    *   Modify `Sovereign Manager` to check NER confidence scores.
    *   Implement Logic: `if confidence < threshold: zone = 0 (BLOCK_CLOUD_ACCESS)`.
*   **EXP10: DP Benchmarking:**
    *   Integrate a standard Differential Privacy library (e.g., `Opacus` or a text-DP wrapper) as a baseline comparison for utility vs. privacy trade-offs.

### Phase 3: Adversarial Power Study (Weeks 3-4)
*   **EXP06: ARR at Scale:**
    *   Develop an "Adversarial Reconstruction Agent" using Gemini 1.5 Pro.
    *   Prompt the agent to reconstruct entities from sanitized strings across 1, 3, and 10 conversational turns.
    *   Generate the **ARR Degradation Curve**.
*   **EXP07 & EXP09: SOTA Comparison:**
    *   Wrapper implementation for Preempt (token-format focus).
    *   Side-by-side benchmarking on the full 2,000-query corpus.

### Phase 4: Red Team Expansion (Week 4)
*   **EXP11: Categorized Red Teaming:**
    *   Develop 200 prompts across 5 categories: Direct Extraction, Roleplay/Jailbreak, CoT Leakage, Multi-turn Inference, and System Prompt Injection.
    *   Run 3 trials per prompt to establish 95% Confidence Intervals (CIs).

---

## 4. Completed Adjustments (Phase 1-4 Setup)

All required scripts and architecture tweaks have been completed and stored in the `paper-improvement` branch.

### **Core Systems Updates:**
*   **Conservative Routing (Guardrail):** Modified `guard.py` and `guardrail_tools.py` to accept `ner_confidence`. If confidence drops below `0.85`, it enforces **Zone 0 (Local-only)** routing.
*   **Privacy Waterfall Table (C8.2):** Updated `dashboard/sovereign_dashboard.py` to include the exact `Δ` metric table detailing exposure differences "Before" and "After" each agent stage.

### **Experiment Scripts Created:**
*   `experiments/exp12_nelr_scan.py`: Post-hoc cloud hallucination leakage analysis.
*   `experiments/exp08_ner_audit.py`: Benchmark coverage mapping using existing ground truths.
*   `experiments/exp09_gama_mvpi_demo.py`: Demo to definitively prove that GAMA's token-based approach fails to catch educational domain IP.
*   `scripts/generate_corpus.py`: Generates synthetic multi-domain conversational sets to hit the 2,000 query scale requirements.
*   `experiments/exp10_dp_benchmarking.py`: Pareto plotting script to map Utility vs. Privacy tradeoffs (DP vs. Semantic Generalizer).
*   `experiments/exp06_arr_at_scale.py`: Scaled simulation of Adversarial Reconstruction Resistance up to 10 context turns.
*   `experiments/exp07_09_sota_comparison.py`: Base comparison tables targeting Preempt, PP-TS, and GAMA.
*   `experiments/exp11_red_team.yaml`: Complete mapping of Promptfoo configurations focusing on 5 distinct LLM attack categories tailored for hybrid local/cloud separations.
*   `tests/test_conservative_routing_fallback.py`: Automated testing suite asserting that routing fails safely into local zones.

---

## 5. Next Steps for Developer

1.  **Run Pipeline Benchmarks:** Execute `python -m pytest` on the `tests/` directory to ensure system stability.
2.  **Generate Expanded Corpus:** Execute `python scripts/generate_corpus.py` locally to build up the `expanded_corpus_2000.json`.
3.  **Execute Phase 1 Scripts:** Start by running `exp12_nelr_scan.py` and `exp09_gama_mvpi_demo.py` and reviewing the console metric outputs.
4.  **Finalize Results:** Format findings directly into LaTeX tables for the upcoming publication submission.
