# Scout run report - DKSC-0929201853

LOT: DKSC-CLAUDE-CODE-SCOUT-001 | scout v0.1.0 | AUTHORITY: NONE | RESULT: **PASS** | COLLECTION_STATUS: MEASURED

## Execution

- Command: `python3 scout.py run --question 'PDF, 문서, Excel 또는 카탈로그에서 구조화된 데이터를 자동 추출하는 데 사용할 수 있는 공개 Skill 또는 코드 도구를 찾아줘.' --out runs/001`
- Started: 2026-09-29T20:18:53+00:00 (KST 2026-09-30T05:18:53+09:00), finished 2026-09-29T20:19:12+00:00, 19.1 s
- Input mode: cli --question
- HTTP requests: 90 (ok 69); budget 180; GET only, no credentials sent

## Input question

> PDF, 문서, Excel 또는 카탈로그에서 구조화된 데이터를 자동 추출하는 데 사용할 수 있는 공개 Skill 또는 코드 도구를 찾아줘.

## Question decomposition

- **OBJECT**: PDF (`pdf`), 문서 (`문서`), Excel/스프레드시트 (`excel`), 카탈로그 (`카탈로그`)
- **ACTION**: 추출 (`추출`)
- **OUTPUT**: 구조화된 데이터 (`구조화`)
- **CONTEXT**: 자동화 (`자동`), Agent Skill (`skill`), 코드 도구 (`코드`), 공개/오픈소스 (`공개`)
- Implied (secondary) concepts: table, ocr, product, json
- Free keywords (not in lexicon): -; unmapped Korean tokens: -

## Generated queries

- CORE_QUERY: `pdf document excel extract extraction structured data`
- GITHUB_QUERY: `(pdf OR document OR excel OR spreadsheet) (extract OR extraction OR parse) "structured data" in:name,description,readme`
- SKILL_QUERY: `SKILL.md pdf document extract structured data`
- MCP_QUERY: `mcp server pdf document extract structured data`
- NPM_QUERIES: `pdf extract structured data`, `keywords:mcp pdf extract`, `document extract structured data`
- MCP_REGISTRY_TERMS: pdf, document, excel, catalog, extract, ocr
- TECHNICAL_TERMS: pdf parsing, pdf text extraction, document parsing, intelligent document processing, document ai, xlsx, csv, tabular data, product catalog, product data extraction, product feed, data extraction, information extraction, structured output, json schema extraction, automation pipeline, SKILL.md, python library, cli tool, table extraction, table detection, optical character recognition, product information, product attributes, json output

## Sources accessed

