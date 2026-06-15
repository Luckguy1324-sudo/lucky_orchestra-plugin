# Orchestra — Multi-AI 협업 오케스트레이션 Skill 설계

**작성일**: 2026-05-14
**상태**: 승인 대기 → 구현 진행
**저자**: 정우 (with Claude Code)

## 1. 목적

사용자가 한 가지 목표(예: 논문 공정모델 설계)를 던지면,
Claude Code Opus 4.8이 지휘자(Conductor)가 되어 본인(Performer) 및
ChatGPT Pro Deep Research(Reviewer)와 협업하여 최종 산출물을 자동 도출한다.

기존 단일 모델 워크플로의 한계 — "본인이 한 일을 본인이 검증" — 를
**역할 분리 + 모델 분리**로 해결한다.

## 2. 역할 분리

| Role | Model | 책임 |
|------|-------|------|
| Conductor (지휘자) | Claude Code Opus 4.8 (메인 세션) | 의도 파악, 단계 라우팅, 통합, 품질 평가, **ChatGPT 모델 모드 추천** |
| Researcher Planner | ChatGPT (모드: 사용자 선택, 기본 Pro Deep Research) | "어떤 리서치가 필요한가" 어젠다 설계 |
| Performer ×N (연주자) | Claude Code Opus 4.8 (Task 서브에이전트) | Plan에 명시된 각 리서치 토픽 병렬 수행 |
| Reviewer (검토자) | ChatGPT (모드: 사용자 선택, 기본 Pro Deep Research) | 통합본 심층 검토, 점수 + 구체 피드백 |

### ChatGPT 모델 모드 카탈로그

| ID | 표시명 | 특징 | 적합한 작업 | 예상 소요 |
|----|--------|------|------------|----------|
| `deep-research` | Pro Deep Research | 광범위한 웹 리서치 + 인용 + 장문 보고서 | 신뢰성·인용 필수, 학술/시장 조사 | 5–30분 |
| `pro-reasoning` | Pro 추론 확장 | 최고 추론 강도, 다단계 사고 | 복잡한 모델링/증명, 트레이드오프 분석 | 1–5분 |
| `thinking` | Thinking | 표준 확장 사고 | 일반 검토, 논리 점검 | 30초–2분 |
| `standard` | Standard | 빠른 응답, 추론 짧음 | 단순 요약, 포맷 변환 | 즉시 |

각 모드는 `reviewer-bridge.sh --model <id>`로 호출 시 URL/UI 셀렉터가 달라짐.
스테이지 2와 5는 각각 독립적으로 모드 지정 가능 (예: Stage 2는 deep-research로 리서치 어젠다, Stage 5는 pro-reasoning으로 빠른 검토).

**Conductor ≠ Performer 분리 이유**: 같은 모델이라도 메인 세션의 컨텍스트와
서브에이전트의 격리된 컨텍스트는 다른 역할을 한다. Conductor는 메타 관점
유지, Performer는 단일 토픽에 집중.

## 3. 6단계 워크플로

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

| # | 단계 | 주체 | 입력 | 산출물 |
|---|------|------|------|--------|
| 1 | **Brief** | Conductor | 사용자 한 줄 요청 | `01-brief.md` (목표·제약·성공기준·최대 라운드) |
| 2 | **Plan Research** | ChatGPT Pro DR (브라우저) | `01-brief.md` | `02-research-plan.md` (토픽 N개, 각 토픽별 질문/기대 산출물) |
| 3 | **Research** | Performer ×N (Task 서브에이전트) | `02-research-plan.md`의 토픽 i | `03-research/<topic-i>.md` |
| 4 | **Synthesize** | Conductor | `03-research/*.md` + (라운드 ≥ 2면) `05-review-v(N-1).md` | `04-draft-vN.md` |
| 5 | **Review** | ChatGPT Pro DR (브라우저) | `04-draft-vN.md` + `01-brief.md` | `05-review-vN.md` (구조화된 점수+피드백) |
| 6 | **Decide** | Conductor | `05-review-vN.md` | `final.md` 또는 라운드 진입 |

### Stage 1: Brief

