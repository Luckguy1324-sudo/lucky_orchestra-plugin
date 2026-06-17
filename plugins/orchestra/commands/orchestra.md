---
description: Run scoped, cross-validated, context-durable multi-AI orchestration — Claude conducts, ChatGPT reviews.
argument-hint: "[goal] (optional; omit to start with Brief + CHALLENGE)"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill
---

Invoke the **orchestra** skill to produce a scoped, cross-validated deliverable for: $ARGUMENTS

Follow the orchestra SKILL.md workflow exactly:

1. **Brief (Stage 1)** — if `$ARGUMENTS` is empty, interview (Q1–Q5). Capture
   `acceptance_criteria`, `persona_set`, `forcing_question_route`. Apply anti-sycophancy (S3).
2. **CHALLENGE (Stage 1.5)** — route forcing questions (S2, `forcing-questions.md`),
   pressure-test the premise, commit a scope mode (S1), and write `decisions[]` with WHY (C2).
   Do NOT skip — a perfectly verified wrong answer is the worst outcome.
3. **Model selection (Stage 1.6)** — recommend a ChatGPT mode per stage from goal keywords;
   record in `meta.json.modes`; user confirms or overrides.
4. **Plan (Stage 2)** — draft agenda; user pastes into NEW ChatGPT window. Score each topic's
   confidence gap (S4, `scripts/confidence_gap.py`); mark top 2–5 deepen=true.
5. **Research ×N (Stage 3)** — dispatch isolated Performer subagents (C1); deepen high-gap topics.
6. **Synthesize (Stage 4)** — dispatch an isolated Synthesizer subagent (C1); inject must_fix on REVISE.
7. **Pre-Gate (Stage 5.5, ⑧)** — run `scripts/pre_gate.sh`. On FAIL, fix and re-run. No review until PASS.
8. **Review (Stage 6)** — four sub-passes, raw traces saved:
   - 6a Blind scoring — NEW window every round (①)
   - 6b Persona passes — separate windows (③), focus on deepen=true topics
   - 6c Claim→evidence web audit — Conductor + WebSearch (④)
   - 6d Kill-argument — NEW window (⑦)
   Consolidate, findings CRITICAL→MINOR (②), raw text preserved (⑤).
9. **Decide (Stage 7, ⑥)** — run `scripts/score_gate.py <run-dir>`. Obey: PASS → final.md;
   REVISE → fresh Synthesizer subagent round N+1; RESTART → Plan or CHALLENGE.

Never skip CHALLENGE. Never invent scores or override the gate. Always blind-score in a fresh
window (①). Run Synthesize/Review in isolated subagents (C1). Preserve every scope decision's
"why" (C2). Never assert a standard's clause without web confirmation (④).
