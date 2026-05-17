# Changelog

## [0.4.0] - 2026-05-17

협업 품질 직접 향상 4가지 — performer 표준화, 프롬프트 구조화, must_fix 자동 라우팅, provenance 자동 부착.

### Added

- **`agents/research-worker.md`** — Named subagent for Stage 3 Performer:
  - Read-only tool권한 (`Read, WebFetch, Glob, Grep`) — 자기 토픽 밖 부작용 방지
  - 토픽 격리 강제, 인용 `[r<N>]` 양식 강제, fact/interpretation/assumption 구분 요구
  - Round ≥ 2 시 `previous_must_fix` 직접 처리 + "must_fix addressed" 섹션 자동 작성
- **`scripts/build-provenance.py`** — 자동 출처 섹션 생성기:
  - run_id, started_at, 사용 모델, 라운드별 verdict/score, 참조자료, 파일 목록을 종합한 markdown 출력
  - Stage 6 (finalize) 시 `final.md` 뒤에 자동 append
  - PyYAML 없어도 동작 (minimal parser fallback)
- **must_fix → Performer 자동 라우팅** (Stage 3 Round N≥2):
  - Reviewer가 `scope_topic_id`로 표시한 항목은 해당 토픽 Performer 프롬프트에만 주입
  - `scope_topic_id: null` 항목은 모든 Performer에 공통 전달 (synthesis-level이면 Conductor가 Stage 4에서 처리)

### Changed

- **`references/plan-prompt.md`** — 재설계: XML-tagged 섹션 + 단일 JSON 코드블록 출력 강제
  - `<role>`, `<objective>`, `<success_criterion>`, `<constraints>`, `<references>`, `<rules>`, `<output_format>` 구조
  - "shape-priming" 효과: schema와 example 같이 제공해 형식 위반 감소
  - "Now produce the JSON." trigger phrase로 자유 산문 시작 방지
- **`references/reviewer-prompt.md`** — 재설계: 동일 XML 구조
  - `must_fix` 항목에 `scope_topic_id` 필드 추가
  - `<consistency_rules>` 섹션으로 PASS-but-low-score / PASS-with-must_fix 자기모순 차단을 모델에게 명시
  - `<previous_review>` 섹션 (Round ≥ 2)으로 직전 must_fix 해결 여부 점검 강제
- **`SKILL.md` Stage 3**: research-worker subagent 사용 + must_fix 자동 주입 흐름 명시
- **`SKILL.md` Stage 4 (Synthesize)**: must_fix 처리 양분 (Performer가 본 항목 vs synthesis-level) + 라운드별 변경사항 섹션 추가 요구
- **`SKILL.md` Stage 6 (Decide)**: finalize 단계에서 `build-provenance.py` 자동 호출 + PASS_WITH_WARNINGS 경고 헤더 처리
- **`brief-interview.md`**: frontmatter에 `pass_threshold: 8.0` 명시 (기본값)
- **출력 형식 권장**: YAML → **JSON** (둘 다 수용하지만 JSON 우선)

### Compatibility

- 기존 v0.3.x run 디렉토리와 호환 — meta.json/01-brief.md 형식 변경 없음 (pass_threshold만 신규 필드)
- 마이그레이션: `/plugin update orchestra` + 새 Claude Code 세션. 추가 작업 없음.

## [0.3.0] - 2026-05-17

이 릴리스는 외부 코드 리뷰(`deep-research-report_for_lucky_orchestra-plugin.md`)에서 지적된 critical 항목들을 코드로 반영. 동작 호환성은 유지하면서 결정론·검증·경로 안전성 강화.

