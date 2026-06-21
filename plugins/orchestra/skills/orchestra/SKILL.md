---
name: orchestra
description: >
  Multi-AI collaboration orchestration. Claude Code Opus acts as Conductor,
  coordinating itself (Performer) and ChatGPT Pro (Reviewer) to produce one
  high-quality, cross-validated artifact. The Performer never grades its own
  work — generation is Claude, verification is ChatGPT. Use when the user says
  "orchestra", "오케스트라", "멀티 AI 협업", "교차검증 작업", or wants a
  research/design/writing deliverable rigorously scoped and cross-validated
  across two model families. v0.8.0 adds an early breadth-first knowledge-
  building Landscape pass (so a blank-page premise is grounded before it is
  challenged), a dynamic research-coverage standard (source-type, recency,
  triangulation) with a missing-coverage review lens, two-layer process-physics
  grounding (universal invariants always; design criteria formed over rounds),
  and a convergence-driven decide gate (confirmation pass, disagreement ledger,
  human-escalation on stall) on top of v0.7.0 scoping + the 8 verification
  mechanisms.
version: 0.8.0
license: MIT
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill
---

# Orchestra v0.8.0 — Knowledge-Grounded, Physics-Checked, Convergence-Gated Multi-AI Collaboration

Throw one goal and the Conductor coordinates a workflow with ChatGPT that (1) **builds
knowledge** of the field before committing to a premise, (2) challenges whether you're
solving the right problem, (3) researches with effort concentrated where the plan is
weakest, (4) cross-validates the result across two model families and checks process
physics deterministically, and (5) stops only on **convergence** — not when a round
counter runs out.

**Core principle:** the one who does the work does not verify the work. Performer =
Claude. Reviewer = ChatGPT.

**Five pillars (each maps to a reference doc):**
- **Knowledge building** — survey broad+deep before challenging the premise; coverage is a
  checkable standard. → `research-standards.md`, `landscape-template.md`
- **Scoping** — challenge the premise before producing, weight research by confidence gap.
  → `scoping-rules.md`, `forcing-questions.md`
- **Verification** — 8 hardened mechanisms make the review *trustworthy*.
  → `verification-mechanisms.md`
- **Physics grounding** — a process model's own numbers must close before any review is
  spent. → `physics_check.py` (Pre-Gate Check 6)
- **Context durability** — isolate heavy stages, preserve the "why". → `context-durability.md`

---

## The 8 Verification Mechanisms (unchanged from v0.6.0)

| # | Mechanism | Stage(s) | Why |
|---|-----------|----------|-----|
| ① | Reviewer-Bias Guard | 6a | Fresh context per scoring pass — stops score inflation |
| ② | Severity-Tagged Findings | 6 | CRITICAL > MAJOR > MINOR — fix order unambiguous |
| ③ | Anti-Groupthink Personas | 6 | Narrow non-overlapping lenses (A–C present, D absence) |
| ④ | Web-Verified Claims | 6c | Standards/figures/citations checked against the web |
| ⑤ | Forensic Review Trace | all | Raw reviews preserved, score trajectory logged, regression detected |
| ⑥ | Acquit-Gate Separation | 7 | Pass/fail is a deterministic rule, not Conductor discretion |
| ⑦ | Kill-Argument Adversary | 6d | One pass writes the strongest rejection |
| ⑧ | Deterministic Pre-Gate | 5.5 | Mechanical + physics checks pass BEFORE any expensive review |

## v0.7.0 — Scoping (S) + Context durability (C) (unchanged)

| Tag | Addition | Stage |
|-----|----------|-------|
| S1 | CHALLENGE gate — pressure-test the premise before any production | 1.5 |
| S2 | Stage-routed forcing questions | 1.5 |
| S3 | Anti-sycophancy constraints (banned phrases) in Brief+Plan | 1, 2 |
| S4 | Confidence-gap-weighted research | 2, 3 |
| C1 | Isolated-subagent execution for Synthesize + Review | 4, 6 |
| C2 | Decision-log ("why") in meta.json | 1.5, all |
| C3 | Explicit compaction priority order | all |

## New in v0.8.0 — Knowledge (R) + Physics (PH) + Convergence (CV)

| Tag | Addition | Stage | Why |
|-----|----------|-------|-----|
| R1 | Landscape pass — breadth-first knowledge survey BEFORE CHALLENGE | 0.5 | A blank-page premise can't be challenged against knowledge it doesn't have yet |
| R2 | Research-coverage standard — source-type/recency/triangulation, per-topic dynamic | 0.5, 2, 3 | "Deep+broad research" becomes auditable, not asserted; academic-only drift blocked |
| R3 | Missing-coverage review lens (Persona D) | 6 | 6c checks what's cited; nothing checked what's ABSENT |
| PH | 2-layer process-physics pre-gate | 5.5 | A model whose own numbers contradict each other must never reach review |
| CV | Convergence-driven decide gate | 7 | Stop on convergence, not a counter — kills "good-enough" consensus near the limit |

