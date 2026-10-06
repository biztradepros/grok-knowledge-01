# S1. 공고 레이더: 수집 → 중복 제거 → 고객별 채점

- 주기: 매일 07:00 (Schedule)
- 목적: 새 공고를 모아 고객마다 점수를 매겨 `items` 탭에 쌓는다. 급한 건은 바로 알린다.
- 모델: Haiku 4.5 (`claude-haiku-4-5-20251001`). 건수가 많아 싼 모델로 거른다.

## 준비물
- Google Sheets: `profile`, `clients`, `sources`, `items` 탭 (`../sheets/*.csv` 헤더)
- Make Data store `seen_items` — 키: item_id (원문 URL의 해시나 URL 자체)
- Connections: Google, Anthropic Claude, Gmail(또는 Slack)

## 모듈 순서

| # | 모듈 | 설정 / 매핑 |
|---|---|---|
| 1 | Google Sheets › Search Rows | `profile` 탭 전체 |
| 2 | Tools › Text aggregator | 1의 행을 `{{key}}: {{value}}` 줄로 합침 → **PROFILE_TEXT** |
| 3 | Google Sheets › Search Rows | `sources` 탭, 필터 `active = TRUE` |
| 4 | Router | 경로 A: `type = rss` / 경로 B: `type = api` |
| 4A | RSS › Retrieve RSS feed items | URL = `{{3.url}}`, 최대 30건 |
| 4B | HTTP › Make a request → JSON › Parse JSON | 공공데이터 API. 응답 배열을 Iterator로 풀기 |
| 5 | Data store › Get a record | `seen_items`, key = 원문 URL |
| 6 | Filter | 5의 결과가 **없을 때만** 통과 (새 공고만) |
| 7 | Filter | 제목/본문에 전체 고객 `keywords_exclude` 가 있으면 버림 (비용 절감용 1차 거르기) |
| 8 | Data store › Add a record | `seen_items` 에 URL 저장 (재처리 방지) |
| 9 | Google Sheets › Search Rows | `clients` 탭, `active = TRUE` → 고객 수만큼 반복 |
| 10 | Filter | 고객의 `keywords_include` 중 하나라도 제목/본문에 있으면 통과 (없으면 Claude 호출 생략) |
| 11 | Anthropic Claude › Create a Prompt (또는 HTTP로 Messages API) | model = Haiku 4.5, max tokens 600, System = PROFILE_TEXT + `../prompts/score-item.md` System, User = 같은 파일 User |
| 12 | JSON › Parse JSON | 구조 = `../schemas/score-item.schema.json` |
| 13 | Google Sheets › Add a Row | `items` 탭. score, fit_reason, eligibility, deadline, summary, action, model 매핑. status = `new` |
| 14 | Filter | `action = 즉시 알림` |
| 15 | Gmail › Send an email (또는 Slack) | 받는 사람 = 대표(검토 후 고객 전달). 제목 `[즉시] {{title}} — {{client_name}} {{score}}점`. 본문에 **원문 URL 필수** |

## 오류 처리
- 11번에 Error handler › Break (재시도 3회, 간격 1분). 과부하 응답일 때 다음 실행에서 재처리되도록 8번을 11 뒤로 옮겨도 된다.
- 12번 Parse 실패 시 Resume으로 `items` 에 status = `parse_error`, summary = 원문 응답 앞 200자 기록.

## 비용 줄이는 장치 (중요)
- 6·7·10번 필터가 Claude 호출 수를 결정한다. 키워드를 다듬을수록 싸진다.
- 본문은 앞 4000자만 보낸다.
- 처음 2주는 고객 1명(나 자신)으로만 돌려 작업 수를 확인한다.
