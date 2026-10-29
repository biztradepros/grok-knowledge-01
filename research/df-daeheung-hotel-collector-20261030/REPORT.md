# DF 대흥동 공사비 × 호텔 MCP 공통 수집기 — OSS 병렬 연구 완료 보고 R01

- JOB_ID: `DF-DAEHEUNG-HOTEL-COLLECTOR-OSS-20261030-001`
- 작성: Claude Code 원격 세션, 2026-10-29 (UTC 기준 실행), 작업지시서 R01 기준
- 입력: Drive 작업지시서 `1Br9aONnRMExKBhn_fCnPGf051uOjtu0uAC3yoBC8Bpc` (직접 읽음).
  GitHub 인수인계 파일(`dream-factories/dream-factory-control-center`, 브랜치 `gpt/notebook-handoff-review-20261030`)은 이 세션에 연결되지 않은 저장소라 읽지 못했다. 같은 제목의 Drive 문서를 기준으로 삼았다.
- 결정: **연구 완료. 새 앱 개발·배포는 보류. 최소 수집기 1개는 조건부로 제안한다(§7).**
- 이번 단계에서 하지 않은 일: Make·n8n·Drive·Notebook 자동화 재구축, 서비스 배포, 유료 API 신규 결제, 자격증명 수집, 대량 수집.

---

## 1. 결론 요약

| 항목 | 결론 |
|---|---|
| 웹 수집 경로 (Lane A) | **기존 Firecrawl MCP 커넥터를 그대로 쓴다.** 별도 설치·개발이 없다. 이 클라우드 컨테이너에서 접속이 막힌 한국 공공 사이트(daejeon.go.kr, mcst.go.kr, kind.krx.co.kr 등)도 Firecrawl은 원격에서 받아왔다. Crawl4AI는 로컬에서 실행이 확인됐지만 이 환경에서는 외부 접속이 차단돼 실사이트 수집에 실패했다. JS 다운로드 버튼, SVG 차트 같은 Firecrawl의 빈틈을 메우는 **보조 경로**로만 둔다. |
| 문서·표 추출 (Lane B) | **Docling(MIT) 채택.** 공식 KRX 공시 HTML 1건에서 계약표 33행을 18.6초에 구조화했다. 계약명 필드 4/33행이 빠지는 손실이 있어 검수 규칙이 필요하다. Docling MCP 3.4.0은 MCP Python SDK v2가 필요하다. PDF는 레이아웃 모델을 Hugging Face에서 받아야 하는데, 이 환경에서는 그 호스트가 차단돼 PDF 경로는 Firecrawl PDF 파서로 대신 검증했다. |
| 출처 수집 (Lane C) | 대흥동·인근 공사비 5건, 호텔 운영·수익 5건을 검증했다. 상세는 §5. 대흥동 사례 중 **연면적이 공개된 건이 0건**이라 ㎡당 공사비는 모두 `no-data`로 표기했다. 사업비를 건축비로 환산하지 않았다. |
| 예상 비용 | 소프트웨어 라이선스 0원. 이번 검증에 쓴 Firecrawl은 약 30 크레딧. 월 운영비는 §6. |
| 개발 필요 여부 | **지금은 불필요.** 에이전트 + Firecrawl MCP + JSON 스키마만으로 G1~G6 대부분을 충족한다. 첨부파일(XLSX/PDF)을 Docling으로 반복 처리해야 할 때에 한해 최소 수집기 1개(CLI, 약 200줄)를 제안한다. |
| 추천 조합 | **Firecrawl MCP(수집) + Docling(문서·표) + JSON 스키마·출처 규칙 + Google Drive 보고.** Crawl4AI는 보조, Browser Use와 Dify는 보류. |

---

## 2. OSS_MATRIX (G1: 저장소·커밋·라이선스 검증)

검증 방법: 각 저장소를 `git clone --depth 1`로 받아 HEAD 커밋과 LICENSE 파일을 직접 확인했고, PyPI JSON API로 최신 버전을 확인했다(2026-10-29).

