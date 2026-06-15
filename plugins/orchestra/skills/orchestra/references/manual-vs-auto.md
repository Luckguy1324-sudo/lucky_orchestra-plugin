# Manual Connection vs Automation

Orchestra is designed around a **ChatGPT Pro subscription used manually**. The 8 hardened
verification mechanisms (①–⑧) were specifically built so that manual paste does not
compromise verification quality — the discipline lives in the prompts and the
deterministic scripts, not in any API connection.

## MANUAL mode (default, recommended)

You paste prompts into ChatGPT yourself. The SKILL.md and `review-prompts.md` tell you,
for every ChatGPT interaction, whether to use a **NEW window** or the **SAME window**.

Why this is enough:
- **Mechanism ① (bias guard)** is purely about *which window* you use. A fresh chat for
  blind scoring is exactly as effective whether opened by a human or a script.
- **Mechanism ④ (web verification)** runs on the Claude side (WebSearch), not ChatGPT.
- **Mechanisms ⑤⑥⑧ (trace, gate, pre-gate)** are local scripts — no ChatGPT at all.
- **Mechanisms ②③⑦ (findings schema, personas, kill-argument)** are prompt design — they
  work identically by paste.

So MANUAL mode loses zero verification rigor. It only costs you the manual paste effort.

### The one discipline that matters

When the workflow says "NEW window", actually open a new ChatGPT conversation. The whole
point of mechanism ① is that the scorer has no memory of prior rounds. Reusing a window
to "save effort" silently reintroduces score inflation (real 3/10 → fake 8/10). This is
the single most important habit.

## AUTO mode (optional, opt-in)

`scripts/setup.sh` installs Playwright + an isolated Chromium to semi-automate the paste
steps. Caveats:

- This drives the ChatGPT **web UI**, not the official OpenAI API. It can break when the
  UI changes, and may be subject to OpenAI's terms — review them yourself.
- It is a *convenience* layer only. If it fails, orchestra falls back to MANUAL mode and
  nothing about the verification changes.
- Even in AUTO mode, mechanism ① is honored by opening fresh browser tabs/conversations
  for blind scoring.

## If you later get OpenAI API access

The cleanest upgrade path: replace the ChatGPT paste steps (5a, 5b, 5d, and Stage 2) with
official API calls. The verification design does not change at all — you would simply
swap "paste into a new window" for "new API request with no prior message history". The
NEW-window discipline maps directly onto "fresh message array". Until then, MANUAL mode
delivers the same rigor at the cost of paste effort.
