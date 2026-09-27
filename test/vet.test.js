// node test/vet.test.js  — 외부 라이브러리 없이 실행
const assert = require("assert");
const path = require("path");
const { loadRules, vetText, parseCard, toMarkdown } = require("../tools/vet.js");

const rules = loadRules(path.join(__dirname, ".."));
const rooms = ["grok-knowledge-01", "claude-knowledge-01"];
const card = (extra = "", body = "공개해도 되는 본문.") => `insight: 제목
<!-- insight-room:v1 -->
command: insight.register
room: grok-knowledge-01
title: 숏폼 전환 팁
slug: shortform-tips
sensitivity: none
source_ai: claude
summary: 첫 2초에 제품을 보여준다.
${extra}
## body
${body}

## sources
- chat
<!-- /insight-room -->`;

let n = 0;
const t = (name, fn) => { fn(); n++; console.log("PASS", name); };

t("정상 카드 통과", () => assert.equal(vetText(card(), rules, { existingRooms: rooms }).ok, true));
t("필드 파싱", () => { const c = parseCard(card()); assert.equal(c.fields.slug, "shortform-tips"); assert.equal(c.body, "공개해도 되는 본문."); assert.equal(c.sources, "- chat"); });
t("블록 없음 → 실패", () => assert.equal(vetText("그냥 글", rules).ok, false));
t("전화번호 차단", () => assert.ok(vetText(card("", "연락 010-1234-5678"), rules).sensitive.some((s) => s.includes("phone_kr"))));
t("이메일 차단", () => assert.ok(vetText(card("", "a@b.com 로 연락"), rules).sensitive.some((s) => s.includes("email"))));
t("거래처 연락처 금지어", () => assert.ok(vetText(card("", "거래처 연락처는 따로"), rules).sensitive.length > 0));
t("단가 금액 차단", () => assert.ok(vetText(card("", "공급가: 3,500원"), rules).sensitive.some((s) => s.includes("price_krw"))));
t("토큰 차단", () => assert.ok(vetText(card("", "ghp_abcdefghijklmnopqrstuvwxyz123"), rules).sensitive.length > 0));
t("없는 방 거부", () => assert.ok(vetText(card().replace("room: grok-knowledge-01", "room: nope"), rules, { existingRooms: rooms }).errors.some((e) => e.includes("nope"))));
t("잘못된 slug 거부", () => assert.ok(vetText(card().replace("shortform-tips", "숏폼"), rules).errors.length > 0));
t("sensitivity 다르면 거부", () => assert.ok(vetText(card().replace("sensitivity: none", "sensitivity: high"), rules).errors.length > 0));
t("마크다운 변환", () => { const md = toMarkdown(parseCard(card()), { issueNumber: 7, approvedAt: "2026-09-25", approver: "biztradepros" }); assert.ok(md.includes("status: approved")); assert.ok(md.includes("issue: 7")); assert.ok(md.includes("# 숏폼 전환 팁")); });
console.log(`\n${n}개 통과`);
