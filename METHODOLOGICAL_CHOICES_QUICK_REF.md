# 📋 Quick Reference: Methodological Choices

**TL;DR version of THEORETICAL_JUSTIFICATIONS.md**

---

## Metrics Cheat Sheet

| Metric | When to Use | Why We Used It | Why NOT Alternatives |
|--------|-------------|----------------|---------------------|
| **F1 Score** | Imbalanced classification | Struggle detection (15% struggling) | Accuracy misleading (85% by predicting "not struggling") |
| **MSE** | Regression with normal errors | Assessment score prediction | MAE doesn't penalize large errors enough |
| **R²** | Interpretable regression | Shows "% variance explained" | Provides context MSE lacks |
| **IP Leakage Rate** | Privacy measurement | Entity-based adversarial testing | k-anonymity requires multiple records |
| **Utility Score** | LLM output quality | LLM-as-judge (scalable) | Human eval too expensive |

---

## Algorithms Cheat Sheet

| Algorithm | When to Use | Why We Used It | Why NOT Alternatives |
|-----------|-------------|----------------|---------------------|
| **Random Forest** | Tabular data, need interpretability | Struggle detection, score prediction | XGBoost: +2% accuracy, -90% interpretability |
| **LLM-as-Adversary** | Privacy testing | Realistic threat model | Rule-based misses semantic leakage |
| **LLM-as-Judge** | Quality evaluation | Scalable, nuanced | BLEU/ROUGE measure similarity, not quality |

---

## Design Choices Cheat Sheet

| Choice | What We Did | Why | Alternative |
|--------|-------------|-----|-------------|
| **Train-Test Split** | 80/20 | Standard, sufficient samples | 75/25 (less training data) |
| **Sampling** | Stratified | Maintains 15% struggling in both sets | Random (could create imbalance) |
| **Cross-Validation** | Not used | 32K samples sufficient | 5-fold CV (5× slower, marginal benefit) |
| **Baselines** | 3 baselines | Shows privacy-utility tradeoff | Single baseline (no context) |
| **p-values** | Not reported | Large N makes everything "significant" | Effect sizes more meaningful |

---

## One-Sentence Justifications

### Why F1 Score?
**"Accuracy is 85% by predicting everyone passes, but F1 is 0 because we miss all struggling students."**

### Why Random Forest over XGBoost?
**"XGBoost gives +2% accuracy but requires 20 hyperparameters and loses interpretability—not worth it."**

### Why MSE?
**"Predicting 60 instead of 80 should be 16× worse than predicting 75—MSE's squared penalty captures this."**

### Why LLM-as-Judge?
**"Human evaluation costs $1,000 and takes a week; LLM-as-judge costs $5 and takes an hour with 85% correlation."**

### Why Stratified Sampling?
**"Random split could create 10% struggling in test set when real-world is 15%—stratified ensures representativeness."**

### Why Multiple Baselines?
**"Claiming 95% privacy means nothing without comparing to 0% (no protection) and 100% (full redaction)."**

### Why NOT Deep Learning?
**"3,000 struggling students is too small for neural networks (need 10K+), and educators need interpretable features."**

### Why Adversarial Testing?
**"Normal testing shows 95% protection, but adversarial testing reveals 75% attack success—both are needed."**

---

## Common Questions

### Q: Why not use accuracy for struggle detection?
**A:** With 85% passing, predicting "everyone passes" gives 85% accuracy but helps zero students. F1 Score forces the model to actually detect struggling students.

### Q: Why Random Forest instead of the "best" algorithm?
**A:** 
- XGBoost: +2% accuracy, but complex and uninterpretable
- Neural Network: Needs 10K+ samples, we have 3K
- Random Forest: Good enough (F1=0.78), interpretable, robust

### Q: Why not report p-values?
**A:** With 32,000 students, even a 0.001 difference is "statistically significant" (p<0.05). We care about practical significance: Is +25.8% F1 improvement meaningful? Yes!

### Q: Why LLM-as-judge instead of human evaluation?
**A:** 
- Human: $1,000, 1 week, subjective
- LLM: $5, 1 hour, 85% correlation with humans
- For 1,000 queries: LLM is only viable option

### Q: How do you measure privacy?
**A:** Entity-based adversarial testing:
1. Mask "CRISPR" → "Protocol-Alpha"
2. Give response to adversarial LLM
3. Ask: "Can you guess the original term?"
4. If yes → leaked, if no → protected

### Q: Why 80/20 split instead of cross-validation?
**A:** 
- Dataset: 32,000 students (large enough)
- 80/20: Train once, test once
- 5-fold CV: Train 5 times, test 5 times (5× slower)
- Benefit: Marginal (more robust estimate)
- Cost: 5× computational time
- Decision: Not worth it for this dataset size

---

## Red Flags We Avoided

❌ **Using accuracy for imbalanced data** → Used F1 instead  
❌ **Overfitting with complex models** → Used Random Forest (built-in regularization)  
❌ **Reporting only statistical significance** → Reported effect sizes  
❌ **Single baseline comparison** → Used 3 baselines  
❌ **Only normal testing** → Added adversarial testing (EXP05)  
❌ **Ignoring interpretability** → Chose Random Forest over XGBoost  
❌ **Random train-test split** → Used stratified sampling  

---

## Key Principles

1. **Domain-Driven Metrics:** Choose metrics that matter to stakeholders (educators care about F1, not accuracy)

2. **Pragmatic Algorithms:** "Good enough" + interpretable > "best" + black box

3. **Effect Size > Significance:** With large N, focus on practical impact, not p-values

4. **Multiple Baselines:** Show tradeoffs, not just absolute performance

5. **Adversarial Validation:** Normal testing + red teaming = complete picture

6. **Reproducibility:** Fixed seeds, stratified sampling, documented choices

---

**For full details, see:** `THEORETICAL_JUSTIFICATIONS.md`