| 도구 | 저장소 / HEAD 커밋 (커밋 시각) | 라이선스 (파일 확인) | 최신 패키지 | 역할 | 판정 |
|---|---|---|---|---|---|
| Firecrawl | github.com/firecrawl/firecrawl `33f295dc1f09` (2026-10-28) | **AGPL-3.0** (SDK·일부 UI는 MIT, README 명시) | firecrawl-py 4.54.0 (MIT) | 웹·PDF 수집, 검색 | **채택 (기존 MCP 커넥터 재사용)** |
| Crawl4AI | github.com/unclecode/crawl4ai `888299fb5f0b` (2026-10-26) | **Apache-2.0** | crawl4ai 0.9.5 (2026-10-14) | 브라우저 기반 크롤링, 셀프호스트 | 보조 (JS·첨부 대응용) |
| Docling | github.com/docling-project/docling `af2dbadb4cd3` (2026-10-29) | **MIT** | docling 2.145.0 (2026-10-29) | PDF·XLSX·DOCX·HTML 구조화 | **채택** |
| Docling MCP | github.com/docling-project/docling-mcp `463e6b429ebc` (2026-10-27) | **MIT** | docling-mcp **3.4.0** (2026-10-27) | Docling을 MCP 도구로 노출 | 조건부 채택 (클라이언트 SDK v2 확인 후) |
| Browser Use | — (이번 범위 밖) | — | — | 로그인·JS 위주 페이지 | 보류 (자격증명·LLM 비용이 걸린 경로) |
| Dify | — | — | — | 2단계 워크플로 UI | 보류 (2단계) |

주의: 작업지시서는 Docling MCP를 v3.3.0으로 적었지만, 현재 최신은 **3.4.0**(2026-10-27 배포)이다.

---

## 3. Lane A — Firecrawl MCP vs Crawl4AI

### 3.1 실측 결과 (G2: 기존 커넥터 재사용 증거)

| 시험 | Firecrawl MCP (기존 커넥터) | Crawl4AI 0.9.5 (이 컨테이너에 로컬 설치) |
|---|---|---|
| 대전시 공식 페이지 (daejeon.go.kr 대흥동 뉴빌리지) | **성공.** HTTP 200, 1 크레딧, 본문·작성일·담당부서·공공누리 1유형 표기까지 추출 | **실패.** `net::ERR_TUNNEL_CONNECTION_FAILED`. 이 환경의 네트워크 정책이 해당 호스트를 막음 |
| KRX KIND 공시 HTML (3.3MB) | **성공.** markdown 62만 자, 표 보존, 1 크레딧 | 같은 HTML을 `file://`로 넣으면 **성공**: 4.5초, 표 663개, 계약표 행 보존 |
| PDF (야놀자리서치 2025 2Q, 31쪽 중 4쪽) | **성공.** 표 9개 추출, 4 크레딧. 일부 차트 데이터는 `Series 1 (unlabelled)`로 나오고 행 라벨 오류 1건(`2024.02` → 실제 `2024.Q2`) | 이 환경에서는 시험 불가 |
| JS 다운로드 버튼 (문체부 첨부 XLSX, 호텔업협회 연도별 파일) | 링크가 `#`으로만 나와 **파일 URL을 확보하지 못함** | 브라우저 클릭 자동화로 해결 가능(설계상). 이 환경에서는 실사이트 접속 불가 |
| SVG 차트 수치 (신한서부티엔디리츠 OCC/ADR) | 이미지 링크만 추출되고 **수치는 없음** | SVG 원문을 받아 파싱하면 가능(별도 코드 필요) |
| 사이트 탐색·검색 | `firecrawl_search`로 한국어 검색 가능, 검색 1회 2 크레딧 | 자체 검색 없음. 호스티드 API의 `/search`는 유료 크레딧 |

### 3.2 결정

- **최저비용·최저개발 경로 = 기존 Firecrawl MCP.** 설치도 코드도 필요 없다. 원격 수집이라 이 환경의 접속 제한을 받지 않는다. 페이지당 1 크레딧, PDF는 쪽당 1 크레딧으로 관측됐다.
- **AGPL 영향:** Firecrawl을 SaaS·MCP로 쓰는 경우에는 우리 쪽 소스 공개 의무가 생기지 않는다. 셀프호스트한 Firecrawl을 수정해서 네트워크 서비스로 제공할 때에만 AGPL 공개 의무가 걸린다. 셀프호스트는 권하지 않는다.
- **Crawl4AI(Apache-2.0)는 보조로만 둔다.** 첨부 다운로드 버튼이나 SVG처럼 Firecrawl이 놓치는 경우에 쓴다. 실행하려면 한국 사이트로 나가는 접속이 열린 호스트가 있어야 한다.
- 시험 중 주의점: Crawl4AI 0.9.5는 Playwright 1.64.1을 함께 설치한다. 그래서 미리 설치된 Chromium(빌드 1243)과 버전이 어긋났고, 브라우저 경로를 이어 붙여(symlink) 해결했다. 실제 운영에서는 공식 Docker 이미지를 쓰는 편이 안전하다.

