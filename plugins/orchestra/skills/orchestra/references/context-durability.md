# Context Durability — Surviving a Long Run Without Degrading (C1–C3)

A scoped, 8-mechanism, multi-round orchestra run is long. In a single CLI session, the
context window fills, the system compacts, and a naive workflow degrades: the late stages
lose the early intent, and the artifact gets rushed. This document defines the three
mechanisms that keep a long run from degrading.

The underlying problem, stated precisely: compaction summarizes context within a session —
it keeps the "what" but tends to lose the "why". The reasoning that chose warm-suction over
cryogenic, or topic B over topic A, lives in intermediate steps that compaction drops. A
later stage, missing that reasoning, can silently re-decide the opposite on incomplete
information. orchestra prevents this three ways.

---

## C1 — Isolated-subagent execution for heavy stages

**Principle:** a subagent should never inherit the main session's context or history. The
controller constructs exactly what the subagent needs. This keeps the subagent focused AND
preserves the controller's own context for coordination.

orchestra v0.6.0 already isolated Research (Stage 3). v0.7.0 extends isolation to the two
other heavy stages:

| Stage | Runs as | Receives (and nothing else) | Returns |
|-------|---------|------------------------------|---------|
| 3 Research ×N | N isolated Task subagents | topic spec + relevant `_refs/` | `03-research/tK.md` |
| 4 Synthesize | 1 isolated Synthesizer subagent | the N research files + draft template + `must_fix[]` | `04-draft-vN.md` |
| 6 Review consolidate | isolated subagent (when heavy) | the four raw trace files | `05-review-vN.md` |

**Effect:** the main Conductor session passes file paths and receives file paths. Its context
stays roughly constant no matter how many rounds run. The thing that causes late-stage
rush — a main session bloated with every stage's full text — never happens. The Conductor
holds only: `meta.json`, the current stage's file path, and the active `must_fix[]`.

**Implementation note:** dispatch via the Agent/Task tool. The subagent prompt must say
explicitly: "You do not have the main session's history. Work only from the files provided."
On REVISE rounds the Synthesizer is a *fresh* subagent each time — it reads the prior draft
and review from disk, not from inherited context.

---

## C2 — Decision log: preserve the "why"

Every durable scope decision is written to `meta.json.decisions[]` as:

```json
{
  "what": "warm-suction multi-stage seawater-intercooled baseline",
  "why": "industry-standard; avoids the 45 K suction-temperature stream anomaly seen in N-2R+",
  "evidence_that_would_change_it": "a peer-reviewed process showing cryogenic suction with lower total kJ/kg"
}
```

Three rules:
1. **Log at decision time** — primarily during CHALLENGE (1.5), but any time a durable scope
   or method choice is made.
2. **Never silently re-litigate** — on resume or later stages, treat `decisions[]` as settled
   with their recorded rationale. If you're about to reverse one, say so explicitly and add a
   superseding entry (keep the old one, mark it superseded).
3. **The "why" is what survives compaction (C3 tier 2)** — this is the field that prevents a
   later stage from re-deciding the opposite.

This directly closes the "compaction keeps what, loses why" gap: the why is now durable
state on disk, not ephemeral reasoning in the window.

---

## C3 — Explicit compaction priority order

If the window fills and compaction triggers, preserve in this order. Never drop a higher tier
to keep a lower one:

```
Tier 1  acceptance_criteria              — what "done" means (the Stage-7 gate)
Tier 2  decisions[] with their "why"     — why the scope is what it is (C2)
Tier 3  current stage output path + active must_fix[]
Tier 4  latest blind score + open CRITICAL findings
Tier 5  everything else (prose history, prior-round narrative)
```

State this priority in the run so that if the user or system requests compaction, the
Conductor compacts in this order rather than the default (which preserves recent prose and
may drop early decisions).

---

## Resume protocol (compaction OR fresh session)

Because heavy stages are isolated (C1) and all state is on disk, recovery is clean:

1. On startup, check for an in-progress `meta.json` with timestamp < 24h.
2. If found: read `meta.json` + the latest stage file(s). Give a 2-sentence "resuming from
   Stage X; scope mode HOLD; N decisions logged" summary.
3. Continue from the next stage. Do NOT re-run completed stages. Do NOT re-litigate
   `decisions[]`.
4. If the latest stage was a Review awaiting REVISE, read `must_fix[]` from the review file
   and dispatch a fresh Synthesizer subagent (C1) for the next round.

A good state-persistence setup compresses rebuild cost from many minutes of re-derivation to
near-instant resume — because the "why" (C2) is already on disk, the new session reaches the
same decisions instead of re-deriving (and possibly contradicting) them.

---

## Why these three are sufficient (and we stop here)

- C1 keeps the main context flat → no late-stage rush from a bloated window.
- C2 keeps the "why" durable → compaction can't silently flip a decision.
- C3 makes compaction itself prioritize the right tiers → graceful degradation, not random
  loss.

orchestra already persists the "what" (run-dir files, meta.json) and isolates Research. With
C1–C3 it now also isolates the other heavy stages and preserves the "why". That fully
addresses the long-run degradation failure mode; piling on additional context machinery
beyond this would add complexity without closing a remaining gap.
