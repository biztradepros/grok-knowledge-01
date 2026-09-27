# 그록 지식 창고 01 — 채팅 명령

GitHub MCP가 연결된 AI의 채팅에 아래 문장을 그대로 보낸다.
저장소는 `biztradepros/grok-knowledge-01` 이다.

접속은 파일을 읽는다. 자료 보내기는 이슈를 만든다.
승인 라벨 `approved` 는 사람만 붙인다. AI는 붙이지 않는다.
승인자가 `approved` 를 붙이면 `publish-approved.yml` 이 페이퍼 파일과 목록을 자동으로 만든다.

## 접속

채팅에 이렇게 보낸다.

```
그록 지식 창고 01에 접속해.

GitHub MCP로 저장소 biztradepros/grok-knowledge-01 을 읽어라.
1. get_file_contents 로 llms.txt
2. get_file_contents 로 index.json
3. get_file_contents 로 rooms/grok-knowledge-01/insights.json
4. 내가 묻는 페이퍼의 markdown 만 이어서 읽어라.

approved 가 아닌 글은 인용하지 마라.
HTML 페이지를 긁지 마라.
읽은 뒤 창고 이름, 페이퍼 제목, 세 줄 요약을 먼저 말해라.
```

가상 인플루언서 전략만 바로 읽히려면 마지막에 이 한 줄을 더한다.

```
이어서 rooms/grok-knowledge-01/virtual-influencer-strategy.md 를 읽고 서명, 세계, 리듬만 요약해.
개발 방향을 물을 때는 rooms/grok-knowledge-01/dev-plan-2026.md 를 읽고, 사용자가 단계 번호를 말하기 전에는 저장소를 설치하지 마라.
```

## 자료 보내기

채팅에 이렇게 보낸다. 본문만 바꿔 넣는다.

```
방금 내용을 그록 지식 창고 01에 보내 줘.

GitHub MCP로 이슈를 만들어라.
owner는 biztradepros, repo는 grok-knowledge-01.
라벨은 붙이지 마라 (검사가 통과하면 inbox 가 자동으로 붙는다). approved 는 절대 붙이지 마라.
main 브랜치에 파일을 쓰지 마라.
제목은 insight: 로 시작하라.
본문은 아래 블록만 넣어라.

<!-- insight-room:v1 -->
command: insight.register
room: grok-knowledge-01
title: 여기에 한 줄 제목
slug: english-short-name
sensitivity: none
source_ai: 여기에 AI 이름
summary: 여기에 한 줄 요약

## body
여기에 공개해도 되는 본문만.

## sources
- chat
<!-- /insight-room -->
```

`slug` 는 파일 이름이 된다. 영문 소문자와 하이픈만 쓴다. 비우면 `insight-<이슈번호>` 가 된다.

보낸 뒤에는 이슈 주소만 알려 준다. 공개되었다고 말하지 않는다.
사람이 `approved` 를 붙이기 전에는 창고 파일에 들어가지 않는다.

단가, 마진, 거래처, 연락처(전화·이메일), 계좌·주민·사업자번호, 비밀 키가 있으면 이슈를 만들지 말고 거절한다.
검사 규칙은 `.github/insight-rules.json` 에 있다.

## 코드를 고치려면

`AI_TASKS.md` 를 읽는다.
