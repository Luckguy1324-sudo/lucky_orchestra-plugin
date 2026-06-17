# Worked Example — LH2 Reliquefaction Process Model (v0.7.0)

End-to-end run showing all three pillars: scoping (S), verification (①–⑧), context
durability (C). Abbreviated.

## Invocation
```
/orchestra 액화수소 재액화공정 모델 논문용 설계. 참조: @./refs/choi-2025.pdf
```

## Stage 1 — Brief
Captured: `persona_set: lh2-paper`, `forcing_question_route: research-paper`,
`acceptance_criteria` = [energy balance closes within 2%, every citation web-verified,
economic assumptions sourced, survives kill-argument with no new CRITICAL].

## Stage 1.5 — CHALLENGE (S1/S2/C2)
Routed questions for `research-paper`: Q2 (status quo), Q4 (narrowest wedge), Q5 (surprise).
- Q2: "Standard approach underperforms where for LH2?" → first answer "less efficient" →
  pushback → "warm-suction multi-stage is standard; the contribution is the recuperator duty
  split at 60 K."
- Q4: contribution = process architecture (not control, not LCA).
- Q5: the surprising finding = 86% of conversion heat releases at 60 K, forcing OPC.

Scope mode: **HOLD**. `decisions[]` written (C2):
```json
[{"what":"warm-suction baseline","why":"industry-standard; avoids 45K stream anomaly in N-2R+",
  "evidence_that_would_change_it":"a peer process with cryogenic suction and lower total kJ/kg"},
 {"what":"contribution = architecture","why":"control/LCA are secondary per Q4 wedge",
  "evidence_that_would_change_it":"reviewer shows architecture is not novel vs Choi 2025"}]
```
Gate question passed: Plan has scope + criteria + framing.

## Stage 2 — Plan + confidence gap (S4)
3 topics. `confidence_gap.py` scores: t1 warm/cryo trade-off gap=7 (deepen), t3 recuperator
split gap=6 (deepen), t2 compression sizing gap=2. Top-2 deepen=true.

## Stage 3 — Research ×3 (isolated, C1)
3 isolated subagents. t1 and t3 get richer briefs + second pass (deepen). Main context
unchanged — Conductor only holds file paths.

## Stage 4 — Synthesize (isolated Synthesizer, C1)
Dedicated subagent reads 3 research files + template, returns `04-draft-v1.md`. Conductor
context stays flat.

## Stage 5.5 — Pre-Gate ⑧
FAIL: `TBD` in cost section + `[Wartsila2024]` no reference. Fix → re-run → PASS. No ChatGPT
spent on mechanical defects.

## Stage 6 — Review (isolated dispatch)
- 6a blind (NEW window): 4/10. CRITICAL: stream table 45 K vs warm-suction claim.
- 6b personas: A(thermo) confirms 45 K + energy gap; B(econ) "no LCA boundary"→MAJOR;
  C(standards) "Choi 2025 misattributed"→MAJOR. Focus weighted to deepen topics t1/t3.
- 6c web audit: Choi 2025 exists [WEB-VERIFIED] but claim misattributed→MAJOR; "IGC clause"
  [WEB-INCONCLUSIVE]→MAJOR, concept-level only.
- 6d kill-argument: "stream table self-contradicts → energy analysis unreliable → reject" →
  already CRITICAL, no new.

## Stage 7 — Decide ⑥
`score_gate.py` → REVISE (score 4<7, 1 CRITICAL, criteria not met, round 1<5, regression 0).

## Round 2 (fresh Synthesizer subagent, C1)
Fixes all must_fix. 6a blind (new window) → 7/10, 0 CRITICAL, 0 web-contradicted. Regression
check: round-1 resolved items don't reappear → 0. Criteria met. **PASS** → final.md.

## What each pillar did
- **S1/S2** caught that the contribution is architecture, not control — focusing the whole run.
- **S4** put double research + reviewer weight on t1/t3 where the real risk was.
- **C1** kept the main context flat across 2 rounds — round 2 was as sharp as round 1, no rush.
- **C2** the "warm-suction why" survived; round 2 didn't re-litigate suction temperature.
- **①** kept round-2's 7/10 honest (fresh window).
- **②④⑦⑧** ordered fixes, caught the misattribution + unconfirmed clause, confirmed the core
  flaw, and saved a review pass on mechanical defects.
- **⑤⑥** proved no regression and produced the verdict by rule.
```
meta.json.rounds: [{n:1,score:4,...},{n:2,score:7,...}]  — fully auditable
meta.json.decisions: 2 entries with why  — durable across compaction
```
