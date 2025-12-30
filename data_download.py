import os
import time
from typing import List, Optional, Tuple

import requests


def split_fasta(filepath: str) -> List[Tuple[str, str]]:
    """
    Parses a FASTA file and returns a list of (header, sequence) tuples.
    """
    sequences: List[Tuple[str, str]] = []
    with open(filepath, "r", encoding="utf-8") as f:
        header: Optional[str] = None
        seq_lines: List[str] = []
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if header is not None:
                    sequences.append((header, "".join(seq_lines)))
                header = line
                seq_lines = []
            else:
                seq_lines.append(line)
        # Add the final sequence
        if header is not None:
            sequences.append((header, "".join(seq_lines)))
    return sequences


def download_pdb_chains(limit: int = 15000, output_file: str = "pdb_chains.fasta") -> str:
    """
    Downloads PDB chain sequences from RCSB HTTPS mirror, keeps the first 'limit' entries,
    and saves to 'output_file'.
    """
    pdb_url = "https://files.wwpdb.org/pub/pdb/derived_data/pdb_seqres.txt"
    try:
        resp = requests.get(pdb_url, timeout=60)
        resp.raise_for_status()
        text = resp.text.strip()
        if not text.startswith(">"):
            raise RuntimeError("Downloaded content does not look like FASTA.")
    except Exception as e:
        raise RuntimeError(f"Failed to download PDB chain sequences: {e}") from e

    # Write the complete dump to a temporary file
    temp_file = "temp_pdb_full.fasta"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(text + "\n")

    # Split and subset
    all_chains = split_fasta(temp_file)
    subset = all_chains[:limit]

    # Write subset to output file
    with open(output_file, "w", encoding="utf-8") as f:
        for header, seq in subset:
            f.write(f"{header}\n")
            f.write(f"{seq}\n")

    # Clean up temp file
    os.remove(temp_file)

    print(f"✔ Extracted {len(subset)} PDB chains → '{output_file}'")
    return output_file


def _parse_fasta_block(block: str) -> List[str]:
    """
    Parse a FASTA format block and extract sequences.
    Returns a list of sequence strings (without headers).
    """
    raw_lines = block.splitlines()
    header = None
    seq_buf = ""
    sequences = []

    for line in raw_lines:
        if line.startswith(">"):
            if header is not None and seq_buf:
                sequences.append(seq_buf)
            header = line
            seq_buf = ""
        else:
            seq_buf += line.strip()

    if header is not None and seq_buf:
        sequences.append(seq_buf)

    return sequences


def download_disprot_sequences(
    total_desired: int = 25000, output_file: str = "disprot_13000.fasta"
) -> str:
    """
    Downloads DisProt sequences via API, aiming for 'total_desired' sequences,
    and saves to 'output_file'.
    """
    PER_PAGE = 100  # DisProt’s hard cap per request
    accum_seqs: List[str] = []
    offset = 0

    while len(accum_seqs) < total_desired:
        url = f"https://disprot.org/api/search?format=fasta&limit={PER_PAGE}&offset={offset}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to GET DisProt FASTA (offset={offset}): {e}") from e

        block = resp.text.strip()
        if not block.startswith(">"):
            raise RuntimeError("Downloaded content does not look like FASTA.")

        # Parse sequences from the block
        this_page_seqs = _parse_fasta_block(block)

        if not this_page_seqs:
            break  # No more sequences

        accum_seqs.extend(this_page_seqs)
        offset += PER_PAGE
        time.sleep(0.4)  # Be nice to the server

    # Trim if overshot
    accum_seqs = accum_seqs[:total_desired]

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        for i, seq in enumerate(accum_seqs):
            f.write(f">disprot_sequence_{i+1}\n")
            f.write(seq + "\n")

    print(f"✔ Fetched {len(accum_seqs)} DisProt sequences → '{output_file}'")
    return output_file


def setup_training_data(
    pdb_limit: int = 15000,
    disprot_total: int = 25000,
    pdb_file: str = "pdb_chains.fasta",
    disprot_file: str = "disprot_13000.fasta",
) -> None:
    """
    Convenience function to download both PDB and DisProt data.
    """
    download_pdb_chains(limit=pdb_limit, output_file=pdb_file)
    download_disprot_sequences(total_desired=disprot_total, output_file=disprot_file)
    print("Training data setup complete.")
