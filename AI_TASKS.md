# AI 작업판

이 저장소는 여러 AI(Claude, GPT, Grok, Gemini 등)가 같이 고친다. 작업은 GitHub 이슈의 `ai-task` 라벨로 관리한다.

## 작업을 맡는 법

1. `ai-task` 라벨이 붙은 열린 이슈를 고른다: https://github.com/biztradepros/grok-knowledge-01/issues?q=is%3Aopen+label%3Aai-task
2. 이슈에 "맡습니다 — <AI 이름>" 댓글을 단다. 이미 누가 맡았으면 다른 이슈를 고른다.
3. `<ai이름>/<이슈번호>-<짧은설명>` 브랜치를 만든다. main 에 직접 쓰지 않는다.
4. 고친 뒤 PR 을 연다. 본문에 `Closes #<이슈번호>`, 무엇을 바꿨는지, 어떻게 확인했는지 적는다.
5. 코드를 바꿨으면 테스트를 돌린다: `node test/vet.test.js` 와 `node test/workflows.test.js` (외부 라이브러리 없음). 돌릴 수 없는 환경이면 PR에 "테스트 못 돌림"이라고 쓴다.
6. 작업이 끝나면 `devlog/YYYY-MM-DD-<ai이름>.md` 에 소감을 남긴다 (아래 양식).

## 지켜야 할 것

- `approved` 라벨은 사람만 붙인다. AI는 붙이지도 떼지도 않는다.
- PR 은 사람이 Merge 한다. AI는 자기 PR 을 Merge 하지 않는다.
- 단가·마진·거래처·연락처·비밀키는 어떤 파일에도 쓰지 않는다. 이 저장소는 공개다.
- 규칙 단어·패턴을 늘릴 때는 `.github/insight-rules.json` 만 고치고, 테스트에 한 줄 추가한다.

## 코드 지도

| 파일 | 하는 일 |
| --- | --- |
| `tools/vet.js` | 카드 파싱, 형식·민감정보 검사, 마크다운 변환 (두 워크플로 공통) |
| `.github/insight-rules.json` | 금지어·정규식·필수 항목 |
| `fixes/workflows/vet-inbox.yml` | 접수 검사 v2 → `.github/workflows/` 로 옮겨야 동작 |
| `fixes/workflows/publish-approved.yml` | 승인자 확인 → 페이퍼 생성, 목록·llms.txt 갱신 → `.github/workflows/` 로 옮겨야 동작 |
| `fixes/F1-private-inbox/` | 비공개 접수함으로 옮기는 방법 |
| `test/` | 로컬 테스트 (모의 GitHub) |
| `devlog/` | AI별 작업 소감 |

`fixes/workflows` 에 있는 이유: `.github/workflows` 에 쓰려면 GitHub `workflow` 권한이 필요한데, Claude(Zapier 연결)에는 그 권한이 없었다. 권한이 있는 AI 또는 사람이 옮긴다.

## 소감 양식 (devlog)

```
# YYYY-MM-DD <AI 이름> 작업 소감
- 한 일:
- 확인한 방법:
- 막힌 점:
- 다음 AI에게:
```
