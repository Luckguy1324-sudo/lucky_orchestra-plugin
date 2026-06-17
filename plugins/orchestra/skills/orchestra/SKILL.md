---
name: orchestra
description: >
  Multi-AI collaboration orchestration. Claude Code Opus acts as Conductor,
  coordinating itself (Performer) and ChatGPT Pro (Reviewer) to produce one
  high-quality, cross-validated artifact. The Performer never grades its own
  work — generation is Claude, verification is ChatGPT. Use when the user says
  "orchestra", "오케스트라", "멀티 AI 협업", "교차검증 작업", or wants a
  research/design/writing deliverable rigorously scoped and cross-validated
  across two model families. v0.7.0 adds premise-challenging scoping (CHALLENGE
  gate, stage-routed forcing questions, confidence-gap-weighted research,
  anti-sycophancy constraints) and context durability (isolated-subagent
  execution for Synthesize/Review, decision-log "why" preservation, explicit
  compaction priority) on top of the 8 hardened verification mechanisms.
version: 0.7.0
license: MIT
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill
---

# Orchestra v0.7.0 — Scoped, Verified, Context-Durable Multi-AI Collaboration

Throw one goal and the Conductor coordinates a workflow with ChatGPT that (1) challenges
whether you're solving the right problem, (2) researches with effort concentrated where
the plan is weakest, (3) cross-validates the result across two model families, and (4)
survives context exhaustion without degrading into a rushed artifact.

**Core principle:** the one who does the work does not verify the work. Performer =
Claude. Reviewer = ChatGPT.

**Three pillars (each maps to a reference doc):**
- **Verification** — 8 hardened mechanisms make the review *trustworthy*. → `verification-mechanisms.md`
- **Scoping** — challenge the premise before producing, weight research by confidence gap. → `scoping-rules.md`, `forcing-questions.md`
- **Context durability** — isolate heavy stages, preserve the "why". → `context-durability.md`

---

## The 8 Verification Mechanisms (unchanged from v0.6.0)

| # | Mechanism | Stage(s) | Why |
|---|-----------|----------|-----|
| ① | Reviewer-Bias Guard | 6a | Fresh context per scoring pass — stops score inflation |
| ② | Severity-Tagged Findings | 6 | CRITICAL > MAJOR > MINOR — fix order unambiguous |
| ③ | Anti-Groupthink Personas | 6 | One model, narrow non-overlapping lenses — no consensus collapse |
| ④ | Web-Verified Claims | 6c | Standards/figures/citations checked against the web |
| ⑤ | Forensic Review Trace | all | Raw reviews preserved, score trajectory logged, regression detected |
| ⑥ | Acquit-Gate Separation | 7 | Pass/fail is a deterministic rule, not Conductor discretion |
| ⑦ | Kill-Argument Adversary | 6d | One pass writes the strongest rejection |
| ⑧ | Deterministic Pre-Gate | 5.5 | Mechanical checks pass BEFORE any expensive review |

## New in v0.7.0 — Scoping (S) + Context durability (C)

| Tag | Addition | Stage | Why |
|-----|----------|-------|-----|
| S1 | CHALLENGE gate — pressure-test the premise before any production | 1.5 | Stops "verifying the wrong thing perfectly" |
| S2 | Stage-routed forcing questions | 1.5 | Right hard question for the work's stage |
| S3 | Anti-sycophancy constraints (banned phrases) in Brief+Plan | 1, 2 | Scoping decisions become falsifiable, not vague |
| S4 | Confidence-gap-weighted research | 2, 3 | Costly passes concentrate where the plan is weakest |
| C1 | Isolated-subagent execution for Synthesize + Review | 4, 6 | Main Conductor context stays flat — no late-stage degradation |
| C2 | Decision-log ("why") in meta.json | 1.5, all | The reason behind scope survives compaction |
| C3 | Explicit compaction priority order | all | If the window fills, the right things survive |

---

## Role Separation