---

## Role Separation

| Role | Model | Responsibility |
|------|-------|----------------|
| Conductor (지휘자) | Claude Code Opus (main session) | Intent, routing, gate execution, file-only coordination — NOT judging, NOT heavy synthesis |
| Landscape researcher | ChatGPT Deep Research + Claude WebSearch | Breadth-first knowledge survey (Stage 0.5, R1) |
| Challenger | Claude (Conductor, scoping mode) | Runs the CHALLENGE gate forcing questions |
| Researcher Planner | ChatGPT (mode-selected) | Designs the research agenda |
| Performer ×N (연주자) | Claude Task subagents (isolated) | Executes each research topic in parallel, to the R2 coverage standard |
| Synthesizer | Claude Task subagent (isolated) | Integrates research into a draft + emits `streams.json` for physics-bearing work — C1 |
| Reviewer (검토자) | ChatGPT (mode-selected) | Deep review under enforced schema, persona passes A–D |
| Adversary (반론자) | ChatGPT (mode-selected) | Writes the strongest rejection |

**Why the Conductor delegates Synthesize and Review (C1):** so the main session never
accumulates the full weight of every stage. The Conductor passes file paths and receives
file paths. Its own context stays roughly constant regardless of how many rounds run.

---

## ChatGPT Mode Catalog

| ID | Display | Best for | Est. time |
|----|---------|----------|-----------|
| `deep-research` | Pro Deep Research | Landscape survey (R1), citations, literature, market/industry research | 5–30 min |
| `pro-reasoning` | Pro Reasoning | Modeling, proofs, verification | 1–5 min |
| `thinking` | Thinking | General review | 30 s–2 min |
| `standard` | Standard | Summarize, format conversion | instant |

**Point Deep Research at knowledge-building (R1), not only at agenda-planning** — that is
where its breadth+citation strength pays off most. At Stage 1.6 the Conductor recommends a
mode per stage; the user confirms.

**Manual connection:** ChatGPT Pro via manual paste (no API). Each interaction specifies NEW
window (bias-sensitive) or SAME window (context-continuing). Honoring that is mechanism ①.

---

## Workflow — 8 Stages + 3 Gates

```
 1   Brief ─────────────── interview, capture acceptance_criteria (S3 anti-sycophancy)
 0.5 [LANDSCAPE R1/R2] ─── breadth-first knowledge survey (routed) → 00-landscape.md
                            (ChatGPT Deep Research + Claude WebSearch); grounds the premise
 1.5 [CHALLENGE GATE S1/S2] ── forcing questions (now answerable): right problem? scope mode
                                  └─ writes decisions[] with WHY (C2); conflicts → disagreements[]
 1.6 Model selection ─── recommend ChatGPT mode per stage, user confirms
 2   Plan Research (ChatGPT, NEW window) ── agenda + gap scores + required_sources per topic (S4/R2)
 3   Research ×N (Performer subagents, isolated, parallel) ── deepen high-gap first; meet R2 coverage
 4   Synthesize (Synthesizer SUBAGENT, isolated) ── integrate; emit streams.json (physics work); C1
 5.5 [PRE-GATE ⑧] ── mechanical + recency + PHYSICS checks (code) BEFORE any review
 6   Review (ChatGPT, isolated dispatch C1):
       6a Blind score    (NEW window every round)        ①②
       6b Persona passes A–D (separate windows)          ③ + R3 coverage
       6c Web audit      (Conductor + WebSearch)         ④
       6d Kill-argument  (NEW window)                    ⑦
 7   [DECIDE GATE ⑥/CV] ── score_gate.py: PASS / CONFIRM / REVISE / RESTART / HUMAN_ESCALATE
                          └─ convergence diagnostic + disagreement ledger + regression (⑤)
```

PASS → `final.md`. CONFIRM → one confirmation blind pass, then re-gate. REVISE → round N+1.
RESTART → back to Plan (or CHALLENGE if the premise failed). HUMAN_ESCALATE → stop, get a
human decision.

---

### Stage 1 — Brief (Conductor interview)
Output: `01-brief.md`. As v0.7.0. Q5 (domain) now also sets `forcing_question_route`, which
decides whether the Landscape pass (0.5) is required.

### Stage 0.5 — LANDSCAPE (R1, R2) — knowledge building BEFORE the challenge

