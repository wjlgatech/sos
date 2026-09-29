#!/usr/bin/env sh
# install-voice.sh — set up the sos /voice skill for voice-as-input on THIS machine, end to end.
# Idempotent — safe to re-run.
#
#   sh plugins/sos/scripts/install-voice.sh
#
# What it does:
#   1. Symlinks the voice skill → ~/.claude/skills/voice (so `git pull` in this clone updates it).
#   2. Installs the optional audio stack: mic capture (sounddevice+numpy), LOCAL speech→text
#      (faster-whisper — no key, offline), and no-key text→speech (edge-tts). Handles PEP-668
#      ("externally-managed") pythons (e.g. Homebrew) by falling back to --user.
#   3. Wires a `talk` shell function into your rc: one-shot push-to-talk → transcribe → clipboard.
#   4. Runs `voice.py doctor` so you can see the stack is green.
#
# ffmpeg is NOT installed here (some providers want it) — `doctor` will name it if missing:
#   macOS: brew install ffmpeg   ·   Debian/Ubuntu: sudo apt install ffmpeg

set -e

CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST="${CLAUDE_SKILLS_DIR}/voice"

# ── 1/4  Link the skill (resolve source relative to this script, works from any clone) ──
script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
src_skill=$(CDPATH= cd "$script_dir/../skills/voice" 2>/dev/null && pwd || true)

echo "→ 1/4  Linking voice skill → ${DEST}…"
mkdir -p "${CLAUDE_SKILLS_DIR}"
if [ -n "${src_skill}" ] && [ -f "${src_skill}/SKILL.md" ]; then
  if [ -L "${DEST}" ] || [ ! -e "${DEST}" ]; then
    ln -sfn "${src_skill}" "${DEST}"
    echo "  ✓ ${DEST} -> ${src_skill}"
  else
    echo "  ! ${DEST} exists as a non-symlink — left untouched"
  fi
elif [ -f "${DEST}/scripts/voice.py" ]; then
  echo "  ✓ already present at ${DEST}"
else
  echo "  ✗ voice skill source not found. Run from a clone of the sos repo, or install the" >&2
  echo "    plugin via the marketplace first, then re-run." >&2
  exit 1
fi

# ── 2/4  Install the optional audio stack (PEP-668 aware) ──
echo "→ 2/4  Installing audio deps (sounddevice numpy faster-whisper edge-tts)…"
PKGS="sounddevice numpy faster-whisper edge-tts"
if python3 -m pip install ${PKGS} >/dev/null 2>&1; then
  echo "  ✓ installed"
elif python3 -m pip install --user --break-system-packages ${PKGS} >/dev/null 2>&1; then
  echo "  ✓ installed to user site-packages (PEP-668 externally-managed python)"
else
  echo "  ! pip install failed — install manually:" >&2
  echo "    python3 -m pip install --user --break-system-packages ${PKGS}" >&2
fi

# ── 3/4  Wire the `talk` shell function (idempotent via the 'sos /voice' marker) ──
add_talk_to_rc() {
  rc="$1"
  if [ -f "${rc}" ] && grep -q "sos /voice" "${rc}" 2>/dev/null; then
    echo "  ✓ talk() already in ${rc}"
    return 0
  fi
  cat >> "${rc}" <<'EOF'

# sos /voice — talk(): one-shot push-to-talk → transcribe locally → copy to clipboard.
#   talk         record (auto-stop on silence), transcribe with the 'base' model
#   talk small   more accurate (slower); any faster-whisper model name works
talk() {
  skill="$HOME/.claude/skills/voice/scripts/voice.py"
  [ -f "$skill" ] || { echo "voice skill not found at $skill"; return 1; }
  model="${1:-base}"
  wav="$(mktemp -t talk).wav"
  echo "🎤 speak now — press Enter to stop (or stay silent to auto-stop)…"
  python3 "$skill" record --out "$wav" --silence || { rm -f "$wav"; echo "record failed"; return 1; }
  text="$(python3 "$skill" transcribe "$wav" --model "$model")"
  rm -f "$wav"
  printf '%s\n' "$text"
  if command -v pbcopy >/dev/null 2>&1 && [ -n "$text" ]; then
    printf '%s' "$text" | pbcopy && echo "📋 copied to clipboard"
  fi
}
EOF
  echo "  ✓ added talk() to ${rc}"
}

echo "→ 3/4  Wiring the 'talk' alias into your shell rc…"
# Target the rc for the current login shell; default to zsh on macOS.
case "${SHELL:-}" in
  *bash) add_talk_to_rc "${HOME}/.bashrc" ;;
  *)     add_talk_to_rc "${HOME}/.zshrc" ;;
esac

# ── 4/4  Doctor (never abort the script on a red line) ──
echo "→ 4/4  Checking the voice stack…"
python3 "${DEST}/scripts/voice.py" doctor || true

echo ""
echo "✓ Done. Open a new terminal (or 'source' your rc), then just run:"
echo "    talk          # speak → transcribe → text on your clipboard"
echo "    talk small    # more accurate model"
