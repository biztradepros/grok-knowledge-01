#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DREAM FACTORIES - CLAUDE CODE SKILL SCOUT v0.1
LOT: DKSC-CLAUDE-CODE-SCOUT-001 | MODE: BUILD + RUN + EVIDENCE | AUTHORITY: NONE

One natural-language question in ->
  search terms -> public sources -> skill / code / MCP candidates -> source read ->
  normalize -> deduplicate -> classify -> next questions + keywords -> OUTBOX candidates.

Rules this program enforces on itself:
  * Python standard library only. No framework, no paid API, no LLM call.
  * HTTP GET only, to an allowlist of public hosts, with no credentials attached.
  * Nothing found is installed or executed. Nothing is written except the output directory.
  * Every capability record points at the fetch-log entries that prove it was read.
  * A blocked source is recorded (HOLD / FAIL) and the run continues with the rest.

Usage:
  python3 scout.py run --question "..." --out runs/001
  python3 scout.py run --from-next runs/001/next_questions.json --pick 1 --out runs/002
  python3 scout.py handoff --runs runs/001 runs/002 --out CLAUDE_CODE_SCOUT_HANDOFF.md
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = "0.1.0"
LOT = "DKSC-CLAUDE-CODE-SCOUT-001"
USER_AGENT = "DreamFactories-ClaudeCodeScout/0.1 (read-only research pilot)"
KST = dt.timezone(dt.timedelta(hours=9))

LIMITS = {
    "min_results": 5,
    "target_results": 10,
    "max_results": 15,
    "per_source_pool_cap": 20,
    "per_source_min_pick": 2,
    "request_budget": 180,
    "timeout_s": 25,
    "max_body_bytes": 8_000_000,
    "readme_chars": 40_000,
}

# Only these public hosts may be contacted. Anything else is refused and logged.
ALLOWED_HOSTS = {
    "raw.githubusercontent.com",
    "api.github.com",
    "registry.modelcontextprotocol.io",
    "registry.npmjs.org",
    "pypi.org",
    "code.claude.com",
    "platform.claude.com",
    "docs.claude.com",
    "claude.com",
    "www.claude.com",
}

# Source catalogue, in the priority order of the pilot spec (section 3).
# These are *where* to look, not *what* to find: no candidate names are hardcoded.
ANTHROPIC_SKILLS = {"owner": "anthropics", "repo": "skills", "ref": "main",
                    "marketplace": ".claude-plugin/marketplace.json"}
CURATED_LISTS = [
    ("ComposioHQ", "awesome-claude-skills"),
    ("travisvn", "awesome-claude-skills"),
    ("VoltAgent", "awesome-agent-skills"),
    ("punkpeye", "awesome-mcp-servers"),
]
OFFICIAL_DOC_INDEXES = [
    "https://code.claude.com/docs/llms.txt",
    "https://platform.claude.com/llms.txt",
]
MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers"
NPM_SEARCH = "https://registry.npmjs.org/-/v1/search"
GITHUB_SEARCH = "https://api.github.com/search/repositories"
PYPI_SEARCH = "https://pypi.org/search/"
CLAUDE_DIRECTORY = "https://claude.com/plugins"

# ---------------------------------------------------------------------------
# Lexicon: bilingual (ko/en) concept map used to decompose a question into
# OBJECT / ACTION / OUTPUT / CONTEXT and to score candidate text.
#   q       : regexes that detect the concept in the *question*
#   match   : regexes that detect the concept in *candidate* text
#   terms   : English search terms
#   expand  : technical expansions (TECHNICAL_TERMS)
#   reg     : single-word terms for name-substring registries (MCP registry)
#   implies : related concepts added as secondary signals
# ---------------------------------------------------------------------------
LEXICON = [
    # OBJECT
    dict(id="pdf", facet="OBJECT", ko="PDF", q=[r"pdf"], match=[r"\bpdfs?\b"],
         terms=["pdf"], expand=["pdf parsing", "pdf text extraction"], reg=["pdf"],
         implies=["table", "ocr"]),
    dict(id="document", facet="OBJECT", ko="문서", q=[r"문서", r"\bdocuments?\b", r"docx", r"워드"],
         match=[r"\bdocuments?\b", r"\bdocx\b"], terms=["document"],
         expand=["document parsing", "intelligent document processing", "document ai"],
         reg=["document", "docx"], implies=[]),
    dict(id="spreadsheet", facet="OBJECT", ko="Excel/스프레드시트",
         q=[r"엑셀", r"excel", r"xlsx", r"스프레드\s*시트", r"spreadsheet", r"\bcsv\b"],
         match=[r"\bexcel\b", r"\bxlsx\b", r"spreadsheets?", r"\bcsv\b"], terms=["excel", "spreadsheet"],
         expand=["xlsx", "csv", "tabular data"], reg=["excel", "spreadsheet", "xlsx"], implies=["table"]),
    dict(id="catalog", facet="OBJECT", ko="카탈로그",
         q=[r"카탈로그", r"catalog", r"상품\s*목록", r"제품\s*목록"],
         match=[r"catalog(ue)?s?\b", r"product (list|listing|feed|data|catalog)"], terms=["catalog"],
         expand=["product catalog", "product data extraction", "product feed"], reg=["catalog"],
         implies=["product", "table"]),
    dict(id="product", facet="OBJECT", ko="상품", q=[r"상품", r"제품", r"\bproducts?\b", r"\bsku\b"],
         match=[r"\bproducts?\b", r"\bskus?\b"], terms=["product"],
         expand=["product information", "product attributes"], reg=["product"], implies=[]),
    dict(id="table", facet="OBJECT", ko="표",
         q=[r"(?<![가-힣])표(?:를|에서|의|와|과|로|는|가)?(?![가-힣])", r"테이블", r"\btables?\b"],
         match=[r"\btables?\b"], terms=["table"], expand=["table extraction", "table detection"],
         reg=["table"], implies=[]),
    dict(id="image", facet="OBJECT", ko="이미지", q=[r"이미지", r"사진", r"\bimages?\b", r"\bphotos?\b"],
         match=[r"\bimages?\b", r"\bphotos?\b", r"screenshots?"], terms=["image"],
         expand=["image text extraction", "multimodal extraction"], reg=["image"], implies=["ocr"]),
    dict(id="scanned", facet="OBJECT", ko="스캔 문서", q=[r"스캔", r"\bscan"],
         match=[r"scann(ed|ing)", r"\bscans?\b"], terms=["scanned"], expand=["scanned documents"],
         reg=["scan"], implies=["ocr", "image"]),
    dict(id="invoice", facet="OBJECT", ko="인보이스/영수증",
         q=[r"인보이스", r"송장", r"영수증", r"청구서", r"invoice", r"receipt"],
         match=[r"invoices?", r"receipts?"], terms=["invoice", "receipt"],
         expand=["invoice parsing", "receipt ocr"], reg=["invoice", "receipt"], implies=["structured_data"]),
    dict(id="web", facet="OBJECT", ko="웹 페이지", q=[r"웹", r"사이트", r"website", r"web\s*page", r"\burls?\b"],
         match=[r"web ?pages?", r"websites?", r"\burls?\b", r"\bhtml\b"], terms=["web page"],
         expand=["web scraping", "html extraction"], reg=["web", "scrape"], implies=[]),
    dict(id="email", facet="OBJECT", ko="이메일", q=[r"이메일", r"메일", r"e-?mail"],
         match=[r"\be-?mails?\b"], terms=["email"], expand=["email parsing"], reg=["email"], implies=[]),
    dict(id="audio", facet="OBJECT", ko="음성/오디오", q=[r"음성", r"오디오", r"녹음", r"\baudio\b", r"speech"],
         match=[r"\baudio\b", r"speech", r"\bvoice\b"], terms=["audio"], expand=["speech to text"],
         reg=["audio", "speech"], implies=["transcribe"]),
    dict(id="video", facet="OBJECT", ko="영상", q=[r"영상", r"비디오", r"\bvideo", r"youtube"],
         match=[r"\bvideos?\b", r"youtube"], terms=["video"], expand=["video transcript"], reg=["video"],
         implies=[]),
    dict(id="form", facet="OBJECT", ko="양식", q=[r"양식", r"서식", r"\bforms?\b"], match=[r"\bforms?\b"],
         terms=["form"], expand=["form field extraction"], reg=["form"], implies=[]),
    dict(id="contract", facet="OBJECT", ko="계약서", q=[r"계약서", r"contract"], match=[r"contracts?"],
         terms=["contract"], expand=["contract analysis"], reg=["contract"], implies=[]),
    # ACTION
    dict(id="extract", facet="ACTION", ko="추출",
         q=[r"추출", r"뽑아", r"extract", r"데이터화", r"파싱", r"pars(e|ing)", r"인식"],
         match=[r"extract", r"\bpars(e|es|ing|er)\b"], terms=["extract", "extraction", "parse"],
         expand=["data extraction", "document parsing", "information extraction"],
         reg=["extract", "parse", "parser"], implies=["ocr", "table", "structured_data"]),
    dict(id="ocr", facet="ACTION", ko="OCR", q=[r"\bocr\b", r"ocr", r"문자\s*인식", r"광학"],
         match=[r"\bocr\b", r"optical character", r"text recognition"], terms=["ocr"],
         expand=["optical character recognition"], reg=["ocr"], implies=[]),
    dict(id="convert", facet="ACTION", ko="변환", q=[r"변환", r"convert", r"바꾸"],
         match=[r"conver(t|ts|sion|ter)"], terms=["convert"], expand=["format conversion"], reg=["convert"],
         implies=[]),
    dict(id="summarize", facet="ACTION", ko="요약", q=[r"요약", r"summar"], match=[r"summar"],
         terms=["summarize"], expand=["summarization"], reg=["summar"], implies=[]),
    dict(id="classify", facet="ACTION", ko="분류", q=[r"분류", r"classif", r"태깅"],
         match=[r"classif", r"categori[sz]"], terms=["classify"], expand=["document classification"],
         reg=["classif"], implies=[]),
    dict(id="search", facet="ACTION", ko="검색", q=[r"검색", r"\bsearch\b"], match=[r"\bsearch"],
         terms=["search"], expand=["semantic search"], reg=["search"], implies=[]),
    dict(id="transcribe", facet="ACTION", ko="전사", q=[r"전사", r"받아쓰", r"자막", r"transcri"],
         match=[r"transcri", r"speech[- ]to[- ]text"], terms=["transcribe"], expand=["speech to text"],
         reg=["transcri", "whisper"], implies=[]),
    dict(id="translate", facet="ACTION", ko="번역", q=[r"번역", r"translat"], match=[r"translat"],
         terms=["translate"], expand=["machine translation"], reg=["translat"], implies=[]),
    dict(id="generate", facet="ACTION", ko="생성", q=[r"생성", r"\bgenerat"], match=[r"generat"],
         terms=["generate"], expand=["generation"], reg=["generat"], implies=[]),
    dict(id="collect", facet="ACTION", ko="수집", q=[r"수집", r"크롤", r"스크랩", r"scrap", r"crawl"],
         match=[r"scrap(e|er|ing)", r"crawl"], terms=["scrape", "crawl"], expand=["web crawling"],
         reg=["scrape", "crawl"], implies=[]),
    # OUTPUT
    dict(id="structured_data", facet="OUTPUT", ko="구조화된 데이터",
         q=[r"구조화", r"structured", r"정형", r"스키마", r"schema", r"필드"],
         match=[r"structured", r"\bschemas?\b", r"key[- ]value", r"\bfields?\b"],
         terms=["structured data"], expand=["structured output", "json schema extraction"],
         reg=["structured", "schema"], implies=["json"]),
    dict(id="attributes", facet="OUTPUT", ko="상품 속성(가격·규격)",
         q=[r"가격", r"규격", r"사양", r"\bprices?\b", r"\bspecs?\b", r"specification", r"attribute"],
         match=[r"\bprices?\b", r"specifications?", r"\battributes?\b", r"\bskus?\b"], terms=["price", "attributes"],
         expand=["product attribute extraction", "price extraction"], reg=["price"], implies=[]),
    dict(id="json", facet="OUTPUT", ko="JSON", q=[r"json"], match=[r"\bjson\b"], terms=["json"],
         expand=["json output"], reg=["json"], implies=[]),
    dict(id="database", facet="OUTPUT", ko="데이터베이스",
         q=[r"데이터베이스", r"\bdb\b", r"database", r"적재"], match=[r"database", r"\bsql\b", r"\bdb\b"],
         terms=["database"], expand=["database import", "etl"], reg=["database", "sql"], implies=[]),
    dict(id="markdown", facet="OUTPUT", ko="Markdown", q=[r"마크다운", r"markdown"], match=[r"markdown"],
         terms=["markdown"], expand=["llm-ready markdown"], reg=["markdown"], implies=[]),
    # CONTEXT
    dict(id="automation", facet="CONTEXT", ko="자동화",
         q=[r"자동", r"automat", r"워크플로", r"파이프라인", r"pipeline", r"workflow"],
         match=[r"automat", r"workflow", r"pipeline", r"\bbatch\b"], terms=["automation"],
         expand=["automation pipeline"], reg=[], implies=[]),
    dict(id="agent_skill", facet="CONTEXT", ko="Agent Skill", q=[r"skill", r"스킬"],
         match=[r"skill\.md", r"agent skills?", r"claude skills?"], terms=["claude skill", "agent skill"],
         expand=["SKILL.md"], reg=[], implies=[]),
    dict(id="mcp", facet="CONTEXT", ko="MCP", q=[r"\bmcp\b", r"model context protocol"],
         match=[r"\bmcp\b", r"model context protocol"], terms=["mcp server"], expand=["model context protocol"],
         reg=[], implies=[]),
    dict(id="code_tool", facet="CONTEXT", ko="코드 도구",
         q=[r"코드", r"라이브러리", r"library", r"\bsdk\b", r"\bcli\b", r"개발\s*도구"],
         match=[r"\blibrary\b", r"\bsdk\b", r"\bcli\b", r"\bapi\b"], terms=["library"],
         expand=["python library", "cli tool"], reg=[], implies=[]),
    dict(id="open_source", facet="CONTEXT", ko="공개/오픈소스", q=[r"공개", r"오픈\s*소스", r"open[- ]source"],
         match=[r"open[- ]source", r"\bmit license\b", r"apache"], terms=["open source"], expand=[],
         reg=[], implies=[]),
    dict(id="local", facet="CONTEXT", ko="로컬 실행", q=[r"로컬", r"오프라인", r"\blocal", r"offline"],
         match=[r"\blocal(ly)?\b", r"offline", r"on[- ]device", r"never leave"], terms=["local"],
         expand=["offline", "self-hosted"], reg=[], implies=[]),
    dict(id="supplier", facet="CONTEXT", ko="공급업체", q=[r"공급\s*업체", r"공급사", r"벤더", r"거래처", r"supplier", r"vendor"],
         match=[r"supplier", r"vendor"], terms=["supplier"], expand=["supplier data"], reg=[], implies=[]),
    dict(id="ecommerce", facet="CONTEXT", ko="커머스", q=[r"쇼핑몰", r"커머스", r"e-?commerce", r"스토어"],
         match=[r"e-?commerce", r"shopify", r"\bstorefront\b"], terms=["ecommerce"], expand=["product feed"],
         reg=[], implies=[]),
    dict(id="korean", facet="CONTEXT", ko="한국어", q=[r"한국어", r"한글", r"korean"], match=[r"korean", r"hangul"],
         terms=["korean"], expand=["korean ocr"], reg=[], implies=[]),
    dict(id="benchmark", facet="CONTEXT", ko="정확도/벤치마크", q=[r"벤치마크", r"정확도", r"benchmark", r"accuracy"],
         match=[r"benchmark", r"accura"], terms=["benchmark"], expand=["evaluation dataset"], reg=[], implies=[]),
]
CONCEPTS = {c["id"]: c for c in LEXICON}
FACETS = ["OBJECT", "ACTION", "OUTPUT", "CONTEXT"]
FACET_WEIGHT = {"OBJECT": 3, "ACTION": 3, "OUTPUT": 2, "CONTEXT": 1}

