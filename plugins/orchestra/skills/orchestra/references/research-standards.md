# Research Standards — Depth, Breadth, Recency, Triangulation (R1–R3, v0.8.0)

orchestra v0.7.0 concentrated research *effort* (S4 confidence-gap) but never defined what
*adequate coverage* means. v0.8.0 makes "deep, broad knowledge construction" a checkable
standard instead of a hope. Knowledge-building is the first real stage of a paper, not a
warm-up — these rules govern it.

The standard is **dynamic, not hard-coded.** Which source types a topic requires is decided
during CHALLENGE/Plan and recorded on `meta.json.topics[].required_sources` — the same
layer-1/layer-2 pattern used for physics criteria. A pure-theory topic is not forced to cite
vendor data; a "latest industry trend" topic is not allowed to lean only on a 2009 paper.

---

## The Landscape pass (R1) — build knowledge BEFORE pressure-testing the premise

A blank-page user cannot honestly answer CHALLENGE's Q2 ("where does the status quo fail?")
or Q5 ("what's surprising?") before reading the field. So for the routes that need it, a
bounded **Landscape** pass runs at **Stage 0.5**, before CHALLENGE.

- **Routed.** Required for `research-paper` and `blank-page`; skipped for `has-users`,
  `paying`, and quick tasks (they already know their field). Set by `forcing_question_route`.
- **Breadth-first, bounded.** This is orientation, not the deep dive. Goal: map the
  territory well enough that CHALLENGE is grounded. It is explicitly NOT exhaustive — the
  depth happens later, in Stage 3, weighted by confidence gap.
- **Use the strongest tool here.** ChatGPT Pro **Deep Research** is at its best on broad
  literature/industry/market sweeps with citations — point it at knowledge-building, not
  only at agenda-planning. Claude WebSearch covers breadth in parallel.
- **Output `00-landscape.md`** (see `landscape-template.md`): status quo, recent trends
  (last `window_years`), key players/works, open controversies, and the candidate
  surprising finding. This becomes a required INPUT to CHALLENGE and seeds S4 gap scores
  (a topic the landscape shows as contested or thin starts with a higher gap).

A two-pass shape results, and it does not violate "challenge before produce" — the
Landscape produces knowledge, not the deliverable:

```
Brief → [0.5 Landscape: breadth orientation] → CHALLENGE (now grounded) → Plan
      → [3 Research: depth, per-topic, S4-weighted] → ...
```

---

## Source-type requirements (R2) — dynamic per topic

For each topic, CHALLENGE/Plan records `required_sources` — the subset that actually applies:

| Tag | Means | Demand it when |
|-----|-------|----------------|
| `peer_reviewed` | journal / conference papers | almost always |
| `industry` | vendor technical data, datasheets, white papers, patents, trade press | the topic touches real equipment, costs, or current practice |
| `standards` | codes/standards (IGC, API, ASME, ISO, IEC, SOLAS) | any regulatory / compliance / safety claim |
| `recent_trend` | last-`window_years` developments, news, conference proceedings | any "state of the art" / "latest" claim |

**Rule:** a topic tagged `recent_trend` or `industry` may NOT be satisfied by academic
papers alone. A Stage-3 research file that lacks a required source type is incomplete and
must be sent back before Synthesize — academic-only drift is the failure this prevents.

## Recency floor

For topics tagged `recent_trend`, set `research_standards.recency_floor` in meta.json:

```json
"research_standards": {
  "recency_floor": {"window_years": 3, "min_recent_share": 0.3, "enforce": true}
}
```

`pre_gate.sh` Check 4 parses publication years from the reference list and verifies the
share within `window_years`. `enforce:true` makes it a hard gate; otherwise it warns.
Foundational classics are fine — the floor only requires that *enough* of the evidence is
current, not that all of it is.

## Triangulation

Every load-bearing **quantitative** claim (a kJ/kg figure, a cost, an efficiency, a market
number) needs **≥2 independent sources**, or it is tagged `[SINGLE-SOURCE]` and treated as
a MAJOR finding at Review until corroborated. One vendor's brochure is not a fact.

## Conflicting sources → the disagreement ledger (links to P3)

When two credible sources disagree (common: a vendor claim vs. a peer-reviewed measurement),
do NOT silently pick one. Record a `disagreements[]` entry
(`{id, topic, claim, performer_pos, reviewer_pos, resolution, resolved_by_evidence}`) with
`gating:true` if the topic feeds `acceptance_criteria` or is `deepen:true`. The decide gate
then refuses PASS until the conflict is `evidence-resolved` — so an unresolved data conflict
cannot hide inside a "good enough" consensus.

---

## Missing-coverage review lens (R3)

Stage 6c web audit verifies that what IS cited is correct. It does not ask what is MISSING —
and for knowledge-building, missing coverage is the dominant failure mode. v0.8.0 adds a
coverage lens to every `persona_set` (see `persona-sets.md` → Persona D). Its only job:
"what important prior work, recent development, or industry datum is NOT here?" Concentrate
it on `deepen:true` topics. A coverage gap it finds is a MAJOR finding (or CRITICAL if the
omitted work would change the contribution claim).

---

## What this is not

This does not turn research into box-ticking. The `required_sources` set is chosen per
topic with judgment at CHALLENGE/Plan, not applied uniformly. The standard exists so that
"we did deep, broad research" is auditable from `meta.json.topics[]` and the reference list —
a falsifiable claim, consistent with S3 anti-sycophancy — rather than an assertion.
