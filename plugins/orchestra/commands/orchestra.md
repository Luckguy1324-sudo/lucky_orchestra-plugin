---
name: orchestra
description: "Multi-AI 협업 오케스트레이션 — Claude 지휘자가 Performer(Claude)와 Reviewer(ChatGPT)를 조율해 산출물을 도출"
argument-hint: "[목표 한 문장]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - Task
  - WebFetch
  - WebSearch
  - Skill
---

# /orchestra Command

Claude Code Opus 4.8이 지휘자(Conductor)가 되어 본인(Performer ×N)과 ChatGPT Pro Deep Research(Reviewer)를 조율해 하나의 결과물을 만들어내는 6단계 워크플로.

## Workflow Summary

```
1. Brief         — 사용자 의도 명확화 (AskUserQuestion) + acceptance criteria → meta.json
  1.5. Model     — Stage 2/5 ChatGPT 모드 추천 + 사용자 확정
2. Plan Research — ChatGPT가 리서치 어젠다 설계 (브라우저)
3. Research      — Performer ×N 병렬 리서치 (Task 서브에이전트)
4. Synthesize    — Conductor가 통합본 작성 (REVISE 라운드에선 must_fix[] 주입)
  4.5. Pre-Gate  — scripts/pre_gate.sh로 결정론적 사전 검증 (⑧). FAIL이면 수정 후 재실행, PASS 전엔 리뷰 금지
5. Review        — 강화된 교차검증 4패스: blind 스코어링(①) → persona 패스(③) → claim→근거 웹 감사(④) → kill-argument(⑦). 원문 trace 보존(⑤), CRITICAL→MINOR 정렬(②)
6. Decide        — scripts/score_gate.py로 PASS/REVISE/RESTART 판정(⑥), 임계치 통과까지 반복
```

## Parse Arguments

`$ARGUMENTS`로 받은 목표 문장을 그대로 Stage 1 인터뷰에 전달한다. 인수가 없으면 Brief 인터뷰부터 시작.

## Execute

**필수 절차:**

1. `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/skills/orchestra/SKILL.md`를 Read로 읽는다.
2. 거기 명시된 6단계 워크플로를 그대로 실행한다.
3. 각 단계의 산출물은 `<cwd>/.orchestra/runs/<run-id>/` 하위에 저장한다.
4. 단계 종료마다 사용자에게 진행 상황을 1-2줄 보고한다.

**스킬 파일은 참고문서가 아니라 실행 지시서다. 읽은 후 그대로 따른다.**

## Hardened Verification (①–⑧)

교차검증은 8개 메커니즘으로 강화되어 있으며, 자동화 여부와 무관하게(MANUAL 모드 포함) 동일하게 동작한다:
reviewer-bias guard·blind 스코어링(①), severity 태깅 정렬(②), anti-groupthink 페르소나(③),
claim→근거 웹 검증(④), forensic raw trace 보존(⑤), acquit-gate 분리(⑥),
kill-argument 적대 검토(⑦), deterministic pre-gate(⑧).
점수를 임의로 만들거나 게이트를 무시하지 않는다. 표준 조항은 웹 확인 없이 단정하지 않는다(④).
매 라운드 blind 스코어링은 항상 새 ChatGPT 창에서 수행한다(①).

## Notes

- 최초 실행 시 `open-gstack-browser`로 ChatGPT 로그인이 필요할 수 있다 (1회). 자동화 없이도 MANUAL 모드로 항상 실행 가능.
- 라운드 수와 ChatGPT 모드는 Stage 1.5에서 결정된다.
- 중단된 run은 `<cwd>/.orchestra/runs/<run-id>/meta.json`을 보고 이어서 진행 가능.
