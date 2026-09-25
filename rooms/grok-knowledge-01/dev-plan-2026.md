---
id: plan-2026-01
room: grok-knowledge-01
title: 있는 사례 위에 올리는 개발 계획
status: approved
source_ai: grok
approved_at: 2026-09-25
sensitivity: none
---

# 있는 사례 위에 올리는 개발 계획

공개 원본은 GitHub 마크다운으로 둔다. 대기열은 GitHub 이슈로 둔다. 서버형 데이터베이스와 자동 게시 도구는 지금 도입하지 않는다.

## 다른 AI가 먼저 읽을 결정

결정. 공개 원본은 biztradepros/grok-knowledge-01 의 마크다운과 llms.txt 다.

결정. 접수 대기열은 라벨 inbox 인 GitHub 이슈다. approved 는 사람만 붙인다.

결정. Sanity, Contentful, Tina Cloud, Strapi, Payload, Supabase 는 지금 설치하지 않는다.

결정. SocialFlow 처럼 소셜에 자동으로 올리는 저장소는 가져오지 않는다.

결정. 새 코드는 같은 실수가 두 번 나온 뒤에만 붙이고, 기존 사례와의 차이만 만든다.

English abstract. Keep the public canon as GitHub markdown. Keep the queue as GitHub issues. Do not add a hosted content database or an auto-posting engine now. Copy only the missing difference from an existing project, and only after the same mistake happens twice.

## GitHub에 있는 실제 사례

1. rokuosan/github-issue-cms. 이슈를 마크다운 글로 바꾼다. 나중에 쓸 수 있는 가장 가까운 배관이다. 그 도구는 이슈가 닫힐 때 글을 만든다. 우리는 approved 라벨일 때만 만들어야 한다. https://github.com/rokuosan/github-issue-cms
2. decaporg/decap-cms. 깃 위의 편집기다. 초안은 풀 리퀘스트이고 승인은 병합이다. 사람이 브라우저에서 글을 고칠 때 맞다. 지금 작성자는 AI이므로 설치하지 않는다. https://github.com/decaporg/decap-cms
3. yanhua1010/self-media-content-workflow. 브리프, 전략, 초안, 게시 사이에 사람 승인이 여러 번 있다. 게이트의 모양만 빌린다. 코드 전체를 가져오지 않는다. https://github.com/yanhua1010/self-media-content-workflow
4. inbharatai/SocialFlow. 정찰, 기획, 생성, 검수, 게시, 분석으로 나뉜다. 게시까지 자동이다. 가져오지 않는다. https://github.com/inbharatai/SocialFlow
5. intelligent-iterations/ii-content-engine. 사람이 승인한 뒤 예약을 건다. 게시 자동화는 90일 운영 뒤에만 다시 본다. https://github.com/intelligent-iterations/ii-content-engine
6. Blume. 마크다운 폴더를 사이트로 만들고 llms.txt 를 낸다. 다른 AI는 이미 raw 주소를 읽으므로 사이트를 새로 만들지 않는다. https://www.infoq.com/news/2026/09/blume-docs-ai/

가상 인플루언서의 교육, 섭외, 생성 부서를 그대로 제공하는 저장소는 찾지 못했다. 그 규칙은 가상 인플루언서 전략 페이퍼에 있고, 이 계획서는 그 규칙을 어느 소프트웨어 위에 얹을지만 정한다.

## 서버에 데이터베이스가 있는 서비스

1. Sanity. 호스팅된 문서 데이터베이스다. 에디터가 여러 명일 때 맞다. 공개 비교에서는 Growth 가 좌석당 월 15달러로 적혀 있다. 지금 도입하지 않는다.
2. Contentful. 호스팅 CMS 다. 같은 비교에서 Team 이 월 300달러대로 올라간다. 지금 규모보다 비싸다.
3. Tina Cloud. 깃 기반에 유료 편집 흐름이 있다. 비교 글은 Team Plus 를 월 49달러부터로 적는다. 챗 명령과 역할이 겹친다.
4. Strapi 와 Payload. 직접 서버를 띄우는 오픈소스 CMS 다. 서버 운영이 우리 일이 된다. 하지 않는다.
5. Supabase. Postgres 호스팅이다. 초안, 단가, 일정이 이슈로 부족해지면 비공개 층의 후보다. 공개 원본을 대체하지 않는다.
6. Notion. 이미 연결할 수 있는 문서 데이터베이스다. 사람용 비공개 메모로는 쓸 수 있다. 다른 AI가 외우는 공개 주소는 아니다.

가격은 2026년 공개 비교 글의 숫자다. 견적이 아니다. 돈을 내기 전에 그 서비스의 현재 가격 페이지를 다시 읽는다.

## 개발 방향

공개 층은 GitHub 에 둔다. 다른 AI가 외우는 주소가 바뀌면 창고가 깨진다.

비공개 층은 GitHub 이슈에 둔다. 단가, 마진, 버린 초안은 파일로 커밋하지 않는다.

서버형 데이터베이스는 이슈가 검색과 권한으로 부족해진 뒤에만 비공개 층으로 붙인다. 공개 층은 옮기지 않는다.

교육, 섭외, 생성 봇은 새 앱을 만들지 않고 이 방의 승인 페이퍼만 읽는다. 빈 서명이나 초대받지 않은 협업이면 생성을 멈춘다.

## 단계

1. 지금. 승인본은 가상 인플루언서 전략과 이 계획서뿐이다. CMS, 문서 사이트, 자동 게시는 설치하지 않는다.
2. 90일. 세 봇은 이 두 페이퍼만 읽고 결과는 inbox 이슈로만 보낸다. 새 플랫폼을 만들지 않는다. 주 4편과 초대 또는 거절만 남긴다.
3. 같은 실수가 두 번이면. approved 이슈를 마크다운 파일로 복사하는 동작만 github-issue-cms 의 모양으로 붙인다. 조건은 이슈가 닫힌 것이 아니라 approved 라벨이다.
4. 두 번째 캐릭터가 같은 방을 쓸 때. 비공개 초안만 Supabase 또는 Notion 으로 옮기는 안을 다시 연다. 공개 주소는 GitHub raw 로 남긴다.

## 다른 AI의 실행 규칙

이 계획서를 읽고 개발을 시작하지 마라.

사용자가 단계 번호를 말하기 전에는 저장소를 설치하거나 서버를 만들지 마라.

제안을 쓸 때는 위의 사례 중 하나를 고르고, grok-knowledge-01 에 없는 차이만 적어라.

자동 게시, 단가 공개, approved 를 스스로 붙이는 일은 거절해라.

원문 경로는 rooms/grok-knowledge-01/dev-plan-2026.md 이고 id 는 plan-2026-01 이다.
