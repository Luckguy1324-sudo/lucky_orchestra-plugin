# Scoping Rules — Challenge the Premise Before Producing (S1–S4)

orchestra's verification makes the review trustworthy. Scoping makes sure the *right thing*
is being reviewed. A perfectly verified answer to the wrong question is the most expensive
failure mode in the whole workflow. This document defines the scoping discipline.

The principle, distilled from analysis of dozens of planning skills: most deliverables fail
not because the work was bad, but because the wrong thing was built — assumptions never
challenged, requirements invented mid-production, reviews that validated what the builder
already believed. orchestra attacks this with a structured CHALLENGE gate before any
production work.

---

## §scope-modes — Commit to one, never silently shift (S1)

At the start of CHALLENGE (Stage 1.5), declare exactly one scope mode and hold it through
the run. A review without a declared scope mode oscillates — expanding when expansion feels
productive, holding when pushed back on, reducing when out of time. A committed mode
creates a consistent posture.

| Mode | Meaning | Use when |
|------|---------|----------|
| `EXPAND` | Deliberately broaden scope | The framing is too narrow to matter |
| `SELECTIVE` | Expand only specific named areas | One dimension is under-scoped, rest is fine |
| `HOLD` | Keep scope exactly as briefed | Scope is right; resist drift |
| `REDUCE` | Deliberately narrow scope | Too broad to ship/finish in the horizon |

Record as `meta.json.scope_mode`. If you later need to change it, say so explicitly and log
the reversal in `decisions[]` — never shift silently.

---

## §banned-phrases — Anti-sycophancy as structural constraint (S3)

"Be critical" is tone advice and models ignore it. The stronger method is to name the
specific phrases that signal sycophancy and prohibit them, each with a required replacement.
Apply these in Brief, CHALLENGE, and Plan — not only in Review.

| Banned | Required replacement |
|--------|---------------------|
| "That's interesting" | Take a position. Say whether it's right or wrong and why. |
| "There are many ways to think about this" | Pick one. State what evidence would change your mind. |
| "That could work" | Say whether it WILL work based on evidence, and what evidence is missing. |
| "It depends" (alone) | State what it depends on, then commit to the most likely case. |
| "You could consider…" | Recommend, or don't raise it. |

The rule: **take a position AND state the falsifiability condition** — the evidence that
would change it. Position plus falsifiability is more rigorous than any tone instruction.
Every `decisions[]` entry carries its `evidence_that_would_change_it` for exactly this
reason.

---

## §confidence-gap — Weight research by where the plan is weakest (S4)

Generic "improve the plan" instructions produce uniformly padded plans. Scoring concentrates
effort where the plan is *actually* weakest, not where words are easiest to add.

After the Plan (Stage 2) enumerates N topics, score each:

```
gap_score(topic) = trigger_count + risk_bonus + critical_section_bonus
```

- **trigger_count** — count of weakness signals present in the topic. Signals (1 point each):
  unstated assumption, no source cited, novel/unproven method, conflicting prior evidence,
  quantitative claim without derivation, external dependency, ambiguous success criterion.
- **risk_bonus** (+2) — topic sits in a high-risk domain: safety, regulatory/standards
  compliance, irreversible decisions, anything feeding `acceptance_criteria`.
- **critical_section_bonus** (+2) — topic maps to a Key Decision, a System-Wide Impact, or
  the central thesis/claim of the deliverable.

Rank topics by `gap_score`. Mark the **top 2–5** `deepen: true`. Those get:
- richer research briefs and (if warranted) a second research pass in Stage 3,
- the most reviewer/persona attention in Stage 6.

`scripts/confidence_gap.py` computes this from a small JSON of per-topic signal flags; or
apply the rubric by hand and write `gap_score` into `meta.json.topics[]`.

**How the Conductor builds the input.** After the Plan enumerates topics, the Conductor (not
the user) reviews each topic against the 7 signal questions above and writes a `topics.json`
with each signal as a boolean — e.g. "does this topic rest on an unstated assumption?" →
`unstated_assumption: true`. This is a Claude judgment step, fast and local, requiring no
ChatGPT. Then run `confidence_gap.py topics.json --top 5 --write <run-dir>` to score, rank,
and merge `gap_score`/`deepen` into meta.json in one step. A minimal `topics.json` entry:
`{"id":"t1","title":"...","signals":{"unstated_assumption":true},"high_risk_domain":true,"critical_section":false}`.

---

## §handoff-test — Testable phase completion (S1)

Before leaving any scoping phase, ask: **"What would the next phase still have to invent if
we stopped here?"** If the answer is product behavior, scope boundaries, success criteria,
or the core problem framing — the current phase is NOT done. This makes completion testable
rather than felt, and catches lazy handoffs that push undecided scope downstream where it
becomes expensive.

---

## How scoping connects to the rest

- CHALLENGE (1.5) uses `forcing-questions.md` for the questions, this doc for scope mode +
  handoff test, and writes `decisions[]` (the "why", preserved by C2).
- Confidence-gap scores (S4) flow from Plan (2) into Research depth (3) and Reviewer
  attention (6) — the same weakest topics get more effort at both ends.
- Anti-sycophancy (S3) is the connective tissue: every scoping decision is a committed
  position with a stated falsifiability condition, which is exactly what makes the later
  deterministic gate (⑥) meaningful.