EN_STOP = set("""the and for with from that this into can use using used find tool tools code public any some
which what how are was were will would should could does have has had not but all you your our their them
about than then there here also more most very just only other such each both able way ways like want need
data automatically automatic open source server servers text file files find me please agent agents
capability capabilities"""
.split())
KO_STOP = {"찾아줘", "찾아", "사용할", "사용", "있는", "또는", "에서", "하는", "대한", "위한", "가능한", "공개", "자동으로",
           "도구를", "있는가", "까지", "결합하면", "처리할", "만들", "있을까", "알려줘", "해줘", "무엇", "어떤", "데이터를",
           "구조화된", "데이터", "기능", "기능을", "통해", "그리고", "동시에", "수있는", "할", "것", "존재하는가", "기반으로",
           "목록", "전용", "바로", "만들"}

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.isoformat(timespec="seconds")


def uniq(seq):
    out, seen = [], set()
    for x in seq:
        k = x.lower() if isinstance(x, str) else x
        if x and k not in seen:
            seen.add(k)
            out.append(x)
    return out


def slug(s, n=48):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:n] or "x"


def clip(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


GH_URL = re.compile(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)"
                    r"(?:/(?:tree|blob)/([^/\s#?)]+)(/[^\s#?)]*)?)?", re.I)


def parse_github(url):
    """Return {'owner','repo','ref','path'} for a github.com URL (incl. git+https / .git forms)."""
    if not url:
        return None
    u = url.replace("git+", "").replace("git://", "https://").replace("ssh://git@github.com/", "https://github.com/")
    u = u.replace("git@github.com:", "https://github.com/")
    m = GH_URL.search(u)
    if not m:
        return None
    owner, repo, ref, path = m.group(1), m.group(2), m.group(3), (m.group(4) or "")
    repo = re.sub(r"\.git$", "", repo)
    if owner.lower() in {"orgs", "topics", "search", "sponsors", "features", "marketplace"}:
        return None
    path = path.strip("/")
    if path and re.search(r"\.(md|json|ya?ml|py|js|ts|txt)$", path, re.I):
        path = path.rsplit("/", 1)[0] if "/" in path else ""
    return {"owner": owner, "repo": repo, "ref": ref or "HEAD", "path": path}


def gh_key(gh, with_path=True):
    k = f"gh:{gh['owner']}/{gh['repo']}".lower()
    if with_path and gh.get("path"):
        k += "/" + gh["path"].lower()
    return k


def gh_human_url(gh):
    base = f"https://github.com/{gh['owner']}/{gh['repo']}"
    if gh.get("path"):
        return f"{base}/tree/{gh['ref'] if gh['ref'] != 'HEAD' else 'main'}/{gh['path']}"
    return base


def raw_url(gh, file_path):
    return f"https://raw.githubusercontent.com/{gh['owner']}/{gh['repo']}/{gh.get('ref') or 'HEAD'}/{file_path.lstrip('/')}"


def parse_frontmatter(md):
    fm = {}
    if not md or not md.startswith("---"):
        return fm, md or ""
    end = md.find("\n---", 3)
    if end < 0:
        return fm, md
    block = md[3:end]
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            fm[m.group(1)] = v
    return fm, md[end + 4:]


# ---------------------------------------------------------------------------
# Fetcher: the only door to the network. Logs every request as evidence.
# ---------------------------------------------------------------------------

class Fetcher:
    def __init__(self, budget, timeout):
        self.budget = budget
        self.timeout = timeout
        self.log = []
        self.cache = {}

    def get(self, url, stage, source_id):
        if url in self.cache:
            entry, text = self.cache[url]
            return entry, text
        host = (urllib.parse.urlparse(url).hostname or "").lower()
        entry = {"id": f"F{len(self.log) + 1:03d}", "ts": iso(now_utc()), "stage": stage,
                 "source_id": source_id, "method": "GET", "url": url, "status": None,
                 "ok": False, "bytes": 0, "sha256_16": None, "elapsed_ms": None, "error": None}
        if host not in ALLOWED_HOSTS:
            entry["error"] = "HOST_NOT_ALLOWLISTED"
            self.log.append(entry)
            return entry, None
        if len(self.log) >= self.budget:
            entry["error"] = "REQUEST_BUDGET_EXHAUSTED"
            self.log.append(entry)
            return entry, None
        req = urllib.request.Request(url, method="GET", headers={
            "User-Agent": USER_AGENT, "Accept": "application/json, text/plain, text/markdown, */*"})
        t0 = time.time()
        body, text = b"", None
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = r.read(LIMITS["max_body_bytes"])
                entry["status"] = r.status
                if r.geturl() != url:
                    entry["final_url"] = r.geturl()
        except urllib.error.HTTPError as e:
            entry["status"] = e.code
            try:
                body = e.read(4000)
            except Exception:
                body = b""
            entry["error"] = f"HTTP_{e.code}"
        except urllib.error.URLError as e:
            msg = str(e.reason)
            entry["error"] = "EGRESS_BLOCKED (proxy 403)" if "403" in msg else f"URL_ERROR: {clip(msg, 140)}"
        except Exception as e:  # timeouts, resets
            entry["error"] = f"{type(e).__name__}: {clip(str(e), 140)}"
        entry["elapsed_ms"] = int((time.time() - t0) * 1000)
        entry["bytes"] = len(body)
        if body:
            entry["sha256_16"] = hashlib.sha256(body).hexdigest()[:16]
            text = body.decode("utf-8", "replace")
        if entry["status"] == 200 and not entry["error"]:
            if "<title>Client Challenge</title>" in (text or "")[:3000]:
                entry["error"] = "BOT_CHALLENGE_NOT_BYPASSED"
            else:
                entry["ok"] = True
        if not entry["ok"] and text:
            entry["error_body"] = clip(re.sub(r"<[^>]+>", " ", text), 220)
        self.log.append(entry)
        result = (entry, text if entry["ok"] else None)
        self.cache[url] = result
        return result

    def get_json(self, url, stage, source_id):
        entry, text = self.get(url, stage, source_id)
        if text is None:
            return entry, None
        try:
            return entry, json.loads(text)
        except ValueError:
            entry["ok"] = False
            entry["error"] = "INVALID_JSON"
            return entry, None


# ---------------------------------------------------------------------------
# 7. QUESTION -> SEARCH QUERY
# ---------------------------------------------------------------------------

def analyze_question(question):
    ql = question.lower()
    found = {}
    for c in LEXICON:
        for pat in c["q"]:
            m = re.search(pat, ql, re.I)
            if m:
                found[c["id"]] = m.group(0).strip()
                break
    primary = [c for c in LEXICON if c["id"] in found]
    implied = []
    for c in primary:
        for i in c["implies"]:
            if i not in found and i not in implied:
                implied.append(i)
    facets = {f: [] for f in FACETS}
    for c in primary:
        facets[c["facet"]].append({"concept": c["id"], "label": c["ko"], "matched_text": found[c["id"]],
                                   "terms": c["terms"]})
    # Words the lexicon does not know: English ones become free keywords, Korean ones are reported.
    covered = " ".join(found.values())
    en_tokens = re.findall(r"[a-z][a-z0-9+#-]{2,}", ql)
    free = [t for t in uniq(en_tokens) if t not in EN_STOP and t not in covered
            and not any(re.search(p, t) for c in LEXICON for p in c["q"])]
    ko_tokens = re.findall(r"[가-힣]{2,}", question)
    unmapped_ko = [t for t in uniq(ko_tokens) if t not in KO_STOP
                   and not any(re.search(p, t, re.I) for c in LEXICON for p in c["q"])]

    def terms_of(facet, n=None, secondary=False):
        ids = [c["id"] for c in primary if c["facet"] == facet]
        if secondary:
            ids += [i for i in implied if CONCEPTS[i]["facet"] == facet]
        out = uniq([t for i in ids for t in CONCEPTS[i]["terms"]])
        return out[:n] if n else out

    obj, act, out = terms_of("OBJECT"), terms_of("ACTION"), terms_of("OUTPUT")
    ctx_ids = [c["id"] for c in primary if c["facet"] == "CONTEXT"]
    technical = uniq([t for c in primary for t in c["expand"]] +
                     [t for i in implied for t in CONCEPTS[i]["expand"]] + free)
    core = uniq(obj[:3] + act[:2] + out[:1] + free[:2])
    act_or = act or terms_of("ACTION", secondary=True)
    github_q = " ".join(filter(None, [
        f"({' OR '.join(obj[:4])})" if obj else "",
        f"({' OR '.join(act_or[:3])})" if act_or else "",
        f"\"{out[0]}\"" if out else "", " ".join(free[:2]), "in:name,description,readme"]))
    skill_q = " ".join(uniq(["SKILL.md"] + obj[:2] + act_or[:1] + out[:1]))
    mcp_q = " ".join(uniq(["mcp server"] + obj[:2] + act_or[:1] + out[:1]))
    npm_q = [" ".join(uniq(obj[:1] + act_or[:1] + out[:1])),
             " ".join(uniq(["keywords:mcp"] + obj[:1] + act_or[:1])),
             " ".join(uniq(obj[1:2] + act_or[:1] + out[:1])) if len(obj) > 1 else ""]
    npm_q = uniq([q.strip() for q in npm_q if q.strip()]) or [" ".join(core)]
    reg_ids = [c["id"] for c in primary if c["facet"] in ("OBJECT", "ACTION")] + \
              [i for i in implied if CONCEPTS[i]["facet"] == "ACTION"]
    registry_terms = uniq([t for i in reg_ids for t in CONCEPTS[i]["reg"][:1]] + free[:2])[:7]
    web = uniq([
        " ".join(uniq(obj[:2] + act_or[:1] + out[:1] + ["open source"])),
        " ".join(uniq(["claude skill"] + obj[:1] + act_or[:1])),
        " ".join(uniq(["mcp server"] + obj[:1] + act_or[:1] + out[:1])),
        " ".join(uniq(["best"] + obj[:1] + act_or[:1] + ["tool"])),
    ])
    return {
        "question": question,
        "facets": facets,
        "primary_ids": [c["id"] for c in primary],
        "implied_ids": implied,
        "free_keywords": free,
        "unmapped_korean_tokens": unmapped_ko,
        "queries": {
            "CORE_QUERY": " ".join(core),
            "GITHUB_QUERY": github_q,
            "SKILL_QUERY": skill_q,
            "MCP_QUERY": mcp_q,
            "NPM_QUERIES": npm_q,
            "MCP_REGISTRY_TERMS": registry_terms,
            "WEB_QUERIES": web,
            "TECHNICAL_TERMS": technical,
        },
        "method": "deterministic bilingual lexicon (no LLM, no paid API)",
    }


def score_text(text, A):
    t = (text or "").lower()
    hits = {"OBJECT": [], "ACTION": [], "OUTPUT": [], "CONTEXT": [], "SECONDARY": [], "FREE": []}
    for cid in A["primary_ids"]:
        c = CONCEPTS[cid]
        if any(re.search(p, t) for p in c["match"]):
            hits[c["facet"]].append(cid)
    for cid in A["implied_ids"]:
        if any(re.search(p, t) for p in CONCEPTS[cid]["match"]):
            hits["SECONDARY"].append(cid)
    for kw in A["free_keywords"]:
        if re.search(r"\b" + re.escape(kw), t):
            hits["FREE"].append(kw)
    score = sum(FACET_WEIGHT[f] * len(hits[f]) for f in FACETS) + len(hits["SECONDARY"]) + 2 * len(hits["FREE"])
    need_obj = bool(A["facets"]["OBJECT"])
    need_act = bool(A["facets"]["ACTION"] or A["facets"]["OUTPUT"])
    obj_ok = bool(hits["OBJECT"]) if need_obj else True
    sec = lambda f: [i for i in hits["SECONDARY"] if CONCEPTS[i]["facet"] == f]
    if A["facets"]["ACTION"]:
        act_ok = bool(hits["ACTION"] or sec("ACTION"))
    else:
        act_ok = bool(hits["OUTPUT"] or sec("OUTPUT")) if need_act else True
    if not need_obj and not need_act:
        passed = score > 0
    else:
        passed = obj_ok and act_ok
    return score, hits, passed


# ---------------------------------------------------------------------------
# 8. COLLECT - one function per public source. Each returns (status_record, raw_candidates).
# ---------------------------------------------------------------------------

def new_status(source_id, priority, label, method):
    return {"source_id": source_id, "priority": priority, "label": label, "method": method,
            "status": "NOT_RUN", "reason": "", "requests": [], "raw_seen": 0, "gated": 0, "kept": 0}


def finish_status(st, kept, attempted, ok, hold_reason=None):
    st["kept"] = len(kept)
    st["ok_requests"] = ok
    if hold_reason:
        st["status"], st["reason"] = "HOLD", hold_reason
    elif ok == 0:
        st["status"] = "FAIL"
        st["reason"] = st["reason"] or "no request succeeded"
    elif ok < attempted or not kept:
        st["status"] = "PARTIAL"
        if not st["reason"]:
            st["reason"] = f"{ok}/{attempted} requests ok; {len(kept)} relevant candidates kept"
    else:
        st["status"] = "PASS"
        st["reason"] = f"{ok}/{attempted} requests ok; {len(kept)} relevant candidates kept"
    return st


def make_candidate(source_id, name, description, url, fetch_ids, A, gh=None, npm=None, pypi=None,
                   mcpreg=None, doc_url=None, meta=None, extra_text=""):
    text = " ".join([name or "", description or "", extra_text or ""])
    score, hits, passed = score_text(text, A)
    return {"source_id": source_id, "name": name, "description": clip(description, 600), "candidate_url": url,
            "gh": gh, "npm": npm, "pypi": pypi, "mcpreg": mcpreg, "doc_url": doc_url, "meta": meta or {},
            "fetch_ids": list(fetch_ids), "score": score, "hits": hits, "passed": passed}


def top_passed(cands, cap):
    ok = [c for c in cands if c["passed"]]
    ok.sort(key=lambda c: (-c["score"], 0 if c.get("gh") else 1, c["name"].lower()))
    return ok[:cap]


def collect_anthropic(F, A, cap):
    sid = "S1_ANTHROPIC_OFFICIAL_SKILLS"
    st = new_status(sid, 1, "Anthropic official Skills repository (anthropics/skills)",
                    "raw.githubusercontent.com: .claude-plugin/marketplace.json -> each skills/*/SKILL.md")
    gh0 = dict(ANTHROPIC_SKILLS, path="")
    e, text = F.get_json(raw_url(gh0, ANTHROPIC_SKILLS["marketplace"]), "collect", sid)
    st["requests"].append(e["id"])
    attempted, ok = 1, int(e["ok"])
    cands = []
    if text:
        paths = uniq([p.lstrip("./") for plug in text.get("plugins", []) for p in plug.get("skills", [])])
        for p in paths:
            gh = {"owner": "anthropics", "repo": "skills", "ref": "main", "path": p}
            e2, md = F.get(raw_url(gh, f"{p}/SKILL.md"), "collect", sid)
            st["requests"].append(e2["id"])
            attempted += 1
            ok += int(e2["ok"])
            if not md:
                continue
            fm, _ = parse_frontmatter(md)
            name = fm.get("name") or p.rsplit("/", 1)[-1]
            c = make_candidate(sid, name, fm.get("description", ""), gh_human_url(gh), [e["id"], e2["id"]], A,
                               gh=gh, meta={"frontmatter": fm, "skill_md_url": e2["url"]})
            c["_skill_md"] = md
            cands.append(c)
    st["raw_seen"] = len(cands)
    st["gated"] = sum(c["passed"] for c in cands)
    kept = top_passed(cands, cap)
    return finish_status(st, kept, attempted, ok), kept


