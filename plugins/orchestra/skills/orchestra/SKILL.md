---
name: orchestra
description: Multi-AI 협업 오케스트레이션 스킬. Claude Code Opus 4.7이 지휘자가 되어 본인(Performer)과 ChatGPT Pro Deep Research(Reviewer)를 조율해 하나의 결과물을 도출한다. "/orchestra", "오케스트라", "협업해줘", "여러 AI로 만들어줘" 같은 요청에 사용된다.
---

# Orchestra — Multi-AI 협업 오케스트레이션

> Conductor (Claude Opus 4.7) — Performer ×N (Claude Opus 4.7) — Reviewer (ChatGPT Pro Deep Research)

## 핵심 원칙

1. **역할 분리**: 본인이 한 일을 본인이 검증하지 않는다. Reviewer는 별도 모델.
2. **단계 외부화**: 모든 산출물은 파일로 떨어뜨려 다음 단계의 입력으로 사용.
3. **적응형 루프**: 품질 임계치 통과까지 Review-Revise 반복, 단 max_rounds 안전장치.
4. **사용자 통제**: Stage 1.5에서 ChatGPT 모드 선택, max_rounds 결정.

## 사전 준비 (스킬 진입 시 즉시 수행)

다음 레퍼런스를 Read로 읽는다:
- `${CLAUDE_PLUGIN_ROOT}/skills/orchestra/references/brief-interview.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/orchestra/references/model-recommendation.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/orchestra/references/plan-prompt.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/orchestra/references/reviewer-prompt.md`

브라우저 자동화 첫 호출 직전에 읽는다:
- `${CLAUDE_PLUGIN_ROOT}/skills/orchestra/references/chatgpt-selectors.md`

## 워크플로

### 0. Init

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/orchestra-init.sh" "<slug>"
```

- `<cwd>/.orchestra/runs/<run-id>/`를 만들고 run-id를 echo한다 (`YYYYMMDD-HHMMSS-<slug>`).
- 이후 모든 경로는 `RUN_DIR=$(pwd)/.orchestra/runs/<run-id>`.
- `meta.json` 초기화: `{"run_id":..., "started_at":..., "round":1, "verdict_history":[]}`.

### 1. Brief

`brief-interview.md`에 명시된 5개 질문을 AskUserQuestion으로 순차 실행:

1. 목표 (한 줄 텍스트 → Other로 받기)
2. 제약 (마감/포맷/길이)
3. 성공 기준
4. **참조 자료** (파일/URL/텍스트, 다수 허용)
5. 최대 라운드 (기본 3, 옵션: 1, 2, 3, 5)

**Q4 후속 처리 (참조 자료 로딩)**:
- 파일 경로 → `Read`로 본문 적재
- 디렉토리 → `ls` 후 각 파일 적재 (50개 초과 시 우선순위 질문)
- URL → `WebFetch`로 본문 적재
- 각 자료는 `$RUN_DIR/_refs/r<N>.md`에 저장하고 `01-brief.md` frontmatter의 `references` 리스트에 인덱싱 (id, source, type, size_chars, summary, body_path)

답변을 `01-brief.md`에 frontmatter+본문으로 저장.

### 1.5. Model

`model-recommendation.md`의 휴리스틱을 적용해 Stage 2와 Stage 5의 ChatGPT 모드를 추천한다. 그 다음 AskUserQuestion으로 추천안+이유 표시 → 사용자 확정.

선택 결과를 `01-brief.md` frontmatter의 `stage2_model`, `stage5_model`에 기록.

### 2. Plan Research (ChatGPT)

1. `plan-prompt.md`의 **v0.4.0 XML-tagged + JSON-output 템플릿**을 사용:
   - `<role>`, `<objective>`, `<success_criterion>`, `<constraints>`, `<references>`, `<rules>`, `<output_format>` 섹션 구조 그대로 사용
   - References 본문은 `<references>` 섹션 내부에 `[r1] path — summary` 라벨 + 본문 fenced로 인라인
   - 본문 길이 8KB 초과 시 head 4KB + "...[truncated]..." + tail 1KB
   - URL/PDF는 추출된 텍스트만 (raw 바이너리 금지)
   - 출력 형식: 단일 fenced JSON 코드블록 (`agenda`, `notes`, `risk_flags`)
   ```
   $RUN_DIR/_tmp/plan-prompt.md
   ```
2. reviewer-bridge로 호출:
   ```bash
   STAGE2_MODEL=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/frontmatter_get.py" \
     "$RUN_DIR/01-brief.md" stage2_model)
   bash "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/reviewer-bridge.sh" \
     --model "$STAGE2_MODEL" \
     "$RUN_DIR/_tmp/plan-prompt.md" \
     "$RUN_DIR/02-research-plan.md"
   ```
3. 응답에서 JSON 블록 추출 → `agenda`, `clarification_questions` 파싱. 토픽이 0개면 사용자에게 알리고 RESTART 옵션 제시.

### 2.5. Clarification Gate (Pre-Research)

**목적**: ChatGPT planner가 식별한 진짜 필요한 질문만 사용자에게 묻고, 답변을 Stage 3에 주입. 명확한 주제의 90%+ 경우 이 단계는 자동 skip된다.

**흐름**:

1. `02-research-plan.md`의 JSON에서 `clarification_questions` 배열 추출
2. 배열이 비어있으면 → **즉시 Stage 3로 진행** (이게 디폴트, 가장 흔한 경로)
3. 비어있지 않으면 (1~3개):
   - 각 질문을 AskUserQuestion으로 사용자에게 표시 (`question`, `why_needed`, `impact_if_skipped` 모두 보여줌)
   - 각 질문에는 "Skip — use AI's best guess" 옵션을 항상 포함
4. 사용자 답변 수집:
   - 답변한 질문 → 그대로 기록
   - skip한 질문 → `(Skipped — proceeding with assumption: <impact_if_skipped 텍스트>)` 기록
5. `01-brief.md` 끝에 `## Clarifications` 섹션 append:

