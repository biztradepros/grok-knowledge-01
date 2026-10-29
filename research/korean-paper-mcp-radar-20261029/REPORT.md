# 한국 논문 리서치용 MCP 지식 레이더 — 후보 10선 연구 보고서 R01

- 문서 ID: `DF-KR-PAPER-MCP-RADAR-20261029-R01`
- 작성: Claude Code 원격 세션, 2026-10-29
- 목적: 한국 논문(KCI·RISS·DBpia·ScienceON 등)의 검색·원문·인용을 AI가 직접 다룰 수 있는 MCP 서버 후보 10개를 골라 점수화한다. 다른 AI가 이어서 검증·확장할 수 있는 공동 연구 기준을 정한다.
- 기계 판독용 목록: 같은 폴더의 `candidates.json`

---

## 1. 결론 요약

1. **한국 논문 단일 통합 MCP는 없다.** KCI, ScienceON, RISS는 각각 다른 MCP가 맡는다. DBpia는 PhDHan88의 3원(KCI·DBpia·RISS) 검색 MCP 하나만 있고, 원문 다운로드는 하지 않는다.
2. **1순위 조합(레이더 코어):**
   - KCI·OAK: `ckgerteis/korea-scholarship-mcp` (80점). 키 없이 OAI-PMH 수확이 되고, 해시 체인 질의 원장으로 출처가 남는다.
   - ScienceON: `rubatoyd/scienceON-mcp` (75점). 단일 출처를 가장 깊게 다루며, 결과를 xlsx·sqlite로 저장한다.
   - 국가R&D·특허·보고서: `ansua79/kisti-mcp` (74점). 다만 **CC BY-NC 4.0**이라 상업 이용이 불가하다.
3. **원문(full-text) 읽기는 해외 OA 쪽이 강하다.** `arxiv-mcp-server`(70점)와 `paper-search-mcp`(66점)가 원문 다운로드·읽기·인용그래프·주제 알림을 지원한다. 한국 논문 원문은 KCI·OAK의 OA 원문 링크, ScienceON 원문 URL, 사용자 Zotero 라이브러리(PDF)로 확보한다.
4. **RISS 학위논문은 `auraweon7-ship-it/riss`(63점)만 있다.** README의 공용 배포 URL이 API 키를 URL 쿼리에 넣는 방식이라 **직접 셀프호스트해야 한다.**
5. 이번 검증은 **정적 검증**이다. 저장소 clone, 라이선스·최근 커밋·도구 목록·PyPI 메타데이터를 확인했다. 서버를 실행하는 스모크 테스트는 실행 권한 정책에 막혀 하지 못했다. 한국 학술 API(kci.go.kr 등)는 이 클라우드 환경에서 접속도 차단돼 있다. **실행 검증은 §7의 공동 연구 과제로 남긴다.**

---

## 2. 평가 방법

### 2.1 점수 기준 (100점)

| 항목 | 배점 | 보는 것 |
|---|---|---|
| K. 한국 논문 커버리지 | 30 | KCI·RISS·DBpia·ScienceON·NTIS·OAK 중 어디를 공식 API로 덮는가 |
| F. 원문 접근 | 20 | 원문 PDF·텍스트를 읽거나 합법적 OA 원문 링크를 주는가 |
| R. 레이더 기능 | 15 | 대량 수확, 주제 알림(watch), 인용·참고문헌 그래프, 저널 지표 |
| I. 설치·인증 난이도 | 10 | 키 없이 쓰는 도구, uvx·.mcpb 원클릭, 키 발급 난이도 |
| M. 유지관리 | 10 | 최근 커밋, 릴리스·버전, CI |
| L. 라이선스 | 10 | MIT·Apache=10, 비상업=4, 라이선스 파일 없음=2 |
| P. 협업·출처성 | 5 | 구조화 응답, 질의 기록, 잘림(truncation) 표시 등 다른 AI가 재검증할 수 있는 근거 |

### 2.2 검증 근거

- 모든 저장소를 `git clone --depth 1`로 받아 HEAD 커밋, LICENSE, README, 도구 정의를 직접 확인했다.
- PyPI 버전은 PyPI JSON API로 확인했다.
- GitHub 별 수는 이 환경에서 GitHub 웹·API 접근이 막혀 **측정하지 못했고**, 점수에 넣지 않았다.

---

## 3. 후보 10선 — 순위표

