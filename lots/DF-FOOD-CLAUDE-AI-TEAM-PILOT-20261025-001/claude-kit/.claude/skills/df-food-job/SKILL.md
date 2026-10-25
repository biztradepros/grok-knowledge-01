---
name: df-food-job
description: DREAM FACTORIES 식품 수입·광고대행 JOB 1회 실행 절차. JOB_ID와 상품명을 받으면 조사→전략→검증→Drive 저장→재조회→n8n 인계까지 수행한다. 게시·결제·발송은 하지 않는다.
---
# DF FOOD JOB

입력: JOB_ID, 상품명, Drive 부모 폴더 ID (기본 1rnrIzWEZVI6JJTlVp1arCWLAXl4Bl330).

1. Drive에서 JOB_ID 폴더를 검색한다. 있으면 재사용, 없으면 만든다 (중복 금지).
2. `df-import-food-intel` 서브에이전트 → MARKET_RESEARCH.md, SOURCE_REGISTRY.json.
3. `df-ad-strategy` 서브에이전트 → AD_STRATEGY.md, VIDEO_SCRIPTS.md, CARD_NEWS_PLAN.md, LANDING_PLAN.md.
4. `df-quality-rights-auditor` 서브에이전트 → QUALITY_AUDIT.md.
5. 팀장(메인 세션)이 8개 파일을 Drive에 저장한다 (text/markdown, application/json, 변환 끔).
6. 파일마다 get_file_metadata 와 download/read 로 독립 재조회하고 결과를 EXECUTION_EVIDENCE.json 에 적는다.
7. n8n `DF FOOD CLAUDE TEAM R03 RESULT INTAKE STAGING` (ODHAK1s10mByNdtx) 에 manifest를 webhookData.body 로 넣어 manual 실행하고 STATUS를 회수한다.

금지: 광고 게시, Postiz 예약, 결제, 외부 고객 발송, GOLDEN 워크플로 수정, 비밀키 출력.
