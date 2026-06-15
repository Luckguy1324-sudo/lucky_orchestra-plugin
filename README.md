# Orchestra

> Multi-AI 협업 오케스트레이션 — Claude Code Opus 4.8이 지휘자가 되어 본인(Performer)과 ChatGPT Pro Deep Research(Reviewer)를 조율해 하나의 결과물을 도출. 8개 메커니즘으로 하드닝된 교차검증(hardened cross-validation) 내장.

## 핵심 아이디어

한 가지 목표(예: 논문 공정모델 설계)를 던지면 Claude Code가 6단계 워크플로로 ChatGPT와 협업해 산출물을 만든다. **본인이 한 일을 본인이 검증하지 않는다** — Performer는 Claude, Reviewer는 ChatGPT.

```
┌──────┐   ┌──────────────┐   ┌──────────┐   ┌────────────┐   ┌────────┐   ┌────────┐
│Brief │ → │Plan Research │ → │ Research │ → │ Synthesize │ → │ Review │ → │ Decide │
│      │   │  (ChatGPT)   │   │ (×N병렬) │   │            │   │(ChatGPT│   │        │
└──────┘   └──────────────┘   └──────────┘   └────────────┘   └────────┘   └────────┘
                                                                                │
                              ┌─────────────────────────────────────────────────┘
                              │
                              ▼
                  PASS → final.md (종료)
                  REVISE → 라운드 N+1 (Research부터 재실행)
                  RESTART → Plan부터 재실행
```

## 역할 분리

| Role | Model | 책임 |
|------|-------|------|
| Conductor (지휘자) | Claude Code Opus 4.8 | 의도 파악, 단계 라우팅, 통합, 품질 평가 |
| Researcher Planner | ChatGPT (모드 선택) | "어떤 리서치가 필요한가" 어젠다 설계 |
| Performer ×N (연주자) | Claude Code Opus 4.8 (Task 서브에이전트) | Plan에 명시된 각 리서치 토픽 병렬 수행 |
| Reviewer (검토자) | ChatGPT (모드 선택) | 통합본 심층 검토, 점수 + 구체 피드백 |

## ChatGPT 모드 카탈로그

| ID | 표시명 | 적합한 작업 | 예상 소요 |
|----|--------|------------|----------|
| `deep-research` | Pro Deep Research | 인용·문헌·시장조사·학술 리서치 | 5–30분 |
| `pro-reasoning` | Pro 추론 확장 | 모델링·증명·검증 | 1–5분 |
| `thinking` | Thinking | 일반 검토 | 30초–2분 |
| `standard` | Standard | 요약·포맷 변환 | 즉시 |

Stage 1.5에서 Conductor가 목표 키워드 기반으로 추천 → 사용자가 그대로 / 변경 선택.

## 설치

Claude Code 세션에서 두 줄:

```
/plugin marketplace add https://github.com/Luckguy1324-sudo/lucky_orchestra-plugin
/plugin install orchestra@lucky-orchestra
```

또는 marketplace 별칭 없이:
```
/plugin install orchestra
```

설치 성공 시 `/orchestra` 명령 사용 가능.

### 업데이트
```
/plugin update orchestra
```

### 제거
```
/plugin uninstall orchestra
```

## 환경 요구사항

| 항목 | 필수 | 비고 |
|------|------|------|
| Claude Code | ✅ | CLI / 데스크톱 / IDE 확장 모두 가능 |
| ChatGPT Pro 계정 | ✅ | Deep Research 사용 권장 |
| Bash | ✅ | macOS/Linux 기본. Windows는 Git Bash 또는 WSL2 |
| Python 3.8+ + Playwright + Chromium | ⚠️ 권장 | ChatGPT 자동화에 필수. 없으면 MANUAL 모드 (사용자 직접 paste) |
| PyYAML | ⚠️ 권장 | 없으면 score-check.sh가 grep 폴백 |

### 자동화 설치 (Stage 2/5 ChatGPT 자동 입력/수확)

v0.2.0부터 ChatGPT 자동화가 포함됐습니다. plugin 설치 후 한 번 실행:

```bash
# 버전 글로브로 자동 감지 (권장)
bash ~/.claude/plugins/cache/lucky-orchestra/orchestra/*/skills/orchestra/scripts/setup.sh
```

또는 특정 버전 명시:
```bash
bash ~/.claude/plugins/cache/lucky-orchestra/orchestra/0.3.0/skills/orchestra/scripts/setup.sh
```

(설치된 버전은 `/plugin list`로 확인)

설치되는 것:
- Playwright (Python 패키지, `pip --user`로 설치)
- Chromium 브라우저 (~200MB, Playwright 전용 격리 설치)