Conductor가 AskUserQuestion으로 사용자 의도 명확화:
- 목표 (한 문장)
- 제약 (마감·예산·도구·산출물 형식)
- 성공 기준 (어떤 상태가 되어야 종료인가)
- 최대 라운드 (기본 3, 논문급 5)

**ChatGPT 모델 모드 결정 (1.5 단계)**:
1. Conductor가 위 답변을 기반으로 Stage 2(Plan Research)와 Stage 5(Review)
   각각에 어떤 모델 모드가 적합한지 **추천**한다.
   - 추천 로직 (간단 휴리스틱, `references/model-recommendation.md`에 상세):
     - 목표에 "리서치/조사/인용/문헌/학술" 키워드 → Stage 2: deep-research
     - 목표에 "모델/설계/증명/수식/알고리즘" 키워드 → Stage 5: pro-reasoning
     - 목표에 "초안/요약/포맷" 키워드 → standard
     - 기본값: 양 단계 모두 deep-research
2. AskUserQuestion으로 추천안 제시 + 사용자가 변경 가능:
   ```
   추천: Stage 2 = Pro Deep Research, Stage 5 = Pro 추론 확장
   이유: 논문 공정모델은 리서치 폭이 중요하고, 검토는 깊은 추론이 필요해서요.
   변경하시겠어요? [그대로 / Stage 2만 변경 / Stage 5만 변경 / 둘 다 변경]
   ```
3. 최종 선택을 `01-brief.md`의 frontmatter에 저장:
   ```yaml
   ---
   stage2_model: deep-research
   stage5_model: pro-reasoning
   max_rounds: 3
   ---
   ```

산출물은 frontmatter + plain Markdown. 이후 모든 단계의 컨텍스트 기준이 됨.

### Stage 2: Plan Research (NEW)

ChatGPT Pro Deep Research에 다음 프롬프트 전달:
```
You are a research planner. Given the following objective, produce a research
agenda. List the minimum number of independent research topics required to
achieve the objective. For each topic, specify:
- topic_id, title
- key_question (what we need to learn)
- expected_artifact (what the researcher should produce)
- depends_on (topic_ids that must finish first, if any)

Return as YAML.

OBJECTIVE:
<paste 01-brief.md>
```

산출물 `02-research-plan.md`에 YAML 블록으로 저장. Conductor가 파싱해서
Stage 3의 워커 수와 토픽을 결정.

### Stage 3: Research

Conductor는 Plan의 토픽 수만큼 Task 서브에이전트를 dispatch.
의존성이 없는 토픽은 병렬, 있는 토픽은 의존성 해소 후 dispatch.

각 Performer 프롬프트는 자기 토픽의 `key_question` + `expected_artifact`만
포함 (다른 토픽 정보는 전달하지 않음 — 격리).

옵션 `--use-codex` 사용 시 Task 서브에이전트 대신 pumasi 스크립트 호출해서
Codex CLI로 병렬 실행 (Claude 토큰 절약).

### Stage 4: Synthesize

Conductor가 모든 Performer 결과 + (라운드 2 이상이면) 직전 Review의
`must_fix`를 입력으로 받아 통합본 작성. 라운드 N의 산출물은
`04-draft-vN.md`.

### Stage 5: Review

ChatGPT Pro Deep Research에 통합본 + Brief 전달, 다음 양식으로 답을 받음:

```yaml
score: 0-10            # 종합 점수
strengths:
  - "..."
must_fix:              # 다음 라운드 진입 시 Performer/Synthesizer에 그대로 주입
  - "..."
nice_to_have:
  - "..."
verdict: PASS | REVISE | RESTART
verdict_reason: "..."
```

### Stage 6: Decide

분기 규칙:
- `verdict: PASS` → `04-draft-vN.md`를 `final.md`로 복사, 종료
- `verdict: REVISE` AND `round < max_rounds` → 라운드 N+1 (Stage 3부터)
- `verdict: REVISE` AND `round >= max_rounds` → 강제 종료, `final.md`에
  "리뷰어가 PASS 판정 전 라운드 한도 도달" 명기
- `verdict: RESTART` → Plan 자체가 잘못됨. Stage 2부터 재실행 (총 라운드
  카운트 유지)

## 4. ChatGPT 브라우저 자동화

### 첫 실행 (세션당 1회)