| Role | Model | Responsibility |
|------|-------|----------------|
| Conductor (지휘자) | Claude Code Opus (main session) | Intent, routing, gate execution, file-only coordination — NOT judging, NOT heavy synthesis |
| Challenger | Claude (Conductor, scoping mode) | Runs the CHALLENGE gate forcing questions |
| Researcher Planner | ChatGPT (mode-selected) | Designs the research agenda |
| Performer ×N (연주자) | Claude Task subagents (isolated) | Executes each research topic in parallel |
| Synthesizer | Claude Task subagent (isolated) | Integrates research into a draft — C1 |
| Reviewer (검토자) | ChatGPT (mode-selected) | Deep review under enforced schema, persona passes |
| Adversary (반론자) | ChatGPT (mode-selected) | Writes the strongest rejection |

**Why the Conductor delegates Synthesize and Review (C1):** so the main session never
accumulates the full weight of every stage. The Conductor passes file paths and receives
file paths. Its own context stays roughly constant regardless of how many rounds run —
this is what prevents the late-stage rushed-artifact failure mode.

---

## ChatGPT Mode Catalog

| ID | Display | Best for | Est. time |
|----|---------|----------|-----------|
| `deep-research` | Pro Deep Research | Citations, literature, market/academic research | 5–30 min |
| `pro-reasoning` | Pro Reasoning | Modeling, proofs, verification | 1–5 min |
| `thinking` | Thinking | General review | 30 s–2 min |
| `standard` | Standard | Summarize, format conversion | instant |

At Stage 1.5 the Conductor recommends a mode by goal keywords; the user confirms.

**Manual connection:** This skill assumes ChatGPT Pro via manual paste (no API). Each
ChatGPT interaction specifies NEW window (bias-sensitive) or SAME window
(context-continuing). Honoring that is mechanism ①. See `manual-vs-auto.md`.

---

## Workflow — 7 Stages + 3 Gates

```
 1   Brief ─────────────── interview, capture acceptance_criteria (S3 anti-sycophancy)
 1.5 [CHALLENGE GATE S1/S2] ── forcing questions: are we solving the right problem?
                                  └─ writes decisions[] with WHY (C2)
 1.6 Model selection ─── recommend ChatGPT mode per stage, user confirms
 2   Plan Research (ChatGPT, NEW window) ── agenda + confidence-gap scores per topic (S4)
 3   Research ×N (Performer subagents, isolated, parallel) ── deepen high-gap topics first (S4)
 4   Synthesize (Synthesizer SUBAGENT, isolated) ── integrate; inject must_fix on REVISE (C1)
 5.5 [PRE-GATE ⑧] ── mechanical checks (code) BEFORE any review
 6   Review (ChatGPT, isolated dispatch C1):
       6a Blind score    (NEW window every round)        ①②
       6b Persona passes (separate windows)              ③
       6c Web audit      (Conductor + WebSearch)         ④
       6d Kill-argument  (NEW window)                    ⑦
 7   [DECIDE GATE ⑥] ── score_gate.py: PASS / REVISE / RESTART (deterministic)
                          └─ regression auto-escalates to RESTART (⑤)
```

PASS → `final.md`. REVISE → round N+1 (Stage 4 with must_fix). RESTART → back to Plan
(or to CHALLENGE if the premise itself failed).

---

### Stage 1 — Brief (Conductor interview)

Output: `01-brief.md`

Interview (or parse args). Apply **S3 anti-sycophancy** to your own framing — see
`scoping-rules.md` §banned-phrases. Do not say "that's interesting" or "there are several
ways"; take a position and state what evidence would change it.

- Q1: Deliverable? (paper section, design doc, analysis…)
- Q2: What does "done" look like? → these become `acceptance_criteria[]` (Stage 7 gate)
- Q3: Venue/standard/audience? → sets reviewer persona + web-verification scope
- Q4: Reference materials? → paths into `_refs/`
- Q5: Domain → selects `persona_set` (③) and `forcing_question_route` (S2)

If acceptance criteria are vague, propose concrete checkable ones and confirm.

---

### Stage 1.5 — CHALLENGE GATE (S1, S2) + decision log (C2)

**This is the v0.7.0 scoping core. Do not skip it.** Before any production work, pressure-
test whether this is the right problem to solve. A perfectly verified answer to the wrong
question is worthless.

