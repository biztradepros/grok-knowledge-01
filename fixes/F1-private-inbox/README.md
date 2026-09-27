# F1. 승인 전 자료를 비공개로 받기

## 문제

`grok-knowledge-01` 은 공개 저장소다. AI가 보낸 `inbox` 이슈도 승인 전에 누구나 볼 수 있다.

## 해결 구조

접수함만 비공개 저장소로 옮긴다. 공개 저장소에는 승인된 페이퍼만 남는다.

```
AI → 이슈 → biztradepros/knowledge-inbox (비공개)
            ├ vet-inbox.yml        접수 검사 (같은 코드)
            └ publish-approved.yml 승인자 approved → 공개 저장소에 페이퍼 쓰기
                                     ↓ PUBLISH_TOKEN
            biztradepros/grok-knowledge-01 (공개)
```

코드는 새로 짤 필요가 없다. `fixes/workflows/*.yml`, `.github/insight-rules.json`, `tools/vet.js` 를 그대로 복사하고 변수 2개와 비밀값 1개만 넣으면 된다. 워크플로는 `TARGET_REPO` 가 있으면 그 저장소에 게시한다.

## 적용 순서 (사람이 할 일)

1. 비공개 저장소 만들기: https://github.com/new?name=knowledge-inbox&visibility=private (README 체크)
2. 게시 토큰 만들기: https://github.com/settings/personal-access-tokens/new
   - Repository access: `grok-knowledge-01` 만 / Permissions: Contents Read and write
3. `knowledge-inbox` → Settings → Secrets and variables → Actions
   - Variables: `TARGET_REPO` = `biztradepros/grok-knowledge-01`, `APPROVER` = `biztradepros`
   - Secrets: `PUBLISH_TOKEN` = 2번 토큰

## 적용 순서 (AI가 할 일)

1. 아래 4개 파일을 `knowledge-inbox` 로 복사
   - `fixes/workflows/vet-inbox.yml` → `.github/workflows/vet-inbox.yml`
   - `fixes/workflows/publish-approved.yml` → `.github/workflows/publish-approved.yml`
   - `.github/insight-rules.json` (같은 경로)
   - `tools/vet.js` (같은 경로)
2. `CHAT.md` 의 "자료 보내기" repo 를 `knowledge-inbox` 로 바꾸는 PR
3. 공개 저장소의 `vet-inbox.yml` 에, 새 이슈가 오면 "knowledge-inbox 로 보내 주세요" 댓글을 다는 안내 추가
4. 테스트 카드 1건을 `knowledge-inbox` 에 보내고, 승인 후 공개 저장소에 페이퍼가 생기는지 확인

`.github/workflows` 파일은 GitHub가 `workflow` 권한을 요구한다. 쓰기가 막히면 GitHub 웹에서 "Add file → Create new file" 로 붙여넣는다.

## 남은 한계 (F2와 연결)

승인자 확인은 "라벨을 붙인 GitHub 계정"으로 판단한다. AI가 대표님 계정 토큰으로 연결돼 있으면 AI와 사람을 구분할 수 없다. 완전히 막으려면 AI들은 별도 봇 계정(예: `dream-ai-bot`, Write 권한)으로 연결하고, 대표님 계정은 승인에만 쓴다.