```markdown
## Clarifications

### Stage 2.5 (Pre-Research, 라운드 {round_no})

- **q1**: <question>
  - **Why needed**: <why_needed>
  - **Answer**: <user answer | "Skipped">
  - (skip 시) **Assumption applied**: <impact_if_skipped>

- **q2**: ...
```

6. `meta.json`에 `clarifications_count` 카운터 increment (디버깅용)
7. Stage 3로 진행. Performer 프롬프트의 `<clarifications>` 섹션에 위 정보 주입.

**안전장치**:
- 같은 라운드에서 Stage 2.5는 한 번만 실행. 같은 라운드 재진입 시 (REVISE 등) 이미 답변된 질문은 다시 묻지 않음.
- 라운드 N≥2 진입 시 Reviewer가 새로운 clarification을 요구해도 Stage 2.5는 라운드 1 결과를 그대로 들고 진행 (재질문 금지). Reviewer는 must_fix로 표현해야 함.
- `clarifications_count > 6` (한 run 총량) 시 사용자에게 경고: "AI가 자료를 과도하게 요구하고 있습니다. 작업 종료 후 brief를 보강하는 것이 효율적일 수 있습니다."

### 3. Research (Performer ×N) — `research-worker` named subagent

`02-research-plan.md`의 agenda를 순회한다. 의존성 그래프를 파싱 (`depends_on`).

- 의존성 없는 토픽 → Task 도구로 **병렬** dispatch (한 메시지에 여러 Task 호출), `subagent_type: "research-worker"`
- 의존성 있는 토픽 → 의존성 완료 후 dispatch

**Round N ≥ 2 (must_fix 자동 주입)**:
- `05-review-v(N-1).md`에서 `must_fix` 배열 추출
- 각 토픽 i에 대해 해당 토픽 관련 must_fix만 필터링:
  - `scope_topic_id == topic_id_i` (정확 매칭) — 최우선
  - `scope_topic_id == null` (synthesis 또는 다중 토픽) — 모든 토픽에 공통 전달
- 필터링된 must_fix 항목을 해당 Performer 프롬프트의 `<previous_must_fix>` 섹션에 JSON 배열로 주입

각 research-worker dispatch 프롬프트 형식 (XML 섹션):

