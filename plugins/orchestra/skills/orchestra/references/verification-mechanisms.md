# Verification Mechanisms — Rationale & Implementation (①–⑧)

This document explains why each of the 8 verification mechanisms exists and how to implement
it. The short version is in `SKILL.md`; this is the reasoning. Stage numbers reflect v0.7.0
(Review is Stage 6, Pre-Gate is 5.5, Decide is 7).

The weakest assumption a naive review loop makes is that a review score is meaningful. In
practice scores drift upward regardless of real quality, critical findings hide in flat
lists, and fabricated citations pass. Each mechanism closes one of those gaps.

---

## ① Reviewer-Bias Guard

**Problem.** When the Reviewer remembers prior rounds ("since last review we did X"), it
feels consistency pressure to reward effort. Scores inflate even when quality is flat.

**Evidence.** In a documented run, reusing one review thread with "since last round we did X"
inflated a score from a real 3/10 to a fake 8/10 across 5 rounds. Fresh zero-context threads
recovered the true 3/10.

**Implementation.** Split review purpose:
- **Scoring (6a)** — ALWAYS a brand-new ChatGPT window per round. Prompt says "fresh,
  zero-context; ignore prior rounds/fix-lists/explanations; judge only the current artifact."
  The 6a score is the only number feeding the gate.
- **Diagnosis (optional)** — context-continuing windows may show "what changed", but that
  output never influences the gate score.

Trivially honored in MANUAL mode: scoring in a fresh chat, diagnosis in the existing one.

---

## ② Severity-Tagged Findings

**Problem.** A flat findings list forces the Conductor to guess fix priority; time goes to
cosmetics while a fatal flaw slips through.

**Implementation.** Every review finding is ranked CRITICAL > MAJOR > MINOR, and each
CRITICAL/MAJOR answers the 4-question rule: (1) what can go wrong, (2) why wrong/vulnerable,
(3) impact, (4) specific actionable fix. Style/naming/speculative comments are excluded.
`must_fix[]` is assembled and consumed CRITICAL → MAJOR → MINOR.

---

## ③ Anti-Groupthink Personas

**Problem and counterintuition.** The naive fix for a biased reviewer is "more reviewers".
This backfires: heterogeneous multi-agent teams consistently fail to match their best
individual member, losing up to ~37.6% performance, because they seek consensus over
expertise. Homogeneous copies of one model make it worse.

**Implication.** Don't average N reviewers. Give ONE model several narrow, non-overlapping
lenses in separate windows — different blind spots, no shared conversation to converge in.

**Implementation.** Define a domain persona set (`persona-sets.md`). Each persona is a
separate window with one mandate; they never see each other's output. The Conductor — not the
personas — reconciles. Persona effort concentrates on `deepen: true` topics (S4 linkage).

---

## ④ Web-Verified Claims

**Problem.** Models fabricate plausible citations and clauses; a review loop and a numeric
audit both miss these — only a fresh external lookup catches them. In a documented run, real
papers were cited in unsupported contexts and a bib entry shipped as author="Anonymous",
caught only by a web-lookup review.

**Why critical here.** This work cites IGC Code, API 520/521, ASME, ISO, SOLAS. A fabricated
clause that "sounds right" is worse than none. Rule: never assert "the standard requires X"
without confirming the original text.

**Implementation (6c).** Conductor (Claude + WebSearch) extracts every standard citation,
numeric claim, literature citation, and tags each `[WEB-VERIFIED]` /
`[WEB-CONTRADICTED]`→CRITICAL / `[WEB-INCONCLUSIVE]`→MAJOR (concept-level only, no clause
number asserted). Standards are guilty until verified.

---

## ⑤ Forensic Review Trace

**Problem.** Without preserved raw reviews and a score trajectory, you cannot tell whether a
fix held or a resolved defect quietly returned. A documented run had a main-vs-appendix
inconsistency that drifted across rounds because nothing checked regression.

**Implementation.**
- Save every sub-pass response verbatim to `traces/` (never summarize/truncate).
- Log a per-round score table in `meta.json.rounds[]`.
- Before each Decide, compare this round's CRITICAL/MAJOR against prior-resolved items; a
  reappearance increments `regression` and auto-escalates to RESTART (⑥).

---

## ⑥ Acquit-Gate Separation

**Problem.** If the Conductor both synthesizes (Stage 4) and decides pass/fail (Stage 7),
the synthesizer judges its own output — subtle self-verification. (v0.7.0 further isolates
Synthesize into a subagent per C1, but the gate separation still matters.)

**Principle.** "A loop can DRIVE, it cannot ACQUIT." The loop judges whether it *executed
completely*, never whether the result is *good*. Quality judgment is an external rule over
the external Reviewer's blind score.

**Implementation (Stage 7).** `scripts/score_gate.py` — a fixed rule (see SKILL.md). The
Conductor runs it and obeys; it never overrides by judgment. Thresholds live in meta.json,
set from the user's acceptance criteria at Brief time.

---

## ⑦ Kill-Argument Adversary

**Problem.** Improvement-mode reviews accumulate patches but rarely ask: should this be
rejected outright? A polished-but-fundamentally-flawed artifact can pass an improvement loop.

**Implementation (6d).** One pass per round, NEW window: "You have decided to REJECT this.
In ≤200 words write the single strongest, most defensible rejection. Attack the core." A new
flaw → CRITICAL. Surviving a real kill-argument is a stronger signal than accumulated patches.
Mirrors a Bull/Bear adversarial structure — a reviewer trying to lose the case for the work.

---

## ⑧ Deterministic Pre-Gate

**Problem.** Expensive manual ChatGPT passes get wasted on drafts with mechanical defects
(empty sections, broken citations, placeholders, compile errors).

**Principle.** Hard, machine-checkable gates must PASS before any reviewer sees the artifact.

**Implementation (Stage 5.5).** `scripts/pre_gate.sh` checks empty sections, citation↔ref
matching, placeholders, unit/notation, LaTeX compile. Any FAIL → fix → re-run. Only full PASS
unlocks Stage 6, keeping costly manual review focused on substance.

---

## How the 8 fit together

```
④ web-verify ─┐
②③⑦ findings ─┼─→ consolidated must_fix (CRITICAL→MINOR)
① blind score ┘            │
                           ▼
⑧ pre-gate (before) → ⑤ trace (during) → ⑥ gate (after, deterministic)
```

① makes the score honest. ②③⑦ make findings complete and prioritized. ④ makes external
claims real. ⑧ keeps review focused; ⑤ makes the loop auditable and regression-aware; ⑥
ensures the decision isn't self-granted. Together: "a review happened" → "a review you can
trust". In v0.7.0 this trustworthy review now operates on a correctly-scoped problem (S1–S4)
inside a context-durable run (C1–C3).