| 순위 | MCP | 점수 | 대상 | GitHub | 웹·배포 주소 |
|---|---|---|---|---|---|
| 1 | korea-scholarship-mcp | **80** | KCI + OAK | https://github.com/ckgerteis/korea-scholarship-mcp | DOI https://doi.org/10.5281/zenodo.22305407 · https://glama.ai/mcp/servers/ckgerteis/korea-scholarship-mcp |
| 2 | scienceON-mcp (rubatoyd) | **75** | ScienceON | https://github.com/rubatoyd/scienceON-mcp | https://github.com/rubatoyd/scienceON-mcp/releases (.mcpb) · https://glama.ai/mcp/servers/rubatoyd/scienceon-mcp |
| 3 | kisti-mcp | **74** | ScienceON + NTIS + DataON | https://github.com/ansua79/kisti-mcp | https://pypi.org/project/kisti-mcp/ |
| 4 | KCI_openAPI (kci-openapi-mcp) | **72** | KCI | https://github.com/rubatoyd/KCI_openAPI | MCP 레지스트리 `io.github.rubato103/kci-openapi-mcp` · https://pluginbench.com/mcp/io.github.rubato103/kci-openapi-mcp |
| 5 | arxiv-mcp-server | **70** | arXiv (+Semantic Scholar 인용) | https://github.com/blazickjp/arxiv-mcp-server | https://pypi.org/project/arxiv-mcp-server/ · https://registry.modelcontextprotocol.io/v0.1/servers/io.github.blazickjp%2Farxiv-mcp-server/versions/latest |
| 6 | paper-search-mcp | **66** | 20여 개 해외 소스(arXiv·PMC·CORE·OpenAlex·Semantic Scholar 등) | https://github.com/openags/paper-search-mcp | https://pypi.org/project/paper-search-mcp/ · https://smithery.ai/server/@openags/paper-search-mcp |
| 7 | zotero-mcp | **64** | 사용자 Zotero 라이브러리(한국 PDF 포함) | https://github.com/54yyyu/zotero-mcp | https://pypi.org/project/zotero-mcp-server/ |
| 8 | riss (RISS MCP Server) | **63** | RISS 학위·학술지 | https://github.com/auraweon7-ship-it/riss | API: https://www.riss.kr/apicenter/apiSearchThesis.do |
| 9 | semantic-scholar-fastmcp | **53** | Semantic Scholar | https://github.com/zongmin-yu/semantic-scholar-fastmcp-mcp-server | https://pypi.org/project/semantic-scholar-fastmcp/ · https://smithery.ai/server/semantic-scholar-fastmcp-mcp-server |
| 10 | korea-academic-mcp | **52** | KCI + DBpia + RISS | https://github.com/PhDHan88/korea-academic-mcp | https://glama.ai/mcp/servers/PhDHan88/korea-academic-mcp (Smithery 게이트웨이용) |

### 3.1 세부 점수

| MCP | K30 | F20 | R15 | I10 | M10 | L10 | P5 | 합계 |
|---|---|---|---|---|---|---|---|---|
| korea-scholarship-mcp | 24 | 10 | 13 | 9 | 9 | 10 | 5 | **80** |
| scienceON-mcp (rubatoyd) | 22 | 8 | 13 | 8 | 10 | 10 | 4 | **75** |
| kisti-mcp | 27 | 14 | 12 | 6 | 8 | 4 | 3 | **74** |
| KCI_openAPI | 20 | 6 | 13 | 9 | 10 | 10 | 4 | **72** |
| arxiv-mcp-server | 2 | 19 | 15 | 10 | 10 | 10 | 4 | **70** |
| paper-search-mcp | 5 | 18 | 11 | 9 | 9 | 10 | 4 | **66** |
| zotero-mcp | 6 | 18 | 8 | 7 | 10 | 10 | 5 | **64** |
| riss | 24 | 8 | 9 | 5 | 6 | 10 | 1 | **63** |
| semantic-scholar-fastmcp | 4 | 8 | 13 | 9 | 6 | 10 | 3 | **53** |
| korea-academic-mcp | 28 | 4 | 5 | 5 | 6 | 2 | 2 | **52** |

---

## 4. 후보별 특징 분석

### 1) korea-scholarship-mcp — 80점
- **구성:** FastMCP stdio, 도구 8개, v0.6.3, 최근 커밋 2026-10-12 `66aeda3`, MIT, Zenodo DOI가 있다.
- **도구:** `kci_search`, `kci_article`(초록·키워드·UCI), `kci_references`(참고문헌), `kci_journal_metrics`(저널 인용지표)는 KCI 키가 필요하다. `kci_harvest`, `oak_harvest`, `oak_record`, `korea_sources_status`는 **키 없이** 쓴다.
- **강점:**
  - 모든 응답이 공통 envelope(response-schema 2.3.0)로 나오고, 해시 체인 질의 원장에 기록된다. 다른 AI가 같은 질의를 재현·감사하기 좋다.
  - 일본 `cinii-mcp`·`jstage-mcp`와 응답 형식이 같아 한·일·영 비교 연구가 된다.
  - KCI가 오류를 HTTP 200으로 돌려주는 함정을 `KCI_REJECTED` 같은 상태코드로 드러낸다.
