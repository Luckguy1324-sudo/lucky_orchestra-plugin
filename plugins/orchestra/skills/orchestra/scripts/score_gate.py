#!/usr/bin/env python3
"""score_gate.py — Mechanism ⑥ (deterministic acquit-gate) + ⑤ (regression detection).

The Conductor RUNS this. It does not judge. The verdict is a fixed rule over the
external reviewer's blind score and finding counts recorded in meta.json.

Usage:
    score_gate.py <run-dir>

Reads <run-dir>/meta.json, evaluates the latest round, prints a verdict
(PASS / REVISE / RESTART) and the reason, and writes the verdict back into meta.json.
Exit code: 0 = PASS, 10 = REVISE, 20 = RESTART, 2 = error.

meta.json relevant shape:
{
  "pass_threshold": 7,
  "max_rounds": 5,
  "acceptance_criteria": ["...", "..."],
  "rounds": [
    {
      "n": 1,
      "blind_score": 4,
      "critical": 3,
      "major": 5,
      "web_contradicted": 1,
      "criteria_met": false,
      "resolved_items": ["item-a", "item-b"],   # items this round marked resolved
      "findings": ["item-c", "item-d"]           # CRITICAL/MAJOR finding ids this round
    }
  ]
}
"""
import json
import sys
from pathlib import Path


def load_meta(run_dir: Path) -> dict:
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        print(f"ERROR: meta.json not found in {run_dir}", file=sys.stderr)
        sys.exit(2)
    with meta_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_meta(run_dir: Path, meta: dict) -> None:
    with (run_dir / "meta.json").open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)


def detect_regression(rounds: list, current: dict) -> list:
    """Mechanism ⑤: a finding in the current round that was marked resolved in any
    earlier round is a regression."""
    resolved_before = set()
    for r in rounds[:-1]:
        resolved_before.update(r.get("resolved_items", []))
    current_findings = set(current.get("findings", []))
    return sorted(resolved_before & current_findings)


def evaluate(meta: dict):
    rounds = meta.get("rounds", [])
    if not rounds:
        print("ERROR: no rounds recorded in meta.json", file=sys.stderr)
        sys.exit(2)

    cur = rounds[-1]
    threshold = meta.get("pass_threshold", 7)
    max_rounds = meta.get("max_rounds", 3)
    n = cur.get("n", len(rounds))

    score = cur.get("blind_score", 0)
    critical = cur.get("critical", 0)
    web_contra = cur.get("web_contradicted", 0)
    criteria_met = bool(cur.get("criteria_met", False))

    regressions = detect_regression(rounds, cur)
    regression_count = len(regressions)
    cur["regression"] = regression_count
    if regressions:
        cur["regression_items"] = regressions

    # --- Deterministic rule (mechanism ⑥) ---
    reasons = []
    is_pass = (
        score >= threshold
        and critical == 0
        and web_contra == 0
        and regression_count == 0
        and criteria_met
    )

    if is_pass:
        verdict = "PASS"
        reasons.append(f"blind_score {score} >= threshold {threshold}")
        reasons.append("0 CRITICAL, 0 web-contradicted, 0 regression")
        reasons.append("all acceptance_criteria met")
    elif regression_count > 0:
        verdict = "RESTART"
        reasons.append(
            f"{regression_count} regression(s) — previously-resolved item(s) returned: "
            + ", ".join(regressions)
        )
        reasons.append("a patch loop reintroducing old defects signals the plan is wrong")
    elif n < max_rounds:
        verdict = "REVISE"
        if score < threshold:
            reasons.append(f"blind_score {score} < threshold {threshold}")
        if critical > 0:
            reasons.append(f"{critical} CRITICAL finding(s) open")
        if web_contra > 0:
            reasons.append(f"{web_contra} web-contradicted claim(s)")
        if not criteria_met:
            reasons.append("acceptance_criteria not all met")
        reasons.append(f"round {n} < max_rounds {max_rounds} — iterate")
    else:
        verdict = "RESTART"
        reasons.append(f"round {n} reached max_rounds {max_rounds} without PASS")
        reasons.append("recommend RESTART from Plan, or user may force-stop")

    cur["verdict"] = verdict
    return verdict, reasons


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: score_gate.py <run-dir>", file=sys.stderr)
        sys.exit(2)
    run_dir = Path(sys.argv[1])
    if not run_dir.is_dir():
        print(f"ERROR: not a directory: {run_dir}", file=sys.stderr)
        sys.exit(2)

    meta = load_meta(run_dir)
    verdict, reasons = evaluate(meta)
    save_meta(run_dir, meta)

    print("=== Orchestra Decide Gate (mechanism ⑥ + ⑤) ===")
    print(f"Run: {run_dir.name}")
    print(f"Verdict: {verdict}")
    print("Reasons:")
    for r in reasons:
        print(f"  - {r}")
    print()
    if verdict == "PASS":
        print("→ Write final.md.")
        sys.exit(0)
    elif verdict == "REVISE":
        print("→ Round N+1: re-run Stage 4 (Synthesize) with must_fix injected.")
        sys.exit(10)
    else:
        print("→ RESTART: return to Stage 2 (Plan Research).")
        sys.exit(20)


if __name__ == "__main__":
    main()