### Fixed
- **`/orchestra` allowed-tools에 `WebFetch` 누락** — SKILL.md/brief-interview.md는 URL 참조 처리에 WebFetch를 사용한다고 명시했지만 권한 목록에 없었음. URL 자료 첨부가 자동화 경로에서 실패하던 버그 수정.
- **EXTRACTING phase 부분 응답 → exit 0 처리 버그** — 타임아웃 시 부분 텍스트가 있으면 성공으로 처리해 불완전 리뷰가 정상 산출물로 흘러갔음. 이제 exit 6 + frontmatter에 `partial: true` 기록 + `.meta.json` 사이드카 생성.
- **README 경로의 `0.2.0` 하드코딩** — 버전 글로브(`/orchestra/*/scripts/setup.sh`)로 교체해 업데이트 후에도 동작.
- **SKILL.md의 `${HOME}/.claude/...` 하드코딩** — `${CLAUDE_PLUGIN_ROOT}` 사용으로 통일 (Anthropic 공식 권장).
- **`yq` 외부 의존성** — `frontmatter_get.py` (stdlib only) 로 교체.

### Added
- **`selectors.json`** (single source of truth) — ChatGPT UI 셀렉터 + 모드별 폴링 예산을 한 파일에 통합. `reviewer-bridge-helper.py`가 자동 로드, 누락 시 코드 내 fallback. UI 변경 시 이 JSON만 패치하면 됨.
- **`score_check.py`** — 강화된 review validator:
  - PASS but score < pass_threshold → REVISE 자동 escalate
  - PASS but must_fix 비어있지 않음 → REVISE 자동 escalate
  - REVISE + round >= max_rounds → PASS_WITH_WARNINGS
  - frontmatter/YAML의 `partial: true` → PARTIAL verdict
  - inline list `[]`, `["x"]` 등 일반 YAML 형식 지원
- **`plugin.json` 메타데이터 보강**:
  - `homepage`, `repository` 필드
  - `userConfig`: execution_mode, browser_profile_dir, headless, pass_threshold, optional API keys (sensitive)
- **`frontmatter_get.py`** — 외부 `yq` 의존성을 stdlib 만으로 교체
- **`.meta.json` 사이드카** — reviewer-bridge-helper가 응답마다 `{partial, exit_code, char_count, elapsed_seconds}` 메타데이터 별도 저장
- **`reviewer-bridge.sh` exit 6 인식** — partial 응답 처리, output frontmatter에 `partial: true` 자동 기록
- **setup.sh가 PyYAML도 설치** — score_check.py의 robust 파싱 지원

### Changed
- `chatgpt-selectors.md` → selectors.json을 참조하는 안내 문서로 단순화 (single source of truth 확립)
- `score-check.sh` → Python validator(`score_check.py`) 위임. Python 부재 시 v0.2.x 동작으로 fallback

### Migration
v0.2.x → v0.3.0: `/plugin update orchestra` 후 새 Claude Code 세션부터 적용. 추가 작업 불필요. PyYAML이 더 robust한 파싱을 제공하므로 setup.sh 재실행 권장(선택).

### Known limitations / 미반영 항목 (v0.4+ 후속)
검토 보고서의 큰 그림(`thin skill + thick orchestrator`) 중 다음은 별도 마일스톤으로 분리:
- `bin/orchestra-run` 결정론적 런타임 (state.json + events.jsonl)
- `agents/` named subagents (research-worker, synthesizer)
- `hooks/` PreToolUse/SubagentStart 정책 가드
- `tests/` + CI (`claude plugin validate`, pytest fixture)
- API/SDK fallback 모드 (OpenAI Responses Deep Research + Structured Outputs)
- Browser profile을 `${CLAUDE_PLUGIN_DATA}/browser/chatgpt`로 이전 (현재는 `~/.orchestra/chrome-profile/` 유지 — 기존 로그인 세션 보존)
- `pip --user` → 플러그인 데이터 디렉토리 내부 venv

## [0.2.1] - 2026-05-15

