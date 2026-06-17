#!/usr/bin/env bash
# pre_gate.sh — Mechanism ⑧: deterministic pre-gate (Stage 5.5).
# Runs mechanical checks on a draft BEFORE any ChatGPT review is spent on it.
# Exit 0 = all hard checks PASS (review may proceed). Exit 1 = a hard check FAILED.
#
# Usage: pre_gate.sh <draft-file> [reference-list-file]
# Pure bash/grep — no model judgment, no network. Safe to run repeatedly.

set -uo pipefail

DRAFT="${1:-}"
REFLIST="${2:-}"

if [[ -z "$DRAFT" || ! -f "$DRAFT" ]]; then
  echo "ERROR: draft file not found: '$DRAFT'" >&2
  echo "Usage: pre_gate.sh <draft-file> [reference-list-file]" >&2
  exit 2
fi

FAIL=0
echo "=== Orchestra Pre-Gate (mechanism ⑧) ==="
echo "Draft: $DRAFT"
echo

# --- Check 1: no empty sections -----------------------------------------------
echo "[1] Empty-section check"
empty_sections=$(awk '
  /^#{2,}[[:space:]]/ {
    if (header != "" && body == 0) { print header }
    header = $0; body = 0; next
  }
  /[^[:space:]]/ && $0 !~ /^#{2,}[[:space:]]/ { if (header != "") body = 1 }
  END { if (header != "" && body == 0) print header }
' "$DRAFT")
if [[ -n "$empty_sections" ]]; then
  echo "    FAIL — empty sections:"
  echo "$empty_sections" | sed 's/^/      /'
  FAIL=1
else
  echo "    PASS"
fi

# --- Check 2: unresolved placeholders -----------------------------------------
echo "[2] Placeholder check (TODO/TBD/[?]/XXX/Anonymous)"
placeholders=$(grep -nE 'TODO|TBD|\[\?\]|XXX|author[[:space:]]*=[[:space:]]*"Anonymous"' "$DRAFT" || true)
if [[ -n "$placeholders" ]]; then
  echo "    FAIL — unresolved placeholders:"
  echo "$placeholders" | sed 's/^/      /'
  FAIL=1
else
  echo "    PASS"
fi

# --- Check 3: citation ↔ reference matching -----------------------------------
echo "[3] Citation ↔ reference matching"
if [[ -n "$REFLIST" && -f "$REFLIST" ]]; then
  cites=$(grep -oE '\\cite\{[^}]+\}|\[[A-Za-z][A-Za-z0-9_-]*[0-9]{4}[a-z]?\]' "$DRAFT" \
            | sed -E 's/\\cite\{//; s/\}//; s/^\[//; s/\]$//' \
            | tr ',' '\n' | sed 's/[[:space:]]//g' | sort -u)
  missing=""
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    if ! grep -qF "$key" "$REFLIST"; then
      missing+="$key"$'\n'
    fi
  done <<< "$cites"
  if [[ -n "${missing// /}" ]]; then
    echo "    FAIL — citations with no matching reference entry:"
    echo "$missing" | sed '/^$/d; s/^/      /'
    FAIL=1
  else
    echo "    PASS"
  fi
else
  echo "    SKIP — no reference list provided (pass [reference-list-file] to enable)"
fi

# --- Check 4: notation/unit consistency (heuristic, advisory) -----------------
echo "[4] Notation/unit consistency scan (advisory)"
units=$(grep -oE '[0-9]+(\.[0-9]+)?[[:space:]]*(barg|bar|K|°C|kg/h|m3/h|kW|MW|kJ/kg)' "$DRAFT" \
          | sort | uniq -c | sort -rn | head -20 || true)
if [[ -n "$units" ]]; then
  echo "    INFO — unit tokens seen (review for consistency):"
  echo "$units" | sed 's/^/      /'
else
  echo "    INFO — no recognized unit tokens"
fi

# --- Check 5: LaTeX compile (only if a .tex main file is detectable) ----------
echo "[5] LaTeX compile check"
TEXMAIN=""
case "$DRAFT" in
  *.tex) TEXMAIN="$DRAFT" ;;
esac
if [[ -z "$TEXMAIN" && -f "$(dirname "$DRAFT")/main.tex" ]]; then
  TEXMAIN="$(dirname "$DRAFT")/main.tex"
fi
if [[ -n "$TEXMAIN" ]] && command -v latexmk >/dev/null 2>&1; then
  if latexmk -pdf -interaction=nonstopmode -halt-on-error "$TEXMAIN" >/tmp/orch_tex.log 2>&1; then
    undef=$(grep -cE 'undefined (references|citations)|There were undefined' /tmp/orch_tex.log || true)
    if [[ "$undef" -gt 0 ]]; then
      echo "    FAIL — LaTeX has undefined references/citations"
      FAIL=1
    else
      echo "    PASS"
    fi
  else
    echo "    FAIL — LaTeX did not compile (see /tmp/orch_tex.log)"
    FAIL=1
  fi
else
  echo "    SKIP — not a LaTeX project or latexmk unavailable"
fi

echo
if [[ "$FAIL" -eq 0 ]]; then
  echo "=== PRE-GATE: PASS — review may proceed (Stage 6) ==="
  exit 0
else
  echo "=== PRE-GATE: FAIL — fix the above, then re-run Stage 5.5. Do NOT review yet. ==="
  exit 1
fi