| # | Source | Status | Requests | Raw seen | Passed gate | Kept | Reason |
|---|---|---|---|---|---|---|---|
| 1 | Anthropic official Skills repository (anthropics/skills) | **PASS** | 20 | 19 | 2 | 2 | 20/20 requests ok; 2 relevant candidates kept |
| 2 | GitHub public repository search (REST API, unauthenticated) | **HOLD** | 1 | 0 | 0 | 0 | HOLD_POLICY: this execution environment scopes api.github.com to its configured repositories; public search not reachable without widening access. Not bypassed. |
| 3 | Public GitHub curated lists of Skills / MCP servers (raw README) | **PASS** | 4 | 5416 | 46 | 20 | 4/4 requests ok; 20 relevant candidates kept |
| 3 | Official MCP Registry (registry.modelcontextprotocol.io) | **PASS** | 6 | 345 | 48 | 20 | 6/6 requests ok; 20 relevant candidates kept |
| 4 | Official Claude documentation indexes (llms.txt) | **PARTIAL** | 2 | 863 | 0 | 0 | 2/2 requests ok; 0 relevant candidates kept |
| 5 | npm public registry search API | **PASS** | 3 | 55 | 25 | 20 | 3/3 requests ok; 20 relevant candidates kept |
| 5 | PyPI search (no JSON search API exists; HTML listing) | **HOLD** | 1 | 0 | 0 | 0 | HOLD: PyPI search answers with a JavaScript client challenge; not bypassed. PyPI JSON API is still used for per-package metadata. |
| 5 | Claude plugin / connector directory (web) | **PARTIAL** | 1 | 0 | 0 | 0 | HTTP 200 (https://claude.com/marketplace/plugins) but no public machine-readable listing; HTML not scraped (machine-first rule) |

## Counts

- Raw candidates kept from sources: 62
- After dedup pass 1: 59 groups (3 duplicate listings merged)
- Selected and read: 15
- Capability records: 15 (UNIQUE 15, POSSIBLE_DUPLICATE 0)
- Next questions: 8
- OUTBOX candidates: 3

## Capabilities

| ID | Name | Type | Evidence | Dedup | Score | Categories | License | Auth | Source |
|---|---|---|---|---|---|---|---|---|---|
| DKSC-0929201853-001-koraynar-doc-extract-mcp | koraynar/doc-extract-mcp | MCP_SERVER | E3 | UNIQUE | 15 | DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/STRUCTURED_OUTPUT/MCP | MIT | UNKNOWN | https://github.com/koraynar/doc-extract-mcp |
| DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski | PSPDFKit-labs/nutrient-agent-skill | MCP_SERVER | E2 | UNIQUE | 15 | DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/TABLE_EXTRACTION/SPREADSHEET | UNKNOWN | YES - NUTRIENT_API_KEY | https://github.com/PSPDFKit-labs/nutrient-agent-skill |
| DKSC-0929201853-003-kordoc | kordoc | MCP_SERVER | E3 | UNIQUE | 14 | DOCUMENT_PROCESSING/DATA_EXTRACTION/CONVERSION/FORMS/MCP | MIT | UNKNOWN | https://www.npmjs.com/package/kordoc |
| DKSC-0929201853-004-anthropics-skills-docx | anthropics/skills/docx | AGENT_SKILL | E3 | UNIQUE | 13 | DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/CONVERSION/AGENT_SKILL | Proprietary. LICENSE.txt has… | NO_EVIDENCE_OF_AUTH - SKILL.m… | https://github.com/anthropics/skills/tree/main/skills/docx |
| DKSC-0929201853-005-document-to-json-pdf-invoice-sta | Document to JSON – PDF Invoice/Statement/Contract Parser | MCP_SERVER | E3 | UNIQUE | 13 | DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/STRUCTURED_OUTPUT/INVOICE_RECEIPT | MIT | YES - APIFY_TOKEN | https://registry.modelcontextprotocol.io/v0/servers?search=io.github.fashionmascherine-svg/document-to-json-mcp&version=latest |
| DKSC-0929201853-006-drolosoft-go-docs-mcp | drolosoft/go-docs-mcp | MCP_SERVER | E3 | UNIQUE | 13 | DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/SPREADSHEET/MCP | MIT | UNKNOWN | https://github.com/drolosoft/go-docs-mcp |
| DKSC-0929201853-007-lfnovo-content-core | lfnovo/content-core | MCP_SERVER | E3 | UNIQUE | 13 | DOCUMENT_PROCESSING/DATA_EXTRACTION/STRUCTURED_OUTPUT/AUTOMATION/WEB_EXTRACTION | MIT | YES - OPENAI_API_KEY, CRAWL4A… | https://github.com/lfnovo/content-core |
| DKSC-0929201853-008-opendatalab-mineru-ecosystem | opendatalab/MinerU-Ecosystem | MCP_SERVER | E3 | UNIQUE | 13 | DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/CONVERSION/MCP | Apache-2.0 | YES - MINERU_API_TOKEN | https://github.com/opendatalab/MinerU-Ecosystem/tree/main/mcp |
| DKSC-0929201853-009-linxule-mineru-mcp | linxule/mineru-mcp | MCP_SERVER | E3 | UNIQUE | 12 | DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/AUTOMATION/MCP | MIT | YES - MINERU_API_KEY | https://github.com/linxule/mineru-mcp |
| DKSC-0929201853-010-pdf4me | PDF4me | MCP_SERVER | E3 | UNIQUE | 12 | DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/CONVERSION/AUTOMATION | MIT | YES - PDF4ME_API_KEY | https://registry.modelcontextprotocol.io/v0/servers?search=io.github.pdf4me/pdf4me-mcp&version=latest |
| DKSC-0929201853-011-bigapi-mcp | @bigapi/mcp | MCP_SERVER | E3 | UNIQUE | 11 | MCP | MIT | YES - BIGAPI_KEY | https://www.npmjs.com/package/@bigapi/mcp |
| DKSC-0929201853-012-pspdfkit-nutrient-dws-mcp-server | PSPDFKit/nutrient-dws-mcp-server | MCP_SERVER | E3 | UNIQUE | 11 | DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/CONVERSION/MCP | MIT | YES - NUTRIENT_DWS_API_KEY, N… | https://github.com/PSPDFKit/nutrient-dws-mcp-server |
| DKSC-0929201853-013-flexorch-flexorch-mcp | flexorch/flexorch-mcp | MCP_SERVER | E3 | UNIQUE | 11 | DOCUMENT_PROCESSING/DATA_EXTRACTION/STRUCTURED_OUTPUT/INVOICE_RECEIPT/MCP | MIT | YES - FLEXORCH_API_KEY | https://github.com/flexorch/flexorch-mcp |
| DKSC-0929201853-014-zacccck-claude-mcp-read-email-at | Zacccck/Claude-MCP-Read-Email-Attachments | MCP_SERVER | E3 | UNIQUE | 11 | DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/STRUCTURED_OUTPUT/MCP | MIT | UNKNOWN | https://github.com/Zacccck/Claude-MCP-Read-Email-Attachments |
| DKSC-0929201853-015-anthropics-skills-pdf | anthropics/skills/pdf | AGENT_SKILL | E3 | UNIQUE | 10 | DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/TABLE_EXTRACTION/FORMS | Proprietary. LICENSE.txt has… | NO_EVIDENCE_OF_AUTH - SKILL.m… | https://github.com/anthropics/skills/tree/main/skills/pdf |

## Next questions

1. **PSPDFKit-labs/nutrient-agent-skill의 OCR과 anthropics/skills/pdf의 PDF 표 추출을 결합하면 스캔된 공급업체 카탈로그까지 구조화된 데이터(JSON)로 만들 수 있는가?**
   - WHY: 이번 실행에서 OCR 분류 7개, 추출 분류 14개가 확인됐지만 둘을 이어 붙인 검증 사례는 수집되지 않았다 (NOT_MEASURED).
   - SOURCE_CAPABILITIES: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski, DKSC-0929201853-015-anthropics-skills-pdf
   - NEXT_SEARCH_TERMS: pdf, catalog, table, extract, extraction, structured, pypdf, pdfplumber, pdf2image
2. **PSPDFKit-labs/nutrient-agent-skill의 PDF 표 추출 결과를 koraynar/doc-extract-mcp(으)로 넘겨 Excel 또는 데이터베이스 적재까지 자동화할 수 있는가?**
   - WHY: 추출 후보 14개와 스프레드시트 후보 6개가 따로 존재한다. 출력 형식(JSON/CSV)이 서로 맞는지는 확인되지 않았다.
   - SOURCE_CAPABILITIES: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski, DKSC-0929201853-001-koraynar-doc-extract-mcp
   - NEXT_SEARCH_TERMS: pdf, excel, spreadsheet, extract, extraction, database
3. **카탈로그(상품 목록) PDF에서 상품명·가격·규격 필드를 스키마 기반으로 추출하는 공개 Capability가 존재하는가?**
   - WHY: 질문의 핵심 대상 '카탈로그'를 설명에서 직접 언급한 후보가 하나도 없다 (공백 영역).
   - SOURCE_CAPABILITIES: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski
   - NEXT_SEARCH_TERMS: pdf, catalog, product, extract, extraction, structured
4. **상품 이미지와 텍스트를 동시에 추출할 수 있는 Capability가 존재하는가?**
   - WHY: 이미지를 언급한 후보는 7개다. 카탈로그 데이터화에는 상품 사진과 설명을 짝지어야 하지만 이번 후보들은 대부분 텍스트/표 중심이다.
   - SOURCE_CAPABILITIES: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski, DKSC-0929201853-004-anthropics-skills-docx, DKSC-0929201853-006-drolosoft-go-docs-mcp
   - NEXT_SEARCH_TERMS: product, image, extract, extraction, product information, product attributes, docx
5. **JSON 스키마 기반 추출을 지원하는 koraynar/doc-extract-mcp, Document to JSON – PDF Invoice/Statement/Contract Parser을(를) 공급업체 카탈로그 상품 스키마에 적용하면 데이터베이스 레코드를 바로 만들 수 있는가?**
   - WHY: 5개 후보가 JSON/스키마 출력을 언급한다. 스키마를 우리 쪽 필드로 바꿔 끼울 수 있는지는 확인되지 않았다.
   - SOURCE_CAPABILITIES: DKSC-0929201853-001-koraynar-doc-extract-mcp, DKSC-0929201853-005-document-to-json-pdf-invoice-sta, DKSC-0929201853-007-lfnovo-content-core
   - NEXT_SEARCH_TERMS: catalog, product, extract, extraction, structured, data
6. **API 키 없이 로컬에서 실행 가능한 후보(6개)만으로 PDF 문서 → 구조화 데이터 추출 파이프라인을 구성할 수 있는가?**
   - WHY: 전체 15개 중 9개는 인증 또는 외부 서비스가 필요하거나 표시돼 있다. 비용·보안 면에서 로컬 조합을 먼저 확인할 가치가 있다.
   - SOURCE_CAPABILITIES: DKSC-0929201853-001-koraynar-doc-extract-mcp, DKSC-0929201853-003-kordoc, DKSC-0929201853-004-anthropics-skills-docx, DKSC-0929201853-006-drolosoft-go-docs-mcp
   - NEXT_SEARCH_TERMS: pdf, document, extract, extraction, structured, data, docx
7. **Agent Skill(anthropics/skills/docx)의 절차와 MCP 서버(koraynar/doc-extract-mcp)의 도구 호출을 결합해 문서 추출 작업을 한 번의 요청으로 자동화할 수 있는가?**
   - WHY: Skill은 절차와 코드를, MCP는 외부 도구 호출을 제공한다. 두 형태가 이번 실행에서 모두 발견됐다.
   - SOURCE_CAPABILITIES: DKSC-0929201853-004-anthropics-skills-docx, DKSC-0929201853-001-koraynar-doc-extract-mcp
   - NEXT_SEARCH_TERMS: document, extract, extraction, document parsing, intelligent document processing, document ai, docx
8. **PSPDFKit-labs/nutrient-agent-skill과(와) anthropics/skills/pdf의 PDF 표 추출 정확도를 비교할 공개 벤치마크나 테스트 데이터셋이 있는가?**
   - WHY: 같은 역할의 후보가 여러 개라서 고르려면 정확도 근거가 필요하다. 이번 파일럿은 정확도를 측정하지 않았다.
   - SOURCE_CAPABILITIES: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski, DKSC-0929201853-015-anthropics-skills-pdf
   - NEXT_SEARCH_TERMS: pdf, table, extract, extraction, pdf parsing, pdf text extraction, pypdf, pdfplumber, pdf2image

## OUTBOX candidates

- **OBX-DKSC-0929201853-01** DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski | PSPDFKit-labs/nutrient-agent-skill | MCP_SERVER - relevance 15, E2_PRIMARY_DOC_READ, categories DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/TABLE_EXTRACTION/SPREADSHEET, referenced by 5 next question(s), found in 1 source(s). STATUS DISCOVERED, AUTHORITY NONE
- **OBX-DKSC-0929201853-02** DKSC-0929201853-001-koraynar-doc-extract-mcp | koraynar/doc-extract-mcp | MCP_SERVER - relevance 15, E3_PRIMARY_DOC_AND_MANIFEST_READ, categories DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/STRUCTURED_OUTPUT/MCP, referenced by 4 next question(s), found in 2 source(s). STATUS DISCOVERED, AUTHORITY NONE
- **OBX-DKSC-0929201853-03** DKSC-0929201853-004-anthropics-skills-docx | anthropics/skills/docx | AGENT_SKILL - relevance 13, E3_PRIMARY_DOC_AND_MANIFEST_READ, categories DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/CONVERSION/AGENT_SKILL, referenced by 3 next question(s), found in 1 source(s). STATUS DISCOVERED, AUTHORITY NONE

## Self test

| Test | Check | Result | Detail |
|---|---|---|---|
| TEST 1 | natural-language question accepted | **PASS** | question via cli --question; concepts=['pdf', 'document', 'spreadsheet', 'catalog', 'extract', 'structured_data', 'automation', 'agent_skill', 'code_tool', 'open_source']; free=[] |
| TEST 2 | search queries generated | **PASS** | CORE_QUERY='pdf document excel extract extraction structured data', 25 technical terms |
| TEST 3 | >=5 real public-source candidates | **PASS** | 15 capabilities backed by successful fetches in this run (69/90 requests ok) |
| TEST 4 | source URL kept | **PASS** | 15/15 records have http(s) SOURCE_URL |
| TEST 5 | capability records created (full schema) | **PASS** | 15 records x 22 required fields |
| TEST 6 | deduplication performed | **PASS** | raw 62 -> groups 59 (merged 3), possible duplicates 0, pairwise comparisons 1711 |
| TEST 7 | >=5 next questions | **PASS** | 8 generated |
| TEST 8 | next search keywords generated | **PASS** | all 5 keyword channels filled for 8/8 questions |
| TEST 9 | OUTBOX candidates generated | **PASS** | 3 candidates, all STATUS=DISCOVERED AUTHORITY=NONE |

## Errors

- F021 S2_GITHUB_SEARCH_API https://api.github.com/search/repositories?q=pdf%20document%20excel%20spreadsheet%20extract&per_page=20 -> 403 HTTP_403 ({"message":"This GitHub API path is not available: sessions are bound to their configured repositories. Use repository-scoped endpoints (repos/{owner}/{repo}/..)
- F037 S6_PYPI_SEARCH https://pypi.org/search/?q=pdf%20extract%20structured%20data -> 200 BOT_CHALLENGE_NOT_BYPASSED (Client Challenge #loading-error { font-size: 16px; font-family: 'Inter', sans-serif; margin-top: 10px; margin-left: 10px; display: none; } JavaScript is disable)
- 19 expected misses: optional files probed while reading (SKILL.md / package.json / pyproject.toml / LICENSE) returned 404; listed in the fetch log below

## Limitations

- Question decomposition and keyword generation use a fixed bilingual lexicon, not an LLM. Words outside it fall back to raw English keywords; unmapped Korean words are only reported.
- Relevance is keyword matching on names/descriptions; it does not prove the tool works. No candidate was installed or run.
- GitHub search API, repository metadata (stars, last commit) and code search are not reachable from this environment; GitHub coverage comes from curated lists + raw files, so LAST_UPDATED is UNKNOWN for GitHub-only records.
- The MCP registry search matches server *names* only, so tools whose names lack the search words are missed.
- INPUT/OUTPUT/API/AUTH/COST/NETWORK fields are detected from text; UNKNOWN means the text did not say, not 'no'.
- Curated lists are community-maintained and may be stale; listing presence is not an endorsement.
- Per-source caps and the 15-record ceiling mean the result is a sample, not a census.

## Fetch log (evidence)

| ID | Stage | Source | Status | Bytes | sha256[:16] | URL |
|---|---|---|---|---|---|---|
| F001 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 2213 | 9bafecba8a8fd0a4 | https://raw.githubusercontent.com/anthropics/skills/main/.claude-plugin/marketplace.json |
| F002 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 8598 | 6712b39718fe8150 | https://raw.githubusercontent.com/anthropics/skills/main/skills/xlsx/SKILL.md |
| F003 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 6911 | 8017469ea95fb7d2 | https://raw.githubusercontent.com/anthropics/skills/main/skills/docx/SKILL.md |
| F004 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 20796 | a7ff03e2c85b636f | https://raw.githubusercontent.com/anthropics/skills/main/skills/pptx/SKILL.md |
| F005 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 8072 | 9f78b8359fbd4943 | https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md |
| F006 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 19769 | 3bc4092c09804853 | https://raw.githubusercontent.com/anthropics/skills/main/skills/algorithmic-art/SKILL.md |
| F007 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 2235 | 1120b3769e2985ce | https://raw.githubusercontent.com/anthropics/skills/main/skills/brand-guidelines/SKILL.md |
| F008 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 11939 | a1f288079624402f | https://raw.githubusercontent.com/anthropics/skills/main/skills/canvas-design/SKILL.md |
| F009 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 15815 | 2e47d78846faeea4 | https://raw.githubusercontent.com/anthropics/skills/main/skills/doc-coauthoring/SKILL.md |
| F010 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 9390 | d91970639e9f5c37 | https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md |
| F011 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 1511 | 067b7587a344a928 | https://raw.githubusercontent.com/anthropics/skills/main/skills/internal-comms/SKILL.md |
| F012 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 9092 | 0f4592dcb53cf2b5 | https://raw.githubusercontent.com/anthropics/skills/main/skills/mcp-builder/SKILL.md |
| F013 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 33168 | dcd4803e61e913e6 | https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md |
| F014 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 7841 | 2efca615ce55a3ed | https://raw.githubusercontent.com/anthropics/skills/main/skills/slack-gif-creator/SKILL.md |
| F015 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 3124 | c35893e221e28895 | https://raw.githubusercontent.com/anthropics/skills/main/skills/theme-factory/SKILL.md |
| F016 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 3087 | 81c5002c6643b0de | https://raw.githubusercontent.com/anthropics/skills/main/skills/web-artifacts-builder/SKILL.md |
| F017 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 3913 | 51b7349e77ec63b7 | https://raw.githubusercontent.com/anthropics/skills/main/skills/webapp-testing/SKILL.md |
| F018 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 101724 | 9aac10d9ffb8778c | https://raw.githubusercontent.com/anthropics/skills/main/skills/claude-api/SKILL.md |
| F019 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 7755 | f27992510c051355 | https://raw.githubusercontent.com/anthropics/skills/main/skills/academy-guide/SKILL.md |
| F020 | collect | S1_ANTHROPIC_OFFICIAL_SKILLS | 200 | 10592 | 9191177c4a8ef11a | https://raw.githubusercontent.com/anthropics/skills/main/skills/discernment-nudge/SKILL.md |
| F021 | collect | S2_GITHUB_SEARCH_API | 403 | 249 | 7616419b9bf270d6 | https://api.github.com/search/repositories?q=pdf%20document%20excel%20spreadsheet%20extract&per_page=20 |
| F022 | collect | S3_GITHUB_CURATED_LISTS | 200 | 40668 | e693f2701840f26f | https://raw.githubusercontent.com/ComposioHQ/awesome-claude-skills/HEAD/README.md |
| F023 | collect | S3_GITHUB_CURATED_LISTS | 200 | 21783 | b15fa837edeb632f | https://raw.githubusercontent.com/travisvn/awesome-claude-skills/HEAD/README.md |
| F024 | collect | S3_GITHUB_CURATED_LISTS | 200 | 222911 | c3bb1c2b4380c5d7 | https://raw.githubusercontent.com/VoltAgent/awesome-agent-skills/HEAD/README.md |
| F025 | collect | S3_GITHUB_CURATED_LISTS | 200 | 1364081 | 86e1898becee0e0d | https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/HEAD/README.md |
| F026 | collect | S4_OFFICIAL_MCP_REGISTRY | 200 | 88782 | 75af6beb840fbe29 | https://registry.modelcontextprotocol.io/v0/servers?search=pdf&version=latest&limit=100 |
| F027 | collect | S4_OFFICIAL_MCP_REGISTRY | 200 | 31845 | 2551d69bb3f43b91 | https://registry.modelcontextprotocol.io/v0/servers?search=document&version=latest&limit=100 |
| F028 | collect | S4_OFFICIAL_MCP_REGISTRY | 200 | 12932 | 4ffd808b321a1f31 | https://registry.modelcontextprotocol.io/v0/servers?search=excel&version=latest&limit=100 |
| F029 | collect | S4_OFFICIAL_MCP_REGISTRY | 200 | 74165 | 7b2d00d5733c1f6c | https://registry.modelcontextprotocol.io/v0/servers?search=catalog&version=latest&limit=100 |
| F030 | collect | S4_OFFICIAL_MCP_REGISTRY | 200 | 46748 | c8d023388f0d21db | https://registry.modelcontextprotocol.io/v0/servers?search=extract&version=latest&limit=100 |
| F031 | collect | S4_OFFICIAL_MCP_REGISTRY | 200 | 43428 | 95c3d027d4075517 | https://registry.modelcontextprotocol.io/v0/servers?search=ocr&version=latest&limit=100 |
| F032 | collect | S7_OFFICIAL_DOCUMENTATION | 200 | 50458 | 1abbe03e4a4fdb98 | https://code.claude.com/docs/llms.txt |
| F033 | collect | S7_OFFICIAL_DOCUMENTATION | 200 | 69795 | fcbcbc2ca4fe2291 | https://platform.claude.com/llms.txt |
| F034 | collect | S5_NPM_REGISTRY | 200 | 23501 | aad07ee8edff2a47 | https://registry.npmjs.org/-/v1/search?text=pdf%20extract%20structured%20data&size=20 |
| F035 | collect | S5_NPM_REGISTRY | 200 | 21349 | ac05036e644c3e28 | https://registry.npmjs.org/-/v1/search?text=keywords%3Amcp%20pdf%20extract&size=20 |
| F036 | collect | S5_NPM_REGISTRY | 200 | 21388 | e9ef2ebe4543f87d | https://registry.npmjs.org/-/v1/search?text=document%20extract%20structured%20data&size=20 |
| F037 | collect | S6_PYPI_SEARCH | 200 | 3038 | 32ed63159c77e21e | https://pypi.org/search/?q=pdf%20extract%20structured%20data |
| F038 | collect | S8_CLAUDE_PLUGIN_DIRECTORY | 200 | 552250 | 5d11b9f340ae038d | https://claude.com/plugins |
| F039 | read | READ | 200 | 6169 | 73f9c3173067adfb | https://raw.githubusercontent.com/koraynar/doc-extract-mcp/HEAD/README.md |
| F040 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/koraynar/doc-extract-mcp/HEAD/SKILL.md |
| F041 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/koraynar/doc-extract-mcp/HEAD/package.json |
| F042 | read | READ | 200 | 1302 | e149cb088c957db4 | https://raw.githubusercontent.com/koraynar/doc-extract-mcp/HEAD/pyproject.toml |
| F043 | read | READ | 200 | 1066 | 67256dd7ad42f590 | https://raw.githubusercontent.com/koraynar/doc-extract-mcp/HEAD/LICENSE |
| F044 | read | READ | 200 | 10346 | 2524011558e3ee9d | https://raw.githubusercontent.com/PSPDFKit-labs/nutrient-agent-skill/HEAD/README.md |
| F045 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/PSPDFKit-labs/nutrient-agent-skill/HEAD/SKILL.md |
| F046 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/PSPDFKit-labs/nutrient-agent-skill/HEAD/package.json |
| F047 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/PSPDFKit-labs/nutrient-agent-skill/HEAD/pyproject.toml |
| F048 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/PSPDFKit-labs/nutrient-agent-skill/HEAD/LICENSE |
| F049 | read | READ | 200 | 37588 | 88fcc3e6ec5810d4 | https://raw.githubusercontent.com/chrisryugj/kordoc/HEAD/README.md |
| F050 | read | READ | 200 | 3654 | 81293d948fb6853f | https://registry.npmjs.org/kordoc/latest |
| F051 | read | READ | 200 | 1467 | 79f6d8f5b427252f | https://raw.githubusercontent.com/anthropics/skills/main/skills/docx/LICENSE.txt |
| F052 | read | READ | 200 | 7482 | 1321e8b63dcf0ac1 | https://raw.githubusercontent.com/fashionmascherine-svg/document-to-json-mcp/HEAD/README.md |
| F053 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/fashionmascherine-svg/document-to-json-mcp/HEAD/SKILL.md |
| F054 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/fashionmascherine-svg/document-to-json-mcp/HEAD/package.json |
| F055 | read | READ | 200 | 596 | 7ea289ca10b5e974 | https://raw.githubusercontent.com/fashionmascherine-svg/document-to-json-mcp/HEAD/pyproject.toml |
| F056 | read | READ | 200 | 1072 | d36b9755859fc256 | https://raw.githubusercontent.com/fashionmascherine-svg/document-to-json-mcp/HEAD/LICENSE |
| F057 | read | READ | 200 | 13196 | b2ef484b69ba39f8 | https://raw.githubusercontent.com/drolosoft/go-docs-mcp/HEAD/README.md |
| F058 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/drolosoft/go-docs-mcp/HEAD/SKILL.md |
| F059 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/drolosoft/go-docs-mcp/HEAD/package.json |
| F060 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/drolosoft/go-docs-mcp/HEAD/pyproject.toml |
| F061 | read | READ | 200 | 1066 | 289bff2cd2f7712c | https://raw.githubusercontent.com/drolosoft/go-docs-mcp/HEAD/LICENSE |
| F062 | read | READ | 200 | 9609 | 600a88dc026bd5ce | https://raw.githubusercontent.com/lfnovo/content-core/HEAD/README.md |
| F063 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/lfnovo/content-core/HEAD/SKILL.md |
| F064 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/lfnovo/content-core/HEAD/package.json |
| F065 | read | READ | 200 | 2231 | 69d2a9362fca8f16 | https://raw.githubusercontent.com/lfnovo/content-core/HEAD/pyproject.toml |
| F066 | read | READ | 200 | 1066 | 9b28f4cf64f8a889 | https://raw.githubusercontent.com/lfnovo/content-core/HEAD/LICENSE |
| F067 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/opendatalab/MinerU-Ecosystem/main/mcp/SKILL.md |
| F068 | read | READ | 200 | 5682 | 5eba13aebd685434 | https://raw.githubusercontent.com/opendatalab/MinerU-Ecosystem/main/mcp/README.md |
| F069 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/opendatalab/MinerU-Ecosystem/main/mcp/LICENSE.txt |
| F070 | read | READ | 200 | 11357 | c71d239df91726fc | https://raw.githubusercontent.com/opendatalab/MinerU-Ecosystem/main/LICENSE |
| F071 | read | READ | 200 | 11548 | 9fe722e1c937bfcb | https://raw.githubusercontent.com/linxule/mineru-mcp/HEAD/README.md |
| F072 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/linxule/mineru-mcp/HEAD/SKILL.md |
| F073 | read | READ | 200 | 1542 | bd433510d4bfaf64 | https://raw.githubusercontent.com/linxule/mineru-mcp/HEAD/package.json |
| F074 | read | READ | 200 | 1070 | 5b305ca6094cb2ff | https://raw.githubusercontent.com/linxule/mineru-mcp/HEAD/LICENSE |
| F075 | read | READ | 200 | 19391 | 713d3a2aa806791b | https://raw.githubusercontent.com/pdf4me/pdf4me-mcp/HEAD/README.md |
| F076 | read | READ | 200 | 33404 | 3aa744f8f54881c5 | https://pypi.org/pypi/pdf4me-mcp/json |
| F077 | read | READ | 200 | 5401 | a796ece86873d695 | https://raw.githubusercontent.com/BiGapi-2026/bigapi-mcp/HEAD/README.md |
| F078 | read | READ | 200 | 1904 | 5d0838c9f6b4ffd0 | https://registry.npmjs.org/@bigapi%2Fmcp/latest |
| F079 | read | READ | 200 | 29519 | 8e723b017d86cf80 | https://raw.githubusercontent.com/PSPDFKit/nutrient-dws-mcp-server/HEAD/README.md |
| F080 | read | READ | 200 | 3291 | eba20f1037ee37ae | https://registry.npmjs.org/@nutrient-sdk%2Fdws-mcp-server/latest |
| F081 | read | READ | 200 | 5323 | deaf2eeed89758ce | https://raw.githubusercontent.com/flexorch/flexorch-mcp/HEAD/README.md |
| F082 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/flexorch/flexorch-mcp/HEAD/SKILL.md |
| F083 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/flexorch/flexorch-mcp/HEAD/package.json |
| F084 | read | READ | 200 | 1519 | 58eac41449279ea8 | https://raw.githubusercontent.com/flexorch/flexorch-mcp/HEAD/pyproject.toml |
| F085 | read | READ | 200 | 1065 | ecbb578ddfb735b4 | https://raw.githubusercontent.com/flexorch/flexorch-mcp/HEAD/LICENSE |
| F086 | read | READ | 200 | 17561 | 2d4124a9e5fd39ea | https://raw.githubusercontent.com/Zacccck/Claude-MCP-Read-Email-Attachments/HEAD/README.md |
| F087 | read | READ | 404 | 14 | d5558cd419c8d46b | https://raw.githubusercontent.com/Zacccck/Claude-MCP-Read-Email-Attachments/HEAD/SKILL.md |
| F088 | read | READ | 200 | 1937 | 3d9435c3070dc2e7 | https://raw.githubusercontent.com/Zacccck/Claude-MCP-Read-Email-Attachments/HEAD/package.json |
| F089 | read | READ | 200 | 1064 | b928f58406887517 | https://raw.githubusercontent.com/Zacccck/Claude-MCP-Read-Email-Attachments/HEAD/LICENSE |
| F090 | read | READ | 200 | 1467 | 79f6d8f5b427252f | https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/LICENSE.txt |