```
<run_context>
run_id: $RUN_ID
round_no: $ROUND
topic_id: <topic.topic_id>
</run_context>

<objective>
<paste 01-brief.md objective>
</objective>

<constraints>
<paste 01-brief.md constraints>
</constraints>

<topic>
title: <topic.title>
key_question: <topic.key_question>
expected_artifact: <topic.expected_artifact>
</topic>

<references>
[<r.id>] <r.source> — <r.summary>
  Full text path: $RUN_DIR/_refs/<r.id>.md
... (다른 refs 동일 형식)
</references>

<previous_must_fix>
{Round ≥ 2 only — JSON array of relevant must_fix items}
{Round 1 → 이 섹션 자체를 생략 또는 빈 배열 "[]"}
</previous_must_fix>

Now research the topic. Return a markdown report as your final message.
```

research-worker 서브에이전트는 자기 토픽 정보만 본다 (다른 토픽 차단됨).

**Stage 2.5 clarifications 주입**: `01-brief.md`의 `## Clarifications` 섹션 내용을 Performer 프롬프트의 `<clarifications>` 섹션으로 전달. 답변과 skip된 항목의 assumption 모두 포함.

**Performer-level escalation 처리** (research-worker 응답이 `## Cannot proceed`로 시작하는 경우):

1. Conductor가 subagent 응답에서 `escalation:` YAML 블록 파싱
2. 추출되는 필드: `reason`, `clarification_requests[]` (최대 2개), `suggested_default`
3. AskUserQuestion으로 각 질문 표시 + "Skip — use suggested_default" 옵션 추가
4. 답변 수집 후 `01-brief.md`에 추가 섹션 append:

```markdown
### Stage 3 — Topic {topic_id} escalation (라운드 {round_no})

- **q1**: <question>
  - **Answer**: <user answer | "Skipped — using default: <suggested_default>">
```

5. 같은 Performer를 재dispatch — `<clarifications>` 섹션에 새 답변 포함. 다른 Performer는 영향 없음.
6. 같은 토픽에서 escalation은 라운드당 1회만 허용. 두 번째 escalation 시 사용자에게 알리고 `suggested_default`로 강제 진행.

**산출물**: Conductor가 subagent의 최종 메시지(텍스트)를 받아 `$RUN_DIR/03-research/<topic_id>.md`로 저장.

### 4. Synthesize (Conductor)

- 입력:
  - `$RUN_DIR/03-research/*.md` (모든 Performer 결과)
  - `$RUN_DIR/01-brief.md` (objective, constraints, refs index)
  - Round ≥ 2: `$RUN_DIR/05-review-v(N-1).md`의 must_fix (전체 — Performer가 못 본 synthesis-level 이슈도 포함)
- 출력: `$RUN_DIR/04-draft-v<round>.md`

통합 시 원칙:
1. 모든 토픽 결과를 명시적으로 인용/통합 (드롭 금지)
2. **must_fix 적용 양분**: Performer 단계에서 이미 본 항목(scope_topic_id가 토픽에 매칭)은 Performer 출력에 반영된 것을 인용/통합. Synthesis-level 항목(scope_topic_id=null) 또는 Performer가 미해결로 남긴 항목은 통합 단계에서 Conductor가 직접 처리.
3. 라운드 N≥2 통합본 마지막에 `## Round N 변경사항` 섹션 추가 — 직전 must_fix 각 항목에 대해 "어떻게 반영됐는지" 한 줄씩 명기. 이는 다음 라운드 Reviewer가 점검할 대상.
4. 최종 산출물 형식은 `01-brief.md`의 `constraints` 필드 따름 (한국어 / 인용 필수 / 수식 포함 등).

### 5. Review (ChatGPT)

1. `reviewer-prompt.md`의 **v0.4.0 XML-tagged + JSON-output 템플릿**을 사용:
   - `<objective>`, `<success_criterion>`, `<constraints>`, `<references>`, `<draft>` 섹션 채우기
   - Round ≥ 2면 `<previous_review>` 섹션에 직전 라운드 `must_fix` JSON 배열 첨부 (Reviewer가 각 항목 해결 여부 점검하도록)
   - `<consistency_rules>`에서 PASS-but-low-score / PASS-with-must_fix 자기모순 차단 명시
   - 출력 형식: 단일 fenced JSON 코드블록, `must_fix` 항목마다 `scope_topic_id` 필드 포함
   - 트렁케이션 규칙은 Stage 2와 동일 (8KB 한도, head 4K + tail 1K)
   ```
   $RUN_DIR/_tmp/review-prompt-v<round>.md
   ```
