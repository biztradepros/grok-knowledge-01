# S4. 주간 종합 인사이트 (대표용)

- 주기: 매주 월 07:30
- 목적: 쌓인 데이터에서 패턴을 뽑아 상품·영업 아이디어로 연결. 팀이 "강해지는" 장치다.
- 모델: Opus 5.5 (`claude-opus-5-5`). 주 1회라 가장 좋은 모델을 쓴다.

| # | 모듈 | 설정 / 매핑 |
|---|---|---|
| 1 | Google Sheets › Search Rows + Text aggregator | PROFILE_TEXT |
| 2 | Google Sheets › Search Rows | `items`, `collected_at` 이 지난 7일 |
| 3 | Tools › Text aggregator | `item_id | client_id | score | action | title` 한 줄씩 |
| 4 | Anthropic Claude › Create a Prompt | `../prompts/weekly-insight.md`, max tokens 2000 |
| 5 | Google Drive › Upload a file | `주간메모/YYYY-MM-DD_주간인사이트.md` |
| 6 | Gmail › Send an email | 대표에게 (내부용이라 자동 발송 OK) |

활용: 이 메모를 클로드 코드 리서치 팀 폴더 `분석/` 에도 내려받아 두면,
"지난 4주 주간 메모 보고 새 상품 아이디어 3개 내 줘" 같은 깊은 작업을 클로드 코드에서 이어 할 수 있다.
