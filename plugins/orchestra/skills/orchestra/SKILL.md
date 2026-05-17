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

1. `plan-prompt.md`의 템플릿에 `01-brief.md` 내용 + **References 본문**을 채워 넣어 프롬프트 파일 생성:
   - frontmatter의 `references[].body_path`를 순회하며 각 자료 본문을 인라인 첨부
   - 본문 길이가 8KB 초과하는 자료는 첫 4KB + "...[truncated]" + 마지막 1KB
   - URL/PDF는 추출된 텍스트만 (raw 바이너리 금지)
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
3. 응답에서 YAML 블록 추출 → 토픽 리스트 확인. 토픽이 0개면 사용자에게 알리고 RESTART 옵션 제시.

### 3. Research (Performer ×N)

`02-research-plan.md`의 토픽을 순회한다. 의존성 그래프를 파싱 (`depends_on` 필드).

- 의존성 없는 토픽 → Task 도구로 **병렬** dispatch (한 메시지에 여러 Task 호출)
- 의존성 있는 토픽 → 의존성 완료 후 dispatch

각 Performer 프롬프트:
```
You are a researcher. Topic: <topic.title>.
Key question: <topic.key_question>.
Expected artifact: <topic.expected_artifact>.

Constraints from the overall objective:
<paste 01-brief.md body>

References available (read these BEFORE researching externally):
<for each r in references:>
- [<r.id>] <r.source> — <r.summary>
  Full text: $RUN_DIR/_refs/<r.id>.md
</for>

You may Read any reference path above. Cite using [r<N>] notation when used.
Produce a thorough markdown report. Cite sources where possible.
DO NOT speculate on other topics. Focus only on yours.
```

Performer는 자기 토픽에 관련된 참조 자료만 선별해 Read한다 (모든 자료를 무조건 읽을 필요 없음).

산출물 저장 경로: `$RUN_DIR/03-research/<topic_id>.md`.

### 4. Synthesize (Conductor)

- 입력: `$RUN_DIR/03-research/*.md` + `$RUN_DIR/01-brief.md`
- 라운드 ≥ 2면 추가 입력: 직전 라운드의 `05-review-v(N-1).md`의 `must_fix` 항목
- 출력: `$RUN_DIR/04-draft-v<round>.md`

통합 시 원칙:
- 모든 토픽 결과를 명시적으로 인용/통합 (드롭 금지)
- must_fix 항목은 통합본 본문에 반영, 변경 내역을 마지막 섹션에 "Round N 변경사항"으로 명기
- 최종 산출물 형식은 `01-brief.md`의 "제약" 필드에 명시된 포맷 따름

### 5. Review (ChatGPT)

1. `reviewer-prompt.md`의 템플릿에 `04-draft-v<round>.md` + `01-brief.md` 내용 + **References 본문**을 채워 프롬프트 생성 (Stage 2와 동일한 트렁케이션 규칙 적용):
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
bash "${CLAUDE_PLUGIN_ROOT}/skills/orchestra/scripts/score-check.sh" "$RUN_DIR/05-review-v<round>.md"
```

스크립트 출력 verdict별 분기:
- `PASS` → `cp "$RUN_DIR/04-draft-v<round>.md" "$RUN_DIR/final.md"`, 사용자에게 완료 보고 + 경로 알림
- `REVISE` AND round < max_rounds → round++ 후 Stage 3부터 재실행. `must_fix`는 Synthesize에서 반영됨
- `REVISE` AND round >= max_rounds → `final.md`에 통합본 + "리뷰어 PASS 전 라운드 한도 도달" 헤더 추가
- `RESTART` → Stage 2부터 재실행 (round는 카운트 유지)
- `PARTIAL` → reviewer-bridge가 부분 응답으로 판정. 사용자에게 재요청 여부 질문 (기본: 같은 라운드 재실행)
- `PARSE_ERROR` → 사용자에게 raw 리뷰 보여주고 수동 verdict 입력 요청

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
