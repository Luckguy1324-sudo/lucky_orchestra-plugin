# ChatGPT 모델 모드 추천 휴리스틱 (Stage 1.5)

## 모드 카탈로그

| ID | 표시명 | 적합한 작업 | 예상 소요 |
|----|--------|------------|----------|
| `deep-research` | Pro Deep Research | 인용·문헌·시장조사·학술 리서치 | 5–30분 |
| `pro-reasoning` | Pro 추론 확장 | 모델링·증명·트레이드오프 분석·검증 | 1–5분 |
| `thinking` | Thinking | 일반 검토·논리 점검 | 30초–2분 |
| `standard` | Standard | 요약·포맷 변환·간단 검증 | 즉시 |

## Stage 2 (Plan Research) 추천 규칙

목표 텍스트 또는 제약에서 키워드 매칭. 첫 매칭으로 결정 (우선순위 순).

| 우선순위 | 키워드 (목표/제약) | 추천 모드 | 이유 |
|---------|------------------|----------|------|
| 1 | 논문, 학술, 인용, 참고문헌, 문헌, 메타분석, 시장조사, 경쟁분석 | `deep-research` | 광범위 출처+인용 필수 |
| 2 | 리서치, 조사, 알아봐, 비교, 동향 | `deep-research` | 외부 정보 폭이 중요 |
| 3 | 설계, 모델, 알고리즘, 아키텍처, 수식 | `pro-reasoning` | 깊은 추론 필요, 외부 폭은 부차 |
| 4 | 초안, 요약, 변환, 정리 | `standard` | 형식 변환 위주 |
| 0 (기본) | (매칭 없음) | `deep-research` | 안전 기본값 |

## Stage 5 (Review) 추천 규칙

| 우선순위 | 키워드 (목표/제약) | 추천 모드 | 이유 |
|---------|------------------|----------|------|
| 1 | 학술, 논문, 검증, 엄밀, 증명 | `pro-reasoning` | 논리 정합성과 깊은 검토 |
| 2 | 인용, 참고문헌, 출처 | `deep-research` | 인용 정확성 재확인 |
| 3 | 빠른, 간단, 초안 | `thinking` | 가벼운 점검 |
| 4 | 시장, 트렌드, 데이터 | `deep-research` | 최신성 재확인 |
| 0 (기본) | (매칭 없음) | `pro-reasoning` | 깊은 검토가 디폴트로 안전 |

## 추천 출력 양식 (사용자에게 보여줄 메시지)

```
📋 Stage 1.5: ChatGPT 모델 모드 추천

목표: <목표 한 문장>
제약: <constraints>

추천:
  Stage 2 (리서치 어젠다 설계) → <recommended_stage2> (<korean_label>)
    이유: <키워드 매칭/기본값 사유>
  Stage 5 (통합본 검토) → <recommended_stage5> (<korean_label>)
    이유: <키워드 매칭/기본값 사유>
```

그 다음 AskUserQuestion으로 다음 선택지 제시:

```yaml
question: 추천한 모드 그대로 진행할까요?
header: 모드 확정
multiSelect: false
options:
  - label: 그대로 진행
    description: 추천한 stage2/stage5 모드로 진행
  - label: Stage 2만 변경
    description: Stage 5는 추천 유지, Stage 2 모드 다시 고르기
  - label: Stage 5만 변경
    description: Stage 2는 추천 유지, Stage 5 모드 다시 고르기
  - label: 둘 다 변경
    description: Stage 2/5 모두 모드 다시 고르기
```

변경 선택 시 후속 질문 (한 단계씩):

```yaml
question: Stage <N>에서 사용할 ChatGPT 모드는?
header: 모드 선택
multiSelect: false
options:
  - label: Pro Deep Research (5-30분)
    description: 광범위 웹 리서치 + 인용 + 장문 보고서
  - label: Pro 추론 확장 (1-5분)
    description: 최고 추론 강도, 다단계 사고
  - label: Thinking (30초-2분)
    description: 표준 확장 사고
  - label: Standard (즉시)
    description: 빠른 응답, 추론 짧음
```

선택 결과를 `01-brief.md` frontmatter의 `stage2_model` / `stage5_model`에 ID(`deep-research` 등)로 기록.