**Runs before CHALLENGE for `research-paper` and `blank-page` routes; skipped for
has-users/paying/quick tasks.** A blank-page user cannot honestly answer "where does the
status quo fail?" (Q2) or "what's surprising?" (Q5) without first reading the field. So
build the knowledge first — but bounded: this is breadth-first orientation, not the deep
dive (that is Stage 3).

1. **Sweep broad with the strongest tool.** ChatGPT Deep Research (literature + industry +
   market, with citations) and Claude WebSearch (breadth) in parallel. Cover peer-reviewed
   work AND industry/vendor/standards/recent-trend sources per `research-standards.md`.
2. **Fill `00-landscape.md`** (`landscape-template.md`): status quo + where it breaks,
   recent trends (last `window_years`), key works/players, open controversies, candidate
   surprising finding, and an honest coverage self-check.
3. **Handoff test:** the premise is grounded only when §1 (status quo) and §5 (surprise) are
   answerable. If not, extend before leaving 0.5.
4. **Seed downstream:** controversies → `disagreements[]`; thin/contested topics → higher S4
   `gap_score`. Raw research saved in `00-landscape-research/`.

Output: `00-landscape.md`.

### Stage 1.5 — CHALLENGE GATE (S1, S2) + decision log (C2)
As v0.7.0, but now **fed by the Landscape**: forcing questions are pressure-tested against
`00-landscape.md`, not blank-state guesses. Commit one scope mode (EXPAND/SELECTIVE/HOLD/
REDUCE); write `decisions[]` as `{what, why, evidence_that_would_change_it}`. A design
criterion that is decided here (e.g. ΔT_min) may carry a machine-readable `check` so the
physics pre-gate can enforce it later (PH Layer 2). Output: `01.5-challenge.md`.

### Stage 1.6 — Model selection
Conductor recommends ChatGPT modes per stage → `meta.json.modes`. User confirms.

### Stage 2 — Plan Research (ChatGPT, NEW window) + gap scoring (S4) + coverage tags (R2)
Output: `02-research-plan.md`. As v0.7.0, plus: for each topic record `required_sources`
(peer/industry/standards/recent_trend) per `research-standards.md`. Top 2–5 by `gap_score`
are `deepen:true`.

### Stage 3 — Research ×N (Performer subagents, isolated, parallel) (S4, R2, C1)
Output: `03-research/t1.md … tN.md`. Isolated subagents, one per topic. A topic tagged
`recent_trend` or `industry` may NOT be satisfied by academic papers alone — a research file
missing a required source type is incomplete and is sent back before Synthesize.
Load-bearing quantitative claims need ≥2 independent sources or carry `[SINGLE-SOURCE]`.

### Stage 4 — Synthesize (Synthesizer SUBAGENT, isolated) (C1) + structured data (PH)
Output: `04-draft-vN.md` (+ `streams.json` for process-model work). The dedicated
Synthesizer receives the N research files + template + (on REVISE) `must_fix[]`. **For a
process-model deliverable it must also emit `streams.json`** — the machine-readable stream
table / unit balances / heat exchangers the physics pre-gate checks. Prose numbers and
`streams.json` must agree.

### Stage 5.5 — DETERMINISTIC PRE-GATE (⑧, +PH)
Runs in code. `pre_gate.sh <draft> [reflist] [streams.json] [meta.json]`. Hard checks:
empty sections; citation↔reference match; placeholders; **recency floor (R2, if set);**
LaTeX compiles; and **physics grounding (PH)** when a `streams.json` is present —
`physics_check.py` runs Layer 1 (mass/energy closure, 2nd-law/no temp-cross, dimensions)
always, and Layer 2 (design criteria from `decisions[].check`) dynamically. ANY FAIL → fix
→ re-run. Only full PASS unlocks Stage 6. Output: `04-pregate-vN.md`.

### Stage 6 — Review (ChatGPT, four sub-passes, isolated dispatch) (①②③④⑤⑦, R3, C1)
As v0.7.0. **6b now runs personas A–D** — D is the missing-coverage lens (R3): "what
important prior work / recent development / industry datum is ABSENT?", concentrated on
`deepen:true` topics. A coverage gap → MAJOR (CRITICAL if it changes the contribution
claim). Save every raw response in `traces/` (⑤). Build `must_fix[]` (CRITICAL+MAJOR).
**Record per round:** `blind_score`, `confirm_score` (when run), `critical`, `major_findings`
(ids), `web_contradicted`, `findings`, `resolved_items`, `criteria_met`.

### Stage 7 — DECIDE GATE (⑥, CV) + regression (⑤)
The Conductor RUNS `scripts/score_gate.py <run-dir>`; it does not judge.

