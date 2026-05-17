#!/usr/bin/env bash
# setup.sh — install Python + Playwright dependencies for ChatGPT automation
#
# Usage: setup.sh
#
# Behavior:
#   - Detects python3, installs Playwright via pip (user scope)
#   - Downloads Chromium for Playwright (~200MB)
#   - Verifies installation
#
# Idempotent — safe to re-run.

set -euo pipefail

echo "========================================"
echo " orchestra setup — ChatGPT automation"
echo "========================================"

# 1. Python check
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
  exit 1
fi

echo "[1/4] Python found: $($PY --version)"

# 2. pip check
if ! "$PY" -m pip --version >/dev/null 2>&1; then
  echo "ERROR: pip not available with $PY." >&2
  echo "Install pip: $PY -m ensurepip --upgrade" >&2
  exit 1
fi

echo "[2/4] pip OK"

# 3. Install playwright + PyYAML (PyYAML is optional but makes score_check.py
#    more robust against unusual review YAML shapes)
echo "[3/4] Installing playwright + PyYAML (pip --user)..."
"$PY" -m pip install --user --upgrade playwright PyYAML

# 4. Install Chromium
echo "[4/4] Installing Chromium for Playwright (~200MB, this may take a minute)..."
"$PY" -m playwright install chromium

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
else
  echo "ERROR: playwright import failed even after install." >&2
  exit 1
fi
