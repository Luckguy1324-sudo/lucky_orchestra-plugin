#!/usr/bin/env bash
# score-check.sh — parse review file, print verdict + score
#
# Usage: score-check.sh <review-file>
#
# Output (stdout, one line):
#   PASS|REVISE|RESTART|PARSE_ERROR <score>
#
# Exit codes:
#   0  — parsed successfully (verdict and score determined)
#   1  — file missing
#   2  — parse error (no YAML block found, or required fields missing)

set -euo pipefail

REVIEW_FILE="${1:-}"
[[ -z "$REVIEW_FILE" ]] && { echo "Usage: $0 <review-file>" >&2; exit 1; }
[[ -f "$REVIEW_FILE" ]] || { echo "Review file not found: $REVIEW_FILE" >&2; exit 1; }

# Extract first ```yaml ... ``` block
YAML_BLOCK=$(awk '
  /^```yaml/ { in_block=1; next }
  /^```/ && in_block { exit }
  in_block { print }
' "$REVIEW_FILE")

if [[ -z "$YAML_BLOCK" ]]; then
  echo "PARSE_ERROR 0"
  exit 2
fi

# Use python yaml if available, else simple grep
HAS_YAML=0
if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import yaml' 2>/dev/null; then
    HAS_YAML=1
  fi
fi

if [[ "$HAS_YAML" -eq 1 ]]; then
  RESULT=$(printf '%s' "$YAML_BLOCK" | python3 -c '
import sys, yaml
try:
    data = yaml.safe_load(sys.stdin.read())
    score = int(data.get("score", 0))
    verdict = str(data.get("verdict", "")).strip().upper()
    if verdict not in ("PASS", "REVISE", "RESTART"):
        print("PARSE_ERROR 0")
    else:
        print(f"{verdict} {score}")
except Exception:
    print("PARSE_ERROR 0")
')
else
  SCORE=$(printf '%s' "$YAML_BLOCK" | grep -E '^score:' | head -1 | sed -E 's/^score:[[:space:]]*//;s/[^0-9].*$//')
  VERDICT=$(printf '%s' "$YAML_BLOCK" | grep -E '^verdict:' | head -1 | sed -E 's/^verdict:[[:space:]]*//;s/[[:space:]].*$//')
  VERDICT=$(printf '%s' "$VERDICT" | tr '[:lower:]' '[:upper:]')

  if [[ -z "$SCORE" ]] || ! [[ "$SCORE" =~ ^[0-9]+$ ]]; then
    SCORE=0
  fi
  case "$VERDICT" in
    PASS|REVISE|RESTART)
      RESULT="$VERDICT $SCORE"
      ;;
    *)
      RESULT="PARSE_ERROR 0"
      ;;
  esac
fi

echo "$RESULT"
if [[ "$RESULT" =~ ^PARSE_ERROR ]]; then
  exit 2
fi
exit 0
