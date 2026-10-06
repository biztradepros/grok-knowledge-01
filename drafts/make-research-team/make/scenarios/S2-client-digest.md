# S2. 고객별 다이제스트 발송

- 주기: 고객 `digest_cycle` 에 따라 매일 08:00 또는 매주 월 08:00
- 목적: `items` 중 `action = 다이제스트|즉시 알림`, `status = new` 인 항목을 고객별로 묶어 보낸다.
- 모델: Sonnet 5.5 (`claude-sonnet-5-5`). 고객이 읽는 글이라 문장 품질이 중요하다.

| # | 모듈 | 설정 / 매핑 |
|---|---|---|
| 1 | Google Sheets › Search Rows | `profile` → Text aggregator로 PROFILE_TEXT |
| 2 | Google Sheets › Search Rows | `clients`, `active = TRUE`, 오늘이 발송일인 고객 |
| 3 | Google Sheets › Search Rows | `items`, `client_id = {{2.client_id}}`, `status = new`, `action ≠ 버림`, 점수 내림차순 상위 10 |
| 4 | Filter | 3의 결과 1건 이상 |
| 5 | Tools › Text aggregator | 행마다 `- [{{score}}] {{title}} / 마감 {{deadline}} / {{fit_reason}} / {{url}}` |
| 6 | Anthropic Claude › Create a Prompt | System = PROFILE_TEXT + 리서치 팀 CLAUDE.md의 "리포트 형식" 부분. User = 고객 정보 + 5의 목록. "목록에 없는 항목을 만들지 말 것, 모든 항목에 링크 유지" 명시 |
| 7 | Gmail › Create a draft (처음엔 draft!) | 받는 사람 = `{{2.email}}`. 대표가 확인 후 발송. 4주간 문제없으면 Send an email로 바꾼다 |
| 8 | Google Sheets › Update a Row (반복) | 보낸 item의 status = `sent` |
| 9 | Google Sheets › Add a Row | `reports` 탭 기록 |

메모: 7번을 처음부터 자동 발송으로 두지 않는다. 사람 검토 기간이 곧 프롬프트 학습 기간이다.
