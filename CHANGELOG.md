# Changelog

## v0.8.0 (2026-06-21) — Knowledge-Building + Physics-Grounded + Convergence-Gated

v0.7.0 made verification trustworthy and scoping correct. v0.8.0 closes three remaining
gaps: (1) the deepest research tool wasn't aimed at building knowledge; (2) process-model
physics was never checked deterministically; (3) stopping was decided by a round counter,
which risks a "good-enough" consensus near the limit. Three pillars added, no existing
mechanism changed.

### Added — Knowledge building (R)
- **R1 Landscape pass (Stage 0.5)** — a bounded, breadth-first knowledge survey BEFORE the
  CHALLENGE gate, so a blank-page premise is pressure-tested against the actual field, not
  guesses. ChatGPT Deep Research is pointed here (knowledge-building), not only at planning.
  Routed: required for `research-paper`/`blank-page`, skipped otherwise.
  `references/landscape-template.md`, output `00-landscape.md`.
- **R2 Research-coverage standard** — per-topic `required_sources` (peer/industry/standards/
  recent_trend), a recency floor (pre_gate Check 4), and triangulation (≥2 sources for
  load-bearing quantitative claims). Dynamic per topic, not hard-coded.
  `references/research-standards.md`.
- **R3 Missing-coverage review lens** — Persona D added to every set; asks "what important
  work/development/datum is ABSENT?" (6c only checks what is present).

### Added — Physics grounding (PH)
- **2-layer process-physics pre-gate** — `scripts/physics_check.py`, wired into
  `pre_gate.sh` Check 6. Layer 1 (always): mass & energy closure, 2nd-law / no HX
  temperature-cross, dimensional sanity. Layer 2 (dynamic): design criteria (ΔT_min, T
  bounds, tolerance tightening) loaded from machine-readable `check` blocks on
  `meta.json.decisions[]` — so physical criteria FORM over rounds instead of being assumed.
  Operates on a structured `streams.json` the Synthesizer emits with the draft.

### Added — Convergence gate (CV)
- **score_gate.py rewrite** — stopping is now driven by convergence, with the round counter
  demoted to a safety rail:
  - **CONFIRM** verdict: a passing blind score must be confirmed by ONE independent blind
    pass on the same draft (both ≥ threshold, |diff| ≤ 1) — +1 window per run, not per round.
  - **Depth check**: PASS requires zero fresh MAJOR findings this round (`major_findings`).
  - **Disagreement ledger (P3)**: a gating Performer-vs-Reviewer disagreement that is not
    `evidence-resolved` blocks PASS — a papered-over compromise can no longer hide.
  - **Convergence diagnostic**: at max_rounds, a still-climbing trajectory auto-extends by
    one round (cap 8); an oscillating/stalled one returns **HUMAN_ESCALATE** with a diagnosis
    (trajectory, repeated findings, suspected decision) and explicit options — never an
    auto-pass to end the loop.
- Default `pass_threshold` raised 7 → 8.

### Changed
- Workflow is now **8 stages + 3 gates** (Landscape inserted at 0.5).
- `meta.json` schema extended: `landscape`, `research_standards.recency_floor`,
  `topics[].required_sources`, `disagreements[]`, round `confirm_score` + `major_findings`;
  `schema_version` → `0.8.0`.
- Compaction priority (C3) gains a tier: `decisions[]` design-criteria checks rank with
  acceptance_criteria (they are now enforced, not just rationale).

### Unchanged
- All 8 verification mechanisms (①–⑧) and the v0.7.0 scoping (S1–S4) / context-durability
  (C1–C3) pillars operate exactly as before, now on a knowledge-grounded, physics-checked,
  convergence-gated run.
- MANUAL mode (ChatGPT Pro by paste) remains default and loses zero rigor.

### Migration
- Backward compatible: a v0.7.0 `meta.json` still evaluates; missing v0.8.0 fields are
  treated as empty/false. To use the new guards, add the fields above. The physics check
  runs only when a `streams.json` is present, so non-process-model runs are unaffected.

## v0.7.0 (2026-06-17) — Scoping + Context Durability
## v0.6.0 — 8 hardened verification mechanisms integrated on the v0.5.2 backbone
## v0.5.2 — Stage 2.5 Clarification Gate, Performer escalation
## v0.4.0 — initial 8-mechanism hardened cross-validation
## v0.3.0 — automation + base 6-stage workflow
## v0.1.0 — initial Conductor/Performer/Reviewer workflow
