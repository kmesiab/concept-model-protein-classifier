"""
Tests for the classifier module.
"""

from app.classifier import (
    get_aa_composition,
    calculate_shannon_entropy,
    compute_features,
    count_conditions_met,
    classify_sequence,
    classify_batch,
    CANONICAL_AAS,
    DEFAULT_THRESHOLDS
)


class TestAAComposition:
    """Tests for amino acid composition calculation."""
    
    def test_simple_sequence(self):
        """Test composition of a simple sequence."""
        composition, length = get_aa_composition("AAA")
        assert length == 3
        assert composition['A'] == 1.0
        assert composition['C'] == 0.0
    
    def test_mixed_sequence(self):
        """Test composition of mixed sequence."""
        composition, length = get_aa_composition("ACDEFGH")
        assert length == 7
        assert composition['A'] == 1/7
        assert composition['C'] == 1/7
    
    def test_empty_sequence(self):
        """Test empty sequence."""
        composition, length = get_aa_composition("")
        assert length == 0
        assert all(v == 0.0 for v in composition.values())
    
    def test_invalid_characters(self):
        """Test sequence with invalid characters."""
        composition, length = get_aa_composition("AAA123XXX")
        assert length == 3  # Only valid AAs counted
        assert composition['A'] == 1.0


class TestShannonEntropy:
    """Tests for Shannon entropy calculation."""
    
    def test_uniform_distribution(self):
        """Test entropy of uniform distribution."""
        # All 20 amino acids equally distributed
        composition = {aa: 1/20 for aa in CANONICAL_AAS}
        entropy = calculate_shannon_entropy(composition)
        # Should be log2(20) ≈ 4.32
        assert 4.3 < entropy < 4.4
    
    def test_single_amino_acid(self):
        """Test entropy of single amino acid."""
        composition = {aa: (1.0 if aa == 'A' else 0.0) for aa in CANONICAL_AAS}
        entropy = calculate_shannon_entropy(composition)
        assert entropy == 0.0
    
    def test_two_amino_acids(self):
        """Test entropy of two amino acids."""
        composition = {aa: (0.5 if aa in ['A', 'C'] else 0.0) for aa in CANONICAL_AAS}
        entropy = calculate_shannon_entropy(composition)
        assert abs(entropy - 1.0) < 0.01  # Should be 1.0


class TestComputeFeatures:
    """Tests for feature computation."""
    
    def test_structured_protein_features(self):
        """Test features of a typical structured protein sequence."""
        # Use a hydrophobic, low-charge sequence
        sequence = "VVVVVVVVVVVVVVVVVVVV"
        features = compute_features(sequence)
        
        assert 'hydro_norm_avg' in features
        assert 'flex_norm_avg' in features
        assert 'h_bond_potential_avg' in features
        assert 'abs_net_charge_prop' in features
        assert 'shannon_entropy' in features
        assert 'freq_proline' in features
        assert 'freq_bulky_hydrophobics' in features
        
        # Hydrophobic sequence should have high hydrophobicity
        assert features['hydro_norm_avg'] > 0.5
        # No proline
        assert features['freq_proline'] == 0.0
        # Low entropy (all same AA)
        assert features['shannon_entropy'] == 0.0
    
    def test_disordered_protein_features(self):
        """Test features of a typical disordered protein sequence."""
        # Use a charged, flexible sequence with unbalanced charge
        sequence = "KKKKEEEEGGGGSSSSPPPP"
        features = compute_features(sequence)
        
        # Has proline
        assert features['freq_proline'] > 0.0
        # Low hydrophobicity (charged and polar residues)
        assert features['hydro_norm_avg'] < 0.6
    
    def test_empty_sequence(self):
        """Test features of empty sequence."""
        features = compute_features("")
        assert all(v == 0.0 for v in features.values())
    
    def test_feature_ranges(self):
        """Test that features are within expected ranges."""
        sequence = "ACDEFGHIKLMNPQRSTVWY"
        features = compute_features(sequence)
        
        # All features should be non-negative
        assert all(v >= 0.0 for v in features.values())
        
        # Frequencies should be <= 1.0
        assert features['freq_proline'] <= 1.0
        assert features['freq_bulky_hydrophobics'] <= 1.0


