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
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

# Rate limiting: delay between issue creations to avoid API throttling
ISSUE_CREATE_DELAY_SECONDS = 2

# Content sanitization limits to prevent injection and oversized issues
MAX_FIELD_LENGTH = 2000
MAX_ADVISORY_LENGTH = 5000


def get_repository_name() -> str:
    """
    Get the current repository name from environment or fallback.

    Returns:
        Repository name in 'owner/repo' format
    """
    # GitHub Actions provides GITHUB_REPOSITORY env var in 'owner/repo' format
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo:
        return repo.split("/")[-1]  # Extract just repo name
    return "concept-model-protein-classifier"  # Fallback for local testing


def sanitize_text(
    text: str, max_length: int = MAX_FIELD_LENGTH, allow_newlines: bool = False
) -> str:
    """
    Sanitize text to prevent markdown/control-character injection.

    Removes control characters (except newlines if allowed) and enforces
    length limits to prevent oversized issue bodies.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        allow_newlines: Whether to preserve newline characters

    Returns:
        Sanitized text string
    """
    if not isinstance(text, str):
        text = str(text)

    # Remove control characters except newlines if allowed
    if allow_newlines:
        # Keep newlines, remove other control chars (ASCII 0-31 except \n and \r)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    else:
        # Remove all control characters including newlines
        text = re.sub(r"[\x00-\x1f\x7f]", "", text)

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"

    return text


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
    # Check if scan failures should be skipped (for CI flexibility)
    skip_failures = os.environ.get("SKIP_VULN_SCAN_FAILURES", "").lower() in [
        "true",
        "1",
        "yes",
    ]
    exit_code = 0 if skip_failures else 1

    try:
        with open(scan_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        print(
            f"Error reading vulnerability scan results from {scan_file}: "
            f"{exc}. Ensure the Safety CLI scan step completed successfully "
            "and produced a valid JSON file."
        )
        sys.exit(exit_code)
    except json.JSONDecodeError as exc:
        print(
            f"Error parsing JSON from {scan_file}: {exc}. "
            "The scan file may be corrupted or invalid."
        )
        sys.exit(exit_code)


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
                "security,automated",
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
    # Sanitize all fields to prevent injection and control character issues
    cve_id = sanitize_text(vulnerability.get("CVE") or vulnerability.get("vulnerability_id", "N/A"))
    current_version = sanitize_text(vulnerability.get("analyzed_version", "unknown"))
    severity = sanitize_text(vulnerability.get("severity", "unknown"))
    package = sanitize_text(package)
    fix_version = sanitize_text(fix_version)

    # Advisory allows newlines but has larger max length and is sanitized
    advisory = sanitize_text(
        vulnerability.get("advisory", "No description available"),
        max_length=MAX_ADVISORY_LENGTH,
        allow_newlines=True,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Use explicit f-string for better readability
    action_line_1 = (
        f"1. Update the version constraint to a compatible range "
        f"(for example `~={fix_version}` or an upper-bounded range) "
        f"to allow security patches without unexpected breaking changes"
    )
    action_line_2 = "2. Run the test suite to ensure compatibility"
    action_line_3 = "3. Open a PR with the changes"
    action_line_4 = "4. Include a closing reference to this issue in the PR description"

    # Make repository name configurable for reusability
    repo_name = get_repository_name()
    safety_url = f"https://platform.safetycli.com/codebases/{repo_name}/findings"

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
{action_line_1}
{action_line_2}
{action_line_3}
{action_line_4}

### 📊 References
- **CVE Details:** https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}
- **Safety Report:** {safety_url}

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
        try:
            with open(summary_file, "a", encoding="utf-8") as file:
                file.write("## Security Scan Summary\n\n")
                file.write(f"- **Total vulnerabilities found:** {total_vulns}\n")
                file.write(f"- **Issues created:** {issues_created}\n")
                file.write(f"- **Issues skipped:** {total_vulns - issues_created}\n\n")
        except (OSError, IOError) as exc:
            # Log error but don't crash - summary is non-critical
            print(
                f"Warning: Failed to write workflow summary to {summary_file}: "
                f"{exc}. Continuing without summary output."
            )


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
        # Validate that the entry is a dictionary
        if not isinstance(vuln, dict):
            print(
                f"Warning: Skipping malformed vulnerability entry "
                f"(expected dict, got {type(vuln).__name__})"
            )
            continue

        # Check for required fields
        package = vuln.get("package_name")
        if not package:
            print("Warning: Skipping vulnerability entry without 'package_name' field")
            continue

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

            # Rate limiting: Add delay between issue creations to avoid
            # GitHub API throttling (secondary rate limits)
            time.sleep(ISSUE_CREATE_DELAY_SECONDS)
        except subprocess.CalledProcessError as exc:
            print(f"❌ Failed to create issue for {package}: {exc}")

    print(f"\nSummary: Created {issues_created} security issue(s)")
    write_workflow_summary(issues_created, total_medium_plus)


if __name__ == "__main__":
    main()
