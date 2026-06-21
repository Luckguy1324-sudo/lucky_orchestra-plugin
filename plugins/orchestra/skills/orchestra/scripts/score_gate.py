#!/usr/bin/env python3
"""score_gate.py — v0.8.0 decision gate.

v0.7.0 made the gate deterministic over a single blind score and a fixed pass threshold,
with max_rounds as the stop. v0.8.0 changes WHAT makes the gate stop: convergence, not a
counter. The counter becomes a safety rail. Three additions:

  CONVERGENCE (P2) — PASS now requires the score to be CONFIRMED stable (two independent
    blind scores >= threshold, |diff| <= 1) AND no fresh MAJOR finding this round (depth
    reached) — not merely one score over the line. When max_rounds is hit, the script reads
    the SCORE TRAJECTORY: still climbing toward the bar -> extend by one round; oscillating
    or stalled -> HUMAN_ESCALATE with a diagnosis, never a silent "good-enough" pass.

  DISAGREEMENT LEDGER (P3) — a gating disagreement (Performer vs Reviewer on an
    acceptance-criteria / deepen-topic claim) that is not 'evidence-resolved' blocks PASS.
    This makes a papered-over compromise structurally visible instead of invisible.

  CONFIRM verdict — when the first blind score clears the bar, the gate asks for exactly ONE
    confirmation blind pass (a new window on the SAME draft) before PASS. This costs +1
    window per RUN, not per round.

Backward compatible: missing v0.8.0 fields are treated as empty/false (a v0.7.0 meta.json
still evaluates, just without the new guards).

Usage: score_gate.py <run-dir>
Reads <run-dir>/meta.json, evaluates the latest round, writes verdict back.
Exit: 0=PASS, 10=REVISE, 20=RESTART, 30=CONFIRM, 40=HUMAN_ESCALATE, 2=error.
"""
import json
import sys
from pathlib import Path

CONVERGENCE_GAP = 1          # how close to threshold still counts as "converging"
MAX_ROUNDS_HARD_CAP = 8      # convergence may extend max_rounds up to this ceiling


def load_meta(run_dir: Path) -> dict:
    p = run_dir / "meta.json"
    if not p.exists():
        print(f"ERROR: meta.json not found in {run_dir}", file=sys.stderr)
        sys.exit(2)
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_meta(run_dir: Path, meta: dict) -> None:
    with (run_dir / "meta.json").open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)


def detect_regression(rounds, current):
    """⑤: a current finding that an earlier round marked resolved is a regression."""
    resolved_before = set()
    for r in rounds[:-1]:
        resolved_before.update(r.get("resolved_items", []))
    return sorted(resolved_before & set(current.get("findings", [])))


def traces_to_decision(items, decisions):
    blob = " ".join(
        f"{d.get('what','')} {d.get('why','')} {d.get('evidence_that_would_change_it','')}"
        for d in decisions
    ).lower()
    return any(str(it).lower() in blob for it in items)


def new_major_findings(rounds, current):
    """MAJOR findings present now that did NOT appear in any prior round.

    Requires per-round `major_findings` (list of ids). If the current round omits it, we
    cannot certify depth was reached -> return None (blocks PASS with a message)."""
    if "major_findings" not in current:
        return None
    seen_before = set()
    for r in rounds[:-1]:
        seen_before.update(r.get("findings", []))
        seen_before.update(r.get("major_findings", []))
    return sorted(set(current.get("major_findings", [])) - seen_before)


def gating_open_disagreements(meta):
    """P3: gating disagreements not 'evidence-resolved' block PASS."""
    out = []
    for d in meta.get("disagreements", []):
        if d.get("gating", True) and d.get("resolution") != "evidence-resolved":
            out.append(d.get("id", d.get("claim", "?")))
    return out


def trajectory(rounds):
    return [r.get("blind_score", 0) for r in rounds]


def is_monotonic_nondecreasing(seq):
    return all(b >= a for a, b in zip(seq, seq[1:]))


def repeated_findings(rounds):
    """Findings that appear in 2+ rounds — the signature of a stall."""
    counts = {}
    for r in rounds:
        for f in set(r.get("findings", [])):
            counts[f] = counts.get(f, 0) + 1
    return sorted([f for f, c in counts.items() if c >= 2])


