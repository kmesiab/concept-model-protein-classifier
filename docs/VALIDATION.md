# Validation Guide

## Overview

This document describes the rigorous validation experiments added to the protein folding classifier to ensure the concept model captures true biophysical principles rather than dataset-specific artifacts.

## Motivation

The original model achieved ~85% accuracy on PDB vs DisProt test sets. However, this could be due to:
- Dataset-specific biases (organism distributions, sequence length, etc.)
- Sequence homology leakage between train/test sets
- Features capturing superficial artifacts rather than folding propensity

To prove the concept model works, we need independent validation beyond the original train/test split.

## Validation Experiments

### 1. MobiDB Independent Test Set

**Function:** `load_mobidb_consensus(limit=1000, output_file="mobidb_test.fasta")`

**Purpose:** Provides an independent validation dataset from a different source than the training data.

**Description:**
- MobiDB aggregates disorder predictions from multiple tools AND has experimental annotations
- Fetches both highly ordered proteins (≤10% disorder) and highly disordered proteins (≥70% disorder)
- Uses MobiDB API with rate limiting to respect server resources
- Saves sequences to FASTA file for reproducibility

**Usage:**
```python
# Fetch MobiDB data
mobidb_data = load_mobidb_consensus(limit=100)

# The function returns a list of (sequence, label) tuples
# label = 0 for disordered, 1 for ordered
```

**Expected Result:**
- If the model generalizes well: **>70% accuracy**
- Poor performance (<60%) suggests PDB/DisProt-specific biases

### 2. Homology-Aware Cross-Validation

**Function:** `homology_aware_split(sequences, labels, test_size=0.2, identity_threshold=0.3, random_state=42)`

**Purpose:** Prevents sequence homology leakage by ensuring similar sequences stay together in train or test set.

**Description:**
- Uses MMseqs2 for fast sequence clustering at 30% identity threshold
- Clusters similar sequences together
- Splits entire clusters (not individual sequences) between train/test
- Maintains stratification by label (folded vs disordered)
- Falls back to random split if MMseqs2 is unavailable

**Usage:**
```python
# Perform homology-aware split
sequences = [item['sequence'] for item in all_sequences_data]
labels = [item['label'] for item in all_sequences_data]

train_indices, test_indices = homology_aware_split(
    sequences, 
    labels,
    test_size=0.2,
    identity_threshold=0.3,
    random_state=42
)

# Use indices to split your data
X_train = df.iloc[train_indices]
X_test = df.iloc[test_indices]
```

**Expected Result:**
- If the model learns generalizable patterns: **>75% accuracy**
- Large drop (>15%) suggests model was memorizing via sequence similarity

### 3. Label-Shuffle Control Experiment

**Function:** `run_label_shuffle_control(sequences_data, n_iterations=5, random_state=42)`

**Purpose:** Tests for data leakage and overfitting by randomizing labels.

**Description:**
- Randomly permutes the labels while keeping sequences intact
- Runs entire classification pipeline with shuffled labels
- Repeats multiple times and averages results
- With random labels, any pattern detection is spurious

**Usage:**
```python
# Run control experiment
shuffle_results = run_label_shuffle_control(
    all_sequences_data, 
    n_iterations=5
)

print(f"Shuffled label accuracy: {shuffle_results['accuracy']:.4f}")
```

**Expected Result:**
- Should drop to **~50% accuracy** (random chance)
- High accuracy (>60%) with shuffled labels indicates:
  - Data leakage
  - Features capturing dataset artifacts
  - Overfitting

**Interpretation:**
- ✓ PASS: Accuracy < 60%
- ✗ FAIL: Accuracy ≥ 60%

### 4. Statistical Significance Testing

**Functions:**
- `bootstrap_confidence_interval(y_true, y_pred, n_bootstrap=1000, confidence_level=0.95)`
- `mcnemar_test(y_true, predictions1, predictions2)`
- `compute_statistical_significance(predictions1, predictions2, labels, ...)`

**Purpose:** Quantifies uncertainty and tests if differences between methods are statistically significant.

**Description:**

**Bootstrap Confidence Intervals:**
- Resamples data with replacement 1000 times
- Calculates accuracy for each bootstrap sample
- Reports 95% confidence interval for accuracy

**McNemar's Test:**
- Compares two classifiers on the same test set
- Tests if differences are statistically significant
- p < 0.05 indicates significant difference

**Usage:**
```python
# Bootstrap CI for a single method
ci = bootstrap_confidence_interval(y_test, predictions, n_bootstrap=1000)
print(f"Accuracy: {ci['mean']:.4f} [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}]")

# Compare two methods
stats = compute_statistical_significance(
    predictions_original,
    predictions_homology_aware,
    y_test,
    method1_name="Original Split",
    method2_name="Homology-Aware Split",
    n_bootstrap=1000
)
```

**Expected Results:**
- Narrow confidence intervals indicate stable performance
- Wide intervals suggest high variance
- p < 0.05 in McNemar's test shows methods differ significantly

### 5. Comprehensive Performance Comparison

**Function:** `run_all_validation_experiments()`

**Purpose:** Runs all validation experiments and creates a comparison table.

