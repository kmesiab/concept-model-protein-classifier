# Concept Model Experiment – Protein Folding Predictions

https://kevinmesiab.substack.com/p/emergent-concept-modeling-a-paradigm

This repository contains a Jupyter notebook experiment that explores the prediction of protein folding states (Folded vs. Disordered) using a rule-based classification framework inspired by the Concept Model (4-Layer Matrix). The analysis investigates the biophysical and compositional constraints that distinguish folded protein domains (typically from PDB) from intrinsically disordered proteins (from DisProt), and tests how well these constraints can be used for automated prediction.

## Overview

The notebook implements and evaluates two main approaches:

1. **Global Feature Classifier:**  
   - Extracts 7 biophysical/compositional features from full protein sequences.
   - Calculates empirical thresholds (midpoints) between folded and disordered training data for each feature.
   - Classifies test proteins by counting how many features meet the “folded” condition, optimizing the count for best F1-score.
2. **Sliding Window Classifier with Failure Cancellation:**  
   - Extracts the same 7 features in sliding 9-amino-acid windows along each sequence.
   - Applies a stateful rule: a protein is "Folded" if it has at most 3 uncancelled “failed” windows, where a window “fails” if fewer than 4 features meet the folded condition.

Both approaches are mapped to the Concept Model framework:
- **M1:** Property vectors for amino acids or sequence segments.
- **M2:** Empirically-derived constraints (feature thresholds).
- **M3:** Rules for counting and aggregating satisfied conditions.
- **M4:** Goal state (true labels: Folded or Disordered).

## Data Sources

- **Folded proteins:** Downloaded from the Protein Data Bank (PDB), 15,000 chains in FASTA.
- **Disordered proteins:** Downloaded from DisProt, 25,000 sequences in FASTA.

## Feature Definitions

For each sequence or segment, the following features are computed:
1. Average normalized hydrophobicity
2. Average normalized flexibility
3. Average hydrogen bond potential
4. Absolute net charge proportion
5. Sequence Shannon entropy
6. Frequency of proline
7. Frequency of bulky hydrophobics (W, C, F, Y, I, V, L)

## Results

- The best global classifier achieves ~85% accuracy and F1-score for folded proteins, using a simple count of satisfied feature constraints.
- The sliding window approach is more stringent and provides a different trade-off between precision and recall, revealing the limits of rule-based classification for this task.

See the notebook for detailed metrics, confusion matrices, and code for reproducing the analysis.

## Running the Experiment

1. Install dependencies (`numpy`, `pandas`, `scikit-learn`, `requests`).
2. Download the notebook and run all cells. The scripts will download required protein FASTA files and compute all features and results.

## Reference

If you use this code or approach, please credit this repository and cite the relevant Concept Model literature.

---
