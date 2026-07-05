#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// engage-scout.mjs — the PROACTIVE half of /viral-loop's PUBLISH+ENGAGE stage.
//
// Goes OUT and finds public conversations where your content's topics are being
// discussed, screens them for genuine relevance IN CODE, and writes a review
// QUEUE — one entry per thread, with the direct URL and an empty draftReply slot.
// The agent then drafts each reply in your voice (grounded in the article); YOU
// review, edit, and post from your own account. Deterministic core: no LLM, no
// keys, no auth. Node 18+ (global fetch), zero dependencies.
//
// ░░ THE HARD LINE (do not remove) ░░
// This tool DISCOVERS and DRAFTS. It NEVER posts, replies, DMs, follows, or likes
// — not via API, not via browser automation. Auto-engagement violates LinkedIn/X
// ToS (LinkedIn won a $13M automation case), gets accounts banned, and torches the
// "own your data / a real human answered" brand. A human always owns Send. The
// bot's job is to save you the *finding*, never to fake the *relationship*.
//
// Usage:
//   node engage-scout.mjs --keywords "llm inference, kv cache, disaggregation"
//   node engage-scout.mjs --from marketing/ship-a-loop-linkedin.md
//   node engage-scout.mjs --keywords "…" --platform hn,reddit --min-score 0.18 \
//       --out marketing/engagement-queue.md
//
// Flags:
//   --keywords "a, b, c"   comma-separated topics to hunt (OR --from a content file)
//   --from <file>          extract top keywords from a content file (freq, minus stopwords)
//   --platform hn[,reddit] which surfaces to search (default hn). reddit is best-effort.
//   --min-score <0..1>     relevance floor to enter the queue (default 0.15)
//   --limit <n>            max hits per platform per keyword (default 5)
//   --out <file>           write the queue markdown here (default: stdout only)
//   --json                 also print the raw queue as JSON (for the ledger / a cron)
// ─────────────────────────────────────────────────────────────────────────────

import fs from "node:fs";

const HELP = `engage-scout — proactive engagement discovery for /viral-loop (drafts, never sends).
  --keywords "a, b, c"  topics to hunt   |   --from <file>  extract keywords from content
  --platform hn,reddit  surfaces (default hn)   --min-score 0..1 (default 0.15)
  --limit <n> (5)   --out <file>   --json
Searches PUBLIC, server-readable surfaces only. LinkedIn/X are login-walled — a bot
cannot (and must not) read or post there; you watch those and paste threads in for a draft.`;

const STOP = new Set(("the a an and or of to in on for with is are be this that your you our we it as at by from into than then so if not no yes can will just how what why when who which their they them its it's about over under across via using use used more most less least new here there".split(" ")));

const args = parseArgs(process.argv.slice(2));
if (args.help || (!args.keywords && !args.from)) {
  console.log(HELP);
  process.exit(args.help ? 0 : 1);
}

function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--json") o.json = true;
    else if (a === "--help" || a === "-h") o.help = true;
    else if (a.startsWith("--")) { o[a.slice(2)] = argv[i + 1]; i++; }
  }
  return o;
}

function tokenize(s) {
  return (s || "").toLowerCase().replace(/<[^>]+>/g, " ").replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/).filter((w) => w.length > 2 && !STOP.has(w));
}

function keywordsFromFile(path) {
  
  const text = fs.readFileSync(path, "utf8");
  const freq = new Map();
  for (const w of tokenize(text)) freq.set(w, (freq.get(w) || 0) + 1);
  return [...freq.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([w]) => w);
}

// Relevance IN CODE (never vibes): fraction of the query's terms present in the hit.
function relevance(queryTerms, hitText) {
  const hit = new Set(tokenize(hitText));
  if (!queryTerms.length) return 0;
  const overlap = queryTerms.filter((t) => hit.has(t)).length;
  return overlap / queryTerms.length;
}

