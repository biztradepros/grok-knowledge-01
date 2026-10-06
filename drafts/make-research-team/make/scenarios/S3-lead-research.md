# S3. 바이어·리드 리서치 (행 추가 시 실행)

- 트리거: Google Sheets › Watch Rows — `leads` 탭 (열: lead_id, company, country, website, our_product, status, 결과 열들)
- 목적: 회사 이름과 웹사이트만 넣으면 개요·필요 추정·첫 메일 초안이 같은 행에 채워진다.
- 모델: Sonnet 5.5

| # | 모듈 | 설정 / 매핑 |
|---|---|---|
| 1 | Google Sheets › Watch Rows | `leads`, `status` 가 비어 있는 새 행 |
| 2 | Google Sheets › Search Rows + Text aggregator | PROFILE_TEXT |
| 3 | HTTP › Make a request | GET `{{1.website}}`. 실패 시 status = `site_error` 기록 후 종료 |
| 4 | Text parser › HTML to text | 본문만 추출, 앞 8000자 |
| 5 | Anthropic Claude › Create a Prompt | `../prompts/lead-research.md` |
| 6 | JSON › Parse JSON | lead-research 출력 구조 |
| 7 | Google Sheets › Update a Row | 결과 열 채움, status = `researched` |
| 8 | Filter → Gmail › Create a draft | `fit_score ≥ 70` 이면 첫 메일 초안을 Gmail 초안으로 생성 (자동 발송 금지) |

지킬 것
- 웹사이트 한 곳만 읽는다. 다른 사이트를 대량으로 긁지 않는다.
- 개인 연락처는 저장하지 않는다. 회사 대표 채널만.
- 고객 납품용이면 클로드 코드 리서치 팀에서 fact-checker로 한 번 더 검증한 뒤 보낸다.
