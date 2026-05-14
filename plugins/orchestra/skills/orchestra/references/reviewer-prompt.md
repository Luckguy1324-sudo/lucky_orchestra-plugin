# Review 프롬프트 템플릿 (Stage 5)

ChatGPT에 전달할 통합본 검토 프롬프트.

## 템플릿

```
You are a senior reviewer. Critically evaluate the DRAFT below against the
ORIGINAL OBJECTIVE and SUCCESS CRITERION. Identify strengths, must-fix issues,
and nice-to-have improvements. Then deliver a verdict.

Be specific. Each issue should be actionable — a writer should be able to fix
it without further clarification.

Output STRICTLY as a single YAML code block. No prose outside the block.
Schema:

```yaml
score: <integer 0-10>
strengths:
  - "..."
  - "..."
must_fix:
  - issue: "..."
    where: "section/line if identifiable"
    fix_direction: "what to do"
nice_to_have:
  - "..."
verdict: PASS | REVISE | RESTART
verdict_reason: "1-2 sentences"
```

Verdict guidance:
- PASS: success criterion met, no critical issues
- REVISE: critical issues exist but the plan/structure is sound
- RESTART: the research plan itself was wrong; better to redo Stage 2

ORIGINAL OBJECTIVE
==================
<paste 01-brief.md objective + constraints + success criterion>

USER-PROVIDED REFERENCES
========================
Materials the user attached to the brief. Use them as the ground truth when
checking the draft. Flag any contradiction between the draft and these
materials as must_fix.

<for each r in references:>
[<r.id>] <r.source> — <r.summary>
---
<paste body content from $RUN_DIR/_refs/<r.id>.md, truncated per skill rules>
---
</for>

<if references is empty:>
(No user-provided references. Evaluate the draft on its own merits.)
</if>

DRAFT (Round <N>)
=================
<paste 04-draft-v<N>.md>

<if N >= 2>
PREVIOUS REVIEW (Round <N-1>)
==============================
<paste 05-review-v(N-1).md>

Note: Check whether previous must_fix items were addressed in this draft.
</if>

Now produce the YAML review.
```

## Conductor의 처리 절차

1. 템플릿의 `<paste ...>` 부분을 채워 `$RUN_DIR/_tmp/review-prompt-v<round>.md`에 저장
2. reviewer-bridge로 호출 → `$RUN_DIR/05-review-v<round>.md` 수신
3. score-check.sh로 파싱 → verdict 결정

## 파싱 가드

- yq 또는 python yaml로 verdict, score 추출
- score가 숫자가 아니면 PARSE_ERROR
- verdict가 PASS|REVISE|RESTART 셋 중 하나가 아니면 PARSE_ERROR
- must_fix가 비어있는데 verdict가 REVISE면 경고 + 사용자 확인

## 파일 저장 형식 (`05-review-v<N>.md`)

```markdown
---
generated_by: chatgpt
model: <stage5_model id>
round: <N>
generated_at: <ISO 8601>
verdict: <PASS|REVISE|RESTART>
score: <int>
---

# Review (Round <N>)

```yaml
score: ...
strengths: ...
must_fix: ...
nice_to_have: ...
verdict: ...
verdict_reason: ...
```

# Raw Response

<원본 응답 전체>
```
