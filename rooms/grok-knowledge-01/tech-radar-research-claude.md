---
id: radar-2026-claude-01
room: grok-knowledge-01
lot: DF-MULTIAI-TECH-RADAR-RESEARCH-20261015-001
parent: DF-TECH-RADAR-VISUAL-SRT-SLIM-20261015-001
title: Technology Radar & Component Intake Pipeline — Claude independent thesis
status: draft
source_ai: claude
researcher_focus: architecture, security, license, dependency risk, failure isolation, SRT boundary, red team
date_checked: 2026-10-15
sensitivity: none
---

# Technology Radar & Component Intake Pipeline — Claude independent thesis

> **Status: draft.** Not approved. Do not cite as approved until a human adds `approved`.
> Written independently. No Grok or Gemini output was read before writing it.

한국어 요약. 레이더는 새 AI 시스템이 아니다. GitHub 저장소 하나와 예약된 GitHub Actions, 정적 JSON 레지스트리다. 수집, 중복 제거, 라이선스/유지보수/보안 게이트, FAST 점수는 AI 없이 규칙으로 돈다. AI는 주에 10건 이하만 본다. GPT HQ는 이 저장소의 `inbox` 패턴과 같은 형식의 이슈(`radar-control:v1`)로 레이더를 조종한다. 코드 수정은 격리된 랩 저장소의 브랜치와 PR로만 하고, 운영 반영은 사람 1회 승인이다. Visual Command Center 에는 타일 하나와 `/technology-radar` 경로 하나만 붙인다.

English abstract. The Radar should be a batch pipeline, not an agent: one GitHub repo, scheduled GitHub Actions, direct public APIs, a static JSON registry, deterministic gates and a FAST score. AI touches at most ~10 items a week. GPT HQ drives it through typed GitHub Issues (the same pattern this repository already uses for `insight-room:v1`). Code changes happen only on branches in an isolated lab repo, prove themselves with Before/After evidence produced by CI, and reach production through one human merge. The Visual Command Center gets one tile and one lazy route.

## Legend

- **[FACT]** verified on the date checked, with source.
- **[FACT-K]** from prior knowledge, not re-fetched today. Re-verify before relying on it.
- **[REC]** AI recommendation.
- **[ASSUME]** assumption about DREAM's existing system that must be confirmed.

Star counts below were read live from the GitHub Search API through GitHub MCP on 2026-10-15. Licenses marked [FACT] were read from the repository page today; others are [FACT-K].

---

## 1. EXECUTIVE VERDICT

1. **Buildable now, cheaply, with almost no new infrastructure.** Zero-click discovery, filtering, scoring, summarising and candidate proposal are realistic. Install and production promotion should stay at one human approval each. [REC]
2. **The biggest risk is not cost. It is a pipeline that ingests untrusted text (READMEs, issues, package descriptions) into an LLM that also holds write tokens.** That is the "lethal trifecta" that has already been exploited against the GitHub MCP server (May 2025) and against coding agents via PR titles (2026). The architecture below is shaped around never giving one process all three: untrusted input, private data, and a write/exfiltration path. [FACT for the incidents, sources in §20; REC for the design]
3. **MCP is the control and inspection surface, not the ingestion engine.** Scheduled discovery should call public HTTP APIs directly from GitHub Actions. MCP is used by GPT HQ and AI reviewers, read-only, to inspect what the pipeline already collected. [REC]
4. **Nothing discovered is ever installed into the Visual repo directly.** It goes through a lab repo, becomes a DREAM-owned component behind an adapter, and is docked by contract. [REC]
5. **Stars are an adoption signal capped at 10% of the FAST score.** Relevance and maintenance dominate. [REC]
6. **Do not adopt Backstage.** It is excellent (Apache-2.0, 34.6k stars), but it is a developer portal with its own backend and catalog. Adopting it would create the second Command Center that the order forbids. [REC]

## 2. RECOMMENDED ARCHITECTURE

```
                   ┌──────────────────── GPT HQ ────────────────────┐
                   │ writes radar-control:v1 issues / reads results │
                   └───────────────┬────────────────────────────────┘
                                   │ (GitHub connector, MCP read-only, or Common Room job)
                                   ▼
┌──────────────────────── repo: dream-radar (GitHub) ────────────────────────┐
│ .github/workflows/                                                          │
│   collect.yml      cron daily  → sources/*  → raw/ (artifact, not committed)│
│   score.yml        after collect → gates + FAST score → registry/*.json     │
│   review.yml       weekly → AI summary for top N (no write token)           │
│   control.yml      on issues(radar-control:v1) → validate → dispatch job    │
│   deep.yml         manual/approved → DEEP score in lab repo                 │
│ registry/  candidates/ decisions/ evidence/ adapters/ summary.json          │
└───────────────┬─────────────────────────────────────────┬───────────────────┘
                │ static JSON (raw URL / release asset)   │ work-order issue
                ▼                                         ▼
     Visual Command Center (Replit)              repo: dream-component-lab
     - RadarSummaryTile (adapter)                 - coding worker branch radar/<id>
     - /technology-radar (lazy route)             - CI: OSV, license, size, a11y,
                                                    Playwright Before/After
                                                  - PR → GPT review → 1 human merge
                                                  - tag → Visual pins version
```

Mapping to existing DREAM roles [ASSUME roles as described in the order]:

| Existing role | Radar use | New thing built? |
|---|---|---|
| GPT HQ | issues control packets, reads result JSON, writes judgment | no |
| Common Room / ONE-BRAIN | routes a "radar" job to the GitHub issue endpoint; result returns as issue link | adapter only (one job type) |
| GitHub | registry, evidence, CI, branch isolation | one repo + workflows |
| Replit | renders tile + route from static JSON | one tile, one route |
| Notion | human-readable decision log (mirrored from `decisions/`, optional) | no |
| n8n | optional: forward Common Room jobs to `repository_dispatch` | no new engine |
| External AIs | DEEP review, red-team on finalists only | no |

Why a separate `dream-radar` repo instead of a folder in the Visual repo [REC]: the radar's Actions need tokens and network access to the open internet; the Visual repo should never run workflows that fetch arbitrary external content. Failure isolation starts at the repo boundary.

