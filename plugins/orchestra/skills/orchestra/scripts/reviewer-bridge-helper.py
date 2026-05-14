#!/usr/bin/env python3
"""
reviewer-bridge-helper.py — Drive ChatGPT web UI via Playwright

Used by reviewer-bridge.sh to automate ChatGPT (Stage 2 plan, Stage 5 review).

Usage:
  reviewer-bridge-helper.py \\
    --url <url> \\
    --mode <deep-research|pro-reasoning|thinking|standard> \\
    --poll-interval <sec> \\
    --poll-max <sec> \\
    --prompt-file <path> \\
    --output-file <path>

Behavior:
  - Reuses a persistent Chromium profile at ~/.orchestra/chrome-profile/
    so the user logs in to ChatGPT only ONCE per machine.
  - Headed mode (visible browser) — user can intervene on CAPTCHA / 2FA.
  - Polls based on mode-specific policy.
  - Writes assistant response text to <output-file>.

Exit codes:
  0  success
  2  auth required (sign-in detected, user closed without logging in)
  3  timeout
  4  extraction failed
  5  missing dependencies (playwright not installed)
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(
        "ERROR: playwright not installed.\n"
        "Run the setup script: ~/.claude/plugins/cache/lucky-orchestra/orchestra/<version>/skills/orchestra/scripts/setup.sh\n"
        "Or manually: pip install playwright && playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(5)

PROFILE_DIR = Path.home() / ".orchestra" / "chrome-profile"

# Selectors (kept in code for now — chatgpt-selectors.md is the doc)
PROMPT_SELECTORS = [
    "textarea#prompt-textarea",
    'div[contenteditable="true"][data-id="root"]',
    'div[contenteditable="true"]',
    "textarea",
]
SEND_BUTTON_SELECTORS = [
    'button[data-testid="send-button"]',
    'button[aria-label*="Send"]',
    'button[type="submit"]',
]
STOP_BUTTON_SELECTORS = [
    'button[data-testid="stop-button"]',
    'button[aria-label*="Stop"]',
    'button[aria-label*="streaming"]',
]
ASSISTANT_MSG_SELECTOR = '[data-message-author-role="assistant"]'
SIGNIN_INDICATORS = [
    "text=/Log in/",
    "text=/Sign in/",
    "text=/로그인/",
]


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def find_first(page, selectors, timeout=5000):
    """Return the first matching locator, or None."""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            return loc
        except PlaywrightTimeout:
            continue
    return None


def is_signed_in(page) -> bool:
    """Return True if no sign-in indicators are visible."""
    for sel in SIGNIN_INDICATORS:
        try:
            if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible():
                return False
        except Exception:
            continue
    return True


def is_generating(page) -> bool:
    """Return True if a stop-streaming button is visible (model still producing)."""
    for sel in STOP_BUTTON_SELECTORS:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                return True
        except Exception:
            continue
    return False


def submit_prompt(page, prompt_text: str) -> bool:
    """Type the prompt and submit. Returns True on success."""
    textarea = find_first(page, PROMPT_SELECTORS, timeout=15000)
    if textarea is None:
        log("ERROR: prompt textarea not found")
        return False

    textarea.click()
    page.wait_for_timeout(300)

    # Use clipboard for large prompts (faster + avoids per-char issues)
    try:
        page.evaluate(
            "text => navigator.clipboard.writeText(text)",
            prompt_text,
        )
        modifier = "Control" if sys.platform.startswith(("linux", "win")) else "Meta"
        page.keyboard.press(f"{modifier}+V")
    except Exception:
        # Fallback: type directly
        textarea.type(prompt_text, delay=0)

    page.wait_for_timeout(800)

    send = None
    for sel in SEND_BUTTON_SELECTORS:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_enabled():
                send = btn
                break
        except Exception:
            continue

    if send is not None:
        send.click()
    else:
        page.keyboard.press("Enter")

    return True


def extract_response(page) -> str:
    """Return the latest assistant message text."""
    try:
        msgs = page.locator(ASSISTANT_MSG_SELECTOR)
        if msgs.count() == 0:
            return ""
        return msgs.last.inner_text().strip()
    except Exception as e:
        log(f"extract error: {e}")
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--poll-interval", type=int, required=True)
    parser.add_argument("--poll-max", type=int, required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headless (default: headed for auth visibility)",
    )
    args = parser.parse_args()

    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        log(f"prompt file not found: {prompt_path}")
        return 5

    prompt = prompt_path.read_text(encoding="utf-8")
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    log(f"[orchestra] Mode: {args.mode} | Profile: {PROFILE_DIR}")
    log(f"[orchestra] URL: {args.url}")
    log(f"[orchestra] Poll: every {args.poll_interval}s, max {args.poll_max}s")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=args.headless,
            viewport={"width": 1280, "height": 900},
            args=["--no-first-run", "--disable-blink-features=AutomationControlled"],
        )

        page = context.new_page()

        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
        except PlaywrightTimeout:
            log("Initial navigation timed out — continuing anyway")

        if not is_signed_in(page):
            log("\n" + "=" * 60)
            log("AUTH REQUIRED: ChatGPT 로그인 페이지가 감지됐어요.")
            log("브라우저 창에서 로그인을 완료한 뒤 이 터미널로 돌아와서")
            log("Enter 키를 누르세요. (브라우저 창은 닫지 마세요)")
            log("=" * 60 + "\n")
            try:
                input()
            except EOFError:
                pass

            if not is_signed_in(page):
                log("로그인 미완료로 판단됨. 종료.")
                context.close()
                return 2

        log("[orchestra] 인증 OK. 프롬프트 입력 중...")

        if not submit_prompt(page, prompt):
            context.close()
            return 4

        log("[orchestra] 프롬프트 제출 완료. 응답 대기 중...")

        start = time.time()
        last_text = ""
        stable_polls = 0
        STABLE_THRESHOLD = 2  # 2회 연속 동일하면 완료로 간주

        while True:
            elapsed = int(time.time() - start)
            if elapsed >= args.poll_max:
                log(f"\nTIMEOUT after {elapsed}s")
                if last_text:
                    log("부분 응답을 저장합니다.")
                    output_path.write_text(last_text, encoding="utf-8")
                    context.close()
                    return 0
                context.close()
                return 3

            time.sleep(args.poll_interval)

            generating = is_generating(page)
            current = extract_response(page)

            mins = elapsed // 60
            secs = elapsed % 60
            log(
                f"[{mins:02d}:{secs:02d}] generating={generating} "
                f"chars={len(current)} stable={stable_polls}"
            )

            if generating:
                stable_polls = 0
                last_text = current
                continue

            if current and current == last_text:
                stable_polls += 1
                if stable_polls >= STABLE_THRESHOLD:
                    log(f"[orchestra] 응답 안정화 ({elapsed}s 소요, {len(current)} chars)")
                    output_path.write_text(current, encoding="utf-8")
                    context.close()
                    return 0
            else:
                stable_polls = 0
                last_text = current


if __name__ == "__main__":
    sys.exit(main())