**Description:**
- Executes all four validation experiments
- Computes metrics for each: accuracy, precision, recall, F1-score
- Creates formatted comparison table
- Includes statistical significance tests

**Usage:**
```python
# Run all experiments
comparison_results = run_all_validation_experiments()

# Display results table
print(comparison_results.to_markdown(index=False))
```

**Output Format:**
```
| Dataset                              | Accuracy | Precision | Recall | F1-Score |
|--------------------------------------|----------|-----------|--------|----------|
| Original PDB/DisProt Split           | 0.8547   | 0.8623    | 0.8421 | 0.8521   |
| Homology-Aware Split (30% identity)  | 0.7834   | 0.7912    | 0.7723 | 0.7816   |
| Label-Shuffle Control                | 0.4923   | 0.4856    | 0.5012 | 0.4933   |
| MobiDB Independent Test              | 0.7245   | 0.7334    | 0.7123 | 0.7227   |
```

## Interpretation Guidelines

### Model is Production-Ready If:
✓ Homology-aware accuracy > 75%  
✓ MobiDB accuracy > 70%  
✓ Label-shuffle accuracy ~ 50%  
✓ Narrow bootstrap confidence intervals (<0.05 width)  
✓ Statistical tests show expected differences

### Model Needs Refinement If:
⚠ Large accuracy drop in homology-aware split (>15%)  
⚠ Poor MobiDB performance (<60%)  
⚠ Label-shuffle accuracy > 60%  
⚠ Wide bootstrap confidence intervals (>0.10 width)

### Possible Failure Modes:

1. **Dataset-Specific Biases**
   - Symptom: Good on PDB/DisProt, poor on MobiDB
   - Cause: Features capture source database artifacts
   - Solution: Revise features to be more universal

2. **Sequence Homology Leakage**
   - Symptom: Large drop with homology-aware split
   - Cause: Model memorizes via sequence similarity
   - Solution: Already using homology-aware split going forward

3. **Feature Artifacts**
   - Symptom: High accuracy with shuffled labels
   - Cause: Features correlate with dataset origin, not disorder
   - Solution: Investigate feature distributions, revise features

4. **Overfitting**
   - Symptom: High training accuracy, poor on all validation sets
   - Cause: Model too complex for data size
   - Solution: Simplify model or increase training data

## Running the Experiments

### Quick Start

1. Open `protein_classifier.ipynb`
2. Run all cells up to the validation section
3. Uncomment and run individual validation experiments:

```python
# Test MobiDB loader
mobidb_data = load_mobidb_consensus(limit=100)

# Run homology-aware experiment (already integrated)
# Run label-shuffle control
shuffle_results = run_label_shuffle_control(all_sequences_data, n_iterations=5)

# Run comprehensive validation
comparison_results = run_all_validation_experiments()
print(comparison_results.to_markdown(index=False))
```

### Full Validation Pipeline

For comprehensive validation:

```python
# 1. Original split (already done in main notebook)
# Results stored in variables from main analysis

# 2. Run all validation experiments
comparison_results = run_all_validation_experiments()

# 3. Display comparison table
print("\n" + "="*80)
print("PERFORMANCE COMPARISON TABLE")
print("="*80)
print(comparison_results.to_markdown(index=False))

# 4. Interpret results
if comparison_results['Accuracy'].iloc[2] < '0.6000':  # Label shuffle
    print("\n✓ VALIDATION PASSED: Model shows no data leakage")
else:
    print("\n⚠ WARNING: Model may have data leakage issues")
```

## Dependencies

The validation experiments require:
- `numpy` - Numerical operations
- `pandas` - Data manipulation
- `scikit-learn` - ML metrics and splitting
- `scipy` - Statistical tests
- `requests` - MobiDB API calls
- `mmseqs2` (optional) - Sequence clustering
  - Install: `conda install -c bioconda mmseqs2`
  - Fallback to random split if unavailable

## Notes and Caveats

1. **API Rate Limits:** MobiDB loader includes rate limiting (0.2s per request). Fetching 1000 sequences takes ~5-10 minutes.

2. **MMseqs2 Installation:** The homology-aware split tries to install MMseqs2 automatically via conda. If this fails, it falls back to a simple random split.

3. **Computational Cost:** 
   - Label shuffle with 5 iterations: ~2-5 minutes
   - Bootstrap with 1000 samples: ~1-2 minutes
   - MobiDB fetch: ~5-10 minutes for 100 sequences

4. **Reproducibility:** All experiments use `random_state=42` for reproducibility. Results should be identical across runs.

5. **Sample Sizes:** For publication-quality validation:
   - Use at least 500 sequences for MobiDB test
   - Use 10+ iterations for label shuffle
   - Use 1000+ bootstrap samples

## References

1. **MobiDB:** Piovesan et al. (2021) "MobiDB: intrinsically disordered proteins in 2021"
2. **MMseqs2:** Steinegger & Söding (2017) "MMseqs2 enables sensitive protein sequence searching"
3. **Bootstrap Methods:** Efron & Tibshirani (1993) "An Introduction to the Bootstrap"
4. **McNemar's Test:** McNemar (1947) "Note on the sampling error of the difference between correlated proportions"

## Contact

For questions or issues with validation experiments, please open an issue on the GitHub repository.