## 3. TECHNOLOGY RADAR PIPELINE

| Stage | Runs where | AI? | Human clicks | Output |
|---|---|---|---|---|
| DISCOVER | `collect.yml`, daily cron | no | 0 | raw records per source |
| INGEST / NORMALISE | same job | no | 0 | one `Candidate` record per canonical identity (purl or `github.com/owner/repo`) |
| DEDUPE | same job | no | 0 | merge by canonical repo URL; packages map to repo via registry metadata |
| HARD GATES | `score.yml` | no | 0 | `REJECT` / `HOLD` / pass, with reason codes |
| FAST SCORE | `score.yml` | no | 0 | 0–100 + per-dimension breakdown |
| AI REVIEW | `review.yml`, weekly, top ≤10 | 1 cheap model call each, read-only | 0 | 150-word summary + DREAM fit + risks |
| GPT JUDGE | GPT HQ reads `summary.json` | GPT | 0 | `PROPOSE` / `WATCH` / `REJECT` decision file via control packet |
| HUMAN GATE | only on trigger list (§11) | — | 0–1 | approval label |
| COMPONENT CANDIDATE | lab repo work order | coding worker | 0 | branch + PR |
| SRT SAFE DOCK | lab CI + adapter contract | no | 0 | evidence bundle |
| VISUAL | merge + version pin | — | 1 | docked component |
| EVIDENCE / REUSE | `evidence/`, `decisions/` | no | 0 | permanent record; rejected items suppressed for 180 days |

Realistic funnel (per week) [REC, estimate]:

```
~1,500–3,000 raw hits (many duplicates across sources)
  → ~400 unique candidates after dedupe
  → ~80 after hard gates (license, archived, stale, known critical vuln)
  → top 10 by FAST score → AI summary
  → 1–3 GPT "PROPOSE" per week
  → ~1–3 DEEP reviews per month
```

10,000/week is achievable but undesirable: the bottleneck is attention, not compute. Tune queries for precision first.

## 4. TOP DISCOVERY SOURCES

| Source | API | MCP | RSS | Webhook | Auth | Cost | Limits | Commercial concern | Metadata quality | Automation fit | Noise |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub Search (repos) | yes, REST + GraphQL | yes (github-mcp-server) | no | no (poll) | token recommended | free | **30 req/min authenticated, 10 unauth; code search 9/min** [FACT, docs.github.com/en/rest/search] | low | high (stars, topics, license, pushed_at) | **best** | medium |
| GitHub Topics | via search `topic:` | yes | no | no | token | free | as search | low | medium (self-tagged) | high | high |
| GitHub Trending | **no official API** [FACT-K] | no | no | no | — | — | scraping only | ToS risk | low | **reject**; emulate with `created:>DATE stars:>N` search | — |
| GitHub Releases | REST | yes | **yes, `/releases.atom`** [FACT-K] | only for repos you own | none for atom | free | atom unmetered by API quota | low | high | **best for watchlist** | low |
| GitHub license / security | REST license endpoint, Dependabot, advisories DB | yes (toolsets `security_advisories`, `dependabot`) | advisories RSS no | yes on own repos | token | free | 5,000/h core [FACT-K] | low | high | high | low |
| MCP Registry | **yes, `registry.modelcontextprotocol.io/v0/servers`** cursor pagination [FACT, fetched] | n/a | no | no | none | free | not documented | low | medium (name, description, remotes, version, status) | high | medium, many low-quality servers |
| npm registry | yes (`registry.npmjs.org/-/v1/search`) | community | no | no (changes feed deprecated [FACT-K]) | none | free | soft | low | medium | high | high |
| PyPI | JSON API, no search API [FACT-K] | community | **yes, per-project RSS** [FACT-K] | no | none | free | soft | low | medium | medium (lookup, not discovery) | medium |
| Hugging Face Hub | yes | **yes, official HF MCP** (connected in this session) | daily papers | yes (own repos) | token optional | free | documented per tier | **model licenses vary widely** | high for models | high for AI model radar | high |
| deps.dev (Google) | **yes, v3, free; licenses as SPDX, advisories, Scorecard, dependents** [FACT, docs.deps.dev] | no | no | no | none [FACT-K] | free | not documented | low | **high** | **best for enrichment** | n/a |
| OSV.dev | yes, free | no | no | no | none | free | — | low | high | enrichment | n/a |
| OpenSSF Scorecard | API + BigQuery dataset | no | no | no | none | free | — | low | high | enrichment | n/a |
| ecosyste.ms | yes | no | no | no | key for 1,000 req/h community tier | **free tier; data CC BY-SA, code AGPL** [FACT, ecosyste.ms/pricing + docs] | 1,000/h | **share-alike data license; commercial terms on request** | high | high | medium |
| Docker Hub | yes | no | no | no | token | free tier | **pull/API limits for anonymous** [FACT-K] | image licenses unclear | low | low | high |
| Product Hunt | GraphQL API | no | yes | no | token | free | low | **ToS restricts commercial use of data** [ASSUME, verify] | low for tech | low | very high |
| Hacker News | Algolia HN API | no | yes | no | none | free | generous | low | low (title + points) | medium as signal only | high |
| Vercel / Cloudflare / Replit changelogs | mostly no | Cloudflare and Vercel publish MCP servers [FACT-K] | **changelog RSS** [FACT-K, per vendor] | no | none | free | — | low | low | **watchlist via RSS** | low |
| Figma Community | limited REST | **Figma MCP (connected here)** | no | yes (own files) | token | free | — | plugin licenses vary | low for code | low | high |
| Mobbin | **no public API** [ASSUME] | no | no | no | paid account | paid | — | **ToS likely forbids scraping** [ASSUME] | n/a | **reference by hand only** | — |
| arXiv / HF daily papers | arXiv API, HF MCP | HF | yes | no | none | free | polite rate | low | medium | medium | high |
| Newsletters (TLDR, Console.dev, etc.) | no | no | some RSS | no | — | free | — | low | low | low | high |

