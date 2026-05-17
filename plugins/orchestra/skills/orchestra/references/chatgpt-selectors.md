# ChatGPT UI Selectors — 안내 문서

> **Single source of truth는 `selectors.json`입니다.** 이 파일은 그 내용을 사람이 읽기 좋게 설명하는 보조 문서입니다.

## 어디서 변경해야 하나?

ChatGPT UI가 변경되어 자동화가 깨지면 다음 파일을 패치하세요:

```
${CLAUDE_PLUGIN_ROOT}/skills/orchestra/references/selectors.json
```

`reviewer-bridge-helper.py`는 이 파일을 자동으로 다시 읽으므로 별도 빌드 단계 없이 다음 실행부터 반영됩니다. 파일이 누락되거나 파싱 실패 시 코드 내 fallback 셀렉터로 동작합니다.

## selectors.json 구조

```jsonc
{
  "common": {
    "prompt":          [...prompt textarea selectors],
    "send":            [...send button selectors],
    "stop":            [...stop streaming button selectors],
    "assistant_message": "...",
    "signin_indicators": [...],
    "error_indicators":  [...]
  },
  "modes": {
    "deep-research":  { "url": "...", "poll_interval": 30, "start_timeout": 180, "extract_timeout": 600 },
    "pro-reasoning":  { "url": "...", "poll_interval": 15, ... },
    "thinking":       { ... },
    "standard":       { ... }
  }
}
```

`common.*` 셀렉터는 배열 순서대로 시도 (앞이 우선). 첫 매칭으로 선택.

## 폴링 정책 개요 (v0.2.1+)

3-페이즈 상태 머신:

| Phase | 의미 | 타임아웃 |
|-------|------|---------|
| WAITING_FOR_START | Submit 후 "생성 중" 신호 대기 | `start_timeout` |
| **GENERATING** | "Stop streaming" 버튼 visible — 모델 작업 중 | **무제한** |
| EXTRACTING | 생성 멈춤, 텍스트 안정화 대기 | `extract_timeout` |

ChatGPT 작업 시간(GENERATING)에는 타임아웃이 없습니다. 타임아웃은 "submit 실패(WAITING)" / "텍스트 안정화 실패(EXTRACTING)" 같은 자동화 측 오류만 감지.

추가 오류 감지: sign-in 페이지 출현, error/rate-limit 배너, 페이지 crash → 즉시 실패.

## 모드별 진입 절차

### `deep-research`

1. URL 직접 진입: `https://chatgpt.com/?model=deep-research`
2. 또는 모델 피커에서 "Pro Deep Research" 클릭
3. 입력창 상단에 "Deep research" 라벨 표시 확인
4. 완료 표시: "Stop streaming" 버튼 사라짐 + "Research complete" 또는 "Read sources" 토글 등장

### `pro-reasoning`

1. URL: `https://chatgpt.com/?model=gpt-5-pro`
2. 모델 피커에서 "GPT-5 Pro" 선택
3. 추론 강도 토글: 입력창 좌측 옵션 메뉴 → "Reasoning effort" → "Extended" 또는 "Max"
4. 완료 표시: 일반 응답 완료 신호 (stop button 사라짐 + 텍스트 안정화)

### `thinking`

1. URL: `https://chatgpt.com/?model=gpt-5-thinking`
2. 모델 피커에서 "GPT-5 Thinking" 선택
3. 완료 표시: 일반 응답 완료 신호

### `standard`

1. URL: `https://chatgpt.com/?model=gpt-5`
2. 모델 피커에서 "GPT-5" 선택
3. 완료 표시: 일반 응답 완료 신호

## 응답 추출 절차 (helper 내부)

1. 가장 최근 `[data-message-author-role="assistant"]` 노드 선택
2. `inner_text()` 추출 (마크다운 구조는 일부 손실 가능)
3. Deep Research의 경우 "Read sources" 토글이 있으면 펼친 후 인용 목록도 함께 수확

## 폴백 동작

- 모드별 URL이 동작하지 않으면 helper는 그대로 진입한 페이지에서 모델 피커 시도
- 셀렉터가 모두 실패하면 reviewer-bridge.sh가 MANUAL 모드로 전환

## 셀렉터 업데이트 절차

1. reviewer-bridge 실패 보고 받으면 selectors.json 열기
2. 브라우저 개발자 도구로 새 셀렉터 확인
3. 해당 배열에 추가 (앞쪽이 우선)
4. 다음 호출부터 자동 반영 — 별도 재시작 불필요
