# Migration Guide — v0.6.0 → v0.7.0

v0.7.0 is backward-compatible with existing runs. It adds two pillars (scoping, context
durability) and shifts stage numbers, but removes nothing from v0.6.0.

## At a glance

| Area | v0.6.0 | v0.7.0 |
|------|--------|--------|
| Stages | 6 + 2 gates | 7 + 3 gates (new CHALLENGE at 1.5) |
| Scoping | Brief interview only | CHALLENGE gate, forcing questions, scope mode, confidence gap |
| Heavy stages | Research isolated | Research + Synthesize + Review-consolidate isolated (C1) |
| "Why" preservation | none | decisions[] log (C2) + compaction priority (C3) |
| Stage numbers | Pre-Gate 4.5, Review 5, Decide 6 | Pre-Gate 5.5, Review 6, Decide 7 |

## Steps

### 1. Pull new files
After `/plugin update orchestra`, confirm these exist:
```
skills/orchestra/SKILL.md                                  (rewritten)
skills/orchestra/scripts/confidence_gap.py                 (new)
skills/orchestra/references/scoping-rules.md               (new)
skills/orchestra/references/forcing-questions.md           (new)
skills/orchestra/references/context-durability.md          (new)
```
Existing scripts (`pre_gate.sh`, `score_gate.py`, `setup.sh`) and references
(`verification-mechanisms.md`, `review-prompts.md`, `persona-sets.md`, `manual-vs-auto.md`)
are updated in place.

### 2. Make scripts executable
```
chmod +x skills/orchestra/scripts/*.sh
chmod +x skills/orchestra/scripts/*.py
```

### 3. In-progress runs
Old `meta.json` lacks `decisions[]`, `scope_mode`, `topics[]`. The scripts degrade safely:
- `score_gate.py` treats a missing `decisions[]` as empty (regression restarts at Plan, not
  CHALLENGE) and missing counts as 0.
- `confidence_gap.py` is opt-in; if you don't run it, all topics are treated equally as before.
To adopt fully, add `decisions[]` and `scope_mode` at the next CHALLENGE pass.

### 4. Adopt the highest-impact habits immediately
- **Run CHALLENGE (Stage 1.5)** on your next run — it's the single biggest quality lever.
- **Dispatch Synthesize/Review as subagents (C1)** — this is what keeps long runs from
  degrading. If your harness lacks subagents, the workflow still runs inline but loses the
  flat-context benefit; note that in `manual-vs-auto.md` terms it's a graceful degradation.

### 5. Nothing to undo
All v0.6.0 run artifacts keep their meaning. New files are `01.5-challenge.md` and the new
meta.json fields. Stage *content* is unchanged; only numbers shifted and two pillars were added.
