# Review 프롬프트 (Stage 5)

> AI 모델이 안정적으로 해석할 수 있도록 **XML 섹션 + 단일 JSON 출력 강제** 구조. plan-prompt와 동일한 설계 원칙.

## 핵심 변경 (v0.4.0)

- `must_fix` 항목에 **`scope_topic_id`** 필드 추가 → 다음 라운드에서 해당 토픽 Performer 프롬프트에 자동 라우팅 가능
- `previous_must_fix` 섹션 (Round ≥ 2) → Reviewer가 직전 라운드 이슈가 실제로 해결됐는지 명시적으로 점검

## 템플릿

```
<role>
You are a Senior Reviewer. Critically evaluate the DRAFT against the ORIGINAL OBJECTIVE and SUCCESS CRITERION. Be specific. Each issue must be actionable — a writer should be able to fix it without further clarification.
</role>

<objective>
{{ objective_one_liner }}
</objective>

<success_criterion>
{{ success_criterion_text }}
</success_criterion>

<constraints>
{{ constraints_yaml_list }}
</constraints>

<references>
{{ references_block }}
</references>

<draft round="{{ round_no }}">
{{ draft_body }}
</draft>

{{ previous_review_block_or_empty }}

<verdict_guidance>
PASS — success criterion met, score >= {{ pass_threshold }}, no critical issues
REVISE — structure is sound but specific issues remain
RESTART — research plan itself is flawed; Stage 2 must redo
</verdict_guidance>

<consistency_rules>
1. If verdict=PASS, must_fix MUST be empty. Otherwise pick REVISE.
2. If verdict=PASS, score MUST be >= {{ pass_threshold }}. Otherwise pick REVISE.
3. If you cite a problem in must_fix, also indicate which topic_id is responsible (if any) via scope_topic_id, so the next round can route the fix correctly. Use null if the issue spans multiple topics or belongs to synthesis.
4. partial = true ONLY if your own response is incomplete (truncated). Do not use this to indicate the draft is incomplete; that goes into must_fix.
</consistency_rules>

<output_format>
Respond with EXACTLY ONE fenced JSON code block. No prose before, after, or between the fences. Match this schema:

```json
{
  "schema_version": "1.0.0",
  "score": 0.0,
  "pass_threshold": {{ pass_threshold }},
  "strengths": ["..."],
  "must_fix": [
    {
      "issue": "Concrete problem description",
      "where": "section / line / heading if identifiable",
      "fix_direction": "What to do",
      "scope_topic_id": "t1"
    }
  ],
  "nice_to_have": ["..."],
  "verdict": "PASS",
  "verdict_reason": "1-2 sentences",
  "partial": false
}
```

verdict ∈ {"PASS", "REVISE", "RESTART"}. scope_topic_id ∈ topic_id values from the plan, or null.
</output_format>

Now produce the JSON.
```

## `previous_review_block_or_empty` (Round ≥ 2 only)

Round 1에서는 빈 문자열. Round 2 이상에서는 직전 라운드 must_fix 항목 삽입:

```
<previous_review round="{{ round - 1 }}">
The previous reviewer flagged these must_fix items. For each, indicate in your evaluation whether this draft addressed it:
{{ previous_must_fix_json_array }}
</previous_review>
```

## Reference 블록 형식

plan-prompt와 동일 (`[r1] path — summary` + 본문 truncated).

## Conductor의 처리 절차

1. `01-brief.md` + `04-draft-v<N>.md` + `_refs/*.md` 로드
2. Round ≥ 2면 `05-review-v(N-1).md`에서 must_fix 배열 추출
3. 템플릿 채워서 `$RUN_DIR/_tmp/review-prompt-v<N>.md` 작성
4. `reviewer-bridge.sh --model <stage5_model> "..." "$RUN_DIR/05-review-v<N>.md"`
5. `score-check.sh "$RUN_DIR/05-review-v<N>.md" <pass_threshold> <round_no> <max_rounds>` 호출 → effective_decision 획득

## 파싱 가드 (`score_check.py`가 이미 처리)

- verdict이 enum 밖이면 PARSE_ERROR
- score가 숫자 아니면 0 처리
- PASS이지만 score < threshold OR must_fix 비어있지 않음 → REVISE로 escalate
- REVISE + round >= max_rounds → PASS_WITH_WARNINGS
- frontmatter/JSON의 `partial: true` → PARTIAL

## 파일 저장 형식 (`05-review-v<N>.md`)

```markdown
---
generated_by: chatgpt
model: <stage5_model id>
round: <N>
generated_at: <ISO 8601>
partial: false
verdict: <PASS|REVISE|RESTART>
score: <float>
---

# Review (Round <N>)

```json
{
  "schema_version": "1.0.0",
  "score": ...,
  ...
}
```

# Raw Response

<원본 응답 전체>
```