[REC] Phase 1 uses only four sources: **GitHub Search, GitHub Releases atom (watchlist), MCP Registry, npm search**, enriched by **deps.dev + OSV**. Everything else waits until those four produce useful candidates for four weeks.

## 5. TOP MCP OPTIONS

Decision: **E. Hybrid** — direct APIs for scheduled ingestion, existing MCP servers for interactive inspection, **no custom DREAM Radar MCP in phase 1**. GitHub MCP `get_file_contents` on `registry/summary.json` already gives every AI read access to the radar. Build a thin read-only Radar MCP only if three AIs repeatedly need queries that a static file cannot answer. [REC]

| MCP | Source | Capability | Auth | Cost | Maturity | Security risk | DREAM use | Verdict |
|---|---|---|---|---|---|---|---|---|
| GitHub MCP Server | github/github-mcp-server, MIT [FACT], 33.6k★ [FACT]; remote at `api.githubcopilot.com/mcp/` [FACT] | repo search, file read, issues, PRs, releases, security advisories, Dependabot | PAT / OAuth | free | high | **high if write-enabled**: known injection exploit 2025 | GPT HQ and reviewers inspect registry and candidate repos | **RECOMMENDED, with `--read-only` and `--toolsets repos,issues,security_advisories,dependabot`** [FACT: flags exist]. Write path only via the control workflow, never via a reviewer session. |
| MCP Registry (as data) | modelcontextprotocol/registry, 7.4k★ [FACT]; API frozen at v0.1, still "preview" in README [FACT, may be stale] | list MCP servers | none | free | medium | low (read), but listed servers are unvetted | Discovery source for the "MCP" radar quadrant | **RECOMMENDED as HTTP source**, not as an MCP tool |
| Hugging Face MCP | huggingface (official) | model/dataset/space/paper search | token | free | high | low (read) | AI-model quadrant discovery | **HOLD** until DREAM needs a model radar |
| Figma MCP | Figma (official) | design context, screenshots | OAuth | plan-dependent | high | medium | Before/After design reference only | **HOLD** |
| Exa (web search MCP) | Exa | semantic web search | key | **paid per query** | high | medium (untrusted web text) | DEEP review only, finalists | **HOLD**; use only inside DEEP |
| `fetch` reference server | modelcontextprotocol/servers (91k★ [FACT]) | fetch arbitrary URL | none | free | reference quality | **high: SSRF, prompt injection, data exfil via URL** | none | **REJECT** for any session holding secrets |
| n8n MCP | n8n (connected here) | build/run workflows | n8n creds | existing | high | high (can create executors) | Only to forward Common Room jobs to `repository_dispatch` if DREAM already uses n8n | **HOLD** |
| Composio / Zapier / Activepieces aggregators | vendors (connected here) | thousands of SaaS actions | broad OAuth | free–paid | high | **very high: one token reaches everything** | none for radar | **REJECT** for radar |
| Socket.dev MCP / dependency-scoring MCPs | Socket and others [ASSUME exists, verify] | package risk scores | key | free tier [ASSUME] | medium | medium | DEEP dependency review | **HOLD — verify** |
| Custom "DREAM Radar MCP" | would be ours | `radar.search`, `radar.get`, read-only over registry | none | free | — | low if read-only | multi-AI query | **REJECT for phase 1; reconsider in phase 3** |

Rules for every MCP connection [REC]:

1. Read-only by default. Write tools only in a session that reads no untrusted content.
2. One token per purpose, fine-grained, single repo, expiring ≤90 days.
3. Pin the MCP server version; review its tool descriptions on update (tool poisoning / rug pull is a known class [FACT, CSA notes 2025–2026]).
4. Never auto-run project-defined MCP servers from a cloned candidate repo (CurXecute class, CVE-2025-54135 [FACT, per CSA note; verify on NVD]).

## 6. TOP OPEN-SOURCE RADAR OPTIONS

| Project | Stars [FACT 2026-10-15] | Last activity [FACT] | License | Complexity / deploy cost | DREAM verdict |
|---|---|---|---|---|---|
| zalando/tech-radar | 1.9k | updated 2026-10-13 | MIT [FACT-K] | one D3 script + JSON, zero backend | **RECOMMENDED** as the radar-view renderer, wrapped in a DREAM component |
| AOEpeople/aoe_technology_radar | 415 | updated 2026-10-13 | MIT [FACT-K] | static site generator, Markdown items, item history | **PATTERN** — copy its "item history" data model, not the app |
| thoughtworks/build-your-own-radar | 2.6k | updated 2026-10-15 | **AGPL-3.0** [FACT] | Node app, reads sheet/CSV/JSON | **PATTERN ONLY** — AGPL is incompatible with embedding in a closed Visual |
| backstage/backstage (+ tech-radar plugin) | 34.6k | updated 2026-10-15 | Apache-2.0 [FACT-K] | Node backend, Postgres, plugin system, high ops cost | **REJECT for now** — would duplicate Command Center and Project Registry |
| ossf/scorecard | 5.8k | 2026-10-14 | Apache-2.0 [FACT-K] | Action or API | **RECOMMENDED** security signal (read published results via deps.dev; do not run per candidate) |
| google/osv-scanner | 11.2k | 2026-10-15 | Apache-2.0 [FACT-K] | single Go binary | **RECOMMENDED** in lab CI |
| google/deps.dev (API) | 455 (docs repo) | 2026-10-15 | API terms [verify] | none | **RECOMMENDED** enrichment |
| aboutcode-org/scancode-toolkit | 2.6k | 2026-10-14 | Apache-2.0 code, CC-BY-4.0 data [FACT-K] | Python, slow, thorough | **RECOMMENDED for DEEP license scan only** |
| anchore/syft | 9.7k | 2026-10-15 | Apache-2.0 [FACT-K] | single binary | **RECOMMENDED** SBOM for every docked component |
| fossas/fossa-cli | 1.5k | 2026-10-13 | MPL-2.0 [FACT-K] | CLI, hosted backend for full value | **HOLD** |
| renovatebot/renovate | 22.8k | 2026-10-15 | **AGPL-3.0** [FACT-K] | CLI or hosted app | **HOLD** — use GitHub-native Dependabot first; AGPL is fine for running as a tool but avoid vendoring |
| ecosyste.ms | n/a | — | AGPL code, CC BY-SA data [FACT] | API | **HOLD** — great data, but share-alike + commercial terms need legal check |

