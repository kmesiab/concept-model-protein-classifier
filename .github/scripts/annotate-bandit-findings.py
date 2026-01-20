#!/usr/bin/env python3
"""Parse Bandit JSON report and emit GitHub Actions error annotations."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_bandit_report(filepath: str) -> Dict[str, Any]:
    """Load Bandit JSON report from file.

    Args:
        filepath: Path to Bandit JSON report

    Returns:
        Parsed JSON report as dictionary

    Raises:
        FileNotFoundError: If report file doesn't exist
        json.JSONDecodeError: If report is not valid JSON
    """
    report_path = Path(filepath)
    if not report_path.exists():
        raise FileNotFoundError(f"Bandit report not found: {filepath}")

    with report_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def emit_github_error(filename: str, line: int, severity: str, issue_id: str, message: str) -> None:
    """Emit GitHub Actions error annotation.

    Args:
        filename: Source file path
        line: Line number
        severity: Severity level (HIGH, MEDIUM, LOW)
        issue_id: Bandit issue ID (e.g., B201)
        message: Issue description
    """
    # Format: ::error file={name},line={line}::{message}
    annotation = (
        f"::error file={filename},line={line}::" f"[Bandit {severity}] {issue_id}: {message}"
    )
    print(annotation, flush=True)


def annotate_findings(report: Dict[str, Any], min_severity: str = "MEDIUM") -> int:
    """Parse Bandit report and emit GitHub annotations for findings.

    Args:
        report: Parsed Bandit JSON report
        min_severity: Minimum severity to annotate (HIGH, MEDIUM, or LOW)

    Returns:
        Number of findings annotated
    """
    severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    min_level = severity_order.get(min_severity.upper(), 1)

    results: List[Dict[str, Any]] = report.get("results", [])
    count = 0

    for finding in results:
        severity = finding.get("issue_severity", "UNKNOWN").upper()
        severity_level = severity_order.get(severity, 0)

        if severity_level < min_level:
            continue

        filename = finding.get("filename", "unknown")
        line = finding.get("line_number", 0)
        issue_id = finding.get("test_id", "")
        message = finding.get("issue_text", "Security issue detected")

        emit_github_error(filename, line, severity, issue_id, message)
        count += 1

    return count


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if len(sys.argv) < 2:
        print("Usage: annotate-bandit-findings.py <bandit-report.json>", file=sys.stderr)
        return 1

    report_path = sys.argv[1]
    min_severity = sys.argv[2] if len(sys.argv) > 2 else "MEDIUM"

    try:
        report = load_bandit_report(report_path)
        count = annotate_findings(report, min_severity)

        print(f"\n📊 Annotated {count} Bandit finding(s)", flush=True)
        return 0

    except FileNotFoundError as e:
        print(f"::error::{e}", flush=True)
        return 1
    except json.JSONDecodeError as e:
        print(f"::error::Invalid JSON in Bandit report: {e}", flush=True)
        return 1
    except Exception as e:
        print(f"::error::Error processing Bandit report: {e}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