2. reviewer-bridge로 호출:
   ```bash
   STAGE5_MODEL=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/frontmatter_get.py" \
     "$RUN_DIR/01-brief.md" stage5_model)
   bash "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/reviewer-bridge.sh" \
     --model "$STAGE5_MODEL" \
     "$RUN_DIR/_tmp/review-prompt-v<round>.md" \
     "$RUN_DIR/05-review-v<round>.md"
   ```

### 6. Decide

```bash
PASS_THRESHOLD=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/frontmatter_get.py" \
  "$RUN_DIR/01-brief.md" pass_threshold 2>/dev/null || echo "8.0")
MAX_ROUNDS=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/frontmatter_get.py" \
  "$RUN_DIR/01-brief.md" max_rounds 2>/dev/null || echo "3")

DECISION=$(bash "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/score-check.sh" \
  "$RUN_DIR/05-review-v<round>.md" "$PASS_THRESHOLD" "$round" "$MAX_ROUNDS")
```

`$DECISION`은 `<VERDICT> <SCORE>` 형식 한 줄 (예: `PASS 8.7`, `REVISE 7.0`, `PASS_WITH_WARNINGS 6.5`, `PARTIAL 0`, `PARSE_ERROR 0`).

스크립트 출력 verdict별 분기:

- `PASS` → finalize (아래 절차 참조)
- `PASS_WITH_WARNINGS` → finalize, 단 final.md 상단에 "max_rounds 도달, REVISE 잔여 이슈 있음" 헤더 추가
- `REVISE` AND round < max_rounds → round++ 후 **Stage 3부터 재실행**. must_fix는 다음 라운드 research-worker 프롬프트(Stage 3)와 Synthesize 프롬프트(Stage 4) **양쪽**에 자동 주입됨
- `RESTART` → Stage 2부터 재실행 (round는 카운트 유지)
- `PARTIAL` → reviewer-bridge가 부분 응답 판정. 사용자에게 재요청 여부 질문 (기본: 같은 라운드 재실행)
- `PARSE_ERROR` → 사용자에게 raw 리뷰 보여주고 수동 verdict 입력 요청

**finalize 절차 (PASS / PASS_WITH_WARNINGS 공통)**:

```bash
# 1. 최종 draft를 final.md로 복사
cp "$RUN_DIR/04-draft-v<round>.md" "$RUN_DIR/final.md"

# 2. Provenance 섹션 자동 부착
python3 "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/build-provenance.py" \
  "$RUN_DIR" --plugin-version 0.4.0 >> "$RUN_DIR/final.md"

# 3. PASS_WITH_WARNINGS인 경우 상단에 경고 헤더 prepend (sed 또는 임시 파일)
```

Provenance 섹션은 run_id, started_at, 사용 모델, 라운드별 verdict/score, 참조자료 목록, 생성된 파일 목록을 자동 정리한다 — final.md만 보면 어떤 과정으로 만들어졌는지 추적 가능.

매 분기마다 `meta.json`의 `verdict_history`에 push.

## 진행 보고 패턴

각 Stage 종료 시 1줄 보고:
```
[Stage 3/6] Research: 3개 토픽 병렬 진행 중 (worker-1/2/3)
[Stage 5/6] Review: ChatGPT Pro Deep Research 응답 대기 (예상 5-30분)
[Stage 6/6] Decide: verdict=REVISE, must_fix 2개. 라운드 2 진입
```

## 중단/재개

`meta.json`에 `current_stage`, `round`를 매번 업데이트. 같은 run-id로 재진입 시 그 단계부터 이어 실행.

## 안티패턴

- **Stage 2 건너뛰기**: Conductor가 자기 머리로 토픽 정하지 말 것. 반드시 ChatGPT에 위임.
- **Performer가 다른 토픽 정보 보기**: 각 Performer 프롬프트에는 자기 토픽 정보만 넣는다 (격리).
- **Review 결과 임의 해석**: verdict는 score-check.sh가 산출한 값을 그대로 따른다. Conductor가 "괜찮아 보이는데" 같은 판단으로 우회 금지.
- **무한 루프**: max_rounds 안전장치 절대 우회 금지.