### Changed
- **GENERATING phase에 시간 제한 제거** — ChatGPT가 응답 만드는 시간(특히 Deep Research)이 길어져도 자동화가 끊지 않음
- 폴링 모델을 3-페이즈 상태 머신으로 재설계:
  - Phase 1 (WAITING_FOR_START): submit ↔ generating 사이. 모드별 START_TIMEOUT
  - Phase 2 (GENERATING): "Stop streaming" 버튼 visible. **타임아웃 없음**
  - Phase 3 (EXTRACTING): 생성 멈춤 후 텍스트 안정화 대기. 모드별 EXTRACT_TIMEOUT
- 모드별 예산을 두 값으로 분리: `START_TIMEOUT` / `EXTRACT_TIMEOUT` (기존 `POLL_MAX` 단일 값 폐기)
- Deep Research 새 예산: START 3분 / EXTRACT 10분 / GENERATING 무제한 (기존: 30분 하드캡)
- 폴링 간격 짧아짐 (예: deep-research 5분 → 30초): 더 정확한 진행 상황 표시

### Added
- 오류 자동 감지 강화:
  - "Something went wrong" / "Network error" / "Rate limit" 배너 → 즉시 실패
  - 실행 중 sign-in 페이지 출현 → 즉시 인증 오류 (exit 2)
  - 브라우저 페이지 closed/crashed → 즉시 실패
- Phase 전환 hysteresis (GENERATING→EXTRACTING 2회 연속 확인 필요) — 스트리밍 일시 정지로 인한 오탐 방지
- 진행 로그에 elapsed 시간 (HH:MM:SS) 표시

### Migration
v0.2.0 → v0.2.1: 코드만 변경, 사용자 작업 없음. `/plugin update orchestra` 후 새 세션부터 적용.

## [0.2.0] - 2026-05-15

### Added
- **ChatGPT 브라우저 자동화** (Playwright 기반) — Stage 2/5에서 사람 개입 없이 ChatGPT에 프롬프트 전송 + 응답 수확
  - `scripts/reviewer-bridge-helper.py` — Playwright 헬퍼
  - `~/.orchestra/chrome-profile/` 영속 프로필 (로그인 1회만 필요)
  - 모드별 폴링 정책 (deep-research 30분, pro-reasoning 5분 등)
  - 응답 안정화 감지 (2회 연속 동일 내용이면 완료)
  - 응답 길이 + 경과 시간 진행 로깅
- **setup.sh** — Python + Playwright + Chromium 원샷 설치 스크립트

### Fixed
- `reviewer-bridge.sh`가 존재하지 않는 `gstack` 명령을 찾던 버그 → 헬퍼 경로 자동 탐지로 변경
- Python 미설치 시 명확한 안내 메시지

### Changed
- 자동화 실패 시 MANUAL 모드로 자동 fallback (원본 동작 유지)
- 헬퍼 위치 변경: `~/.claude/skills/orchestra/scripts/.reviewer-bridge-helper.py` → 같은 디렉토리의 `reviewer-bridge-helper.py`

### Migration
v0.1.0 → v0.2.0 업그레이드 후 한 번 실행:
```bash
bash ~/.claude/plugins/cache/lucky-orchestra/orchestra/0.2.0/skills/orchestra/scripts/setup.sh
```

## [0.1.0] - 2026-05-14

### Added
- 초기 릴리스
- 6단계 워크플로: Brief → Plan Research → Research ×N → Synthesize → Review → Decide
- ChatGPT 모델 모드 4종 (deep-research, pro-reasoning, thinking, standard)
- Stage 1.5에서 Conductor가 모드 추천 + 사용자 확정 게이트
- 참조 자료 자동 적재 (파일/디렉토리/URL/텍스트) 및 모든 단계로 전파
- 적응형 이터레이션 (PASS/REVISE/RESTART verdict + max_rounds 안전장치)
- 스크립트: orchestra-init.sh, reviewer-bridge.sh, score-check.sh
- 예제: 논문 공정모델 도출 (polyethylene LDPE)

### Notes
- reviewer-bridge.sh는 gstack browse 도구 없을 시 MANUAL 모드로 fallback
- score-check.sh는 PyYAML 없을 시 grep 폴백 (덜 robust)