```bash
# Conductor가 호출
gstack browser open --profile orchestra
# 사용자에게 "ChatGPT에 로그인 후 Deep Research 액세스 확인되면 Enter" 안내
```

### 검토 호출 (Stage 2 & 5)

`scripts/reviewer-bridge.sh --model <model-id> <prompt-file> <output-file>`:
1. `<model-id>` 별 진입 URL / UI 토글 매핑 (`references/chatgpt-selectors.md`):
   - `deep-research` → 모델 피커에서 "Pro Deep Research" 선택, 작업 라벨 확인
   - `pro-reasoning` → "Pro" 모델 + "추론 강도: 확장" 토글
   - `thinking` → "Thinking" 모드 토글
   - `standard` → 기본 모델
2. 진입 후 프롬프트 파일 내용 paste
3. 모드별 폴링 정책:
   - `deep-research`: 5분 간격, 최대 30분
   - `pro-reasoning`: 30초 간격, 최대 5분
   - `thinking`: 15초 간격, 최대 2분
   - `standard`: 5초 간격, 최대 30초
4. 완료 감지 시 응답 텍스트 추출 → output-file에 저장
5. 메타데이터 헤더 prepend (모드, 시작/종료 시각, 추출 길이)

### 안전장치

| 실패 모드 | 감지 | 복구 |
|----------|------|------|
| 인증 만료 | "Sign in" 버튼 감지 | 사용자에게 재로그인 요청 후 재시도 |
| Deep Research 응답 없음 | 30분 폴링 후 미완료 | 사용자에게 알림, 대기 연장 or 중단 선택 |
| YAML 파싱 실패 | `yq` 실패 | raw 응답 그대로 저장 + 사용자 확인 |
| Rate limit | "Too many requests" 텍스트 감지 | exponential backoff, 최대 3회 |

## 5. 파일/디렉토리 구조

### 플러그인 구조

```
~/.claude/plugins/local/orchestra/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── orchestra.md
├── skills/orchestra/
│   ├── SKILL.md
│   └── references/
│       ├── brief-interview.md
│       ├── plan-prompt.md
│       ├── reviewer-prompt.md
│       ├── model-recommendation.md   # Stage 1.5 추천 휴리스틱
│       ├── chatgpt-selectors.md      # 모드별 URL/UI 셀렉터
│       └── examples/
│           └── paper-process-model.md
└── scripts/
    ├── orchestra-init.sh
    ├── reviewer-bridge.sh
    └── score-check.sh
```

### 런타임 상태 (사용자 CWD 하위)

```
<cwd>/.orchestra/runs/<run-id>/
├── 01-brief.md
├── 02-research-plan.md
├── 03-research/
│   ├── topic-1.md
│   └── topic-2.md
├── 04-draft-v1.md
├── 05-review-v1.md
├── 04-draft-v2.md          # (REVISE 시)
├── 05-review-v2.md
├── meta.json               # round 카운트, 시작 시각, verdict 이력
└── final.md                # 종료 시 생성
```

`run-id`: `YYYYMMDD-HHMMSS-<slug>` 형식.

## 6. 트리거

```
명시적: /orchestra <goal>
        /orchestra (인수 없음 → Brief 인터뷰만 진행)

내부 코드는 한국어 명령도 인식 (/orchestra <목표>).
```

## 7. 기존 플러그인과의 관계

- **kkirikkiri**: Stage 1 인터뷰 패턴(AskUserQuestion 사용법)을 참고. 직접 호출
  안 함. 의도: 워크플로 무거움 회피.
- **pumasi**: Stage 3 병렬 dispatch 패턴 차용. `--use-codex` 옵션 시
  `pumasi.sh` 직접 호출.
- **open-gstack-browser / browse**: Stage 2 & 5의 ChatGPT 자동화에 사용.

## 8. 비범위 (Out of Scope, v1)

- ChatGPT 외 다른 LLM(Claude.ai 웹 UI 등) 검토자 옵션 — v2
- 시각적 산출물(다이어그램, 도표) 자동 생성 — v2
- 멀티 사용자 / 팀 협업 모드 — v3
- 비용 추정 / 토큰 회계 — v2

## 9. 성공 기준