---

## 4. Lane B — Docling / Docling MCP

### 4.1 공개 샘플 시험 (G3)

- **샘플:** 효성중공업 사업보고서(2024.12) 정정신고, KRX KIND 공시 HTML (2025-08-14)
  - URL: https://kind.krx.co.kr/external/2025/08/14/002382/20250814007272/11011.htm
  - 수집 경로: Firecrawl `rawHtml`(1 크레딧) → 로컬 저장 → Docling `DocumentConverter`
  - 원본 SHA-256: `5cf56ce23bbc7211205bf9813f5cbef3c816cf7c70007f2ac5e4d5c3ef06bf19`
- **결과:** `ConversionStatus.SUCCESS`, 18.6초, 표 2,358개 / 텍스트 블록 1,668개를 인식했다. 3번째 표(“단일판매ㆍ공급계약체결 공시 진행사항”)는 33행 × 8열로 추출됐다.
- **대전 관련 행 (자동 필터):**

| 신고일자 | 계약내역 | 계약금액총액 (백만원) | 비고 |
|---|---|---|---|
| 2021-12-30 | 대전시 선화2구역 도시환경정비사업 | 284,575 | 이주 완료, 인허가 준비중 |
| 2023-11-03 | 대전 갑천역 APT 신축공사 | 124,365 | '28년 2월 준공 예정 |
| 2023-12-21 | 선화재정비촉진구역주택재개발정비사업 | 151,895 | '대전'이 없어 자동 필터에서 빠짐 → 지명 사전으로 보완 필요 |

- **필드 품질 감사 (G4):**
  - 셀 안에 줄바꿈(`<br>`)이 있는 계약명 **4/33행(12%)이 빈 값**으로 추출됐다. 예: 2022-05-04 남아공 BESS, 2022-09-07 에티오피아 전력망, 2023-09-19 GTX-C, 2024-11-04 건.
  - 2단 헤더 “판매ㆍ공급금액”이 사라지고 `당기/누적`만 남았다.
  - 대응 규칙: Docling 표와 Firecrawl markdown 표를 행 단위로 대조하고, 계약명이 빈 행은 `needs_review`로 표시한다.
- **설치 조건:** `docling-slim[format-html,format-xlsx,format-docx]`만 설치했다. torch 없이 HTML·XLSX·DOCX 경로가 동작했다. PDF 표준 파이프라인은 레이아웃·TableFormer 모델을 **huggingface.co에서 받아야 하는데, 이 환경에서는 그 호스트가 차단**돼 PDF 시험은 하지 못했다. PDF 표 추출은 §3.1의 Firecrawl PDF 시험으로 대신 검증했다.

### 4.2 MCP_CAPABILITY (Docling MCP 3.4.0, README 직접 확인)

| 항목 | 내용 |
|---|---|
| 호환성 | docling-mcp ≥3.0.0 은 `mcp>=2.0.0`(MCP Python SDK v2) 필요. 클라이언트가 v1이면 `docling-mcp<3.0.0`으로 고정 |
| 실행 | `uvx --from docling-mcp docling-mcp-server --transport stdio` (Claude Desktop/Code), streamable-http도 지원 |
| 변환 모드 | 기본 `remote` → `DOCLING_MCP_SERVICE_URL`(docling-serve) 필요, API 키는 선택. `local`은 `docling-mcp[local]`로 설치하며 torch와 모델이 필요 |
| 도구 | 변환(PDF·URL → DoclingDocument), 생성, 캐시, RAG(Milvus/LlamaIndex/LlamaStack) 선택 |
| 권장 | 처음에는 **로컬 stdio + local 모드**로 시작하고, 모델은 사전에 내려받아 캐시한다. 원격 docling-serve는 배포에 해당하므로 이번 단계에서 보류 |

### 4.3 문서 유형별 적합도

