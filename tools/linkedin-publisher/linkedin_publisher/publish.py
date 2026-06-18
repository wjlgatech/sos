"""Build the browser-console publish bundle for LinkedIn's Tiptap editor.

LinkedIn's article editor is Tiptap (ProseMirror). The public API cannot create
articles, so we generate a console script the user runs in the open editor:
  1. set the title field
  2. paste cleaned body via a DataTransfer 'paste' event (single-newline text)
  3. inject each extracted code block as a real codeBlock node (one <pre>, dark)

This mirrors the verified fixes in LINKEDIN_ARTICLE_POSTING_GUIDE.md.
"""
import json
from typing import List

from .preprocess import CODE_MARKER


def build_publish_bundle(title: str, paste_text: str, code_blocks: List[str]) -> str:
    """Return a self-contained JS string to paste into the browser console."""
    # split body on the code markers so JS can interleave paste + codeBlock inject
    segments, codes = _split_on_markers(paste_text, code_blocks)
    payload = json.dumps({"title": title, "segments": segments, "codes": codes},
                         ensure_ascii=False)
    return _TEMPLATE.replace("__PAYLOAD__", payload)


def _split_on_markers(text: str, code_blocks: List[str]):
    segments, codes, buf, i = [], [], [], 0
    marker_prefix = CODE_MARKER.split("{")[0]
    for line in text.split("\n"):
        if line.strip().startswith(marker_prefix):
            idx = int("".join(ch for ch in line if ch.isdigit()))
            segments.append("\n".join(buf).strip())
            buf = []
            codes.append(code_blocks[idx] if idx < len(code_blocks) else "")
        else:
            buf.append(line)
    if buf:
        segments.append("\n".join(buf).strip())
    return segments, codes


_TEMPLATE = r"""
(async () => {
  const DATA = __PAYLOAD__;
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  // 1) Title
  const titleEl = document.querySelector('textarea, [data-placeholder*="title" i], h1[contenteditable]');
  if (titleEl) {
    if ('value' in titleEl) { titleEl.value = DATA.title; }
    else { titleEl.textContent = DATA.title; }
    titleEl.dispatchEvent(new Event('input', { bubbles: true }));
  } else { console.warn('Title field not found — set it manually.'); }

  const editor = document.querySelector('[contenteditable="true"]');
  if (\!editor) { console.error('Article body editor not found.'); return; }
  editor.focus();

  const pasteText = (t) => {
    const dt = new DataTransfer();
    dt.setData('text/plain', t);
    editor.dispatchEvent(new ClipboardEvent('paste',
      { clipboardData: dt, bubbles: true, cancelable: true }));
  };

  const insertCode = (code) => {
    const tiptap = editor.editor;            // Tiptap instance on the DOM node
    if (\!tiptap) { pasteText(code); return; } // fallback
    const { state, view } = tiptap;
    const cb = state.schema.nodes.codeBlock;
    const node = cb.create(null, state.schema.text(code));
    const pos = state.selection.$to.end();
    view.dispatch(state.tr.insert(pos, node));
  };

  // 2) Interleave body segments with code blocks
  for (let i = 0; i < DATA.segments.length; i++) {
    if (DATA.segments[i]) { pasteText(DATA.segments[i] + "\n"); await sleep(120); }
    if (i < DATA.codes.length && DATA.codes[i]) { insertCode(DATA.codes[i]); await sleep(120); }
  }

  // 3) Cleanup stray empty paragraphs
  Array.from(editor.querySelectorAll('p')).forEach(p => { if (\!p.textContent.trim()) p.remove(); });
  editor.dispatchEvent(new Event('input', { bubbles: true }));
  console.log('%c[linkedin_publisher] body inserted. Verify code blocks render dark, then upload cover + Publish.', 'color:#58a6ff');
})();
"""