def evaluate(meta):
    rounds = meta.get("rounds", [])
    if not rounds:
        print("ERROR: no rounds recorded in meta.json", file=sys.stderr)
        sys.exit(2)

    cur = rounds[-1]
    threshold = meta.get("pass_threshold", 8)            # v0.8.0 default raised to 8
    max_rounds = meta.get("max_rounds", 5)
    n = cur.get("n", len(rounds))

    score = cur.get("blind_score", 0)
    confirm = cur.get("confirm_score", None)             # P2: confirmation pass
    critical = cur.get("critical", 0)
    web_contra = cur.get("web_contradicted", 0)
    criteria_met = bool(cur.get("criteria_met", False))

    regressions = detect_regression(rounds, cur)
    cur["regression"] = len(regressions)
    if regressions:
        cur["regression_items"] = regressions

    nm = new_major_findings(rounds, cur)
    open_disag = gating_open_disagreements(meta)

    reasons = []

    # ---- hard blockers evaluated first -------------------------------------
    if len(regressions) > 0:
        cur["verdict"] = "RESTART"
        restart_at = ("CHALLENGE (Stage 1.5)"
                      if traces_to_decision(regressions, meta.get("decisions", []))
                      else "Plan (Stage 2)")
        cur["restart_at"] = restart_at
        return "RESTART", [f"{len(regressions)} regression(s): " + ", ".join(regressions),
                           "a prior-resolved item returned -> premise/plan is wrong",
                           f"restart at {restart_at}"]

    # ---- compute PASS eligibility (pre-confirmation) -----------------------
    base_ok = (score >= threshold and critical == 0 and web_contra == 0 and criteria_met)
    depth_ok = (nm is not None and len(nm) == 0)
    disag_ok = (len(open_disag) == 0)

    if base_ok and depth_ok and disag_ok:
        # stability requires a confirmation blind score on the SAME draft
        if confirm is None:
            cur["verdict"] = "CONFIRM"
            return "CONFIRM", [
                f"blind_score {score} >= threshold {threshold}, 0 CRITICAL/web/regression, "
                "criteria met, no fresh MAJOR, no open gating disagreement",
                "stability not yet confirmed -> run ONE confirmation blind pass "
                "(new window, SAME draft) and record `confirm_score`, then re-run the gate"]
        if confirm >= threshold and abs(score - confirm) <= 1:
            cur["verdict"] = "PASS"
            return "PASS", [
                f"blind {score} and confirm {confirm} both >= {threshold}, |diff| <= 1 (stable)",
                "0 CRITICAL, 0 web-contradicted, 0 regression, no fresh MAJOR",
                "all acceptance_criteria met, no open gating disagreement"]
        # confirmation disagreed with the first score -> not stable, treat as REVISE/escalate
        reasons.append(f"confirmation unstable: blind {score} vs confirm {confirm} "
                       f"(need both >= {threshold}, |diff| <= 1)")

    # ---- not a PASS: explain why -------------------------------------------
    if score < threshold:
        reasons.append(f"blind_score {score} < threshold {threshold}")
    if critical > 0:
        reasons.append(f"{critical} CRITICAL finding(s) open")
    if web_contra > 0:
        reasons.append(f"{web_contra} web-contradicted claim(s)")
    if not criteria_met:
        reasons.append("acceptance_criteria not all met")
    if nm is None:
        reasons.append("round is missing `major_findings` -> cannot certify depth; record it")
    elif nm:
        reasons.append(f"{len(nm)} fresh MAJOR finding(s) this round ({', '.join(nm)}) "
                       "-> depth not yet bottomed out")
    if open_disag:
        reasons.append(f"{len(open_disag)} open gating disagreement(s): " + ", ".join(open_disag))

    # ---- within budget -> iterate ------------------------------------------
    if n < max_rounds:
        cur["verdict"] = "REVISE"
        reasons.append(f"round {n} < max_rounds {max_rounds} -> iterate")
        return "REVISE", reasons

    # ---- budget exhausted: convergence diagnostic (P2) ---------------------
    traj = trajectory(rounds)
    climbing = is_monotonic_nondecreasing(traj) and (threshold - score) <= CONVERGENCE_GAP
    if climbing and max_rounds < MAX_ROUNDS_HARD_CAP:
        meta["max_rounds"] = max_rounds + 1
        cur["verdict"] = "REVISE"
        return "REVISE", reasons + [
            f"trajectory {traj} is converging (monotonic, gap {threshold - score} "
            f"<= {CONVERGENCE_GAP}) -> max_rounds extended to {max_rounds + 1} (cap "
            f"{MAX_ROUNDS_HARD_CAP}); one more round, NOT a relaxed pass"]

    # ---- stalled / oscillating / hit cap -> escalate to a human ------------
    cur["verdict"] = "HUMAN_ESCALATE"
    rep = repeated_findings(rounds)
    suspect = [f for f in rep if traces_to_decision([f], meta.get("decisions", []))]
    diag = [f"trajectory {traj} did not converge after {n} round(s) "
            f"(cap/limit {max_rounds})"]
    if rep:
        diag.append("repeated findings (stall signature): " + ", ".join(rep))
    if suspect:
        diag.append("these trace to a logged decision -> the PREMISE may be wrong: "
                    + ", ".join(suspect))
    diag.append("HUMAN DECISION REQUIRED — choose one:")
    diag.append("  (a) revise/supersede the suspected decisions[] entry, then RESTART at CHALLENGE")
    diag.append("  (b) accept a documented limitation in final.md (records the open finding honestly)")
    diag.append("  (c) lower pass_threshold ONLY with written justification in decisions[] (not silent)")
    diag.append("Refusing to choose is itself a choice to keep iterating — the gate will not "
                "auto-pass to end the loop.")
    return "HUMAN_ESCALATE", reasons + diag


def main():
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

    print("=== Orchestra Decide Gate v0.8.0 (convergence + ledger) ===")
    print(f"Run: {run_dir.name}")
    print(f"Verdict: {verdict}")
    print("Reasons:")
    for r in reasons:
        print(f"  - {r}")
    print()
    code = {"PASS": 0, "REVISE": 10, "RESTART": 20, "CONFIRM": 30, "HUMAN_ESCALATE": 40}[verdict]
    nxt = {
        "PASS": "-> Write final.md.",
        "REVISE": "-> Round N+1: fresh Synthesizer subagent (C1) with must_fix injected.",
        "RESTART": f"-> RESTART: return to {meta['rounds'][-1].get('restart_at', 'Plan (Stage 2)')}.",
        "CONFIRM": "-> Run ONE confirmation blind pass (new window, SAME draft), record "
                   "`confirm_score`, re-run gate.",
        "HUMAN_ESCALATE": "-> STOP. Present the diagnosis to the user and get a decision. "
                          "Do NOT auto-pass.",
    }[verdict]
    print(nxt)
    sys.exit(code)


if __name__ == "__main__":
    main()
