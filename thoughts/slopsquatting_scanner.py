"""
Slopsquatting Scanner (Step 9)

AI models sometimes hallucinate package names — attackers register these
fake names with malicious code ("slopsquatting" / dependency confusion).

This scanner:
  1. Extracts import/require statements from AI-generated code snippets or text files
  2. Checks each package name against PyPI (Python) and npm (JS)
  3. Flags unknown packages as potentially dangerous
  4. Checks for typosquat patterns against a known-safe allowlist

Usage:
    python slopsquatting_scanner.py --file ai_output.txt [--lang python|node|auto]

Install dependency (optional, for faster checks):
    pip install requests
"""

import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass

# ---------------------------------------------------------------------------
# ANSI colors
# ---------------------------------------------------------------------------
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ---------------------------------------------------------------------------
# Import extraction patterns
# ---------------------------------------------------------------------------
PYTHON_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+([a-zA-Z0-9_\-]+)",
    re.MULTILINE,
)
NODE_IMPORT_RE = re.compile(
    r"""(?:require\s*\(\s*['"]|from\s+['"])([a-zA-Z0-9@][a-zA-Z0-9_\-./]*)['"]""",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Known-safe stdlib modules (Python) — skip these
# ---------------------------------------------------------------------------
PYTHON_STDLIB = {
    "os", "sys", "re", "json", "math", "time", "datetime", "pathlib",
    "collections", "itertools", "functools", "typing", "abc", "io",
    "hashlib", "hmac", "base64", "urllib", "http", "socket", "ssl",
    "threading", "multiprocessing", "subprocess", "shutil", "tempfile",
    "logging", "unittest", "argparse", "dataclasses", "enum", "copy",
    "random", "string", "struct", "csv", "xml", "html", "email",
    "contextlib", "textwrap", "pprint", "ast", "dis", "inspect",
    "traceback", "warnings", "gc", "weakref", "signal", "platform",
    "uuid", "decimal", "fractions", "statistics", "array", "queue",
    "asyncio", "concurrent", "pickle", "shelve", "sqlite3", "zipfile",
    "tarfile", "gzip", "bz2", "lzma", "zlib", "binascii",
}

# Known-safe Node builtins
NODE_BUILTIN = {
    "fs", "path", "os", "http", "https", "url", "crypto", "stream",
    "events", "util", "child_process", "cluster", "net", "dns",
    "readline", "buffer", "assert", "console", "process", "timers",
    "vm", "module", "querystring", "zlib", "string_decoder",
}

# ---------------------------------------------------------------------------
# Typosquat similarity check (Levenshtein distance ≤ 2 against popular packages)
# ---------------------------------------------------------------------------
POPULAR_PACKAGES = [
    "requests", "numpy", "pandas", "flask", "django", "fastapi",
    "sqlalchemy", "boto3", "pytest", "click", "pydantic", "httpx",
    "aiohttp", "celery", "redis", "pillow", "matplotlib", "scikit-learn",
    "tensorflow", "torch", "transformers", "openai", "anthropic",
    "langchain", "psycopg2", "faker", "loguru", "typer",
]


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        return levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def is_typosquat(pkg: str) -> Optional[str]:
    for known in POPULAR_PACKAGES:
        dist = levenshtein(pkg.lower(), known.lower())
        if 0 < dist <= 2:
            return known
    return None


# ---------------------------------------------------------------------------
# PyPI existence check
# ---------------------------------------------------------------------------
def check_pypi(package: str) -> bool:
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "slopsquatting-scanner/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404
    except Exception:
        return None  # Network error → unknown


def check_npm(package: str) -> bool:
    url = f"https://registry.npmjs.org/{package}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "slopsquatting-scanner/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
@dataclass
class PackageResult:
    package: str
    lang: str
    exists: Optional[bool]
    is_stdlib: bool
    typosquat_of: Optional[str]
    risk: str  # "safe" | "warning" | "danger" | "unknown"
    message: str


def analyze_package(pkg: str, lang: str) -> PackageResult:
    if lang == "python" and pkg in PYTHON_STDLIB:
        return PackageResult(pkg, lang, True, True, None, "safe", "Standard library")
    if lang == "node" and pkg in NODE_BUILTIN:
        return PackageResult(pkg, lang, True, True, None, "safe", "Node.js builtin")

    typo = is_typosquat(pkg)
    if typo:
        return PackageResult(pkg, lang, None, False, typo,
                             "danger",
                             f"Possible typosquat of '{typo}' — do NOT install!")

    # Check registry
    exists = check_pypi(pkg) if lang == "python" else check_npm(pkg)
    time.sleep(0.2)  # rate-limit courtesy

    if exists is True:
        return PackageResult(pkg, lang, True, False, None, "safe", "Found in registry")
    elif exists is False:
        return PackageResult(pkg, lang, False, False, None,
                             "danger",
                             "Package NOT found in registry — AI hallucination or slopsquat!")
    else:
        return PackageResult(pkg, lang, None, False, None,
                             "unknown",
                             "Registry check failed (network error)")


def extract_packages(text: str, lang: str) -> list[str]:
    if lang == "python":
        matches = PYTHON_IMPORT_RE.findall(text)
    elif lang == "node":
        matches = NODE_IMPORT_RE.findall(text)
        matches = [m for m in matches if not m.startswith(".")]  # skip relative imports
    else:
        matches = PYTHON_IMPORT_RE.findall(text) + [
            m for m in NODE_IMPORT_RE.findall(text) if not m.startswith(".")
        ]
    return list(dict.fromkeys(matches))  # deduplicate, preserve order


def detect_lang(text: str) -> str:
    py_score  = len(PYTHON_IMPORT_RE.findall(text))
    js_score  = len(NODE_IMPORT_RE.findall(text))
    return "python" if py_score >= js_score else "node"


def print_result(r: PackageResult) -> None:
    if r.risk == "safe":
        color, icon = GREEN, "OK "
    elif r.risk == "danger":
        color, icon = RED,   "!! "
    elif r.risk == "warning":
        color, icon = YELLOW,"!  "
    else:
        color, icon = YELLOW,"?  "

    print(f"  {color}{BOLD}[{icon}]{RESET} {color}{r.package:<30}{RESET} {r.message}")


def main(file_path: Path, lang: str = "auto") -> int:
    text = file_path.read_text(errors="replace")
    if lang == "auto":
        lang = detect_lang(text)

    packages = extract_packages(text, lang)
    if not packages:
        print("No import statements found.")
        return 0

    print(f"{BOLD}=== Slopsquatting Scanner ==={RESET}")
    print(f"File : {file_path}")
    print(f"Lang : {lang}")
    print(f"Pkgs : {len(packages)} found\n")
    print("Checking registry...\n")

    results = [analyze_package(pkg, lang) for pkg in packages]
    for r in results:
        print_result(r)

    dangerous = [r for r in results if r.risk == "danger"]
    print(f"\n{len(dangerous)} dangerous package(s) detected out of {len(results)}.")

    out_path = Path("slopsquat_report.jsonl")
    with out_path.open("w") as f:
        for r in results:
            f.write(json.dumps(asdict(r)) + "\n")
    print(f"Full report: {out_path}")

    return 1 if dangerous else 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect hallucinated/malicious packages in AI output")
    parser.add_argument("--file", required=True, help="File containing AI-generated code or text")
    parser.add_argument("--lang", default="auto", choices=["auto", "python", "node"])
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    sys.exit(main(path, lang=args.lang))
