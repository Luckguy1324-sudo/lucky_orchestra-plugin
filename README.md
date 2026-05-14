# Orchestra

> Multi-AI 협업 오케스트레이션 — Claude Code Opus 4.7이 지휘자가 되어 본인(Performer)과 ChatGPT Pro Deep Research(Reviewer)를 조율해 하나의 결과물을 도출

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
| Conductor (지휘자) | Claude Code Opus 4.7 | 의도 파악, 단계 라우팅, 통합, 품질 평가 |
| Researcher Planner | ChatGPT (모드 선택) | "어떤 리서치가 필요한가" 어젠다 설계 |
| Performer ×N (연주자) | Claude Code Opus 4.7 (Task 서브에이전트) | Plan에 명시된 각 리서치 토픽 병렬 수행 |
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

```
/plugin marketplace add https://github.com/<your-username>/orchestra-plugin
/plugin install orchestra
```

또는 로컬 디렉토리에서 직접:
```
/plugin marketplace add /path/to/orchestra-plugin
/plugin install orchestra
```

## 환경 요구사항

| 항목 | 필수 | 비고 |
|------|------|------|
| Claude Code | ✅ | CLI / 데스크톱 / IDE 확장 모두 가능 |
| ChatGPT Pro 계정 | ✅ | Deep Research 사용 권장 |
| Bash | ✅ | macOS/Linux 기본. Windows는 Git Bash 또는 WSL2 |
| Python 3 + PyYAML | ⚠️ 권장 | 없으면 score-check.sh가 grep 폴백 |
| gstack browse | ⚠️ 권장 | 없으면 reviewer-bridge가 MANUAL 모드 (사용자 직접 paste) |

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
| 3 | **Research** | Performer ×N | `03-research/*.md` |
| 4 | **Synthesize** | Conductor | `04-draft-vN.md` |
| 5 | **Review** | ChatGPT | `05-review-vN.md` |
| 6 | **Decide** | Conductor | `final.md` 또는 라운드 N+1 |

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
- 예제: `skills/orchestra/references/examples/paper-process-model.md`

## 라이선스

MIT
