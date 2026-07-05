#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// syndicate.mjs — the PUBLISH half of /viral-loop, POSSE-style.
//
// Input: one canonical article (--from a markdown file) + its live URL (--url).
// Output: a SYNDICATION KIT — per-channel paste-ready copy + 1-click share-intent
// links — so one canonical publish fans out to every channel in seconds.
// Deterministic core: no LLM, no keys, no network. Node 18+, zero dependencies.
//
// ░░ THE HARD LINE (do not remove) ░░
// This tool DRAFTS and links. It NEVER posts, replies, DMs, or schedules — not via
// API, not via browser automation. Auto-posting to LinkedIn/X/IG/TikTok violates ToS,
// gets accounts banned, and reads as a bot. Every output is paste-ready copy or a
// 1-click intent URL the HUMAN clicks. The whole point of POSSE is that the canonical
// lives on YOUR site; the copies link home. You own Send.
//
// Usage:
//   node syndicate.mjs --from marketing/my-article.md --url https://site.com/articles/x.html
//   node syndicate.mjs --from … --url … --handle wjlgatech --out marketing/my-article-kit.md
//
// Flags:
//   --from <file>     canonical article markdown (title = first "# ", subtitle = first "*..*")
//   --url  <url>      the LIVE canonical URL (used for every link + intent). Required.
//   --handle <name>   your X/Twitter handle (for "via @handle"), optional
//   --out  <file>     write the kit here (default: stdout)
// ─────────────────────────────────────────────────────────────────────────────
import fs from "node:fs";

const HELP = `syndicate — POSSE syndication kit for /viral-loop (drafts + intents, never sends).
  --from <file>  canonical article md   --url <live-url> (required)
  --handle <x>   your X handle           --out <file>
Publish once on your own site; this fans it out. You click Send.`;

function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") o.help = true;
    else if (a.startsWith("--")) { o[a.slice(2)] = argv[i + 1]; i++; }
  }
  return o;
}
const args = parseArgs(process.argv.slice(2));
if (args.help || !args.from || !args.url) { console.log(HELP); process.exit(args.help ? 0 : 1); }

const enc = encodeURIComponent;
function clip(s, n) { s = (s || "").trim(); return s.length <= n ? s : s.slice(0, n - 1).trimEnd() + "…"; }

