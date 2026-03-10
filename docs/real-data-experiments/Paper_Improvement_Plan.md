# Paper Improvement Plan
**Paper:** Semantic Generalization: Privacy-Preserving Inference-Time Query Sanitization for Agentic Educational AI
**Reviewer:** paperreview.ai (Stanford ML Group)
**Review Date:** March 10, 2026
**Submission Deadline:** March 30, 2026 — **20 days remaining**

---

## Executive Summary

The reviewer recommends **revision, not rejection**. The core idea is accepted as novel and practically motivated. The path to acceptance has four clear pillars:

1. Stronger privacy metrics (semantic/attribute leakage, not just exact-match)
2. Full adversarial evaluation (EXP06, n=1,402 — already planned)
3. Fairer baseline comparison (equip baselines with the same educational-IP taxonomy)
4. Algorithmic formalization (Shadow Lexicon, generalization algorithm, OULAD query construction)

Items 2 and 4 are already in progress or addressable with prose additions. Items 1 and 3 require targeted new experiments. The plan below triages by deadline feasibility and impact.

---

## Priority Triage

| Priority | Issue | Deadline Feasible? | Effort |
|---|---|---|---|
| 🔴 P0 | Complete EXP06 full AttaQ run (n=1,402) | ✅ Yes | Low — script ready |
| 🔴 P0 | Formalize semantic generalization algorithm | ✅ Yes | Medium — writing only |
| 🔴 P0 | Clarify OULAD query construction and sanitized-cloud pipeline | ✅ Yes | Low — writing only |
| 🔴 P0 | Reconcile 99.8% (RQ1) vs ~96% (RQ3) IP protection discrepancy | ✅ Yes | Low — writing only |
| 🟠 P1 | Add semantic/attribute leakage metric to EXP01 | ✅ Yes | Medium — new eval |
| 🟠 P1 | Augmented baseline experiment (baselines + educational-IP lexicon) | ⚠️ Tight | High — new experiment |
| 🟡 P2 | Add IslandRun/MIST and KBA to related work | ✅ Yes | Low — writing only |
| 🟡 P2 | LLM-judge reliability note / human correlation | ⚠️ Tight | Medium |
| 🟢 P3 | Multi-turn evaluation (Crescendo-style) | ❌ Post-submission | High |
| 🟢 P3 | Formal DP at semantic layer | ❌ Future work | Very High |

---

## Issue-by-Issue Action Plan

---

### ISSUE 1 — Privacy Metrics Undercount Semantic Leakage
**Reviewer quote:** *"Privacy metrics (exact-string match and coarse 'Field Exposure') are insufficient to capture semantic/attribute leakage; paraphrase- and inference-based leakage can pass undetected."*

**The problem:** A query generalized from "Student 629654 from South Region with IMD band 30–40%" to "a student from a mid-deprivation-index region" still reveals socioeconomic category. Exact-match IP Protection Rate misses this.

**Actions:**

**A1. Add a Semantic Leakage metric to EXP01**
- Compute **STS between original sensitive field values and generalized placeholders** (not between answers). If STS(original entity, placeholder) > threshold, flag as semantic leakage.
- Example: STS("South Region", "mid-deprivation-index region") — if high, leakage is present.
- Use the same all-MiniLM-L6-v2 model already in the pipeline.
- Add a "Semantic Leakage Rate" column to Table IV (EXP01).

**A2. Add a prose acknowledgment to Section V-B (Discussion)**
- Explicitly state that exact-match IP Protection Rate is a lower bound on leakage.
- Acknowledge that type-preserving generalization, by design, preserves category-level information (socioeconomic band → deprivation index). This is intentional — it allows cloud LLM utility — not a flaw.
- Frame it as a privacy-utility frontier: the system operates at a different point on the frontier than full redaction, not a worse point.

**LaTeX target:** Table IV + Section V-B paragraph addition (~80 words).