| 문서 | Docling 경로 | 비고 |
|---|---|---|
| 건축 견적서·내역서 XLSX | `format-xlsx`(openpyxl), 모델 불필요 | 병합셀·다단 헤더 검수 규칙 필요 |
| 공시·공고 HTML | HTML 백엔드, 모델 불필요 | **이번에 실측 성공** |
| 스캔 PDF·도면 내역 | PDF 파이프라인 + OCR(RapidOCR 등) + 모델 | 모델을 받을 수 있는 호스트가 필요 |
| 호텔 IR PDF·운영보고서 | PDF 파이프라인 또는 Firecrawl PDF 파서 | 차트 수치는 둘 다 불완전 → `no-data` 표기 |

---

## 5. Lane C — 출처 수집·검증 (각 5건)

판정 기준: **official** = 정부·지자체·거래소 공시·발행 기관 원문. **corroborated** = 원문은 못 받았지만 언론 2건 이상이 일치. **secondary** = 2차 정리 자료.
대흥동 건 중 연면적이 공개된 사례는 없어 `cost_per_m2`는 모두 `no-data`다. **사업비를 건축비로 환산하지 않았다.**

### 5.1 대흥동·인근 공사비 사례

| # | 사례 | original_url | source_date | project_kind / region | 규모 (층·GFA) | 금액·price_basis | VAT | cost_per_m2 | confidence |
|---|---|---|---|---|---|---|---|---|---|
| D1 | 대흥동 뉴빌리지 도시재생사업 | https://www.daejeon.go.kr/drh/drhStoryDaejeonView.do?boardId=blog_0001&categorySeq=292&menuSeq=1625&ntatcSeq=1486993891 | 2025-07-08 (대전시 도시재생과) | 도시재생(골목·CCTV·복합커뮤니티센터·주차장) / 중구 대흥동 309-11 일원, 구역 약 7.3만㎡ | 개별 건축물 규모 미공개 | **총사업비** 309억원 (국비 150, 지방비 150, 기타 8.89), 2025~2029 | 미표기 | **no-data** (구역 면적이라 건축비 환산 불가) | high (official, Firecrawl로 원문 확인, 공공누리 1유형) |
| D2 | 대흥4구역 주택재개발 (HJ중공업 수주 공시) | https://www.dnews.co.kr/uhtml/view.jsp?idxno=202407111110511860595 · https://www.businesspost.co.kr/BP?command=article_view&num=358574 · https://www.kmecnews.co.kr/news/articleView.html?idxno=35842 | 공시 2024-07-11 | 공동주택 재개발 / 중구 대흥동 260-9 일원 | 지하3~지상29층, 10개동, 909세대. GFA 미공개 | 계약금액 1,115억 7,571만원 = **HJ중공업 지분 45%분**. 공사기간 실착공 후 39개월 | **VAT 별도** (보도) | **no-data** | medium (corroborated 3건 일치. DART 원문 rcpNo는 확보하지 못함) |
| D3 | 대전 선화2구역 도시환경정비 / 선화재정비촉진구역 / 갑천역 APT (효성중공업 공시 진행표) | https://kind.krx.co.kr/external/2025/08/14/002382/20250814007272/11011.htm | 2025-08-14 (사업보고서 정정) | 정비·공동주택 / 대전 중구 선화동(대흥동 인접) 및 대전 | 미공개 | 계약금액총액(백만원): 284,575 / 151,895 / 124,365 | 표에 미표기 | **no-data** | high (official 공시. Docling으로 표 추출, §4.1) |
| D4 | 조달청 공사비 정보광장 “주요시설 유형별 단위당 공사비” (공공청사 2024년 약 352만원/㎡) | 2차: https://anbak4.com/entry/조달청-주요-시설-유형별-단위당-공사비 · 기관 보도: https://eiec.kdi.re.kr/policy/materialView.do?num=144338 | 2025-01 (2차 정리) | 공공건축 벤치마크 / 전국 | — | 단위면적당 공사비 (조달청 기준) | 기준 미확인 | 352만원/㎡ (**검증 대기**) | low (원문 나라장터 화면은 JS 기반이고 이 환경에서 접속 불가) |
| D5 | 한국건설기술연구원(KICT) 건설공사비지수 — 에스컬레이션 기준 | 보도: https://www.fnnews.com/news/202604281518290933 · 지수 원천: KICT 공사비원가관리센터 / KOSIS | 2026-04-28 보도 | 비용지수 / 전국 | — | 2026-05 지수 137.67 (전년동월 +5.1%), 2026-02 133.7 (+2.0%), 2차 인용 | — | 지수 (금액 아님) | medium (국토부 표준시장단가 보정에 쓰이는 공식 지수. 수치는 2차 인용이라 원문 대조 필요) |