## 7. TOP FRONTEND / VISUAL OPTIONS

| Need | Candidate | Stars [FACT] | License | Verdict |
|---|---|---|---|---|
| Base components, cards, status board | shadcn/ui | 125.6k | MIT [FACT-K] | **RECOMMENDED** — copy-in source model means no runtime dependency to break; ideal for SRT |
| Charts (cost/risk, score bars, trends) | Recharts (basis of shadcn charts) | 27.6k | MIT [FACT-K] | **RECOMMENDED** |
| Dependency graph, architecture map, JOB tree | xyflow / React Flow | 38.7k | MIT [FACT-K] | **RECOMMENDED** |
| Radar quadrant view | zalando/tech-radar | 1.9k | MIT [FACT-K] | **RECOMMENDED**, wrapped |
| Dashboard blocks | Tremor | 3.7k | Apache-2.0 [FACT-K] | **HOLD** — overlaps shadcn; pick one |
| Heavy charts / large datasets | Apache ECharts | 67.5k | Apache-2.0 [FACT-K] | **HOLD** — large bundle; only if Recharts fails |
| Large graph analysis | Cytoscape.js | 11.2k | MIT [FACT-K] | **HOLD** — only if xyflow struggles above ~1k nodes |
| Component lab / isolation | Storybook | 91.3k | MIT [FACT-K] | **RECOMMENDED in the lab repo only**, not in Visual |
| Before/After screenshots | Playwright | 97.7k | Apache-2.0 [FACT-K] | **RECOMMENDED** |
| Perf / a11y budget | Lighthouse CI | 7.1k | Apache-2.0 [FACT-K] | **RECOMMENDED** |
| Bundle budget | size-limit | 7.0k | MIT [FACT-K] | **RECOMMENDED** |

Integration choice (A–E): **E (adapter-based component packages) with B (selective import) as the mechanism.** [REC]

- A (replace existing components) — reject; breaks a locally verified Visual.
- C (patterns only) — default for anything AGPL/GPL or heavy.
- D (iframe/microfrontend) — only for viewing untrusted third-party demos in the lab, never for docked components (separate runtime, CSP and auth complexity, poor a11y).
- E — each import becomes a DREAM-owned module with a versioned adapter (§14).

## 8. LOW-COST COMPUTE / STORAGE DESIGN

**Compute** [REC]: GitHub Actions only. Public repositories have free standard runner usage in 2026 [FACT, GitHub Dec-2025 changelog]. If `dream-radar` is private, usage counts against plan minutes (2,000/month on Free per a third-party source [unverified]). Expected load: collect + score ≈ 3–5 min/day; weekly review ≈ 5 min; lab CI ≈ 10–20 min per candidate. Comfortably under quota.

**Storage** — first version needs no database [REC]:

```
dream-radar/
  schema/            candidate.schema.json, control.schema.json, evidence.schema.json, adapter.schema.json
  registry/
    candidates/      <id>.json   one file per canonical identity (id = sha1 of canonical URL, first 12)
    decisions/       <id>.json   append-only log: who/what/when/why
    evidence/        <id>/<run>.json + screenshots via Actions artifacts or release assets
    adapters/        <component>.json  docked component manifests
    suppress.json    rejected ids with until-date
    summary.json     ≤50 KB, what the Visual tile and GPT read
  queries/           discovery queries as data (YAML), versioned
  scripts/           collector, scorer (plain Python or Node, no framework)
```

Why not Issues as the store: Issues are good for **commands and conversation**, poor for structured querying and bulk rewrite. Use Issues for control, files for state. [REC]

When to move off GitHub JSON [REC, thresholds are judgments]:

| Trigger | Move to |
|---|---|
| > ~5,000 candidate files, or scoring job spends > 2 min on git I/O | **SQLite** built from JSON inside the Action and published as a release asset (still no server) |
| Concurrent human edits from the Visual UI, or need for auth'd per-user state | **Supabase** (already the named future private layer in `dev-plan-2026`) |
| Full-text search across READMEs | SQLite FTS5 asset first; hosted search only after that fails |

Notion: mirror `decisions/` as a read-only log for humans if desired. Never the source of truth (no stable machine contract for other AIs, as `dev-plan-2026` already decided).

## 9. GPT REMOTE CONTROL DESIGN

Mechanism: **typed GitHub Issues + one validating workflow**, optionally fed by Common Room via `repository_dispatch`. This reuses a pattern DREAM already runs in this repository (`insight-room:v1` + `vet-inbox.yml`). It is not a new router: it accepts one closed set of radar commands and nothing else. [REC]

Control packet (issue body):

```
<!-- radar-control:v1 -->
command: radar.discover
job_id: DF-RADAR-20261015-0007
requested_by: gpt-hq
params:
  query_set: dashboard-components
  max_results: 20
  license_allow: [MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0]
return: issue_comment
<!-- /radar-control -->
```

Closed command set:

| Command | Effect | Writes | Gate |
|---|---|---|---|
| `radar.discover` | run collector for a named query set (no free-form query strings in phase 1) | candidates/ | none |
| `radar.compare` | table of N candidate ids, FAST + DEEP if present | comment only | none |
| `radar.reject` | add to suppress.json with reason | decisions/ | none |
| `radar.watch` | add repo to releases-atom watchlist | queries/ | none |
| `radar.review` | AI summary for ids (read-only model call) | evidence/ | none |
| `radar.prepare_test` | open work-order issue in lab repo | lab issue | **human gate if new dependency** |
| `radar.propose_component` | draft adapter manifest + proposal | adapters/ (draft) | none |
| `radar.regression` | run lab CI against current Visual tag | evidence/ | none |
| `radar.before_after` | produce Before/After bundle | evidence/ | none |

Validation in `control.yml`:

1. Issue author in an allowlist (the GPT HQ bot account / human owners). Others are ignored, not answered.
2. Body parsed with a strict YAML schema; unknown keys or commands → reject comment.
3. Workflow uses `permissions:` minimal per job; third-party actions **pinned by full commit SHA** (tag-repointing compromise of tj-actions/changed-files, CVE-2025-30066 [FACT]).
4. Result returned as a comment containing a link to the committed JSON, plus label `radar-done` or `radar-failed`. Common Room picks up the result by polling the label or via a webhook it already has [ASSUME].

[ASSUME / verify] How GPT HQ writes issues: through a GitHub connector with write scope, a Custom GPT Action calling the REST API, or by asking Common Room to file it. Any of the three works; the packet is the contract.

## 10. REMOTE CODE MODIFICATION DESIGN

```
GPT HQ ── radar.prepare_test ──▶ dream-radar
                                    │ opens work-order issue (template) in
                                    ▼
                           dream-component-lab  (separate repo, no prod secrets)
                                    │ assigned to coding worker
                                    │ (Copilot coding agent / Codex / Claude Code Action /
                                    │  Cursor background agent — any that works from an issue)
                                    ▼
                           branch radar/<candidate-id>
                                    │ PR opened
                                    ▼
                    required checks (all must pass, none skippable):
                      • lockfile diff: new deps listed; any new dep → label needs-human
                      • osv-scanner on lockfile
                      • license allowlist on full tree (SPDX via deps.dev / syft SBOM)
                      • size-limit budget
                      • typecheck + unit tests
                      • Playwright Before/After + axe a11y
                      • Lighthouse CI budget
                      • adapter contract test (§14)
                                    │
                                    ▼
                    GPT HQ review comment (reads diff + evidence JSON, read-only)
                                    │
                                    ▼
                    HUMAN merge (1 click)  → tag component@x.y.z
                                    │
                                    ▼
                    Visual repo: Renovate/Dependabot-style PR bumps the pinned tag
                    (or one-line manifest change) → Visual CI → human merge → Replit deploy
```

Safety properties [REC]:

- **Branch-isolated**: workers can only push `radar/*` branches in the lab repo. Branch protection on `main` requires checks + 1 human review. Workers cannot approve.
- **Golden Core protection**: the Visual repo's core paths are in `CODEOWNERS` with a human owner; the lab repo does not contain them at all. Coding workers never get a token for the Visual repo.
- **Cheap**: one worker run per approved candidate, not per discovery.
- **Traceable**: work-order id = job_id = branch name = evidence folder.
- **Reversible**: Visual pins a component tag; rollback = revert one manifest line.
- **No secrets in lab**: the lab repo's Actions use no production secrets; prompt injection inside a candidate's README therefore has nothing valuable to exfiltrate.

## 11. HUMAN-WORK REDUCTION DESIGN

| Step | Target clicks | Realistic? |
|---|---|---|
| Discovery, metadata, dedupe | 0 | yes |
| License detection | 0 | yes for SPDX-declared; **unknown/NOASSERTION → HOLD, not human** |
| Maintenance / security pre-check | 0 | yes (deps.dev, OSV, Scorecard) |
| Compatibility pre-check | 0 | yes for static facts (language, framework peer deps, bundle size) |
| AI summary | 0 | yes |
| GPT review / component proposal | 0 | yes |
| Install / modify in lab | 0 if no new transitive dependency outside an approved set; else 1 | yes |
| Production promotion | 1 | yes, and should stay 1 |

Always-human triggers (cannot be auto-approved by any AI): license not on allowlist or ambiguous; new dependency with install scripts (`preinstall`/`postinstall`); any change touching auth, secrets, payments, Golden Core paths; paid API or new SaaS account; external publishing; architecture change (new runtime, new datastore, new service).

Batch the human: one weekly "Radar decisions" issue lists all pending gates as checkboxes. Target: **≤5 minutes of human time per week.** [REC]

## 12. FAST SCORE

Runs on every candidate, deterministic, no AI, from metadata already fetched.

**Hard gates first** (fail = not scored):

| Gate | Rule | Outcome |
|---|---|---|
| License | SPDX not in allowlist (MIT, Apache-2.0, BSD-2/3, ISC, MPL-2.0, 0BSD, Unlicense) | REJECT if copyleft-strong (GPL/AGPL/SSPL/BUSL/Elastic/Commons Clause); HOLD if missing/unknown |
| Archived | `archived: true` | REJECT |
| Stale | no push in 365 days and no release in 365 days | HOLD |
| Known vuln | OSV critical/high on latest version, unfixed | HOLD |
| Suppressed | in suppress.json | skip |

**Weighted score (0–100)**:

| Dimension | Weight | Signal | Why this weight |
|---|---|---|---|
| Relevance | 30 | match of topics/description/keywords to a named DREAM need in `queries/*.yaml`; framework match (TS/React/Tailwind) | Noise is the dominant failure; an irrelevant excellent project is worthless |
| Maintenance | 20 | days since push (decay), releases in last 180 days, open/closed issue ratio | Abandoned code becomes DREAM's maintenance burden |
| Security | 15 | OpenSSF Scorecard overall (via deps.dev), 0 if unavailable → scaled 5 | Supply-chain risk enters at adoption time |
| Compatibility | 15 | peer-dependency fit with Visual's stack, ESM, SSR-safe, no native build step | Predicts integration cost cheaply |
| Integration cost (inverse) | 10 | direct dependency count, install scripts present (−), unpacked size | Fewer deps = smaller blast radius |
| Adoption | 10 | `log10(stars+1)` and dependents count, **capped** | Social proof matters but is gameable and biased to old/famous projects |

Notes: score bands `≥70 REVIEW`, `50–69 WATCH`, `<50 ARCHIVE`. Weights live in `queries/weights.yaml` and every decision file records the weights version, so the score can be re-run and audited. After 10 decisions, compare GPT/human outcomes to FAST rank and adjust weights — the only legitimate way to tune them.

## 13. DEEP SCORE

Runs only on candidates GPT marks `PROPOSE` (expected 1–3/month). Every dimension must cite evidence; a dimension without evidence scores 0.