---

### ISSUE 2 — Adversarial Evaluation Too Small (n=5)
**Reviewer quote:** *"Small-scale adversarial evaluation (n=5 AttaQ; full run pending) limits generalizability."*

**This is already the #1 pre-submission task. Nothing to plan — execute.**

**Actions:**

**A3. Run EXP06 full AttaQ evaluation (n=1,402)**
```bash
cd /Users/madus/sovereign_system
source .venv/bin/activate
python experiments/exp06_red_teaming/exp06_attaq_runner.py
```
- Replace Table VII smoke-test figures with full-run results
- Update Architecture Attribution figure in Abstract, Introduction, and Table VII
- If Architecture Attribution changes significantly from 80%, update the framing in Section III-C

**A4. Strengthen attribution methodology prose in Section IV-F**
- Explain how Architecture Attribution is measured: for each blocked query, log WHICH guardrail layer triggered the block (Input Validator, Zone Validator, etc.)
- A block attributed to architecture = triggered at Layer 1–5 before LLM is called
- A block attributed to base model = passed all guardrail layers, blocked by LLM refusal
- This addresses the reviewer's "requires stronger attribution methodology" concern

---

### ISSUE 3 — Baseline Comparison Biased by Taxonomy Advantage
**Reviewer quote:** *"A fairer test would extend baselines with the same educational-IP lexicon or evaluate the proposed architectural mechanisms independently of taxonomy."*

**This is the hardest reviewer concern to fully address before March 30. Two strategies:**

**Strategy A (preferred — lower effort):** Run a **taxonomy-equalized baseline experiment**
- Take the best-performing baseline (PP-TS, Field Exposure 0.15) and plug in the Shadow Lexicon as its entity detector
- Measure IP Protection and Field Exposure with the augmented detector
- If PP-TS + Shadow Lexicon still underperforms Sovereign Learner on Field Exposure → proves architectural advantage beyond taxonomy
- Add as a row in Table VI: "PP-TS + SL Lexicon" and brief prose note

**Strategy B (fallback — writing only):** Acknowledge the limitation explicitly and reframe
- Add a paragraph to Section IV-E (RQ5): "To isolate taxonomy advantage from architectural advantage, future work should equip all baselines with the same educational-IP entity set. The current comparison measures the full-system advantage including domain adaptation."
- This is honest, not defensive, and directly anticipates the concern

**Recommendation:** Attempt Strategy A. If the experiment runs in under 2 days, include it. If not, use Strategy B. Either satisfies the reviewer — they accept acknowledgment for a revision.

**Actions:**

**A5. Taxonomy-equalized baseline experiment (Strategy A)**
- Plug Shadow Lexicon into PP-TS detection layer
- Run on same n=50 OULAD queries as EXP05
- Add result row to Table VI
- Add 2-sentence prose note in Section IV-E

**A6. Fallback prose if A5 is not feasible (Strategy B)**
- Add limitation paragraph to Section IV-E (~60 words)

---

### ISSUE 4 — Semantic Generalization Under-Specified
**Reviewer quote:** *"The core primitive—semantic generalization—is described conceptually but not formalized sufficiently for reproducibility or analysis."*
**Author Question 1:** *"Please provide a formal description or algorithm: input representation, detection rules, ontology/types, transformation constraints."*

**Actions:**

**A7. Add Algorithm box to Section III-B**

Add a LaTeX `\begin{algorithm}` block after the pipeline prose:

```
Algorithm 1: Semantic Generalization (Stage 3)
Input:  Query q, Shadow Lexicon L, Entity type ontology T
Output: Generalized query q', Mapping table M

1. E ← Presidio.detect(q) ∪ ShadowLexicon.detect(q, L)
2. for each entity e_i ∈ E:
3.     t_i ← T.classify(e_i)           // type: {student_id, region, imd_band, module_code, ...}
4.     p_i ← T.placeholder(t_i)        // type-preserving placeholder
5.     M[p_i] ← e_i                    // store mapping locally
6.     q ← q.replace(e_i, p_i)
7. Validate: LLM.check_reasoning_structure(q) ≥ θ_utility
8. If validation fails: raise ZoneDowngrade → Zone 0
9. return q as q', M
```

