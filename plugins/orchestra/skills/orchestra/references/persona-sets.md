# Persona Sets — Anti-Groupthink Lenses (mechanism ③)

Each persona set defines narrow, non-overlapping review lenses for a domain. The
Conductor picks the set at Stage 1 (Q5) and records it as `meta.json.persona_set`. Each
persona runs in its OWN ChatGPT window so they cannot converge on consensus.

Add your own sets by following the same structure. Keep lenses NON-overlapping — overlap
reintroduces the consensus pressure mechanism ③ exists to prevent.

---

## persona_set: `lh2-paper`  (liquid-hydrogen reliquefaction / process design papers)

**Persona A — Thermodynamic consistency**
Lens: energy & mass balances, stream tables, suction/discharge temperatures, refrigeration
cycle architecture, recuperator duty splits. Checks only whether the physics closes.
Ignore economics, writing, formatting.

**Persona B — Techno-economic & LCA**
Lens: cost basis assumptions, CAPEX/OPEX reasoning, LCA boundary definitions, sensitivity
treatment, whether economic claims follow from the stated assumptions. Ignore the physics
derivations themselves.

**Persona C — Standards & literature compliance**
Lens: every code/standard citation (IGC Code, API, ASME, ISO), every literature citation,
whether attributed claims are actually supported. Flags any clause number not confirmable.
Ignore content quality — only citation integrity.

---

## persona_set: `investment-thesis`  (AI 투자위원회-style investment analysis)

**Persona A — Bull-case integrity**
Lens: is the upside thesis internally coherent? Are the growth/moat/FCF claims supported
by the cited data? Does the TAM math hold? Ignore downside and valuation.

**Persona B — Bear-case / risk**
Lens: what kills this thesis? Competitive, regulatory, cyclical, balance-sheet, and
execution risks. MDD scenarios. Ignore the upside framing.

**Persona C — Data & source integrity**
Lens: every number (PER, FCF, market share, macro print) traced to a source; every source
checked for date and reliability. Flag stale or unsourced figures. Ignore the thesis itself.

---

## persona_set: `eng-doc`  (engineering documents — specs, policies, review memos)

**Persona A — Technical correctness**
Lens: are the engineering claims, calculations, and sizing correct and self-consistent?
Ignore wording and compliance framing.

**Persona B — Standards & regulatory compliance**
Lens: every standard/code/regulation cited — confirmable? Correctly applied? Scope
correct? Flag unconfirmed clause numbers. Ignore technical depth.

**Persona C — Operational / safety risk**
Lens: what fails in practice? Edge cases, failure modes, safety implications, ambiguity
that could be misread on site. Ignore academic rigor.

---

## persona_set: `generic`  (fallback when no domain set fits)

**Persona A — Logical soundness**
Lens: does the argument follow? Are there gaps, non-sequiturs, unstated assumptions?

**Persona B — Evidence integrity**
Lens: is every claim supported? Are sources real and correctly used?

**Persona C — Adversarial / failure**
Lens: where does this break? What would a hostile expert attack first?

---

## Rules for all persona sets

- Exactly 3 personas per set (more dilutes; fewer loses coverage). Tune per domain only
  with deliberate reason.
- Lenses MUST NOT overlap. If two personas would flag the same issue, narrow them.
- Each persona must be allowed to return "no issues in my lens" — forcing findings
  manufactures noise.
- The Conductor, never a persona, reconciles findings across personas.
