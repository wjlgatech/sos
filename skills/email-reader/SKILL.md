---
name: email-reader
description: >-
  Read and search a Gmail mailbox over IMAP using Python stdlib only — no MCP
  connector, no OAuth, no pip installs. Authenticates with a Gmail address and
  a Google App Password kept in a local .env. Use when asked to check, search,
  read, or summarize someone's emails (e.g. "what did <person> email me",
  "find emails from <address>", "summarize the latest mail from <sender>"),
  especially when the built-in Gmail connector is unavailable or returns
  "insufficient authentication scopes".
---

# Email Reader (Gmail over IMAP)

Connector-independent way to read Gmail. Everything runs locally through
`imap.gmail.com` with the Python standard library (`imaplib`, `email`).

## When to use this

- The built-in Gmail/MCP connector fails (e.g. `insufficient authentication
  scopes`) or isn't connected.
- You need to search or summarize someone's emails headlessly/repeatably.
- You want a path that doesn't depend on a browser session or OAuth grant.

## One-time setup (the user does this once)

1. Enable **2-Step Verification** on the Google account.
2. Create an **App Password**: Google Account → Security → 2-Step Verification
   → App passwords → generate one (16 chars, shown as 4 groups).
3. Ensure **IMAP is enabled**: Gmail → Settings → Forwarding and POP/IMAP →
   Enable IMAP.
4. Copy `.env.example` to `.env` in this skill directory and fill in:
   ```
   GMAIL_USER=you@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```
   `.env` is gitignored and must never be committed (private overlay).

## How to run

From this skill directory (`skills/email-reader/`):

```bash
# Summaries of the most recent messages from a sender:
python gmail_imap.py search --from info@rbitfinancial.com

# Narrow by date / subject, machine-readable output:
python gmail_imap.py search --from info@rbitfinancial.com --since 2025-01-01 --json

# Full plain-text bodies (newest first), capped:
python gmail_imap.py read --from info@rbitfinancial.com --limit 5

# A single message by UID (UIDs come from `search` output):
python gmail_imap.py read --uid 4821

# List available folders:
python gmail_imap.py folders
```

Filters (apply to `search` and `read`): `--from`, `--to`, `--subject`,
`--text`, `--since YYYY-MM-DD`, `--before YYYY-MM-DD`, `--unread`,
`--limit N` (0 = all), `--json`. Default folder is `[Gmail]/All Mail` so it
searches everything, not just the inbox; override with `--folder`.

## Recommended agent flow

1. Run `search --json` with the requested filters to get UIDs + headers.
2. If the user wants content, run `read --json` (optionally `--uid` per
   message) and summarize the bodies.
3. Report counts honestly. If zero matches, say so and suggest broadening the
   filter (drop `--since`, widen `--from` to a domain, etc.).

## Exit codes

`0` success · `1` usage/runtime error · `2` authentication error (bad app
password, 2SV off, or IMAP disabled — the stderr message says which).

## Notes / limits

- IMAP `FROM`/`SUBJECT`/`TEXT` match substrings server-side; results may be
  slightly broad — verify the `From` header before trusting a match.
- Read-only: the script selects folders with `readonly=True` and never
  deletes, moves, or marks mail.
- Stdlib only, matching this repo's zero-dependency principle.