This directly answers Author Question 1 and makes the system reproducible.

**A8. Add Shadow Lexicon description to Section III-B**
- State the lexicon size (number of entity types, number of seed terms)
- State the construction method: manually seeded from OULAD field names + VLE activity taxonomy + FERPA-sensitive fields
- State the update policy: lexicon is versioned; coverage measured by recall on OULAD ground-truth entities
- ~80 words in prose form, no new table needed

---

### ISSUE 5 — OULAD Query Construction Under-Specified
**Reviewer quote / Author Question 3:** *"How were the 300 real queries constructed from OULAD (a tabular dataset)? Are templates used? Are queries and ground-truth sensitive fields released?"*

**Actions:**

**A9. Add query construction paragraph to Section IV-A (Experimental Setup)**

Draft addition (~100 words):
> OULAD-derived queries are constructed via structured templates that embed real student field values from OULAD as natural language. Each template follows one of three forms: (i) support-seeking ("Student [ID] from [Region] with [IMD\_band] is struggling with [module\_code]..."), (ii) performance-inquiry ("How should I interpret [assessment\_score] for [module\_code] given [VLE\_clicks] interactions?"), and (iii) institutional-context ("Advise on [disability] accommodations for [region] students"). Ground-truth sensitive entities are the original OULAD field values substituted into each template. Queries and ground-truth annotations are released at [GitHub repo] for reproducibility.

**A10. Ensure GitHub repo includes the query set before submission**
- Commit the 100 OULAD-derived queries + ground truth annotations to `data/oulad_queries/` in the sovereign-learner repo

---

### ISSUE 6 — IP Protection Rate Discrepancy (99.8% vs ~96%)
**Reviewer quote / Author Question 4:** *"Reconcile the discrepancy between 99.8% IP protection (RQ1) and ≈96% in RQ3."*

**This is a legitimate question with a simple answer — write it clearly.**

**Actions:**

**A11. Add a clarifying sentence to Section IV-H (Model Agnosticism)**

> The 99.8% IP protection rate in EXP01 (Table IV) is measured on the primary Llama~3.2 backend on the full 300-query set (200 AI4Privacy + 100 OULAD). EXP03's ≈96% rates reflect per-model evaluation on the OULAD-only subset (n=100), where educational-domain entities are inherently harder to generalize than AI4Privacy PII tokens. The two experiments measure the same system under different data conditions, not different measurement criteria.

This is a 3-sentence addition that closes the question entirely.

---

### ISSUE 7 — LLM-Judge Reliability (3B Model)
**Reviewer quote:** *"The LLM-judge relies on a small local model (3B), raising concerns about judging reliability."*

**This is fair but not fatal. The judge is for usefulness assessment, not privacy measurement.**

**Actions:**

**A12. Add LLM-Judge reliability note to Section IV-A**
- State that llama3.2 (3B) is used as LLM-Judge for its on-device constraint
- Acknowledge the reliability limitation relative to larger judges
- Note: the STS metric provides an independent utility signal that does not depend on the judge; both are reported and neither is suppressed
- If time permits: run 20-query human correlation study (Pearson r between Judge scores and 3-point human usefulness ratings). Even n=20 gives a correlation estimate.

**A13. Optional: Add human correlation footnote**
- If A12 experiment runs: add footnote to Table IV: "LLM-Judge achieves r=X correlation with human usefulness ratings on n=20 sampled queries (p<0.05)."

---

### ISSUE 8 — Missing Related Work: IslandRun/MIST and KBA
**Reviewer quote:** *"Limited engagement with IslandRun's MIST component... KBA orchestration with privacy-preserving probes."*

