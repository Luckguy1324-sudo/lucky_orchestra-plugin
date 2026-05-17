# Plan Research 프롬프트 (Stage 2)

> AI 모델(GPT/Claude 공통)이 안정적으로 해석할 수 있도록 **XML 섹션 + 단일 JSON 출력 강제** 구조로 설계.

## 설계 원칙

| 원칙 | 이유 |
|------|------|
| XML 태그로 컨텍스트 구분 | Claude/GPT 모두 XML 섹션 인식 정확도 높음. 자유 산문보다 mis-attention 적음 |
| 한국어/영어 혼용 금지 | 모델이 출력 언어를 헷갈리지 않도록 영어로 통일 (constraint에 한국어 출력 명시 가능) |
| 출력은 단일 JSON 코드블록 강제 | YAML보다 모호성 적고, downstream parser가 robust |
| 규칙은 numbered list | 모델이 각 항목을 개별 constraint로 처리 |
| schema와 example 같이 제공 | "shape-priming" 효과로 형식 위반률 감소 |
| 출력 직전 trigger phrase | "Now produce..."로 자유 산문 시작 방지 |

## 템플릿

다음 텍스트를 그대로 사용하고 `{{ ... }}` 자리만 채운다. JSON 스키마 부분은 그대로 둔다.

```
<role>
You are a Research Planner. Decompose the OBJECTIVE into the minimum set of independently-researchable topics for parallel execution by junior researchers.
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

<rules>
1. Output 2–5 topics. Fewer is better when feasible.
2. Each topic must be independently researchable — no shared state.
3. Express ordering only via the depends_on field (DAG, no cycles).
4. Topics MAY reference materials by id (e.g., "extends [r1]") in key_question or expected_artifact.
5. risk_flags MUST include at least: missing-info risks, freshness risks, security risks (use empty list only if truly none).
6. estimated_effort ∈ {low, medium, high}.
7. Do not include topics whose sole purpose is summarization — the Conductor handles synthesis.
8. clarification_questions: ONLY include questions whose answers materially change the agenda or affect feasibility. If you can make a reasonable assumption and proceed, DO NOT ask. The default is an empty list. Maximum 3 questions. Each question must include `impact_if_skipped` so the user can decide whether the trade-off is acceptable.
</rules>

<output_format>
Respond with EXACTLY ONE fenced JSON code block. No prose before, after, or between the fences. Match this schema:

```json
{
  "schema_version": "1.0.0",
  "agenda": [
    {
      "topic_id": "t1",
      "title": "Short topic title",
      "key_question": "What exactly should the researcher learn?",
      "expected_artifact": "What file/format the researcher should produce",
      "depends_on": [],
      "estimated_effort": "medium"
    }
  ],
  "notes": ["optional caveats or alternative decompositions"],
  "risk_flags": ["missing-info", "freshness", "security"],
  "clarification_questions": [
    {
      "id": "q1",
      "question": "Specific question the user must answer for the agenda to be reliable",
      "why_needed": "What ambiguity in the brief makes this necessary",
      "impact_if_skipped": "What assumption you will make if user skips, and why output quality may degrade"
    }
  ]
}
```

Most runs should have `"clarification_questions": []`. Use questions ONLY when proceeding without the answer would meaningfully degrade output quality or send research in the wrong direction.
</output_format>

Now produce the JSON.
```

## Reference 블록 형식 (`{{ references_block }}` 자리에 들어갈 내용)

References가 없으면 `(no user-provided references)` 한 줄. 있으면 다음 형식:

```
[r1] ./refs/kiparissides-2005.pdf — LDPE 메커니즘 표준 문헌
---
{본문, 8KB 초과 시 첫 4KB + "...[truncated]..." + 마지막 1KB}
---

[r2] https://example.com/article — 튜브형 반응기 사례
---
{본문}
---
```

## Conductor의 처리 절차

1. `01-brief.md`에서 frontmatter + 본문 추출
2. References 본문을 위 형식으로 패키징 (truncation 8KB 한도)
3. 위 템플릿의 `{{ }}` 자리 채워 `$RUN_DIR/_tmp/plan-prompt.md` 작성
4. `reviewer-bridge.sh --model <stage2_model> "$RUN_DIR/_tmp/plan-prompt.md" "$RUN_DIR/02-research-plan.md"`
5. 응답에서 JSON 코드블록 추출 → 파싱 → DAG 검증 (cycle, 미존재 topic_id 참조)
6. 토픽 0개 또는 cycle 감지 시 사용자에게 RESTART 옵션

## 파일 저장 형식 (`02-research-plan.md`)

```markdown
---
generated_by: chatgpt
model: <stage2_model id>
generated_at: <ISO 8601>
partial: false
---

# Research Agenda

```json
{
  "schema_version": "1.0.0",
  "agenda": [ ... ],
  "notes": [ ... ],
  "risk_flags": [ ... ]
}
```

# Raw Response

<원본 응답 전체>
```

## YAML/JSON 양쪽 수용

기존 v0.2.x는 YAML을 기대했고, 일부 모델이 YAML로 응답할 수도 있다. `score_check.py`/parser는 JSON과 YAML 양쪽 수용 (JSON은 valid YAML이므로 PyYAML로 둘 다 파싱 가능). 그러나 **권장 형식은 JSON** (덜 모호).

## 파싱 가드

- topic_id 중복 검사 (첫 번째만 채택)
- depends_on이 존재하지 않는 topic_id 참조 → 무시 (병렬 실행 가능 처리)
- agenda가 비어있으면 RESTART
- risk_flags가 누락되면 빈 배열로 보강