| Dimension | Method | Evidence |
|---|---|---|
| License (full tree) | SBOM (syft) + SPDX per transitive dep; ScanCode on vendored files | sbom.json, license-report.json |
| Dependency risk | transitive count, install scripts, maintainers count, new-maintainer events | deps graph |
| Security | osv-scanner on lockfile; Scorecard detail checks (branch protection, signed releases, token permissions) | osv.json |
| Compatibility | actually build a minimal DREAM adapter in lab | CI log |
| Runtime impact | size-limit delta, Lighthouse delta | budgets.json |
| Visual improvement | Before/After bundle (§15) | screenshots + metrics |
| Replaceability | can the adapter be swapped with a stub in one line? test proves it | contract test |
| Automation value | human minutes or clicks saved, estimated from the scripted task | task script |
| Compute cost | runtime calls to paid APIs, if any | manifest |

Multi-AI: one reviewer by default. Escalate to a second and third AI (Grok/Gemini/Claude) **only** when: DEEP score within ±5 of the adoption threshold, or the first reviewer flags a security/license concern, or the change touches a shared module. Reviewers read the evidence bundle, not the raw internet.

## 14. SRT SAFE DOCK DESIGN

```
external code ─▶ lab: vendored source (copy-in, pinned commit) or pinned npm version
             ─▶ DREAM component  (our props, our styles, our tests)
             ─▶ adapter          (maps Radar/JOB/Evidence contract → component props)
             ─▶ module           (registered in module manifest with version + flag)
             ─▶ SRT SAFE DOCK    (ErrorBoundary + Suspense + feature flag + budget)
             ─▶ existing Visual Command Center
```

Adapter manifest (`registry/adapters/<name>.json`):

```json
{
  "component": "radar-summary-tile",
  "version": "0.1.0",
  "contract": "dream.radar.summary/v1",
  "source": { "type": "vendored", "origin": "github.com/zalando/tech-radar", "commit": "<sha>", "license": "MIT" },
  "mode": "LOCAL|MOCK|LIVE",
  "flag": "radar.tile.enabled",
  "fallback": "StaticSummaryCard",
  "budgets": { "gzip_kb": 30, "lcp_delta_ms": 100 },
  "owner": "human-owner-handle",
  "evidence": "registry/evidence/<id>/"
}
```

Technical rules [REC]:

1. **One-directional data**: dock reads a versioned JSON contract; components never import other docked modules (no full mesh). Communication, if ever needed, goes through the Command Center's existing state/event bus.
2. **Failure isolation**: each docked module is lazy-loaded (`React.lazy`) inside its own ErrorBoundary that renders the `fallback` and reports to Evidence. A crash shows a degraded card, never a blank Command Center.
3. **Contract versioning**: `contract` string with major version; Visual supports N and N−1; schema validated at runtime in MOCK/LOCAL and in CI for LIVE.
4. **Replaceability**: a contract test renders the adapter with the `fallback` swapped in; if the page still passes, the component is replaceable.
5. **Rollback**: flag off (instant) → manifest pin revert (one commit). No database migrations allowed in a docked component.
6. **Dependency firewall**: lab CI fails if the component adds a dependency already present at a different major version in Visual, or any dependency with install scripts.
7. **Existing status contract**: dock maps candidate states to the canonical status contract the Visual already has [ASSUME it includes LOCAL/MOCK/LIVE and pass/fail states]; the radar does not invent new status words.

## 15. BEFORE / AFTER PROOF MODEL

Evidence is produced by CI, not by an AI's opinion. One `before_after.json` per run:

| Measure | How measured | Tool |
|---|---|---|
| Visual readability | side-by-side screenshots at 1440 and 390 px of the same route, same mock data | Playwright |
| Information density | count of labelled data values visible above the fold (DOM query on `data-metric` attrs) | Playwright script |
| Click count | scripted task (e.g. "find top candidate and open evidence") — count actions to completion | Playwright script |
| Load/runtime | LCP, TBT, JS bytes delta | Lighthouse CI |
| Dependency impact | direct + transitive count delta, install-script count | SBOM diff |
| Bundle | gzip KB delta | size-limit |
| Accessibility | axe violations delta (by severity) | @axe-core/playwright |
| Maintenance impact | number of new deps × their maintenance score; files touched outside adapter | script |
| Cost | paid API calls per page view | manifest |
| Rollback difficulty | flag-off test passes? manifest revert only? | CI |

Display: the radar page shows the two screenshots with a slider and a metrics table where every number links to the CI run. A candidate cannot be marked `IMPROVED` unless at least one of readability/density/click-count improves and no budget regresses. "AI says it improved" is not an accepted field.

## 16. VISUAL COMMAND CENTER INTEGRATION

Recommendation: **`/technology-radar`** as its own lazy route, plus one tile on the Command Center. Reject `/partners/radar`: the radar is not a partner concept, and nesting it there couples two unrelated modules. [REC]

Command Center tile (fixed height, one data fetch of `summary.json`):

```
TECHNOLOGY RADAR                      updated 06:00
DISCOVERED 412 · REVIEWING 7 · APPROVED 2 · DOCKED 1 · HOLD 9
TOP CANDIDATE  xyflow/xyflow  FAST 84  → dependency map
NEXT ACTION    1 human gate pending (license: MPL-2.0)
[ OPEN RADAR ]
```

`/technology-radar` sections: Quadrant view (zalando radar renderer) · Candidate cards with FAST/DEEP breakdown · Decisions log · Before/After viewer · Docked components with version + rollback flag.

Load budget: tile ≤ 5 KB JS beyond shared shadcn primitives; route chunk loaded only on navigation. If `summary.json` fetch fails, tile shows "Radar offline — last good: <date>" from cache; it never blocks the Command Center.

## 17. TOP 10 TECHNOLOGIES TO TEST

