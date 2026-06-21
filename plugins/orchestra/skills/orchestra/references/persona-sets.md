# Persona Sets — Anti-Groupthink Lenses (③, +R3 coverage in v0.8.0)

Each set defines narrow, non-overlapping review lenses for a domain. The Conductor picks the
set at Stage 1 (Q5) → `meta.json.persona_set`. Each persona runs in its OWN ChatGPT window so
they cannot converge. Keep lenses NON-overlapping — overlap reintroduces the consensus
pressure ③ exists to prevent.

**v0.8.0 adds Persona D — Missing-coverage (R3)** to every set. A–C verify what IS present
(and whether it is correct). D asks the orthogonal question: *what important thing is NOT
here?* For knowledge-building deliverables, missing coverage is the dominant failure mode,
and 6c (web audit) only checks cited claims, never omissions. D is concentrated on
`deepen:true` topics. A coverage gap → MAJOR (or CRITICAL if the omission would change the
contribution claim).

---

## persona_set: `lh2-paper`  (LH2 reliquefaction / process design papers)

**Persona A — Thermodynamic consistency.** Energy & mass balances, stream tables,
suction/discharge temperatures, refrigeration architecture, recuperator duty splits. Only
whether the physics closes. Ignore economics, writing, formatting.

**Persona B — Techno-economic & LCA.** Cost-basis assumptions, CAPEX/OPEX reasoning, LCA
boundaries, sensitivity treatment, whether economic claims follow from assumptions. Ignore
the physics derivations.

**Persona C — Standards & literature compliance.** Every code/standard citation (IGC, API,
ASME, ISO) and literature citation; whether attributed claims are supported. Flags any
unconfirmable clause number. Ignore content quality.

**Persona D — Missing coverage (R3).** What relevant prior work, recent reliquefaction
development, or industry/vendor datum is absent? Is a competing process architecture
unaddressed? Is the recency floor met for "state of the art" claims? Only omissions —
ignore whatever is already present.

---

## persona_set: `investment-thesis`  (AI 투자위원회-style analysis)

**Persona A — Bull-case integrity.** Is the upside thesis coherent? Are growth/moat/FCF
claims supported by cited data? Does the TAM math hold? Ignore downside and valuation.

**Persona B — Bear-case / risk.** What kills this thesis? Competitive, regulatory, cyclical,
balance-sheet, execution risks; MDD scenarios. Ignore the upside framing.

**Persona C — Data & source integrity.** Every number (PER, FCF, share, macro) traced to a
source; each source checked for date/reliability. Flag stale/unsourced figures. Ignore the
thesis itself.

**Persona D — Missing coverage (R3).** What competitor, regulatory shift, recent filing, or
industry development is NOT considered? Is a disconfirming data point omitted? Only gaps.

---

## persona_set: `eng-doc`  (specs, policies, review memos)

**Persona A — Technical correctness.** Are claims, calculations, sizing correct and
self-consistent? Ignore wording and compliance framing.

**Persona B — Standards & regulatory compliance.** Every standard/code/regulation —
confirmable? Correctly applied? Scope correct? Flag unconfirmed clause numbers. Ignore
technical depth.

**Persona C — Operational / safety risk.** What fails in practice? Edge cases, failure modes,
safety implications, on-site ambiguity. Ignore academic rigor.

**Persona D — Missing coverage (R3).** What applicable standard, prior incident, vendor
limitation, or operating scenario is absent from the document? Only omissions.

---

## persona_set: `generic`  (fallback)

**Persona A — Logical soundness.** Does the argument follow? Gaps, non-sequiturs, unstated
assumptions?

**Persona B — Evidence integrity.** Is every claim supported? Are sources real and correctly
used?

**Persona C — Adversarial / failure.** Where does this break? What would a hostile expert
attack first?

**Persona D — Missing coverage (R3).** What important perspective, source, or counter-case
is not present at all? Only omissions.

---

## Rules for all sets

- **3 correctness lenses (A–C) + 1 coverage lens (D).** A–C examine what is present; D
  examines what is absent. All four MUST stay non-overlapping.
- Lenses MUST NOT overlap. If two would flag the same issue, narrow them.
- Each persona may return "no issues in my lens" — forcing findings manufactures noise.
- The Conductor, never a persona, reconciles across personas.
- Concentrate persona effort — especially D — on `deepen: true` topics (S4).
- D may be skipped only for non-knowledge-building deliverables where coverage is not a
  quality axis (rare); record the skip with a reason.