async function getJson(url) {
  try {
    const r = await fetch(url, { headers: { "User-Agent": "viral-loop-engage-scout (drafts-never-sends)" } });
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

// HN via Algolia — comments are where readers actually discuss; stories catch the topic hubs.
async function searchHN(query, limit) {
  const out = [];
  for (const tags of ["comment", "story"]) {
    const j = await getJson(`https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}&tags=${tags}&hitsPerPage=${limit}`);
    for (const h of j?.hits || []) {
      const text = (h.comment_text || h.title || h.story_title || "").replace(/<[^>]+>/g, " ").trim();
      out.push({
        platform: "hackernews",
        author: h.author || "?",
        title: (h.story_title || h.title || "(comment)").slice(0, 140),
        excerpt: text.slice(0, 280),
        url: `https://news.ycombinator.com/item?id=${h.objectID}`,
        id: `hn:${h.objectID}`,
      });
    }
  }
  return out;
}

// Reddit public JSON — usually 403s from datacenter IPs; best-effort, degrades to [].
async function searchReddit(query, limit) {
  const j = await getJson(`https://www.reddit.com/search.json?q=${encodeURIComponent(query)}&sort=new&limit=${limit}`);
  const out = [];
  for (const c of j?.data?.children || []) {
    const d = c.data || {};
    out.push({
      platform: "reddit",
      author: d.author || "?",
      title: (d.title || "").slice(0, 140),
      excerpt: (d.selftext || d.title || "").slice(0, 280),
      url: `https://www.reddit.com${d.permalink || ""}`,
      id: `rd:${d.id}`,
    });
  }
  return out;
}

async function main() {
  const keywords = args.from
    ? keywordsFromFile(args.from)
    : String(args.keywords).split(",").map((s) => s.trim()).filter(Boolean);
  const queryTerms = [...new Set(keywords.flatMap(tokenize))];
  const platforms = String(args.platform || "hn").split(",").map((s) => s.trim());
  const limit = Number(args.limit) || 5;
  const minScore = args["min-score"] != null ? Number(args["min-score"]) : 0.15;

  const searched = [];
  const raw = [];
  for (const kw of keywords) {
    if (platforms.includes("hn")) { searched.push(`hackernews("${kw}")`); raw.push(...await searchHN(kw, limit)); }
    if (platforms.includes("reddit")) { searched.push(`reddit("${kw}")`); raw.push(...await searchReddit(kw, limit)); }
  }

  // Dedup by id, score by code, keep only genuinely-relevant, rank best-first.
  const seen = new Set();
  const queue = [];
  for (const h of raw) {
    if (seen.has(h.id) || !h.url || !h.excerpt) continue;
    seen.add(h.id);
    const score = Number(relevance(queryTerms, `${h.title} ${h.excerpt}`).toFixed(3));
    if (score >= minScore) queue.push({ ...h, score });
  }
  queue.sort((a, b) => b.score - a.score);

  const redditTried = platforms.includes("reddit");
  const redditHits = queue.filter((q) => q.platform === "reddit").length;
  const report = {
    generatedForKeywords: keywords,
    queryTerms,
    searched,
    found: queue.length,
    queue,
    feasibility: {
      hackernews: "server-searchable (Algolia) — reliable",
      reddit: redditTried ? (redditHits ? "server-searchable this run" : "attempted; likely 403 from this IP (best-effort, empty is normal)") : "not searched",
      loginWalled: "LinkedIn, X/Twitter, Instagram, Facebook — a bot cannot and MUST NOT read or post there. Watch them yourself; paste a thread in and the agent drafts a reply.",
    },
    hardRule: "This queue is for DRAFTING only. Never auto-post/reply/DM. The human reviews, edits, and sends from their own account, then marks it sent (feeds LEARN).",
  };

  const md = renderQueue(report);
  if (args.out) { fs.writeFileSync(args.out, md); console.error(`queue → ${args.out} (${queue.length} threads)`); }
  else process.stdout.write(md);
  if (args.json) process.stderr.write("\n" + JSON.stringify(report, null, 2) + "\n");
}

function renderQueue(r) {
  const rows = r.queue.map((q, i) => `
### ${i + 1}. [${q.platform}] ${q.title}  ·  relevance ${q.score}
- **by** ${q.author} — **open the thread:** ${q.url}
- **they said:** ${q.excerpt.replace(/\n/g, " ")}
- **draftReply:** _(agent drafts here in your voice, grounded in the article; you edit + post)_
`).join("\n");
  return `# Engagement queue — DRAFTS ONLY (human sends)

> Proactively discovered by \`engage-scout\`. Keywords: ${r.generatedForKeywords.join(", ")}.
> **${r.found} genuinely-relevant public thread(s)** (relevance scored in code, ≥ floor).
> ⚠️ ${r.hardRule}

**Feasibility (honest walls):** HN — ${r.feasibility.hackernews}. Reddit — ${r.feasibility.reddit}.
Login-walled — ${r.feasibility.loginWalled}
${rows || "\n_(No thread cleared the relevance floor this run — that's the spam gate working, not a failure. Lower --min-score to widen, or try different keywords.)_\n"}
---
_Next: the agent drafts each \`draftReply\` in your voice (PUBLISH+ENGAGE §4). You review, post from your own account, then mark sent → MEASURE/LEARN._
`;
}

main().catch((e) => { console.error("engage-scout error:", e.message); process.exit(1); });
