# Claude Code Skill Scout v0.1

LOT `DKSC-CLAUDE-CODE-SCOUT-001` · MODE BUILD + RUN + EVIDENCE · AUTHORITY NONE

This is a small program. You give it one question in plain language. It searches public sources for Skills, MCP servers, and code tools that fit the question, and reads what it finds. It then writes a structured record for each capability and suggests the next questions to research.

It is a pilot that finds 5 to 15 capabilities per run. It is not a full collector.

```
QUESTION -> SEARCH TERMS -> PUBLIC SOURCES -> CANDIDATES -> SOURCE READ -> NORMALIZE
        -> DEDUPLICATE -> CLASSIFY -> DREAM FIT -> NEXT QUESTIONS -> KEYWORDS -> OUTBOX
```

## Run

Python 3.9+ and only the standard library. There is nothing to install.

```bash
cd scout
python3 scout.py run --question "PDF에서 상품 정보를 자동 추출할 수 있는 Skill을 찾아줘." --out runs/my-run
echo "Find an MCP server that parses invoices" | python3 scout.py run --stdin --out runs/my-run-2

# feed a generated next question back in (closed loop)
python3 scout.py run --from-next runs/001/next_questions.json --pick 3 --out runs/002

# rebuild the one-file handoff from run folders
python3 scout.py handoff --runs runs/001 runs/002 --out CLAUDE_CODE_SCOUT_HANDOFF.md
```

No question is hardcoded. A bilingual (Korean/English) lexicon breaks the question into OBJECT, ACTION, OUTPUT and CONTEXT. English words that are not in the lexicon still become search keywords.

## Sources, in priority order

| # | Source | How |
|---|---|---|
| 1 | Anthropic official Skills (`anthropics/skills`) | raw `marketplace.json`, then every `SKILL.md` |
| 2 | GitHub search API | unauthenticated `search/repositories`; recorded HOLD if blocked |
| 3 | Public GitHub curated lists (awesome-claude-skills ×2, awesome-agent-skills, awesome-mcp-servers) | raw README, parsed `- [name](url) - description` |
| 3 | Official MCP Registry | `registry.modelcontextprotocol.io/v0/servers?search=` |
| 4 | Official Claude docs | `llms.txt` indexes |
| 5 | npm registry | `/-/v1/search` |
| 5 | PyPI | search page (HOLD if challenged); JSON API for per-package metadata |
| 5 | Claude plugin directory | probe only; HTML is not scraped |

If a source fails, the run records it and moves on. Each source gets its own PASS / PARTIAL / HOLD / FAIL.

## Output (per run folder)

| File | What |
|---|---|
| `results.json` | everything: analysis, per-source status, raw candidates, dedup, records, questions, outbox, self test, full fetch log |
| `capabilities.json` | the normalized capability records (22 schema fields + categories, dream fit, evidence) |
| `next_questions.json` | next research questions with 5 keyword channels each, plus OUTBOX candidates |
| `run_report.md` | human-readable evidence: command, time, queries, sources, counts, errors, limitations, fetch log |

## Safety rules the code enforces

- It sends HTTP GET only, and only to an allowlist of public hosts. It sends no credentials and no auth headers.
- It never installs or executes anything it finds.
- It writes only to the `--out` folder.
- It has a request budget of 180 per run and a hard ceiling of 15 capability records.
- Every record lists the fetch-log IDs (with HTTP status, byte count and sha256 prefix) that prove it was read.
- A field is `UNKNOWN` when the sources did not state it. The code does not guess.
- Every OUTBOX candidate has STATUS `DISCOVERED` and AUTHORITY `NONE`. Nothing is marked VERIFIED, and revenue is never claimed.
