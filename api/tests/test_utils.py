"""
Tests for utility functions.
"""

import pytest
from api.app.utils import parse_fasta, format_fasta, validate_amino_acid_sequence


class TestParseFasta:
    """Tests for FASTA parsing."""
    
    def test_single_sequence(self):
        """Test parsing single sequence."""
        fasta = ">seq1\nACDEFGHIKLMNPQRSTVWY"
        sequences = parse_fasta(fasta)
        
        assert len(sequences) == 1
        assert sequences[0] == ('seq1', 'ACDEFGHIKLMNPQRSTVWY')
    
    def test_multiple_sequences(self):
        """Test parsing multiple sequences."""
        fasta = ">seq1\nACDEFG\n>seq2\nHIKLMN"
        sequences = parse_fasta(fasta)
        
        assert len(sequences) == 2
        assert sequences[0] == ('seq1', 'ACDEFG')
        assert sequences[1] == ('seq2', 'HIKLMN')
    
    def test_multiline_sequence(self):
        """Test parsing multiline sequence."""
        fasta = ">seq1\nACDEFG\nHIKLMN\nPQRSTV"
        sequences = parse_fasta(fasta)
        
        assert len(sequences) == 1
        assert sequences[0] == ('seq1', 'ACDEFGHIKLMNPQRSTV')
    
    def test_empty_lines(self):
        """Test parsing with empty lines."""
        fasta = ">seq1\nACDEFG\n\n>seq2\nHIKLMN\n\n"
        sequences = parse_fasta(fasta)
        
        assert len(sequences) == 2
    
    def test_complex_header(self):
        """Test parsing with complex header."""
        fasta = ">sp|P12345|PROT_HUMAN Protein name OS=Homo sapiens\nACDEFG"
        sequences = parse_fasta(fasta)
        
        assert len(sequences) == 1
        assert sequences[0][0] == 'sp|P12345|PROT_HUMAN Protein name OS=Homo sapiens'
        assert sequences[0][1] == 'ACDEFG'
    
    def test_empty_input(self):
        """Test parsing empty input."""
        with pytest.raises(ValueError, match="Empty FASTA"):
            parse_fasta("")
    
    def test_no_header(self):
        """Test parsing without header."""
        fasta = "ACDEFGHIKLMNPQRSTVWY"
        with pytest.raises(ValueError, match="Sequence data found before header"):
            parse_fasta(fasta)
    
    def test_empty_sequence(self):
        """Test parsing with empty sequence."""
        fasta = ">seq1\n>seq2\nACDEFG"
        with pytest.raises(ValueError, match="has no sequence data"):
            parse_fasta(fasta)
    
    def test_header_without_id(self):
        """Test header without ID."""
        fasta = ">\nACDEFG"
        sequences = parse_fasta(fasta)
        
        # Should generate default ID
        assert len(sequences) == 1
        assert sequences[0][0].startswith('sequence_')


class TestFormatFasta:
    """Tests for FASTA formatting."""
    
    def test_single_sequence(self):
        """Test formatting single sequence."""
        sequences = [('seq1', 'ACDEFGHIKLMNPQRSTVWY')]
        fasta = format_fasta(sequences)
        
        assert fasta.startswith('>seq1\n')
        assert 'ACDEFGHIKLMNPQRSTVWY' in fasta
    
    def test_multiple_sequences(self):
        """Test formatting multiple sequences."""
        sequences = [
            ('seq1', 'ACDEFG'),
            ('seq2', 'HIKLMN')
        ]
        fasta = format_fasta(sequences)
        
        assert '>seq1\n' in fasta
        assert '>seq2\n' in fasta
        assert 'ACDEFG' in fasta
        assert 'HIKLMN' in fasta
    
    def test_line_wrapping(self):
        """Test line wrapping at 60 characters."""
        long_seq = 'A' * 120
        sequences = [('seq1', long_seq)]
        fasta = format_fasta(sequences, line_width=60)
        
        lines = fasta.strip().split('\n')
        # Should have header + 2 lines of 60 chars each
        assert len(lines) == 3
        assert len(lines[1]) == 60
        assert len(lines[2]) == 60
    
    def test_custom_line_width(self):
        """Test custom line width."""
        sequences = [('seq1', 'A' * 100)]
        fasta = format_fasta(sequences, line_width=80)
        
        lines = fasta.strip().split('\n')
        # Should have header + 2 lines (80 + 20)
        assert len(lines) == 3
        assert len(lines[1]) == 80


class TestValidateAminoAcidSequence:
    """Tests for amino acid sequence validation."""
    
    def test_valid_sequence(self):
        """Test valid amino acid sequence."""
        is_valid, error = validate_amino_acid_sequence("ACDEFGHIKLMNPQRSTVWY")
        assert is_valid
        assert error == ""
    
    def test_valid_lowercase(self):
        """Test valid sequence with lowercase."""
        is_valid, error = validate_amino_acid_sequence("acdefg")
        assert is_valid
        assert error == ""
    
    def test_valid_with_whitespace(self):
        """Test valid sequence with whitespace."""
        is_valid, error = validate_amino_acid_sequence("ACDE FG\nHI")
        assert is_valid
        assert error == ""
    
    def test_invalid_characters(self):
        """Test sequence with invalid characters."""
        is_valid, error = validate_amino_acid_sequence("ACDE123FG")
        assert not is_valid
        assert "Invalid amino acid characters" in error
        assert "1" in error
    
    def test_special_characters(self):
        """Test sequence with special characters."""
        is_valid, error = validate_amino_acid_sequence("ACDE*FG")
        assert not is_valid
        assert "*" in error
    
    def test_empty_sequence(self):
        """Test empty sequence."""
        is_valid, error = validate_amino_acid_sequence("")
        assert not is_valid
        assert "no valid amino acids" in error
    
    def test_only_whitespace(self):
        """Test sequence with only whitespace."""
        is_valid, error = validate_amino_acid_sequence("   \n\t  ")
        assert not is_valid
        assert "no valid amino acids" in error
    
    def test_mixed_valid_invalid(self):
        """Test sequence with mixed valid and invalid characters."""
        is_valid, error = validate_amino_acid_sequence("AAA123BBB")
        assert not is_valid
        # Should identify all invalid characters
        assert "1" in error
        assert "2" in error
        assert "3" in error


class TestFastaRoundTrip:
    """Tests for FASTA parse/format round trip."""
    
    def test_round_trip(self):
        """Test that parse and format are inverse operations."""
        original_fasta = """>seq1
ACDEFGHIKLMNPQRSTVWY
>seq2
ABCDEFGHIJKLMNOPQRSTUVWXYZ"""
        
        # Parse
        sequences = parse_fasta(original_fasta)
        
        # Format
        formatted = format_fasta(sequences)
        
        # Parse again
        sequences2 = parse_fasta(formatted)
        
        # Should be equivalent
        assert sequences == sequences2
