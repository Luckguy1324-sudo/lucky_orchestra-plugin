# Changelog

## v0.7.0 (2026-06-17) — Scoping + Context Durability

v0.6.0 made the *verification* trustworthy. v0.7.0 makes sure the **right problem** is
verified, and that a **long run doesn't degrade**. Two new pillars on top of the 8 mechanisms.

### Added — Scoping (S)
- **S1 CHALLENGE gate (Stage 1.5)** — pressure-tests the premise before any production work.
  Commits a scope mode (EXPAND/SELECTIVE/HOLD/REDUCE), held throughout. Includes the handoff
  completeness test.
- **S2 Stage-routed forcing questions** — six forcing questions routed by work stage
  (research-paper, investment-thesis, pure-engineering, etc.); only the stage-appropriate
  subset is asked, with pushback patterns for vague answers. `references/forcing-questions.md`.
- **S3 Anti-sycophancy constraints** — banned phrases with required replacements, applied in
  Brief, Challenge, and Plan (not only Review). Position + falsifiability condition required.
- **S4 Confidence-gap-weighted research** — `scripts/confidence_gap.py` scores each research
  topic; top 2–5 by gap get deeper research (Stage 3) and more reviewer attention (Stage 6).

### Added — Context durability (C)
- **C1 Isolated-subagent execution** — Synthesize (Stage 4) and Review consolidation (Stage 6)
  now run as isolated subagents, like Research already did. The Conductor coordinates by file
  path; its main context stays flat across rounds → no late-stage rushed artifact.
- **C2 Decision log** — `meta.json.decisions[]` records every durable scope decision as
  `{what, why, evidence_that_would_change_it}`. The "why" survives compaction.
- **C3 Explicit compaction priority** — a fixed tier order (acceptance_criteria > decisions >
  current stage > scores/findings > prose) so the right things survive a full window.

### Changed
- Workflow is now 7 stages + 3 gates. Stage numbers shifted: Pre-Gate 4.5→5.5, Review 5→6,
  Decide 6→7, with new CHALLENGE at 1.5.
- `score_gate.py` now records `restart_at` (CHALLENGE vs Plan) when a regression traces to a
  logged decision.
- `meta.json` schema extended: `decisions[]`, `scope_mode`, `forcing_question_route`,
  `topics[]` with `gap_score`/`deepen`, `schema_version`.

### Unchanged
- All 8 verification mechanisms (①–⑧) operate exactly as in v0.6.0, now on a correctly-scoped
  problem inside a context-durable run.
- MANUAL mode (ChatGPT Pro by paste) remains default and loses zero rigor.

## v0.6.0 — 8 hardened verification mechanisms integrated on the v0.5.2 backbone
## v0.5.2 — Stage 2.5 Clarification Gate, Performer escalation
## v0.4.0 — initial 8-mechanism hardened cross-validation
## v0.3.0 — automation + base 6-stage workflow
## v0.1.0 — initial Conductor/Performer/Reviewer workflow