**보류 후보:** SM그룹 대흥동 주상복합 (대흥동 38-17, 지하3~지상35층, 시공 경남기업). 언론 보도만 있고 계약금액 공시는 찾지 못했다. 경남기업 단일판매·공급계약 공시를 확인하면 D6로 올릴 수 있다.

**비용지수·에스컬레이션 분리:** D5는 지수로만 쓰고 D1~D3 금액에 섞지 않는다. 보정할 때는 `계약일 지수 → 기준일 지수` 비율만 별도 필드(`escalation_factor`)로 기록한다.

### 5.2 호텔 운영·수익 자료

| # | 자료 | original_url | 날짜 | region / property_type | room_count | ADR (구분) | OCC (구분) | RevPAR | mgmt fee / NOI / opex | comparability | confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | 한국호텔업협회 「호텔업운영현황」 (문체부 위탁, 2015~2024 연간) | http://www.hotelskorea.or.kr/datacenter/index_1.php?code=1 · 정의 출처: https://www.hotelrestaurant.co.kr/news/articleView.html?idxno=10192 | 페이지 2026-10-29 확인, 정의 기사 2022-02-10 | 전국·지역별 / 관광호텔(등급별)·가족·소형 등 | 협회 집계 | **실현 ADR** = 객실매출 ÷ 판매객실 (보고통계) | 실현 OCC | ADR×OCC | 인건비율 등 일부 | 높음 (표준 정의). 단, 제출업체가 해마다 달라 총량 비교는 금지 | high (official 위탁 통계). 연도별 파일은 JS 다운로드라 수치 미추출 |
| H2 | 문체부 「2025년 기준 관광숙박업 등록현황(수정)」 XLSX 2종 | https://www.mcst.go.kr/site/s_policy/dept/deptView.jsp?pSeq=2122&pDataCD=0417000000&pType=05 | 2026-03-31 | 전국·시도(대전 포함) / 호텔·휴양콘도 | 등록 객실수 (공급) | — | — | — | — | 공급측 기준선 | high (official). **공공누리 4유형: 상업적 이용·변경 금지** |
| H3 | 롯데관광개발 IR — 그랜드 하얏트 제주 1Q26 실적 | http://ir.lottetour.com/kor/PressDetail?i=141 (+2Q26: https://www.yna.co.kr/view/AKR20260701152500030) | 2026-05-14 (분기보고서 공시일) | 제주 / 5성 대형 복합리조트 호텔 | 판매객실 109,233실(1Q). 1,600실 규모와 OCC 역산이 일치 | 1Q 객실 ADR **미공개**. 4·5월 ADR 25.4만·26.1만원은 언론이 인용한 IR 수치(검증 대기) | **실현** 75.9% (1Q26, 전년 55.3%), 2Q26 88.3% | 미공개 | 호텔매출 381.4억, F&B 95.4억. 운영사 하얏트, 수수료 조건 미공개 | 대전과 시장 상이 → 운영지표 상한 참고용 | high (회사 IR 원문) |
| H4 | 신한서부티엔디리츠 호텔운영실적 (그랜드머큐어 용산, 신라스테이 마포 등) | https://shsbreit.com/kr/sub/investment/hotel.php | '26.06.30 기준 | 서울 / 상장 리츠 보유 호텔 | 페이지에 미기재 | 실현 ADR (천원, 차트) | 실현 OCC (차트) | — | 마스터리스·매출연동 수수료 구조(IR PDF 2023) | 리츠 공시라 대전 비교엔 한계 | medium (official IR. **수치가 SVG 차트에 있어 미추출 → no-data**) |
| H5 | 야놀자리서치 「2025년 2분기 국내 숙박업 동향」 PDF | https://www.yanolja-research.com/common/fileDown?type=1&number=252 (파일명 생략) | 2025 3분기 발간 | 전국 / 등급별 호텔·모텔·펜션 | — | 플랫폼·설문 기반 ADR. 5성 YoY −4.1% | 5성 OCC YoY −19.8% | 5성 RevPAR YoY −23.0% | — | **비공식 민간 리서치**(NOL·AirDNA·설문) → 실현 ADR/OCC로 표기 금지 | medium (원문 PDF 파싱 성공, 4/31쪽) |

