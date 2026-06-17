# Manual Connection vs Automation

orchestra is designed around a ChatGPT Pro subscription used manually. All mechanisms
(①–⑧, S1–S4, C1–C3) were built so manual paste does not compromise quality — the rigor lives
in the prompts and the deterministic scripts, not in any API connection.

## MANUAL mode (default, recommended)

You paste prompts into ChatGPT yourself. SKILL.md and `review-prompts.md` tell you, for every
ChatGPT interaction, whether to use a NEW window or the SAME window.

Why this loses zero rigor:
- **① bias guard** is about *which window* you use — a fresh chat for blind scoring works
  identically whether opened by a human or a script.
- **④ web verification** runs on the Claude side (WebSearch), not ChatGPT.
- **⑤⑥⑧ + S4 scoring + C1–C3** are local scripts / subagent dispatch — no ChatGPT at all.
- **②③⑦ + S1–S3** are prompt design — identical by paste.

So MANUAL mode costs only paste effort.

### The one discipline that matters

When the workflow says NEW window, open a new ChatGPT conversation. Mechanism ①'s entire
value is that the scorer has no memory of prior rounds. Reusing a window to "save effort"
silently reintroduces score inflation (real 3/10 → fake 8/10).

## AUTO mode (optional, opt-in)

`scripts/setup.sh` installs Playwright + isolated Chromium to semi-automate paste. Caveats:
it drives the ChatGPT web UI (not the official API), can break on UI changes, and may be
subject to OpenAI's terms — review them. It is convenience only; on failure orchestra falls
back to MANUAL and nothing about verification changes. Even in AUTO, ① is honored by opening
fresh conversations for blind scoring.

## If you later get OpenAI API access

Replace the paste steps (6a, 6b, 6d, Stage 2) with official API calls. The design doesn't
change — "paste into a new window" becomes "new API request with no prior message history".
The NEW-window discipline maps directly onto "fresh message array". Until then, MANUAL mode
delivers the same rigor at the cost of paste effort.
