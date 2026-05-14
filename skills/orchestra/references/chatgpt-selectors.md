# ChatGPT UI Selectors (모드별)

ChatGPT 웹 UI를 자동화할 때 사용하는 셀렉터 / URL / 토글 위치. UI가 변경되면 이 파일만 패치하면 reviewer-bridge가 다시 동작한다.

> **주의**: ChatGPT는 종종 UI 변경이 있다. 동작 실패 시 가장 먼저 이 파일을 확인하라.

## 공통

| 요소 | 셀렉터 (CSS) | 비고 |
|-----|------------|------|
| Base URL | `https://chatgpt.com/` | 로그인된 세션 가정 |
| Sign-in 감지 | `text=Log in` 또는 `text=Sign in` 가시화 시 미인증 | 인증 만료 시그널 |
| 모델 피커 버튼 | `button[aria-label*="Model selector"]` | 좌측 상단 또는 채팅 입력창 위 |
| 입력 textarea | `textarea#prompt-textarea` 또는 `[contenteditable="true"]` | 메시지 입력란 |
| 전송 버튼 | `button[data-testid="send-button"]` | |
| 응답 컨테이너 | `div[data-message-author-role="assistant"]` (최근 노드) | |
| "생성 중" 인디케이터 | `button[aria-label="Stop streaming"]` 가시화 | 아직 미완료 |
| 응답 완료 신호 | "Stop streaming" 버튼 사라짐 + "Regenerate" 버튼 등장 | |

## 모드별 진입 절차

### `deep-research`

1. URL 직접 진입: `https://chatgpt.com/?model=deep-research`
2. 또는 모델 피커에서 "Pro Deep Research" 항목 클릭 (`role="menuitem"`, text contains "Deep Research")
3. 선택 후 입력창 상단에 "Deep research" 라벨 표시 확인
4. 폴링 정책: 5분 간격, 최대 30분
5. 완료 표시: 응답 카드 상단에 "Research complete" 텍스트 또는 "Read sources" 토글 등장

### `pro-reasoning`

1. URL: `https://chatgpt.com/?model=gpt-5-pro`
2. 모델 피커에서 "GPT-5 Pro" 선택
3. 추론 강도 토글: 입력창 좌측 옵션 메뉴 → "Reasoning effort" → "Extended" 또는 "Max"
4. 폴링 정책: 30초 간격, 최대 5분
5. 완료 표시: 일반 응답 완료 신호와 동일

### `thinking`

1. URL: `https://chatgpt.com/?model=gpt-5-thinking`
2. 모델 피커에서 "GPT-5 Thinking" 선택
3. 폴링 정책: 15초 간격, 최대 2분
4. 완료 표시: 일반 응답 완료 신호와 동일

### `standard`

1. URL: `https://chatgpt.com/?model=gpt-5`
2. 모델 피커에서 "GPT-5" 선택
3. 폴링 정책: 5초 간격, 최대 30초
4. 완료 표시: 일반 응답 완료 신호와 동일

## 응답 추출 절차

1. 가장 최근 `div[data-message-author-role="assistant"]` 노드 선택
2. 내부 모든 코드블록 + 텍스트를 markdown으로 변환 (가능하면 "Copy" 버튼이 제공하는 raw 텍스트 사용)
3. Deep Research의 경우 "Read sources" 토글을 펼친 후 인용 목록도 함께 수확

## 폴백 동작

모드별 URL이 동작하지 않으면 (모델 ID 변경 가능성):
1. 기본 URL로 진입 후 모델 피커 사용
2. 그래도 실패 시 raw URL을 사용자에게 보여주고 수동 진입 요청

## 셀렉터 업데이트 절차

1. 사용자가 reviewer-bridge 실패를 보고하면 이 파일 열기
2. 브라우저 개발자 도구로 새 셀렉터 확인
3. 해당 항목 갱신, 다음 호출에서 자동 반영
