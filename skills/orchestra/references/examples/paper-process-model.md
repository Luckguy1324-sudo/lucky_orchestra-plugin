# 예제: 논문 공정모델 도출

`/orchestra "폴리에틸렌 생산 공정모델 논문용 설계. 참조: @./refs/kiparissides-2005.pdf @./refs/prior-attempts.md"` 입력 시 흐름 예시.

## Stage 1 (Brief)

사용자 답변 + 참조 자료 처리 후 `01-brief.md`:

```markdown
---
run_id: 20260514-163000-pe-process-model
created_at: 2026-05-14T16:30:00+09:00
stage2_model: deep-research      # set in 1.5
stage5_model: pro-reasoning      # set in 1.5
max_rounds: 5
constraints:
  - markdown
  - korean
  - citations
  - equations
references:
  - id: r1
    source: "./refs/kiparissides-2005.pdf"
    type: file
    size_chars: 12450
    summary: "LDPE 자유라디칼 중합 메커니즘 표준 문헌 (Kiparissides et al., 2005)"
    body_path: "_refs/r1.md"
  - id: r2
    source: "./refs/prior-attempts.md"
    type: file
    size_chars: 3200
    summary: "이전 모델링 시도 메모"
    body_path: "_refs/r2.md"
---

# Objective
폴리에틸렌 생산 공정모델 논문용 설계 (저밀도 LDPE 기준, 튜브형 반응기)

# Constraints
- Markdown 보고서
- 한국어
- 모든 메커니즘 주장에 출처 표기
- 핵심 반응에 수식 포함

# Success Criterion
학술적 엄밀성 확보 — 인용 정확성과 메커니즘 완결성이 ChatGPT 검토에서 8/10 이상

# References
- **r1** `./refs/kiparissides-2005.pdf` — LDPE 자유라디칼 중합 메커니즘 표준 문헌
- **r2** `./refs/prior-attempts.md` — 이전 모델링 시도 메모
```

## Stage 1.5 (Model)

Conductor 추천:
- Stage 2: `deep-research` (이유: "논문", "공정모델", "인용" 키워드)
- Stage 5: `pro-reasoning` (이유: "학술", "검증" 의미, "엄밀성")

사용자가 "그대로 진행" 선택.

## Stage 2 (Plan Research → ChatGPT Deep Research)

ChatGPT 응답 (`02-research-plan.md`)에 다음 YAML 포함:

```yaml
agenda:
  - topic_id: t1
    title: "LDPE 튜브형 반응기 메커니즘 선행 연구"
    key_question: "최근 10년간 학계가 채택한 자유라디칼 중합 메커니즘과 모델 형식"
    expected_artifact: "선행 연구 8-12편 요약 + 메커니즘 분류표"
    depends_on: []

  - topic_id: t2
    title: "후보 공정 메커니즘 비교"
    key_question: "tube vs autoclave 반응기에서 사슬 이전/종결 반응 차이"
    expected_artifact: "메커니즘별 가정/한계/적용 사례 비교표"
    depends_on: []

  - topic_id: t3
    title: "필요 파라미터 및 경계조건"
    key_question: "온도/압력/이니시에이터 농도 범위, 무차원수, 경계조건"
    expected_artifact: "파라미터 테이블 + 표준 경계조건"
    depends_on: [t1]
```

## Stage 3 (Research)

- t1, t2는 의존성 없음 → 병렬 Task dispatch
- t3는 t1 완료 후 dispatch

각 Performer는 자기 토픽만 보고 마크다운 보고서 작성.

## Stage 4 (Synthesize)

Conductor가 t1+t2+t3 결과를 통합하여 `04-draft-v1.md`:
- §1 서론 (배경+기여점)
- §2 선행 연구 (t1)
- §3 메커니즘 비교 및 선정 (t2)
- §4 제안 모델 (수식, 가정, 경계조건 t3)
- §5 검증 계획
- §6 결론

## Stage 5 (Review → ChatGPT Pro 추론 확장)

ChatGPT 응답 (`05-review-v1.md`):

```yaml
score: 7
strengths:
  - "메커니즘 비교가 명확함"
  - "수식 표현이 일관됨"
must_fix:
  - issue: "사슬 이전 상수 출처가 누락된 표 3"
    where: "§4 Table 3"
    fix_direction: "Kiparissides et al. (2005) 또는 등가 출처 인용 추가"
  - issue: "경계조건 §4.3에서 압력 단위 혼용 (bar/atm)"
    where: "§4.3"
    fix_direction: "전 문서 bar로 통일"
nice_to_have:
  - "검증 계획에 in-situ Raman 추가 고려"
verdict: REVISE
verdict_reason: "구조와 분석은 양호하나 인용 누락과 단위 혼용은 학술 기준 미달"
```

## Stage 6 (Decide)

- verdict=REVISE, round=1, max_rounds=5 → 라운드 2 진입
- Stage 3 재실행 시 must_fix가 Synthesize 단계에서 반영됨
- 라운드 2 통합본 `04-draft-v2.md` → 다시 Stage 5 검토
- 만약 score ≥ 8 + verdict=PASS → `final.md` 생성, 완료

## 산출물 디렉토리 (예)

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
├── 04-draft-v2.md
├── 05-review-v2.md          # verdict=PASS
├── final.md                 # = 04-draft-v2.md 복사본
├── _refs/                   # 참조 자료 본문 (Brief에서 적재)
│   ├── r1.md                # kiparissides-2005.pdf 추출 텍스트
│   └── r2.md                # prior-attempts.md 사본
└── meta.json
```
