"""
Secrets & Critical-Content Scanner (Step 6 / Key Feature)

Scans every log entry's text fields for leaked secrets, API keys,
credentials, and other critical content.

On a match:
  - Prints a RED alert to the terminal (with !! prefix)
  - Writes flagged entries to flagged_secrets.jsonl for dashboard display
  - (Optional) sends a webhook notification to alert the source

Usage:
    python secrets_scanner.py [--file logs.jsonl] [--webhook-url URL]

Exit code: 0 = clean, 1 = secrets found.
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import urllib.request
except ImportError:
    pass

# ---------------------------------------------------------------------------
# ANSI colors (terminal output)
# ---------------------------------------------------------------------------
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ---------------------------------------------------------------------------
# Secret pattern library
# ---------------------------------------------------------------------------
@dataclass
class SecretPattern:
    name: str
    pattern: re.Pattern
    severity: str  # "critical" | "high" | "medium"
    advice: str


PATTERNS: list[SecretPattern] = [
    SecretPattern(
        name="AWS Secret Access Key",
        pattern=re.compile(r"(?i)aws_secret_access_key\s*[=:]\s*[A-Za-z0-9/+]{40}"),
        severity="critical",
        advice="Rotate this AWS secret key immediately at https://console.aws.amazon.com/iam/",
    ),
    SecretPattern(
        name="AWS Access Key ID",
        pattern=re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}\b"),
        severity="critical",
        advice="Rotate this AWS Access Key ID immediately.",
    ),
    SecretPattern(
        name="Generic API Key",
        pattern=re.compile(r"(?i)(api[_\-]?key|apikey)\s*[=:\"']\s*[A-Za-z0-9\-_]{20,}"),
        severity="high",
        advice="Revoke and regenerate this API key.",
    ),
    SecretPattern(
        name="Private Key (PEM)",
        pattern=re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        severity="critical",
        advice="This is a private key — do NOT share it. Revoke and regenerate immediately.",
    ),
    SecretPattern(
        name="GitHub Token",
        pattern=re.compile(r"ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}"),
        severity="critical",
        advice="Revoke this GitHub token at https://github.com/settings/tokens",
    ),
    SecretPattern(
        name="OpenAI API Key",
        pattern=re.compile(r"sk-[A-Za-z0-9]{20,}"),
        severity="critical",
        advice="Revoke this OpenAI key at https://platform.openai.com/api-keys",
    ),
    SecretPattern(
        name="Slack Token",
        pattern=re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
        severity="high",
        advice="Revoke this Slack token at https://api.slack.com/apps",
    ),
    SecretPattern(
        name="Password in plaintext",
        pattern=re.compile(r"(?i)(password|passwd|pwd)\s*[=:\"']\s*\S{6,}"),
        severity="high",
        advice="Never include plaintext passwords in prompts or logs.",
    ),
    SecretPattern(
        name="Database connection string",
        pattern=re.compile(r"(?i)(postgres|mysql|mongodb|redis)://[^\s\"']+:[^\s\"'@]+@"),
        severity="critical",
        advice="Rotate database credentials. Use environment variables instead.",
    ),
    SecretPattern(
        name="JWT Token",
        pattern=re.compile(r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
        severity="high",
        advice="JWTs may contain sensitive claims — invalidate this token.",
    ),
    SecretPattern(
        name="IP Address (internal)",
        pattern=re.compile(r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
        severity="medium",
        advice="Internal IP addresses can reveal network topology.",
    ),
    SecretPattern(
        name="Email address",
        pattern=re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
        severity="medium",
        advice="Remove or hash email addresses before sending to LLM providers.",
    ),
    SecretPattern(
        name="IBAN",
        pattern=re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7,}(?:[A-Z0-9]{0,3})\b"),
        severity="high",
        advice="Bank account numbers must not appear in LLM prompts.",
    ),
]

# ---------------------------------------------------------------------------
# Custom company keyword patterns (extend as needed)
# ---------------------------------------------------------------------------
COMPANY_KEYWORDS: list[re.Pattern] = [
    re.compile(r"(?i)\bprojekt[_\-\s]?(alpha|beta|geheim|intern|confidential)\b"),
    re.compile(r"(?i)\b(streng\s+)?vertraulich\b"),
    re.compile(r"(?i)\btop\s+secret\b"),
]

TEXT_FIELDS = ["purpose", "prompt", "content", "message", "text", "query"]


@dataclass
class Finding:
    line_num: int
    record_id: str
    field: str
    pattern_name: str
    severity: str
    advice: str
    snippet: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def scan_value(value: str, field_name: str, line_num: int, record_id: str) -> list[Finding]:
    findings = []
    for sp in PATTERNS:
        match = sp.pattern.search(value)
        if match:
            snippet = value[max(0, match.start() - 10): match.end() + 10]
            findings.append(Finding(
                line_num=line_num,
                record_id=record_id,
                field=field_name,
                pattern_name=sp.name,
                severity=sp.severity,
                advice=sp.advice,
                snippet=f"...{snippet}...",
            ))
    for kw_pattern in COMPANY_KEYWORDS:
        match = kw_pattern.search(value)
        if match:
            snippet = value[max(0, match.start() - 10): match.end() + 10]
            findings.append(Finding(
                line_num=line_num,
                record_id=record_id,
                field=field_name,
                pattern_name="Company Confidential Keyword",
                severity="high",
                advice="This content may be confidential — do not send to external LLM providers.",
                snippet=f"...{snippet}...",
            ))
    return findings


def scan_record(record: dict, line_num: int) -> list[Finding]:
    record_id = str(record.get("id", f"line-{line_num}"))
    findings = []
    for key, value in record.items():
        if isinstance(value, str):
            findings.extend(scan_value(value, key, line_num, record_id))
    return findings


def print_finding(f: Finding) -> None:
    color = RED if f.severity == "critical" else YELLOW
    icon = "!!" if f.severity == "critical" else "! "
    print(f"{color}{BOLD}[{icon} {f.severity.upper()}]{RESET} {color}Line {f.line_num} | id={f.record_id}{RESET}")
    print(f"       Pattern : {f.pattern_name}")
    print(f"       Field   : {f.field}")
    print(f"       Snippet : {f.snippet}")
    print(f"       Action  : {f.advice}")
    print()


def send_webhook(url: str, finding: Finding) -> None:
    payload = json.dumps({
        "text": (
            f":rotating_light: *{finding.severity.upper()} SECRET DETECTED* :rotating_light:\n"
            f"*Pattern:* {finding.pattern_name}\n"
            f"*Record:* `{finding.record_id}` (field: `{finding.field}`)\n"
            f"*Action:* {finding.advice}"
        )
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"  [webhook] Failed to notify: {e}")


def scan_file(path: Path) -> list[Finding]:
    all_findings = []
    with path.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            all_findings.extend(scan_record(record, line_num))
    return all_findings


def write_flagged(findings: list[Finding], out_path: Path) -> None:
    with out_path.open("w") as f:
        for finding in findings:
            f.write(json.dumps(asdict(finding), ensure_ascii=False) + "\n")


def main(file_path: Path, webhook_url: Optional[str] = None) -> int:
    print(f"{BOLD}=== Secrets Scanner ==={RESET}")
    print(f"Scanning: {file_path}\n")

    findings = scan_file(file_path)

    if not findings:
        print("No secrets or critical content detected.")
        return 0

    critical = [f for f in findings if f.severity == "critical"]
    high     = [f for f in findings if f.severity == "high"]
    medium   = [f for f in findings if f.severity == "medium"]

    print(f"{RED}{BOLD}Found {len(findings)} issue(s): "
          f"{len(critical)} critical, {len(high)} high, {len(medium)} medium{RESET}\n")

    for finding in findings:
        print_finding(finding)
        if webhook_url and finding.severity in ("critical", "high"):
            send_webhook(webhook_url, finding)

    out_path = Path("flagged_secrets.jsonl")
    write_flagged(findings, out_path)
    print(f"Flagged entries written to: {out_path}")
    print("(Dashboard: show these in red sidebar with !! icon)")

    return 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scan logs for leaked secrets and critical content")
    parser.add_argument("--file", default="logs.jsonl")
    parser.add_argument("--webhook-url", help="Slack/Teams webhook URL for critical alerts")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    sys.exit(main(path, webhook_url=args.webhook_url))
