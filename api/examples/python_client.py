#!/usr/bin/env python3
"""
Python client example for the Protein Disorder Classification API.

This example demonstrates how to use the API to classify protein sequences.
"""

import requests
from typing import List, Tuple, Dict


class ProteinClassifierClient:
    """Client for the Protein Disorder Classification API."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the API (default: http://localhost:8000)
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def health_check(self) -> Dict:
        """Check if the API is healthy."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def classify(self, sequences: List[Tuple[str, str]], threshold: int = 4) -> Dict:
        """
        Classify protein sequences.

        Args:
            sequences: List of (id, sequence) tuples
            threshold: Classification threshold (default: 4)

        Returns:
            Classification results as a dictionary
        """
        payload = {
            "sequences": [{"id": seq_id, "sequence": seq} for seq_id, seq in sequences],
            "threshold": threshold,
        }

        response = self.session.post(f"{self.base_url}/api/v1/classify", json=payload)
        response.raise_for_status()
        return response.json()

    def classify_fasta(self, fasta_text: str, threshold: int = 4) -> Dict:
        """
        Classify sequences from FASTA format.

        Args:
            fasta_text: FASTA formatted text
            threshold: Classification threshold (default: 4)

        Returns:
            Classification results as a dictionary
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/classify/fasta",
            params={"threshold": threshold},
            data=fasta_text,
            headers={"Content-Type": "text/plain"},
        )
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of the client."""
    # Initialize client with API key
    api_key = "YOUR_API_KEY_HERE"  # Replace with your API key
    client = ProteinClassifierClient(api_key=api_key)

    # Check API health
    print("Checking API health...")
    health = client.health_check()
    print(f"API Status: {health['status']}")
    print(f"API Version: {health['version']}")
    print()

    # Example 1: Classify a single sequence
    print("=" * 60)
    print("Example 1: Single Sequence Classification")
    print("=" * 60)

    sequences = [("albumin_fragment", "MKVLWAASLLLLASAARA")]

    results = client.classify(sequences)

    for result in results["results"]:
        print(f"\nSequence ID: {result['id']}")
        print(f"Classification: {result['classification']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Conditions Met: {result['conditions_met']}/{result['threshold']}")
        print(f"Processing Time: {result['processing_time_ms']}ms")
        print("\nFeatures:")
        for feature, value in result["features"].items():
            print(f"  {feature}: {value:.4f}")

    print()

    # Example 2: Classify multiple sequences
    print("=" * 60)
    print("Example 2: Batch Classification")
    print("=" * 60)

    sequences = [
        ("structured_protein", "ILVILVILVILVILVILVILVIL"),
        ("disordered_protein", "KKEEKKEEKKEEKKEEGGPPGGPP"),
        ("mixed_protein", "ACDEFGHIKLMNPQRSTVWY"),
    ]

    results = client.classify(sequences)

    print(f"\nProcessed {results['total_sequences']} sequences in {results['total_time_ms']:.2f}ms")
    print()

    for result in results["results"]:
        print(
            f"{result['id']:25s} -> {result['classification']:12s} "
            f"(confidence: {result['confidence']:.2f}, "
            f"conditions: {result['conditions_met']}/{result['threshold']})"
        )

    print()

    # Example 3: Classify from FASTA
    print("=" * 60)
    print("Example 3: FASTA Classification")
    print("=" * 60)

    fasta_text = """>protein1
MKVLWAASLLLLASAARA
>protein2
MALWMRLLPLLALLALWGPDPAAAF
"""

    results = client.classify_fasta(fasta_text)

    print(f"\nProcessed {results['total_sequences']} sequences from FASTA")
    print()

    for result in results["results"]:
        print(f"{result['id']:15s} -> {result['classification']}")


if __name__ == "__main__":
    main()
