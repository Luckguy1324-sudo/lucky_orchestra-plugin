#!/usr/bin/env python3
"""
score_check.py — strict validator for Stage 5 review files.

Outputs to stdout (one line):
  <effective_decision> <score>

Where effective_decision is one of:
  PASS        — verdict=PASS, score >= threshold, must_fix empty, not partial
  REVISE      — verdict=REVISE, OR PASS-but-below-threshold, OR PASS-with-must_fix
  RESTART     — verdict=RESTART
  PARTIAL     — partial: true in frontmatter or YAML block (retry same round)
  PASS_WITH_WARNINGS — REVISE but round >= max_rounds (forced finalize)
  PARSE_ERROR — could not parse YAML or required fields missing

This script enforces self-consistency that the raw model output can violate:
  - Reviewer claims PASS but score < threshold → escalate to REVISE
  - Reviewer claims PASS but must_fix non-empty → escalate to REVISE
  - Reviewer claims REVISE but must_fix empty → warn, keep as REVISE
  - reviewer-bridge marked partial=true in frontmatter → PARTIAL verdict wins

Exit codes:
  0 — decision computed
  1 — file missing or unreadable
  2 — parse error
"""
import argparse
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> dict:
    """Return dict from YAML frontmatter block at top of file, or empty dict."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fm_lines = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)

    out = {}
    for line in fm_lines:
        m = re.match(r"^\s*([a-zA-Z_][\w]*)\s*:\s*(.+)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        out[key] = value.strip("'\"")
    return out


def extract_yaml_block(text: str) -> str | None:
    """Return contents of the first ```yaml ... ``` fenced block."""
    in_block = False
    out = []
    for line in text.splitlines():
        if not in_block and line.strip().startswith("```yaml"):
            in_block = True
            continue
        if in_block and line.strip().startswith("```"):
            return "\n".join(out)
        if in_block:
            out.append(line)
    return "\n".join(out) if out else None


def parse_review_yaml(yaml_text: str) -> dict | None:
    """Parse review YAML — prefer PyYAML, else minimal parser."""
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(yaml_text)
        return data if isinstance(data, dict) else None
    except ImportError:
        return parse_minimal_review(yaml_text)


def parse_minimal_review(yaml_text: str) -> dict:
    out: dict = {}
    current_list_key = None
    for raw_line in yaml_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if current_list_key and (line.startswith("  - ") or line.startswith("- ")):
            item = line.split("- ", 1)[1].strip().strip("'\"")
            out.setdefault(current_list_key, []).append(item)
            continue
        m = re.match(r"^([a-zA-Z_][\w]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2).strip()
        if not value:
            current_list_key = key
            out[key] = []
            continue

        # Inline list: [], ["x"], ["x", "y"]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            current_list_key = None
            if not inner:
                out[key] = []
            else:
                items = [s.strip().strip("'\"") for s in inner.split(",")]
                out[key] = [s for s in items if s]
            continue

        current_list_key = None
        out[key] = value.strip("'\"")
    return out


def to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"true", "yes", "1"}


def to_float(v) -> float:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return -1.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review_file")
    parser.add_argument("--pass-threshold", type=float, default=8.0)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--max-rounds", type=int, default=3)
    args = parser.parse_args()

    path = Path(args.review_file)
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    # If bridge already flagged partial in frontmatter, that wins.
    if to_bool(fm.get("partial", "false")):
        print(f"PARTIAL 0")
        return 0

    yaml_text = extract_yaml_block(text)
    if not yaml_text:
        print("PARSE_ERROR 0")
        return 2

    review = parse_review_yaml(yaml_text)
    if not review:
        print("PARSE_ERROR 0")
        return 2

    raw_verdict = str(review.get("verdict", "")).strip().upper()
    if raw_verdict not in {"PASS", "REVISE", "RESTART"}:
        print("PARSE_ERROR 0")
        return 2

    score = to_float(review.get("score", -1))
    must_fix = review.get("must_fix", [])
    if not isinstance(must_fix, list):
        must_fix = [must_fix]
    has_must_fix = any(bool(str(x).strip()) for x in must_fix)

    score_str = f"{score:.1f}" if score >= 0 else "0"

    # PARTIAL flag inside YAML block also recognized
    if to_bool(review.get("partial", False)):
        print(f"PARTIAL {score_str}")
        return 0

    # Self-consistency enforcement
    if raw_verdict == "PASS":
        if score < args.pass_threshold:
            print(f"REVISE {score_str}", file=sys.stderr)
            print(f"REVISE {score_str}")
            return 0
        if has_must_fix:
            print(f"REVISE {score_str}")
            return 0
        print(f"PASS {score_str}")
        return 0

    if raw_verdict == "REVISE":
        if args.round >= args.max_rounds:
            print(f"PASS_WITH_WARNINGS {score_str}")
            return 0
        print(f"REVISE {score_str}")
        return 0

    if raw_verdict == "RESTART":
        print(f"RESTART {score_str}")
        return 0

    print("PARSE_ERROR 0")
    return 2


if __name__ == "__main__":
    sys.exit(main())
