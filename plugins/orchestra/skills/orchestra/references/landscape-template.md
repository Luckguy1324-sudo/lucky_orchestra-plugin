# Landscape Template — `00-landscape.md` (Stage 0.5, R1)

The knowledge-construction pass. Fill this BEFORE the CHALLENGE gate so the premise is
pressure-tested against the actual field, not blank-state guesses. Breadth-first and
bounded — depth comes later in Stage 3. Apply S3 anti-sycophancy throughout: every entry
takes a position with a falsifiability condition, no "there are many approaches."

Run with ChatGPT Deep Research (literature/industry/market sweep) + Claude WebSearch
(breadth) in parallel. Save raw research alongside as you would Stage 3 outputs.

---

```markdown
# Landscape — <topic>

## 0. Scope of this survey
- Question being oriented: <one sentence>
- Boundary: what is IN and OUT of this survey (so depth later isn't pre-judged)

## 1. Status quo — the current accepted approach
- The standard method(s): <name them concretely>
- Where exactly it underperforms / breaks: <specific operating point, not "less efficient">
- Evidence: <citations — peer-reviewed AND industry>

## 2. Recent trends (last <window_years> years)
- What has changed recently: <developments, new entrants, new data>
- Sources skew recent here (recency floor applies): <cite years>

## 3. Key works and players
| Work / vendor / group | Claim or contribution | Source | Type (peer/industry/standard) |
|---|---|---|---|
| | | | |

## 4. Open controversies / conflicting evidence
- Where do credible sources DISAGREE? <list>
- For each: which side, what would settle it → seed a disagreements[] entry if it will gate

## 5. Candidate surprising finding (feeds CHALLENGE Q5)
- The non-obvious thing a domain expert might NOT already expect: <state it>
- Why it might be wrong (falsifiability): <condition>

## 6. Coverage self-check (feeds R3)
- What important area did this survey NOT reach yet? <honest gaps>
- Which topics look thin or contested → higher S4 gap_score later

## 7. Handoff to CHALLENGE
- Status quo known? (Q2 answerable now?)  yes/no
- Surprising finding identified? (Q5)      yes/no
- If either is "no", the Landscape is not done — extend before CHALLENGE.
```

---

## How it wires into the run

- **Output:** `00-landscape.md` in the run dir; raw research in `00-landscape-research/`.
- **Feeds CHALLENGE (1.5):** §1 answers Q2, §5 answers Q5 — no more blank-state forcing
  questions. The handoff test (§7) gates leaving Stage 0.5.
- **Seeds S4 (Plan):** §4 and §6 raise `gap_score` on contested/thin topics, so depth in
  Stage 3 lands where the landscape was weakest.
- **Seeds P3:** §4 conflicts become `disagreements[]` entries (gating if on a deepen/criteria
  topic).
- **Routed:** only `research-paper` / `blank-page` routes require this stage; others skip it.