- **한계:** ScienceON·RISS·DBpia는 의도적으로 다루지 않는다. KCI는 단행본·학위논문을 색인하지 않는다. PyPI에 없어 git으로 설치한다.

### 2) scienceON-mcp (rubatoyd) — 75점
- **구성:** 도구 5개(`scienceON_status`, `_search`, `_detail`, `_export`, `_collect_groups`), v0.5.1, 최근 커밋 2026-10-29 `877c34d`, MIT, CI와 `.mcpb` 원클릭 릴리스가 있다.
- **강점:**
  - 다중 쿼리·와일드카드·연도범위 검색과 대량 수집 결과를 xlsx·csv·json·sqlite로 저장한다. 연구 코퍼스를 만들기에 적합하다.
  - `truncated`·`total_mismatch`로 덜 받은 결과를 명시한다.
  - stdio·streamable-http·sse를 지원한다.
- **한계:** ScienceON API 키, Client ID, MAC 주소 등록이 필요하다(공인 IP 진단 도구 있음). 원문은 URL 수준이다. PyPI의 `scienceon-mcp`(1.0.2)는 **다른 개발자(ansua79)의 패키지**라 혼동하지 않아야 한다.

### 3) kisti-mcp — 74점
- **구성:** 도구 32종(ScienceON 17, NTIS 13, DataON 2), v0.3.32.2(PyPI 2026-07-01), `uvx kisti-mcp`로 실행. KISTI 개발자 측 프로젝트다.
- **강점:**
  - 논문, 특허, 보고서, 국가R&D 과제·성과, 연구데이터, 기술트렌드까지 가장 넓게 다룬다.
  - DOI·원문 URL·인용을 반환한다.
  - NTIS 권한 등급별 자동 폴백(전문기관용 → 기관용 → 전체용)을 지원한다.
- **한계:**
  - **라이선스가 CC BY-NC 4.0**이다. 비상업 연구에만 쓸 수 있고 OSI 오픈소스가 아니다.
  - NTIS 키는 API별로 따로 신청해야 하고 유효기간이 1년이다.
  - DataON은 2026년 3월부터 기관 사용자만 신청할 수 있다.

### 4) KCI_openAPI (kci-openapi-mcp) — 72점
- **구성:** 도구 7개, v0.3.6, 최근 커밋 2026-10-29 `b311008`, MIT. MCP 레지스트리에는 `io.github.rubato103/kci-openapi-mcp`로 등록돼 있고, 원래 레지스트리 경로의 저장소(rubato103)는 지금 접근할 수 없다.
- **강점:**
  - `kci_collect`가 키 유무에 따라 REST와 OAI-PMH를 자동으로 고르고 파일로 저장한다.
  - `kci_detail`로 참고문헌을, `kci_journal_citation`으로 연도별 IF를 받는다.
  - OS별 자체완결 `.mcpb`가 있다.
- **한계:** 기능이 1번과 겹친다. 둘 중 하나만 고르면 협업 원장은 1번, 대량 수집 자동화는 4번이 낫다. REST 검색은 `title`이 필수다.

### 5) arxiv-mcp-server — 70점
- **구성:** v0.8.2(PyPI 2026-10-08), Apache-2.0, 공식 MCP 레지스트리에 등록, CI가 있다.
- **레이더 기능이 가장 완성돼 있다.**
  - `watch_topic`, `check_alerts`로 주제 알림을 건다.
  - `citation_graph`(Semantic Scholar)와 `export_citations`(BibTeX)를 지원한다.
  - 원문을 Markdown으로 내려받아 섹션·LaTeX 단위로 읽는다(`read_paper_section`, `get_paper_latex_section`).
- **한계:** 한국 논문은 거의 없다. 한국 연구자의 arXiv 논문만 해당한다.

### 6) paper-search-mcp — 66점
- **구성:** v0.1.4(PyPI 2026-07-02), MIT, stdio·sse·streamable-http와 OAuth 모드를 지원한다.
- **강점:**
  - `search_papers`로 다중 소스를 동시 검색하고 중복을 제거한다.
  - `download_with_fallback`이 OA 원문을 순차 폴백으로 확보한다.
  - 소스별로 검색·다운로드·읽기 가능 여부를 표로 공개한다.