```
PASS    if blind_score >= threshold(8) AND confirm_score >= threshold AND |blind-confirm| <= 1
        AND critical == 0 AND web_contradicted == 0 AND regression == 0
        AND new_major == 0 (no fresh MAJOR this round — depth reached)
        AND open_gating_disagreements == 0
        AND all acceptance_criteria met
CONFIRM if the above holds but confirm_score not yet recorded
        → run ONE confirmation blind pass (NEW window, SAME draft), record confirm_score, re-gate
REVISE  if not PASS AND round < max_rounds AND regression == 0
RESTART if regression > 0  (prior-resolved item returned → premise/plan wrong)
HUMAN_ESCALATE at max_rounds with no PASS:
        - trajectory still climbing toward the bar (monotonic, gap ≤ 1) → extend max_rounds +1
          (cap 8) and REVISE — one more round, NOT a relaxed pass
        - oscillating / stalled (repeated finding) → STOP, emit diagnosis (trajectory,
          repeated findings, suspected decision) + options; the gate never auto-passes to
          end the loop
```

Exit codes: PASS 0, REVISE 10, RESTART 20, CONFIRM 30, HUMAN_ESCALATE 40. PASS → `final.md`.

---

## Runtime State

```
.orchestra/runs/<run-id>/
├── 00-landscape.md             ← R1 knowledge survey (routed)
├── 00-landscape-research/      ← raw breadth research
├── 01-brief.md
├── 01.5-challenge.md           ← S1/S2 + decisions[]
├── 02-research-plan.md         ← gap_score + required_sources per topic (S4/R2)
├── 03-research/{t1..tN}.md
├── 04-draft-vN.md              ← isolated Synthesizer (C1)
├── streams.json                ← machine-readable process data (PH; physics-bearing work)
├── 04-pregate-vN.md            ← ⑧ + recency + physics
├── 05-review-vN.md             ← ①②③④⑤⑦ + R3 consolidated
├── final.md
├── _refs/
├── traces/                     ← ⑤ raw per-pass reviews
└── meta.json                   ← criteria, decisions[], scores[], gaps, disagreements[], regression
```

### meta.json schema (v0.8.0)

```json
{
  "run_id": "20260621-lh2-reliq",
  "goal": "...",
  "schema_version": "0.8.0",
  "modes": { "landscape": "deep-research", "plan": "deep-research", "review": "pro-reasoning" },
  "persona_set": "lh2-paper",
  "forcing_question_route": "research-paper",
  "scope_mode": "HOLD",
  "acceptance_criteria": ["energy balance closes within 2%", "every citation web-verified"],
  "research_standards": { "recency_floor": {"window_years": 3, "min_recent_share": 0.3, "enforce": true} },
  "decisions": [
    {"what": "ΔT_min 3K at HX1", "why": "pinch study round 2",
     "evidence_that_would_change_it": "a feasible design below 3K",
     "check": {"type": "dt_min", "hx": "HX1", "min_K": 3}}
  ],
  "pass_threshold": 8,
  "max_rounds": 5,
  "topics": [
    {"id": "t1", "gap_score": 7, "deepen": true, "required_sources": ["peer_reviewed","industry","recent_trend"]},
    {"id": "t2", "gap_score": 2, "deepen": false, "required_sources": ["peer_reviewed"]}
  ],
  "disagreements": [
    {"id": "d1", "topic": "t1", "claim": "...", "performer_pos": "...", "reviewer_pos": "...",
     "gating": true, "resolution": "evidence-resolved", "resolved_by_evidence": "Choi 2025 fig.4"}
  ],
  "rounds": [
    {"n": 1, "blind_score": 4, "confirm_score": null, "critical": 3, "major_findings": ["econ-bound"],
     "web_contradicted": 1, "criteria_met": false, "regression": 0, "verdict": "REVISE",
     "resolved_items": [], "findings": ["stream-table-45K"]}
  ]
}
```

---

## Context Durability — compaction priority (C3, v0.8.0)

Preserve in THIS order (highest first); never drop a higher tier to keep a lower one:

1. `acceptance_criteria` — what "done" means
2. `decisions[]` with their "why" and any enforced `check` (C2) — why the scope is what it is
3. Current stage's output file path + active `must_fix[]`
4. Open gating `disagreements[]` (unresolved) and the latest blind/confirm score + open CRITICAL
5. Everything else (prose history, prior-round narrative)

All state is on disk; a fresh session resumes from `meta.json` + latest stage files. On
startup with an in-progress `meta.json` < 24h old, read it + latest files, give a 2-sentence
"resuming from Stage X" summary, continue. Do NOT silently re-litigate `decisions[]`; reverse
one only by explicitly superseding it in the log.

