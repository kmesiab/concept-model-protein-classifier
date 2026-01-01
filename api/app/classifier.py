"""
Protein Disorder Classification Module

This module contains the core classification logic for protein disorder prediction.
Extracted from the validated notebook with 84.52% accuracy.
"""

import math
from typing import Dict, List, Optional, Tuple

# Amino Acid Property Scales
# These are the fundamental biophysical properties used for classification

KD_HYDROPHOBICITY = {
    "A": 1.8,
    "R": -4.5,
    "N": -3.5,
    "D": -3.5,
    "C": 2.5,
    "Q": -3.5,
    "E": -3.5,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "L": 3.8,
    "K": -3.9,
    "M": 1.9,
    "F": 2.8,
    "P": -1.6,
    "S": -0.8,
    "T": -0.7,
    "W": -0.9,
    "Y": -1.3,
    "V": 4.2,
}

CHARGE = {
    "A": 0,
    "R": 1,
    "N": 0,
    "D": -1,
    "C": 0,
    "Q": 0,
    "E": -1,
    "G": 0,
    "H": 0,
    "I": 0,
    "L": 0,
    "K": 1,
    "M": 0,
    "F": 0,
    "P": 0,
    "S": 0,
    "T": 0,
    "W": 0,
    "Y": 0,
    "V": 0,
}

H_DONORS = {
    "A": 0,
    "R": 2,
    "N": 2,
    "D": 0,
    "C": 0,
    "Q": 2,
    "E": 0,
    "G": 0,
    "H": 1,
    "I": 0,
    "L": 0,
    "K": 1,
    "M": 0,
    "F": 0,
    "P": 0,
    "S": 1,
    "T": 1,
    "W": 1,
    "Y": 1,
    "V": 0,
}

H_ACCEPTORS = {
    "A": 0,
    "R": 0,
    "N": 2,
    "D": 2,
    "C": 1,
    "Q": 2,
    "E": 2,
    "G": 0,
    "H": 1,
    "I": 0,
    "L": 0,
    "K": 0,
    "M": 0,
    "F": 0,
    "P": 0,
    "S": 1,
    "T": 1,
    "W": 0,
    "Y": 1,
    "V": 0,
}

FLEXIBILITY = {
    "A": 0.357,
    "R": 0.529,
    "N": 0.463,
    "D": 0.511,
    "C": 0.346,
    "Q": 0.493,
    "E": 0.497,
    "G": 0.544,
    "H": 0.323,
    "I": 0.462,
    "L": 0.365,
    "K": 0.466,
    "M": 0.295,
    "F": 0.314,
    "P": 0.509,
    "S": 0.507,
    "T": 0.444,
    "W": 0.305,
    "Y": 0.420,
    "V": 0.386,
}

# Canonical amino acids set
CANONICAL_AAS = set(KD_HYDROPHOBICITY.keys())

# Pre-computed thresholds from validation (best k=4 with 84.52% accuracy)
# These are the midpoints between PDB (folded) and DisProt (disordered) means
DEFAULT_THRESHOLDS = {
    "hydro_norm_avg": 0.507,
    "flex_norm_avg": 0.821,
    "h_bond_potential_avg": 1.476,
    "abs_net_charge_prop": 0.082,
    "shannon_entropy": 2.932,
    "freq_proline": 0.063,
    "freq_bulky_hydrophobics": 0.347,
}

# Classification parameters
CLASSIFICATION_THRESHOLD = 4  # Number of conditions that must be met for "structured"
BULKY_HYDROPHOBICS = ["W", "C", "F", "Y", "I", "V", "L"]

# Pre-computed AA properties for fast lookup
AA_PROPERTIES = {}
for aa in CANONICAL_AAS:
    AA_PROPERTIES[aa] = {
        "hydro_norm": (KD_HYDROPHOBICITY[aa] + 4.5) / 9.0,
        "charge_val": CHARGE[aa],
        "h_donors": H_DONORS[aa],
        "h_acceptors": H_ACCEPTORS[aa],
        "flexibility": FLEXIBILITY[aa],
    }


