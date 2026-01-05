# Concept Model Architecture

## Explanation of the Protein Folding Prediction Script

This Python script is designed to classify protein sequences as either "Folded" (typically from PDB) or "Disordered" (typically from DisProt). It does this by:

1. Defining a set of biophysical and compositional features for amino acid sequences.
2. Implementing and evaluating two main rule-based classification approaches.
3. Using a proper training/testing split to ensure fair evaluation of the classifiers.

The script's structure and logic can be mapped to the **Concept Model** framework (M1: Properties, M2: Constraints, M3: Transformations, M4: Goal State).

### Key Components of the Script

1. **Amino Acid Property Definitions (`aa_properties_base`):**
    * The script begins by defining various fundamental physicochemical properties for each of the 20 canonical amino acids (e.g., hydrophobicity, charge, flexibility, propensity for helix/sheet).
    * These base properties are normalized and stored. They are the building blocks for the features used by the classifiers.

2. **Data Loading (`load_fasta_with_labels`):**
    * Protein sequences are loaded from FASTA files (`pdb_chains.fasta` for folded, `disprot_13000.fasta` for disordered).
    * Each sequence is stored along with its true label (1 for PDB/Folded, 0 for DisProt/Disordered) and its raw sequence string.

3. **New 7 Feature Definitions (`compute_new_seven_features`):**
    * A function `compute_new_seven_features` is defined to calculate a specific set of 7 features for any given sequence string (which could be a whole protein or a shorter window/segment). These features are:
        1. `hydro_norm_avg`: Average normalized hydrophobicity.
        2. `flex_norm_avg`: Average normalized flexibility.
        3. `h_bond_potential_avg`: Average H-bonding potential (sum of donors/acceptors).
        4. `abs_net_charge_prop`: Absolute proportion of net charge.
        5. `shannon_entropy`: A measure of sequence complexity.
        6. `freq_proline`: Frequency of Proline.
        7. `freq_bulky_hydrophobics`: Combined frequency of W, C, F, Y, I, V, L.
    * **Concept Model M1 (Property Vectors / Tensor Snapshots):** This set of 7 features calculated for a protein (or segment) constitutes its M1 representation – a vector of its key properties.

4. **Main Feature Computation (`compute_features_for_dataset`):**
    * This function processes a list of raw sequences.
    * It can either calculate the 7 new features globally for each entire protein (if `WINDOW_SIZE_BASELINE` is `None`) or calculate them for sliding windows and then average these window features to get 7 global values for the protein. For the "New Global Features Classifier" part, it's set to compute direct global features.

5. **Train/Test Split:**
    * The full dataset (with globally computed new features and labels) is split into a training set (80%) and a testing set (20%). This is crucial for an unbiased evaluation of how well the classifiers generalize to unseen data.
    * Raw sequences corresponding to the test set are kept aside for the sliding window classifier.

6. **Midpoint Calculation (from Training Data's Global Features):**
    * From the **training set's global features**, the script calculates the average value of each of the 7 new features for PDB proteins and for DisProt proteins.
    * The `midpoints` are then calculated as the halfway point between these PDB and DisProt averages for each feature.
    * **Concept Model M2 (Constraints):** These empirically derived `midpoints` define the thresholds for the classification rules. A condition like `feature_value >= midpoint` (or `<= midpoint`, depending on the feature) acts as a constraint. A protein/segment feature vector is tested against these constraints.

7. **Defining "Conditions Met" (`count_conditions_for_new_feature_vector`):**
    * This helper function takes a 7-feature vector (for a protein or a segment) and the `midpoints`.
    * It checks, for each of the 7 features, whether it falls on the "PDB-like" side of its respective midpoint (e.g., higher hydrophobicity, lower proline frequency). The direction of comparison (`>=` or `<=`) is determined by observing the means of PDB vs. DisProt proteins in the training data.
    * It returns the total number of conditions (out of 7) that were met.

### Classifier 1: Baseline Threshold-Based Classifier (New Global Features)

* **Logic:**
    1. The 7 new global features are calculated for each protein in the test set.
    2. For each test protein, `count_conditions_for_new_feature_vector` determines how many of its 7 global features satisfy the midpoint-derived conditions. This result is stored as `conditions_met`.
    3. The script then evaluates performance by trying different thresholds `k` (from 1 to 7). A protein is predicted as "Folded" if its `conditions_met >= k`.
* **Relation to Concept Model:**
  * **M1:** The 7 new global features of an entire protein.
  * **M2:** The set of 7 conditions derived from `midpoints`.
  * **M3 (Transformation/Rule):** The process of (a) counting how many conditions are met by M1, and (b) comparing this count to a threshold `k`.
  * **M4 (Goal State):** The true labels (Folded/Disordered). The script finds the `k` that yields the best F1-score for PDB proteins, effectively optimizing this simple M3 rule against M4.

### Classifier 2: Sliding Window (Larger - 9 AA) Classifier with Failure Cancellation

* **Logic:** This classifier processes each raw protein sequence in the test set with a more complex, stateful rule:
    1. **Parameters:**
        * `SLIDING_WINDOW_SIZE = 9` (each local window to analyze).
        * `SLIDING_WINDOW_SLIDE_STEP = 9` (non-overlapping windows).
        * `SLIDING_WINDOW_PASS_K = 5` (a 9-AA window "passes" if its 7 *local* features meet at least 5 conditions, judged by the *globally-derived `midpoints`*).
        * `MAX_UNFORGIVEN_FAILED_WINDOWS_SLIDING = 3` (the protein is "Folded" if it has 3 or fewer uncancelled failed windows).
    2. **Serial Processing:** It slides a 9-AA window across the sequence.
    3. **Window Evaluation:** For each 9-AA window, its 7 new features are calculated. `count_conditions_for_new_feature_vector` determines if this window "passes" or "fails" based on `SLIDING_WINDOW_PASS_K` and the global `midpoints`.
    4. **Failure Cancellation:** A running count of `current_consecutive_failures_streak` is maintained. If a window "passes," this streak is reset to 0 (any failures in that streak are "cancelled"). If a window "fails," the streak count increases.
    5. **Protein Classification:** After all windows are processed, the `total_unforgiven_failures` is simply the value of `current_consecutive_failures_streak` at the end of the sequence (as any streaks terminated by a pass were reset). The protein is predicted "Folded" if `total_unforgiven_failures <= MAX_UNFORGIVEN_FAILED_WINDOWS_SLIDING`.
* **Relation to Concept Model:**
  * **M1 (local):** The 7 new features calculated for each 9-AA window.
  * **M2 (local):** The conditions a window must meet (based on global `midpoints` and `SLIDING_WINDOW_PASS_K`) to "pass."
  * **M3 (Transformation/Rule):** This is a more complex M3. It involves:
    * The serial processing of windows.
    * The evaluation of each window against local M2.
    * The stateful tracking of `current_consecutive_failures_streak`.
    * The "failure cancellation" logic.
    * The final decision rule based on `total_unforgiven_failures` and `MAX_UNFORGIVEN_FAILED_WINDOWS_SLIDING`.
  * **M4 (Goal State):** The true labels (Folded/Disordered) that this entire M3 rule system is trying to predict.

### Summary

The script first establishes a baseline performance using a threshold classifier on 7 new global features. It then tests a more intricate, serial window-based classifier with a failure cancellation mechanism, using the same underlying feature definitions (calculated locally) and the same globally-derived midpoints for local window evaluation. The results then show how these different approaches (different M1 aggregations and different M3 rules) perform at predicting the M4 goal state.
