#!/usr/bin/env bash
# pre_gate.sh — Mechanism ⑧: deterministic pre-gate (Stage 5.5).  v0.8.0
# Runs mechanical + physics-grounding checks on a draft BEFORE any ChatGPT review is spent.
# Exit 0 = all hard checks PASS (review may proceed). Exit 1 = a hard check FAILED.
#
# Usage: pre_gate.sh <draft-file> [reference-list-file] [streams-json] [meta-json]
#   <streams-json>  optional. If present (or a sibling streams.json exists), the v0.8.0
#                   physics grounding check runs: mass/energy closure, 2nd-law/no temp-cross,
#                   plus any machine-readable design criteria recorded in meta.json.decisions[].
# Pure bash/grep + a deterministic python physics checker — no model judgment, no network.

set -uo pipefail

DRAFT="${1:-}"
REFLIST="${2:-}"
STREAMS="${3:-}"
META="${4:-}"

if [[ -z "$DRAFT" || ! -f "$DRAFT" ]]; then
  echo "ERROR: draft file not found: '$DRAFT'" >&2
  echo "Usage: pre_gate.sh <draft-file> [reference-list] [streams-json] [meta-json]" >&2
  exit 2
fi

DIR="$(dirname "$DRAFT")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# auto-discover sibling streams.json / meta.json if not passed explicitly
[[ -z "$STREAMS" && -f "$DIR/streams.json" ]] && STREAMS="$DIR/streams.json"
[[ -z "$META" && -f "$DIR/../meta.json" ]] && META="$DIR/../meta.json"
[[ -z "$META" && -f "$DIR/meta.json" ]] && META="$DIR/meta.json"

FAIL=0
echo "=== Orchestra Pre-Gate (mechanism ⑧, v0.8.0) ==="
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
  echo "    FAIL — empty sections:"; echo "$empty_sections" | sed 's/^/      /'; FAIL=1
else
  echo "    PASS"
fi

# --- Check 2: unresolved placeholders -----------------------------------------
echo "[2] Placeholder check (TODO/TBD/[?]/XXX/Anonymous)"
placeholders=$(grep -nE 'TODO|TBD|\[\?\]|XXX|author[[:space:]]*=[[:space:]]*"Anonymous"' "$DRAFT" || true)
if [[ -n "$placeholders" ]]; then
  echo "    FAIL — unresolved placeholders:"; echo "$placeholders" | sed 's/^/      /'; FAIL=1
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
    if ! grep -qF "$key" "$REFLIST"; then missing+="$key"$'\n'; fi
  done <<< "$cites"
  if [[ -n "${missing// /}" ]]; then
    echo "    FAIL — citations with no matching reference entry:"
    echo "$missing" | sed '/^$/d; s/^/      /'; FAIL=1
  else
    echo "    PASS"
  fi
else
  echo "    SKIP — no reference list provided"
fi

# --- Check 4: recency floor (v0.8.0, advisory→hard if meta sets it) ------------
# If meta.json carries research_standards.recency_floor {min_recent_share, window_years},
# verify the reference list's publication years. Advisory unless 'enforce' is true.
echo "[4] Reference recency floor (v0.8.0)"
if [[ -n "$REFLIST" && -f "$REFLIST" && -n "$META" && -f "$META" ]] && command -v python3 >/dev/null 2>&1; then
  python3 - "$REFLIST" "$META" <<'PY'
import json, re, sys
reflist, meta_p = sys.argv[1], sys.argv[2]
meta = json.load(open(meta_p, encoding="utf-8"))
rs = (meta.get("research_standards") or {}).get("recency_floor")
if not rs:
    print("    SKIP — no recency_floor in meta.research_standards"); sys.exit(0)
import datetime
now = datetime.date.today().year
window = int(rs.get("window_years", 3)); share = float(rs.get("min_recent_share", 0.3))
years = [int(a + b) for a, b in re.findall(r'((?:19|20))(\d{2})', open(reflist, encoding='utf-8').read())]
if not years:
    print("    SKIP — no years parsed from reference list"); sys.exit(0)
recent = [y for y in years if y >= now - window]
got = len(recent) / len(years)
ok = got >= share
tag = "PASS" if ok else ("FAIL" if rs.get("enforce") else "WARN")
print(f"    {tag} — {len(recent)}/{len(years)} refs within last {window}y "
      f"(share {got:.0%}, floor {share:.0%})")
sys.exit(1 if (tag == "FAIL") else 0)
PY
  [[ $? -eq 1 ]] && FAIL=1
else
  echo "    SKIP — needs reference list + meta.json + python3"
fi

# --- Check 5: LaTeX compile (only if a .tex main file is detectable) ----------
echo "[5] LaTeX compile check"
TEXMAIN=""
case "$DRAFT" in *.tex) TEXMAIN="$DRAFT" ;; esac
if [[ -z "$TEXMAIN" && -f "$DIR/main.tex" ]]; then TEXMAIN="$DIR/main.tex"; fi
if [[ -n "$TEXMAIN" ]] && command -v latexmk >/dev/null 2>&1; then
  if latexmk -pdf -interaction=nonstopmode -halt-on-error "$TEXMAIN" >/tmp/orch_tex.log 2>&1; then
    undef=$(grep -cE 'undefined (references|citations)|There were undefined' /tmp/orch_tex.log || true)
    if [[ "$undef" -gt 0 ]]; then echo "    FAIL — undefined references/citations"; FAIL=1
    else echo "    PASS"; fi
  else
    echo "    FAIL — LaTeX did not compile (see /tmp/orch_tex.log)"; FAIL=1
  fi
else
  echo "    SKIP — not a LaTeX project or latexmk unavailable"
fi

# --- Check 6: PHYSICS GROUNDING (v0.8.0) --------------------------------------
# Runs only for process-model deliverables that ship a streams.json. Layer 1 universal
# invariants always; Layer 2 design criteria from meta.json.decisions[] checks.
echo "[6] Physics grounding (process-model deliverables)"
if [[ -n "$STREAMS" && -f "$STREAMS" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    if python3 "$SCRIPT_DIR/physics_check.py" "$STREAMS" ${META:+"$META"}; then
      echo "    PASS — physics grounding"
    else
      echo "    FAIL — physics grounding (see above)"; FAIL=1
    fi
  else
    echo "    SKIP — python3 unavailable"
  fi
else
  echo "    SKIP — no streams.json (non-process-model deliverable, or numbers not yet structured)"
fi

echo
if [[ "$FAIL" -eq 0 ]]; then
  echo "=== PRE-GATE: PASS — review may proceed (Stage 6) ==="
  exit 0
else
  echo "=== PRE-GATE: FAIL — fix the above, then re-run Stage 5.5. Do NOT review yet. ==="
  exit 1
fi