def collect_github_search(F, A, cap):
    sid = "S2_GITHUB_SEARCH_API"
    st = new_status(sid, 2, "GitHub public repository search (REST API, unauthenticated)",
                    "api.github.com/search/repositories")
    q = A["queries"]["GITHUB_QUERY"].replace(" in:name,description,readme", "")
    q = re.sub(r"[()\"]", " ", q).replace(" OR ", " ")
    words = uniq(q.split())[:5]
    url = f"{GITHUB_SEARCH}?q={urllib.parse.quote(' '.join(words))}&per_page=20"
    e, data = F.get_json(url, "collect", sid)
    st["requests"].append(e["id"])
    if not data:
        body = (e.get("error_body") or "").lower()
        if e.get("status") in (401, 403) or "egress" in (e.get("error") or "").lower():
            reason = "HOLD_AUTH_REQUIRED/HOLD_POLICY: " + (e.get("error_body") or e.get("error") or "")
            if "bound to their configured repositories" in body:
                reason = ("HOLD_POLICY: this execution environment scopes api.github.com to its configured "
                          "repositories; public search not reachable without widening access. Not bypassed.")
            return finish_status(st, [], 1, 0, hold_reason=reason), []
        st["reason"] = e.get("error") or "no data"
        return finish_status(st, [], 1, 0), []
    cands = []
    for it in data.get("items", []):
        gh = parse_github(it.get("html_url"))
        desc = it.get("description") or ""
        c = make_candidate(sid, it.get("full_name"), desc, it.get("html_url"), [e["id"]], A, gh=gh,
                           meta={"stars": it.get("stargazers_count"), "pushed_at": it.get("pushed_at"),
                                 "license": (it.get("license") or {}).get("spdx_id"), "topics": it.get("topics")},
                           extra_text=" ".join(it.get("topics") or []))
        cands.append(c)
    st["raw_seen"] = len(cands)
    st["gated"] = sum(c["passed"] for c in cands)
    kept = top_passed(cands, cap)
    return finish_status(st, kept, 1, 1), kept


LIST_LINE = re.compile(r"^\s*[-*]\s+(?:\*\*)?\[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)\)(?:\*\*)?(?P<rest>.*)$")


def collect_curated_lists(F, A, cap):
    sid = "S3_GITHUB_CURATED_LISTS"
    st = new_status(sid, 3, "Public GitHub curated lists of Skills / MCP servers (raw README)",
                    "raw.githubusercontent.com/<list>/HEAD/README.md -> parse '- [name](url) - description'")
    attempted = ok = 0
    cands = []
    for owner, repo in CURATED_LISTS:
        lgh = {"owner": owner, "repo": repo, "ref": "HEAD", "path": ""}
        e, md = F.get(raw_url(lgh, "README.md"), "collect", sid)
        st["requests"].append(e["id"])
        attempted += 1
        ok += int(e["ok"])
        if not md:
            continue
        for line in md.splitlines():
            m = LIST_LINE.match(line)
            if not m:
                continue
            name, url, rest = m.group("name").strip(), m.group("url").strip(), m.group("rest")
            if url.startswith("#"):
                continue
            if url.startswith("./") or url.startswith("../") or not url.startswith("http"):
                url = f"https://github.com/{owner}/{repo}/tree/HEAD/{url.lstrip('./')}"
            rest = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", " ", rest)   # badges
            rest = re.sub(r"\*By \[[^\]]*\]\([^)]*\)\*", " ", rest)          # author credits
            parts = re.split(r"\s[-–—:]\s", rest, maxsplit=1)
            desc = parts[1] if len(parts) > 1 else rest
            desc = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", desc).strip(" -*")
            if len(desc) < 8:
                continue
            gh = parse_github(url)
            c = make_candidate(sid, name, desc, url, [e["id"]], A, gh=gh,
                               meta={"list": f"{owner}/{repo}", "list_line": clip(line, 400)})
            cands.append(c)
    st["raw_seen"] = len(cands)
    st["gated"] = sum(c["passed"] for c in cands)
    kept = top_passed(cands, cap)
    return finish_status(st, kept, attempted, ok), kept


def collect_mcp_registry(F, A, cap):
    sid = "S4_OFFICIAL_MCP_REGISTRY"
    st = new_status(sid, 3, "Official MCP Registry (registry.modelcontextprotocol.io)",
                    "GET /v0/servers?search=<term>&version=latest&limit=100 per term")
    attempted = ok = 0
    seen = {}
    for term in A["queries"]["MCP_REGISTRY_TERMS"]:
        url = f"{MCP_REGISTRY}?search={urllib.parse.quote(term)}&version=latest&limit=100"
        e, data = F.get_json(url, "collect", sid)
        st["requests"].append(e["id"])
        attempted += 1
        ok += int(e["ok"])
        if not data:
            continue
        for row in data.get("servers", []):
            s = row.get("server", {})
            name = s.get("name")
            if not name or name in seen:
                continue
            meta_official = (row.get("_meta") or {}).get("io.modelcontextprotocol.registry/official", {})
            repo = (s.get("repository") or {})
            gh = parse_github(repo.get("url"))
            if gh and repo.get("subfolder"):
                gh["path"] = repo["subfolder"].strip("/")
            pkgs = [{"registryType": p.get("registryType"), "identifier": p.get("identifier"),
                     "transport": (p.get("transport") or {}).get("type"),
                     "env": [{"name": v.get("name"), "isSecret": v.get("isSecret"), "isRequired": v.get("isRequired")}
                             for v in (p.get("environmentVariables") or [])]} for p in (s.get("packages") or [])]
            remotes = [{"type": r.get("type"), "url": r.get("url"),
                        "headers": [h.get("name") for h in (r.get("headers") or [])]} for r in (s.get("remotes") or [])]
            npm = next((p["identifier"] for p in pkgs if p["registryType"] == "npm"), None)
            pypi = next((p["identifier"] for p in pkgs if p["registryType"] == "pypi"), None)
            desc = s.get("description") or ""
            human = f"{MCP_REGISTRY}?search={urllib.parse.quote(name)}&version=latest"
            c = make_candidate(sid, s.get("title") or name, desc, human, [e["id"]], A, gh=gh, npm=npm,
                               pypi=pypi, mcpreg=name,
                               meta={"registry_name": name, "version": s.get("version"),
                                     "websiteUrl": s.get("websiteUrl"), "repository": repo.get("url"),
                                     "packages": pkgs, "remotes": remotes,
                                     "updatedAt": meta_official.get("updatedAt"),
                                     "status": meta_official.get("status")},
                               extra_text=name)
            seen[name] = c
    cands = list(seen.values())
    st["raw_seen"] = len(cands)
    st["gated"] = sum(c["passed"] for c in cands)
    kept = top_passed(cands, cap)
    return finish_status(st, kept, attempted, ok), kept


def collect_npm(F, A, cap):
    sid = "S5_NPM_REGISTRY"
    st = new_status(sid, 5, "npm public registry search API", "GET /-/v1/search?text=<query>&size=20")
    attempted = ok = 0
    seen = {}
    for q in A["queries"]["NPM_QUERIES"]:
        url = f"{NPM_SEARCH}?text={urllib.parse.quote(q)}&size=20"
        e, data = F.get_json(url, "collect", sid)
        st["requests"].append(e["id"])
        attempted += 1
        ok += int(e["ok"])
        if not data:
            continue
        for o in data.get("objects", []):
            p = o.get("package", {})
            name = p.get("name")
            if not name or name in seen:
                continue
            links = p.get("links") or {}
            gh = parse_github(links.get("repository") or links.get("homepage"))
            kw = p.get("keywords") or []
            c = make_candidate(sid, name, p.get("description") or "", links.get("npm") or
                               f"https://www.npmjs.com/package/{name}", [e["id"]], A, gh=gh, npm=name,
                               meta={"version": p.get("version"), "date": p.get("date"), "license": p.get("license"),
                                     "keywords": kw, "publisher": (p.get("publisher") or {}).get("username"),
                                     "repository": links.get("repository"), "homepage": links.get("homepage")},
                               extra_text=" ".join(kw))
            seen[name] = c
    cands = list(seen.values())
    st["raw_seen"] = len(cands)
    st["gated"] = sum(c["passed"] for c in cands)
    kept = top_passed(cands, cap)
    return finish_status(st, kept, attempted, ok), kept


def collect_pypi_search(F, A, cap):
    sid = "S6_PYPI_SEARCH"
    st = new_status(sid, 5, "PyPI search (no JSON search API exists; HTML listing)", "GET pypi.org/search/?q=")
    q = A["queries"]["NPM_QUERIES"][0]
    e, html_text = F.get(f"{PYPI_SEARCH}?q={urllib.parse.quote(q)}", "collect", sid)
    st["requests"].append(e["id"])
    if not html_text:
        if e.get("error") == "BOT_CHALLENGE_NOT_BYPASSED":
            return finish_status(st, [], 1, 0, hold_reason="HOLD: PyPI search answers with a JavaScript client "
                                 "challenge; not bypassed. PyPI JSON API is still used for per-package metadata."), []
        st["reason"] = e.get("error") or "no data"
        return finish_status(st, [], 1, 0), []
    cands = []
    for m in re.finditer(r'<span class="package-snippet__name">([^<]+)</span>.*?'
                         r'<p class="package-snippet__description">([^<]*)</p>', html_text, re.S):
        name, desc = m.group(1).strip(), m.group(2).strip()
        cands.append(make_candidate(sid, name, desc, f"https://pypi.org/project/{name}/", [e["id"]], A, pypi=name))
    st["raw_seen"] = len(cands)
    st["gated"] = sum(c["passed"] for c in cands)
    kept = top_passed(cands, cap)
    return finish_status(st, kept, 1, 1), kept


DOC_LINE = re.compile(r"^\s*-\s+\[(?P<title>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)\s*:?\s*(?P<desc>.*)$")


def collect_official_docs(F, A, cap):
    sid = "S7_OFFICIAL_DOCUMENTATION"
    st = new_status(sid, 4, "Official Claude documentation indexes (llms.txt)",
                    "GET code.claude.com/docs/llms.txt and platform.claude.com/llms.txt")
    attempted = ok = 0
    cands = []
    for idx in OFFICIAL_DOC_INDEXES:
        e, txt = F.get(idx, "collect", sid)
        st["requests"].append(e["id"])
        attempted += 1
        ok += int(e["ok"])
        if not txt:
            continue
        for line in txt.splitlines():
            m = DOC_LINE.match(line)
            if not m:
                continue
            title, url, desc = m.group("title"), m.group("url"), m.group("desc")
            if re.search(r"/(ja|ko|zh|fr|de|es|it|pt|ru|id)/", url):
                continue
            c = make_candidate(sid, title, desc, url, [e["id"]], A, doc_url=url, meta={"index": idx})
            cands.append(c)
    st["raw_seen"] = len(cands)
    st["gated"] = sum(c["passed"] for c in cands)
    kept = top_passed(cands, min(cap, 3))
    return finish_status(st, kept, attempted, ok), kept


def probe_claude_directory(F):
    sid = "S8_CLAUDE_PLUGIN_DIRECTORY"
    st = new_status(sid, 5, "Claude plugin / connector directory (web)", f"GET {CLAUDE_DIRECTORY}")
    e, txt = F.get(CLAUDE_DIRECTORY, "collect", sid)
    st["requests"].append(e["id"])
    if not txt:
        st["reason"] = f"{e.get('error') or e.get('status')}: no machine-readable listing reachable"
        return finish_status(st, [], 1, 0), []
    st["ok_requests"] = 1
    st["reason"] = (f"HTTP 200 ({e.get('final_url', e['url'])}) but no public machine-readable listing; "
                    "HTML not scraped (machine-first rule)")
    st["status"] = "PARTIAL"
    return st, []


# ---------------------------------------------------------------------------
# 11. DEDUPLICATE (pass 1 on collection keys, pass 2 after reading)
# ---------------------------------------------------------------------------

def strong_keys(c):
    ks = set()
    if c.get("gh") and c["gh"].get("path"):
        ks.add(gh_key(c["gh"]))
    if c.get("npm"):
        ks.add("npm:" + c["npm"].lower())
    if c.get("pypi"):
        ks.add("pypi:" + re.sub(r"[-_.]+", "-", c["pypi"].lower()))
    if c.get("mcpreg"):
        ks.add("mcpreg:" + c["mcpreg"].lower())
    if c.get("doc_url"):
        ks.add("url:" + c["doc_url"].lower().rstrip("/"))
    if not ks and c.get("candidate_url"):
        ks.add("url:" + c["candidate_url"].lower().rstrip("/"))
    return ks


NAME_NOISE = {"mcp", "server", "skill", "skills", "claude", "the", "ai", "agent", "tool", "tools", "official"}


def norm_name(name):
    n = (name or "").lower().split("/")[-1]
    toks = [t for t in re.split(r"[^a-z0-9]+", n) if t and t not in NAME_NOISE]
    return "-".join(toks)


def provider_of(c):
    if c.get("gh"):
        return c["gh"]["owner"].lower()
    if c.get("mcpreg"):
        parts = c["mcpreg"].split("/")[0].split(".")
        return parts[-1].lower() if parts[0] in ("io", "com", "dev", "ai", "app", "co", "net", "org") else parts[0]
    if c.get("npm") and c["npm"].startswith("@"):
        return c["npm"][1:].split("/")[0].lower()
    if (c.get("meta") or {}).get("publisher"):
        return c["meta"]["publisher"].lower()
    if (c.get("name") or "").count("/") == 1:
        return c["name"].split("/")[0].lower()
    return ""


def dedupe(cands):
    """Union candidates that share a strong key; flag same-repo / same-name look-alikes as POSSIBLE_DUPLICATE."""
    n = len(cands)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)

    key_owner = {}
    comparisons = 0
    for i, c in enumerate(cands):
        for k in strong_keys(c):
            if k in key_owner:
                union(i, key_owner[k])
            else:
                key_owner[k] = i
    # same repository root: merge a non-registry listing into the single project that lives there,
    # but keep distinct registry servers that happen to share a monorepo apart (possible duplicates).
    by_root = {}
    for i, c in enumerate(cands):
        if c.get("gh"):
            by_root.setdefault(gh_key(c["gh"], with_path=False), []).append(i)
    possible = {}
    for root, idxs in by_root.items():
        clusters = sorted({find(i) for i in idxs})
        if len(clusters) < 2:
            continue
        # distinct sub-paths (e.g. skills/pdf vs skills/docx) are distinct capabilities: never flagged
        pathful = [r for r in clusters if any(cands[j]["gh"].get("path") for j in idxs if find(j) == r)]
        reg_nopath = [r for r in clusters if r not in pathful and
                      any(cands[j].get("mcpreg") for j in idxs if find(j) == r)]
        rootonly = [r for r in clusters if r not in pathful and r not in reg_nopath]
        for a in reg_nopath[1:]:
            possible.setdefault(a, []).append((reg_nopath[0], f"same repository {root[3:]}, different registry server name"))
        anchors = pathful + reg_nopath
        for r in rootonly:
            if len(anchors) == 1:
                union(r, anchors[0])
            elif len(anchors) > 1:
                possible.setdefault(r, []).append((anchors[0], f"repository-level listing of {root[3:]}, which holds several capabilities"))
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    # name look-alikes across groups: same normalized name and same provider (or same homepage domain)
    roots = sorted(groups)
    for x in range(len(roots)):
        for y in range(x + 1, len(roots)):
            comparisons += 1
            a, b = cands[roots[x]], cands[roots[y]]
            na, nb = norm_name(a["name"]), norm_name(b["name"])
            if not na or na != nb:
                continue
            pa, pb = provider_of(a), provider_of(b)
            if pa and pa == pb:
                possible.setdefault(roots[y], []).append((roots[x], f"same normalized name '{na}' and provider '{pa}'"))
    return groups, possible, comparisons