// ── extract the article's bones (deterministic) ──────────────────────────────
function extract(path) {
  const raw = fs.readFileSync(path, "utf8");
  const lines = raw.split("\n");
  let title = "", subtitle = "";
  const headings = [], strongs = [], hashtags = [];
  let hook = "";
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    if (!title && /^#\s+/.test(t)) { title = t.replace(/^#\s+/, "").trim(); continue; }
    if (title && !subtitle && /^[*_].+[*_]$/.test(t)) { subtitle = t.replace(/^[*_]+|[*_]+$/g, "").trim(); continue; }
    if (/^##\s+/.test(t)) headings.push(t.replace(/^#+\s+/, "").replace(/[*`]/g, "").trim());
    // Bold-lead phrases that read as CLAIMS (skip quotes and short fragments like "Kitchen A is top-down.")
    for (const m of t.matchAll(/\*\*([^*]{22,})\*\*/g)) {
      const s = m[1].replace(/[`]/g, "").trim();
      if (/^["“'']/.test(s) || s.split(/\s+/).length < 4) continue;
      strongs.push(s);
    }
    for (const m of t.matchAll(/(#[A-Za-z][A-Za-z0-9]+)/g)) if (t.startsWith("*#") || t.startsWith("#")) hashtags.push(m[1]);
    // first substantial prose paragraph = the hook
    if (!hook && title && t && !/^[#>|*_!\-`]/.test(t) && !t.startsWith("![") && t.length > 40) hook = t.replace(/[*`]/g, "");
  }
  const tags = [...new Set(hashtags)].slice(0, 6);
  const points = [...new Set(strongs)].slice(0, 5);
  return { title, subtitle, hook, headings: [...new Set(headings)], points, tags };
}

const a = extract(args.from);
const url = args.url;
const via = args.handle ? ` via @${args.handle}` : "";
const tagline = a.tags.length ? "\n\n" + a.tags.join(" ") : "";
const teaser = a.hook || a.subtitle || a.title;

// ── 1-click share intents (open a pre-filled composer; the human clicks Post) ─
const xText = clip(`${a.title}`, 200);
const intents = {
  "X / Twitter": `https://twitter.com/intent/tweet?text=${enc(xText + via)}&url=${enc(url)}`,
  "LinkedIn": `https://www.linkedin.com/sharing/share-offsite/?url=${enc(url)}`,
  "Facebook": `https://www.facebook.com/sharer/sharer.php?u=${enc(url)}`,
  "Reddit": `https://www.reddit.com/submit?url=${enc(url)}&title=${enc(clip(a.title, 300))}`,
  "Hacker News": `https://news.ycombinator.com/submitlink?u=${enc(url)}&t=${enc(clip(a.title, 80))}`,
  "Bluesky": `https://bsky.app/intent/compose?text=${enc(clip(a.title, 240) + "\n\n" + url)}`,
  "Threads": `https://www.threads.net/intent/post?text=${enc(clip(a.title, 400) + "\n\n" + url)}`,
};

// ── per-channel paste-ready drafts ───────────────────────────────────────────
const pts = a.points.length ? a.points : a.headings;
const bullets = pts.slice(0, 4).map((p) => `• ${p}`).join("\n");

const linkedin = `${teaser}\n\n${bullets}\n\nFull piece (published on my own site — link in first comment):\n${url}${tagline}`;
const xthread = [
  `${clip(teaser, 250)}\n\n🧵`,
  ...pts.slice(0, 3).map((p, i) => `${i + 1}/ ${clip(p, 260)}`),
  `Read the whole thing (I publish canonically on my own site, not the feed):\n${url}${via ? "\n\n— @" + args.handle : ""}`,
].map((t, i) => `**Post ${i + 1}:**\n${t}`).join("\n\n");
const ig = `${clip(teaser, 180)}\n\n(full article at the link in bio → ${url})\n${a.tags.join(" ")}`;
const youtube = `${a.title}\n\n${a.subtitle || teaser}\n\nRead the full article: ${url}\n\nChapters:\n${a.headings.slice(0, 8).map((h) => `• ${h}`).join("\n")}\n${tagline}`;

// ── render ───────────────────────────────────────────────────────────────────
const md = `# Syndication kit — ${a.title}

> **DRAFTS ONLY — you publish, you send.** Canonical lives at ${url}. Every copy below links home.
> This tool never posts/DMs/schedules (ToS + bans + brand). Polish the voice, then Send yourself.

## 1-click share intents (open a pre-filled composer → you click Post)

${Object.entries(intents).map(([k, v]) => `- **${k}:** ${v}`).join("\n")}

## Owned homes (canonical stays yours)

- **Medium:** New story → \`⋯\` → **Import a story** → paste \`${url}\`. Medium auto-sets rel=canonical back to your site.
- **Substack:** New post → paste the body, then Settings → set **Canonical URL** = \`${url}\`.
- **Your feed:** already carries it — \`/feed.xml\` · \`/feed.json\`.

## LinkedIn (feed post teasing the article)

Post the article via LinkedIn's article editor, or drop this feed teaser with the link as the first comment:

\`\`\`
${linkedin}
\`\`\`

## X / Twitter (thread)

${xthread}

## Instagram (caption)

\`\`\`
${ig}
\`\`\`

## YouTube (description, if you cut a video from this)

> Video is a *different artifact* — record a short from the article, then upload with this description:

\`\`\`
${youtube}
\`\`\`

---
*Generated by \`viral-loop/syndicate.mjs\` from ${args.from}. Deterministic; no LLM. The human owns Send.*
`;

if (args.out) { fs.writeFileSync(args.out, md); console.log(`kit → ${args.out} (${Object.keys(intents).length} intents · 5 channels)`); }
else process.stdout.write(md);