**관리수수료 근거(management_fee_basis)는 공식 공개 원문을 이번에 확보하지 못했다.** 블로그에 나오는 “기본 0.5~1% + 인센티브” 같은 수치는 검증되지 않아 쓰지 않았다. 해당 필드는 `no-data`로 둔다. 상장 호텔 리츠의 투자설명서(DART)나 운영위탁계약 요약 공시가 다음 후보다.

**예약가 금지 원칙 준수:** 예약 사이트 판매가는 하나도 쓰지 않았다. H3·H1은 `realized`, H5는 `platform_derived`로 구분했다.

---

## 6. COST_LICENSE_SECURITY

| 항목 | 내용 |
|---|---|
| 이번 검증 비용 | Firecrawl 약 30 크레딧 (scrape 11회, 검색 6회 × 2). 이 중 `query` 형식 1회가 5 크레딧이라 비쌌다. 일반 수집은 markdown 형식을 쓴다 |
| Firecrawl 월 운영 예상 | 사례 1건당 평균 3~6 크레딧(검색 1~2 + 본문 1 + PDF 쪽수) → 월 100건이면 300~600 크레딧. **현재 연결된 Firecrawl 계정 플랜의 잔여 크레딧 안에서 처리**하는 것을 원칙으로 한다(신규 유료 결제 없음). 요금표는 사용 전에 계정 화면에서 확인 |
| Crawl4AI | 셀프호스트 0원 (Apache-2.0). 호스티드는 README 기준 무료 월 1,000 크레딧, 유료 월 $10부터. 이번 단계에서는 사용하지 않음 |
| Docling / Docling MCP | 0원 (MIT). 로컬 PDF는 CPU로도 돌지만 torch와 모델로 수 GB가 든다. docling-serve 원격 운영은 배포에 해당해 보류 |
| 라이선스 위험 | Firecrawl은 AGPL이지만 SaaS·MCP 사용에는 영향이 없다. 셀프호스트 수정본을 배포하지 않는다. 공공누리 4유형(H2)은 상업적 이용·변경 금지라 **보고서에 출처 인용만 하고 가공 재배포는 하지 않는다** |
| 보안 | 쿠키·자격증명 저장 없음. Firecrawl 키는 커넥터가 관리. Browser Use는 로그인 세션을 쓰므로 보류. 수집 원본은 SHA-256으로 출처를 고정 |
| 접근 제약 | 이 클라우드 환경의 네트워크 정책이 daejeon.go.kr, mcst.go.kr, dart.fss.or.kr, g2b.go.kr, kosis.kr, data.go.kr, huggingface.co 등을 차단한다. 로컬 크롤러·Docling 모델 다운로드는 **접속이 열린 다른 호스트**에서 해야 한다 |

---

## 7. PROPOSED_ARCHITECTURE 및 BUILD_OR_NO_BUILD_DECISION

### 7.1 추천 구성 (공통 엔진 1개 + 도메인 어댑터 2개)

```
[입력: URL 또는 업로드 PDF/XLSX]
   │  source_id = sha256(url|file), job_id
   ▼
[수집] Firecrawl MCP (scrape markdown/rawHtml, PDF parser, search)
   │      └ 보조: Crawl4AI (JS 다운로드·SVG) — 접속 가능한 호스트에서만
   ▼
[문서 파싱] Docling (XLSX/HTML/DOCX, PDF는 모델 캐시 후)
   │      └ 표 교차검증: Docling 표 ↔ Firecrawl markdown 표
   ▼
[분류·스키마] 어댑터 A: 공사비 (§5.1 필드)  /  어댑터 B: 호텔 (§5.2 필드)
   │      필수: original_url, fetched_at, sha256, parser, confidence, no_data_fields[], needs_review
   ▼
[산출] JSON + 짧은 보고서 → Google Drive (담당 방)
```

### 7.2 결정

