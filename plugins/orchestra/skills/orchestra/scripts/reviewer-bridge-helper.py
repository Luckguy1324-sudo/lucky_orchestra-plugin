#!/usr/bin/env python3
"""
reviewer-bridge-helper.py — Drive ChatGPT web UI via Playwright

Used by reviewer-bridge.sh to automate ChatGPT (Stage 2 plan, Stage 5 review).

Polling design (v0.2.1+):
  Phase 1  WAITING_FOR_START — after submit, before any generating signal
           Timeout: --start-timeout (default 120s). Catches submit failures.
  Phase 2  GENERATING — model is actively producing
           No time limit. Detected by "Stop streaming" button visibility.
           For Deep Research this can legitimately run hours.
  Phase 3  EXTRACTING — generating stopped, text stabilizing
           Timeout: --extract-timeout (default 300s). Catches fetch failures.
  Phase 4  DONE — text stable for N consecutive polls → success

Error detection (any phase):
  - Sign-in page → exit 2 (auth required)
  - Error banner / rate limit text → exit 4
  - Page crashed/closed → exit 4

Usage:
  reviewer-bridge-helper.py \\
    --url <url> \\
    --mode <deep-research|pro-reasoning|thinking|standard> \\
    --poll-interval <sec> \\
    --start-timeout <sec> \\
    --extract-timeout <sec> \\
    --prompt-file <path> \\
    --output-file <path>

Exit codes:
  0  success
  2  auth required
  3  timeout (phase-specific)
  4  extraction/error
  5  missing dependencies (playwright not installed)
"""
import argparse
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(
        "ERROR: playwright not installed.\n"
        "Run setup.sh in the same directory, or manually:\n"
        "  pip install playwright && playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(5)

PROFILE_DIR = Path.home() / ".orchestra" / "chrome-profile"

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
ERROR_INDICATORS = [
    "text=/Something went wrong/i",
    "text=/Network error/i",
    "text=/Rate limit/i",
    "text=/Too many requests/i",
    "text=/Please try again later/i",
    "text=/오류가 발생/i",
]

# Phase 2 → Phase 3 hysteresis: require N consecutive polls without generating
# signal before switching to EXTRACTING. Prevents flicker during streaming pauses.
GENERATING_GONE_HYSTERESIS = 2

# Phase 3 → Phase 4: text stable for N polls = done
STABLE_THRESHOLD = 2


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def find_first(page, selectors, timeout=5000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            return loc
        except PlaywrightTimeout:
            continue
    return None


def is_signed_in(page) -> bool:
    for sel in SIGNIN_INDICATORS:
        try:
            if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible():
                return False
        except Exception:
            continue
    return True


def detect_error(page):
    """Return error message string if ChatGPT shows an error, else None."""
    for sel in ERROR_INDICATORS:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                try:
                    if loc.first.is_visible():
                        return loc.first.inner_text()[:200]
                except Exception:
                    return sel
        except Exception:
            continue
    return None


def is_generating(page) -> bool:
    for sel in STOP_BUTTON_SELECTORS:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                return True
        except Exception:
            continue
    return False


def submit_prompt(page, prompt_text: str) -> bool:
    textarea = find_first(page, PROMPT_SELECTORS, timeout=15000)
    if textarea is None:
        log("ERROR: prompt textarea not found")
        return False

    textarea.click()
    page.wait_for_timeout(300)

    try:
        page.evaluate(
            "text => navigator.clipboard.writeText(text)",
            prompt_text,
        )
        modifier = "Control" if sys.platform.startswith(("linux", "win")) else "Meta"
        page.keyboard.press(f"{modifier}+V")
    except Exception:
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
    try:
        msgs = page.locator(ASSISTANT_MSG_SELECTOR)
        if msgs.count() == 0:
            return ""
        return msgs.last.inner_text().strip()
    except Exception:
        return ""


def fmt_elapsed(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--poll-interval", type=int, required=True,
                        help="Seconds between status polls")
    parser.add_argument("--start-timeout", type=int, default=120,
                        help="Max seconds to wait for generating signal after submit")
    parser.add_argument("--extract-timeout", type=int, default=300,
                        help="Max seconds to wait for text to stabilize after generating stops")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headless (default: headed)",
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
    log(f"[orchestra] Phase budgets — start: {args.start_timeout}s, "
        f"extract: {args.extract_timeout}s | poll every {args.poll_interval}s")
    log(f"[orchestra] GENERATING phase has NO time limit "
        f"(ChatGPT can take hours for deep research)")

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

        log("[orchestra] 프롬프트 제출 완료. 상태 머신 시작.")

        # ===== State machine =====
        phase = "WAITING_FOR_START"
        phase_started = time.time()
        run_started = time.time()
        last_text = ""
        stable_polls = 0
        gone_polls = 0  # consecutive polls without generating signal (for Phase 2 → 3)
        ever_generated = False

        while True:
            time.sleep(args.poll_interval)
            now = time.time()
            elapsed_phase = now - phase_started
            elapsed_total = now - run_started

            # Universal: page closed?
            if page.is_closed():
                log("\nERROR: 브라우저 페이지가 닫혔습니다.")
                context.close()
                return 4

            # Universal: error banner?
            err = detect_error(page)
            if err:
                log(f"\nERROR detected: {err}")
                context.close()
                return 4

            # Universal: signed out mid-run?
            if not is_signed_in(page):
                log("\nERROR: 실행 중 로그아웃됨 (세션 만료)")
                context.close()
                return 2

            generating = is_generating(page)
            current = extract_response(page)

            log(f"[{fmt_elapsed(elapsed_total)}] phase={phase} "
                f"phase_t={int(elapsed_phase)}s generating={generating} "
                f"chars={len(current)} stable={stable_polls} gone={gone_polls}")

            # ===== Phase 1: WAITING_FOR_START =====
            if phase == "WAITING_FOR_START":
                if generating:
                    log("[orchestra] → Phase 2: GENERATING (생성 시작 감지)")
                    phase = "GENERATING"
                    phase_started = now
                    ever_generated = True
                    continue

                # Some models (standard, thinking) may produce response without
                # ever showing stop button if response is very short. Check if
                # text appeared.
                if current and current != last_text:
                    log("[orchestra] → Phase 3: EXTRACTING (텍스트 직접 출현)")
                    phase = "EXTRACTING"
                    phase_started = now
                    last_text = current
                    stable_polls = 0
                    continue

                if elapsed_phase >= args.start_timeout:
                    log(f"\nTIMEOUT in WAITING_FOR_START phase after {int(elapsed_phase)}s.")
                    log("프롬프트 제출 후 응답 생성 신호가 감지되지 않았습니다.")
                    context.close()
                    return 3
                continue

            # ===== Phase 2: GENERATING (no time limit) =====
            if phase == "GENERATING":
                if generating:
                    gone_polls = 0
                    last_text = current  # track latest while generating
                    # NO TIMEOUT CHECK — keep waiting indefinitely
                    continue

                # Generating signal gone — confirm with hysteresis
                gone_polls += 1
                if gone_polls >= GENERATING_GONE_HYSTERESIS:
                    log("[orchestra] → Phase 3: EXTRACTING (생성 완료 감지)")
                    phase = "EXTRACTING"
                    phase_started = now
                    last_text = current
                    stable_polls = 0
                continue

            # ===== Phase 3: EXTRACTING =====
            if phase == "EXTRACTING":
                # Generating shouldn't come back, but if it does, return to Phase 2
                if generating:
                    log("[orchestra] ← Phase 2: GENERATING (재개됨)")
                    phase = "GENERATING"
                    phase_started = now
                    gone_polls = 0
                    continue

                if current and current == last_text:
                    stable_polls += 1
                    if stable_polls >= STABLE_THRESHOLD:
                        log(f"[orchestra] → Phase 4: DONE "
                            f"(총 {fmt_elapsed(elapsed_total)}, {len(current)} chars)")
                        output_path.write_text(current, encoding="utf-8")
                        context.close()
                        return 0
                else:
                    stable_polls = 0
                    last_text = current

                if elapsed_phase >= args.extract_timeout:
                    log(f"\nTIMEOUT in EXTRACTING phase after {int(elapsed_phase)}s.")
                    if last_text:
                        log("부분 응답을 저장합니다.")
                        output_path.write_text(last_text, encoding="utf-8")
                        context.close()
                        return 0
                    context.close()
                    return 3
                continue


if __name__ == "__main__":
    sys.exit(main())
