# Orchestra v0.8.0

> Multi-AI 협업 오케스트레이션 — Claude Code Opus가 지휘자가 되어 본인(Performer)과
> ChatGPT Pro(Reviewer)를 조율해 하나의 결과물을 도출. v0.8.0은 **빈 페이지의 전제를 검토
> 전에 먼저 다지는 지식 구축(R)**, **공정 물리 그라운딩(PH)**, **수렴 기반 판정 게이트(CV)**를
> v0.7.0의 scoping 강화(S)·컨텍스트 내구성(C)과 8가지 검증 메커니즘(①–⑧) 위에 추가한다.

## v0.8.0에서 추가된 것 (R · PH · CV)

**지식 구축 (R1–R3)** — CHALLENGE *전에* breadth-first Landscape 패스를 돌려 빈 페이지의
전제를 먼저 다진다. 동적 research-coverage 표준(출처 유형·최신성·삼각검증)과 누락-커버리지
검토 렌즈(Persona D)로 "무엇을 빠뜨렸는가"를 잡는다. `references/research-standards.md`,
`references/landscape-template.md`.

**물리 그라운딩 (PH)** — 2-layer `physics_check.py`를 pre-gate에 연결. 보편 불변식(질량·에너지
closure, 2법칙)은 항상 검사하고, 설계 결정 기준은 라운드를 거치며 동적으로 형성한다.

**수렴 게이트 (CV)** — `score_gate.py`가 수렴 기반으로 판정한다. CONFIRM 확인 패스,
disagreement ledger, 정체 시 HUMAN_ESCALATE. pass_threshold 7 → 8로 상향.

## 기반 세 기둥 (v0.7.0)

orchestra는 아래 세 가지 위에서 작동한다.

**검증 (①–⑧)** — 리뷰를 *신뢰할 수 있게* 만든다. 리뷰어 편향 가드, severity 태그, 안티-
그룹싱크 페르소나, 웹 검증, 포렌식 트레이스, 판정 권한 분리, kill-argument, 결정론적 사전
게이트.

**Scoping (S1–S4)** — *올바른 문제*를 검토하게 만든다. 완벽하게 검증된 틀린 답이 가장 비싼
실패다. CHALLENGE 게이트가 생산 전에 전제를 압박 테스트하고, confidence gap 점수가 가장
약한 곳에 검토 자원을 집중시킨다.

**컨텍스트 내구성 (C1–C3)** — 긴 작업에서도 *품질이 떨어지지 않게* 만든다. 무거운 단계를
격리 서브에이전트로 실행해 메인 컨텍스트를 평평하게 유지하고, 모든 scope 결정의 "왜"를
보존해 압축이 일어나도 초기 의도가 살아남는다.

## 워크플로 (7단계 + 3게이트)

```
 0.5 [LANDSCAPE 패스 R1] ── breadth-first 지식 구축: 전제를 검토 전에 먼저 다짐
 1   Brief ─────────────── acceptance_criteria 수집 (S3)
 1.5 [CHALLENGE 게이트 S1/S2] ── 강제 질문: 올바른 문제를 푸는가? + decisions[] WHY 기록 (C2)
 2   Plan (ChatGPT NEW창) ── 에이전다 + 토픽별 confidence gap 점수 (S4) + research-coverage 표준 (R2)
 3   Research ×N (격리 서브에이전트, 병렬) ── 고-gap 토픽 우선 심화 (S4, C1)
 4   Synthesize (격리 Synthesizer 서브에이전트) ── must_fix 주입 (C1)
 5.5 [PRE-GATE ⑧ + PH] ── 기계적 검증 + physics_check.py(질량·에너지 closure, 2법칙)를 리뷰 전에
 6   Review: 6a blind①② / 6b persona③ / 6c web④ / 6d kill⑦ / 6e missing-coverage(Persona D, R3)
 7   [DECIDE 게이트 ⑥ + CV] ── score_gate.py: PASS/REVISE/RESTART + CONFIRM·disagreement ledger·HUMAN_ESCALATE
```

## 핵심 메커니즘 요약

| 그룹 | 항목 |
|------|------|
| 검증 ①–⑧ | bias guard, severity tag, persona, web-verify, trace, acquit-gate, kill-argument, pre-gate |
| Scoping S1–S4 | CHALLENGE 게이트, 단계별 강제질문, 안티-아첨, confidence-gap 가중 |
| 내구성 C1–C3 | 격리 서브에이전트 실행, decision-log(why), 압축 우선순위 |
| 지식구축 R1–R3 (v0.8.0) | Landscape 패스, research-coverage 표준, 누락-커버리지 렌즈(Persona D) |
| 물리 PH (v0.8.0) | 2-layer physics_check(보편 불변식 + 동적 결정기준), pre-gate 연동 |
| 수렴 CV (v0.8.0) | CONFIRM 패스, disagreement ledger, HUMAN_ESCALATE, threshold 7→8 |

상세 근거는 references 폴더 참조: `verification-mechanisms.md`, `scoping-rules.md`,
`forcing-questions.md`, `context-durability.md`, `research-standards.md`,
`landscape-template.md`.

## 설치

```
/plugin marketplace add https://github.com/Luckguy1324-sudo/lucky_orchestra-plugin
/plugin install orchestra@lucky-orchestra
```

설치 후 `/orchestra` 사용 가능. 업데이트는 `/plugin update orchestra`.

## 사용법

```
/orchestra 폴리에틸렌 공정모델 논문용 설계
/orchestra                                    # Brief + CHALLENGE부터
/orchestra 공정모델 설계. 참조: @./refs/choi-2025.pdf
```

## 수동 연결

ChatGPT Pro를 **수동 paste**로 활용하는 것을 전제로 설계됐다. 모든 메커니즘(①–⑧, S1–S4,
C1–C3, R1–R3, PH, CV)은 수동 연결에서도 품질을 전혀 잃지 않는다 — 핵심은 API가 아니라
프롬프트 설계, 결정론적 스크립트, 서브에이전트 격리에 있기 때문이다. `references/manual-vs-auto.md` 참조.

**가장 중요한 습관:** 워크플로가 "NEW window"라고 하면 실제로 새 ChatGPT 대화를 열어라.
메커니즘 ①의 전부가 이것이다.

## 환경 요구사항

| 항목 | 필수 | 비고 |
|------|------|------|
| Claude Code | ✅ | 서브에이전트 dispatch 지원 (C1에 필요) |
| ChatGPT Pro | ✅ | Deep Research 권장 |
| Bash | ✅ | macOS/Linux. Windows는 Git Bash/WSL2 |
| Python 3.8+ | ✅ | score_gate.py, confidence_gap.py, physics_check.py |
| latexmk | ⚠️ | LaTeX 논문일 때만 |
| Playwright + Chromium | ⚠️ | AUTO 모드만. 없으면 MANUAL 자동 폴백 |

## 마이그레이션

v0.7.0 → v0.8.0은 `docs/v0.8.0-upgrade-notes.md` 참조 (이전 단계는 `docs/MIGRATION.md`).
기존 run과 호환되며 meta.json은 자동 확장된다.

## 라이선스
MIT
