#!/usr/bin/env python3
"""
build-provenance.py — generate a Provenance section for orchestra's final.md

Reads the run directory (meta.json + 01-brief.md frontmatter + 05-review-v*.md
frontmatter) and prints a self-documenting markdown section to stdout. The
Conductor appends this to final.md after copying the winning draft.

Usage:
  build-provenance.py <run-dir> [--plugin-version 0.4.0]

Output (stdout, ready to append):
  Markdown section starting with `## Provenance` and ending with a blank line.

Why this exists:
  - Reviewers, future-you, and other AI agents can read final.md and know
    EXACTLY what produced it: rounds, scores, verdicts, models used, refs.
  - Removes "magic black box" feel — every claim has a trail.
  - Safe to run multiple times; output is deterministic given the same inputs.

Exit codes:
  0 — provenance generated
  1 — run-dir missing or unreadable
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    body_lines = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body_lines.append(line)
    body = "\n".join(body_lines)
    try:
        import yaml  # type: ignore
        d = yaml.safe_load(body)
        return d if isinstance(d, dict) else {}
    except ImportError:
        return parse_minimal_yaml(body)


def parse_minimal_yaml(text: str) -> dict:
    out: dict = {}
    current_list_key = None
    current_dict_key = None
    current_dict = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # List of dicts entry: "  - id: r1"
        if current_list_key and re.match(r"^\s*-\s+\w+\s*:", line):
            current_dict = {}
            out.setdefault(current_list_key, []).append(current_dict)
            m = re.match(r"^\s*-\s+(\w+)\s*:\s*(.*)$", line)
            if m:
                current_dict[m.group(1)] = m.group(2).strip().strip("'\"")
            current_dict_key = None
            continue
        # Continued key in current dict: "    source: ./x"
        if current_dict is not None and re.match(r"^\s{4,}\w+\s*:", line):
            m = re.match(r"^\s+(\w+)\s*:\s*(.*)$", line)
            if m:
                current_dict[m.group(1)] = m.group(2).strip().strip("'\"")
            continue
        # Simple list item
        if current_list_key and re.match(r"^\s*-\s+", line):
            item = re.sub(r"^\s*-\s+", "", line).strip().strip("'\"")
            out.setdefault(current_list_key, []).append(item)
            continue
        m = re.match(r"^(\w+)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if not value:
            current_list_key = key
            current_dict = None
            out[key] = []
        else:
            current_list_key = None
            current_dict = None
            # Inline list: [], ["x", "y"]
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                out[key] = [
                    s.strip().strip("'\"") for s in inner.split(",") if s.strip()
                ] if inner else []
            else:
                out[key] = value.strip("'\"")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", help="Path to .orchestra/runs/<run-id>/")
    parser.add_argument("--plugin-version", default="unknown")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"run-dir not found: {run_dir}", file=sys.stderr)
        return 1

    meta_path = run_dir / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    brief_path = run_dir / "01-brief.md"
    brief_fm = {}
    if brief_path.exists():
        brief_fm = parse_frontmatter(brief_path.read_text(encoding="utf-8"))

    review_files = sorted(run_dir.glob("05-review-v*.md"))
    review_meta = []
    for rf in review_files:
        fm = parse_frontmatter(rf.read_text(encoding="utf-8"))
        review_meta.append({
            "round": fm.get("round", "?"),
            "model": fm.get("model", "?"),
            "verdict": fm.get("verdict", "?"),
            "score": fm.get("score", "?"),
            "partial": str(fm.get("partial", "false")).lower() == "true",
            "file": rf.name,
        })

    research_dir = run_dir / "03-research"
    research_files = sorted(research_dir.glob("*.md")) if research_dir.is_dir() else []

    draft_files = sorted(run_dir.glob("04-draft-v*.md"))

    out_lines = []
    out_lines.append("")
    out_lines.append("---")
    out_lines.append("")
    out_lines.append("## Provenance")
    out_lines.append("")
    out_lines.append(f"Generated by `orchestra` plugin v{args.plugin_version} on "
                     f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} local time.")
    out_lines.append("")

    out_lines.append("### Pipeline summary")
    out_lines.append("")
    out_lines.append(f"- **run_id**: `{meta.get('run_id', run_dir.name)}`")
    out_lines.append(f"- **started_at**: `{meta.get('started_at', 'unknown')}`")
    out_lines.append(f"- **total rounds**: {meta.get('round', '?')}")
    out_lines.append(f"- **max_rounds**: {brief_fm.get('max_rounds', '?')}")
    out_lines.append(f"- **pass_threshold**: {brief_fm.get('pass_threshold', '8.0 (default)')}")
    out_lines.append("")

    out_lines.append("### Models")
    out_lines.append("")
    out_lines.append(f"- **Stage 2 (Plan Research)**: ChatGPT `{brief_fm.get('stage2_model', '?')}`")
    out_lines.append(f"- **Stage 3 (Research)**: Claude Code (research-worker subagent) × {len(research_files)} performer(s)")
    out_lines.append(f"- **Stage 4 (Synthesize)**: Claude Code (Conductor)")
    out_lines.append(f"- **Stage 5 (Review)**: ChatGPT `{brief_fm.get('stage5_model', '?')}`")
    out_lines.append("")

    out_lines.append("### Round history")
    out_lines.append("")
    if review_meta:
        out_lines.append("| Round | Model | Verdict | Score | Partial |")
        out_lines.append("|-------|-------|---------|-------|---------|")
        for r in review_meta:
            out_lines.append(
                f"| {r['round']} | `{r['model']}` | "
                f"{r['verdict']} | {r['score']} | {r['partial']} |"
            )
    else:
        out_lines.append("(no review files found)")
    out_lines.append("")

    refs = brief_fm.get("references", []) or []
    out_lines.append("### Reference materials")
    out_lines.append("")
    if refs and isinstance(refs, list):
        for ref in refs:
            if isinstance(ref, dict):
                rid = ref.get("id", "?")
                source = ref.get("source", "?")
                summary = ref.get("summary", "")
                out_lines.append(f"- **{rid}** `{source}` — {summary}")
            else:
                out_lines.append(f"- {ref}")
    else:
        out_lines.append("(none)")
    out_lines.append("")

    out_lines.append("### Files produced (relative to run dir)")
    out_lines.append("")
    out_lines.append("```")
    interesting = [
        "01-brief.md",
        "02-research-plan.md",
    ]
    for f in interesting:
        if (run_dir / f).exists():
            out_lines.append(f)
    if research_files:
        out_lines.append("03-research/")
        for rf in research_files:
            out_lines.append(f"  {rf.name}")
    for df in draft_files:
        out_lines.append(df.name)
    for rv in review_files:
        out_lines.append(rv.name)
    if (run_dir / "_refs").is_dir():
        out_lines.append("_refs/")
    out_lines.append("final.md   <-- this file")
    out_lines.append("meta.json")
    out_lines.append("```")
    out_lines.append("")

    out_lines.append("### Reproducibility note")
    out_lines.append("")
    out_lines.append(
        "ChatGPT responses are not deterministic — re-running this orchestra "
        "run with the same brief and references will produce similar but not "
        "identical output. The artifacts in this run directory are the "
        "authoritative record."
    )
    out_lines.append("")

    sys.stdout.write("\n".join(out_lines))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
