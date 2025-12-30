"""
Utility functions for the API.
"""

from typing import List, Tuple
from io import StringIO


def _save_sequence(
    sequences: List[Tuple[str, str]], seq_id: str, seq_parts: List[str]
) -> None:
    """
    Save a sequence to the sequences list after validation.

    Args:
        sequences: List to append sequence to
        seq_id: Sequence identifier
        seq_parts: List of sequence parts to join

    Raises:
        ValueError: If sequence has no data
    """
    if not seq_parts:
        raise ValueError(f"Sequence {seq_id} has no sequence data")
    sequences.append((seq_id, "".join(seq_parts)))


def _process_header_line(line: str, line_num: int) -> str:
    """
    Process a FASTA header line and extract the sequence ID.

    Args:
        line: Header line (starting with >)
        line_num: Line number for error reporting

    Returns:
        Sequence ID
    """
    seq_id = line[1:].strip()
    if not seq_id:
        seq_id = f"sequence_{line_num}"
    return seq_id


def parse_fasta(fasta_text: str) -> List[Tuple[str, str]]:
    """
    Parse FASTA format text into a list of (id, sequence) tuples.

    Args:
        fasta_text: FASTA formatted text

    Returns:
        List of (sequence_id, sequence) tuples

    Raises:
        ValueError: If FASTA format is invalid
    """
    sequences = []
    current_id = None
    current_seq = []

    lines = fasta_text.strip().split("\n")

    if not lines or not fasta_text.strip():
        raise ValueError("Empty FASTA input")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        if not line:  # Skip empty lines
            continue

        if line.startswith(">"):
            # Save previous sequence if exists
            if current_id is not None:
                _save_sequence(sequences, current_id, current_seq)

            # Start new sequence
            current_id = _process_header_line(line, line_num)
            current_seq = []
        else:
            if current_id is None:
                raise ValueError(
                    f"Sequence data found before header at line {line_num}"
                )
            current_seq.append(line)

    # Save last sequence
    if current_id is not None:
        _save_sequence(sequences, current_id, current_seq)

    if not sequences:
        raise ValueError("No valid sequences found in FASTA input")

    return sequences


def format_fasta(sequences: List[Tuple[str, str]], line_width: int = 60) -> str:
    """
    Format sequences as FASTA text.

    Args:
        sequences: List of (id, sequence) tuples
        line_width: Maximum line width for sequence (default: 60)

    Returns:
        FASTA formatted string
    """
    output = StringIO()

    for seq_id, sequence in sequences:
        output.write(f">{seq_id}\n")

        # Wrap sequence at line_width
        for i in range(0, len(sequence), line_width):
            output.write(sequence[i : i + line_width] + "\n")

    return output.getvalue()


def validate_amino_acid_sequence(sequence: str) -> Tuple[bool, str]:
    """
    Validate that a sequence contains valid amino acid characters.

    Args:
        sequence: Protein sequence string

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_aas = set("ACDEFGHIKLMNPQRSTVWY")
    invalid_chars = set()

    for char in sequence.upper():
        if char not in valid_aas and char not in " \t\n\r":
            invalid_chars.add(char)

    if invalid_chars:
        return False, f"Invalid amino acid characters: {', '.join(sorted(invalid_chars))}"

    clean_seq = "".join(c for c in sequence.upper() if c in valid_aas)
    if not clean_seq:
        return False, "Sequence contains no valid amino acids"

    return True, ""
