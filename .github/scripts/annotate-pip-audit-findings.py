#!/usr/bin/env python3
"""Parse pip-audit JSON report and emit GitHub Actions error annotations."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_pip_audit_report(filepath: str) -> Dict[str, Any]:
    """Load pip-audit JSON report from file.

    Args:
        filepath: Path to pip-audit JSON report

    Returns:
        Parsed JSON report as dictionary

    Raises:
        FileNotFoundError: If report file doesn't exist
        json.JSONDecodeError: If report is not valid JSON
    """
    report_path = Path(filepath)
    if not report_path.exists():
        raise FileNotFoundError(f"pip-audit report not found: {filepath}")

    with report_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def emit_github_error(package: str, version: str, vuln_id: str, message: str) -> None:
    """Emit GitHub Actions error annotation for vulnerability.

    Args:
        package: Package name
        version: Installed version
        vuln_id: Vulnerability ID (e.g., CVE-2023-1234)
        message: Vulnerability description
    """
    # Use requirements.txt as the file for annotation
    annotation = (
        f"::error file=requirements.txt::" f"[pip-audit] {package} {version} - {vuln_id}: {message}"
    )
    print(annotation, flush=True)


def annotate_findings(report: Dict[str, Any]) -> int:
    """Parse pip-audit report and emit GitHub annotations for vulnerabilities.

    Args:
        report: Parsed pip-audit JSON report

    Returns:
        Number of vulnerabilities annotated
    """
    dependencies: List[Dict[str, Any]] = report.get("dependencies", [])
    count = 0

    for dep in dependencies:
        package = dep.get("name", "unknown")
        version = dep.get("version", "unknown")
        vulns: List[Dict[str, Any]] = dep.get("vulns", [])

        for vuln in vulns:
            vuln_id = vuln.get("id", "UNKNOWN")
            description = vuln.get("description", "Vulnerability detected")
            # Truncate long descriptions
            if len(description) > 150:
                description = description[:147] + "..."

            emit_github_error(package, version, vuln_id, description)
            count += 1

    return count


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if len(sys.argv) < 2:
        print("Usage: annotate-pip-audit-findings.py <pip-audit-report.json>", file=sys.stderr)
        return 1

    report_path = sys.argv[1]

    try:
        report = load_pip_audit_report(report_path)
        count = annotate_findings(report)

        print(f"\n📊 Annotated {count} pip-audit vulnerability/vulnerabilities", flush=True)
        return 0

    except FileNotFoundError as e:
        print(f"::error::{e}", flush=True)
        return 1
    except json.JSONDecodeError as e:
        print(f"::error::Invalid JSON in pip-audit report: {e}", flush=True)
        return 1
    except Exception as e:
        print(f"::error::Error processing pip-audit report: {e}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
