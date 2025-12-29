import requests
import time
import os

def split_fasta(filepath):
    """
    Parses a FASTA file and returns a list of (header, sequence) tuples.
    """
    sequences = []
    with open(filepath, "r") as f:
        header = None
        seq_lines = []
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

def download_pdb_chains(limit=15000, output_file="pdb_chains.fasta"):
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
        raise RuntimeError(f"Failed to download PDB chain sequences: {e}")

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

def download_disprot_sequences(total_desired=25000, output_file="disprot_13000.fasta"):
    """
    Downloads DisProt sequences via API, aiming for 'total_desired' sequences,
    and saves to 'output_file'.
    """
    PER_PAGE = 100  # DisProt’s hard cap per request
    accum_seqs = []
    offset = 0

    while len(accum_seqs) < total_desired:
        url = f"https://disprot.org/api/search?format=fasta&limit={PER_PAGE}&offset={offset}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to GET DisProt FASTA (offset={offset}): {e}")

        block = resp.text.strip()
        if not block.startswith(">"):
            raise RuntimeError("Downloaded content does not look like FASTA.")

        # Parse sequences
        raw_lines = block.splitlines()
        header = None
        seq_buf = ""
        this_page_seqs = []
        for line in raw_lines:
            if line.startswith(">"):
                if header is not None and seq_buf:
                    this_page_seqs.append(seq_buf)
                header = line
                seq_buf = ""
            else:
                seq_buf += line.strip()
        if header is not None and seq_buf:
            this_page_seqs.append(seq_buf)

        if not this_page_seqs:
            break  # No more sequences

        accum_seqs.extend(this_page_seqs)
        offset += PER_PAGE
        time.sleep(0.4)  # Be nice to the server

    # Trim if overshot
    accum_seqs = accum_seqs[:total_desired]

    # Write to file
    with open(output_file, "w") as f:
        for i, seq in enumerate(accum_seqs):
            f.write(f">disprot_sequence_{i+1}\n")
            f.write(seq + "\n")

    print(f"✔ Fetched {len(accum_seqs)} DisProt sequences → '{output_file}'")
    return output_file

def setup_training_data(pdb_limit=15000, disprot_total=25000, pdb_file="pdb_chains.fasta", disprot_file="disprot_13000.fasta"):
    """
    Convenience function to download both PDB and DisProt data.
    """
    download_pdb_chains(limit=pdb_limit, output_file=pdb_file)
    download_disprot_sequences(total_desired=disprot_total, output_file=disprot_file)
    print("Training data setup complete.")