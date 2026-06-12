---
name: enduser-webtest
description: "Test mic/camera (getUserMedia) web features AS AN END USER — no human, no hardware: real Chromium with fake media devices, where the microphone 'speaks' a WAV file you provide and permissions auto-grant, so a script drives the REAL UI (the same buttons a finger hits) and asserts what the user actually sees. Use when a voice/video feature 'works in the server harness but not for the user', when verifying a fix to any getUserMedia flow (push-to-talk, voice chat, camera capture, level meters, device pickers), or when CI needs a browser-half test that server-side API tests can't cover. Triggers on 'test as end user', 'fake microphone/camera', 'test getUserMedia / push-to-talk / voice UI', 'mic works for me but not the user', 'browser e2e with audio'. NOT for plain DOM e2e without media (any Playwright setup does that) and NOT for testing audio QUALITY (fake capture is bit-exact playback, not a room mic)."
argument-hint: "[url + what to verify — e.g. 'localhost:3000/session, the push-to-talk flow']"
allowed-tools: Bash, Read, Write
metadata:
  type: testing
  portable: true
  cross-agent: true
  origin: "DreamMakeTrue voice-mic incident, 2026-06-11"
---

# Skill: enduser-webtest — fake-media Chromium harness for getUserMedia features

## The lesson this encodes (why it exists)

A voice feature has TWO halves. Server harnesses (drive the WebSocket/API directly) prove
the engine half — STT, LLM, TTS. They **cannot execute** the browser half: `getUserMedia`,
AudioContext quirks (suspended contexts read silence), MediaRecorder container negotiation,
OS input-device selection, the actual buttons. Two "fixes" once shipped green on the server
harness while the user's mic stayed broken — because the failing layer was never run.
**A user-reported UI bug is not fixed until the fix is verified through the path the
user's finger takes.** This skill makes that cheap.

## The mechanism (three Chromium flags)

```
--use-fake-ui-for-media-stream                     auto-grant the permission prompt
--use-fake-device-for-media-stream                 synthetic mic + camera devices
--use-file-for-fake-audio-capture=<speech.wav>     the mic PLAYS this file (loops; %noloop to play once)
```

The page receives a real MediaStream carrying real speech — every layer downstream
(meters, recorders, VADs, silent-mic detectors, STT) behaves exactly as with a live human.

## Run it

```bash
SKILL=~/.claude/skills/enduser-webtest   # or the sos checkout path

# 1. Make the mic's "speech" — any PCM WAV; an engine's own TTS is perfect:
curl -s -X POST localhost:8001/v1/multimodal/tts -H 'Content-Type: application/json' \
  -d '{"text":"What is the first concrete move to cap a downside you cannot yet measure?"}' \
  -o /tmp/voice_question.wav

# 2. Smoke (does the page even load with a live mic?):
node $SKILL/scripts/fake_media_browser.cjs http://localhost:3000/session --wav /tmp/voice_question.wav

# 3. Full journey (scenario drives the real buttons + asserts the visible outcome):
node $SKILL/scripts/fake_media_browser.cjs http://localhost:3000/library \
     --wav /tmp/voice_question.wav --scenario $SKILL/examples/dmt-voice-session.cjs
```

`--headed` to watch it; `--shot out.png` for the evidence screenshot; exit 0/1 = pass/fail
(CI-gateable). Playwright + Chromium resolve automatically (env `PLAYWRIGHT_CORE` /
`CHROME_BIN` override; `npm i -g playwright-core && npx playwright install chromium` if bare).

## Writing a scenario (the assertion is what the USER sees)

```js
module.exports = async ({ page, log, logs }) => {
  // TAP  (<250ms toggle)   → locator.click()
  // HOLD (press-to-record) → mouse.down() … waitForTimeout(ms) … mouse.up()
  // PASS = expected text/state visible in the UI; throw to fail.
};
```

See `examples/dmt-voice-session.cjs` — library card → tap mic → hold 5s → assert the
transcript appears and the avatar replies.

## Agent guidance (gotchas already paid for)

- **`networkidle` never settles on dev servers** (HMR sockets) — use `domcontentloaded`
  and wait for your element.
- **Assert page-visible outcomes**, not network internals — "transcript text appears" is
  the end-user truth; a 200 on the wire is not.
- **Hold ≥ the app's tap threshold** (commonly ~250ms) or your "hold" registers as a tap.
- The WAV **loops** as mic input by default — phase doesn't matter for a multi-second
  hold; use `%noloop` (`--noloop`) when the test needs silence after one playback.
- Camera flows: the fake device renders a rolling test pattern — enough for "did the
  capture/preview/upload path run", not for CV quality.
- When this harness PASSES but the real user still fails, the diagnosis is environmental
  (wrong OS input device, hardware mute) — fix it in-product (device picker + level
  meter), don't keep patching the pipeline.

## Cross-agent install (once per machine)

```bash
git clone https://github.com/wjlgatech/sos.git && cd sos
bash plugins/sos/scripts/install-skills-global.sh   # → ~/.claude/skills + ~/.hermes/skills + Codex AGENTS.md
```
