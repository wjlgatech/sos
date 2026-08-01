#!/usr/bin/env python3
"""voice.py — a self-contained push-to-talk voice engine for any agent CLI.

Recreated (simplified, decoupled) from the hermes-agent voice-mode implementation. Same design
principle as the rest of this plugin's tools: **the portable half is bundled; the provider half is a
seam.** Audio *capture* is stdlib + a lazily-imported `sounddevice` (records mic → a 16 kHz mono WAV,
Whisper's native rate). *Transcription* and *speech* are a **provider seam** you wire — a local
`faster-whisper` (no key, no network) or a hosted STT/TTS (Groq/OpenAI/ElevenLabs/Edge). anyagent
never bundles a model or calls a paid API for you.

Debugging doctrine (Paul's "check env before code"): **`voice.py doctor` first.** Voice fails silently
far more often from a *missing audio stack / headless environment / absent provider* than from logic —
so the engine leads with a diagnostic that names the layer and the exact install/export to fix it.

Zero required deps (stdlib). Optional at runtime, lazily imported so this NEVER crashes headless:
  pip install sounddevice numpy         # mic capture
  pip install faster-whisper            # local STT — free, offline, no key (recommended)

Usage:
  voice.py doctor                       # is the voice stack ready? (audio · STT · TTS · env) + fixes
  voice.py record [--out a.wav] [--seconds N] [--silence]   # push-to-talk → a WAV
  voice.py transcribe a.wav [--model base]                  # WAV → text via the local seam
  voice.py contract                     # print the voice contract this engine encodes
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
import wave

# ── Audio constants (faithful to the hermes engine) ──
SAMPLE_RATE = 16000     # Whisper's native rate
CHANNELS = 1            # mono
SAMPLE_WIDTH = 2        # int16 → 2 bytes/sample
SILENCE_RMS = 200       # RMS below this (of int16 0..32767) counts as silence
SILENCE_SECONDS = 3.0   # sustained silence before auto-stop (with --silence)
_TMP = os.path.join(tempfile.gettempdir(), "agent_voice")

# Known Whisper-on-silence hallucinations — filter these so a quiet clip doesn't "hear" phantom text.
WHISPER_HALLUCINATIONS = {
    "thank you", "thanks for watching", "you", "bye", "thank you for watching",
    "please subscribe", "subscribe", ".", "so", "okay", "thank you very much",
}


# ── The provider seam: capture is bundled, STT/TTS are wired (never bundled) ──
def _import_audio():
    """Lazily import sounddevice + numpy. Raises ImportError/OSError on a headless box — callers
    catch this so importing the module never crashes where there's no PortAudio."""
    import numpy as np
    import sounddevice as sd
    return sd, np


def _audio_available() -> bool:
    try:
        _import_audio()
        return True
    except Exception:
        return False


def _headless_reason() -> str | None:
    """A human reason (with the fix) if this environment can't do local audio — else None.
    Honors forwarded sound servers (a socket over SSH/Docker/WSL works fine)."""
    forwarded = bool(os.environ.get("PULSE_SERVER") or os.environ.get("PIPEWIRE_REMOTE"))
    if forwarded:
        return None
    if any(os.environ.get(v) for v in ("SSH_CLIENT", "SSH_TTY", "SSH_CONNECTION")):
        return ("over SSH, no audio devices — point at a sound server, e.g.\n"
                "    export PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native")
    try:
        with open("/proc/version", encoding="utf-8") as f:
            if "microsoft" in f.read().lower() and not os.environ.get("PULSE_SERVER"):
                return "in WSL without a PulseAudio bridge — set PULSE_SERVER"
    except OSError:
        pass
    if os.path.exists("/.dockerenv") and not forwarded:
        return ("inside a container with no audio forwarding — mount the host socket:\n"
                "    -v $XDG_RUNTIME_DIR/pulse/native:$XDG_RUNTIME_DIR/pulse/native "
                "-e PULSE_SERVER=unix:$XDG_RUNTIME_DIR/pulse/native")
    return None


