#!/usr/bin/env bash
# score-check.sh — validate review file, print verdict + score
#
# Usage: score-check.sh <review-file> [<pass-threshold>] [<round-no>] [<max-rounds>]
#
# Output (stdout, one line):
#   PASS|REVISE|RESTART|PARTIAL|PASS_WITH_WARNINGS|PARSE_ERROR <score>
#
# Logic delegated to score_check.py for richer validation:
#   - Inconsistency between verdict and must_fix (PASS with must_fix → REVISE)
#   - Score below pass_threshold but verdict=PASS → escalates to REVISE
#   - partial: true in frontmatter → PARTIAL verdict
#   - Round-limit awareness (round >= max_rounds + REVISE → PASS_WITH_WARNINGS)
#
# Exit codes:
#   0  — parsed successfully (verdict determined)
#   1  — file missing
#   2  — parse error

set -euo pipefail

REVIEW_FILE="${1:-}"
PASS_THRESHOLD="${2:-8.0}"
ROUND_NO="${3:-1}"
MAX_ROUNDS="${4:-3}"

[[ -z "$REVIEW_FILE" ]] && { echo "Usage: $0 <review-file> [pass-threshold] [round-no] [max-rounds]" >&2; exit 1; }
[[ -f "$REVIEW_FILE" ]] || { echo "Review file not found: $REVIEW_FILE" >&2; exit 1; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PY_VALIDATOR="${SCRIPT_DIR}/score_check.py"

# Prefer the Python validator. Fallback to inline grep if Python missing.
if command -v python3 >/dev/null 2>&1 && [[ -f "$PY_VALIDATOR" ]]; then
  python3 "$PY_VALIDATOR" "$REVIEW_FILE" \
    --pass-threshold "$PASS_THRESHOLD" \
    --round "$ROUND_NO" \
    --max-rounds "$MAX_ROUNDS"
  exit $?
fi

# === Minimal fallback (no python) — same behavior as v0.2.x ===
YAML_BLOCK=$(awk '
  /^```yaml/ { in_block=1; next }
  /^```/ && in_block { exit }
  in_block { print }
' "$REVIEW_FILE")

if [[ -z "$YAML_BLOCK" ]]; then
  echo "PARSE_ERROR 0"
  exit 2
fi

SCORE=$(printf '%s' "$YAML_BLOCK" | grep -E '^score:' | head -1 \
  | sed -E 's/^score:[[:space:]]*//;s/[^0-9.].*$//')
VERDICT=$(printf '%s' "$YAML_BLOCK" | grep -E '^verdict:' | head -1 \
  | sed -E 's/^verdict:[[:space:]]*//;s/[[:space:]].*$//' | tr '[:lower:]' '[:upper:]')

if [[ -z "$SCORE" ]] || ! [[ "$SCORE" =~ ^[0-9.]+$ ]]; then
  SCORE=0
fi
case "$VERDICT" in
  PASS|REVISE|RESTART)
    echo "$VERDICT $SCORE"
    exit 0
    ;;
  *)
    echo "PARSE_ERROR 0"
    exit 2
    ;;
esac