| # | Technology | Why | Test |
|---|---|---|---|
| 1 | GitHub Search REST API | primary discovery | query sets return ≥30% relevant hits by human spot-check |
| 2 | MCP Registry API `/v0/servers` | MCP quadrant | full pagination nightly in < 2 min |
| 3 | deps.dev API v3 | license + Scorecard + advisories enrichment | ≥90% of GitHub candidates resolve to SPDX license |
| 4 | OSV-Scanner | lab vuln gate | blocks a known-vulnerable fixture |
| 5 | GitHub MCP Server (read-only toolsets) | GPT/AI inspection | GPT reads summary.json and a candidate README without write tools present |
| 6 | Syft (SBOM) | full-tree license | SBOM for a shadcn-based component in < 1 min |
| 7 | Playwright + axe | Before/After + a11y | identical screenshots on repeated runs (flake < 2%) |
| 8 | Lighthouse CI + size-limit | budgets | fail PR on +30 KB gzip |
| 9 | zalando/tech-radar renderer | quadrant view | wrapped as DREAM component under 30 KB gzip |
| 10 | xyflow / React Flow | dependency + architecture map | renders 300 nodes interactively on a mid laptop |

## 18. FIRST 3 COMPONENTS TO BUILD

1. **Radar Collector + Scorer** (`dream-radar` workflows + scripts). GitHub Search + MCP Registry + deps.dev; gates; FAST score; writes `registry/` and `summary.json`. No AI.
2. **Radar Control Workflow** (`control.yml` + `radar-control:v1` schema). Supports `discover`, `compare`, `reject` only at first. This is what gives GPT HQ remote control.
3. **RadarSummaryTile** (Visual, via adapter + SRT dock). Reads `summary.json`; MOCK mode with a fixture; ErrorBoundary fallback.

Deliberately second wave: `/technology-radar` route, Before/After runner, lab repo work-order flow.

## 19. FIRST SLIM GOLDEN

**SLIM GOLDEN = "GPT asks, radar answers, Visual shows" with zero AI inside the radar.**

Scope:

- One query set: `dashboard-components` (React/TS dashboard/chart/graph libraries).
- One discovery source (GitHub Search) + one enrichment (deps.dev license/Scorecard).
- Hard gates + FAST score.
- `radar.discover` and `radar.reject` via issue.
- `summary.json` rendered by RadarSummaryTile in MOCK and LOCAL modes.

PASS criteria (all must be shown with evidence, not documentation):

1. GPT HQ files a `radar.discover` issue → `radar-done` label and result comment within 10 minutes, with no human click.
2. ≥ 20 candidates written; every one has license, last push, FAST breakdown, reason codes.
3. A seeded AGPL fixture is rejected by the gate; a seeded archived repo is rejected.
4. `radar.reject <id>` suppresses the id on the next run.
5. Tile renders the counts and top candidate from `summary.json`; with `summary.json` deleted, tile shows the offline fallback and the Command Center still passes its existing local verification.
6. Workflow file: all actions SHA-pinned, `permissions` minimal, no secret other than a fine-grained read token (plus `issues: write` on the radar repo).

Not LIVE until it has run on schedule for 7 consecutive days without manual fixes.

## 20. RISKS / RED TEAM

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Overbuilt AI system** — radar grows its own agent, router, DB, UI | high | Phase gates in §22; AI calls capped per week in workflow config; "what not to build" list §23 is a review checklist |
| **Star bias** — famous ≠ fit; stars bought/botted | high | adoption capped at 10%; relevance first; dependents count over stars; manual spot-check of FAST top-10 monthly |
| **Supply-chain attack via discovered package** | medium-high (npm worms: Shai-Hulud Sept + Nov 2025, hundreds of packages, preinstall execution [FACT]) | never install in Visual directly; lab CI installs with `--ignore-scripts`; install-script presence → human gate; lockfile + OSV; prefer copy-in source |
| **Supply-chain attack via GitHub Actions** | medium (tj-actions/changed-files, CVE-2025-30066 [FACT]) | SHA-pin all actions; Dependabot for actions; `permissions: {}` default; no `pull_request_target` with checkout of PR code |
| **Prompt injection from READMEs/issues into AI reviewers** | high (GitHub MCP exploit May 2025; PR-title injection of coding agents 2026 [FACT, secondary sources]) | reviewer sessions have **no write tokens**; outputs are schema-validated JSON; any instruction-like text from candidates is treated as data; write path is only the control workflow parsing a strict schema |
| **MCP servers exposing secrets / tool poisoning** | medium | read-only toolsets; per-purpose tokens; pinned server versions; never auto-start MCP servers from candidate repos; reject aggregator MCPs for radar |
| **License commercial risk** | medium | SPDX allowlist gate; full-tree SBOM in DEEP; AGPL/GPL pattern-only; data licenses (CC BY-SA) treated like code licenses; human gate on any ambiguity |
| **AI auto-approves unsafe code** | medium | AIs can comment, never approve or merge; branch protection requires human review; CODEOWNERS on core |
| **Noise flood** | high | precision-first named query sets, suppress list, weekly cap of 10 reviews, digest not notifications |
| **Visual bloat** | medium | one tile + one lazy route; size budgets fail CI; docked components must beat Before/After |
| **Autonomous modification damages Golden Core** | low with this design | workers only in lab repo; Visual changes are one-line pin bumps through Visual's own CI; flag-off rollback |
| **Radar becomes stale / silently broken** | medium | workflow failure opens one issue; tile shows last-good date; 7-day LIVE rule |
| **Rate-limit / ToS violation** | low-medium | official APIs only, no scraping of Trending, Mobbin or Product Hunt pages; backoff on 403/429 |
| **Duplicate of existing DREAM systems** | medium | radar writes into existing Evidence/Result paths via adapter rather than creating its own inbox [ASSUME paths exist] |

## 21. COST ESTIMATE

Estimates, not quotes. [REC]

| Item | Monthly |
|---|---|
| GitHub Actions, public `dream-radar` | $0 [FACT: public repo standard runners free] |
| GitHub Actions, if private | likely within included minutes (~150–400 min/month expected) |
| APIs (GitHub, MCP Registry, deps.dev, OSV, npm) | $0 |
| AI summaries: ~40/month × ~8k tokens on a small model | ≈ $1–3 |
| DEEP reviews: 1–3/month × multi-AI on finalists | ≈ $3–15 |
| Coding worker runs: 1–3/month | within existing Copilot/Codex/Claude subscriptions [ASSUME] |
| Storage | $0 (git + Actions artifacts) |
| **Total incremental** | **≈ $5–20/month** |
| Human time | target ≤ 5 min/week after setup |

