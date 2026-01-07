#!/usr/bin/env python3
"""
Security Issue Automation Script.

Parses Safety CLI vulnerability scan results and creates GitHub issues for
medium+ severity vulnerabilities with automated remediation instructions.

This script is designed to be run in GitHub Actions workflows and requires
the GitHub CLI (gh) to be available in the environment.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


def read_vulnerability_data(scan_file: Path) -> Dict[str, Any]:
    """
    Read and parse vulnerability scan results from JSON file.

    Args:
        scan_file: Path to the vulnerability scan JSON file

    Returns:
        Dictionary containing vulnerability scan data

    Raises:
        SystemExit: If file cannot be read or parsed
    """
    try:
        with open(scan_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        print(
            f"Error reading vulnerability scan results from {scan_file}: "
            f"{exc}. Ensure the Safety CLI scan step completed successfully "
            "and produced a valid JSON file."
        )
        sys.exit(0)
    except json.JSONDecodeError as exc:
        print(
            f"Error parsing JSON from {scan_file}: {exc}. "
            "The scan file may be corrupted or invalid."
        )
        sys.exit(0)


def get_existing_security_issues() -> Set[str]:
    """
    Fetch existing security issues to prevent duplicates.

    Returns:
        Set of existing issue titles

    Note:
        If fetching fails, returns empty set to allow issue creation to proceed
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--label",
                "security",
                "--label",
                "automated",
                "--json",
                "title",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        existing_issues: List[Dict[str, str]] = json.loads(result.stdout)
        return {issue["title"] for issue in existing_issues}
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(
            f"Error fetching existing issues: {exc}. Duplicate issue "
            "detection will be skipped; proceeding as if no existing "
            "security issues are present."
        )
        return set()


def determine_fix_version(vulnerability: Dict[str, Any]) -> str:
    """
    Determine the recommended fix version from vulnerability data.

    Args:
        vulnerability: Vulnerability data dictionary

    Returns:
        Recommended version string or 'latest'
    """
    recommended_version = vulnerability.get("recommended_version")
    secure_versions = vulnerability.get("secure_versions")

    if recommended_version:
        return recommended_version
    if secure_versions:
        return secure_versions[0]
    return "latest"


def create_issue_body(vulnerability: Dict[str, Any], fix_version: str, package: str) -> str:
    """
    Generate the issue body content for a vulnerability.

    Args:
        vulnerability: Vulnerability data dictionary
        fix_version: Recommended version to fix the vulnerability
        package: Package name

    Returns:
        Formatted issue body as markdown string
    """
    cve_id = vulnerability.get("CVE") or vulnerability.get("vulnerability_id", "N/A")
    current_version = vulnerability.get("analyzed_version", "unknown")
    severity = vulnerability.get("severity", "unknown")
    advisory = vulnerability.get("advisory", "No description available")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    return f"""## 🔒 Security Vulnerability Detected

**Package:** `{package}`
**Current Version:** `{current_version}`
**Severity:** {severity.upper()}
**CVE:** {cve_id}

### 📋 CVE Description
{advisory}

### 🔧 Remediation
**Recommended action:** Upgrade to version `{fix_version}`

**Affected file:** `api/requirements.txt`

### 🤖 Action Required
Please update `{package}` to version `{fix_version}` in `api/requirements.txt`:
1. Update `{package}` to version `{fix_version}` in `api/requirements.txt`
2. Update the version constraint to a compatible range (for example \
`~={fix_version}` or an upper-bounded range) to allow security patches \
without unexpected breaking changes
3. Run the test suite to ensure compatibility
4. Open a PR with the changes
5. Include a closing reference to this issue in the PR description

### 📊 References
- **CVE Details:** https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}
- **Safety Report:** https://platform.safetycli.com/codebases/\
concept-model-protein-classifier/findings

---
*This issue was automatically created by the security automation system.*
*Last scanned: {timestamp} UTC*
"""


def create_github_issue(title: str, body: str, labels: List[str]) -> subprocess.CompletedProcess:
    """
    Create a GitHub issue using the gh CLI.

    Args:
        title: Issue title
        body: Issue body content
        labels: List of labels to apply

    Returns:
        CompletedProcess instance from subprocess.run

    Raises:
        subprocess.CalledProcessError: If gh CLI command fails
    """
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]

    # Add each label separately as required by gh CLI
    for label in labels:
        cmd.extend(["--label", label])

    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def should_create_issue(severity: str) -> bool:
    """
    Determine if an issue should be created based on severity.

    Args:
        severity: Severity level string

    Returns:
        True if issue should be created, False otherwise
    """
    return severity.lower() in ["medium", "high", "critical"]


def write_workflow_summary(issues_created: int, total_vulns: int) -> None:
    """
    Write workflow summary to GitHub Actions summary file.

    Args:
        issues_created: Number of issues created
        total_vulns: Total number of vulnerabilities found
    """
    summary_file = Path(os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null"))
    if summary_file != Path("/dev/null"):
        with open(summary_file, "a", encoding="utf-8") as file:
            file.write("## Security Scan Summary\n\n")
            file.write(f"- **Total vulnerabilities found:** {total_vulns}\n")
            file.write(f"- **Issues created:** {issues_created}\n")
            file.write(f"- **Issues skipped:** {total_vulns - issues_created}\n\n")


def main() -> None:
    """
    Main execution function.

    Reads vulnerability scan results, filters for medium+ severity issues,
    and creates GitHub issues for new vulnerabilities.
    """
    # Read vulnerability scan results
    scan_file = Path("vulns.json")
    data = read_vulnerability_data(scan_file)

    vulnerabilities: List[Dict[str, Any]] = data.get("vulnerabilities", [])

    if not vulnerabilities:
        print("No vulnerabilities found")
        sys.exit(0)

    # Get existing issues to avoid duplicates
    existing_titles = get_existing_security_issues()

    issues_created = 0
    total_medium_plus = 0

    # Process each vulnerability
    for vuln in vulnerabilities:
        package = vuln.get("package_name", "unknown")
        severity = vuln.get("severity", "unknown")

        # Only process medium or higher severity
        if not should_create_issue(severity):
            continue

        total_medium_plus += 1
        cve_id = vuln.get("CVE") or vuln.get("vulnerability_id", "N/A")
        title = f"[Security] Upgrade {package} to fix {cve_id}"

        # Skip if issue already exists
        if title in existing_titles:
            print(f"Issue already exists: {title}")
            continue

        # Determine fix version
        fix_version = determine_fix_version(vuln)

        # Create issue body
        body = create_issue_body(vuln, fix_version, package)

        # Create the issue
        labels = ["security", "automated", "dependency-upgrade"]
        try:
            create_github_issue(title, body, labels)
            print(f"✅ Created issue: {title}")
            issues_created += 1
        except subprocess.CalledProcessError as exc:
            print(f"❌ Failed to create issue for {package}: {exc}")

    print(f"\nSummary: Created {issues_created} security issue(s)")
    write_workflow_summary(issues_created, total_medium_plus)


if __name__ == "__main__":
    main()