1. **Route forcing questions by stage** (S2). Read `forcing-questions.md`, pick the route
   for this work's stage (pre-product / has-users / paying / pure-engineering / research-
   paper). Ask only the routed subset — wrong questions at the wrong stage waste effort.
2. **Pressure-test, don't interview.** For each routed question, push on vague answers
   using the pushback patterns in `forcing-questions.md`. Demand specificity.
3. **Decide scope mode** and commit to it (from `scoping-rules.md` §scope-modes): EXPAND /
   SELECTIVE / HOLD / REDUCE. Chosen once, never silently shifted.
4. **Write `decisions[]` to meta.json (C2)** — each as `{what, why, evidence_that_would_change_it}`.
   This is the "why" that must survive compaction. Example:
   `{"what":"warm-suction baseline","why":"industry-standard, avoids 45K stream anomaly","evidence_that_would_change_it":"a peer process showing cryogenic suction with lower total kJ/kg"}`
5. **Gate question:** "If we stop scoping here, what would the Plan stage still have to
   invent?" If the answer is scope boundaries, success criteria, or the core problem
   framing — CHALLENGE is not done. Loop.

Output: `01.5-challenge.md` + `decisions[]` in meta.json.

---

### Stage 1.6 — Model selection
Conductor recommends ChatGPT modes per stage, records in `meta.json.modes`. User confirms.

---

### Stage 2 — Plan Research (ChatGPT, NEW window) + confidence-gap scoring (S4)

Output: `02-research-plan.md`

1. Draft the agenda question; user pastes into a NEW ChatGPT window (usually
   `deep-research`), pastes response back. Plan enumerates N research topics.
2. **Score each topic's confidence gap (S4)** — run `scripts/confidence_gap.py` or apply
   the rubric in `scoping-rules.md` §confidence-gap: `trigger_count + risk_bonus +
   critical_section_bonus`. Record `gap_score` per topic in meta.json.
3. Rank topics. The top 2–5 by gap score are marked `deepen: true` — they get the most
   research effort in Stage 3 and the most reviewer attention in Stage 6.

Apply S3 anti-sycophancy to the plan: no "this could work" — state whether it will and
what's missing.

---

### Stage 3 — Research ×N (Performer subagents, isolated, parallel) (S4, C1)

Output: `03-research/t1.md … tN.md`

Dispatch N Claude Task subagents, one per topic. **Each subagent is isolated (C1)** — it
receives only its topic spec + relevant `_refs/`, never the Conductor's history. High-gap
topics (`deepen: true`) get richer briefs and, if warranted, a second research pass.
Pure Claude work — no ChatGPT.

---

### Stage 4 — Synthesize (Synthesizer SUBAGENT, isolated) (C1)

Output: `04-draft-vN.md`

**Dispatch a dedicated Synthesizer Task subagent.** It receives the N research files + the
draft template + (on REVISE) the `must_fix[]` list — and nothing else from the main
session. It returns `04-draft-vN.md`. The Conductor does not synthesize inline; this keeps
the main context flat (C1).

On REVISE rounds, `must_fix[]` items are injected here as explicit constraints, in
CRITICAL → MAJOR → MINOR order.

---

### Stage 5.5 — DETERMINISTIC PRE-GATE (⑧)

Runs in code/bash. No ChatGPT, no judgment. Run `scripts/pre_gate.sh <draft> [reflist]`.
Hard checks: no empty sections; citations ↔ references match; no placeholders
(TODO/TBD/[?]/XXX/Anonymous); unit/notation scan; LaTeX compiles (0 undefined refs/cites)
if applicable. ANY FAIL → fix → re-run. Only full PASS unlocks Stage 6. Output:
`04-pregate-vN.md`.

---

### Stage 6 — Review (ChatGPT, four sub-passes, isolated dispatch) (①②③④⑤⑦, C1)

Run in order. Save EVERY raw response verbatim into `traces/` (⑤). The Conductor dispatches
review consolidation to a subagent where heavy (C1), keeping only the consolidated
`05-review-vN.md` in main context.