- **한계:** 한국 소스가 없다. DOI가 있는 한국 학술지만 OpenAlex·Crossref·CORE를 통해 일부 잡힌다. Google Scholar는 CAPTCHA 위험이 있다.

### 7) zotero-mcp — 64점
- **구성:** v0.15.1(PyPI 2026-10-16), MIT, 활발히 유지된다.
- **강점:**
  - 사용자가 모은 한국 논문 PDF(RISS·DBpia에서 합법적으로 받은 원문 포함)를 원문 검색, 의미 검색, 페이지 단위 읽기, 주석으로 다룬다.
  - 그룹 라이브러리를 쓰면 여러 AI와 사람이 같은 원문 집합을 공유한다.
  - DOI·URL로 논문을 추가하는 쓰기 기능이 있다.
- **한계:** 검색 대상은 내 라이브러리뿐이다. Zotero 설치가 필요하다.

### 8) riss (RISS MCP Server) — 63점
- **구성:** Node/TypeScript, HTTP SSE, 도구 6개, v1.0.0, 최근 커밋 2026-04-27, MIT. 개발자는 README에 한국외국어대학교 박정원 교수로 표기돼 있다.
- **강점:** **RISS 학위논문(석·박사)을 다루는 유일한 후보**다. 저자별 검색, 최신 논문, 목차·참고문헌·원문 파일 정보를 준다.
- **한계·보안:**
  - README가 안내하는 공용 Railway URL은 **API 키를 URL 쿼리(`?oc=`)로 전달**한다. 로그와 프록시에 키가 남을 수 있어 **반드시 셀프호스트**해야 한다.
  - RISS API 키 발급이 필요하다.

### 9) semantic-scholar-fastmcp — 53점
- **구성:** 도구 16개 안팎, v0.1.2(2026-03-20), MIT.
- **강점:** 인용·피인용 네트워크, 저자, 추천 API를 지원해 국제 인용 레이더로 쓸 수 있다. 키 없이도 동작한다.
- **한계:** 한국어 논문 커버리지가 약하고, 최근 업데이트가 7개월 전이다. arXiv MCP의 `citation_graph`와 기능이 겹친다.

### 10) korea-academic-mcp — 52점
- **구성:** 도구 3개(KCI·DBpia·RISS), Smithery 게이트웨이용 TypeScript, 최근 커밋 2026-07-22.
- **강점:** **DBpia를 공식 API로 검색하는 유일한 후보**다. 스크래핑을 하지 않는다고 명시한다.
- **한계:**
  - **LICENSE 파일이 없어** 재사용 권리가 불명확하다.
  - 원문 다운로드와 상업적 이용은 범위 밖이다.
  - RISS 키는 기관 단위 승인이 많고, DBpia API 신청이 필요하다.

---

## 5. 추천 구성 — “한국 논문 지식 레이더”

```
[주제 질의]
  ├─ 한국 학술지: korea-scholarship-mcp (KCI REST + OAI 무인증 수확, 질의 원장)
  ├─ 과학기술·R&D: scienceON-mcp (코퍼스 수집)  [+ 비상업이면 kisti-mcp로 NTIS·특허·보고서]
  ├─ 학위논문: riss (셀프호스트, 키는 env로)
  ├─ DBpia: korea-academic-mcp (검색만, 라이선스 확인 후)
  ├─ 해외 연결: paper-search-mcp (OA 원문) + arxiv-mcp-server (알림·인용그래프)
  └─ 원문 보관·읽기: zotero-mcp (그룹 라이브러리) → PDF 표·본문은 Docling으로 구조화
[공통 산출] envelope JSON (source, query, total, returned, truncated, url, doi, oa_url, fetched_at) → Drive 보고서
```

이 세션에 이미 연결된 호스티드 도구도 보완재로 쓸 수 있다. 다만 GitHub OSS가 아니라서 순위에서는 뺐다.
- Consensus·Scite: 해외 논문 근거 검색, 인용 맥락
- Firecrawl research: 논문 전문 검색·읽기
- Hugging Face Papers: AI 분야 최신 논문

---

## 6. 위험·주의

