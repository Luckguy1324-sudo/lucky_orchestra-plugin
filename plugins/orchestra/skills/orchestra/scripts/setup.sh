#!/usr/bin/env bash
# setup.sh — OPTIONAL automation setup for orchestra v0.7.0.
#
# Orchestra works fully in MANUAL mode (you paste prompts into ChatGPT Pro yourself).
# This installs the optional Playwright + Chromium helper for semi-automated paste.
# If you do NOT run this, orchestra runs in MANUAL mode automatically. Nothing breaks.
#
# Usage: bash setup.sh
#
# Browser automation of ChatGPT is a convenience for a Pro subscription used manually.
# It is NOT the official OpenAI API; it can break on UI changes and may be subject to
# OpenAI's terms — review them. The hardened mechanisms (①–⑧, S1–S4, C1–C3) do NOT depend
# on this; they work identically in MANUAL mode.

set -uo pipefail

echo "=== Orchestra v0.7.0 optional automation setup ==="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3.8+ first." >&2
  exit 1
fi

echo "[1/3] Installing Playwright (Python, --user) ..."
python3 -m pip install --user playwright pyyaml || {
  echo "WARN: pip install failed. Orchestra will still run in MANUAL mode." >&2
  exit 0
}

echo "[2/3] Installing isolated Chromium for Playwright ..."
python3 -m playwright install chromium || {
  echo "WARN: Chromium install failed. Orchestra will still run in MANUAL mode." >&2
  exit 0
}

echo "[3/3] Preparing profile directory ..."
mkdir -p "$HOME/.orchestra/chrome-profile"

echo
echo "=== Setup complete ==="
echo "On first Stage-2/6 run, orchestra opens a headed browser window."
echo "Log into ChatGPT once; the session is saved to ~/.orchestra/chrome-profile/ and reused."
echo "To skip automation entirely, just don't rely on it — MANUAL mode is always the default."