# ---------------------------------------------------------------------------
# 9. READ SOURCE
# ---------------------------------------------------------------------------

def read_group(F, members):
    """Fetch primary files for one de-duplicated capability. Returns dict of what was read."""
    reads = {"skill_md": None, "readme": None, "manifest": None, "license_text": None, "npm_latest": None,
             "pypi": None, "doc_page": None, "files": []}

    def note(kind, e):
        reads["files"].append({"kind": kind, "url": e["url"], "fetch_id": e["id"], "status": e["status"],
                               "ok": e["ok"], "bytes": e["bytes"]})

    gh = next((m["gh"] for m in members if m.get("gh") and m["gh"].get("path")), None) or \
        next((m["gh"] for m in members if m.get("gh")), None)
    npm = next((m["npm"] for m in members if m.get("npm")), None)
    pypi = next((m["pypi"] for m in members if m.get("pypi")), None)
    doc = next((m["doc_url"] for m in members if m.get("doc_url")), None)
    pre_skill = next((m.get("_skill_md") for m in members if m.get("_skill_md")), None)
    if gh:
        p = gh.get("path", "")
        if p:
            e, t = F.get(raw_url(gh, f"{p}/SKILL.md"), "read", "READ")
            note("SKILL_MD", e)
            reads["skill_md"] = t or pre_skill
            if not t:
                e, t2 = F.get(raw_url(gh, f"{p}/README.md"), "read", "READ")
                note("README", e)
                reads["readme"] = t2
            e, lt = F.get(raw_url(gh, f"{p}/LICENSE.txt"), "read", "READ")
            note("LICENSE", e)
            reads["license_text"] = lt
        if not reads["readme"] and not reads["skill_md"]:
            e, t = F.get(raw_url(gh, "README.md"), "read", "READ")
            note("README", e)
            reads["readme"] = t
            if not p and t is not None and not npm and not pypi:
                e, sk = F.get(raw_url(gh, "SKILL.md"), "read", "READ")
                note("SKILL_MD", e)
                reads["skill_md"] = sk
        if not npm and not pypi and not p:
            e, pj = F.get(raw_url(gh, "package.json"), "read", "READ")
            note("MANIFEST_PACKAGE_JSON", e)
            if pj:
                try:
                    reads["manifest"] = {"kind": "package.json", "data": json.loads(pj)}
                except ValueError:
                    pass
            else:
                e, pp = F.get(raw_url(gh, "pyproject.toml"), "read", "READ")
                note("MANIFEST_PYPROJECT", e)
                if pp:
                    reads["manifest"] = {"kind": "pyproject.toml", "data": pp[:6000]}
        if not reads["license_text"] and not npm and not pypi:
            e, lt = F.get(raw_url(gh, "LICENSE"), "read", "READ")
            note("LICENSE", e)
            reads["license_text"] = lt
    if npm:
        e, data = F.get_json(f"https://registry.npmjs.org/{urllib.parse.quote(npm, safe='@')}/latest", "read", "READ")
        note("NPM_LATEST_MANIFEST", e)
        reads["npm_latest"] = data
        if data and not reads["manifest"]:
            reads["manifest"] = {"kind": "npm package.json (latest)", "data": data}
        if data and not gh:
            g2 = parse_github((data.get("repository") or {}).get("url") if isinstance(data.get("repository"), dict)
                              else data.get("repository"))
            if g2:
                e, t = F.get(raw_url(g2, "README.md"), "read", "READ")
                note("README", e)
                reads["readme"] = t
                reads["discovered_gh"] = g2
    if pypi:
        e, data = F.get_json(f"https://pypi.org/pypi/{urllib.parse.quote(pypi)}/json", "read", "READ")
        note("PYPI_JSON", e)
        reads["pypi"] = data
        if data and not reads["manifest"]:
            reads["manifest"] = {"kind": "pypi json", "data": {"info": data.get("info", {})}}
    if doc:
        e, t = F.get(doc, "read", "READ")
        note("DOC_PAGE", e)
        reads["doc_page"] = t
    return reads


# ---------------------------------------------------------------------------
# 10. NORMALIZE + 12. CLASSIFY
# ---------------------------------------------------------------------------

FORMAT_PATTERNS = [
    ("PDF", r"\bpdfs?\b"), ("DOCX/Word", r"\bdocx\b|\bword (documents?|files?)\b"), ("XLSX/Excel", r"\bxlsx\b|\bexcel\b"),
    ("CSV", r"\bcsv\b"), ("PPTX", r"\bpptx\b|powerpoint"), ("IMAGE", r"\bimages?\b|\bpng\b|\bjpe?g\b|screenshots?"),
    ("SCANNED", r"scanned"), ("HTML/URL", r"\bhtml\b|\burls?\b|web ?pages?"), ("EMAIL", r"\be-?mails?\b"),
    ("AUDIO", r"\baudio\b"),
]
OUTPUT_RE = re.compile(r"(?:\bto|\binto|\bas|→|->|\breturns?|\boutputs?|\bexports?(?: to)?|\bget)\s+"
                       r"(?:(?:clean|structured|validated|llm[- ]ready|per-page|machine[- ]readable|a|an)\s+)*"
                       r"(json|markdown|csv|excel|xlsx|word|plain text|text|html|rows|tables?|database|"
                       r"structured data|pdfs?|dataframes?)", re.I)
LICENSE_SIGNS = [
    ("MIT", r"\bmit license\b|permission is hereby granted, free of charge"),
    ("Apache-2.0", r"apache license,?\s+version 2\.0"),
    ("AGPL-3.0", r"gnu affero general public license"),
    ("LGPL", r"gnu lesser general public license"),
    ("GPL-3.0", r"gnu general public license\s+version 3"),
    ("GPL-2.0", r"gnu general public license\s+version 2"),
    ("MPL-2.0", r"mozilla public license"),
    ("BSD", r"redistribution and use in source and binary forms"),
    ("Unlicense", r"this is free and unencumbered software"),
    ("PROPRIETARY", r"proprietary|all rights reserved"),
]
PY_STD = set("os sys re json time typing pathlib io subprocess argparse collections datetime math logging "
             "itertools functools base64 tempfile shutil glob csv dataclasses enum uuid hashlib random".split())


def detect_license(text):
    t = (text or "")[:3000].lower()
    for spdx, pat in LICENSE_SIGNS:
        if re.search(pat, t):
            return spdx
    return "CUSTOM_OR_UNRECOGNIZED" if t.strip() else None


TOOL_NOISE = {"skills", "install", "add", "npm", "uv", "pip", "pip3", "python", "python3", "node", "all", "type",
              "run", "init", "create", "g", "y", "e", "r", "u", "s", "sudo", "brew", "git", "cd", "docker"}


def detect_tools(texts, deps=None):
    tools = []
    for t in texts:
        if not t:
            continue
        for block in re.findall(r"```(?:python|py)\n(.*?)```", t, re.S)[:40]:
            for m in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_][\w]*)", block, re.M):
                if m.group(1) not in PY_STD:
                    tools.append(m.group(1))
        for m in re.finditer(r"pip3? install\s+([^\n`|;&]+)", t):
            for x in m.group(1).split()[:5]:
                x = re.sub(r"\[.*$", "", x.strip("'\""))
                if x and not x.startswith("-") and re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$", x):
                    tools.append(x)
        for m in re.finditer(r"\b(?:npm (?:install|i|add)|npx|uvx|pnpm add|yarn add)\s+((?:-{1,2}[\w-]+\s+)*)(@?[\w][\w./@-]*)", t):
            tools.append(m.group(2))
    tools += list((deps or {}).keys())
    out = [re.sub(r"(?<=[^@])@.*$", "", x.strip("`'\"")) for x in tools]   # drop @version suffixes
    return uniq([x for x in out if len(x) > 1 and x.lower() not in TOOL_NOISE])[:12]


def classify(text, rec_type, A):
    t = text.lower()
    rules = [
        ("DOCUMENT_PROCESSING", r"\bpdfs?\b|\bdocx?\b|\bdocuments?\b|\bword\b"),
        ("DATA_EXTRACTION", r"extract|\bpars(e|es|ing|er)\b"),
        ("OCR", r"\bocr\b|optical character|scanned"),
        ("TABLE_EXTRACTION", r"\btables?\b.{0,40}(extract|pars|detect)|(extract|pars)\w*.{0,40}\btables?\b"),
        ("SPREADSHEET", r"\bexcel\b|\bxlsx\b|spreadsheet|\bcsv\b"),
        ("CONVERSION", r"conver(t|ts|sion|ter)|to markdown|→ markdown"),
        ("STRUCTURED_OUTPUT", r"\bjson\b|structured|\bschema\b"),
        ("AUTOMATION", r"automat|workflow|pipeline|\bbatch\b"),
        ("WEB_EXTRACTION", r"web ?pages?|\bhtml\b|scrap|crawl"),
        ("INVOICE_RECEIPT", r"invoices?|receipts?"),
        ("FORMS", r"\bforms?\b"),
    ]
    cats = [name for name, pat in rules if re.search(pat, t)]
    if rec_type.startswith("MCP") or re.search(r"\bmcp\b|model context protocol", t):
        cats.append("MCP")
    if rec_type == "AGENT_SKILL":
        cats.append("AGENT_SKILL")
    if rec_type in ("CODE_LIBRARY", "REPOSITORY") or re.search(r"\blibrary\b|\bsdk\b|\bcli\b", t):
        cats.append("DEVELOPER_TOOL")
    if rec_type == "PLATFORM_FEATURE_DOC":
        cats.append("PLATFORM_FEATURE")
    new = []
    # section 12: create a category when a question concept is present but no rule covers it
    covered_map = {"pdf": "DOCUMENT_PROCESSING", "document": "DOCUMENT_PROCESSING", "spreadsheet": "SPREADSHEET",
                   "table": "TABLE_EXTRACTION", "invoice": "INVOICE_RECEIPT", "web": "WEB_EXTRACTION",
                   "form": "FORMS", "scanned": "OCR"}
    for cid in A["primary_ids"]:
        c = CONCEPTS[cid]
        if c["facet"] != "OBJECT" or cid in covered_map:
            continue
        if any(re.search(p, t) for p in c["match"]):
            label = f"{cid.upper()}_PROCESSING"
            cats.append(label)
            new.append(label)
    return uniq(cats), new


