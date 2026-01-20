#!/usr/bin/env python3
"""Parse Trivy JSON report and emit GitHub Actions error annotations."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_trivy_report(filepath: str) -> Dict[str, Any]:
    """Load Trivy JSON report from file.

    Args:
        filepath: Path to Trivy JSON report

    Returns:
        Parsed JSON report as dictionary

    Raises:
        FileNotFoundError: If report file doesn't exist
        json.JSONDecodeError: If report is not valid JSON
    """
    report_path = Path(filepath)
    if not report_path.exists():
        raise FileNotFoundError(f"Trivy report not found: {filepath}")

    with report_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def emit_github_error(
    filename: str, severity: str, vuln_id: str, package: str, message: str
) -> None:
    """Emit GitHub Actions error annotation for vulnerability.

    Args:
        filename: Target file/path
        severity: Severity level (CRITICAL, HIGH, MEDIUM)
        vuln_id: Vulnerability ID
        package: Affected package
        message: Vulnerability description
    """
    annotation = f"::error file={filename}::" f"[Trivy {severity}] {package} - {vuln_id}: {message}"
    print(annotation, flush=True)


def annotate_findings(report: Dict[str, Any], min_severity: str = "HIGH") -> int:
    """Parse Trivy report and emit GitHub annotations for findings.

    Args:
        report: Parsed Trivy JSON report
        min_severity: Minimum severity to annotate (CRITICAL, HIGH, or MEDIUM)

    Returns:
        Number of findings annotated
    """
    severity_order = {"MEDIUM": 0, "HIGH": 1, "CRITICAL": 2}
    min_level = severity_order.get(min_severity.upper(), 1)

    results: List[Dict[str, Any]] = report.get("Results", [])
    count = 0

    for result in results:
        target = result.get("Target", "unknown")

        # Process vulnerabilities
        vulns: List[Dict[str, Any]] = result.get("Vulnerabilities") or []
        for vuln in vulns:
            severity = vuln.get("Severity", "UNKNOWN").upper()
            severity_level = severity_order.get(severity, 0)

            if severity_level < min_level:
                continue

            vuln_id = vuln.get("VulnerabilityID", "UNKNOWN")
            pkg_name = vuln.get("PkgName", "unknown")
            title = vuln.get("Title", "Vulnerability detected")

            # Truncate long titles
            if len(title) > 150:
                title = title[:147] + "..."

            emit_github_error(target, severity, vuln_id, pkg_name, title)
            count += 1

        # Process misconfigurations
        misconfigs: List[Dict[str, Any]] = result.get("Misconfigurations") or []
        for misconfig in misconfigs:
            severity = misconfig.get("Severity", "UNKNOWN").upper()
            severity_level = severity_order.get(severity, 0)

            if severity_level < min_level:
                continue

            misconfig_id = misconfig.get("ID", "UNKNOWN")
            title = misconfig.get("Title", "Misconfiguration detected")

            # Truncate long titles
            if len(title) > 150:
                title = title[:147] + "..."

            emit_github_error(target, severity, misconfig_id, "config", title)
            count += 1

        # Process secrets
        secrets: List[Dict[str, Any]] = result.get("Secrets") or []
        for secret in secrets:
            rule_id = secret.get("RuleID", "UNKNOWN")
            title = secret.get("Title", "Secret detected")
            line = secret.get("StartLine", 0)

            # Secrets are always CRITICAL
            annotation = (
                f"::error file={target},line={line}::"
                f"[Trivy CRITICAL] Secret - {rule_id}: {title}"
            )
            print(annotation, flush=True)
            count += 1

    return count


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if len(sys.argv) < 2:
        print("Usage: annotate-trivy-findings.py <trivy-report.json>", file=sys.stderr)
        return 1

    report_path = sys.argv[1]
    min_severity = sys.argv[2] if len(sys.argv) > 2 else "HIGH"

    try:
        report = load_trivy_report(report_path)
        count = annotate_findings(report, min_severity)

        print(f"\n📊 Annotated {count} Trivy finding(s)", flush=True)
        return 0

    except FileNotFoundError as e:
        print(f"::error::{e}", flush=True)
        return 1
    except json.JSONDecodeError as e:
        print(f"::error::Invalid JSON in Trivy report: {e}", flush=True)
        return 1
    except Exception as e:
        print(f"::error::Error processing Trivy report: {e}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