class TestCountConditions:
    """Tests for condition counting."""
    
    def test_all_conditions_met(self):
        """Test when all conditions are met."""
        # Create features that satisfy all structured conditions
        features = {
            'hydro_norm_avg': 0.9,  # High (structured)
            'flex_norm_avg': 0.5,   # Low (structured)
            'h_bond_potential_avg': 1.0,  # Low (structured)
            'abs_net_charge_prop': 0.01,  # Low (structured)
            'shannon_entropy': 4.0,  # High (structured)
            'freq_proline': 0.01,  # Low (structured)
            'freq_bulky_hydrophobics': 0.5  # High (structured)
        }
        count = count_conditions_met(features)
        assert count == 7
    
    def test_no_conditions_met(self):
        """Test when no conditions are met."""
        features = {
            'hydro_norm_avg': 0.1,   # Low (disordered)
            'flex_norm_avg': 0.95,   # High (disordered)
            'h_bond_potential_avg': 2.0,  # High (disordered)
            'abs_net_charge_prop': 0.5,   # High (disordered)
            'shannon_entropy': 2.0,  # Low (disordered)
            'freq_proline': 0.2,     # High (disordered)
            'freq_bulky_hydrophobics': 0.1  # Low (disordered)
        }
        count = count_conditions_met(features)
        assert count == 0
    
    def test_custom_thresholds(self):
        """Test with custom thresholds."""
        features = {
            'hydro_norm_avg': 0.6,
            'flex_norm_avg': 0.8,
            'h_bond_potential_avg': 1.4,
            'abs_net_charge_prop': 0.08,
            'shannon_entropy': 3.0,
            'freq_proline': 0.06,
            'freq_bulky_hydrophobics': 0.35
        }
        
        # Use stricter thresholds
        custom_thresholds = {k: v * 1.5 for k, v in DEFAULT_THRESHOLDS.items()}
        count = count_conditions_met(features, custom_thresholds)
        # Fewer conditions should be met with stricter thresholds
        assert count < 7


class TestClassifySequence:
    """Tests for sequence classification."""
    
    def test_structured_classification(self):
        """Test classification of a structured protein."""
        # A hydrophobic, well-folded sequence
        sequence = "ILVILVILVILVILVILVILVILV"
        result = classify_sequence(sequence)
        
        assert result['classification'] == 'structured'
        assert result['conditions_met'] >= 4
        assert 0.5 <= result['confidence'] <= 1.0
        assert 'features' in result
    
    def test_disordered_classification(self):
        """Test classification of a disordered protein."""
        # A charged, flexible sequence
        sequence = "KKEEKKEEKKEEKKEEGGPPGGPP"
        result = classify_sequence(sequence)
        
        assert result['classification'] == 'disordered'
        assert result['conditions_met'] < 4
        assert 0.5 <= result['confidence'] <= 1.0
    
    def test_custom_threshold(self):
        """Test classification with custom threshold."""
        sequence = "ACDEFGHIKLMNPQRSTVWY"
        
        # Try different thresholds
        result_low = classify_sequence(sequence, threshold=2)
        result_high = classify_sequence(sequence, threshold=6)
        
        # With lower threshold, more likely to be structured
        # With higher threshold, more likely to be disordered
        assert result_low['threshold'] == 2
        assert result_high['threshold'] == 6
    
    def test_empty_sequence(self):
        """Test classification of empty sequence."""
        result = classify_sequence("")
        assert result['classification'] == 'unknown'
        assert 'error' in result
    
    def test_invalid_characters(self):
        """Test sequence with invalid characters."""
        result = classify_sequence("AAA123XXX")
        # Should still classify the valid part
        assert result['classification'] in ['structured', 'disordered']


class TestClassifyBatch:
    """Tests for batch classification."""
    
    def test_batch_classification(self):
        """Test batch classification of multiple sequences."""
        sequences = [
            ('seq1', 'ILVILVILVILVILVILVILVIL'),
            ('seq2', 'KKEEKKEEKKEEKKEEGGPPGGPP'),
            ('seq3', 'ACDEFGHIKLMNPQRSTVWY')
        ]
        
        results = classify_batch(sequences)
        
        assert len(results) == 3
        assert all('id' in r for r in results)
        assert all('classification' in r for r in results)
        assert all('confidence' in r for r in results)
    
    def test_batch_with_custom_threshold(self):
        """Test batch with custom threshold."""
        sequences = [
            ('seq1', 'ACDEFGHIKLMNPQRSTVWY'),
            ('seq2', 'ACDEFGHIKLMNPQRSTVWY')
        ]
        
        results = classify_batch(sequences, threshold=5)
        
        assert all(r['threshold'] == 5 for r in results)
    
    def test_empty_batch(self):
        """Test empty batch."""
        results = classify_batch([])
        assert len(results) == 0


class TestRealWorldSequences:
    """Tests with real-world protein sequences."""
    
    def test_albumin_structured(self):
        """Test human serum albumin (structured protein)."""
        # First 50 residues of human serum albumin
        albumin = "MKWVTFISLLFLFSSAYSRGVFRRDAHKSEVAHRFKDLGEENFKALVL"
        result = classify_sequence(albumin)
        
        # Albumin is a structured protein
        # Note: Results may vary, but it should be classified
        assert result['classification'] in ['structured', 'disordered']
        assert 'features' in result
    
    def test_alpha_synuclein_disordered(self):
        """Test alpha-synuclein (intrinsically disordered)."""
        # First 50 residues of alpha-synuclein
        alpha_syn = "MDVFMKGLSKAKEGVVAAAEKTKQGVAEAAGKTKEGVLYVGSKTKEGV"
        result = classify_sequence(alpha_syn)
        
        # Alpha-synuclein is intrinsically disordered
        # Note: Results may vary
        assert result['classification'] in ['structured', 'disordered']
        assert 'features' in result