**첫 실행 시**: orchestra가 Stage 2 단계에서 브라우저 창을 열어줍니다 (headed 모드). ChatGPT에 로그인하면 `~/.orchestra/chrome-profile/`에 세션이 저장돼 이후 자동 재사용됩니다.

자동화를 건너뛰고 싶으면 setup.sh를 실행하지 마세요. orchestra는 자동으로 MANUAL 모드로 fallback합니다 (사용자가 직접 paste).

## 사용법

### 기본 실행

```
/orchestra 폴리에틸렌 공정모델 논문용 설계
```

또는 인수 없이 → Brief 인터뷰부터:
```
/orchestra
```

### 참조 자료 첨부

```
/orchestra 공정모델 설계. 참조: @./refs/kiparissides-2005.pdf @./refs/prior-attempts.md
```

또는 Brief 인터뷰 Q4 "참조 자료" 단계에서 경로 입력.

## 워크플로 6단계

| # | 단계 | 주체 | 산출물 |
|---|------|------|--------|
| 1 | **Brief** | Conductor (인터뷰) | `01-brief.md` |
| 1.5 | **Model** | Conductor (추천) + 사용자 (확정) | frontmatter에 모드 기록 |
| 2 | **Plan Research** | ChatGPT | `02-research-plan.md` |
| 2.5 | **Clarification Gate** | Conductor (필요시) | `01-brief.md`의 `## Clarifications` |
| 3 | **Research** | Performer ×N | `03-research/*.md` |
| 4 | **Synthesize** | Conductor | `04-draft-vN.md` |
| 4.5 | **Pre-Gate (⑧)** | `pre_gate.sh` (결정론적) | PASS 후에만 Review 진입 |
| 5 | **Review (4-pass)** | ChatGPT + Conductor | `05-review-vN.md` + `_review/` raw |
| 6 | **Decide (⑥)** | Conductor | `final.md` 또는 라운드 N+1 |

## 강화된 교차검증 (Hardened Cross-Validation ①–⑧)

리뷰는 단일 패스가 아니라 8개 메커니즘으로 하드닝되어 편향·환각·groupthink를 차단한다:

| # | 메커니즘 | 설명 |
|---|---------|------|
| ① | reviewer-bias guard / blind 스코어링 | 매 라운드 새 ChatGPT 창에서 채점 (직전 맥락 오염 차단) |
| ② | severity 태깅 | finding을 CRITICAL→MAJOR→MINOR로 정렬 |
| ③ | anti-groupthink 페르소나 | 도메인별 페르소나가 별도 창에서 교차 검토 |
| ④ | claim→근거 웹 검증 | 표준 조항·수치를 1차 출처에 대조, 미확인은 finding |
| ⑤ | forensic raw trace | 모든 서브패스 원문을 `_review/`에 불변 보존 |
| ⑥ | acquit-gate 분리 | 미해결 CRITICAL이면 점수가 높아도 REVISE |
| ⑦ | kill-argument | "결론을 무너뜨려라" 적대 검토 패스 |
| ⑧ | deterministic pre-gate | 리뷰 전 기계적 결함 사전 차단 (`pre_gate.sh`) |

정의는 `skills/orchestra/references/verification-mechanisms.md`. **이 메커니즘은 자동화 여부와 무관하게 MANUAL 모드에서도 동일하게 동작한다** (`references/manual-vs-auto.md`).

## 런타임 상태

각 run은 `<cwd>/.orchestra/runs/<run-id>/`에 저장:

```
.orchestra/runs/20260514-163000-pe-process-model/
├── 01-brief.md
├── 02-research-plan.md
├── 03-research/
│   ├── t1.md
│   ├── t2.md
│   └── t3.md
├── 04-draft-v1.md
├── 05-review-v1.md
├── _review/             ← 4-pass 서브패스 raw trace (⑤, 불변)
│   ├── 05a-blind-v1.md
│   ├── 05b-<persona>-v1.md
│   ├── 05c-claim-audit-v1.md
│   └── 05d-kill-v1.md
├── final.md
├── _refs/              ← 참조 자료 본문
└── meta.json
```

## 적응형 이터레이션

Reviewer가 매 라운드마다 verdict 발급:
- `PASS` → `final.md` 생성, 종료
- `REVISE` → 다음 라운드 (must_fix 항목을 Synthesize에 주입)
- `RESTART` → Plan부터 재실행

`max_rounds` 안전장치 (기본 3, 논문급 5 권장).

## 참조

- 설계 문서: 본 repo의 `docs/design.md` (선택적 포함)
- 검증 메커니즘: `skills/orchestra/references/verification-mechanisms.md` (①–⑧)
- 마이그레이션: `docs/MIGRATION.md`
- 예제: `skills/orchestra/references/examples/paper-process-model.md`

## 라이선스

MIT
