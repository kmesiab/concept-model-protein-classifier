"""Tests for data_download module."""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from data_download import download_disprot_sequences, download_pdb_chains, split_fasta


class TestSplitFasta:
    """Test the split_fasta function."""

    def test_split_fasta_basic(self) -> None:
        """Test basic FASTA file parsing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as f:
            f.write(">seq1\n")
            f.write("ACGT\n")
            f.write(">seq2\n")
            f.write("TGCA\n")
            temp_path = f.name

        try:
            sequences = split_fasta(temp_path)
            assert len(sequences) == 2
            assert sequences[0] == (">seq1", "ACGT")
            assert sequences[1] == (">seq2", "TGCA")
        finally:
            os.unlink(temp_path)

    def test_split_fasta_multiline_sequence(self) -> None:
        """Test parsing FASTA with multi-line sequences."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as f:
            f.write(">seq1\n")
            f.write("ACGT\n")
            f.write("NNNN\n")
            f.write(">seq2\n")
            f.write("TGCA\n")
            temp_path = f.name

        try:
            sequences = split_fasta(temp_path)
            assert len(sequences) == 2
            assert sequences[0] == (">seq1", "ACGTNNNN")
            assert sequences[1] == (">seq2", "TGCA")
        finally:
            os.unlink(temp_path)

    def test_split_fasta_empty_file(self) -> None:
        """Test parsing empty FASTA file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as f:
            temp_path = f.name

        try:
            sequences = split_fasta(temp_path)
            assert len(sequences) == 0
        finally:
            os.unlink(temp_path)


class TestDownloadPdbChains:
    """Test the download_pdb_chains function."""

    @patch("data_download.requests.get")
    @patch("data_download.os.remove")
    def test_download_pdb_chains_success(self, mock_remove: MagicMock, mock_get: MagicMock) -> None:
        """Test successful PDB chain download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = ">chain1\nACGT\n>chain2\nTGCA\n>chain3\nGGGG\n"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "test_pdb.fasta")
            result = download_pdb_chains(limit=2, output_file=output_file)

            assert result == output_file
            assert os.path.exists(output_file)

            # Check content
            with open(output_file) as f:
                content = f.read()
                assert ">chain1" in content
                assert ">chain2" in content
                assert ">chain3" not in content  # Should be limited to 2

    @patch("data_download.requests.get")
    def test_download_pdb_chains_network_error(self, mock_get: MagicMock) -> None:
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to download PDB"):
            download_pdb_chains(limit=10, output_file="test.fasta")


class TestDownloadDisprotSequences:
    """Test the download_disprot_sequences function."""

    @patch("data_download.requests.get")
    @patch("data_download.time.sleep")
    def test_download_disprot_basic(self, mock_sleep: MagicMock, mock_get: MagicMock) -> None:
        """Test basic DisProt sequence download."""
        # Mock response for first page
        mock_response = MagicMock()
        mock_response.text = ">DP00001\nMSEQUENCE\n>DP00002\nASEQUENCE\n"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "test_disprot.fasta")
            result = download_disprot_sequences(total_desired=2, output_file=output_file)

            assert result == output_file
            assert os.path.exists(output_file)

            # Check content
            with open(output_file) as f:
                content = f.read()
                assert ">disprot_sequence_1" in content
                assert "MSEQUENCE" in content

    @patch("data_download.requests.get")
    def test_download_disprot_network_error(self, mock_get: MagicMock) -> None:
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to GET DisProt"):
            download_disprot_sequences(total_desired=10, output_file="test.fasta")
