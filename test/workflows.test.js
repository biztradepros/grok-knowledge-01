// 워크플로 안의 github-script 코드를 뽑아 모의 GitHub 로 실행해 본다.
// node test/workflows.test.js
const fs = require("fs");
const path = require("path");
const assert = require("assert");

const ROOT = path.join(__dirname, "..");
process.env.GITHUB_WORKSPACE = ROOT;

function scriptOf(file) {
  // fixes/workflows 에 새 버전이 있으면 그것을, 없으면 .github/workflows 를 검사한다
  const staged = path.join(ROOT, "fixes/workflows", file);
  const src = fs.readFileSync(fs.existsSync(staged) ? staged : path.join(ROOT, ".github/workflows", file), "utf8");
  const m = src.match(/script: \|\n([\s\S]*)$/);
  return m[1].split("\n").map((l) => l.replace(/^ {12}/, "")).join("\n");
}

function mockRepo(files) {
  const calls = { comments: [], labelsAdded: [], labelsRemoved: [], writes: [], closed: false };
  const b64 = (s) => Buffer.from(s, "utf8").toString("base64");
  const rest = {
    repos: {
      getContent: async ({ path: p }) => {
        if (p === "rooms") return { data: Object.keys(files).filter((f) => f.startsWith("rooms/")).map((f) => f.split("/")[1]).filter((v, i, a) => a.indexOf(v) === i).map((name) => ({ name, type: "dir" })) };
        if (!(p in files)) { const e = new Error("Not Found"); e.status = 404; throw e; }
        return { data: { sha: "sha-" + p, content: b64(files[p]) } };
      },
      createOrUpdateFileContents: async ({ path: p, content }) => { files[p] = Buffer.from(content, "base64").toString("utf8"); calls.writes.push(p); },
    },
    issues: {
      createComment: async ({ body }) => calls.comments.push(body),
      addLabels: async ({ labels }) => calls.labelsAdded.push(...labels),
      removeLabel: async ({ name }) => calls.labelsRemoved.push(name),
      update: async ({ state }) => { calls.closed = state === "closed"; },
    },
  };
  return { github: { rest }, calls, files };
}

const baseFiles = () => ({
  "rooms/grok-knowledge-01/room.json": "{}",
  "rooms/grok-knowledge-01/insights.json": JSON.stringify({ room: "grok-knowledge-01", papers: [{ id: "vis-2026-01", markdown: "rooms/grok-knowledge-01/virtual-influencer-strategy.md" }] }),
  "index.json": JSON.stringify({ rooms: [{ id: "grok-knowledge-01", papers: 1, index: "rooms/grok-knowledge-01/insights.json" }] }),
  "llms.txt": "# 창고\n\n## Read\n- https://raw.githubusercontent.com/x/y/main/index.json\n\n## Rules\n- r\n",
});
const body = (extra = "") => `<!-- insight-room:v1 -->
command: insight.register
room: grok-knowledge-01
title: 숏폼 전환 팁
slug: shortform-tips
sensitivity: none
source_ai: claude
summary: 첫 2초에 제품을 보여준다.

## body
본문입니다.${extra}

## sources
- chat
<!-- /insight-room -->`;

async function run(file, { github, sender = "biztradepros", labels = [], text = body(), env = {} }) {
  Object.assign(process.env, { APPROVER: "biztradepros", TARGET_REPO: "", PUBLISH_TOKEN: "" }, env);
  const context = { repo: { owner: "biztradepros", repo: "grok-knowledge-01" }, payload: { sender: { login: sender }, issue: { number: 9, body: text, labels: labels.map((name) => ({ name })) } } };
  const core = { warning: (m) => console.log("  warn:", m) };
  const fn = new Function("github", "context", "core", "getOctokit", "require", `return (async () => {\n${scriptOf(file)}\n})();`);
  await fn(github, context, core, () => github, require);
}

(async () => {
  let n = 0; const t = async (name, f) => { await f(); n++; console.log("PASS", name); };

  await t("vet: 정상 카드 → inbox", async () => { const m = mockRepo(baseFiles()); await run("vet-inbox.yml", { github: m.github }); assert.deepEqual(m.calls.labelsAdded, ["inbox"]); });
  await t("vet: 전화번호 → blocked", async () => { const m = mockRepo(baseFiles()); await run("vet-inbox.yml", { github: m.github, text: body(" 010-1111-2222") }); assert.ok(m.calls.labelsAdded.includes("blocked")); });
  await t("vet: 형식 오류 → 댓글만", async () => { const m = mockRepo(baseFiles()); await run("vet-inbox.yml", { github: m.github, text: "그냥 글" }); assert.equal(m.calls.labelsAdded.length, 0); assert.ok(m.calls.comments[0].includes("형식")); });
  await t("publish: 승인자 아님 → 라벨 제거, 파일 안 씀", async () => { const m = mockRepo(baseFiles()); await run("publish-approved.yml", { github: m.github, sender: "some-bot", labels: ["inbox", "approved"] }); assert.ok(m.calls.labelsRemoved.includes("approved")); assert.equal(m.calls.writes.length, 0); });
  await t("publish: 승인자 → 페이퍼·목록·llms 갱신, 이슈 닫힘", async () => {
    const m = mockRepo(baseFiles());
    await run("publish-approved.yml", { github: m.github, labels: ["inbox", "approved"] });
    assert.ok(m.files["rooms/grok-knowledge-01/shortform-tips.md"].includes("status: approved"));
    assert.equal(JSON.parse(m.files["rooms/grok-knowledge-01/insights.json"]).papers.length, 2);
    assert.equal(JSON.parse(m.files["index.json"]).rooms[0].papers, 2);
    assert.ok(m.files["llms.txt"].includes("shortform-tips.md"));
    assert.ok(m.files["llms.txt"].indexOf("shortform-tips.md") < m.files["llms.txt"].indexOf("## Rules"));
    assert.equal(m.calls.closed, true);
  });
  await t("publish: 승인 직전 민감정보 → 게시 안 함", async () => { const m = mockRepo(baseFiles()); await run("publish-approved.yml", { github: m.github, labels: ["approved"], text: body(" a@b.com") }); assert.equal(m.calls.writes.length, 0); });
  await t("publish: blocked 상태면 게시 안 함", async () => { const m = mockRepo(baseFiles()); await run("publish-approved.yml", { github: m.github, labels: ["blocked", "approved"] }); assert.equal(m.calls.writes.length, 0); });
  await t("publish: 같은 slug 재승인은 중복 없이 교체", async () => { const m = mockRepo(baseFiles()); await run("publish-approved.yml", { github: m.github, labels: ["approved"] }); await run("publish-approved.yml", { github: m.github, labels: ["approved"] }); assert.equal(JSON.parse(m.files["rooms/grok-knowledge-01/insights.json"]).papers.length, 2); });
  console.log(`\n${n}개 통과`);
})().catch((e) => { console.error("FAIL", e); process.exit(1); });
