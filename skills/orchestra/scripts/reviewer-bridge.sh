#!/usr/bin/env bash
# reviewer-bridge.sh — automate ChatGPT web UI for review/plan requests
#
# Usage: reviewer-bridge.sh --model <mode> <prompt-file> <output-file>
#   <mode>: deep-research | pro-reasoning | thinking | standard
#
# Behavior:
#   - Reads prompt from <prompt-file>
#   - Drives ChatGPT browser (via gstack browse) for the given mode
#   - Polls for completion per mode policy
#   - Writes raw assistant response to <output-file>
#   - Prepends a YAML metadata header (mode, start, end, char_count)
#
# Exit codes:
#   0  — success
#   2  — auth required (sign-in detected)
#   3  — timeout (no completion within max poll window)
#   4  — extraction failed
#   5  — bad arguments

set -euo pipefail

usage() {
  echo "Usage: $0 --model <deep-research|pro-reasoning|thinking|standard> <prompt-file> <output-file>" >&2
  exit 5
}

MODE=""
PROMPT_FILE=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      if [[ -z "$PROMPT_FILE" ]]; then
        PROMPT_FILE="$1"
      elif [[ -z "$OUTPUT_FILE" ]]; then
        OUTPUT_FILE="$1"
      else
        usage
      fi
      shift
      ;;
  esac
done

[[ -z "$MODE" || -z "$PROMPT_FILE" || -z "$OUTPUT_FILE" ]] && usage
[[ -f "$PROMPT_FILE" ]] || { echo "prompt-file not found: $PROMPT_FILE" >&2; exit 5; }

# Mode → URL / polling policy
case "$MODE" in
  deep-research)
    URL="https://chatgpt.com/?model=deep-research"
    POLL_INTERVAL=300        # 5 minutes
    POLL_MAX=1800            # 30 minutes
    LABEL="Pro Deep Research"
    ;;
  pro-reasoning)
    URL="https://chatgpt.com/?model=gpt-5-pro"
    POLL_INTERVAL=30
    POLL_MAX=300
    LABEL="Pro Reasoning (Extended)"
    ;;
  thinking)
    URL="https://chatgpt.com/?model=gpt-5-thinking"
    POLL_INTERVAL=15
    POLL_MAX=120
    LABEL="Thinking"
    ;;
  standard)
    URL="https://chatgpt.com/?model=gpt-5"
    POLL_INTERVAL=5
    POLL_MAX=30
    LABEL="Standard"
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    usage
    ;;
esac

START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Best-effort browser automation. Implementation depends on local gstack/browse
# capabilities. We delegate to a Python helper that uses the gstack browse skill
# under the hood. If the helper is missing, fall back to MANUAL mode.

HELPER="${HOME}/.claude/skills/orchestra/scripts/.reviewer-bridge-helper.py"

if command -v gstack >/dev/null 2>&1 && [[ -x "$HELPER" ]]; then
  # Automated path
  "$HELPER" \
    --url "$URL" \
    --mode "$MODE" \
    --poll-interval "$POLL_INTERVAL" \
    --poll-max "$POLL_MAX" \
    --prompt-file "$PROMPT_FILE" \
    --output-file "${OUTPUT_FILE}.raw" \
    || EXIT_CODE=$?

  EXIT_CODE="${EXIT_CODE:-0}"
  if [[ "$EXIT_CODE" -ne 0 ]]; then
    exit "$EXIT_CODE"
  fi
else
  # Manual fallback — show instructions to the user
  echo "================================================================" >&2
  echo "MANUAL MODE: gstack browser automation not available." >&2
  echo "" >&2
  echo "1. Open: $URL" >&2
  echo "2. Select model mode: $LABEL" >&2
  echo "3. Paste content from: $PROMPT_FILE" >&2
  echo "4. Wait for response (estimated: $((POLL_MAX/60)) min max)" >&2
  echo "5. Copy assistant response to: ${OUTPUT_FILE}.raw" >&2
  echo "" >&2
  echo "Press Enter when ${OUTPUT_FILE}.raw is ready..." >&2
  read -r _ </dev/tty || true
fi

if [[ ! -f "${OUTPUT_FILE}.raw" ]]; then
  echo "Expected raw output not found: ${OUTPUT_FILE}.raw" >&2
  exit 4
fi

END_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
CHAR_COUNT=$(wc -c < "${OUTPUT_FILE}.raw" | tr -d ' ')

# Prepend metadata header
{
  echo "---"
  echo "generated_by: chatgpt"
  echo "model: $MODE"
  echo "started_at: $START_TS"
  echo "completed_at: $END_TS"
  echo "char_count: $CHAR_COUNT"
  echo "---"
  echo ""
  cat "${OUTPUT_FILE}.raw"
} > "$OUTPUT_FILE"

rm -f "${OUTPUT_FILE}.raw"
exit 0
