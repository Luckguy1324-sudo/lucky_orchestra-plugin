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

### 폴링 정책 개요 (v0.2.1+)

3-페이즈 상태 머신:

| Phase | 의미 | 타임아웃 |
|-------|------|---------|
| WAITING_FOR_START | Submit 후 "생성 중" 신호 대기 | 모드별 START_TIMEOUT |
| **GENERATING** | "Stop streaming" 버튼 visible — 모델 작업 중 | **무제한** |
| EXTRACTING | 생성 멈춤, 텍스트 안정화 대기 | 모드별 EXTRACT_TIMEOUT |

ChatGPT가 응답을 만드는 시간(GENERATING)에는 타임아웃이 없습니다.
타임아웃은 "submit이 실패한 것 같다(WAITING)" / "텍스트가 안 떠오른다(EXTRACTING)" 같은 자동화 측 오류만 감지합니다.

추가 오류 감지: sign-in 페이지 출현, error/rate-limit 배너, 페이지 crash → 즉시 실패.

### `deep-research`

1. URL 직접 진입: `https://chatgpt.com/?model=deep-research`
2. 또는 모델 피커에서 "Pro Deep Research" 항목 클릭 (`role="menuitem"`, text contains "Deep Research")
3. 선택 후 입력창 상단에 "Deep research" 라벨 표시 확인
4. 폴링 예산: `POLL_INTERVAL=30s`, `START_TIMEOUT=180s`, `EXTRACT_TIMEOUT=600s`
5. 완료 표시: "Stop streaming" 버튼 사라짐 + 응답 카드 상단에 "Research complete" 또는 "Read sources" 토글

### `pro-reasoning`

1. URL: `https://chatgpt.com/?model=gpt-5-pro`
2. 모델 피커에서 "GPT-5 Pro" 선택
3. 추론 강도 토글: 입력창 좌측 옵션 메뉴 → "Reasoning effort" → "Extended" 또는 "Max"
4. 폴링 예산: `POLL_INTERVAL=15s`, `START_TIMEOUT=60s`, `EXTRACT_TIMEOUT=120s`
5. 완료 표시: 일반 응답 완료 신호 (stop button 사라짐 + 텍스트 안정화)

### `thinking`

1. URL: `https://chatgpt.com/?model=gpt-5-thinking`
2. 모델 피커에서 "GPT-5 Thinking" 선택
3. 폴링 예산: `POLL_INTERVAL=10s`, `START_TIMEOUT=30s`, `EXTRACT_TIMEOUT=60s`
4. 완료 표시: 일반 응답 완료 신호

### `standard`

1. URL: `https://chatgpt.com/?model=gpt-5`
2. 모델 피커에서 "GPT-5" 선택
3. 폴링 예산: `POLL_INTERVAL=5s`, `START_TIMEOUT=15s`, `EXTRACT_TIMEOUT=30s`
4. 완료 표시: 일반 응답 완료 신호

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
