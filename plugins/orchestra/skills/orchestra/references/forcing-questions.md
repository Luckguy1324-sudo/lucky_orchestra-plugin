# Forcing Questions — Stage-Routed Premise Pressure-Tests (S2)

Six forcing questions expose whether an idea is worth pursuing. They are NOT all asked every
time — they route by the work's stage. Asking the wrong question at the wrong stage wastes
effort and misframes the problem (asking a paper with solid prior results to "prove the gap
exists" is as misframed as asking a blank-page project to optimize a method it hasn't
chosen).

For each question, if the answer is vague, use the pushback pattern. Do not accept the first
vague answer — that is the entire point of a *forcing* question.

---

## The six questions

**Q1 — Demand Reality.** Who concretely needs this, and what do they do today without it?
- Pushback on vagueness: "Name one specific person/team/paper that hits this problem. What
  exactly do they do instead right now?"

**Q2 — Status Quo.** What is the current accepted approach, and precisely where does it fail?
- Pushback: "Don't describe the gap abstractly. Show the specific case where the status quo
  produces a wrong or worse result."

**Q3 — Desperate Specificity.** What is the narrowest, most concrete version of the problem?
- Pushback: "That's still a category. Give me the single most specific instance — exact
  numbers, exact conditions."

**Q4 — Narrowest Wedge.** What is the smallest piece that, if solved, still matters?
- Pushback: "If you could only deliver one thing here, what is it? Why does that one thing
  still justify the work?"

**Q5 — Observation & Surprise.** What did you observe that others missed or would find surprising?
- Pushback: "What's the non-obvious finding? If a domain expert would already expect your
  result, where is the contribution?"

**Q6 — Future-Fit.** Does this still matter in 1–2 years, or is it solving a transient artifact?
- Pushback: "If the surrounding tech/market/standard shifts as expected, does this still
  hold? What makes it durable?"

---

## Routing table — ask only the routed subset

| Work stage | Ask | Skip | Rationale |
|------------|-----|------|-----------|
| Pre-product / blank page | Q1, Q2, Q3 | Q4–Q6 | Establish the problem exists and is specific before narrowing |
| Has users / early traction | Q2, Q4, Q5 | Q1, Q3, Q6 | Demand is shown; focus on wedge and differentiation |
| Has paying customers | Q4, Q5, Q6 | Q1–Q3 | Don't insult proven demand; focus on durability and edge |
| Pure engineering initiative | Q2, Q4 | Q1, Q3, Q5, Q6 | No market question; focus on status-quo failure and wedge |
| **Research paper** | Q2, Q4, Q5 | Q1, Q3, Q6 | Gap vs. status quo, narrowest contribution, the surprising finding |
| **Investment thesis** | Q1, Q2, Q6 | Q3, Q4, Q5 | Who/what's mispriced, vs. consensus, and durability of the edge |

Set `meta.json.forcing_question_route` to the chosen row. The Conductor selects the row from
Brief Q5 (domain) and confirms with the user if ambiguous.

---

## Domain examples

**Research paper (LH2 thesis):**
- Q2 (Status Quo): "What's the standard reliquefaction approach and where exactly does it
  underperform for LH2?" → pushback if answer is "it's less efficient" → "show the specific
  operating point and the kJ/kg penalty."
- Q4 (Narrowest Wedge): "If the paper's only contribution were one thing, is it the process
  architecture, the control method, or the LCA result?"
- Q5 (Surprise): "What in your five-candidate analysis would surprise a process engineer?"

**Investment thesis (AI 투자위원회):**
- Q1 (Demand Reality): "Who specifically is mispricing this, and what consensus are they
  acting on?"
- Q2 (Status Quo): "What does the market currently believe, and where is that belief wrong?"
- Q6 (Future-Fit): "Does this edge survive the next 1–3 years, or is it a transient
  dislocation?"

---

## Why routing matters more than the questions

The questions themselves are not novel. The value is that **challenge happens before define,
and only the stage-appropriate questions are asked.** A blank-page project pushed on
"narrowest wedge" before demand is established skips the foundation; a paying-customer
product asked to "prove demand" wastes everyone's time. Route first, then pressure-test.
