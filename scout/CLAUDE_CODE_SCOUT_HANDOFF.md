# CLAUDE CODE SCOUT - HANDOFF

LOT: DKSC-CLAUDE-CODE-SCOUT-001 | MODE: BUILD + RUN + EVIDENCE | AUTHORITY: NONE | generated 2026-09-29T20:19:39+00:00

## EXECUTIVE SUMMARY

- CLAUDE_CODE_SCOUT_STATUS: **PASS** (primary run `DKSC-0929201853`)
- One Korean question went in. The program built its own search terms, called 90 public URLs (69 ok) across 6 reachable sources, kept 62 raw candidates, merged duplicates into 59 groups, read 15 of them, and wrote 15 capability records.
- It then produced 8 next research questions with 5 keyword channels each, and 3 OUTBOX candidates (STATUS DISCOVERED, AUTHORITY NONE).
- Loop check: next question #3 was fed back as a new input (run `DKSC-0929201919`): PASS, 15 records, 7 new questions. Closed loop demonstrated.
- Nothing was installed, executed, purchased, posted, or authenticated. Nothing is VERIFIED; everything is DISCOVERED.

## WHAT WAS BUILT

- `scout/scout.py` - one Python 3 file, standard library only (2205 lines). Pipeline: QUESTION -> lexicon decomposition (OBJECT/ACTION/OUTPUT/CONTEXT) -> queries -> 7 source collectors + 1 probe -> relevance gate -> dedup pass 1 -> balanced selection (target 10, max 15) -> source read -> normalize (22-field schema) -> dedup pass 2 -> classify -> dream fit -> next questions -> keyword channels -> OUTBOX -> self test -> files.
- Network door: one `Fetcher` class. GET only, host allowlist, no auth headers, request budget 180, every request logged with status, bytes and sha256 prefix.
- `python3 scout.py handoff ...` regenerates this file from the run folders.

## WHAT ACTUALLY RAN

- `python3 scout.py run --question 'PDF, 문서, Excel 또는 카탈로그에서 구조화된 데이터를 자동 추출하는 데 사용할 수 있는 공개 Skill 또는 코드 도구를 찾아줘.' --out runs/001` at 2026-09-29T20:18:53+00:00 (KST 2026-09-30T05:18:53+09:00), 19.1 s, 90 requests -> `runs/001` -> **PASS**
- `python3 scout.py run --from-next runs/001/next_questions.json --pick 3 --out runs/002` at 2026-09-29T20:19:19+00:00 (KST 2026-09-30T05:19:19+09:00), 19.7 s, 90 requests -> `runs/002` -> **PASS**

## INPUT

> PDF, 문서, Excel 또는 카탈로그에서 구조화된 데이터를 자동 추출하는 데 사용할 수 있는 공개 Skill 또는 코드 도구를 찾아줘.

## GENERATED SEARCH QUERIES

- OBJECT: PDF (`pdf`), 문서 (`문서`), Excel/스프레드시트 (`excel`), 카탈로그 (`카탈로그`)
- ACTION: 추출 (`추출`)
- OUTPUT: 구조화된 데이터 (`구조화`)
- CONTEXT: 자동화 (`자동`), Agent Skill (`skill`), 코드 도구 (`코드`), 공개/오픈소스 (`공개`)
- implied: table, ocr, product, json
- CORE_QUERY: `pdf document excel extract extraction structured data`
- GITHUB_QUERY: `(pdf OR document OR excel OR spreadsheet) (extract OR extraction OR parse) "structured data" in:name,description,readme`
- SKILL_QUERY: `SKILL.md pdf document extract structured data`
- MCP_QUERY: `mcp server pdf document extract structured data`
- NPM_QUERIES: `pdf extract structured data`, `keywords:mcp pdf extract`, `document extract structured data`
- MCP_REGISTRY_TERMS: pdf, document, excel, catalog, extract, ocr
- TECHNICAL_TERMS: pdf parsing, pdf text extraction, document parsing, intelligent document processing, document ai, xlsx, csv, tabular data, product catalog, product data extraction, product feed, data extraction, information extraction, structured output, json schema extraction, automation pipeline, SKILL.md, python library, cli tool, table extraction, table detection, optical character recognition, product information, product attributes, json output

## SOURCES ACCESSED