**6a — Blind Scoring (①, NEW window every round).** Open a brand-new ChatGPT window.
Paste `review-prompts.md` §6a (begins "fresh, zero-context review; ignore prior rounds").
The 6a score is the ONLY number feeding the gate. Schema: overall score 0–10; verdict
Ready/Almost/No; weaknesses ranked CRITICAL>MAJOR>MINOR (②) with the 4-question rule.

**6b — Persona Passes (③, separate windows).** Run the `persona_set` from meta.json
(`persona-sets.md`). Each persona = its own window, one narrow lens, 4-question findings.
Concentrate persona effort on `deepen: true` topics (S4 linkage).

**6c — Claim→Evidence Web Audit (④, Conductor + WebSearch).** Extract every standard
citation (IGC/API/ASME/ISO/SOLAS), numeric claim, literature citation. Verify each via
web. Tag `[WEB-VERIFIED]` / `[WEB-CONTRADICTED]`→CRITICAL / `[WEB-INCONCLUSIVE]`→MAJOR
(describe at concept level, no clause number asserted). Never assert a standard's clause
without confirming the original text.

**6d — Kill-Argument (⑦, NEW window).** Paste `review-prompts.md` §6d. ≤200-word strongest
rejection. New fatal flaw → CRITICAL.

**Consolidate** 6a–6d into `05-review-vN.md`, findings CRITICAL→MINOR (②), raw text in
`<details>` (⑤). Build `must_fix[]` (CRITICAL+MAJOR).

---

### Stage 7 — DECIDE GATE (⑥, deterministic) + regression (⑤)

The Conductor RUNS, does not judge. `scripts/score_gate.py <run-dir>`:

```
PASS    if blind_score(6a) >= PASS_THRESHOLD (default 7)
        AND CRITICAL == 0 AND web_contradicted == 0 AND regression == 0
        AND all acceptance_criteria met
REVISE  if not PASS AND round < max_rounds AND regression == 0
RESTART if regression > 0  (prior-resolved item returned → premise/plan wrong)
        OR round >= max_rounds AND not PASS
```

Regression (⑤): compares this round's CRITICAL/MAJOR against prior-resolved items; a
reappearance auto-escalates to RESTART. On RESTART, if the failure traces to a `decisions[]`
entry, return to CHALLENGE (1.5), else to Plan (2).

PASS → `final.md`. REVISE → round N+1. 

---

## Runtime State

```
.orchestra/runs/<run-id>/
├── 01-brief.md
├── 01.5-challenge.md          ← S1/S2 challenge record
├── 02-research-plan.md         ← includes per-topic gap_score (S4)
├── 03-research/{t1..tN}.md
├── 04-draft-vN.md              ← produced by isolated Synthesizer (C1)
├── 04-pregate-vN.md            ← ⑧
├── 05-review-vN.md             ← ①②③④⑤⑦ consolidated
├── final.md
├── _refs/
├── traces/                     ← ⑤ raw per-pass reviews
└── meta.json                   ← criteria, decisions[] (C2), scores[], gaps, regression
```

### meta.json schema (v0.7.0)

```json
{
  "run_id": "20260617-pe-process-model",
  "goal": "...",
  "schema_version": "0.7.0",
  "modes": { "plan": "deep-research", "review": "pro-reasoning" },
  "persona_set": "lh2-paper",
  "forcing_question_route": "research-paper",
  "scope_mode": "HOLD",
  "acceptance_criteria": ["...", "..."],
  "decisions": [
    {"what": "...", "why": "...", "evidence_that_would_change_it": "..."}
  ],
  "pass_threshold": 7,
  "max_rounds": 5,
  "topics": [
    {"id": "t1", "gap_score": 7, "deepen": true},
    {"id": "t2", "gap_score": 2, "deepen": false}
  ],
  "rounds": [
    {"n": 1, "blind_score": 4, "critical": 3, "major": 5,
     "web_contradicted": 1, "criteria_met": false, "regression": 0, "verdict": "REVISE",
     "resolved_items": [], "findings": ["stream-table-45K"]}
  ]
}
```

---

## Context Durability — compaction priority (C3)

If the context window fills and the system triggers compaction, preserve in THIS order
(highest first). Never drop a higher tier to keep a lower one:

1. `acceptance_criteria` — what "done" means
2. `decisions[]` with their "why" (C2) — why the scope is what it is
3. Current stage's output file path + the active `must_fix[]`
4. The latest blind score and open CRITICAL findings
5. Everything else (prose history, prior-round narrative)

Because heavy stages run in isolated subagents (C1) and all state is on disk, a fresh
session can resume from `meta.json` + the latest stage files. On startup: if an in-progress
`meta.json` exists with timestamp < 24h, read it + latest stage files, give a 2-sentence
"resuming from Stage X" summary, and continue. Do NOT silently re-litigate `decisions[]` —
treat them as settled with their recorded rationale; if reversing one, say so explicitly
and supersede it in the log.

---

## Key Rules

- **CHALLENGE before produce (S1)** — never skip Stage 1.5. Verifying the wrong thing
  perfectly is the most expensive failure.
- **Blind scoring is ALWAYS a new window (①)** — never reuse a prior round's window for 6a.
- **Synthesize and Review run in isolated subagents (C1)** — the Conductor coordinates by
  file path, never inherits stage weight into the main session.
- **Preserve the "why" (C2)** — every scope decision logged with its rationale.
- **Pre-gate before review (⑧)** — never spend a manual ChatGPT pass on mechanical defects.
- **Standards are guilty until web-verified (④)** — unconfirmed clause = MAJOR minimum,
  concept-level description only.
- **The gate decides, not the Conductor (⑥)** — run `score_gate.py`, obey it.
- **Save FULL raw ChatGPT responses (⑤)** — never summarize reviews.
- **Anti-sycophancy (S3)** — banned phrases replaced by position + falsifiability, in
  Brief, Challenge, and Plan, not just Review.
- **Do not fabricate** — web-verification reports what was found; never invents numbers.

---

## Known Limits (honest boundaries)

This skill hardens verification as far as a manual-paste setup allows, but two limits are
structural, not bugs — naming them is part of using the tool well:

1. **The gate trusts the number you enter.** `score_gate.py` is deterministic over the
   `blind_score` you transcribe from ChatGPT (6a). If that number is mis-transcribed or
   self-edited, the gate faithfully computes the wrong verdict. Mitigation: the full raw 6a
   response is preserved verbatim in `traces/` (⑤), so any score is auditable against its
   source after the fact. The discipline is to transcribe honestly; the trace makes lapses
   detectable, not impossible.
2. **Manual window load scales with rounds.** One round is ~6 ChatGPT windows (1 plan + 1
   blind + 3 persona + 1 kill); three rounds ~16. This is real effort. Mitigation:
   confidence-gap weighting (S4) concentrates persona effort on `deepen: true` topics, and
   the deterministic pre-gate (⑧) prevents wasted passes — but a thorough run is genuinely a
   focused work session, not a one-click action. If that load is too high for a given task,
   reduce `max_rounds` or the persona count rather than skipping CHALLENGE or blind-scoring.

Neither limit is closed by adding more machinery; both are inherent to manual cross-model
verification. They resolve cleanly only with official API access (see `manual-vs-auto.md`).



```
/plugin marketplace add https://github.com/Luckguy1324-sudo/lucky_orchestra-plugin
/plugin install orchestra@lucky-orchestra
```

After install, `/orchestra` is available. Optional Playwright automation is opt-in
(`scripts/setup.sh`) — MANUAL paste is the default and loses zero rigor.

## Usage

```
/orchestra 폴리에틸렌 공정모델 논문용 설계
/orchestra                                    # → Brief + CHALLENGE first
/orchestra 공정모델 설계. 참조: @./refs/choi-2025.pdf
```

## References

- `verification-mechanisms.md` — rationale + evidence for ①–⑧
- `scoping-rules.md` — CHALLENGE gate, scope modes, confidence-gap rubric, banned phrases (S1–S4)
- `forcing-questions.md` — stage-routed forcing questions + pushback patterns (S2)
- `context-durability.md` — isolation, decision log, compaction priority (C1–C3)
- `review-prompts.md` — exact ChatGPT prompts for 6a/6b/6c/6d
- `persona-sets.md` — domain persona definitions (③)
- `manual-vs-auto.md` — manual-paste vs automation
- `examples/paper-process-model.md` — worked end-to-end example