def get_aa_composition(sequence: str) -> Tuple[Dict[str, float], int]:
    """
    Calculate amino acid composition for a sequence.

    Args:
        sequence: Protein sequence string

    Returns:
        Tuple of (composition dict, valid sequence length)
    """
    composition = {amino_acid: 0 for amino_acid in CANONICAL_AAS}
    valid_len = 0

    for amino_acid in sequence:
        if amino_acid in CANONICAL_AAS:
            composition[amino_acid] += 1
            valid_len += 1

    if valid_len == 0:
        return {amino_acid: 0.0 for amino_acid in CANONICAL_AAS}, 0

    for amino_acid in composition:
        composition[amino_acid] /= valid_len  # type: ignore

    return composition, valid_len  # type: ignore


def calculate_shannon_entropy(aa_composition: Dict[str, float]) -> float:
    """
    Calculate Shannon entropy of amino acid composition.

    Args:
        aa_composition: Dictionary mapping amino acids to their frequencies

    Returns:
        Shannon entropy value
    """
    entropy = 0.0
    for aa_freq in aa_composition.values():
        if aa_freq > 0:
            entropy -= aa_freq * math.log2(aa_freq)
    return entropy


def compute_features(sequence: str) -> Dict[str, float]:
    """
    Compute the 7 biophysical features used for classification.

    Features:
    1. hydro_norm_avg: Average normalized hydrophobicity
    2. flex_norm_avg: Average normalized flexibility
    3. h_bond_potential_avg: Average hydrogen bonding potential
    4. abs_net_charge_prop: Absolute net charge proportion
    5. shannon_entropy: Sequence complexity
    6. freq_proline: Proline frequency
    7. freq_bulky_hydrophobics: Frequency of bulky hydrophobic residues

    Args:
        sequence: Protein sequence string

    Returns:
        Dictionary of feature names to values
    """
    if not sequence:
        return {
            "hydro_norm_avg": 0.0,
            "flex_norm_avg": 0.0,
            "h_bond_potential_avg": 0.0,
            "abs_net_charge_prop": 0.0,
            "shannon_entropy": 0.0,
            "freq_proline": 0.0,
            "freq_bulky_hydrophobics": 0.0,
        }

    composition, valid_len = get_aa_composition(sequence)

    if valid_len == 0:
        return {
            "hydro_norm_avg": 0.0,
            "flex_norm_avg": 0.0,
            "h_bond_potential_avg": 0.0,
            "abs_net_charge_prop": 0.0,
            "shannon_entropy": 0.0,
            "freq_proline": 0.0,
            "freq_bulky_hydrophobics": 0.0,
        }

    # Compute average properties
    hydro_norm_sum = 0
    flex_norm_sum = 0
    h_bond_potential_sum = 0

    for amino_acid in sequence:
        if amino_acid in AA_PROPERTIES:
            props = AA_PROPERTIES[amino_acid]
            hydro_norm_sum += props["hydro_norm"]  # type: ignore
            flex_norm_sum += props["flexibility"] / 0.544  # type: ignore # Normalize by max flexibility
            h_bond_potential_sum += props["h_donors"] + props["h_acceptors"]  # type: ignore

    # Net charge (positive - negative)
    net_charge_prop = (composition.get("R", 0) + composition.get("K", 0)) - (
        composition.get("D", 0) + composition.get("E", 0)
    )

    # Bulky hydrophobics frequency
    freq_bulky = sum(composition.get(aa, 0) for aa in BULKY_HYDROPHOBICS)

    return {
        "hydro_norm_avg": hydro_norm_sum / valid_len,
        "flex_norm_avg": flex_norm_sum / valid_len,
        "h_bond_potential_avg": h_bond_potential_sum / valid_len,
        "abs_net_charge_prop": abs(net_charge_prop),
        "shannon_entropy": calculate_shannon_entropy(composition),
        "freq_proline": composition.get("P", 0),
        "freq_bulky_hydrophobics": freq_bulky,
    }


