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
*   **EXP08A: NER Coverage Audit:**
    *   Benchmark the current NER pipeline (spaCy + Presidio) against a manually annotated golden set of 200 educational documents.
    *   Calculate Precision, Recall, and F1 by domain (CS, Bio, Legal, Med).
*   **GAMA Reproduction (C10):**
    *   Implement a lightweight version of GAMA's `MVPI` (Multi-View Privacy Identification) and run 20 educational queries to prove its ~0% recall for domain-specific IP.

### Phase 2: System Enhancements & Scaling (Weeks 2-3)
*   **EXP11A: Corpus Expansion:**
    *   Use a generator LLM to synthesize 1,500 additional queries mirroring the OULAD domain distribution.
    *   Conduct human-in-the-loop validation for 10% of generated queries.
*   **EXP08B: Conservative Routing Fallback:**
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
*   **EXP11B: Categorized Red Teaming:**
    *   Develop 200 prompts across 5 categories: Direct Extraction, Roleplay/Jailbreak, CoT Leakage, Multi-turn Inference, and System Prompt Injection.
    *   Run 3 trials per prompt to establish 95% Confidence Intervals (CIs).

---

## 4. Next Steps for Developer

1.  **Do not modify the core `src/` logic yet**; focus on creating the `experiments/` scripts.
2.  Initialize `scripts/generate_corpus.py` to start the expansion to 2,000 queries.
3.  Create `results/metrics_v4_baseline.json` to store current performance before improvements.
4.  Update the Dashboard to include the **Privacy Waterfall Table** as requested in C8.2.
