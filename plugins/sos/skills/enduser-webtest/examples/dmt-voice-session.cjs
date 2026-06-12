/* Worked example: DreamMakeTrue's voice session, tested exactly as a finger would.
 *
 *   node scripts/fake_media_browser.cjs http://localhost:3000/library \
 *        --wav /tmp/voice_question.wav --scenario examples/dmt-voice-session.cjs
 *
 * Demonstrates the two gesture patterns that matter for media UIs:
 *   TAP  (a <250ms press toggles something)  → locator.click()
 *   HOLD (press-and-hold to record)          → mouse.down() … delay … mouse.up()
 */
module.exports = async ({ page, log }) => {
  log("enter a session via the library (Karpathy off the shelf)");
  const card = page.locator("button", { hasText: "Andrej Karpathy" }).first();
  await card.waitFor({ timeout: 20000 });
  await card.click();
  await page.waitForURL("**/session", { timeout: 15000 });
  await page.waitForTimeout(1500);

  log("TAP the composer mic (connect voice)");
  await page.locator('button[aria-label="Tap to start voice"]').click();
  const holdBtn = page.locator('button[aria-label="Hold to talk · tap to end"]');
  await holdBtn.waitFor({ timeout: 25000 }); // listening = mic + WS both up

  log("HOLD 5s while the fake mic speaks, then release");
  const box = await holdBtn.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.waitForTimeout(5000);
  await page.mouse.up();

  log("assert what the USER sees: transcript, then a grounded reply");
  const t0 = Date.now();
  while (Date.now() - t0 < 90000) {
    const body = await page.innerText("body");
    if (body.includes("captured no sound")) throw new Error("silent-mic message shown");
    if (body.includes("Didn't catch that")) throw new Error("server got an empty transcript");
    if (/downside|cannot yet measure/i.test(body)) {
      console.log("  ✅ transcript landed in the UI");
      await page.waitForTimeout(15000); // give the avatar's streamed reply a moment
      const final = await page.innerText("body");
      const i = final.lastIndexOf("Andrej Karpathy");
      console.log("  reply: " + final.slice(i, i + 220).replace(/\s+/g, " "));
      return;
    }
    await page.waitForTimeout(2000);
  }
  throw new Error("no transcript appeared within 90s");
};
