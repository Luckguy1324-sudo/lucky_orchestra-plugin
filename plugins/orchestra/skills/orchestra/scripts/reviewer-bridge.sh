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

# Mode → URL / phase-budget policy
#
# Policy design:
#   POLL_INTERVAL  — how often the helper checks page state
#   START_TIMEOUT  — max wait between submit and first "generating" signal
#                    (catches submit failures, NOT ChatGPT thinking time)
#   EXTRACT_TIMEOUT — max wait after generating stops for text to stabilize
#                     (catches fetch/render failures, NOT thinking time)
#
# The "GENERATING" phase between these has NO time limit. Deep Research can
# legitimately run for hours and we'll keep waiting as long as ChatGPT's
# "Stop streaming" button is visible.
case "$MODE" in
  deep-research)
    URL="https://chatgpt.com/?model=deep-research"
    POLL_INTERVAL=30         # check every 30s
    START_TIMEOUT=180        # 3 min to start (DR sometimes takes a while to begin)
    EXTRACT_TIMEOUT=600      # 10 min to extract final text after generation stops
    LABEL="Pro Deep Research"
    ;;
  pro-reasoning)
    URL="https://chatgpt.com/?model=gpt-5-pro"
    POLL_INTERVAL=15
    START_TIMEOUT=60
    EXTRACT_TIMEOUT=120
    LABEL="Pro Reasoning (Extended)"
    ;;
  thinking)
    URL="https://chatgpt.com/?model=gpt-5-thinking"
    POLL_INTERVAL=10
    START_TIMEOUT=30
    EXTRACT_TIMEOUT=60
    LABEL="Thinking"
    ;;
  standard)
    URL="https://chatgpt.com/?model=gpt-5"
    POLL_INTERVAL=5
    START_TIMEOUT=15
    EXTRACT_TIMEOUT=30
    LABEL="Standard"
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    usage
    ;;
esac

START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Locate the Playwright helper. It lives next to this script.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
HELPER="${SCRIPT_DIR}/reviewer-bridge-helper.py"

# Determine python executable
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done

# Check if Playwright is available
PLAYWRIGHT_OK=0
if [[ -n "$PY" ]] && "$PY" -c "import playwright" >/dev/null 2>&1; then
  PLAYWRIGHT_OK=1
fi

if [[ -f "$HELPER" ]] && [[ "$PLAYWRIGHT_OK" -eq 1 ]]; then
  # Automated path via Playwright
  set +e
  "$PY" "$HELPER" \
    --url "$URL" \
    --mode "$MODE" \
    --poll-interval "$POLL_INTERVAL" \
    --start-timeout "$START_TIMEOUT" \
    --extract-timeout "$EXTRACT_TIMEOUT" \
    --prompt-file "$PROMPT_FILE" \
    --output-file "${OUTPUT_FILE}.raw"
  EXIT_CODE=$?
  set -e

  if [[ "$EXIT_CODE" -ne 0 ]]; then
    echo "reviewer-bridge-helper exited with code $EXIT_CODE" >&2
    exit "$EXIT_CODE"
  fi
else
  # MANUAL fallback
  echo "================================================================" >&2
  echo "MANUAL MODE — browser automation unavailable." >&2
  if [[ ! -f "$HELPER" ]]; then
    echo "Reason: helper script not found at $HELPER" >&2
  elif [[ -z "$PY" ]]; then
    echo "Reason: python3 not on PATH" >&2
  else
    echo "Reason: playwright not installed. Run setup.sh in the same directory." >&2
  fi
  echo "" >&2
  echo "수동 진행 절차:" >&2
  echo "  1. 브라우저에서 열기: $URL" >&2
  echo "  2. 모델 모드 선택: $LABEL" >&2
  echo "  3. 다음 파일 내용을 ChatGPT에 paste: $PROMPT_FILE" >&2
  echo "  4. ChatGPT 응답 완료까지 대기 (Deep Research는 시간 제한 없음)" >&2
  echo "  5. 응답 텍스트를 다음 파일에 저장: ${OUTPUT_FILE}.raw" >&2
  echo "" >&2
  echo "준비되면 Enter를 누르세요..." >&2
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
