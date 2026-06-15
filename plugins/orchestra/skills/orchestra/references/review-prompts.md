# Review Prompts — Exact ChatGPT Templates

These are the prompts the Conductor presents for the user to paste into ChatGPT. Each
specifies NEW window or SAME window. Honoring that is mechanism ①.

Placeholders in `{{ }}` are filled by the Conductor from `meta.json` and the current
draft.

---

## §5a — Blind Scoring  (NEW window, every round, no exceptions)

> This is a fresh, zero-context review. Ignore any prior review rounds, prior fix lists,
> or executor explanations — you have none. Judge the artifact ONLY from what is shown
> below.
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
> 1. **Overall score** (0–10, where 6 = weak accept, 7 = accept)
> 2. **Verdict:** Ready / Almost / No
> 3. **Summary** (2–3 sentences)
> 4. **Strengths** (ranked bullets)
> 5. **Weaknesses** — ranked and tagged CRITICAL > MAJOR > MINOR. For each CRITICAL and
>    MAJOR, answer all four: (a) what can go wrong, (b) why it is wrong/vulnerable,
>    (c) impact, (d) specific actionable fix.
> 6. **Missing references** (if any)
>
> Do NOT include style, naming, or speculative comments in weaknesses. Score strictly on
> substance: correctness, claims-vs-evidence alignment, internal consistency, self-
> containedness.

Save the verbatim response to `traces/5a_blind_run{{NN}}.md`. Extract the score and
findings into `meta.json` and `05-review-vN.md`.

---

## §5b — Persona Passes  (separate NEW window per persona)

Use the persona set named in `meta.json.persona_set` (definitions in `persona-sets.md`).
For each persona, paste its block into its OWN new window. Generic template:

> You are reviewing a {{venue_or_domain}} artifact with ONE narrow lens only:
> **{{persona_lens}}**.
>
> Ignore everything outside this lens. Do not comment on areas other personas cover.
>
> **Artifact:**
> {{full_draft_text}}
>
> For every issue you find within your lens, answer all four:
> (a) what can go wrong, (b) why, (c) impact, (d) specific fix.
> Tag each CRITICAL / MAJOR / MINOR. No style or speculative notes.
>
> If your lens reveals NO issues, say so explicitly — do not invent problems to seem useful.

Save each to `traces/5b_persona-{{X}}_run{{NN}}.md`.

---

## §5c — Claim → Evidence Web Audit  (Conductor runs this — Claude + WebSearch)

This is NOT pasted to ChatGPT. The Conductor executes it.

For each extracted claim, run the user-preference-compliant verification:

1. **Standards/code citations** (IGC Code, API 520/521, ASME, ISO, SOLAS, etc.):
   web-search the clause; if the original text is locatable, confirm the cited number
   and substance. Tag `[WEB-VERIFIED]`. If contradicted → `[WEB-CONTRADICTED]` → CRITICAL.
   If not locatable → `[WEB-INCONCLUSIVE]` → mark "requires original-text confirmation",
   treat as MAJOR, and in the artifact describe the requirement at the concept level
   without asserting a specific clause number.
2. **Numeric claims** (rates, capacities, efficiencies): sanity-check against sources or
   first-principles; flag implausible values.
3. **Literature citations**: confirm author/year/venue exist and that the attributed
   claim is actually supported by the cited work.

Output a table in `05-review-vN.md`:

| Claim | Type | Tag | Note |
|-------|------|-----|------|
| "IGC Code 8.x requires …" | standard | [WEB-INCONCLUSIVE] | clause number unconfirmed → concept-level only |
| "49,494 kg/h relieving rate" | numeric | [WEB-VERIFIED] | consistent with API 520 sizing |

---

## §5d — Kill-Argument  (NEW window, once per round)

> You are a senior {{venue_or_domain}} reviewer who has already DECIDED to REJECT this
> work. You are not here to help improve it.
>
> In **200 words or fewer**, write the single strongest, most defensible argument for
> rejection. Attack the core thesis or method, not surface presentation. Assume a smart,
> skeptical audience that will check your reasoning.
>
> **Artifact:**
> {{full_draft_text}}

Save to `traces/5d_kill_run{{NN}}.md`. If the kill-argument names a flaw not already in
5a/5b findings, the Conductor adds it as CRITICAL.

---

## Consolidation note

After 5a–5d, the Conductor writes `05-review-vN.md` containing:
- The blind score (from 5a only)
- A merged, deduplicated findings list ordered CRITICAL → MAJOR → MINOR
- The web-audit table (5c)
- The kill-argument verdict (5d)
- Full raw responses preserved in `<details>` blocks

Then the consolidated `must_fix[]` (CRITICAL + MAJOR) is what Stage 4 consumes on REVISE.
