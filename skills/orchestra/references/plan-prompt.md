# Plan Research 프롬프트 템플릿 (Stage 2)

ChatGPT에 전달할 리서치 어젠다 설계 프롬프트.

## 템플릿

```
You are a research planner. Given the following OBJECTIVE, produce a research
agenda for a team that will execute the research in parallel.

Constraints:
- List the MINIMUM number of independent research topics required.
- Each topic should be independently researchable (no shared state).
- If two topics must share information, express it via `depends_on`.
- Aim for 2-5 topics. More than 5 means you're over-decomposing.

Output STRICTLY as a single YAML code block. No prose outside the block.
Schema:

```yaml
agenda:
  - topic_id: t1
    title: "Short topic title"
    key_question: "What exactly should the researcher learn?"
    expected_artifact: "What file/format the researcher should produce"
    depends_on: []        # list of topic_ids that must finish first
  - topic_id: t2
    ...
notes: |
  Any caveats, alternative decompositions, or risks (optional).
```

OBJECTIVE
=========
<paste content of 01-brief.md body here, including frontmatter constraints>

SUCCESS CRITERION
=================
<paste success criterion section from 01-brief.md>

USER-PROVIDED REFERENCES
========================
The user has provided the following reference materials. Use them to ground
the agenda — topics should leverage these materials, not duplicate them.

<for each r in references:>
[<r.id>] <r.source> — <r.summary>
---
<paste body content from $RUN_DIR/_refs/<r.id>.md, truncated per skill rules>
---
</for>

<if references is empty:>
(No user-provided references. Plan the agenda from scratch.)
</if>

Now produce the YAML agenda. Topics MAY reference these materials via their
ids (e.g., "extends [r1]") in `key_question` or `expected_artifact`.
```

## Conductor의 처리 절차

1. 위 템플릿의 `<paste ...>` 자리에 `01-brief.md`의 해당 섹션을 그대로 삽입
2. 결과를 `$RUN_DIR/_tmp/plan-prompt.md`에 저장
3. reviewer-bridge로 호출 → `$RUN_DIR/02-research-plan.md` 수신
4. 응답에서 ```yaml ... ``` 블록만 추출, `02-research-plan.md`를 다음 형식으로 정리:

```markdown
---
generated_by: chatgpt
model: <stage2_model id>
generated_at: <ISO 8601>
---

# Research Agenda

```yaml
agenda:
  - topic_id: t1
    ...
```

# Raw Response

<원본 응답 전체>
```

5. 토픽이 0개 또는 의존성 사이클 감지 시 사용자에게 알리고 RESTART 옵션 제시.

## 파싱 가드

- yq 또는 python yaml로 agenda 노드 추출 시도. 실패 시 raw 응답 그대로 사용자에게 표시.
- topic_id 중복 검사. 중복 시 첫 번째만 채택, 경고 출력.
- depends_on이 존재하지 않는 topic_id를 참조하면 무시 (parallel 실행 가능 처리).