논문 공정모델 예제로 다음을 만족:
1. `/orchestra` 한 번으로 6단계 자동 실행
2. Stage 1.5에서 ChatGPT 모드 추천이 표시되고 사용자가 변경 가능
3. Stage 2에서 선택된 모드로 ChatGPT가 최소 3개 토픽 어젠다 산출
4. Stage 3에서 토픽 수만큼 병렬 Performer dispatch 확인
5. Stage 5가 선택된 모드로 호출되고 응답이 YAML 파싱 가능
6. PASS 시 `final.md` 자동 생성, REVISE 시 라운드 N+1 자동 진행
7. 라운드 한도 도달 시 강제 종료 메시지 명확

## 10. 리스크 & 미해결 이슈

| 리스크 | 영향 | 완화 |
|--------|------|------|
| ChatGPT UI 변경으로 셀렉터 깨짐 | Stage 2 & 5 실패 | 모든 셀렉터를 `references/chatgpt-selectors.md`에 분리, 사용자가 패치 가능 |
| 추천 모드가 작업에 안 맞음 | 시간/비용 낭비 | Stage 1.5에서 사용자가 override 가능, 사용 후 `meta.json`에 모드별 성능 기록 (향후 추천 개선) |
| Deep Research 응답 시간 가변 | UX 답답함 | 폴링 상태를 사용자에게 표시 |
| 인증 세션 만료 | 중간 단계 실패 | 인증 확인을 매 호출 전 수행 |
| 토픽 의존성 사이클 | Stage 3 deadlock | Plan 파싱 시 사이클 감지 |

## 11. 후속 계획 (Plan 작성으로 이어짐)

이 spec이 승인되면 writing-plans skill로 step-by-step 구현 plan을 만든다.
주요 마일스톤 후보:
- M1: 플러그인 스캐폴드 + plugin.json + 명령 진입점
- M2: Stage 1 (Brief) 인터뷰 구현
- M3: reviewer-bridge.sh + 첫 ChatGPT 자동화 동작 확인
- M4: Stage 2 (Plan Research) 통합
- M5: Stage 3 (Research) 병렬 dispatch
- M6: Stage 4–6 (Synthesize/Review/Decide) + 루프
- M7: 논문 공정모델 예제로 end-to-end 검증

## 12. 강화된 교차검증 설계 (Hardened Cross-Validation ①–⑧)

v0.6.0에서 Review/Decide 단계는 8개 메커니즘으로 하드닝되어, 단일 Reviewer 응답에 의존할 때
생기는 편향·환각·groupthink·점수 인플레이션을 구조적으로 차단한다. 상세 정의는
`skills/orchestra/references/verification-mechanisms.md`.

| # | 메커니즘 | 적용 단계 | 산출물/스크립트 |
|---|---------|----------|----------------|
| ① | reviewer-bias guard / blind 스코어링 | Stage 5a | 새 ChatGPT 창, `_review/05a-blind-vN.md` |
| ② | severity 태깅 (CRITICAL→MINOR 정렬) | Stage 5 통합 | `05-review-vN.md`의 `must_fix[].severity` |
| ③ | anti-groupthink 페르소나 | Stage 5b | `references/persona-sets.md`, `_review/05b-*` |
| ④ | claim→근거 웹 검증 | Stage 5c | WebSearch/WebFetch, `_review/05c-claim-audit-vN.md` |
| ⑤ | forensic raw trace 보존 | Stage 5 전체 | `_review/` 하위 불변 원문 |
| ⑥ | acquit-gate 분리 | Stage 6 | `score-check.sh` / `score_gate.py` |
| ⑦ | kill-argument 적대 검토 | Stage 5d | `_review/05d-kill-vN.md` |
| ⑧ | deterministic pre-gate | Stage 4.5 | `scripts/pre_gate.sh` |

**설계 원칙**:
- 채점(scoring)과 finding-해결(acquittal)을 분리한다 — 미해결 CRITICAL이 있으면 점수와 무관하게 REVISE(⑥).
- 모든 검증은 자동화에 비의존적이다 — MANUAL 모드에서도 동일 절차로 수행(`references/manual-vs-auto.md`).
- 모든 raw 응답은 삭제·요약 없이 보존해 사후 추적(forensic) 가능(⑤).