## 22. IMPLEMENTATION ORDER

| Phase | Deliverable | Exit criterion |
|---|---|---|
| 0 | `schema/*.json`, query set YAML, allowlist, weights file | schemas reviewed by GPT HQ + human |
| 1 | Collector + Scorer + `summary.json` (Slim Golden part 1) | 7 days green on schedule |
| 2 | Control workflow with discover/compare/reject | Slim Golden PASS 1–4 |
| 3 | RadarSummaryTile docked (MOCK → LOCAL) | Slim Golden PASS 5; Visual local verification still passes |
| 4 | Weekly AI review (read-only) for top 10 | 4 weeks; GPT agrees with ≥50% of top-5 as worth review |
| 5 | Lab repo + work-order flow + Before/After runner | one candidate taken to PR with full evidence |
| 6 | `/technology-radar` route + quadrant view | first DOCKED component visible with rollback flag |
| 7 | Add sources (Releases atom watchlist, npm, HF) | only if phase 4 shows unmet demand |
| 8 | Optional: read-only Radar MCP, SQLite asset | only on threshold triggers in §8 |

## 23. WHAT NOT TO BUILD

- A second Command Center, Result Inbox, Evidence Store, AI router, or ONE-BRAIN.
- Backstage or any developer portal.
- A hosted database in phases 0–6.
- A long-running autonomous agent that browses the web.
- Web scrapers for GitHub Trending, Mobbin, Product Hunt.
- An auto-merge path for any AI.
- A custom MCP server before phase 8.
- Free-form natural-language commands executed directly by a workflow (only the closed command set).
- Real-time notifications per discovery (weekly digest only).
- Embedding of AGPL/GPL code in the Visual.

## 24. UNKNOWN / NEEDS VERIFICATION

1. How GPT HQ writes to GitHub today (connector write scope, Custom GPT Action, or via Common Room). [ASSUME]
2. Whether Common Room can emit `repository_dispatch` or create issues, and how it ingests results. [ASSUME]
3. Visual's exact stack (React version, Tailwind, shadcn already present?) and its canonical status contract field names. [ASSUME]
4. How Replit deploys from GitHub (pull on tag, or manual). [ASSUME]
5. Licenses marked [FACT-K] above — re-check from each repository's LICENSE file before adoption.
6. MCP Registry production status: README read today still says preview with API frozen at v0.1; may be outdated.
7. GitHub Actions included minutes for private repos on DREAM's plan; self-hosted runner platform charge applicability.
8. deps.dev authentication and rate limits (docs do not state limits; the sandbox for this research could not reach the API directly).
9. ecosyste.ms commercial data licence terms.
10. Product Hunt API commercial-use terms; Mobbin API/ToS.
11. Existence and terms of a Socket.dev (or similar) MCP server.
12. The 2026 coding-agent PR-title injection report and CVE IDs — from secondary sources; confirm against primary advisories.

## 25. FINAL RECOMMENDATION

**Answer to the final question:**

> The simplest architecture that can be built and operated now is **one GitHub repository (`dream-radar`) running scheduled GitHub Actions that call public APIs (GitHub Search, MCP Registry, deps.dev, OSV), apply deterministic license/maintenance/security gates and a transparent FAST score, and commit the results as static JSON.** GPT HQ controls it by filing typed `radar-control:v1` issues (the same issue-packet pattern this repository already uses), and reads results as JSON. AI is called only for the weekly top 10, read-only. Approved candidates become work orders in a **separate, secret-free lab repo**, where a coding worker opens a branch and PR, and CI produces license, vulnerability, budget and Before/After evidence. One human merge tags the component; the Visual Command Center pins that tag behind an adapter, an ErrorBoundary and a feature flag, and shows the radar as one tile plus a lazy `/technology-radar` route.

What makes it safe is not the AI. It is three boundaries: **untrusted text never meets a write token; nothing external enters Visual except through an adapter at a pinned version; only a human merges.** What makes it cheap is that every step before the top 10 is plain code.

## Sources (checked 2026-10-15)

- GitHub repository metadata (stars, updated dates): GitHub Search API via GitHub MCP, queried 2026-10-15.
- GitHub REST search rate limits: https://docs.github.com/en/rest/search/search
- MCP Registry live API response: https://registry.modelcontextprotocol.io/v0/servers?limit=3 ; repo status: https://github.com/modelcontextprotocol/registry
- GitHub MCP Server license, `--read-only`, toolsets, remote URL: https://github.com/github/github-mcp-server
- build-your-own-radar AGPL-3.0: https://github.com/thoughtworks/build-your-own-radar
- deps.dev API v3: https://docs.deps.dev/api/v3/index.html , https://blog.deps.dev/api-v3/ , https://security.googleblog.com/2023/04/announcing-depsdev-api-critical.html
- ecosyste.ms pricing, limits, licences: https://ecosyste.ms/pricing , https://docs.ecosyste.ms/docs/usage/ , https://blog.ecosyste.ms/2025/09/01/rate-limiting-the-right-way.html
- GitHub Actions 2026 pricing: https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/ , https://resources.github.com/actions/2026-pricing-changes-for-github-actions/
- tj-actions/changed-files CVE-2025-30066: https://www.wiz.io/fr-fr/blog/github-action-tj-actions-changed-files-supply-chain-attack-cve-2025-30066 , https://www.theregister.com/2025/03/17/supply_chain_attack_github/
- Shai-Hulud npm worm (2025): https://www.infoworld.com/article/4095604/new-shai-hulud-worm-spreading-through-npm-github-2.html , https://flashpoint.io/blog/shai-hulud-worm-targeting-npm-supply-chains/
- GitHub MCP prompt-injection exploit: https://feeds.simonwillison.net/2025/May/26/github-mcp-exploited
- MCP tool poisoning / IDE auto-execution: https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-tool-poisoning-ai-agent-exfiltration-2/ , https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-tool-poisoning-auto-execution-20260701/
