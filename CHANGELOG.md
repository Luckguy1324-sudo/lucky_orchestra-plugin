# Changelog

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
