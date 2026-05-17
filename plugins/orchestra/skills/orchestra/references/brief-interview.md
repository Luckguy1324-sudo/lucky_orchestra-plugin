# Brief 인터뷰 가이드 (Stage 1)

목적: 사용자 의도를 5개 핵심 축으로 명확화.

## 5개 질문

### Q1. 목표 (Goal)

```yaml
question: 무엇을 만들고 싶으세요? 한 문장으로 알려주세요.
header: 목표
multiSelect: false
options:
  - label: 직접 입력
    description: "Other 선택 후 한 문장으로 입력 (예: '폴리에틸렌 생산 공정모델 논문 초안')"
```

(인수가 있으면 Q1 스킵하고 인수를 그대로 목표로 사용)

### Q2. 제약 (Constraints)

```yaml
question: 산출물의 형태/제약은 무엇인가요?
header: 제약
multiSelect: true
options:
  - label: Markdown 보고서
    description: 표준 .md 파일 (기본)
  - label: 한국어 작성
    description: 산출물 본문은 한국어
  - label: 인용/참고문헌 필수
    description: 모든 주장에 출처 표기
  - label: 수식/다이어그램 포함
    description: LaTeX 수식 또는 Mermaid 다이어그램 사용
```

### Q3. 성공 기준 (Success criterion)

```yaml
question: 어떤 상태가 되어야 "완료"인가요?
header: 성공 기준
multiSelect: false
options:
  - label: 즉시 사용 가능한 초안
    description: 최소한의 손질로 바로 활용 가능
  - label: 학술적 엄밀성 확보
    description: 인용 정확성 + 논리 완결성 검증된 상태
  - label: 의사결정용 요약
    description: 핵심 결론과 근거만 명확하면 됨
  - label: 직접 입력
    description: Other로 자유 기술
```

### Q4. 참조 자료 (References)

```yaml
question: 참조할 자료가 있나요? 파일/URL/텍스트 어떤 형태든 첨부 가능합니다.
header: 참조 자료
multiSelect: false
options:
  - label: 없음
    description: 참조 자료 없이 진행
  - label: 파일/디렉토리 경로
    description: "@/path/to/file 또는 ./refs/ 형식. Other에 입력 (다수 가능)"
  - label: URL
    description: "https://... 형식. Other에 입력 (다수 가능)"
  - label: 텍스트 직접 paste
    description: Other에 자료 본문 직접 입력
```

**Conductor 처리 절차 (Q4 답변 후)**:
1. 답변 파싱 → 자료 항목 리스트 추출
2. 파일 경로: `Read`로 본문 로드. PDF는 페이지 한계 내에서. 큰 파일은 첫 N줄만.
3. 디렉토리 경로: `ls` + 각 파일에 대해 위 단계 반복. 50개 초과 시 사용자에게 우선순위 질문.
4. URL: `WebFetch`로 본문 가져오기. 실패 시 경고 표시 후 계속 진행.
5. 각 자료에 대해 다음 메타데이터 정리:
   - `id`: r1, r2, ...
   - `source`: 경로/URL/"paste"
   - `type`: file | url | text
   - `size_chars`: 본문 길이
   - `summary`: Conductor가 직접 작성한 1-2줄 요약
6. 자료 본문은 `$RUN_DIR/_refs/<id>.md`로 저장 (각 자료 독립 파일)
7. `01-brief.md`의 frontmatter `references` 필드와 본문 "References" 섹션에 인덱스 작성

### Q5. 최대 라운드 (max_rounds)

```yaml
question: 검토-수정 라운드는 최대 몇 회까지 허용할까요?
header: 라운드 한도
multiSelect: false
options:
  - label: "3 (기본)"
    description: 일반적 작업
  - label: "2"
    description: 빠른 결과 우선
  - label: "5"
    description: 논문/연구 등 고품질 필요
  - label: "1"
    description: 단순 작업, 1회 검토만
```

## 저장 형식 (`01-brief.md`)

```markdown
---
run_id: <YYYYMMDD-HHMMSS-slug>
created_at: <ISO 8601>
stage2_model: <set in Stage 1.5>
stage5_model: <set in Stage 1.5>
max_rounds: <int>
pass_threshold: 8.0
constraints:
  - markdown
  - korean
  - citations
references:
  - id: r1
    source: "./refs/kiparissides-2005.pdf"
    type: file
    size_chars: 12450
    summary: "LDPE 자유라디칼 중합 메커니즘 표준 문헌 (Kiparissides et al., 2005)"
    body_path: "_refs/r1.md"
  - id: r2
    source: "https://example.com/article"
    type: url
    size_chars: 3200
    summary: "튜브형 반응기 운전 조건 사례"
    body_path: "_refs/r2.md"
---

# Objective

<목표 한 문장>

# Constraints

- <constraint 1>
- ...

# Success Criterion

<success criterion>

# References

- **r1** `./refs/kiparissides-2005.pdf` — LDPE 자유라디칼 중합 메커니즘 표준 문헌 (Kiparissides et al., 2005)
- **r2** `https://example.com/article` — 튜브형 반응기 운전 조건 사례

(자료 본문은 `_refs/r<N>.md`에 저장됨)

## Clarifications 섹션 (v0.5.0+, 필요 시 자동 추가)

Stage 2.5 Clarification Gate 또는 Stage 3 Performer escalation에서 사용자 입력을 받았을 때 `01-brief.md` 끝에 다음 형식으로 append된다. 명확한 주제로 시작한 경우 이 섹션은 생성되지 않는다.

```markdown
## Clarifications

### Stage 2.5 (Pre-Research, 라운드 1)

- **q1**: 측정 단위가 톤/일인지 톤/시간인지?
  - **Why needed**: 모델 시뮬레이션 시간 스케일 결정
  - **Answer**: 톤/시간
  - (skip 시) **Assumption applied**: <impact_if_skipped 텍스트>

- **q2**: ...

### Stage 3 — Topic t1 escalation (라운드 1)

- **q1**: 비교 대상 공정은 LDPE에 한정인가, HDPE도 포함인가?
  - **Why needed**: 메커니즘 비교 범위 결정
  - **Answer**: LDPE만
```

이 섹션의 답변은:
- Stage 3 Performer 프롬프트의 `<clarifications>` 섹션으로 그대로 주입됨
- Stage 4 Synthesize 단계에서 Conductor도 참고함
- Stage 5 Reviewer 프롬프트의 `<objective>` 보조 컨텍스트로 함께 전달됨
```

frontmatter의 `stage2_model`/`stage5_model`은 Stage 1.5에서 채운다.
참조 자료가 없으면 `references: []`로 빈 리스트 유지하고 "References" 섹션 생략.
