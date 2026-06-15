# Migration Guide — v0.5.2 → v0.6.0

v0.6.0 keeps the entire v0.5.2 backbone (6-stage workflow, Stage 2.5 Clarification Gate,
Performer escalation) and layers the v0.4.0 package's **hardened cross-validation** (①–⑧)
on top. It is backward-compatible with existing runs — the workflow gains two gates and a
restructured review stage, but nothing about the v0.5.2 run layout is removed.

## What changed at a glance

| Area | v0.5.2 | v0.6.0 |
|------|--------|--------|
| Stages | 6 (+ 2.5 Clarification) | 6 + 2.5 + 2 gates (4.5 Pre-Gate, deterministic Stage 6) |
| Review | single ChatGPT pass | 4 sub-passes (5a/5b/5c/5d) |
| Scoring | same window OK | blind, NEW window every round (①) |
| Findings | flat | severity-tagged + 4-question rule (②) |
| Reviewers | 1 | 1 model, 3 personas (③) |
| Claims | unverified | web-audited (④) |
| Decide | Conductor judgment | deterministic gate script (⑥) |
| State | brief meta | + acceptance_criteria, scores[], regression log |

## Steps

### 1. Pull the new files
After `/plugin update orchestra`, confirm these exist:
```
skills/orchestra/SKILL.md                       (rewritten)
skills/orchestra/scripts/pre_gate.sh            (new)
skills/orchestra/scripts/score_gate.py          (new)
skills/orchestra/references/verification-mechanisms.md   (new)
skills/orchestra/references/review-prompts.md            (new)
skills/orchestra/references/persona-sets.md              (new)
skills/orchestra/references/manual-vs-auto.md            (new)
```

### 2. Make scripts executable
```
chmod +x skills/orchestra/scripts/pre_gate.sh
chmod +x skills/orchestra/scripts/score_gate.py
chmod +x skills/orchestra/scripts/setup.sh
```

### 3. Existing in-progress runs
Old `meta.json` files lack the new fields. On the next Decide, `score_gate.py` will read
what's present. To use the deterministic gate, add to the latest round object:
- `blind_score` (int), `critical` (int), `web_contradicted` (int), `criteria_met` (bool)
- and at the top level: `pass_threshold` (default 7), `max_rounds`, `acceptance_criteria`

If those are absent the gate treats missing counts as 0 and a missing score as 0 (→ REVISE),
so old runs degrade safely rather than erroring.

### 4. Adopt the NEW-window discipline immediately
The single highest-impact change costs nothing: from now on, open a fresh ChatGPT window
for every blind-scoring pass (5a) and for the kill-argument (5d). This alone fixes the
score-inflation problem that made multi-round verification unreliable.

### 5. Pick your persona set
Set `meta.json.persona_set` to one of: `lh2-paper`, `investment-thesis`, `eng-doc`,
`generic` (or add your own in `references/persona-sets.md`).

## Nothing to undo
v0.6.0 does not delete or rename any v0.5.2 run artifact. `01-brief.md`, `02-research-plan.md`,
`03-research/`, `04-draft-vN.md`, `05-review-vN.md`, `final.md`, `_refs/`, `meta.json` (incl.
the `## Clarifications` section) all keep their meaning. The only addition is the `_review/`
directory holding the 4 sub-pass raw traces (`05a-blind`, `05b-<persona>`, `05c-claim-audit`,
`05d-kill`), preserved immutably as forensic trace (⑤).
