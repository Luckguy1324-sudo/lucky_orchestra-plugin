# Changelog

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