---

## Key Rules

- **Survey before challenge (R1)** — for paper/blank-page routes, never run CHALLENGE on a
  blank knowledge base. Build `00-landscape.md` first.
- **Coverage is a standard, not a hope (R2)** — a `recent_trend`/`industry` topic is not done
  on academic papers alone; load-bearing numbers need ≥2 sources.
- **CHALLENGE before produce (S1)** — verifying the wrong thing perfectly is the most
  expensive failure.
- **The model's own numbers must close (PH)** — physics pre-gate before any review; a draft
  that contradicts itself never costs a manual pass.
- **Blind scoring is ALWAYS a new window (①)**; **PASS must be confirmed (CV)** — one
  independent confirmation pass on the same draft.
- **No fresh MAJOR at PASS (CV)** — if a new MAJOR appears, depth wasn't reached; keep going.
- **A papered-over compromise blocks PASS (P3)** — a gating disagreement must be
  `evidence-resolved`, not deferred.
- **Stop on convergence, not the counter (CV)** — at the limit, extend if climbing, escalate
  to a human if stalled; never auto-pass to end the loop.
- **Standards are guilty until web-verified (④)** — unconfirmed clause = MAJOR minimum,
  concept-level description only.
- **The gate decides, not the Conductor (⑥)** — run `score_gate.py`, obey it.
- **Save FULL raw ChatGPT responses (⑤)**; **anti-sycophancy (S3)** in Brief/Challenge/Plan;
  **do not fabricate** — web-verification reports what was found.

---

## Known Limits (honest boundaries)

1. **Physics closure proves consistency, not correctness.** `physics_check.py` catches a
   stream table that contradicts itself; it cannot catch a fabricated-but-self-consistent
   one. The numbers' correctness is established downstream by the Reviewer (ChatGPT) and the
   web audit (⑥c). Closure is necessary, not sufficient.
2. **The gate trusts the numbers you enter.** `score_gate.py` is deterministic over the
   `blind_score`/`confirm_score`/finding counts transcribed from ChatGPT. Mis-transcription
   yields a faithful-but-wrong verdict. Mitigation: full raw responses preserved in
   `traces/` (⑤) make any score auditable after the fact. The confirmation pass (CV) makes a
   single lenient score insufficient on its own.
3. **Manual window load scales with rounds.** One round ≈ 7 ChatGPT windows (1 plan + 1 blind
   + 4 persona + 1 kill), plus the Landscape pass and one confirmation pass per run. This is
   a focused work session, not one click. Mitigation: confidence-gap weighting (S4)
   concentrates persona effort on `deepen:true` topics; the deterministic pre-gate (⑧+PH)
   prevents wasted passes; the confirmation pass is once per run, not per round. If load is
   too high, reduce `max_rounds` or persona count — never skip CHALLENGE, Landscape, or
   blind-scoring.

These resolve cleanly only with official API access (see `manual-vs-auto.md`).

---

## Install

```
/plugin marketplace add https://github.com/Luckguy1324-sudo/lucky_orchestra-plugin
/plugin install orchestra@lucky-orchestra
```

After install, `/orchestra` is available. Optional Playwright automation is opt-in
(`scripts/setup.sh`) — MANUAL paste is the default and loses zero rigor.

## Usage

```
/orchestra 액화수소 재액화공정 모델 논문용 설계. 참조: @./refs/choi-2025.pdf
/orchestra                                    # → Brief + Landscape + CHALLENGE first
```

## References

- `research-standards.md` — Landscape pass, source-type/recency/triangulation, coverage (R1–R3)
- `landscape-template.md` — the `00-landscape.md` knowledge-map template (R1)
- `scoping-rules.md` — CHALLENGE gate, scope modes, confidence-gap rubric, banned phrases (S1–S4)
- `forcing-questions.md` — stage-routed forcing questions + pushback patterns (S2)
- `verification-mechanisms.md` — rationale + evidence for ①–⑧
- `persona-sets.md` — domain persona definitions A–D (③, R3)
- `context-durability.md` — isolation, decision log, compaction priority (C1–C3)
- `review-prompts.md` — exact ChatGPT prompts for 6a/6b/6c/6d
- `manual-vs-auto.md` — manual-paste vs automation
- `examples/paper-process-model.md` — worked end-to-end example
- `scripts/physics_check.py` — 2-layer process-physics grounding (PH)
- `scripts/score_gate.py` — convergence decide gate (CV) ; `scripts/pre_gate.sh` — ⑧+PH
```
```