def _stt_provider() -> tuple[str | None, str]:
    """Which STT provider is wired, and a note. Prefers a LOCAL model (no key, offline)."""
    try:
        import faster_whisper  # noqa: F401
        return "local", "faster-whisper (free, offline, no key)"
    except Exception:
        pass
    if os.environ.get("GROQ_API_KEY"):
        return "groq", "Groq (GROQ_API_KEY set)"
    if os.environ.get("VOICE_TOOLS_OPENAI_KEY") or os.environ.get("OPENAI_API_KEY"):
        return "openai", "OpenAI (API key set)"
    return None, "none wired — `pip install faster-whisper` (no key) or set GROQ_API_KEY / OPENAI_API_KEY"


def _tts_provider() -> tuple[str | None, str]:
    """Which TTS (speech) provider is wired. Edge TTS needs no key."""
    try:
        import edge_tts  # noqa: F401
        return "edge", "Edge TTS (free, no key)"
    except Exception:
        pass
    if os.environ.get("ELEVENLABS_API_KEY"):
        return "elevenlabs", "ElevenLabs (key set)"
    if os.environ.get("VOICE_TOOLS_OPENAI_KEY") or os.environ.get("OPENAI_API_KEY"):
        return "openai", "OpenAI TTS (key set)"
    return None, "none wired — `pip install edge-tts` (no key) or set ELEVENLABS_API_KEY / OPENAI key"


def is_hallucination(text: str) -> bool:
    """True if a transcript is a known Whisper-on-silence phantom (so we drop it)."""
    c = (text or "").strip().lower().rstrip(".!")
    return not c or c in WHISPER_HALLUCINATIONS


