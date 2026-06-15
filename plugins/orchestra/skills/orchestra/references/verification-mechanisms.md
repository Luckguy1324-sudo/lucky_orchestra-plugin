# Verification Mechanisms — Rationale & Implementation

This document explains *why* each of the 8 mechanisms exists and how to implement it
correctly. The short version lives in `SKILL.md`; this is the reasoning.

The single weakest point of orchestra v0.3.0 was an unstated assumption: that a review
score is meaningful. In practice a naive review loop produces scores that drift upward
regardless of real quality, hides critical findings in flat lists, and passes
fabricated citations. Each mechanism below closes one of those gaps.

---

## ① Reviewer-Bias Guard

**Problem.** When the Reviewer remembers prior rounds ("since your last review we
implemented X, Y, Z"), it feels social/consistency pressure to reward the effort. Scores
inflate round over round even when real quality is flat.

**Evidence.** In a documented April 2026 paper run, reusing the same review thread with
"since last round we did X" prompts inflated a paper's score from a real 3/10 to a fake
8/10 across 5 rounds. Switching to fresh, zero-context threads recovered the true 3/10.

**Implementation.** Split Stage 5 review into two purposes:
- **Scoring (5a)** — ALWAYS a brand-new ChatGPT window per round. The prompt explicitly
  says: "fresh, zero-context review; ignore any prior rounds, fix lists, or executor
  explanations; judge only from the current artifact." The 5a score is the only number
  that feeds the gate.
- **Diagnosis (optional, context-continuing)** — if you want "what changed since last
  time", you may keep a window open, but that output is for the human's understanding
  only and must NOT influence the gate score.

**Manual-connection note.** This is trivially honored without an API: scoring goes in a
fresh chat, diagnosis (if used) in the existing chat. The discipline, not the tooling,
is what matters.

---

## ② Severity-Tagged Findings

**Problem.** A flat findings list ("here are 12 things") forces the Conductor to guess
fix priority. Time gets spent on cosmetics while a fatal flaw slips through.

**Implementation.** Enforce a finding schema in every review prompt. Each finding ranked
CRITICAL > MAJOR > MINOR, and each CRITICAL/MAJOR finding must answer the 4-question rule:
1. What can go wrong?
2. Why is it vulnerable / wrong?
3. What is the impact?
4. What is the specific, actionable recommendation?

Explicitly exclude style, naming, and speculative comments from findings — they dilute
signal. `must_fix[]` is then assembled in strict CRITICAL → MAJOR → MINOR order and
injected into the next Synthesize round in that order.

---

## ③ Anti-Groupthink Personas

**Problem — and the counterintuitive part.** The naive fix for a single biased reviewer
is "use more reviewers". This backfires. A February 2026 study found heterogeneous
multi-agent teams consistently failed to match their best individual member, losing up
to 37.6% performance, even when explicitly told which member was the expert. The failure
mechanism is consensus-seeking over expertise. Homogeneous copies of one model family
make it worse.

**Implication.** Do not just spawn N reviewers and average them. Instead, give ONE model
several *narrow, non-overlapping lenses* in separate windows, so each pass has a
different blind spot and there is no shared conversation to converge in.

**Implementation.** Define a domain persona set (see `persona-sets.md`). Each persona is
a separate ChatGPT window with a single mandate. They never see each other's output, so
they cannot converge. The Conductor — not the personas — reconciles their findings. This
gets the diversity benefit of multiple reviewers while structurally avoiding the
consensus-collapse failure mode.

---

## ④ Web-Verified Claims

**Problem.** Models fabricate plausible-looking citations and standard clauses. A
review loop and a numeric-claim audit both miss these; only a fresh external lookup
catches them. In a documented run, real papers were cited in contexts they did not
support, and a bib entry shipped with `author = "Anonymous"` because metadata was never
resolved — none caught until a web-lookup review surfaced them.

**Why this matters here specifically.** This work routinely cites IGC Code paragraphs,
API 520/521, ASME, ISO, SOLAS. A fabricated clause number that "sounds right" is worse
than no citation. The rule is: never assert "the standard requires X" without confirming
the original text.

**Implementation (Stage 5c).** The Conductor (Claude, with WebSearch/WebFetch) extracts
every standard citation, numeric claim, and literature citation, then verifies each:
- `[WEB-VERIFIED]` — confirmed against an authoritative source
- `[WEB-CONTRADICTED]` — the source says otherwise → auto-promote to CRITICAL
- `[WEB-INCONCLUSIVE]` — could not confirm → flag "requires original-text confirmation",
  treat as MAJOR until resolved, and describe at the concept level rather than asserting
  a specific clause number

Standard citations are guilty until verified.

---

## ⑤ Forensic Review Trace

**Problem.** Without preserved raw reviews and a score trajectory, you cannot tell
whether a fix held or whether a previously-resolved defect quietly returned (regression).
A documented run had a case-split inconsistency between a paper's main body and appendix
that drifted multiple times across fix rounds because nothing checked for regression.

**Implementation.**
- Save every sub-pass response VERBATIM into `traces/` (never summarize, never truncate).
- Log a per-round score table in `meta.json` (`rounds[]`).
- Before each Decide, compare this round's CRITICAL/MAJOR findings against items marked
  resolved in earlier rounds. A reappearing item increments `regression_count`.
- `regression_count > 0` auto-escalates the round to RESTART (see ⑥) — a patch loop that
  reintroduces old defects means the plan is wrong, not the patch.

---

## ⑥ Acquit-Gate Separation

**Problem.** In v0.3.0 the Conductor both synthesized the draft (Stage 4) and decided
pass/fail (Stage 6). The synthesizer judging its own output is subtle self-verification.

**Principle.** "A loop can DRIVE, it cannot ACQUIT." The loop may judge whether it has
*executed completely*, never whether the result is *good or correct*. Quality/correctness
judgment belongs to an external authority — here, a deterministic rule over the external
Reviewer's blind score.

**Implementation (Stage 6).** Pass/fail is `scripts/score_gate.sh`, a fixed rule:
```
PASS if blind_score >= PASS_THRESHOLD AND CRITICAL == 0 AND web_contradicted == 0
        AND regression == 0 AND all acceptance_criteria met
```
The Conductor runs the script and obeys it. It never overrides the verdict by judgment.
Thresholds live in `meta.json`, set at Brief time from the user's acceptance criteria.

---

## ⑦ Kill-Argument Adversary

**Problem.** "Improvement-mode" reviews accumulate patches but rarely ask the
existential question: should this be rejected outright? A polished-but-fundamentally-
flawed artifact can pass an improvement loop.

**Implementation (Stage 5d).** One pass per round, in a NEW window, instructs the model:
"You have decided to REJECT this. In ≤200 words write the single strongest, most
defensible rejection argument. Attack the core, not the surface." If the kill-argument
names a flaw not already in the findings, add it as CRITICAL. Surviving a genuine
kill-argument is a far stronger signal than accumulated patches.

This mirrors a Bull/Bear adversarial structure — the value is in a reviewer that is
*trying to lose the case for the work*, not improve it.

---

## ⑧ Deterministic Pre-Gate

**Problem.** Expensive manual ChatGPT passes get wasted reviewing drafts with mechanical
defects (empty sections, broken citations, placeholders, compile errors). The reviewer
spends attention on what a script could have caught for free.

**Principle (from hardened pipelines).** Hard, machine-checkable gates must PASS before
any reviewer sees the artifact. A closed, mechanical checklist structurally prevents the
cosmetic patch-loop.

**Implementation (Stage 4.5).** `scripts/pre_gate.sh` runs before Stage 5:
- No empty sections
- Every citation has a matching reference entry
- No unresolved placeholders (TODO/TBD/[?]/XXX/Anonymous)
- Unit/notation consistency scan
- If LaTeX: 0 undefined references, 0 undefined citations

Any FAIL → fix → re-run Stage 4.5. Only a full PASS unlocks Stage 5. This keeps the
costly manual review focused entirely on substance.

---

## How the 8 fit together

```
④ web-verify ─┐
②③⑦ findings ─┼─→ consolidated must_fix (CRITICAL→MINOR)
① blind score ┘            │
                           ▼
⑧ pre-gate (before) → ⑤ trace (during) → ⑥ gate (after, deterministic)
```

① guarantees the score is honest. ②③⑦ guarantee the findings are complete and
prioritized. ④ guarantees external claims are real. ⑧ keeps review focused; ⑤ makes the
loop auditable and regression-aware; ⑥ ensures the final decision is not self-granted.
Together they turn "a review happened" into "a review you can trust".