| Priority | Source | Status | Requests | Kept | Reason |
|---|---|---|---|---|---|
| 1 | Anthropic official Skills repository (anthropics/skills) | **PASS** | 20 | 2 | 20/20 requests ok; 2 relevant candidates kept |
| 2 | GitHub public repository search (REST API, unauthenticated) | **HOLD** | 1 | 0 | HOLD_POLICY: this execution environment scopes api.github.com to its configured repositories; public search not reachable without widening access. Not bypassed. |
| 3 | Public GitHub curated lists of Skills / MCP servers (raw README) | **PASS** | 4 | 20 | 4/4 requests ok; 20 relevant candidates kept |
| 3 | Official MCP Registry (registry.modelcontextprotocol.io) | **PASS** | 6 | 20 | 6/6 requests ok; 20 relevant candidates kept |
| 4 | Official Claude documentation indexes (llms.txt) | **PARTIAL** | 2 | 0 | 2/2 requests ok; 0 relevant candidates kept |
| 5 | npm public registry search API | **PASS** | 3 | 20 | 3/3 requests ok; 20 relevant candidates kept |
| 5 | PyPI search (no JSON search API exists; HTML listing) | **HOLD** | 1 | 0 | HOLD: PyPI search answers with a JavaScript client challenge; not bypassed. PyPI JSON API is still used for per-package metadata. |
| 5 | Claude plugin / connector directory (web) | **PARTIAL** | 1 | 0 | HTTP 200 (https://claude.com/marketplace/plugins) but no public machine-readable listing; HTML not scraped (machine-first rule) |

## CAPABILITIES FOUND

### DKSC-0929201853-001-koraynar-doc-extract-mcp - koraynar/doc-extract-mcp

- TYPE: MCP_SERVER
- PROVIDER: koraynar
- SOURCE_URL: https://github.com/koraynar/doc-extract-mcp
- REPOSITORY_URL: https://github.com/koraynar/doc-extract-mcp
- DESCRIPTION: Document extraction tooling: read PDFs, text, CSV and JSON, inspect metadata, chunk long documents, validate against JSON Schema and write JSON/CSV output.
- USE_CASE: PDF/문서/Excel/스프레드시트 -> 추출 -> 구조화된 데이터/JSON
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, CSV
- OUTPUT: TEXT, JSON
- TOOLS: UNKNOWN
- API: UNKNOWN
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: UNKNOWN
- AUTH_REQUIRED: UNKNOWN
- COST: FREE_MENTIONED
- LICENSE: MIT
- LAST_UPDATED: 2026-08-28T17:56:15.763331Z
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, SPREADSHEET, STRUCTURED_OUTPUT, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS, S4_OFFICIAL_MCP_REGISTRY; 1 duplicate listing(s) merged by shared repository/package key
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-015-anthropics-skills-pdf (anthropics/skills/pdf) adds AGENT_SKILL+OCR+TABLE_EXTRACTION; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds OCR+TABLE_EXTRACTION; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F030, F039, F042, F043

### DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski - PSPDFKit-labs/nutrient-agent-skill

- TYPE: MCP_SERVER
- PROVIDER: PSPDFKit-labs
- SOURCE_URL: https://github.com/PSPDFKit-labs/nutrient-agent-skill
- REPOSITORY_URL: https://github.com/PSPDFKit-labs/nutrient-agent-skill
- DESCRIPTION: Document processing with Nutrient DWS API: convert (PDF/DOCX/XLSX/PPTX/HTML/images), extract text/tables, OCR (20+ languages), redact PII (pattern + AI), watermark, digital signatures, form filling. MCP server also available.
- USE_CASE: PDF/문서/Excel/스프레드시트 -> 추출/OCR -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, DOCX/Word, XLSX/Excel, PPTX, IMAGE, HTML/URL
- OUTPUT: PDF, EXCEL
- TOOLS: UNKNOWN
- API: YES - keys: NUTRIENT_API_KEY; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - NUTRIENT_API_KEY
- COST: PAID_OR_METERED_MENTIONED
- LICENSE: UNKNOWN
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E2_PRIMARY_DOC_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, OCR, TABLE_EXTRACTION, SPREADSHEET, CONVERSION, WEB_EXTRACTION, FORMS, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds STRUCTURED_OUTPUT; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL; DKSC-0929201853-005-document-to-json-pdf-invoice-sta (Document to JSON – PDF Invoice/Statement/Contract Parser) adds STRUCTURED_OUTPUT
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, CONTENT_PRODUCTION, COMMERCE, RESEARCH (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F024, F044

### DKSC-0929201853-003-kordoc - kordoc

- TYPE: MCP_SERVER
- PROVIDER: chrisryugj
- SOURCE_URL: https://www.npmjs.com/package/kordoc
- REPOSITORY_URL: https://github.com/chrisryugj/kordoc
- DESCRIPTION: Parse Korean documents (HWP3-5, HWPX, HWPML, PDF, XLS(X), DOCX) to Markdown — CLI + MCP server with lossless patch/roundtrip, form-filler, document diff, print & layout-preserving SVG renderer
- USE_CASE: PDF/문서/Excel/스프레드시트 -> 추출/OCR -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, DOCX/Word
- OUTPUT: MARKDOWN
- TOOLS: kordoc, cfb, zod, jszip, commander, markdown-it, @xmldom/xmldom, @modelcontextprotocol/sdk
- API: UNKNOWN
- MCP: YES
- CODE_EXECUTION: YES - installable package runs locally (not executed in this pilot)
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: CLAIMS_LOCAL - text states local/offline processing
- AUTH_REQUIRED: UNKNOWN
- COST: UNKNOWN
- LICENSE: MIT
- LAST_UPDATED: 2026-09-29T18:41:40.427Z
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, CONVERSION, FORMS, MCP, DEVELOPER_TOOL
- DEDUP: UNIQUE - found in S5_NPM_REGISTRY
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds SPREADSHEET+STRUCTURED_OUTPUT; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds OCR+SPREADSHEET; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL+SPREADSHEET
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, CONTENT_PRODUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F035, F049, F050

### DKSC-0929201853-004-anthropics-skills-docx - anthropics/skills/docx

- TYPE: AGENT_SKILL
- PROVIDER: anthropics
- SOURCE_URL: https://github.com/anthropics/skills/tree/main/skills/docx
- REPOSITORY_URL: https://github.com/anthropics/skills
- DESCRIPTION: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files) or Word templates (.dotx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', '.dotx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx or .dotx files, inserting or replacing images in documents, performing find-and-replace in Wor…
- USE_CASE: PDF/문서/Excel/스프레드시트 -> 추출 -> -
- TRIGGER: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files) or Word templates (.dotx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', '.dotx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from…
- INPUT: PDF, DOCX/Word, IMAGE
- OUTPUT: WORD
- TOOLS: docx
- API: UNKNOWN
- MCP: NOT_DETECTED
- CODE_EXECUTION: YES - SKILL.md instructs running code
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: UNKNOWN
- AUTH_REQUIRED: NO_EVIDENCE_OF_AUTH - SKILL.md mentions no key
- COST: UNKNOWN
- LICENSE: Proprietary. LICENSE.txt has complete terms
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, SPREADSHEET, CONVERSION, AGENT_SKILL
- DEDUP: UNIQUE - found in S1_ANTHROPIC_OFFICIAL_SKILLS
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds MCP+OCR+TABLE_EXTRACTION; DKSC-0929201853-005-document-to-json-pdf-invoice-sta (Document to JSON – PDF Invoice/Statement/Contract Parser) adds MCP+OCR+STRUCTURED_OUTPUT; DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds MCP+STRUCTURED_OUTPUT
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, CONTENT_PRODUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F001, F003, F051

### DKSC-0929201853-005-document-to-json-pdf-invoice-sta - Document to JSON – PDF Invoice/Statement/Contract Parser

- TYPE: MCP_SERVER
- PROVIDER: fashionmascherine-svg
- SOURCE_URL: https://registry.modelcontextprotocol.io/v0/servers?search=io.github.fashionmascherine-svg/document-to-json-mcp&version=latest
- REPOSITORY_URL: https://github.com/fashionmascherine-svg/document-to-json-mcp
- DESCRIPTION: Turn any PDF into structured JSON via AI + OCR: invoices, bank statements, contracts.
- USE_CASE: PDF/문서 -> 추출/OCR -> 구조화된 데이터/JSON
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF
- OUTPUT: JSON
- TOOLS: apify_client
- API: YES - keys: APIFY_TOKEN; remote endpoint: https://mcp.apify.com/?actors=opportunity-biz/document-to-json-mcp; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: NO_LOCAL - hosted remote MCP (runs on provider side)
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - APIFY_TOKEN
- COST: PAID_OR_METERED_MENTIONED + FREE_MENTIONED
- LICENSE: MIT
- LAST_UPDATED: 2026-06-24T17:38:23.829707Z
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, OCR, STRUCTURED_OUTPUT, INVOICE_RECEIPT, MCP
- DEDUP: UNIQUE - found in S4_OFFICIAL_MCP_REGISTRY
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds SPREADSHEET+TABLE_EXTRACTION; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL+SPREADSHEET; DKSC-0929201853-015-anthropics-skills-pdf (anthropics/skills/pdf) adds AGENT_SKILL+TABLE_EXTRACTION
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F027, F052, F055, F056

### DKSC-0929201853-006-drolosoft-go-docs-mcp - drolosoft/go-docs-mcp

- TYPE: MCP_SERVER
- PROVIDER: drolosoft
- SOURCE_URL: https://github.com/drolosoft/go-docs-mcp
- REPOSITORY_URL: https://github.com/drolosoft/go-docs-mcp
- DESCRIPTION: Read, search, OCR and extract from PDF, TXT, Markdown, DOCX, CSV and image files, with caching and directory confinement.
- USE_CASE: PDF/문서/Excel/스프레드시트 -> 추출/OCR -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, DOCX/Word, CSV, IMAGE
- OUTPUT: STRUCTURED DATA, MARKDOWN
- TOOLS: UNKNOWN
- API: UNKNOWN
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: CLAIMS_LOCAL - text states local/offline processing
- AUTH_REQUIRED: UNKNOWN
- COST: FREE_MENTIONED
- LICENSE: MIT
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, OCR, SPREADSHEET, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-015-anthropics-skills-pdf (anthropics/skills/pdf) adds AGENT_SKILL+TABLE_EXTRACTION; DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds STRUCTURED_OUTPUT; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds TABLE_EXTRACTION
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F057, F061

### DKSC-0929201853-007-lfnovo-content-core - lfnovo/content-core

- TYPE: MCP_SERVER
- PROVIDER: lfnovo
- SOURCE_URL: https://github.com/lfnovo/content-core
- REPOSITORY_URL: https://github.com/lfnovo/content-core
- DESCRIPTION: Extract content from web pages, PDFs, Word documents, YouTube transcripts, audio and video with automatic engine selection and structured JSON output.
- USE_CASE: PDF/문서 -> 추출 -> 구조화된 데이터/JSON
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, DOCX/Word, HTML/URL, AUDIO
- OUTPUT: PLAIN TEXT
- TOOLS: content_core, content-core
- API: YES - keys: OPENAI_API_KEY, CRAWL4AI_API_TOKEN, FIRECRAWL_API_KEY, JINA_API_KEY
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - OPENAI_API_KEY, CRAWL4AI_API_TOKEN, FIRECRAWL_API_KEY, JINA_API_KEY
- COST: UNKNOWN
- LICENSE: MIT
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, STRUCTURED_OUTPUT, AUTOMATION, WEB_EXTRACTION, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds OCR+SPREADSHEET; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL+SPREADSHEET; DKSC-0929201853-006-drolosoft-go-docs-mcp (drolosoft/go-docs-mcp) adds OCR+SPREADSHEET
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, COMMERCE, RESEARCH (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F062, F065, F066

### DKSC-0929201853-008-opendatalab-mineru-ecosystem - opendatalab/MinerU-Ecosystem

- TYPE: MCP_SERVER
- PROVIDER: opendatalab
- SOURCE_URL: https://github.com/opendatalab/MinerU-Ecosystem/tree/main/mcp
- REPOSITORY_URL: https://github.com/opendatalab/MinerU-Ecosystem
- DESCRIPTION: Convert PDFs, Word and PowerPoint files, images and spreadsheets to Markdown via the MinerU document parsing API.
- USE_CASE: PDF/문서/Excel/스프레드시트 -> 추출 -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, PPTX, IMAGE
- OUTPUT: MARKDOWN
- TOOLS: UNKNOWN
- API: YES - keys: MINERU_API_TOKEN; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - MINERU_API_TOKEN
- COST: FREE_MENTIONED
- LICENSE: Apache-2.0
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, SPREADSHEET, CONVERSION, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-015-anthropics-skills-pdf (anthropics/skills/pdf) adds AGENT_SKILL+OCR+TABLE_EXTRACTION; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds OCR+TABLE_EXTRACTION; DKSC-0929201853-005-document-to-json-pdf-invoice-sta (Document to JSON – PDF Invoice/Statement/Contract Parser) adds OCR+STRUCTURED_OUTPUT
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, CONTENT_PRODUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F068, F070

### DKSC-0929201853-009-linxule-mineru-mcp - linxule/mineru-mcp

- TYPE: MCP_SERVER
- PROVIDER: linxule
- SOURCE_URL: https://github.com/linxule/mineru-mcp
- REPOSITORY_URL: https://github.com/linxule/mineru-mcp
- DESCRIPTION: Parse PDFs, images, DOCX and PPTX via the MinerU document parsing API, with multilingual OCR, batch processing, page ranges and local file upload.
- USE_CASE: PDF/문서 -> 추출/OCR -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, DOCX/Word, PPTX, IMAGE
- OUTPUT: UNKNOWN
- TOOLS: mineru-mcp, @modelcontextprotocol/sdk, axios, express, zod
- API: YES - keys: MINERU_API_KEY; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - MINERU_API_KEY
- COST: UNKNOWN
- LICENSE: MIT
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, OCR, AUTOMATION, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds SPREADSHEET+STRUCTURED_OUTPUT; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds SPREADSHEET+TABLE_EXTRACTION; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL+SPREADSHEET
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F071, F073, F074

### DKSC-0929201853-010-pdf4me - PDF4me

- TYPE: MCP_SERVER
- PROVIDER: pdf4me
- SOURCE_URL: https://registry.modelcontextprotocol.io/v0/servers?search=io.github.pdf4me/pdf4me-mcp&version=latest
- REPOSITORY_URL: https://github.com/pdf4me/pdf4me-mcp
- DESCRIPTION: PDF & document automation via the PDF4me API — convert, OCR, extract, edit, secure.
- USE_CASE: PDF/문서 -> 추출/OCR -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF
- OUTPUT: PDF, WORD, EXCEL
- TOOLS: pdf4me-mcp
- API: YES - keys: PDF4ME_API_KEY; remote endpoint: https://mcp.pdf4me.com/mcp; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: YES - installable package runs locally (not executed in this pilot)
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - PDF4ME_API_KEY
- COST: PAID_OR_METERED_MENTIONED
- LICENSE: MIT
- LAST_UPDATED: 2026-07-10T14:37:35.504699Z
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, OCR, CONVERSION, AUTOMATION, MCP
- DEDUP: UNIQUE - found in S4_OFFICIAL_MCP_REGISTRY
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds SPREADSHEET+STRUCTURED_OUTPUT; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds SPREADSHEET+TABLE_EXTRACTION; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL+SPREADSHEET
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, CONTENT_PRODUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F026, F075, F076

### DKSC-0929201853-011-bigapi-mcp - @bigapi/mcp

- TYPE: MCP_SERVER
- PROVIDER: BiGapi-2026
- SOURCE_URL: https://www.npmjs.com/package/@bigapi/mcp
- REPOSITORY_URL: https://github.com/BiGapi-2026/bigapi-mcp
- DESCRIPTION: MCP server for bigapi.dev - the output layer for AI agents: turn what an agent produced into a finished file, and read files back in. $0.01 per operation.
- USE_CASE: PDF/문서 -> 추출/OCR -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: UNKNOWN
- OUTPUT: MARKDOWN, PDF, WORD
- TOOLS: zod, @modelcontextprotocol/sdk
- API: YES - keys: BIGAPI_KEY; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: YES - installable package runs locally (not executed in this pilot)
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - BIGAPI_KEY
- COST: PAID_OR_METERED_MENTIONED + FREE_MENTIONED
- LICENSE: MIT
- LAST_UPDATED: 2026-09-19T09:47:27.761Z
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: MCP
- DEDUP: UNIQUE - found in S5_NPM_REGISTRY
- DREAM_USE: 문서 처리 파이프라인의 보조 단계 (역할 추가 확인 필요)
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL; DKSC-0929201853-015-anthropics-skills-pdf (anthropics/skills/pdf) adds AGENT_SKILL
- POSSIBLE_VALUE: UNKNOWN (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F035, F077, F078

### DKSC-0929201853-012-pspdfkit-nutrient-dws-mcp-server - PSPDFKit/nutrient-dws-mcp-server

- TYPE: MCP_SERVER
- PROVIDER: PSPDFKit
- SOURCE_URL: https://github.com/PSPDFKit/nutrient-dws-mcp-server
- REPOSITORY_URL: https://github.com/PSPDFKit/nutrient-dws-mcp-server
- DESCRIPTION: Convert, merge, redact, sign, OCR, watermark and extract data from PDFs and Office documents via the Nutrient DWS Processor API.
- USE_CASE: PDF/문서 -> 추출/OCR -> -
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF
- OUTPUT: MARKDOWN, JSON
- TOOLS: @nutrient-sdk/dws-mcp-server, zod, open, axios, winston, form-data, @modelcontextprotocol/sdk
- API: YES - keys: NUTRIENT_DWS_API_KEY, NUTRIENT_DWS_EXTRACTION_API_KEY; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: YES - installable package runs locally (not executed in this pilot)
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - NUTRIENT_DWS_API_KEY, NUTRIENT_DWS_EXTRACTION_API_KEY
- COST: PAID_OR_METERED_MENTIONED + FREE_MENTIONED
- LICENSE: MIT
- LAST_UPDATED: 2026-08-28T00:12:12.095928Z
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, OCR, CONVERSION, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS, S4_OFFICIAL_MCP_REGISTRY; 1 duplicate listing(s) merged by shared repository/package key
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds SPREADSHEET+STRUCTURED_OUTPUT; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds SPREADSHEET+TABLE_EXTRACTION; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL+SPREADSHEET
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, CONTENT_PRODUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F026, F079, F080

### DKSC-0929201853-013-flexorch-flexorch-mcp - flexorch/flexorch-mcp

- TYPE: MCP_SERVER
- PROVIDER: flexorch
- SOURCE_URL: https://github.com/flexorch/flexorch-mcp
- REPOSITORY_URL: https://github.com/flexorch/flexorch-mcp
- DESCRIPTION: Turn business documents (PDFs, invoices, contracts, payroll) into structured datasets with classification, field extraction, PII masking and quality scoring.
- USE_CASE: PDF/문서 -> 추출 -> 구조화된 데이터
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF
- OUTPUT: STRUCTURED DATA, JSON
- TOOLS: flexorch-mcp
- API: YES - keys: FLEXORCH_API_KEY; README/description mentions an API
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: YES - remote service/API
- AUTH_REQUIRED: YES - FLEXORCH_API_KEY
- COST: PAID_OR_METERED_MENTIONED
- LICENSE: MIT
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, STRUCTURED_OUTPUT, INVOICE_RECEIPT, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds OCR+SPREADSHEET; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL+SPREADSHEET; DKSC-0929201853-006-drolosoft-go-docs-mcp (drolosoft/go-docs-mcp) adds OCR+SPREADSHEET
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F081, F084, F085

### DKSC-0929201853-014-zacccck-claude-mcp-read-email-at - Zacccck/Claude-MCP-Read-Email-Attachments

- TYPE: MCP_SERVER
- PROVIDER: Zacccck
- SOURCE_URL: https://github.com/Zacccck/Claude-MCP-Read-Email-Attachments
- REPOSITORY_URL: https://github.com/Zacccck/Claude-MCP-Read-Email-Attachments
- DESCRIPTION: Read Outlook email attachments via Microsoft Graph, parsing PDF, Word (including embedded images), Excel and text files into structured content.
- USE_CASE: PDF/Excel/스프레드시트 -> 추출 -> 구조화된 데이터
- TRIGGER: Tool call from an MCP client (tool list not introspected in this pilot)
- INPUT: PDF, XLSX/Excel, IMAGE, EMAIL
- OUTPUT: PLAIN TEXT, TEXT, CSV
- TOOLS: @azure/msal-node, @kenjiuno/msgreader, @modelcontextprotocol/sdk, 7zip-bin, adm-zip, cfb, dotenv, exceljs, mammoth, node-7z, node-unrar-js, pdf-parse
- API: UNKNOWN
- MCP: YES
- CODE_EXECUTION: UNKNOWN
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: UNKNOWN
- AUTH_REQUIRED: UNKNOWN
- COST: UNKNOWN
- LICENSE: MIT
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, SPREADSHEET, STRUCTURED_OUTPUT, MCP
- DEDUP: UNIQUE - found in S3_GITHUB_CURATED_LISTS
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-015-anthropics-skills-pdf (anthropics/skills/pdf) adds AGENT_SKILL+OCR+TABLE_EXTRACTION; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds OCR+TABLE_EXTRACTION; DKSC-0929201853-004-anthropics-skills-docx (anthropics/skills/docx) adds AGENT_SKILL
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F025, F086, F088, F089

### DKSC-0929201853-015-anthropics-skills-pdf - anthropics/skills/pdf

- TYPE: AGENT_SKILL
- PROVIDER: anthropics
- SOURCE_URL: https://github.com/anthropics/skills/tree/main/skills/pdf
- REPOSITORY_URL: https://github.com/anthropics/skills
- DESCRIPTION: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.
- USE_CASE: PDF/문서 -> 추출 -> -
- TRIGGER: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file o…
- INPUT: PDF, IMAGE, SCANNED
- OUTPUT: UNKNOWN
- TOOLS: pypdf, pdfplumber, pandas, reportlab, pytesseract, pdf2image
- API: UNKNOWN
- MCP: NOT_DETECTED
- CODE_EXECUTION: YES - SKILL.md instructs running code
- FILE_ACCESS: YES - reads user files (per text)
- NETWORK_ACCESS: UNKNOWN
- AUTH_REQUIRED: NO_EVIDENCE_OF_AUTH - SKILL.md mentions no key
- COST: UNKNOWN
- LICENSE: Proprietary. LICENSE.txt has complete terms
- LAST_UPDATED: UNKNOWN
- EVIDENCE_LEVEL: E3_PRIMARY_DOC_AND_MANIFEST_READ
- CATEGORIES: DOCUMENT_PROCESSING, DATA_EXTRACTION, OCR, TABLE_EXTRACTION, FORMS, AGENT_SKILL
- DEDUP: UNIQUE - found in S1_ANTHROPIC_OFFICIAL_SKILLS, S3_GITHUB_CURATED_LISTS; 1 duplicate listing(s) merged by shared repository/package key
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- DREAM_FACTORY_TARGET: DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인
- POSSIBLE_COMBINATION: DKSC-0929201853-001-koraynar-doc-extract-mcp (koraynar/doc-extract-mcp) adds MCP+SPREADSHEET+STRUCTURED_OUTPUT; DKSC-0929201853-014-zacccck-claude-mcp-read-email-at (Zacccck/Claude-MCP-Read-Email-Attachments) adds MCP+SPREADSHEET+STRUCTURED_OUTPUT; DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski (PSPDFKit-labs/nutrient-agent-skill) adds MCP+SPREADSHEET
- POSSIBLE_VALUE: DATA_ASSET, INTERNAL_AUTOMATION, COST_REDUCTION, COMMERCE (NOT_VERIFIED - no revenue was measured; values above are possibilities only)
- EVIDENCE fetches: F001, F005, F023, F090

## DEDUPLICATION RESULT

- raw candidates 62 -> 59 groups after pass 1 (3 merged as DUPLICATE)
- selected & read 15 -> 15 records: UNIQUE 15, POSSIBLE_DUPLICATE 0; 1711 pairwise name comparisons
- merged: koraynar/doc-extract-mcp <- R003, R024 from S3_GITHUB_CURATED_LISTS, S4_OFFICIAL_MCP_REGISTRY
- merged: PSPDFKit/nutrient-dws-mcp-server <- R010, R038 from S3_GITHUB_CURATED_LISTS, S4_OFFICIAL_MCP_REGISTRY
- merged: anthropics/skills/pdf <- R002, R012 from S1_ANTHROPIC_OFFICIAL_SKILLS, S3_GITHUB_CURATED_LISTS
- rule: pass 1: shared GitHub repo+path, npm name, PyPI name, MCP-registry name or URL -> DUPLICATE (merged)
- rule: pass 1: same repo root but different sub-project/registry server -> POSSIBLE_DUPLICATE
- rule: pass 1: same normalized name + same provider -> POSSIBLE_DUPLICATE
- rule: pass 2: same repository URL discovered while reading -> POSSIBLE_DUPLICATE
- raw-level labels: UNIQUE 59, DUPLICATE 3, POSSIBLE_DUPLICATE 0

## NEXT QUESTIONS

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

## GENERATED AI KEYWORDS

**Q1** concepts: pdf, catalog, table, scanned, extract, ocr, structured_data, json, supplier
- CORE_KEYWORDS: pdf | catalog | table | extract | extraction | structured | data | pdf parsing | pdf text extraction | product catalog | product data extraction
- GITHUB_KEYWORDS: (pdf OR catalog OR table OR scanned) (extract OR extraction OR parse) "structured data" in:name,description,readme | topic:pdf-parsing | topic:pdf-text-extraction | topic:product-catalog
- MCP_KEYWORDS: mcp server pdf catalog extract structured data | pdf | catalog | table | scan | extract | ocr
- SKILL_KEYWORDS: SKILL.md pdf catalog extract structured data | claude skill pdf catalog table
- WEB_KEYWORDS: pdf catalog extract structured data open source | claude skill pdf extract | mcp server pdf extract structured data | best pdf extract tool
- DISCOVERED_TERMS_FROM_SOURCES: pypdf | pdfplumber | pdf2image

**Q2** concepts: pdf, spreadsheet, table, extract, database, automation
- CORE_KEYWORDS: pdf | excel | spreadsheet | extract | extraction | database | pdf parsing | pdf text extraction | xlsx | csv
- GITHUB_KEYWORDS: (pdf OR excel OR spreadsheet OR table) (extract OR extraction OR parse) "database" in:name,description,readme | topic:pdf-parsing | topic:pdf-text-extraction | topic:xlsx
- MCP_KEYWORDS: mcp server pdf excel extract database | pdf | excel | table | extract | ocr
- SKILL_KEYWORDS: SKILL.md pdf excel extract database | claude skill pdf excel spreadsheet
- WEB_KEYWORDS: pdf excel extract database open source | claude skill pdf extract | mcp server pdf extract database | best pdf extract tool
- DISCOVERED_TERMS_FROM_SOURCES: -

**Q3** concepts: pdf, catalog, product, extract, structured_data, attributes, open_source
- CORE_KEYWORDS: pdf | catalog | product | extract | extraction | structured | data | pdf parsing | pdf text extraction | product catalog | product data extraction
- GITHUB_KEYWORDS: (pdf OR catalog OR product) (extract OR extraction OR parse) "structured data" in:name,description,readme | topic:pdf-parsing | topic:pdf-text-extraction | topic:product-catalog
- MCP_KEYWORDS: mcp server pdf catalog extract structured data | pdf | catalog | product | extract | ocr
- SKILL_KEYWORDS: SKILL.md pdf catalog extract structured data | claude skill pdf catalog product
- WEB_KEYWORDS: pdf catalog extract structured data open source | claude skill pdf extract | mcp server pdf extract structured data | best pdf extract tool
- DISCOVERED_TERMS_FROM_SOURCES: -

**Q4** concepts: product, image, extract
- CORE_KEYWORDS: product | image | extract | extraction | product information | product attributes | image text extraction | multimodal extraction
- GITHUB_KEYWORDS: (product OR image) (extract OR extraction OR parse) in:name,description,readme | topic:product-information | topic:product-attributes | topic:image-text-extraction
- MCP_KEYWORDS: mcp server product image extract | product | image | extract | ocr
- SKILL_KEYWORDS: SKILL.md product image extract | claude skill product image extract
- WEB_KEYWORDS: product image extract open source | claude skill product extract | mcp server product extract | best product extract tool
- DISCOVERED_TERMS_FROM_SOURCES: docx

**Q5** concepts: catalog, product, extract, structured_data, json, database, code_tool, supplier
- CORE_KEYWORDS: catalog | product | extract | extraction | structured | data | product catalog | product data extraction | product feed | product information
- GITHUB_KEYWORDS: (catalog OR product) (extract OR extraction OR parse) "structured data" in:name,description,readme | topic:product-catalog | topic:product-data-extraction | topic:product-feed
- MCP_KEYWORDS: mcp server catalog product extract structured data | catalog | product | extract | ocr
- SKILL_KEYWORDS: SKILL.md catalog product extract structured data | claude skill catalog product extract
- WEB_KEYWORDS: catalog product extract structured data open source | claude skill catalog extract | mcp server catalog extract structured data | best catalog extract tool
- DISCOVERED_TERMS_FROM_SOURCES: -

**Q6** concepts: pdf, document, extract, structured_data, automation, local
- CORE_KEYWORDS: pdf | document | extract | extraction | structured | data | api | pdf parsing | pdf text extraction | document parsing | intelligent document processing
- GITHUB_KEYWORDS: (pdf OR document) (extract OR extraction OR parse) "structured data" api in:name,description,readme | topic:pdf-parsing | topic:pdf-text-extraction | topic:document-parsing
- MCP_KEYWORDS: mcp server pdf document extract structured data | pdf | document | extract | ocr | api
- SKILL_KEYWORDS: SKILL.md pdf document extract structured data | claude skill pdf document extract
- WEB_KEYWORDS: pdf document extract structured data open source | claude skill pdf extract | mcp server pdf extract structured data | best pdf extract tool
- DISCOVERED_TERMS_FROM_SOURCES: docx

**Q7** concepts: document, extract, automation, agent_skill, mcp
- CORE_KEYWORDS: document | extract | extraction | document parsing | intelligent document processing | document ai | data extraction
- GITHUB_KEYWORDS: (document) (extract OR extraction OR parse) in:name,description,readme | topic:document-parsing | topic:intelligent-document-processing | topic:document-ai
- MCP_KEYWORDS: mcp server document extract | document | extract | ocr
- SKILL_KEYWORDS: SKILL.md document extract | claude skill document extract extraction
- WEB_KEYWORDS: document extract open source | claude skill document extract | mcp server document extract | best document extract tool
- DISCOVERED_TERMS_FROM_SOURCES: docx

**Q8** concepts: pdf, table, extract, open_source, benchmark
- CORE_KEYWORDS: pdf | table | extract | extraction | pdf parsing | pdf text extraction | table extraction | table detection
- GITHUB_KEYWORDS: (pdf OR table) (extract OR extraction OR parse) in:name,description,readme | topic:pdf-parsing | topic:pdf-text-extraction | topic:table-extraction
- MCP_KEYWORDS: mcp server pdf table extract | pdf | table | extract | ocr
- SKILL_KEYWORDS: SKILL.md pdf table extract | claude skill pdf table extract
- WEB_KEYWORDS: pdf table extract open source | claude skill pdf extract | mcp server pdf extract | best pdf extract tool
- DISCOVERED_TERMS_FROM_SOURCES: pypdf | pdfplumber | pdf2image

## OUTBOX CANDIDATES

### OBX-DKSC-0929201853-01

- SOURCE: https://github.com/PSPDFKit-labs/nutrient-agent-skill
- CAPABILITY: DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski | PSPDFKit-labs/nutrient-agent-skill | MCP_SERVER
- WHY_INTERESTING: relevance 15, E2_PRIMARY_DOC_READ, categories DOCUMENT_PROCESSING/DATA_EXTRACTION/OCR/TABLE_EXTRACTION/SPREADSHEET, referenced by 5 next question(s), found in 1 source(s)
- DREAM_USE: 스캔본 포함 PDF·문서·Excel/스프레드시트·카탈로그에서 텍스트·표를 읽어 구조화하는 추출 단계
- NEXT_RESEARCH_QUESTION: PSPDFKit-labs/nutrient-agent-skill의 OCR과 anthropics/skills/pdf의 PDF 표 추출을 결합하면 스캔된 공급업체 카탈로그까지 구조화된 데이터(JSON)로 만들 수 있는가?
- STATUS: DISCOVERED
- AUTHORITY: NONE

### OBX-DKSC-0929201853-02

- SOURCE: https://github.com/koraynar/doc-extract-mcp
- CAPABILITY: DKSC-0929201853-001-koraynar-doc-extract-mcp | koraynar/doc-extract-mcp | MCP_SERVER
- WHY_INTERESTING: relevance 15, E3_PRIMARY_DOC_AND_MANIFEST_READ, categories DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/STRUCTURED_OUTPUT/MCP, referenced by 4 next question(s), found in 2 source(s)
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- NEXT_RESEARCH_QUESTION: PSPDFKit-labs/nutrient-agent-skill의 PDF 표 추출 결과를 koraynar/doc-extract-mcp(으)로 넘겨 Excel 또는 데이터베이스 적재까지 자동화할 수 있는가?
- STATUS: DISCOVERED
- AUTHORITY: NONE

### OBX-DKSC-0929201853-03

- SOURCE: https://github.com/anthropics/skills/tree/main/skills/docx
- CAPABILITY: DKSC-0929201853-004-anthropics-skills-docx | anthropics/skills/docx | AGENT_SKILL
- WHY_INTERESTING: relevance 13, E3_PRIMARY_DOC_AND_MANIFEST_READ, categories DOCUMENT_PROCESSING/DATA_EXTRACTION/SPREADSHEET/CONVERSION/AGENT_SKILL, referenced by 3 next question(s), found in 1 source(s)
- DREAM_USE: PDF·문서·Excel/스프레드시트·카탈로그에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계
- NEXT_RESEARCH_QUESTION: 상품 이미지와 텍스트를 동시에 추출할 수 있는 Capability가 존재하는가?
- STATUS: DISCOVERED
- AUTHORITY: NONE

## SELF TEST

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
| LOOP | generated next question accepted as new input | **PASS** | run DKSC-0929201919: 카탈로그(상품 목록) PDF에서 상품명·가격·규격 필드를 스키마 기반으로 추출하는 공개 Capability가 존재하는가? -> 15 records, 7 questions |

## SUCCESS CRITERIA (section 24)

1. natural-language question input: **PASS**
2. automatic search terms: **PASS**
3. real public-source exploration: **PASS**
4. >=5 capabilities collected: **PASS**
5. common schema conversion: **PASS**
6. duplicate handling: **PASS**
7. new research questions: **PASS**
8. next AI keywords: **PASS**
9. OUTBOX candidates: **PASS**

## ERRORS

- run DKSC-0929201853: 0 program errors, 2 blocking request failures, 19 expected 404 probes for optional files (see run_report.md fetch log)
  - F021 https://api.github.com/search/repositories?q=pdf%20document%20excel%20spreadsheet%20extract&per_page=20 -> 403 HTTP_403
  - F037 https://pypi.org/search/?q=pdf%20extract%20structured%20data -> 200 BOT_CHALLENGE_NOT_BYPASSED
- run DKSC-0929201919: 0 program errors, 2 blocking request failures, 21 expected 404 probes for optional files (see run_report.md fetch log)
  - F021 https://api.github.com/search/repositories?q=pdf%20catalog%20product%20extract%20extraction&per_page=20 -> 403 HTTP_403
  - F036 https://pypi.org/search/?q=pdf%20extract%20structured%20data -> 200 BOT_CHALLENGE_NOT_BYPASSED

## LIMITATIONS

- Question decomposition and keyword generation use a fixed bilingual lexicon, not an LLM. Words outside it fall back to raw English keywords; unmapped Korean words are only reported.
- Relevance is keyword matching on names/descriptions; it does not prove the tool works. No candidate was installed or run.
- GitHub search API, repository metadata (stars, last commit) and code search are not reachable from this environment; GitHub coverage comes from curated lists + raw files, so LAST_UPDATED is UNKNOWN for GitHub-only records.
- The MCP registry search matches server *names* only, so tools whose names lack the search words are missed.
- INPUT/OUTPUT/API/AUTH/COST/NETWORK fields are detected from text; UNKNOWN means the text did not say, not 'no'.
- Curated lists are community-maintained and may be stale; listing presence is not an endorsement.
- Per-source caps and the 15-record ceiling mean the result is a sample, not a census.

## WHAT WAS NOT MEASURED

- Whether any candidate actually extracts data correctly (nothing was installed or executed).
- Extraction accuracy, speed, or cost per page of any tool.
- Real pricing (only words like 'free' / 'pay per call' were detected).
- GitHub stars, last commit date, issues, and code search (API blocked in this environment).
- The Claude plugin / connector directory contents (no public machine-readable listing reached).
- PyPI keyword search (JavaScript challenge, not bypassed).
- Any revenue. POSSIBLE_VALUE is a label, not a result.
- Security review of any candidate.

## FILES CREATED

- `scout/scout.py`, `scout/README.md`, `scout/CLAUDE_CODE_SCOUT_HANDOFF.md`
- `runs/001/results.json`, `runs/001/capabilities.json`, `runs/001/next_questions.json`, `runs/001/run_report.md`
- `runs/002/results.json`, `runs/002/capabilities.json`, `runs/002/next_questions.json`, `runs/002/run_report.md`

## NEXT RECOMMENDED ACTION

1. A human reads the 3 OUTBOX candidates and decides which (if any) to look at by hand. No install before that.
2. 20-50 capability expansion pilot: raise `max_results`/`per_source_cap`, add 2-3 more curated lists, and run the top 3 next questions as a batch loop (depth 1).
3. If a GitHub token with public read scope is approved later, enable the GitHub search collector (already coded) to fill stars/last-commit. Until then it stays HOLD.
4. Do not auto-install, auto-run, promote to SLIM KTX, or dock to FULL KTX (section 25).

## DREAM HANDOFF PACKET

```json
{
  "lot": "DKSC-CLAUDE-CODE-SCOUT-001",
  "authority": "NONE",
  "status": "PASS",
  "run_tag": "DKSC-0929201853",
  "input_question": "PDF, 문서, Excel 또는 카탈로그에서 구조화된 데이터를 자동 추출하는 데 사용할 수 있는 공개 Skill 또는 코드 도구를 찾아줘.",
  "sources_actually_accessed": 6,
  "raw_candidates": 62,
  "unique_capabilities": 15,
  "capability_records": 15,
  "next_questions": [
    "PSPDFKit-labs/nutrient-agent-skill의 OCR과 anthropics/skills/pdf의 PDF 표 추출을 결합하면 스캔된 공급업체 카탈로그까지 구조화된 데이터(JSON)로 만들 수 있는가?",
    "PSPDFKit-labs/nutrient-agent-skill의 PDF 표 추출 결과를 koraynar/doc-extract-mcp(으)로 넘겨 Excel 또는 데이터베이스 적재까지 자동화할 수 있는가?",
    "카탈로그(상품 목록) PDF에서 상품명·가격·규격 필드를 스키마 기반으로 추출하는 공개 Capability가 존재하는가?",
    "상품 이미지와 텍스트를 동시에 추출할 수 있는 Capability가 존재하는가?",
    "JSON 스키마 기반 추출을 지원하는 koraynar/doc-extract-mcp, Document to JSON – PDF Invoice/Statement/Contract Parser을(를) 공급업체 카탈로그 상품 스키마에 적용하면 데이터베이스 레코드를 바로 만들 수 있는가?",
    "API 키 없이 로컬에서 실행 가능한 후보(6개)만으로 PDF 문서 → 구조화 데이터 추출 파이프라인을 구성할 수 있는가?",
    "Agent Skill(anthropics/skills/docx)의 절차와 MCP 서버(koraynar/doc-extract-mcp)의 도구 호출을 결합해 문서 추출 작업을 한 번의 요청으로 자동화할 수 있는가?",
    "PSPDFKit-labs/nutrient-agent-skill과(와) anthropics/skills/pdf의 PDF 표 추출 정확도를 비교할 공개 벤치마크나 테스트 데이터셋이 있는가?"
  ],
  "outbox": [
    {
      "id": "OBX-DKSC-0929201853-01",
      "capability": "DKSC-0929201853-002-pspdfkit-labs-nutrient-agent-ski | PSPDFKit-labs/nutrient-agent-skill | MCP_SERVER",
      "source": "https://github.com/PSPDFKit-labs/nutrient-agent-skill",
      "status": "DISCOVERED",
      "authority": "NONE"
    },
    {
      "id": "OBX-DKSC-0929201853-02",
      "capability": "DKSC-0929201853-001-koraynar-doc-extract-mcp | koraynar/doc-extract-mcp | MCP_SERVER",
      "source": "https://github.com/koraynar/doc-extract-mcp",
      "status": "DISCOVERED",
      "authority": "NONE"
    },
    {
      "id": "OBX-DKSC-0929201853-03",
      "capability": "DKSC-0929201853-004-anthropics-skills-docx | anthropics/skills/docx | AGENT_SKILL",
      "source": "https://github.com/anthropics/skills/tree/main/skills/docx",
      "status": "DISCOVERED",
      "authority": "NONE"
    }
  ],
  "loop_check": {
    "run_tag": "DKSC-0929201919",
    "question": "카탈로그(상품 목록) PDF에서 상품명·가격·규격 필드를 스키마 기반으로 추출하는 공개 Capability가 존재하는가?",
    "status": "PASS"
  },
  "next_step_candidate": "20-50 capability expansion pilot",
  "forbidden_until_human_approval": [
    "install",
    "execute",
    "SLIM KTX promotion",
    "FULL KTX dock",
    "payment",
    "external posting"
  ]
}
```

## FINAL STATUS

```
CLAUDE_CODE_SCOUT_STATUS: PASS
INPUT_QUESTION: PDF, 문서, Excel 또는 카탈로그에서 구조화된 데이터를 자동 추출하는 데 사용할 수 있는 공개 Skill 또는 코드 도구를 찾아줘.
SOURCES_ACTUALLY_ACCESSED: 6
RAW_CANDIDATES: 62
UNIQUE_CAPABILITIES: 15
NEXT_QUESTIONS: 8
OUTBOX_CANDIDATES: 3
AUTHORITY: NONE
```
