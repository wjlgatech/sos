#!/usr/bin/env node
/* fake_media_browser.cjs — test getUserMedia features AS AN END USER, no human needed.
 *
 * Launches real Chromium with FAKE MEDIA DEVICES: the microphone "speaks" a WAV file you
 * provide (--use-file-for-fake-audio-capture), the camera shows a synthetic feed, and the
 * permission prompt auto-grants — so a script can drive the real UI (the same buttons a
 * finger hits) through mic/camera features and assert what the user would actually see.
 *
 * Usage:
 *   node fake_media_browser.cjs <url> [--wav speech.wav] [--scenario my_scenario.cjs]
 *                                     [--headed] [--shot /tmp/out.png] [--noloop]
 *
 * Scenario contract (a .cjs file):
 *   module.exports = async ({ page, browser, context, log, logs }) => { ... }
 *   - drive `page` (Playwright Page) through the user journey; throw to fail (exit 1).
 *   - `logs` = captured console/pageerror lines; `log(msg)` prints a step header.
 *   Without --scenario: opens the URL, waits 5s, dumps page text head + console,
 *   saves a screenshot — a smoke "does it even load with a live mic".
 *
 * Resolution order (override with env):
 *   PLAYWRIGHT_CORE  a playwright-core dir   → else require.resolve → npm -g scan
 *   CHROME_BIN       a Chromium binary       → else newest ~/Library/Caches/ms-playwright
 *                                              → else system Chrome
 *
 * Gotchas baked in from real use:
 *   - WAV should be PCM 16-bit (any sample rate); it LOOPS as mic input unless --noloop.
 *   - waitUntil:"networkidle" never settles on dev servers (HMR sockets) — we use
 *     domcontentloaded; wait for YOUR element instead.
 *   - For press-and-hold UIs use mouse.down()/up() with a real delay, not click().
 */

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execSync } = require("child_process");

function resolvePlaywright() {
  if (process.env.PLAYWRIGHT_CORE) return require(process.env.PLAYWRIGHT_CORE);
  try {
    return require("playwright-core");
  } catch {
    /* not in local node_modules — scan global */
  }
  try {
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    for (const candidate of [
      path.join(root, "playwright-core"),
      path.join(root, "playwright", "node_modules", "playwright-core"),
    ])
      if (fs.existsSync(candidate)) return require(candidate);
    // packages that vendor playwright-core (e.g. openclaw)
    for (const pkg of fs.readdirSync(root)) {
      const vendored = path.join(root, pkg, "node_modules", "playwright-core");
      if (fs.existsSync(vendored)) return require(vendored);
    }
  } catch {
    /* fall through to the error below */
  }
  throw new Error(
    "playwright-core not found — `npm i -g playwright-core` or set PLAYWRIGHT_CORE=/path/to/playwright-core",
  );
}

function resolveChromium() {
  if (process.env.CHROME_BIN) return process.env.CHROME_BIN;
  const cache = path.join(os.homedir(), "Library", "Caches", "ms-playwright");
  if (fs.existsSync(cache)) {
    const builds = fs
      .readdirSync(cache)
      .filter((d) => d.startsWith("chromium-"))
      .sort()
      .reverse();
    for (const b of builds) {
      for (const sub of ["chrome-mac-arm64", "chrome-mac", "chrome-mac-x64"]) {
        const dir = path.join(cache, b, sub);
        if (!fs.existsSync(dir)) continue;
        for (const app of fs.readdirSync(dir).filter((f) => f.endsWith(".app"))) {
          const bin = path.join(dir, app, "Contents", "MacOS", app.replace(/\.app$/, ""));
          if (fs.existsSync(bin)) return bin;
        }
      }
    }
  }
  for (const sys of [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ])
    if (fs.existsSync(sys)) return sys;
  throw new Error(
    "No Chromium found — set CHROME_BIN, or `npx playwright install chromium`",
  );
}

(async () => {
  const argv = process.argv.slice(2);
  const url = argv.find((a) => !a.startsWith("--"));
  if (!url) {
    console.error(
      "usage: node fake_media_browser.cjs <url> [--wav f.wav] [--scenario f.cjs] [--headed] [--shot out.png] [--noloop]",
    );
    process.exit(2);
  }
  const opt = (name) => {
    const i = argv.indexOf(name);
    return i >= 0 ? argv[i + 1] : undefined;
  };
  const wav = opt("--wav");
  const scenarioPath = opt("--scenario");
  const shot = opt("--shot") || "/tmp/fake_media_browser.png";
  if (wav && !fs.existsSync(wav)) throw new Error(`--wav not found: ${wav}`);

  const { chromium } = resolvePlaywright();
  const args = [
    "--use-fake-ui-for-media-stream", // auto-grant the permission prompt
    "--use-fake-device-for-media-stream", // synthetic mic + camera devices
    "--autoplay-policy=no-user-gesture-required",
  ];
  if (wav)
    args.push(
      `--use-file-for-fake-audio-capture=${path.resolve(wav)}${argv.includes("--noloop") ? "%noloop" : ""}`,
    );

  const browser = await chromium.launch({
    executablePath: resolveChromium(),
    headless: !argv.includes("--headed"),
    args,
  });
  const context = await browser.newContext({
    permissions: ["microphone", "camera"],
  });
  const page = await context.newPage();
  const logs = [];
  page.on("console", (m) => logs.push(`[${m.type()}] ${m.text()}`));
  page.on("pageerror", (e) => logs.push(`[pageerror] ${e.message}`));
  const log = (s) => console.log(`\n— ${s}`);

  let failed = false;
  try {
    log(`open ${url}`);
    await page.goto(url, { waitUntil: "domcontentloaded" });

    if (scenarioPath) {
      const scenario = require(path.resolve(scenarioPath));
      await scenario({ page, browser, context, log, logs });
    } else {
      await page.waitForTimeout(5000);
      console.log("\n— page text (head) —");
      console.log((await page.innerText("body")).slice(0, 800));
    }
  } catch (e) {
    failed = true;
    console.error("\n❌ scenario failed:", e.message || e);
  } finally {
    console.log("\n— browser console (last 20) —");
    console.log("  " + logs.slice(-20).join("\n  "));
    await page.screenshot({ path: shot }).catch(() => {});
    console.log(`\nscreenshot → ${shot}`);
    await browser.close();
  }
  process.exit(failed ? 1 : 0);
})().catch((e) => {
  console.error("launcher failed:", e.message || e);
  process.exit(2);
});
