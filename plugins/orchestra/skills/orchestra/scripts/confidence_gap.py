#!/usr/bin/env python3
"""confidence_gap.py — Mechanism S4: confidence-gap scoring for research topics.

Concentrates research + reviewer effort where the plan is weakest, instead of spreading it
uniformly. Generic "improve the plan" padding is replaced by targeted deepening of the
top 2–5 topics by gap score.

Usage:
    confidence_gap.py <topics.json> [--top N] [--write <run-dir>]

topics.json shape (per topic, all flags optional booleans; defaults false):
[
  {
    "id": "t1",
    "title": "warm vs cryogenic suction trade-off",
    "signals": {
      "unstated_assumption": true,
      "no_source_cited": false,
      "novel_method": true,
      "conflicting_evidence": false,
      "quant_claim_no_derivation": true,
      "external_dependency": false,
      "ambiguous_success_criterion": false
    },
    "high_risk_domain": true,
    "critical_section": true
  }
]

gap_score = trigger_count(signals true) + risk_bonus(+2 if high_risk_domain)
            + critical_section_bonus(+2 if critical_section)

Prints a ranked table and marks the top N (default 5, capped at topic count) deepen=true.
With --write <run-dir>, merges id/gap_score/deepen into <run-dir>/meta.json topics[].
"""
import argparse
import json
import sys
from pathlib import Path

SIGNAL_KEYS = [
    "unstated_assumption",
    "no_source_cited",
    "novel_method",
    "conflicting_evidence",
    "quant_claim_no_derivation",
    "external_dependency",
    "ambiguous_success_criterion",
]


def score_topic(topic: dict) -> int:
    signals = topic.get("signals", {})
    trigger_count = sum(1 for k in SIGNAL_KEYS if signals.get(k))
    risk_bonus = 2 if topic.get("high_risk_domain") else 0
    critical_bonus = 2 if topic.get("critical_section") else 0
    return trigger_count + risk_bonus + critical_bonus


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("topics_json")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--write", default=None, help="run-dir whose meta.json to update")
    args = ap.parse_args()

    tp = Path(args.topics_json)
    if not tp.exists():
        print(f"ERROR: topics file not found: {tp}", file=sys.stderr)
        sys.exit(2)
    with tp.open(encoding="utf-8") as fh:
        topics = json.load(fh)
    if not isinstance(topics, list) or not topics:
        print("ERROR: topics.json must be a non-empty list", file=sys.stderr)
        sys.exit(2)

    for t in topics:
        t["gap_score"] = score_topic(t)

    ranked = sorted(topics, key=lambda t: t["gap_score"], reverse=True)
    top_n = min(args.top, len(ranked))
    deepen_ids = {t["id"] for t in ranked[:top_n]}
    for t in topics:
        t["deepen"] = t["id"] in deepen_ids

    print("=== Confidence-Gap Scoring (S4) ===")
    print(f"{'rank':<5}{'id':<8}{'gap':<5}{'deepen':<8}title")
    for i, t in enumerate(ranked, 1):
        print(f"{i:<5}{t['id']:<8}{t['gap_score']:<5}"
              f"{'YES' if t['deepen'] else '-':<8}{t.get('title','')}")
    print()
    print(f"→ Top {top_n} topic(s) marked deepen=true: {', '.join(sorted(deepen_ids))}")
    print("  These get richer research (Stage 3) and more reviewer attention (Stage 6).")

    if args.write:
        run_dir = Path(args.write)
        meta_path = run_dir / "meta.json"
        if not meta_path.exists():
            print(f"ERROR: {meta_path} not found for --write", file=sys.stderr)
            sys.exit(2)
        with meta_path.open(encoding="utf-8") as fh:
            meta = json.load(fh)
        meta["topics"] = [
            {"id": t["id"], "gap_score": t["gap_score"], "deepen": t["deepen"]}
            for t in topics
        ]
        with meta_path.open("w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)
        print(f"  Wrote topics[] into {meta_path}")


if __name__ == "__main__":
    main()
