# Review Prompts — Exact ChatGPT Templates (Stage 6)

Prompts the Conductor presents for pasting into ChatGPT. Each specifies NEW window or SAME
window — honoring that is mechanism ①. Placeholders `{{ }}` are filled from meta.json and the
current draft.

---

## §6a — Blind Scoring  (NEW window, every round, no exceptions)

> This is a fresh, zero-context review. Ignore any prior review rounds, prior fix lists, or
> executor explanations — you have none. Judge the artifact ONLY from what is shown below.
>
> **Role:** Act as a senior {{venue_or_domain}} reviewer.
>
> **Artifact:**
> {{full_draft_text}}
>
> **Reference materials (if any):**
> {{refs_summary}}
>
> **Produce, in this exact structure:**
> 1. **Overall score** (0–10; 6 = weak accept, 7 = accept)
> 2. **Verdict:** Ready / Almost / No
> 3. **Summary** (2–3 sentences)
> 4. **Strengths** (ranked)
> 5. **Weaknesses** — ranked, tagged CRITICAL > MAJOR > MINOR. For each CRITICAL/MAJOR answer:
>    (a) what can go wrong, (b) why wrong/vulnerable, (c) impact, (d) specific actionable fix.
> 6. **Missing references** (if any)
>
> No style, naming, or speculative comments in weaknesses. Score on substance: correctness,
> claims-vs-evidence alignment, internal consistency, self-containedness.

Save verbatim to `traces/6a_blind_run{{NN}}.md`; extract score + findings to meta.json and
`05-review-vN.md`.

---

## §6b — Persona Passes  (separate NEW window per persona)

Use `meta.json.persona_set` (definitions in `persona-sets.md`). Each persona → its own window.

> You are reviewing a {{venue_or_domain}} artifact with ONE narrow lens only:
> **{{persona_lens}}**.
>
> Ignore everything outside this lens. Do not comment on areas other personas cover.
>
> **Artifact:**
> {{full_draft_text}}
>
> For every issue within your lens, answer: (a) what can go wrong, (b) why, (c) impact,
> (d) specific fix. Tag CRITICAL / MAJOR / MINOR. No style or speculative notes.
> If your lens reveals NO issues, say so — do not invent problems.

Pay special attention to topics marked `deepen: true` (high confidence-gap, S4). Save each to
`traces/6b_persona-{{X}}_run{{NN}}.md`.

---

## §6c — Claim → Evidence Web Audit  (Conductor runs — Claude + WebSearch, NOT pasted)

For each extracted claim:
1. **Standards/code** (IGC/API/ASME/ISO/SOLAS): web-search the clause; confirm number +
   substance → `[WEB-VERIFIED]`. Contradicted → `[WEB-CONTRADICTED]` → CRITICAL. Not
   locatable → `[WEB-INCONCLUSIVE]` → "requires original-text confirmation" → MAJOR,
   describe at concept level without asserting a clause number.
2. **Numeric**: sanity-check vs sources/first-principles; flag implausible values.
3. **Literature**: confirm author/year/venue exist and that the attributed claim is supported.

Output a table in `05-review-vN.md`:

| Claim | Type | Tag | Note |
|-------|------|-----|------|
| "IGC Code 8.x requires …" | standard | [WEB-INCONCLUSIVE] | clause unconfirmed → concept-level only |
| "49,494 kg/h relieving rate" | numeric | [WEB-VERIFIED] | consistent with API 520 sizing |

---

## §6d — Kill-Argument  (NEW window, once per round)

> You are a senior {{venue_or_domain}} reviewer who has already DECIDED to REJECT this work.
> You are not here to help improve it.
>
> In **200 words or fewer**, write the single strongest, most defensible argument for
> rejection. Attack the core thesis or method, not surface presentation. Assume a smart,
> skeptical audience that will check your reasoning.
>
> **Artifact:**
> {{full_draft_text}}

Save to `traces/6d_kill_run{{NN}}.md`. A flaw not already in 6a/6b → add as CRITICAL.

---

## Consolidation

After 6a–6d, write `05-review-vN.md`: blind score (6a only); merged deduplicated findings
CRITICAL→MINOR; web-audit table (6c); kill-argument verdict (6d); full raw responses in
`<details>`. The consolidated `must_fix[]` (CRITICAL+MAJOR) is what the Synthesizer subagent
consumes on REVISE.