- **지금: NO-BUILD.** 에이전트가 Firecrawl MCP로 수집하고 §5의 스키마로 JSON과 보고서를 만드는 방식으로 충분하다. 새 앱, 대시보드, 배포는 만들지 않는다.
- **조건부 BUILD 제안 (최소 수집기 1개):** `df-collect` CLI (Python, 약 200줄).
  - 하는 일: 입력 URL/파일 → (URL이면 Firecrawl SDK로 rawHtml/PDF 수집) → Docling 변환 → 표 교차검증 → 스키마 JSON과 Markdown 출력.
  - 착수 조건: ① 사용자가 XLSX/PDF 견적서·운영자료를 반복해서 올리는 경우(월 10건 이상), ② 한국 공공 사이트와 huggingface.co에 접속할 수 있는 실행 호스트 확보, ③ Firecrawl API 키를 환경변수로 쓰는 것을 사용자가 승인.
  - 산출물 기준: 단위 테스트(이번 KIND 샘플과 야놀자 PDF 샘플 고정), 필드 감사 리포트.

---

## 8. TWO_SAMPLE_DEMO / EXECUTION_EVIDENCE

| 게이트 | 상태 | 근거 |
|---|---|---|
| G1 저장소·커밋·라이선스 | **통과** | §2. clone한 HEAD 커밋과 LICENSE 파일 |
| G2 기존 커넥터 재사용 | **통과** | Firecrawl MCP scrape: daejeon.go.kr scrapeId `01a188b5-b6e9-70e9-9d49-f57e10cd97ff`, KIND rawHtml (1 크레딧), 야놀자 PDF scrapeId `01a188ba-6926-73aa-a377-902e6ac8f34c` |
| G3 도메인별 공개 샘플 1건 파싱 | **통과** | 공사비: KIND 공시 → Docling 표 추출 (§4.1, `evidence/kind_hyosung_table.csv`). 호텔: 야놀자 PDF → Firecrawl PDF 표 9개 (§3.1) |
| G4 필드 품질 감사·no-data 표기 | **통과** | 계약명 손실 4/33, 헤더 손실, 차트 unlabelled, 라벨 오류 1건. §5 표에 no-data 명시 |
| G5 10개 출처 비교 | **통과** | §5.1 5건 + §5.2 5건 |
| G6 출처 고정 보고서 Drive 저장 | **통과** | 이 문서 (Drive URL은 §10) |

실행 로그 요약:
- `docling_test.py`: `status ConversionStatus.SUCCESS secs 18.6 tables 2358 texts 1668`
- `c4a_test.py`: `LOCAL success True secs 4.5 md_chars 658608 tables 663` / `LIVE success False ... net::ERR_TUNNEL_CONNECTION_FAILED`
- 원본 HTML SHA-256: `5cf56ce23bbc7211205bf9813f5cbef3c816cf7c70007f2ac5e4d5c3ef06bf19`

증거 파일(같은 폴더 `evidence/`): `kind_hyosung_table.csv`, `kind_hyosung_daejeon.json`, `docling_test.py`, `c4a_test.py`.

---

## 9. HOLD_BLOCKERS

1. **네트워크:** 이 클라우드 환경에서 한국 공공 사이트와 huggingface.co 접속이 차단돼 있다. 로컬 Crawl4AI 실사이트 수집과 Docling PDF 모델 다운로드를 하려면 환경 설정의 허용 도메인에 해당 호스트를 추가하거나, 다른 실행 호스트가 필요하다.
2. **GitHub 인수인계 원문:** `dream-factories/dream-factory-control-center` 저장소가 이 세션에 연결되지 않아 원문 대조를 하지 못했다(Drive 사본으로 대체).
3. **원문 미확보:** D2(대흥4구역)의 DART 원문 rcpNo, D4(조달청 정보광장 수치), D5(공사비지수 원표), H3의 ADR 원문, H4의 SVG 차트 수치.
4. **연면적 부재:** 대흥동 사례 모두 GFA가 공개되지 않았다. 건축물대장(세움터)·사업시행인가 고시를 조회해야 ㎡당 공사비를 산출할 수 있다.
5. **관리수수료 근거:** 공식 공개 원문이 없다. 사용자가 제공한 계약서나 리츠 투자설명서가 필요하다.

---

## 10. RESULT_URL

- Google Drive 보고서: (업로드 후 기재 — 이 문서의 Drive 사본에는 자기 URL이 들어 있지 않다. 채팅 응답의 URL을 기준으로 한다)
- GitHub 사본: `biztradepros/grok-knowledge-01` 브랜치 `ccr-b405f61b-bk8mms`, 경로 `research/df-daeheung-hotel-collector-20261030/` (approved 자료방 목록에는 올리지 않음)
