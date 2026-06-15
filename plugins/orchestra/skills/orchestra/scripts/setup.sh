#!/usr/bin/env bash
# setup.sh — OPTIONAL automation setup for orchestra.
#
# Orchestra works fully in MANUAL mode (you paste prompts into ChatGPT Pro yourself).
# This script only installs the optional semi-automation helper (Playwright + Chromium)
# for users who want the ChatGPT paste steps partially automated.
#
# If you do NOT run this — or if it fails — orchestra still runs in MANUAL mode
# automatically. Nothing breaks.
#
# Usage: bash setup.sh
#
# IMPORTANT: Browser automation of ChatGPT is a convenience for a Pro subscription used
# manually. It is NOT the official OpenAI API. It can break on UI changes and may be
# subject to OpenAI's terms — review them. The hardened verification mechanisms (①–⑧) do
# NOT depend on this; they work identically in MANUAL mode.
#
# Idempotent — safe to re-run. Degrades gracefully: any failure leaves you in MANUAL mode.

set -uo pipefail

echo "========================================"
echo " orchestra setup — optional ChatGPT automation"
echo "========================================"

# 1. Python check (3.8+)
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
      PY="$candidate"
      break
    fi
  fi
done

if [[ -z "$PY" ]]; then
  echo "ERROR: Python 3.8+ not found on PATH." >&2
  echo "" >&2
  echo "Install Python 3:" >&2
  case "$(uname -s 2>/dev/null || echo Windows)" in
    Darwin) echo "  macOS: brew install python3" >&2 ;;
    Linux)  echo "  Linux: sudo apt install python3 python3-pip  # or your package manager" >&2 ;;
    *)      echo "  Windows: https://www.python.org/downloads/ (3.10+ recommended)" >&2 ;;
  esac
  echo "" >&2
  echo "Orchestra still runs in MANUAL mode without automation." >&2
  exit 0
fi

echo "[1/4] Python found: $($PY --version)"

# 2. pip check
if ! "$PY" -m pip --version >/dev/null 2>&1; then
  echo "WARN: pip not available with $PY — skipping automation install." >&2
  echo "      Enable pip with: $PY -m ensurepip --upgrade" >&2
  echo "      Orchestra will run in MANUAL mode." >&2
  exit 0
fi

echo "[2/4] pip OK"

# 3. Install playwright + PyYAML (PyYAML is optional but makes the score gate
#    more robust against unusual review YAML shapes)
echo "[3/4] Installing playwright + PyYAML (pip --user)..."
if ! "$PY" -m pip install --user --upgrade playwright PyYAML; then
  echo "WARN: pip install failed. Orchestra will still run in MANUAL mode." >&2
  exit 0
fi

# 4. Install Chromium
echo "[4/4] Installing Chromium for Playwright (~200MB, this may take a minute)..."
if ! "$PY" -m playwright install chromium; then
  echo "WARN: Chromium install failed. Orchestra will still run in MANUAL mode." >&2
  exit 0
fi

# Prepare persistent profile directory
mkdir -p "$HOME/.orchestra/chrome-profile"

# Verify
if "$PY" -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
  echo ""
  echo "========================================"
  echo " ✓ Setup complete!"
  echo "========================================"
  echo ""
  echo "ChatGPT 자동화가 활성화되었습니다."
  echo "처음 /orchestra 실행 시 브라우저 창이 뜨면 ChatGPT에 로그인하세요 (1회만)."
  echo "이후 ~/.orchestra/chrome-profile/ 에 세션이 보존됩니다."
  echo "자동화를 쓰지 않으려면 그냥 의존하지 마세요 — MANUAL 모드(직접 붙여넣기)가 항상 기본 폴백입니다."
else
  echo "WARN: playwright import failed even after install. Falling back to MANUAL mode." >&2
  exit 0
fi
