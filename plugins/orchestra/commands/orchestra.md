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
---

# /orchestra Command

Claude Code Opus 4.7이 지휘자(Conductor)가 되어 본인(Performer ×N)과 ChatGPT Pro Deep Research(Reviewer)를 조율해 하나의 결과물을 만들어내는 6단계 워크플로.

## Workflow Summary

```
1. Brief         — 사용자 의도 명확화 (AskUserQuestion)
  1.5. Model     — Stage 2/5 ChatGPT 모드 추천 + 사용자 확정
2. Plan Research — ChatGPT가 리서치 어젠다 설계 (브라우저)
3. Research      — Performer ×N 병렬 리서치 (Task 서브에이전트)
4. Synthesize    — Conductor가 통합본 작성
5. Review        — ChatGPT가 통합본 심층 검토 (브라우저)
6. Decide        — PASS/REVISE/RESTART 분기, 임계치 통과까지 반복
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

## Notes

- 최초 실행 시 `open-gstack-browser`로 ChatGPT 로그인이 필요할 수 있다 (1회).
- 라운드 수와 ChatGPT 모드는 Stage 1.5에서 결정된다.
- 중단된 run은 `<cwd>/.orchestra/runs/<run-id>/meta.json`을 보고 이어서 진행 가능.