def count_conditions_met(
    features: Dict[str, float], thresholds: Optional[Dict[str, float]] = None
) -> int:
    """
    Count how many conditions are met for "structured" classification.

    Args:
        features: Computed feature dictionary
        thresholds: Optional custom thresholds (uses defaults if None)

    Returns:
        Number of conditions met (0-7)
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    conditions_met = 0

    # Feature conditions based on empirical analysis:
    # Structured proteins (PDB) typically have:
    # - Higher hydrophobicity
    if features["hydro_norm_avg"] >= thresholds["hydro_norm_avg"]:
        conditions_met += 1

    # - Lower flexibility
    if features["flex_norm_avg"] <= thresholds["flex_norm_avg"]:
        conditions_met += 1

    # - Lower H-bond potential
    if features["h_bond_potential_avg"] <= thresholds["h_bond_potential_avg"]:
        conditions_met += 1

    # - Lower absolute charge
    if features["abs_net_charge_prop"] <= thresholds["abs_net_charge_prop"]:
        conditions_met += 1

    # - Higher entropy (more diverse composition)
    if features["shannon_entropy"] >= thresholds["shannon_entropy"]:
        conditions_met += 1

    # - Lower proline content
    if features["freq_proline"] <= thresholds["freq_proline"]:
        conditions_met += 1

    # - Higher bulky hydrophobics
    if features["freq_bulky_hydrophobics"] >= thresholds["freq_bulky_hydrophobics"]:
        conditions_met += 1

    return conditions_met


def classify_sequence(
    sequence: str,
    threshold: int = CLASSIFICATION_THRESHOLD,
    custom_thresholds: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Classify a protein sequence as structured or disordered.

    Args:
        sequence: Protein sequence string
        threshold: Minimum number of conditions for "structured" (default: 4)
        custom_thresholds: Optional custom feature thresholds

    Returns:
        Dictionary containing:
        - classification: "structured" or "disordered"
        - confidence: Confidence score (0-1)
        - conditions_met: Number of conditions satisfied
        - threshold: Threshold used
        - features: Feature values
    """
    # Clean sequence to canonical amino acids only
    clean_seq = "".join(aa for aa in sequence.upper() if aa in CANONICAL_AAS)

    if not clean_seq:
        return {
            "classification": "unknown",
            "confidence": 0.0,
            "conditions_met": 0,
            "threshold": threshold,
            "features": {},
            "error": "No valid amino acids in sequence",
        }

    # Compute features
    features = compute_features(clean_seq)

    # Count conditions met
    conditions_met = count_conditions_met(features, custom_thresholds)

    # Classify
    is_structured = conditions_met >= threshold
    classification = "structured" if is_structured else "disordered"

    # Compute confidence (based on how far from threshold)
    # Full confidence at 7 (all conditions) or 0 (no conditions)
    # Less confidence near the threshold
    if is_structured:
        # Structured: confidence increases from threshold to 7
        confidence = (
            0.5 + 0.5 * ((conditions_met - threshold) / (7 - threshold)) if threshold < 7 else 1.0
        )
    else:
        # Disordered: confidence increases from threshold-1 down to 0
        confidence = (
            0.5 + 0.5 * ((threshold - 1 - conditions_met) / threshold) if threshold > 0 else 1.0
        )

    # Cap confidence at reasonable bounds
    confidence = max(0.5, min(1.0, confidence))

    return {
        "classification": classification,
        "confidence": round(confidence, 2),
        "conditions_met": conditions_met,
        "threshold": threshold,
        "features": {k: round(v, 4) for k, v in features.items()},
    }


def classify_batch(
    sequences: List[Tuple[str, str]],
    threshold: int = CLASSIFICATION_THRESHOLD,
    custom_thresholds: Optional[Dict[str, float]] = None,
) -> List[Dict]:
    """
    Classify multiple sequences in batch.

    Args:
        sequences: List of (id, sequence) tuples
        threshold: Minimum number of conditions for "structured"
        custom_thresholds: Optional custom feature thresholds

    Returns:
        List of classification result dictionaries
    """
    results = []

    for seq_id, sequence in sequences:
        result = classify_sequence(sequence, threshold, custom_thresholds)
        result["id"] = seq_id
        result["sequence"] = sequence[:100] + (
            "..." if len(sequence) > 100 else ""
        )  # Truncate long sequences
        results.append(result)

    return results