def normalize(idx, members, reads, A, run_tag):
    primary = max(members, key=lambda m: (m["score"], bool(m.get("gh")), len(m["description"] or "")))
    srcs = uniq([m["source_id"] for m in members])
    fm, skill_body = parse_frontmatter(reads.get("skill_md") or "") if reads.get("skill_md") else ({}, "")
    readme = (reads.get("readme") or "")[: LIMITS["readme_chars"]]
    npm_latest = reads.get("npm_latest") or {}
    pypi_info = ((reads.get("pypi") or {}).get("info")) or {}
    reg = next((m["meta"] for m in members if m.get("mcpreg")), None)
    npm_meta = next((m["meta"] for m in members if m["source_id"] == "S5_NPM_REGISTRY"), {})
    gh = next((m["gh"] for m in members if m.get("gh") and m["gh"].get("path")), None) or \
        next((m["gh"] for m in members if m.get("gh")), None) or reads.get("discovered_gh")
    ev = {}

    desc = fm.get("description") or max((m["description"] or "" for m in members), key=len) or \
        npm_latest.get("description") or pypi_info.get("summary") or "UNKNOWN"
    ev["DESCRIPTION"] = "SKILL.md frontmatter" if fm.get("description") else "source listing/registry description"
    name = fm.get("name") or primary["name"]
    if gh and gh.get("path") and "/" not in name:
        name = f"{gh['owner']}/{gh['repo']}/{name}"   # qualify bare skill names such as 'pdf'

    # TYPE
    if reads.get("skill_md") or primary["source_id"] == "S1_ANTHROPIC_OFFICIAL_SKILLS":
        rtype = "AGENT_SKILL"
    elif reg or re.search(r"\bmcp server\b|model context protocol", (desc + " " + readme[:4000]).lower()):
        rtype = "MCP_SERVER"
    elif any(m["source_id"] == "S7_OFFICIAL_DOCUMENTATION" for m in members):
        rtype = "PLATFORM_FEATURE_DOC"
    elif npm_latest or pypi_info:
        rtype = "CODE_LIBRARY"
    else:
        rtype = "REPOSITORY"
    ev["TYPE"] = {"AGENT_SKILL": "SKILL.md present", "MCP_SERVER": "MCP registry entry or README states MCP server",
                  "PLATFORM_FEATURE_DOC": "official documentation page", "CODE_LIBRARY": "package registry metadata",
                  "REPOSITORY": "GitHub repository listing"}[rtype]

    # PROVIDER
    if gh:
        provider = gh["owner"]
        ev["PROVIDER"] = "GitHub owner"
    elif reg:
        provider = reg["registry_name"].split("/")[0]
        ev["PROVIDER"] = "MCP registry namespace"
    elif npm_meta.get("publisher"):
        provider = npm_meta["publisher"]
        ev["PROVIDER"] = "npm publisher"
    elif rtype == "PLATFORM_FEATURE_DOC":
        provider = "Anthropic"
        ev["PROVIDER"] = "official docs domain"
    else:
        provider = "UNKNOWN"

    text_for_detect = " ".join([name, desc, fm.get("description", ""), skill_body[:20000], readme,
                                " ".join(npm_latest.get("keywords") or []), pypi_info.get("summary") or ""])
    short_text = " ".join([name, desc, fm.get("description", "")] + [m["description"] or "" for m in members])
    tl = text_for_detect.lower()

    fmt_in = [lab for lab, pat in FORMAT_PATTERNS if re.search(pat, (desc + " " + fm.get("description", "")).lower())]
    outs = uniq([re.sub(r"S$", "", m.group(1).upper()) if m.group(1).lower() in ("pdfs", "tables", "dataframes") else m.group(1).upper()
                 for m in OUTPUT_RE.finditer(desc + " " + fm.get("description", "") + " " + readme[:6000])])
    inp = fmt_in or "UNKNOWN"
    out = outs or "UNKNOWN"
    ev["INPUT"] = "formats mentioned in description/SKILL.md (direction not verified)" if fmt_in else "not stated"
    ev["OUTPUT"] = "'to/into/as/returns <format>' phrases in description/README" if outs else "not stated"

    deps = {}
    man = reads.get("manifest") or {}
    if isinstance(man.get("data"), dict):
        deps = man["data"].get("dependencies") or {}
    tools = detect_tools([reads.get("skill_md"), readme], deps)
    if fm.get("allowed-tools"):
        tools = uniq([t.strip() for t in fm["allowed-tools"].split(",")] + tools)
    ev["TOOLS"] = "imports/install commands in SKILL.md/README code, manifest dependencies" if tools else "none detected"

    env_names = uniq([re.sub(r"^YOUR_", "", x) for x in
                      re.findall(r"\b[A-Z][A-Z0-9_]*(?:API_KEY|_TOKEN|_SECRET|_KEY)\b", readme + " " + (skill_body or ""))])
    reg_env = [v["name"] for p in (reg or {}).get("packages", []) for v in p.get("env", []) if v.get("isSecret") or
               re.search(r"KEY|TOKEN|SECRET", v.get("name") or "")]
    remotes = [r["url"] for r in (reg or {}).get("remotes", []) if r.get("url")]
    api_bits = []
    if env_names or reg_env:
        api_bits.append("keys: " + ", ".join(uniq(reg_env + env_names)[:5]))
    if remotes:
        api_bits.append("remote endpoint: " + remotes[0])
    if re.search(r"\bapi key\b|\bapi_key\b|rest api", tl):
        api_bits.append("README/description mentions an API")
    api = "YES - " + "; ".join(api_bits) if api_bits else "UNKNOWN"

    mcp = "YES" if (reg or re.search(r"\bmcp\b|model context protocol", tl)) else "NOT_DETECTED"
    ev["MCP"] = "registry entry" if reg else ("text mention" if mcp == "YES" else "no mention found")

    pkgs = (reg or {}).get("packages", [])
    if rtype == "AGENT_SKILL":
        code_exec = "YES - SKILL.md instructs running code" if re.search(r"```(python|bash|sh|js)", reads.get("skill_md") or "") \
            else "UNKNOWN"
    elif remotes and not pkgs:
        code_exec = "NO_LOCAL - hosted remote MCP (runs on provider side)"
    elif pkgs or npm_latest or pypi_info:
        code_exec = "YES - installable package runs locally (not executed in this pilot)"
    else:
        code_exec = "UNKNOWN"

    if re.search(r"never leave|files never|on[- ]device|offline|runs? locally|local[- ]first|no network", tl):
        net = "CLAIMS_LOCAL - text states local/offline processing"
    elif remotes or re.search(r"api key|hosted|cloud|pay[- ]per|x402", tl):
        net = "YES - remote service/API"
    else:
        net = "UNKNOWN"
    file_access = "YES - reads user files (per text)" if re.search(
        r"file path|local files?|filesystem|upload|\.pdf\b|\bfiles?\b", tl) else "UNKNOWN"

    if reg_env or env_names or re.search(r"requires? (an? )?(api key|account)|bring your own api key|sign ?up", tl):
        auth = "YES - " + ", ".join(uniq(reg_env + env_names)[:4] or ["API key/account mentioned"])
    elif re.search(r"no (signup|sign-up|login|api key)|without (an )?api key|no account", tl):
        auth = "NO - text claims no key/login"
    elif rtype == "AGENT_SKILL" and not env_names:
        auth = "NO_EVIDENCE_OF_AUTH - SKILL.md mentions no key"
    else:
        auth = "UNKNOWN"

    cost_bits = []
    if re.search(r"pay[- ]per|prepaid|\bcredits?\b|x402|usdc|subscription|pricing|paid", tl):
        cost_bits.append("PAID_OR_METERED_MENTIONED")
    if re.search(r"\bfree\b", tl):
        cost_bits.append("FREE_MENTIONED")
    cost = " + ".join(cost_bits) if cost_bits else "UNKNOWN"

    lic = None
    if fm.get("license"):
        lic, ev["LICENSE"] = fm["license"], "SKILL.md frontmatter"
    if not lic and npm_latest.get("license"):
        lic, ev["LICENSE"] = str(npm_latest["license"]), "npm manifest"
    if not lic and npm_meta.get("license"):
        lic, ev["LICENSE"] = str(npm_meta["license"]), "npm search metadata"
    if not lic and (pypi_info.get("license_expression") or pypi_info.get("license")):
        pl = pypi_info.get("license_expression") or pypi_info["license"]
        lic, ev["LICENSE"] = (pl if len(pl) <= 40 else (detect_license(pl) or "CUSTOM_OR_UNRECOGNIZED")), "PyPI metadata"
    if not lic and reads.get("license_text"):
        lic, ev["LICENSE"] = detect_license(reads["license_text"]), "LICENSE file text"
    lic = lic or "UNKNOWN"

    last = None
    if reg and reg.get("updatedAt"):
        last, ev["LAST_UPDATED"] = reg["updatedAt"], "MCP registry updatedAt"
    elif npm_meta.get("date"):
        last, ev["LAST_UPDATED"] = npm_meta["date"], "npm search date"
    elif reads.get("pypi"):
        rel = (reads["pypi"].get("urls") or [{}])
        if rel and rel[0].get("upload_time_iso_8601"):
            last, ev["LAST_UPDATED"] = rel[0]["upload_time_iso_8601"], "PyPI latest upload"
    last = last or "UNKNOWN"
    if last == "UNKNOWN":
        ev["LAST_UPDATED"] = "GitHub commit API not reachable in this environment"

    read_ok = [f for f in reads["files"] if f["ok"]]
    primary_doc = any(f["kind"] in ("SKILL_MD", "README", "DOC_PAGE") and f["ok"] for f in reads["files"]) or \
        bool(reads.get("skill_md"))
    manifest_ok = any(f["kind"].startswith(("MANIFEST", "NPM", "PYPI", "LICENSE")) and f["ok"] for f in reads["files"])
    if primary_doc and manifest_ok:
        level = "E3_PRIMARY_DOC_AND_MANIFEST_READ"
    elif primary_doc:
        level = "E2_PRIMARY_DOC_READ"
    elif manifest_ok or reg or npm_meta:
        level = "E1_REGISTRY_METADATA_ONLY"
    else:
        level = "E0_LISTING_TEXT_ONLY"

    if rtype == "AGENT_SKILL":
        trigger = fm.get("description") or "UNKNOWN"
        ev["TRIGGER"] = "SKILL.md description (this is what makes Claude load the skill)"
    elif rtype == "MCP_SERVER":
        trigger = "Tool call from an MCP client (tool list not introspected in this pilot)"
        ev["TRIGGER"] = "by type"
    elif rtype == "CODE_LIBRARY":
        trigger = "Programmatic import / CLI call from host code"
        ev["TRIGGER"] = "by type"
    elif rtype == "PLATFORM_FEATURE_DOC":
        trigger = "Claude platform feature, used via API/app request"
        ev["TRIGGER"] = "by type"
    else:
        trigger = "UNKNOWN"

    hits = primary["hits"]
    lab = lambda ids: "/".join(CONCEPTS[i]["ko"] for i in ids) or "-"
    use_case = f"{lab(hits['OBJECT'])} -> {lab(hits['ACTION'] + [i for i in hits['SECONDARY'] if CONCEPTS[i]['facet'] == 'ACTION'])}" \
               f" -> {lab(hits['OUTPUT'] + [i for i in hits['SECONDARY'] if CONCEPTS[i]['facet'] == 'OUTPUT'])}"
    ev["USE_CASE"] = "derived from question concepts matched in this candidate's text"

    cats, new_cats = classify(short_text, rtype, A)

    source_url = primary["candidate_url"]
    repo_url = gh_human_url({**gh, "path": ""}) if gh else ((reg or {}).get("repository") or "UNKNOWN")
    all_fetch = uniq([f for m in members for f in m["fetch_ids"]] + [f["fetch_id"] for f in reads["files"] if f["ok"]])
    rec = {
        "CAPABILITY_ID": f"{run_tag}-{idx:03d}-{slug(name, 32)}",
        "NAME": name,
        "TYPE": rtype,
        "PROVIDER": provider,
        "SOURCE_URL": source_url,
        "REPOSITORY_URL": repo_url,
        "DESCRIPTION": clip(desc, 500),
        "USE_CASE": use_case,
        "TRIGGER": clip(trigger, 400),
        "INPUT": inp,
        "OUTPUT": out,
        "TOOLS": tools or "UNKNOWN",
        "API": api,
        "MCP": mcp,
        "CODE_EXECUTION": code_exec,
        "FILE_ACCESS": file_access,
        "NETWORK_ACCESS": net,
        "AUTH_REQUIRED": auth,
        "COST": cost,
        "LICENSE": lic,
        "LAST_UPDATED": last,
        "EVIDENCE_LEVEL": level,
        "CATEGORIES": cats,
        "NEW_CATEGORIES_CREATED": new_cats,
        "RELEVANCE_SCORE": primary["score"],
        "MATCHED_CONCEPTS": {k: v for k, v in hits.items() if v},
        "FOUND_IN_SOURCES": srcs,
        "FIELD_BASIS": ev,
        "EVIDENCE": {"fetch_ids": all_fetch,
                     "files_read": [f for f in reads["files"]],
                     "files_read_ok": len(read_ok)},
    }
    return rec


# ---------------------------------------------------------------------------
# 13. SIMPLE DREAM FIT
# ---------------------------------------------------------------------------

def dream_fit(rec, all_recs, A):
    cats = set(rec["CATEGORIES"])
    commerce_ctx = any(i in A["primary_ids"] for i in ("catalog", "product", "supplier", "ecommerce"))
    obj_label = "·".join(f["label"] for f in A["facets"]["OBJECT"]) or "입력 자료"
    if {"OCR"} & cats and {"DATA_EXTRACTION", "TABLE_EXTRACTION"} & cats:
        use = f"스캔본 포함 {obj_label}에서 텍스트·표를 읽어 구조화하는 추출 단계"
    elif "TABLE_EXTRACTION" in cats or "DATA_EXTRACTION" in cats:
        use = f"{obj_label}에서 필드·표를 뽑아 JSON/행 데이터로 만드는 추출 단계"
    elif "OCR" in cats:
        use = "스캔/이미지 문서를 텍스트로 바꾸는 전처리 단계"
    elif "SPREADSHEET" in cats:
        use = "추출 결과를 Excel/CSV로 정리·검증하는 적재 단계"
    elif "CONVERSION" in cats:
        use = "문서를 Markdown/텍스트로 바꿔 다음 AI 단계에 넘기는 변환 단계"
    else:
        use = "문서 처리 파이프라인의 보조 단계 (역할 추가 확인 필요)"
    if commerce_ctx:
        target = "DATA FACTORY - 공급업체 카탈로그 → 상품 데이터(DB) 라인"
    elif "INVOICE_RECEIPT" in cats:
        target = "BACK-OFFICE FACTORY - 인보이스/영수증 처리 라인"
    elif "WEB_EXTRACTION" in cats:
        target = "RESEARCH FACTORY - 웹 수집 라인"
    else:
        target = "DATA FACTORY - 문서 → 구조화 데이터 라인"
    complement = {
        "OCR": {"TABLE_EXTRACTION", "DATA_EXTRACTION", "SPREADSHEET"},
        "DATA_EXTRACTION": {"SPREADSHEET", "OCR", "STRUCTURED_OUTPUT"},
        "TABLE_EXTRACTION": {"SPREADSHEET", "OCR"},
        "SPREADSHEET": {"DATA_EXTRACTION", "TABLE_EXTRACTION", "OCR"},
        "CONVERSION": {"DATA_EXTRACTION", "STRUCTURED_OUTPUT"},
        "AGENT_SKILL": {"MCP"},
        "MCP": {"AGENT_SKILL"},
    }
    want = set()
    for c in cats:
        want |= complement.get(c, set())
    want -= cats
    combos = []
    for other in all_recs:
        if other is rec:
            continue
        gain = sorted(set(other["CATEGORIES"]) & want)
        if gain:
            combos.append((len(gain), other["RELEVANCE_SCORE"], other["CAPABILITY_ID"], other["NAME"], gain))
    combos.sort(key=lambda x: (-x[0], -x[1]))
    comb = [f"{c[2]} ({c[3]}) adds {'+'.join(c[4])}" for c in combos[:3]] or ["NONE_FOUND_IN_THIS_RUN"]
    val = []
    if {"DATA_EXTRACTION", "TABLE_EXTRACTION", "STRUCTURED_OUTPUT"} & cats:
        val += ["DATA_ASSET", "INTERNAL_AUTOMATION"]
    if {"OCR", "AUTOMATION", "SPREADSHEET"} & cats:
        val += ["COST_REDUCTION", "INTERNAL_AUTOMATION"]
    if "CONVERSION" in cats:
        val.append("CONTENT_PRODUCTION")
    if commerce_ctx and {"DATA_EXTRACTION", "TABLE_EXTRACTION", "OCR", "SPREADSHEET"} & cats:
        val.append("COMMERCE")
    if "WEB_EXTRACTION" in cats or rec["TYPE"] == "PLATFORM_FEATURE_DOC":
        val.append("RESEARCH")
    return {"DREAM_USE": use, "DREAM_FACTORY_TARGET": target, "POSSIBLE_COMBINATION": comb,
            "POSSIBLE_VALUE": uniq(val) or ["UNKNOWN"],
            "REVENUE_EVIDENCE": "NOT_VERIFIED - no revenue was measured; values above are possibilities only"}


# ---------------------------------------------------------------------------
# 14. NEXT QUESTION GENERATION + 15. AI KEYWORD GENERATION
# ---------------------------------------------------------------------------

def josa(word, pair):
    """Korean particle after a word: pair like '을/를', '이/가', '과/와', '로'. Non-Hangul endings get '을(를)' style."""
    last = (word or " ").rstrip()[-1:]
    if pair == "로":
        if "가" <= last <= "힣":
            b = (ord(last) - 0xAC00) % 28
            return "로" if b in (0, 8) else "으로"
        return "(으)로"
    with_b, without_b = pair.split("/")
    if "가" <= last <= "힣":
        return with_b if (ord(last) - 0xAC00) % 28 else without_b
    return f"{with_b}({without_b})"


def filter_discovered(terms, A):
    """Keep tool names found in the sources that share a stem with the question's concepts."""
    stems = set()
    for cid in A["primary_ids"] + A["implied_ids"]:
        c = CONCEPTS[cid]
        if c["facet"] == "CONTEXT":
            continue
        for t in c["terms"] + c["reg"]:
            stems.add(t.split()[0][:5].lower())
    keep = [t for t in terms if any(s in t.lower() for s in stems)]
    return uniq(keep)


def keywords_for(question, discovered_terms, names=()):
    for n in sorted(names, key=len, reverse=True):
        question = question.replace(n, " ")
    A = analyze_question(question)
    q = A["queries"]
    return {
        "CORE_KEYWORDS": uniq(q["CORE_QUERY"].split() + q["TECHNICAL_TERMS"][:4]),
        "GITHUB_KEYWORDS": uniq([q["GITHUB_QUERY"]] + [f"topic:{t.replace(' ', '-')}" for t in q["TECHNICAL_TERMS"][:3]]),
        "MCP_KEYWORDS": uniq([q["MCP_QUERY"]] + q["MCP_REGISTRY_TERMS"]),
        "SKILL_KEYWORDS": uniq([q["SKILL_QUERY"], "claude skill " + " ".join(q["CORE_QUERY"].split()[:3])]),
        "WEB_KEYWORDS": q["WEB_QUERIES"],
        "DISCOVERED_TERMS_FROM_SOURCES": discovered_terms[:8],
        "_concepts": A["primary_ids"],
    }