| 위험 | 내용 | 대응 |
|---|---|---|
| 원문 저작권 | DBpia·RISS 원문은 대부분 기관 구독이나 유료다 | MCP로는 메타데이터와 OA 원문 링크만 다룬다. 원문은 사용자가 합법적으로 받은 PDF를 Zotero로 넣는다 |
| 키 노출 | riss 공용 URL의 쿼리 키 방식 | 셀프호스트하고, env로만 전달한다 |
| 라이선스 | kisti-mcp는 CC BY-NC, korea-academic-mcp는 라이선스 없음 | 상업 프로젝트에서는 1·2·4번(MIT)을 우선 쓴다 |
| API 함정 | KCI는 실패해도 HTTP 200을 돌려준다. ScienceON은 MAC·IP 등록이 필요하다 | 상태 도구(`korea_sources_status`, `kci_status`, `scienceON_status`)를 먼저 호출한다 |
| 결과 잘림 | 일부 API는 질의당 100건 상한 | `truncated`·`total_mismatch` 플래그를 그대로 보고에 남긴다 |

---

## 7. 다른 AI와의 공동 연구 방법

### 7.1 역할 분담 (권장)

| 레인 | 담당 AI | 과제 | 산출물 |
|---|---|---|---|
| L1 실행 검증 | 로컬 실행·키를 쓸 수 있는 AI (Cursor·Claude Desktop 등) | 1~4·8·10번 서버를 실제 키로 띄워 `tools/list`와 질의 1건씩 실행 | 서버별 성공/실패 로그, 응답 샘플 JSON |
| L2 커버리지 측정 | 웹 검색 가능한 AI | 같은 질의 3개(예: “스마트시티”, “호텔 수익관리”, “공사비 지수”)를 각 서버에 넣어 건수·중복률 비교 | 질의 × 서버 건수표 |
| L3 원문 경로 | 문서 파싱 담당 AI | KCI·OAK OA 원문 링크와 ScienceON 원문 URL로 PDF를 받아 Docling으로 표·본문 추출 | 원문 1건당 추출 품질 메모 |
| L4 신규 후보 감시 | GitHub 검색 AI | “KCI MCP”, “RISS MCP”, “DBpia MCP”, “ScienceON MCP”, “NTIS MCP”, “KoreaScience MCP”를 월 1회 검색 | `candidates.json`에 항목 추가 |

### 7.2 기록 규칙

- 새 후보나 점수 변경은 `candidates.json`의 같은 필드로 추가한다: `rank`, `name`, `score`, `scores`, `github`, `web`, `license`, `last_commit`, `version`, `sources`, `key_required`, `full_text`, `radar`, `risks`, `verified_by`, `verified_at`, `verification`.
- `verification` 값은 셋 중 하나로 쓴다.
  - `static`: README·코드 확인
  - `smoke`: 서버 기동과 도구 목록 확인
  - `live`: 실제 질의 성공
- 이번 보고서의 항목은 모두 `static`이다.
- 수치(건수·IF·별 수)는 반드시 원문 URL과 확인 날짜를 함께 적는다. 확인하지 못한 값은 `null`로 둔다.

### 7.3 다음 단계

1. L1 실행 검증으로 1·2·4·8번을 `smoke`에서 `live`로 올린다.
2. KCI·RISS·ScienceON 키는 사용자가 발급해 각 AI의 MCP 설정 `env`에만 넣는다. 저장소에는 넣지 않는다.
3. 결과를 반영해 R02에서 최종 조합을 확정한다.

---

## 8. 실행 증거·한계

- clone한 HEAD 커밋:
  - korea-scholarship-mcp `66aeda3`, scienceON-mcp `877c34d`, kisti-mcp `1c15d5f`, KCI_openAPI `b311008`
  - arxiv-mcp-server `572e301`, paper-search-mcp `cab1b5c`, zotero-mcp `eb016b1`, riss `3306af2`
  - semantic-scholar-fastmcp `68e7b06`, korea-academic-mcp `dcb7398`
- PyPI 확인(2026-10-29):
  - kisti-mcp 0.3.32.2, scienceon-mcp 1.0.2(ansua79), paper-search-mcp 0.1.4
  - arxiv-mcp-server 0.8.2, zotero-mcp-server 0.15.1, semantic-scholar-fastmcp 0.1.2
  - kci-openapi-mcp와 korea-scholarship-mcp는 PyPI에 없어 git 또는 .mcpb로 설치한다
- **하지 않은 것:**
  - 서버 실행 스모크 테스트: 외부 코드 실행이 권한 정책에서 거부됨
  - 한국 학술 API 실질의: 이 환경에서 kci.go.kr·riss.kr·scienceon.kisti.re.kr 접속이 차단됨
  - GitHub 별 수 측정: GitHub 웹·API 접근 제한