**Actions:**

**A14. Add 2–3 sentences to Section II-B (Semantic-Level Methods)**

> Recent routing-based approaches offer complementary perspectives. IslandRun's MIST component performs typed placeholder replacement with a local reversible mapping, sharing structural goals with semantic generalization; the key distinction is that MIST targets named PII in general-purpose chatbot contexts, while Stage~3 operates on educational-domain IP with an ontology-aware type hierarchy. KBA-style knowledge-preserving probes during routing~\cite{kba_ref} aim to reduce misrouting leakage; the AZA fail-closed principle achieves similar conservative routing without requiring cloud knowledge probing.

**Note:** Search for the correct citations for IslandRun/MIST and KBA before adding. If citations cannot be confirmed, frame as "recent work" without citation keys.

---

### ISSUE 9 — Zone Classification Accuracy (100% on n=80 Needs Larger Validation)
**Reviewer quote:** *"100% zone classification accuracy on 80 labeled prompts using a 3B model is unusually high and needs larger-scale validation and inter-annotator agreement."*

**This is a reasonable skepticism that we cannot fully resolve before March 30. Respond strategically.**

**Actions:**

**A15. Add inter-annotator agreement note to Section IV-D**
- State that the 80 ground-truth zone labels were derived from OULAD field values using a deterministic labeling rule (presence of student PII fields → Zone 1; institutional references → Zone 2; etc.)
- This means labels are rule-derived, not human-annotated — inter-annotator agreement is not applicable in the traditional sense
- Acknowledge that larger-scale validation (n > 500) is planned as future work
- This reframes the 100% not as "suspiciously perfect" but as "expected given deterministic ground truth derivation"

---

### ISSUE 10 — Multi-Turn Evaluation
**Reviewer quote:** *"Do you have multi-turn evaluations showing cross-turn leakage accumulation?"*

**This is a post-March-30 item. Do not attempt before submission.**

**Actions:**

**A16. Strengthen future work framing in Section V-C**
- Reference Crescendo [15] more precisely: state the specific attack class (incremental multi-turn intent escalation) and why it applies to the educational setting
- Add: "A session-aware generalization strategy that tracks per-session information budget — analogous to PRV composition in the training-data setting — is the primary extension planned for the next phase of this work."
- This signals to reviewers that we understand the problem deeply even without having solved it

---

## Revision Checklist (Ordered by Execution Sequence)

### Week 1 (March 10–17): Experiments
- [ ] **A3** — Run EXP06 full AttaQ run (n=1,402). Update Table VII, Abstract, Introduction.
- [ ] **A5** — Run taxonomy-equalized baseline (PP-TS + Shadow Lexicon). Add row to Table VI.
- [ ] **A1** — Compute Semantic Leakage Rate for EXP01. Add column to Table IV.
- [ ] **A13** — Optional: 20-query human correlation for LLM-Judge. Add footnote.
- [ ] **A10** — Commit OULAD query set + ground truth to GitHub repo.

### Week 2 (March 17–24): Writing
- [ ] **A7** — Add Algorithm 1 (Semantic Generalization) to Section III-B.
- [ ] **A8** — Add Shadow Lexicon description to Section III-B (~80 words).
- [ ] **A9** — Add OULAD query construction paragraph to Section IV-A.
- [ ] **A11** — Add IP protection discrepancy clarification to Section IV-H (3 sentences).
- [ ] **A12** — Add LLM-Judge reliability note to Section IV-A.
- [ ] **A14** — Add IslandRun/MIST + KBA to Section II-B (2–3 sentences).
- [ ] **A15** — Add inter-annotator note to Section IV-D.
- [ ] **A16** — Strengthen multi-turn future work in Section V-C.
- [ ] **A2** — Add semantic leakage acknowledgment to Section V-B.
- [ ] **A6** — Add taxonomy-equalization limitation note to Section IV-E (if A5 not complete).

