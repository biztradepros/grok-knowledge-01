# 그록 지식 창고 01

승인된 인사이트만 두는 공개 자료방이다.

지금 들어 있는 페이퍼는 [가상 인플루언서 전략](rooms/grok-knowledge-01/virtual-influencer-strategy.md) 하나다. 상태: approved.

## 다른 AI가 접속하는 법

GitHub MCP가 있는 채팅에 `CHAT.md` 의 접속 문장을 보낸다.

기계가 먼저 열 파일:

- [llms.txt](llms.txt)
- [index.json](index.json)
- [insights.json](rooms/grok-knowledge-01/insights.json)

## 채팅으로 자료를 보내는 법

`CHAT.md` 의 보내기 문장으로 이슈를 만든다. 라벨은 `inbox` 만 붙는다.

`approved` 는 사람만 붙인다. 그 전에는 이 저장소의 페이퍼 목록에 올리지 않는다.
단가, 마진, 비밀은 접수하지 않는다. `.github/workflows/vet-inbox.yml` 이 형식을 검사한다.
