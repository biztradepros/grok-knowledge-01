// 인사이트 카드 검사 공통 모듈.
// vet-inbox.yml(접수 검사)과 publish-approved.yml(승인 게시)이 같은 규칙을 쓴다.
// 로컬 테스트: node test/vet.test.js
//
// 카드 형식 (CHAT.md):
// <!-- insight-room:v1 -->
// command: insight.register
// room: grok-knowledge-01
// title: 한 줄 제목
// slug: english-slug            (선택. 없으면 insight-<이슈번호>)
// sensitivity: none
// source_ai: claude
// summary: 한 줄 요약
//
// ## body
// 본문
//
// ## sources
// - chat
// <!-- /insight-room -->

const fs = require("fs");
const path = require("path");

const START = "<!-- insight-room:v1 -->";
const END = "<!-- /insight-room -->";

function loadRules(root = process.cwd()) {
  const p = path.join(root, ".github", "insight-rules.json");
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function parseCard(text = "") {
  const s = text.indexOf(START);
  const e = text.indexOf(END);
  if (s < 0 || e < 0 || e < s) return null;
  const inner = text.slice(s + START.length, e).replace(/\r\n/g, "\n");
  const bodyAt = inner.search(/^##\s+body\s*$/m);
  const head = bodyAt >= 0 ? inner.slice(0, bodyAt) : inner;
  const fields = {};
  for (const line of head.split("\n")) {
    const m = line.match(/^([a-z_]+):\s*(.*)$/);
    if (m) fields[m[1]] = m[2].trim();
  }
  let body = "";
  let sources = "";
  if (bodyAt >= 0) {
    const rest = inner.slice(bodyAt).replace(/^##\s+body\s*\n/, "");
    const srcAt = rest.search(/^##\s+sources\s*$/m);
    body = (srcAt >= 0 ? rest.slice(0, srcAt) : rest).trim();
    sources = srcAt >= 0 ? rest.slice(srcAt).replace(/^##\s+sources\s*\n/, "").trim() : "";
  }
  return { fields, body, sources };
}

function findSensitive(text, rules) {
  const hits = [];
  const lower = text.toLowerCase();
  for (const k of rules.keywords || []) if (lower.includes(k.toLowerCase())) hits.push(`금지어 "${k}"`);
  for (const [name, src] of Object.entries(rules.patterns || {})) {
    const m = new RegExp(src, "i").exec(text);
    if (m) hits.push(`패턴 ${name} ("${m[0].slice(0, 4)}…")`);
  }
  return hits;
}

// 결과: { ok, card, errors[], sensitive[] }
function vetText(text, rules, { existingRooms } = {}) {
  const errors = [];
  const card = parseCard(text);
  if (!card) return { ok: false, card: null, errors: ["insight-room:v1 블록이 없습니다"], sensitive: [] };
  const f = card.fields;
  for (const k of rules.required_fields) if (!f[k]) errors.push(`필수 항목 ${k} 가 비었습니다`);
  if (f.command && f.command !== rules.command) errors.push(`command 는 ${rules.command} 여야 합니다`);
  if (f.sensitivity && f.sensitivity !== rules.sensitivity) errors.push(`sensitivity 는 ${rules.sensitivity} 여야 합니다`);
  if (f.slug && !new RegExp(rules.slug_pattern).test(f.slug)) errors.push("slug 는 영문 소문자-하이픈만 됩니다");
  if (existingRooms && f.room && !existingRooms.includes(f.room)) errors.push(`방 ${f.room} 이 없습니다 (있는 방: ${existingRooms.join(", ")})`);
  if (!card.body) errors.push("## body 가 비었습니다");
  const sensitive = findSensitive(text, rules);
  return { ok: errors.length === 0 && sensitive.length === 0, card, errors, sensitive };
}

function toMarkdown(card, { issueNumber, approvedAt, approver }) {
  const f = card.fields;
  const esc = (s) => JSON.stringify(String(s || ""));
  return `---
title: ${esc(f.title)}
room: ${f.room}
status: approved
source_ai: ${f.source_ai}
summary: ${esc(f.summary)}
approved_at: ${approvedAt}
approved_by: ${approver}
issue: ${issueNumber}
---

# ${f.title}

${card.body}

## 출처

${card.sources || "- chat"}
`;
}

module.exports = { START, END, loadRules, parseCard, findSensitive, vetText, toMarkdown };