def generate_next_questions(recs, A):
    by = lambda cat: sorted([r for r in recs if cat in r["CATEGORIES"]], key=lambda r: -r["RELEVANCE_SCORE"])
    ocr, ext, tab, sheet = by("OCR"), by("DATA_EXTRACTION"), by("TABLE_EXTRACTION"), by("SPREADSHEET")
    schema = [r for r in recs if re.search(r"\bschema\b|\bjson\b", (r["DESCRIPTION"] + str(r["OUTPUT"])).lower())]
    img = [r for r in recs if re.search(r"\bimages?\b", r["DESCRIPTION"].lower())]
    skills = by("AGENT_SKILL")
    mcps = by("MCP")
    local = [r for r in recs if not str(r["AUTH_REQUIRED"]).startswith("YES") and
             not str(r["NETWORK_ACCESS"]).startswith("YES")]
    objs = [f["concept"] for f in A["facets"]["OBJECT"]]
    obj_label = " ".join(CONCEPTS[o]["ko"] for o in objs[:2]) or "문서"
    commerce = any(i in A["primary_ids"] for i in ("catalog", "product", "supplier", "ecommerce"))
    target_doc = "공급업체 카탈로그" if commerce else obj_label
    nm = lambda r: r["NAME"]
    ids = lambda rs: [r["CAPABILITY_ID"] for r in rs]
    out = []

    extractor = tab + [r for r in ext if r not in tab]
    b = next((r for r in extractor if ocr and r is not ocr[0]), None)
    if ocr and b:
        a = ocr[0]
        out.append(dict(
            QUESTION=f"{nm(a)}의 OCR과 {nm(b)}의 PDF 표 추출을 결합하면 스캔된 {target_doc}까지 구조화된 데이터(JSON)로 만들 수 있는가?",
            WHY=f"이번 실행에서 OCR 분류 {len(ocr)}개, 추출 분류 {len(extractor)}개가 확인됐지만 둘을 이어 붙인 검증 사례는 수집되지 않았다 (NOT_MEASURED).",
            SOURCE_CAPABILITIES=ids([a, b])))
    a = extractor[0] if extractor else None
    b = next((r for r in sheet if r is not a), None)
    if a and b:
        out.append(dict(
            QUESTION=f"{nm(a)}의 PDF 표 추출 결과를 {nm(b)}{josa(nm(b), '로')} 넘겨 Excel 또는 데이터베이스 적재까지 자동화할 수 있는가?",
            WHY=f"추출 후보 {len(extractor)}개와 스프레드시트 후보 {len(sheet)}개가 따로 존재한다. 출력 형식(JSON/CSV)이 서로 맞는지는 확인되지 않았다.",
            SOURCE_CAPABILITIES=ids([a, b])))
    for o in objs:
        cover = [r for r in recs if o in r["MATCHED_CONCEPTS"].get("OBJECT", [])]
        if len(cover) <= 1:
            if o == "catalog":
                q = "카탈로그(상품 목록) PDF에서 상품명·가격·규격 필드를 스키마 기반으로 추출하는 공개 Capability가 존재하는가?"
            else:
                q = f"{CONCEPTS[o]['ko']} 전용 추출 Capability가 공개 Source에 존재하는가?"
            ko = CONCEPTS[o]["ko"]
            said = f"{len(cover)}개뿐이다" if cover else "하나도 없다"
            out.append(dict(QUESTION=q,
                            WHY=f"질문의 핵심 대상 '{ko}'{josa(ko, '을/를')} 설명에서 직접 언급한 후보가 {said} (공백 영역).",
                            SOURCE_CAPABILITIES=ids(cover) or ids(extractor[:1])))
    if commerce or img:
        out.append(dict(
            QUESTION="상품 이미지와 텍스트를 동시에 추출할 수 있는 Capability가 존재하는가?",
            WHY=f"이미지를 언급한 후보는 {len(img)}개다. 카탈로그 데이터화에는 상품 사진과 설명을 짝지어야 하지만 이번 후보들은 대부분 텍스트/표 중심이다.",
            SOURCE_CAPABILITIES=ids(img[:3]) or ids(extractor[:2])))
    if schema:
        out.append(dict(
            QUESTION=f"JSON 스키마 기반 추출을 지원하는 {', '.join(nm(r) for r in schema[:2])}{josa(nm(schema[:2][-1]), '을/를')} {target_doc} 상품 스키마에 적용하면 데이터베이스 레코드를 바로 만들 수 있는가?",
            WHY=f"{len(schema)}개 후보가 JSON/스키마 출력을 언급한다. 스키마를 우리 쪽 필드로 바꿔 끼울 수 있는지는 확인되지 않았다.",
            SOURCE_CAPABILITIES=ids(schema[:3])))
    if local:
        out.append(dict(
            QUESTION=f"API 키 없이 로컬에서 실행 가능한 후보({len(local)}개)만으로 {obj_label} → 구조화 데이터 추출 파이프라인을 구성할 수 있는가?",
            WHY=f"전체 {len(recs)}개 중 {len(recs) - len(local)}개는 인증 또는 외부 서비스가 필요하거나 표시돼 있다. 비용·보안 면에서 로컬 조합을 먼저 확인할 가치가 있다.",
            SOURCE_CAPABILITIES=ids(local[:4])))
    if skills and mcps:
        out.append(dict(
            QUESTION=f"Agent Skill({nm(skills[0])})의 절차와 MCP 서버({nm(mcps[0])})의 도구 호출을 결합해 문서 추출 작업을 한 번의 요청으로 자동화할 수 있는가?",
            WHY="Skill은 절차와 코드를, MCP는 외부 도구 호출을 제공한다. 두 형태가 이번 실행에서 모두 발견됐다.",
            SOURCE_CAPABILITIES=ids([skills[0], mcps[0]])))
    if len(extractor) >= 2:
        out.append(dict(
            QUESTION=f"{nm(extractor[0])}{josa(nm(extractor[0]), '과/와')} {nm(extractor[1])}의 PDF 표 추출 정확도를 비교할 공개 벤치마크나 테스트 데이터셋이 있는가?",
            WHY="같은 역할의 후보가 여러 개라서 고르려면 정확도 근거가 필요하다. 이번 파일럿은 정확도를 측정하지 않았다.",
            SOURCE_CAPABILITIES=ids(extractor[:2])))
    # fallback so a sparse run still yields >= 5 questions
    generic = [
        f"{obj_label} 추출 결과의 품질을 자동으로 검증하는 공개 도구가 있는가?",
        f"{obj_label} 추출을 대량 배치로 돌릴 때 비용이 가장 낮은 공개 Capability 조합은 무엇인가?",
        f"한국어 {obj_label}에서도 같은 추출이 동작하는 Capability가 있는가?",
    ]
    for g in generic:
        if len(out) >= 5:
            break
        out.append(dict(QUESTION=g, WHY="수집 결과가 적어 일반 확장 질문을 추가했다.",
                        SOURCE_CAPABILITIES=ids(recs[:2])))
    seen, final = {A["question"].strip()}, []
    for q in out:
        if q["QUESTION"] not in seen:
            seen.add(q["QUESTION"])
            final.append(q)
    return final[:8]


# ---------------------------------------------------------------------------
# 16. OUTBOX CANDIDATES
# ---------------------------------------------------------------------------

def build_outbox(recs, nqs, run_tag):
    ev_bonus = {"E3": 3, "E2": 2, "E1": 1, "E0": 0}
    ref_count = {}
    for q in nqs:
        for cid in q["SOURCE_CAPABILITIES"]:
            ref_count[cid] = ref_count.get(cid, 0) + 1

    def rank(r):
        combos = 0 if r["DREAM_FIT"]["POSSIBLE_COMBINATION"] == ["NONE_FOUND_IN_THIS_RUN"] else len(r["DREAM_FIT"]["POSSIBLE_COMBINATION"])
        return r["RELEVANCE_SCORE"] + ev_bonus[r["EVIDENCE_LEVEL"][:2]] + 2 * ref_count.get(r["CAPABILITY_ID"], 0) + combos

    ranked = sorted([r for r in recs if r["DEDUP_STATUS"] != "POSSIBLE_DUPLICATE"], key=lambda r: -rank(r))
    out = []
    for i, r in enumerate(ranked[:3], 1):
        q = next((q["QUESTION"] for q in nqs if r["CAPABILITY_ID"] in q["SOURCE_CAPABILITIES"]), nqs[0]["QUESTION"] if nqs else "UNKNOWN")
        out.append({
            "OUTBOX_CANDIDATE_ID": f"OBX-{run_tag}-{i:02d}",
            "SOURCE": r["SOURCE_URL"],
            "CAPABILITY": f"{r['CAPABILITY_ID']} | {r['NAME']} | {r['TYPE']}",
            "WHY_INTERESTING": (f"relevance {r['RELEVANCE_SCORE']}, {r['EVIDENCE_LEVEL']}, categories "
                                f"{'/'.join(r['CATEGORIES'][:5])}, referenced by {ref_count.get(r['CAPABILITY_ID'], 0)} next question(s), "
                                f"found in {len(r['FOUND_IN_SOURCES'])} source(s)"),
            "DREAM_USE": r["DREAM_FIT"]["DREAM_USE"],
            "NEXT_RESEARCH_QUESTION": q,
            "STATUS": "DISCOVERED",
            "AUTHORITY": "NONE",
            "RANK_SCORE": rank(r),
        })
    return out


# ---------------------------------------------------------------------------
# 19. SELF TEST
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ["CAPABILITY_ID", "NAME", "TYPE", "PROVIDER", "SOURCE_URL", "REPOSITORY_URL", "DESCRIPTION",
                   "USE_CASE", "TRIGGER", "INPUT", "OUTPUT", "TOOLS", "API", "MCP", "CODE_EXECUTION", "FILE_ACCESS",
                   "NETWORK_ACCESS", "AUTH_REQUIRED", "COST", "LICENSE", "LAST_UPDATED", "EVIDENCE_LEVEL"]


def self_test(res):
    A, recs, log = res["analysis"], res["capabilities"], res["fetch_log"]
    ok_ids = {e["id"] for e in log if e["ok"]}
    proven = [r for r in recs if r["EVIDENCE"]["fetch_ids"] and all(f in ok_ids for f in r["EVIDENCE"]["fetch_ids"])]
    any_ok = bool(ok_ids)
    t = []

    def add(n, name, cond, detail, hold=False):
        t.append({"test": f"TEST {n}", "name": name, "result": "HOLD" if hold else ("PASS" if cond else "FAIL"),
                  "detail": detail})

    add(1, "natural-language question accepted", bool(res["input"]["question"].strip()) and
        bool(A["primary_ids"] or A["free_keywords"]),
        f"question via {res['input']['input_mode']}; concepts={A['primary_ids']}; free={A['free_keywords']}")
    qs = A["queries"]
    add(2, "search queries generated", all(qs.get(k) for k in ("CORE_QUERY", "GITHUB_QUERY", "SKILL_QUERY", "MCP_QUERY")),
        f"CORE_QUERY='{qs['CORE_QUERY']}', {len(qs['TECHNICAL_TERMS'])} technical terms")
    add(3, ">=5 real public-source candidates", len(proven) >= LIMITS["min_results"],
        f"{len(proven)} capabilities backed by successful fetches in this run "
        f"({sum(e['ok'] for e in log)}/{len(log)} requests ok)", hold=not any_ok)
    add(4, "source URL kept", recs and all(str(r["SOURCE_URL"]).startswith("http") for r in recs),
        f"{sum(str(r['SOURCE_URL']).startswith('http') for r in recs)}/{len(recs)} records have http(s) SOURCE_URL")
    add(5, "capability records created (full schema)", recs and all(all(f in r for f in REQUIRED_FIELDS) for r in recs),
        f"{len(recs)} records x {len(REQUIRED_FIELDS)} required fields")
    d = res["dedup"]
    add(6, "deduplication performed", d["pairwise_name_comparisons"] > 0 or d["raw_candidates"] > d["groups_after_pass1"],
        f"raw {d['raw_candidates']} -> groups {d['groups_after_pass1']} (merged {d['merged_away']}), "
        f"possible duplicates {d['possible_duplicates']}, pairwise comparisons {d['pairwise_name_comparisons']}")
    nq = res["next_questions"]
    add(7, ">=5 next questions", len(nq) >= 5, f"{len(nq)} generated")
    channels = ("CORE_KEYWORDS", "GITHUB_KEYWORDS", "MCP_KEYWORDS", "SKILL_KEYWORDS", "WEB_KEYWORDS")
    filled = [q for q in nq if all(q["AI_KEYWORDS"].get(k) for k in channels)]
    add(8, "next search keywords generated", bool(nq) and len(filled) == len(nq),
        f"all 5 keyword channels filled for {len(filled)}/{len(nq)} questions")
    ob = res["outbox"]
    add(9, "OUTBOX candidates generated", 1 <= len(ob) <= 3 and all(o["STATUS"] == "DISCOVERED" and o["AUTHORITY"] == "NONE" for o in ob),
        f"{len(ob)} candidates, all STATUS=DISCOVERED AUTHORITY=NONE")
    return t


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run(question, out_dir, input_mode, parent=None):
    started = now_utc()
    run_tag = "DKSC-" + started.strftime("%m%d%H%M%S")
    F = Fetcher(LIMITS["request_budget"], LIMITS["timeout_s"])
    errors = []
    A = analyze_question(question)
    cap = LIMITS["per_source_pool_cap"]

    collectors = [collect_anthropic, collect_github_search, collect_curated_lists, collect_mcp_registry,
                  collect_official_docs, collect_npm, collect_pypi_search]
    statuses, raw = [], []
    for fn in collectors:
        try:
            st, kept = fn(F, A, cap)
        except Exception as e:  # a broken source must not kill the pilot (section 21)
            st = new_status(fn.__name__, 9, fn.__name__, "exception")
            st.update(status="FAIL", reason=f"{type(e).__name__}: {clip(str(e), 200)}")
            kept = []
            errors.append(f"{fn.__name__}: {type(e).__name__}: {e}")
        statuses.append(st)
        raw.extend(kept)
    try:
        st, _ = probe_claude_directory(F)
        statuses.append(st)
    except Exception as e:
        errors.append(f"probe_claude_directory: {e}")

    for i, c in enumerate(raw, 1):
        c["raw_id"] = f"R{i:03d}"

    groups, possible, comparisons = dedupe(raw)
    group_list = []
    for root, idxs in groups.items():
        members = [raw[i] for i in idxs]
        best = max(m["score"] for m in members)
        group_list.append({"root": root, "members": members, "score": best,
                           "sources": uniq([m["source_id"] for m in members]),
                           "possible_of": possible.get(root, [])})

    # selection: TARGET with per-source balance, extend toward MAX only on ties with the TARGET-th score
    group_list.sort(key=lambda g: (bool(g["possible_of"]), -g["score"], -len(g["sources"])))
    chosen = []
    for s in [st["source_id"] for st in statuses]:
        for g in [g for g in group_list if s in g["sources"] and not g["possible_of"]][:LIMITS["per_source_min_pick"]]:
            if g not in chosen and len(chosen) < LIMITS["target_results"]:
                chosen.append(g)
    for g in group_list:
        if len(chosen) >= LIMITS["target_results"]:
            break
        if g not in chosen:
            chosen.append(g)
    if len(chosen) >= LIMITS["target_results"]:
        floor = min(g["score"] for g in chosen)
        for g in group_list:
            if len(chosen) >= LIMITS["max_results"]:
                break
            if g not in chosen and g["score"] >= floor and not g["possible_of"]:
                chosen.append(g)
    chosen.sort(key=lambda g: -g["score"])

    recs = []
    for i, g in enumerate(chosen, 1):
        try:
            reads = read_group(F, g["members"])
            rec = normalize(i, g["members"], reads, A, run_tag)
        except Exception as e:
            errors.append(f"read/normalize {g['members'][0]['name']}: {type(e).__name__}: {e}")
            continue
        rec["_group_root"] = g["root"]
        rec["_possible_of_roots"] = g["possible_of"]
        recs.append(rec)

    # dedup status per record (+ pass 2: repository discovered while reading)
    root_to_id = {r["_group_root"]: r["CAPABILITY_ID"] for r in recs}
    repo_seen = {}
    for r in recs:
        members = groups[r["_group_root"]]
        r["DEDUP_STATUS"] = "UNIQUE"
        r["DEDUP_DETAIL"] = {"merged_raw_candidates": [raw[i]["raw_id"] for i in members],
                             "merged_from_sources": uniq([raw[i]["source_id"] for i in members])}
        if len(members) > 1:
            r["DEDUP_DETAIL"]["note"] = f"{len(members) - 1} duplicate listing(s) merged by shared repository/package key"
        for other_root, why in r["_possible_of_roots"]:
            r["DEDUP_STATUS"] = "POSSIBLE_DUPLICATE"
            r["DEDUP_DETAIL"]["possible_duplicate_of"] = root_to_id.get(other_root, raw[other_root]["name"])
            r["DEDUP_DETAIL"]["reason"] = why
        repo = r["REPOSITORY_URL"].lower() if r["REPOSITORY_URL"] != "UNKNOWN" else None
        if repo and r["TYPE"] != "AGENT_SKILL":
            if repo in repo_seen and r["DEDUP_STATUS"] == "UNIQUE":
                r["DEDUP_STATUS"] = "POSSIBLE_DUPLICATE"
                r["DEDUP_DETAIL"]["possible_duplicate_of"] = repo_seen[repo]
                r["DEDUP_DETAIL"]["reason"] = "pass 2: same repository URL discovered after reading"
            repo_seen.setdefault(repo, r["CAPABILITY_ID"])
        del r["_group_root"], r["_possible_of_roots"]
    root_of = {i: root for root, idxs in groups.items() for i in idxs}
    for i, c in enumerate(raw):
        root = root_of[i]
        if root != i:
            c["dedup"], c["duplicate_of"] = "DUPLICATE", raw[root]["raw_id"]
        elif possible.get(root):
            c["dedup"] = "POSSIBLE_DUPLICATE"
            c["possible_duplicate_of"] = [raw[o]["raw_id"] for o, _ in possible[root]]
        else:
            c["dedup"] = "UNIQUE"

    for r in recs:
        r["DREAM_FIT"] = dream_fit(r, recs, A)

    nqs = generate_next_questions(recs, A)
    for q in nqs:
        src = [r for r in recs if r["CAPABILITY_ID"] in q["SOURCE_CAPABILITIES"]]
        discovered = filter_discovered([t for r in src for t in (r["TOOLS"] if isinstance(r["TOOLS"], list) else [])], A)
        q["AI_KEYWORDS"] = keywords_for(q["QUESTION"], discovered, [r["NAME"] for r in recs])
        q["NEXT_SEARCH_TERMS"] = uniq(q["AI_KEYWORDS"]["CORE_KEYWORDS"][:6] + discovered[:3])
        q["NEXT_INPUT_CANDIDATE"] = True
    outbox = build_outbox(recs, nqs, run_tag)

    finished = now_utc()
    dd = {"raw_candidates": len(raw), "groups_after_pass1": len(groups),
          "merged_away": len(raw) - len(groups),
          "possible_duplicates": sum(r["DEDUP_STATUS"] == "POSSIBLE_DUPLICATE" for r in recs),
          "pairwise_name_comparisons": comparisons,
          "selected_for_read": len(chosen), "capability_records": len(recs),
          "unique_confirmed": sum(r["DEDUP_STATUS"] == "UNIQUE" for r in recs),
          "rules": ["pass 1: shared GitHub repo+path, npm name, PyPI name, MCP-registry name or URL -> DUPLICATE (merged)",
                    "pass 1: same repo root but different sub-project/registry server -> POSSIBLE_DUPLICATE",
                    "pass 1: same normalized name + same provider -> POSSIBLE_DUPLICATE",
                    "pass 2: same repository URL discovered while reading -> POSSIBLE_DUPLICATE"]}
    res = {
        "lot": LOT, "scout_version": VERSION, "authority": "NONE", "run_tag": run_tag,
        "command": shlex.join([os.path.basename(sys.executable)] + sys.argv),
        "started_utc": iso(started), "finished_utc": iso(finished),
        "started_kst": iso(started.astimezone(KST)), "duration_s": round((finished - started).total_seconds(), 1),
        "input": {"question": question, "input_mode": input_mode, "parent": parent},
        "limits": LIMITS,
        "analysis": A,
        "sources": statuses,
        "raw_candidates": [{k: v for k, v in c.items() if not k.startswith("_")} for c in raw],
        "dedup": dd,
        "capabilities": recs,
        "next_questions": nqs,
        "outbox": outbox,
        "errors": errors,
        "fetch_log": F.log,
        "collection_status": "MEASURED" if any(e["ok"] for e in F.log) else "NOT_MEASURED",
    }
    res["self_test"] = self_test(res)
    results = [t["result"] for t in res["self_test"]]
    if res["collection_status"] == "NOT_MEASURED":
        res["final_status"] = "BUILT_NOT_MEASURED"
    elif all(r == "PASS" for r in results):
        res["final_status"] = "PASS"
    elif results.count("PASS") >= 5:
        res["final_status"] = "PARTIAL"
    else:
        res["final_status"] = "FAIL"
    write_outputs(res, out_dir)
    return res


