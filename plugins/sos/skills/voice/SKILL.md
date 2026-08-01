---
name: voice
description: Give any agent CLI push-to-talk voice — record the mic to a WAV, transcribe it (local, no key), and speak replies back — with a doctor-first diagnostic that names exactly what's missing. Use when the user wants to "add voice", "talk to the agent", "voice mode", "speech-to-text / transcribe mic", "push to talk", or "why isn't my mic working". Triggers on 'voice', 'voice mode', 'push to talk', 'transcribe', 'speech to text', 'STT', 'TTS', 'microphone'. NOT for browser getUserMedia UIs (see enduser-webtest) or generating an audio file from text alone (that's just TTS). Bundled engine: this skill's `scripts/voice.py` (stdlib; audio + STT/TTS are optional, lazily imported).
---

# /voice — push-to-talk voice for any agent, doctor-first

Point it at a terminal; get **push-to-talk voice**: record the mic → a WAV → text (locally, no key),
and speak replies back. Recreated and simplified from the hermes-agent voice engine into one
self-contained script that runs anywhere. The engine travels **with this skill** (`scripts/voice.py`).

## The principle: capture is bundled, the provider is a seam

Same shape as this plugin's other tools. **Audio capture is portable** — mic → a 16 kHz mono WAV is
stdlib `wave` + a lazily-imported `sounddevice`, offline, deterministic. **Transcription and speech are
a seam you wire, never bundled**: prefer a **local** model (`faster-whisper` — free, offline, no key)
or point at a hosted one (Groq / OpenAI / ElevenLabs / Edge). This skill never bundles a model or
calls a paid API for you — it captures the audio and hands you a clean seam.

## Doctor-first (check the env before the code)

Voice fails **silently from the environment** — a missing audio stack, a headless box, an absent STT
provider — far more often than from logic. So the engine *leads* with a diagnostic that names the
layer and the exact fix (Paul's "classify the failure layer first" doctrine, executable):

```bash
python3 scripts/voice.py doctor
#   ✅ audio capture   sounddevice + numpy present
#   ✅ speech→text    faster-whisper (free, offline, no key)
#   🟡 text→speech    none wired — `pip install edge-tts` (no key)
#   ✅ ffmpeg         /opt/homebrew/bin/ffmpeg
#   ✅ ready — `voice.py record` then `voice.py transcribe <wav>`
```

It honors **forwarded audio** (a `PULSE_SERVER`/`PIPEWIRE_REMOTE` socket makes SSH/Docker/WSL work) and
prints the exact `export`/mount/`pip install` for whatever's red. Exit 1 when not ready — gate it in CI.

## The loop

```bash
# 0) once — the optional stack (checked by doctor, never bundled)
pip install sounddevice numpy faster-whisper   # mic capture + LOCAL STT (no key, offline)
#   + ffmpeg (some providers) ; + edge-tts / a hosted key only if you want spoken replies

# 1) is it ready?
python3 scripts/voice.py doctor

# 2) push-to-talk → a WAV (Enter to stop; --silence auto-stops; --seconds caps length)
python3 scripts/voice.py record --out turn.wav --silence

# 3) WAV → text (local faster-whisper; silence-hallucinations filtered)
python3 scripts/voice.py transcribe turn.wav --model base
```

`python3 scripts/voice.py contract` prints the full contract.

## The voice contract (what the engine encodes + the linter of last resort — `doctor`)

- **Capture is portable.** Mic → 16 kHz mono WAV via stdlib `wave` + lazy `sounddevice`. 16 kHz is
  Whisper's native rate — don't resample.
- **Provider is a seam.** STT/TTS are wired, never bundled — a local model (no key) or a hosted one.
- **Never crash headless.** Audio libs are imported *lazily*; importing the engine on an SSH/Docker/WSL
  box with no PortAudio never raises — it degrades to a clear message + a fix.
- **Prefer local, no key.** Default to `faster-whisper` so voice works with zero keys and zero network.
- **Filter hallucinations.** Whisper invents phrases on silence ("thank you", "you", "subscribe") —
  the engine drops known phantoms so a quiet clip doesn't trigger phantom action.
- **Honor forwarded audio.** A `PULSE_SERVER`/`PIPEWIRE_REMOTE` socket works over SSH/Docker/WSL — the
  doctor treats it as OK, not a hard block.
- **Right-size the capture.** Discard clips under 0.3 s or below the silence RMS floor — don't transcribe noise.

## Honest edges

- **Real capture needs PortAudio + sounddevice.** Headless with no forwarded sound server can't record
  a mic (by physics, not a bug) — `doctor` says so and gives the forwarding recipe.
- **STT/TTS need a provider.** Local `faster-whisper` needs no key but downloads a model on first run;
  hosted providers need a key. The seam is deliberately thin — wire your call in `transcribe()`.
- **Not a browser mic tool.** For a web `getUserMedia` UI, use `enduser-webtest`. For voice *calls*
  (Twilio/Telnyx), that's a different integration.
- **`doctor` is a stack check, not a taste oracle** — it proves the pipes are connected; the quality of
  the STT/TTS is the provider's.

> Reference implementation (the full-featured original, coupled to its agent): hermes-agent
> `tools/voice_mode.py` — silence detection, streaming TTS, Termux/Discord paths. This skill is the
> decoupled, portable distillation.