# ── record: push-to-talk capture → WAV (portable half) ──
def record(out: str | None = None, *, seconds: float | None = None, silence_stop: bool = False) -> str | None:
    """Capture mic audio to a 16 kHz mono WAV. Press Enter to stop (or auto-stop on --silence /
    after --seconds). Returns the WAV path, or None if nothing usable was captured."""
    try:
        sd, np = _import_audio()
    except (ImportError, OSError) as e:
        print(f"⛔ audio capture unavailable: {e}\n   Run `voice.py doctor` for the fix.", file=sys.stderr)
        return None

    frames: list = []
    peak = {"rms": 0}
    last_voice = {"t": time.monotonic()}

    def cb(indata, n, ti, status):  # sounddevice callback
        frames.append(indata.copy())
        rms = int((float((indata.astype("float64") ** 2).mean()) ** 0.5))
        peak["rms"] = max(peak["rms"], rms)
        if rms >= SILENCE_RMS:
            last_voice["t"] = time.monotonic()

    print("🎙  recording — press Enter to stop" + (" (auto-stops after silence)" if silence_stop else ""))
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16", callback=cb):
        start = time.monotonic()
        import select
        while True:
            if select.select([sys.stdin], [], [], 0.15)[0]:
                sys.stdin.readline()
                break
            now = time.monotonic()
            if seconds and now - start >= seconds:
                break
            if silence_stop and (now - start) > 1.0 and (now - last_voice["t"]) >= SILENCE_SECONDS:
                print("… silence — stopping")
                break

    if not frames:
        print("⚠ no audio captured", file=sys.stderr)
        return None
    audio = np.concatenate(frames, axis=0)
    if len(audio) < int(SAMPLE_RATE * 0.3) or peak["rms"] < SILENCE_RMS:
        print(f"⚠ too short/quiet (peak RMS {peak['rms']} < {SILENCE_RMS}) — discarded", file=sys.stderr)
        return None

    os.makedirs(_TMP, exist_ok=True)
    path = out or os.path.join(_TMP, f"recording_{time.strftime('%Y%m%d_%H%M%S')}.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    print(f"✓ {path}  ({os.path.getsize(path)} bytes, {len(audio)/SAMPLE_RATE:.1f}s)")
    return path


def transcribe(wav: str, *, model: str = "base") -> str | None:
    """WAV → text via the LOCAL faster-whisper seam (no key, offline). Filters silence-hallucinations.
    For a hosted provider, wire your own call here — the seam is deliberately thin."""
    prov, _ = _stt_provider()
    if prov != "local":
        print("⛔ local STT not installed. `pip install faster-whisper` (no key), or wire a hosted "
              "provider. See `voice.py doctor`.", file=sys.stderr)
        return None
    from faster_whisper import WhisperModel
    segments, _info = WhisperModel(model, device="cpu", compute_type="int8").transcribe(wav)
    text = " ".join(s.text.strip() for s in segments).strip()
    if is_hallucination(text):
        print("… (silence / hallucination filtered)")
        return ""
    print(text)
    return text


# ── doctor: the diagnostic that leads (check env before code) ──
def doctor() -> int:
    print("voice.py doctor — is the voice stack ready?\n")
    ok = True

    audio = _audio_available()
    reason = _headless_reason()
    if audio and not reason:
        print("  ✅ audio capture   sounddevice + numpy present")
    elif reason:
        print(f"  ⛔ audio capture   {reason}"); ok = False
    else:
        print("  ⛔ audio capture   missing — pip install sounddevice numpy"); ok = False

    stt, stt_note = _stt_provider()
    print(f"  {'✅' if stt else '⛔'} speech→text    {stt_note}")
    ok = ok and bool(stt)

    tts, tts_note = _tts_provider()
    print(f"  {'✅' if tts else '🟡'} text→speech    {tts_note}")  # TTS is optional → warn, don't fail

    ff = shutil.which("ffmpeg")
    print(f"  {'✅' if ff else '🟡'} ffmpeg         {ff or 'not found — pip/brew/apt install ffmpeg (needed by some providers)'}")

    print("\n  " + ("✅ ready — `voice.py record` then `voice.py transcribe <wav>`"
                    if ok else "⛔ not ready — fix the ⛔ lines above, then re-run `voice.py doctor`"))
    return 0 if ok else 1


_CONTRACT = [
    ("capture-is-portable", "Mic → 16 kHz mono WAV is stdlib `wave` + a lazily-imported sounddevice — bundled, offline."),
    ("provider-is-a-seam", "STT/TTS are wired, never bundled: a LOCAL model (faster-whisper, no key) or a hosted one (Groq/OpenAI/ElevenLabs/Edge)."),
    ("doctor-first", "Voice fails silently from environment far more than logic — lead with `doctor`, which names the layer + the exact fix."),
    ("never-crash-headless", "Audio libs are lazy-imported; importing this engine on an SSH/Docker/WSL box never raises."),
    ("prefer-local-no-key", "Default to faster-whisper (free, offline) so voice works with zero keys and zero network."),
    ("filter-hallucinations", "Whisper invents phrases on silence ('thank you', 'you') — drop known phantoms, don't act on them."),
    ("honor-forwarded-audio", "A forwarded sound server (PULSE_SERVER/PIPEWIRE_REMOTE) makes SSH/Docker/WSL audio work — honor it, don't hard-block."),
]


def contract() -> int:
    print("The voice contract this engine encodes:\n")
    for cid, rule in _CONTRACT:
        print(f"  • [{cid}] {rule}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="voice.py", description="Self-contained push-to-talk voice engine (capture bundled, STT/TTS wired).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="Check the voice stack (audio · STT · TTS · env) and print exact fixes.").set_defaults(func=lambda a: doctor())
    sub.add_parser("contract", help="Print the voice contract this engine encodes.").set_defaults(func=lambda a: contract())
    r = sub.add_parser("record", help="Push-to-talk capture → a 16 kHz mono WAV.")
    r.add_argument("--out"); r.add_argument("--seconds", type=float); r.add_argument("--silence", action="store_true")
    r.set_defaults(func=lambda a: (0 if record(a.out, seconds=a.seconds, silence_stop=a.silence) else 1))
    t = sub.add_parser("transcribe", help="WAV → text via the local faster-whisper seam.")
    t.add_argument("wav"); t.add_argument("--model", default="base")
    t.set_defaults(func=lambda a: (0 if transcribe(a.wav, model=a.model) is not None else 1))
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