# ---------------------------------------------------------------------------
# 17. OUTPUT FILES + 23. EVIDENCE
# ---------------------------------------------------------------------------

def jdump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def md_escape(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def fmt_val(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v)


def write_outputs(res, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    jdump(os.path.join(out_dir, "results.json"), res)
    jdump(os.path.join(out_dir, "capabilities.json"),
          {"lot": LOT, "run_tag": res["run_tag"], "authority": "NONE", "question": res["input"]["question"],
           "count": len(res["capabilities"]), "capabilities": res["capabilities"]})
    jdump(os.path.join(out_dir, "next_questions.json"),
          {"lot": LOT, "run_tag": res["run_tag"], "authority": "NONE", "from_question": res["input"]["question"],
           "count": len(res["next_questions"]), "next_questions": res["next_questions"], "outbox": res["outbox"]})
    with open(os.path.join(out_dir, "run_report.md"), "w", encoding="utf-8") as f:
        f.write(render_report(res))


def split_failures(log):
    """404s on optional files probed during READ are expected misses, not errors."""
    failed = [e for e in log if not e["ok"]]
    probes = [e for e in failed if e["stage"] == "read" and e["status"] == 404]
    return [e for e in failed if e not in probes], probes


def render_report(res):
    A, q = res["analysis"], res["analysis"]["queries"]
    L = []
    w = L.append
    ok = sum(e["ok"] for e in res["fetch_log"])
    w(f"# Scout run report - {res['run_tag']}\n")
    w(f"LOT: {LOT} | scout v{VERSION} | AUTHORITY: NONE | RESULT: **{res['final_status']}** | "
      f"COLLECTION_STATUS: {res['collection_status']}\n")
    w("## Execution\n")
    w(f"- Command: `{res['command']}`")
    w(f"- Started: {res['started_utc']} (KST {res['started_kst']}), finished {res['finished_utc']}, {res['duration_s']} s")
    w(f"- Input mode: {res['input']['input_mode']}" + (f" (parent: {res['input']['parent']})" if res["input"]["parent"] else ""))
    w(f"- HTTP requests: {len(res['fetch_log'])} (ok {ok}); budget {LIMITS['request_budget']}; GET only, no credentials sent\n")
    w("## Input question\n")
    w(f"> {res['input']['question']}\n")
    w("## Question decomposition\n")
    for fct in FACETS:
        items = A["facets"][fct]
        w(f"- **{fct}**: " + (", ".join(f"{i['label']} (`{i['matched_text']}`)" for i in items) or "-"))
    w(f"- Implied (secondary) concepts: {', '.join(A['implied_ids']) or '-'}")
    w(f"- Free keywords (not in lexicon): {', '.join(A['free_keywords']) or '-'}; unmapped Korean tokens: "
      f"{', '.join(A['unmapped_korean_tokens']) or '-'}\n")
    w("## Generated queries\n")
    for k in ("CORE_QUERY", "GITHUB_QUERY", "SKILL_QUERY", "MCP_QUERY"):
        w(f"- {k}: `{q[k]}`")
    w(f"- NPM_QUERIES: {', '.join('`' + x + '`' for x in q['NPM_QUERIES'])}")
    w(f"- MCP_REGISTRY_TERMS: {', '.join(q['MCP_REGISTRY_TERMS'])}")
    w(f"- TECHNICAL_TERMS: {', '.join(q['TECHNICAL_TERMS'])}\n")
    w("## Sources accessed\n")
    w("| # | Source | Status | Requests | Raw seen | Passed gate | Kept | Reason |")
    w("|---|---|---|---|---|---|---|---|")
    for s in res["sources"]:
        w(f"| {s['priority']} | {md_escape(s['label'])} | **{s['status']}** | {len(s['requests'])} | {s['raw_seen']} | "
          f"{s['gated']} | {s['kept']} | {md_escape(s['reason'])} |")
    d = res["dedup"]
    w("\n## Counts\n")
    w(f"- Raw candidates kept from sources: {d['raw_candidates']}")
    w(f"- After dedup pass 1: {d['groups_after_pass1']} groups ({d['merged_away']} duplicate listings merged)")
    w(f"- Selected and read: {d['selected_for_read']}")
    w(f"- Capability records: {d['capability_records']} (UNIQUE {d['unique_confirmed']}, POSSIBLE_DUPLICATE {d['possible_duplicates']})")
    w(f"- Next questions: {len(res['next_questions'])}")
    w(f"- OUTBOX candidates: {len(res['outbox'])}\n")
    w("## Capabilities\n")
    w("| ID | Name | Type | Evidence | Dedup | Score | Categories | License | Auth | Source |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for r in res["capabilities"]:
        w(f"| {r['CAPABILITY_ID']} | {md_escape(r['NAME'])} | {r['TYPE']} | {r['EVIDENCE_LEVEL'][:2]} | {r['DEDUP_STATUS']} | "
          f"{r['RELEVANCE_SCORE']} | {md_escape('/'.join(r['CATEGORIES'][:5]))} | {md_escape(clip(r['LICENSE'], 30))} | "
          f"{md_escape(clip(r['AUTH_REQUIRED'], 30))} | {r['SOURCE_URL']} |")
    w("\n## Next questions\n")
    for i, nq in enumerate(res["next_questions"], 1):
        w(f"{i}. **{nq['QUESTION']}**")
        w(f"   - WHY: {nq['WHY']}")
        w(f"   - SOURCE_CAPABILITIES: {', '.join(nq['SOURCE_CAPABILITIES'])}")
        w(f"   - NEXT_SEARCH_TERMS: {', '.join(nq['NEXT_SEARCH_TERMS'])}")
    w("\n## OUTBOX candidates\n")
    for o in res["outbox"]:
        w(f"- **{o['OUTBOX_CANDIDATE_ID']}** {o['CAPABILITY']} - {o['WHY_INTERESTING']}. STATUS {o['STATUS']}, AUTHORITY {o['AUTHORITY']}")
    w("\n## Self test\n")
    w("| Test | Check | Result | Detail |")
    w("|---|---|---|---|")
    for t in res["self_test"]:
        w(f"| {t['test']} | {t['name']} | **{t['result']}** | {md_escape(t['detail'])} |")
    w("\n## Errors\n")
    blocking, probes = split_failures(res["fetch_log"])
    if not res["errors"] and not blocking:
        w("- no program errors and no blocking request failures")
    for e in res["errors"]:
        w(f"- {e}")
    for e in blocking:
        w(f"- {e['id']} {e['source_id']} {e['url']} -> {e['status']} {e['error']}"
          + (f" ({md_escape(e.get('error_body', ''))[:160]})" if e.get("error_body") else ""))
    if probes:
        w(f"- {len(probes)} expected misses: optional files probed while reading (SKILL.md / package.json / "
          f"pyproject.toml / LICENSE) returned 404; listed in the fetch log below")
    w("\n## Limitations\n")
    for lim in LIMITATIONS:
        w(f"- {lim}")
    w("\n## Fetch log (evidence)\n")
    w("| ID | Stage | Source | Status | Bytes | sha256[:16] | URL |")
    w("|---|---|---|---|---|---|---|")
    for e in res["fetch_log"]:
        w(f"| {e['id']} | {e['stage']} | {e['source_id']} | {e['status'] or e['error']} | {e['bytes']} | "
          f"{e['sha256_16'] or '-'} | {e['url']} |")
    return "\n".join(L) + "\n"


LIMITATIONS = [
    "Question decomposition and keyword generation use a fixed bilingual lexicon, not an LLM. Words outside it "
    "fall back to raw English keywords; unmapped Korean words are only reported.",
    "Relevance is keyword matching on names/descriptions; it does not prove the tool works. No candidate was installed or run.",
    "GitHub search API, repository metadata (stars, last commit) and code search are not reachable from this "
    "environment; GitHub coverage comes from curated lists + raw files, so LAST_UPDATED is UNKNOWN for GitHub-only records.",
    "The MCP registry search matches server *names* only, so tools whose names lack the search words are missed.",
    "INPUT/OUTPUT/API/AUTH/COST/NETWORK fields are detected from text; UNKNOWN means the text did not say, not 'no'.",
    "Curated lists are community-maintained and may be stale; listing presence is not an endorsement.",
    "Per-source caps and the 15-record ceiling mean the result is a sample, not a census.",
]


# ---------------------------------------------------------------------------
# 26. HANDOFF (built from run results on disk)
# ---------------------------------------------------------------------------

def load_run(d):
    with open(os.path.join(d, "results.json"), encoding="utf-8") as f:
        return json.load(f)


def render_handoff(run_dirs):
    runs = [(d, load_run(d)) for d in run_dirs]
    d0, r0 = runs[0]
    L = []
    w = L.append
    d = r0["dedup"]
    ok0 = sum(e["ok"] for e in r0["fetch_log"])
    accessed = [s for s in r0["sources"] if s.get("ok_requests", 0) > 0]
    loop_ok = len(runs) > 1 and runs[1][1]["final_status"] in ("PASS", "PARTIAL") and \
        runs[1][1]["input"]["input_mode"].startswith("next_question")
    w("# CLAUDE CODE SCOUT - HANDOFF\n")
    w(f"LOT: {LOT} | MODE: BUILD + RUN + EVIDENCE | AUTHORITY: NONE | generated {iso(now_utc())}\n")
    w("## EXECUTIVE SUMMARY\n")
    w(f"- CLAUDE_CODE_SCOUT_STATUS: **{r0['final_status']}** (primary run `{r0['run_tag']}`)")
    w(f"- One Korean question went in. The program built its own search terms, called {len(r0['fetch_log'])} public URLs "
      f"({ok0} ok) across {len(accessed)} reachable sources, kept {d['raw_candidates']} raw candidates, merged duplicates "
      f"into {d['groups_after_pass1']} groups, read {d['selected_for_read']} of them, and wrote {d['capability_records']} capability records.")
    w(f"- It then produced {len(r0['next_questions'])} next research questions with 5 keyword channels each, and "
      f"{len(r0['outbox'])} OUTBOX candidates (STATUS DISCOVERED, AUTHORITY NONE).")
    if len(runs) > 1:
        r1 = runs[1][1]
        w(f"- Loop check: next question #{r1['input']['parent']['pick'] if r1['input']['parent'] else '?'} was fed back as a new input "
          f"(run `{r1['run_tag']}`): {r1['final_status']}, {r1['dedup']['capability_records']} records, "
          f"{len(r1['next_questions'])} new questions. Closed loop {'demonstrated' if loop_ok else 'NOT demonstrated'}.")
    w("- Nothing was installed, executed, purchased, posted, or authenticated. Nothing is VERIFIED; everything is DISCOVERED.\n")
    w("## WHAT WAS BUILT\n")
    try:
        with open(os.path.abspath(__file__), encoding="utf-8") as f:
            nlines = sum(1 for _ in f)
    except OSError:
        nlines = "?"
    w(f"- `scout/scout.py` - one Python 3 file, standard library only ({nlines} lines). Pipeline: "
      "QUESTION -> lexicon decomposition (OBJECT/ACTION/OUTPUT/CONTEXT) -> queries -> 7 source collectors + 1 probe -> "
      "relevance gate -> dedup pass 1 -> balanced selection (target 10, max 15) -> source read -> normalize (22-field schema) "
      "-> dedup pass 2 -> classify -> dream fit -> next questions -> keyword channels -> OUTBOX -> self test -> files.")
    w("- Network door: one `Fetcher` class. GET only, host allowlist, no auth headers, request budget "
      f"{LIMITS['request_budget']}, every request logged with status, bytes and sha256 prefix.")
    w("- `python3 scout.py handoff ...` regenerates this file from the run folders.\n")
    w("## WHAT ACTUALLY RAN\n")
    for dd_, r in runs:
        w(f"- `{r['command']}` at {r['started_utc']} (KST {r['started_kst']}), {r['duration_s']} s, "
          f"{len(r['fetch_log'])} requests -> `{dd_}` -> **{r['final_status']}**")
    w("")
    w("## INPUT\n")
    w(f"> {r0['input']['question']}\n")
    w("## GENERATED SEARCH QUERIES\n")
    A, q = r0["analysis"], r0["analysis"]["queries"]
    for fct in FACETS:
        w(f"- {fct}: " + (", ".join(f"{i['label']} (`{i['matched_text']}`)" for i in A["facets"][fct]) or "-"))
    w(f"- implied: {', '.join(A['implied_ids']) or '-'}")
    for k in ("CORE_QUERY", "GITHUB_QUERY", "SKILL_QUERY", "MCP_QUERY"):
        w(f"- {k}: `{q[k]}`")
    w(f"- NPM_QUERIES: {', '.join('`' + x + '`' for x in q['NPM_QUERIES'])}")
    w(f"- MCP_REGISTRY_TERMS: {', '.join(q['MCP_REGISTRY_TERMS'])}")
    w(f"- TECHNICAL_TERMS: {', '.join(q['TECHNICAL_TERMS'])}\n")
    w("## SOURCES ACCESSED\n")
    w("| Priority | Source | Status | Requests | Kept | Reason |")
    w("|---|---|---|---|---|---|")
    for s in r0["sources"]:
        w(f"| {s['priority']} | {md_escape(s['label'])} | **{s['status']}** | {len(s['requests'])} | {s['kept']} | {md_escape(s['reason'])} |")
    w("")
    w("## CAPABILITIES FOUND\n")
    for r in r0["capabilities"]:
        w(f"### {r['CAPABILITY_ID']} - {r['NAME']}\n")
        for k in REQUIRED_FIELDS[2:]:
            w(f"- {k}: {md_escape(fmt_val(r[k]))}")
        w(f"- CATEGORIES: {', '.join(r['CATEGORIES'])}" + (f" (new: {', '.join(r['NEW_CATEGORIES_CREATED'])})" if r["NEW_CATEGORIES_CREATED"] else ""))
        w(f"- DEDUP: {r['DEDUP_STATUS']} - found in {', '.join(r['FOUND_IN_SOURCES'])}"
          + (f"; {r['DEDUP_DETAIL'].get('note')}" if r["DEDUP_DETAIL"].get("note") else "")
          + (f"; possible duplicate of {r['DEDUP_DETAIL'].get('possible_duplicate_of')} ({r['DEDUP_DETAIL'].get('reason')})"
             if r["DEDUP_STATUS"] == "POSSIBLE_DUPLICATE" else ""))
        f = r["DREAM_FIT"]
        w(f"- DREAM_USE: {f['DREAM_USE']}")
        w(f"- DREAM_FACTORY_TARGET: {f['DREAM_FACTORY_TARGET']}")
        w(f"- POSSIBLE_COMBINATION: {'; '.join(f['POSSIBLE_COMBINATION'])}")
        w(f"- POSSIBLE_VALUE: {', '.join(f['POSSIBLE_VALUE'])} ({f['REVENUE_EVIDENCE']})")
        w(f"- EVIDENCE fetches: {', '.join(r['EVIDENCE']['fetch_ids'])}\n")
    w("## DEDUPLICATION RESULT\n")
    w(f"- raw candidates {d['raw_candidates']} -> {d['groups_after_pass1']} groups after pass 1 ({d['merged_away']} merged as DUPLICATE)")
    w(f"- selected & read {d['selected_for_read']} -> {d['capability_records']} records: UNIQUE {d['unique_confirmed']}, "
      f"POSSIBLE_DUPLICATE {d['possible_duplicates']}; {d['pairwise_name_comparisons']} pairwise name comparisons")
    merged = [r for r in r0["capabilities"] if len(r["DEDUP_DETAIL"]["merged_raw_candidates"]) > 1]
    for r in merged:
        w(f"- merged: {r['NAME']} <- {', '.join(r['DEDUP_DETAIL']['merged_raw_candidates'])} from "
          f"{', '.join(r['DEDUP_DETAIL']['merged_from_sources'])}")
    for rule in d["rules"]:
        w(f"- rule: {rule}")
    dup_raw = [c for c in r0["raw_candidates"] if c.get("dedup") == "DUPLICATE"]
    w(f"- raw-level labels: UNIQUE {sum(c.get('dedup') == 'UNIQUE' for c in r0['raw_candidates'])}, "
      f"DUPLICATE {len(dup_raw)}, POSSIBLE_DUPLICATE {sum(c.get('dedup') == 'POSSIBLE_DUPLICATE' for c in r0['raw_candidates'])}\n")
    w("## NEXT QUESTIONS\n")
    for i, nq in enumerate(r0["next_questions"], 1):
        w(f"{i}. **{nq['QUESTION']}**")
        w(f"   - WHY: {nq['WHY']}")
        w(f"   - SOURCE_CAPABILITIES: {', '.join(nq['SOURCE_CAPABILITIES'])}")
        w(f"   - NEXT_SEARCH_TERMS: {', '.join(nq['NEXT_SEARCH_TERMS'])}")
    w("\n## GENERATED AI KEYWORDS\n")
    for i, nq in enumerate(r0["next_questions"], 1):
        k = nq["AI_KEYWORDS"]
        w(f"**Q{i}** concepts: {', '.join(k['_concepts'])}")
        for ch in ("CORE_KEYWORDS", "GITHUB_KEYWORDS", "MCP_KEYWORDS", "SKILL_KEYWORDS", "WEB_KEYWORDS",
                   "DISCOVERED_TERMS_FROM_SOURCES"):
            w(f"- {ch}: {' | '.join(k[ch]) if k[ch] else '-'}")
        w("")
    w("## OUTBOX CANDIDATES\n")
    for o in r0["outbox"]:
        w(f"### {o['OUTBOX_CANDIDATE_ID']}\n")
        for k in ("SOURCE", "CAPABILITY", "WHY_INTERESTING", "DREAM_USE", "NEXT_RESEARCH_QUESTION", "STATUS", "AUTHORITY"):
            w(f"- {k}: {o[k]}")
        w("")
    w("## SELF TEST\n")
    w("| Test | Check | Result | Detail |")
    w("|---|---|---|---|")
    for t in r0["self_test"]:
        w(f"| {t['test']} | {t['name']} | **{t['result']}** | {md_escape(t['detail'])} |")
    if len(runs) > 1:
        r1 = runs[1][1]
        w(f"| LOOP | generated next question accepted as new input | **{'PASS' if loop_ok else 'FAIL'}** | "
          f"run {r1['run_tag']}: {md_escape(r1['input']['question'])} -> {r1['dedup']['capability_records']} records, "
          f"{len(r1['next_questions'])} questions |")
    w("\n## SUCCESS CRITERIA (section 24)\n")
    st = {t["test"]: t["result"] for t in r0["self_test"]}
    crit = [("natural-language question input", st["TEST 1"]), ("automatic search terms", st["TEST 2"]),
            ("real public-source exploration", "PASS" if r0["collection_status"] == "MEASURED" else "NOT_MEASURED"),
            (">=5 capabilities collected", st["TEST 3"]), ("common schema conversion", st["TEST 5"]),
            ("duplicate handling", st["TEST 6"]), ("new research questions", st["TEST 7"]),
            ("next AI keywords", st["TEST 8"]), ("OUTBOX candidates", st["TEST 9"])]
    for i, (n, v) in enumerate(crit, 1):
        w(f"{i}. {n}: **{v}**")
    w("\n## ERRORS\n")
    for dd_, r in runs:
        blocking, probes = split_failures(r["fetch_log"])
        w(f"- run {r['run_tag']}: {len(r['errors'])} program errors, {len(blocking)} blocking request failures, "
          f"{len(probes)} expected 404 probes for optional files (see run_report.md fetch log)")
        for e in r["errors"]:
            w(f"  - {e}")
        for e in blocking:
            w(f"  - {e['id']} {e['url']} -> {e['status']} {e['error']}")
    w("\n## LIMITATIONS\n")
    for lim in LIMITATIONS:
        w(f"- {lim}")
    w("\n## WHAT WAS NOT MEASURED\n")
    for x in ["Whether any candidate actually extracts data correctly (nothing was installed or executed).",
              "Extraction accuracy, speed, or cost per page of any tool.",
              "Real pricing (only words like 'free' / 'pay per call' were detected).",
              "GitHub stars, last commit date, issues, and code search (API blocked in this environment).",
              "The Claude plugin / connector directory contents (no public machine-readable listing reached).",
              "PyPI keyword search (JavaScript challenge, not bypassed).",
              "Any revenue. POSSIBLE_VALUE is a label, not a result.",
              "Security review of any candidate."]:
        w(f"- {x}")
    w("\n## FILES CREATED\n")
    w("- `scout/scout.py`, `scout/README.md`, `scout/CLAUDE_CODE_SCOUT_HANDOFF.md`")
    for dd_, r in runs:
        w(f"- `{dd_}/results.json`, `{dd_}/capabilities.json`, `{dd_}/next_questions.json`, `{dd_}/run_report.md`")
    w("\n## NEXT RECOMMENDED ACTION\n")
    w("1. A human reads the 3 OUTBOX candidates and decides which (if any) to look at by hand. No install before that.")
    w("2. 20-50 capability expansion pilot: raise `max_results`/`per_source_cap`, add 2-3 more curated lists, and run "
      "the top 3 next questions as a batch loop (depth 1).")
    w("3. If a GitHub token with public read scope is approved later, enable the GitHub search collector (already coded) "
      "to fill stars/last-commit. Until then it stays HOLD.")
    w("4. Do not auto-install, auto-run, promote to SLIM KTX, or dock to FULL KTX (section 25).\n")
    w("## DREAM HANDOFF PACKET\n")
    w("```json")
    packet = {
        "lot": LOT, "authority": "NONE", "status": r0["final_status"], "run_tag": r0["run_tag"],
        "input_question": r0["input"]["question"],
        "sources_actually_accessed": len(accessed),
        "raw_candidates": d["raw_candidates"], "unique_capabilities": d["unique_confirmed"],
        "capability_records": d["capability_records"],
        "next_questions": [x["QUESTION"] for x in r0["next_questions"]],
        "outbox": [{"id": o["OUTBOX_CANDIDATE_ID"], "capability": o["CAPABILITY"], "source": o["SOURCE"],
                    "status": o["STATUS"], "authority": o["AUTHORITY"]} for o in r0["outbox"]],
        "loop_check": ({"run_tag": runs[1][1]["run_tag"], "question": runs[1][1]["input"]["question"],
                        "status": runs[1][1]["final_status"]} if len(runs) > 1 else None),
        "next_step_candidate": "20-50 capability expansion pilot",
        "forbidden_until_human_approval": ["install", "execute", "SLIM KTX promotion", "FULL KTX dock", "payment",
                                           "external posting"],
    }
    w(json.dumps(packet, ensure_ascii=False, indent=2))
    w("```\n")
    w("## FINAL STATUS\n")
    w("```")
    w(f"CLAUDE_CODE_SCOUT_STATUS: {r0['final_status']}")
    w(f"INPUT_QUESTION: {r0['input']['question']}")
    w(f"SOURCES_ACTUALLY_ACCESSED: {len(accessed)}")
    w(f"RAW_CANDIDATES: {d['raw_candidates']}")
    w(f"UNIQUE_CAPABILITIES: {d['unique_confirmed']}")
    w(f"NEXT_QUESTIONS: {len(r0['next_questions'])}")
    w(f"OUTBOX_CANDIDATES: {len(r0['outbox'])}")
    w("AUTHORITY: NONE")
    w("```")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Dream Factories Claude Code Skill Scout (read-only pilot)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run one scout pass for a natural-language question")
    src = r.add_mutually_exclusive_group(required=True)
    src.add_argument("--question", "-q", help="research question (any language the lexicon knows: ko/en)")
    src.add_argument("--stdin", action="store_true", help="read the question from stdin")
    src.add_argument("--from-next", metavar="NEXT_QUESTIONS_JSON", help="use a generated next question as input")
    r.add_argument("--pick", type=int, default=1, help="1-based index into --from-next questions")
    r.add_argument("--out", required=True, help="output directory")
    r.add_argument("--max-results", type=int, default=LIMITS["max_results"])
    h = sub.add_parser("handoff", help="write the handoff file from one or more run folders")
    h.add_argument("--runs", nargs="+", required=True)
    h.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "handoff":
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(render_handoff(a.runs))
        print(f"wrote {a.out}")
        return 0

    LIMITS["max_results"] = max(LIMITS["min_results"], min(a.max_results, 15))
    parent = None
    if a.question:
        question, mode = a.question, "cli --question"
    elif a.stdin:
        question, mode = sys.stdin.read().strip(), "stdin"
    else:
        with open(a.from_next, encoding="utf-8") as f:
            nq = json.load(f)["next_questions"]
        question = nq[a.pick - 1]["QUESTION"]
        mode = f"next_question #{a.pick} from {a.from_next}"
        parent = {"file": a.from_next, "pick": a.pick}
    res = run(question, a.out, mode, parent)
    d = res["dedup"]
    print(json.dumps({
        "CLAUDE_CODE_SCOUT_STATUS": res["final_status"],
        "INPUT_QUESTION": question,
        "SOURCES_ACTUALLY_ACCESSED": sum(s.get("ok_requests", 0) > 0 for s in res["sources"]),
        "SOURCES_YIELDING_CANDIDATES": sum(s["kept"] > 0 for s in res["sources"]),
        "RAW_CANDIDATES": d["raw_candidates"],
        "UNIQUE_CAPABILITIES": d["unique_confirmed"],
        "CAPABILITY_RECORDS": d["capability_records"],
        "NEXT_QUESTIONS": len(res["next_questions"]),
        "OUTBOX_CANDIDATES": len(res["outbox"]),
        "SELF_TEST": {t["test"]: t["result"] for t in res["self_test"]},
        "OUT_DIR": a.out,
        "AUTHORITY": "NONE",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
