// viral-loop art-board renderer — HTML boards → PNG at 2x (crisp for LinkedIn/X).
// Usage:  node render.mjs [boards-dir] [out-dir]
//   boards-dir : folder of *.html art-boards, each with a `.board` root element
//                (default: this script's own directory)
//   out-dir    : where PNGs land (default: boards-dir's parent, the media/ folder)
// Convention (agentic-portfolio docs/marketing/media/): boards live in media/src/,
// PNGs land in media/, and each board links ./shared.css (see brand-tokens.css).
// Requires Playwright (`npm i -D playwright` in the host repo).
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import fs from "node:fs";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const src = path.resolve(process.argv[2] || here);
const out = path.resolve(process.argv[3] || path.dirname(src));

const boards = fs.readdirSync(src).filter((f) => f.endsWith(".html"));
if (!boards.length) {
  console.error(`no .html art-boards in ${src}`);
  process.exit(1);
}

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 2 });
for (const f of boards) {
  await page.goto("file://" + path.join(src, f));
  const name = f.replace(/\.html$/, ".png");
  await page.locator(".board").screenshot({ path: path.join(out, name) });
  console.log("rendered", name);
}
await browser.close();