### Week 3 (March 24–30): Assembly and Compliance
- [ ] Re-check 6-page limit after all additions (algorithm box + new metric columns add ~0.4 pages)
- [ ] If over 6 pages: trim Section I-D (Contributions) bullet list by 30%, trim Section V-C by 1 paragraph
- [ ] Verify all new citations have confirmed arXiv IDs before adding to `references.bib`
- [ ] Recompile PDF, verify IEEE Xplore compatibility
- [ ] Confirm GitHub repo is public and query dataset is committed
- [ ] Submit via https://confcomm.ieee-ies.org/app/general/conferences/IRAI26/initial-submission

---

## Reviewer Concerns That Are Refutable (No New Experiments Needed)

These reviewer concerns have good answers in the existing work — they just need to be written clearly:

| Concern | Response |
|---|---|
| 99.8% vs 96% discrepancy | Different datasets (full 300 vs OULAD-100). Write A11. |
| 100% zone accuracy "unusually high" | Ground truth is rule-derived from OULAD fields, not human-annotated. Write A15. |
| "IP" confusion with internet protocol | Add footnote at first use: "IP = Intellectual Property throughout this paper." |
| STS scores are low (0.342) | Already addressed in Section V-A. Strengthen with one sentence: this is expected and intentional. |
| LLM-Judge is a 3B model | Already dual-reported with STS. Write A12 to close explicitly. |

---

## Reviewer Concerns That Require Honest Acknowledgment (Not Resolvable by March 30)

| Concern | Response |
|---|---|
| No formal privacy guarantee | Already acknowledged in Section V-B. Strengthen with A16's PRV composition framing. |
| Multi-turn leakage evaluation | Future work. Strengthen Section V-C framing (A16). |
| Mapping table M security (encryption at rest) | Add 1-sentence note: "M is stored in local ChromaDB with application-level access control; hardware-level encryption (e.g., secure enclaves) is a deployment-layer concern outside the scope of this work." |
| Full formal threat model | Partially addressed by SovereignGuard description. Add brief threat model paragraph to Section III-C opening: state the assumed adversary (honest-but-curious cloud provider with domain knowledge; active adversarial prompts modeled by AttaQ). |

---

## Word Budget Impact

| Addition | Estimated words | Section |
|---|---|---|
| Algorithm 1 box | ~100 | III-B |
| Shadow Lexicon description | ~80 | III-B |
| OULAD query construction | ~100 | IV-A |
| Semantic Leakage metric note | ~60 | IV-A + Table IV |
| IP discrepancy clarification | ~60 | IV-H |
| LLM-Judge note | ~50 | IV-A |
| Taxonomy fairness note | ~60 | IV-E |
| IslandRun/MIST + KBA | ~80 | II-B |
| Inter-annotator note | ~50 | IV-D |
| Multi-turn future work | ~60 | V-C |
| **Total additions** | **~700 words** | |

At ~500 words/column-page in IEEE two-column format, 700 words ≈ **1.4 additional column-pages**. The current draft is already targeting 6 pages. This means **significant trimming is required in parallel** with additions.

**Recommended cuts (to recover ~1.4 pages):**
- Section I-D: Shorten 7-item bullet list to 4-item numbered list (save ~0.3 pages)
- Section IV (EXP02) prose: condense EXP02a/b/c narrative by 30% — the table already carries the numbers (save ~0.3 pages)
- Section I-A/I-B: Merge into one subsection, cut 2 paragraphs (save ~0.3 pages)
- Section V-A (STS vs Judge): Cut last 2 sentences, already self-evident (save ~0.1 pages)
- Algorithm 1 replaces the pipeline prose list, net +0 pages if prose list is removed

---

*Plan prepared: March 10, 2026 | Next review: March 17, 2026 (post-Week-1 experiments)*
