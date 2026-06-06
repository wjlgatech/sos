# email-reader

Read and search a Gmail mailbox over IMAP using **Python standard library only**
— no MCP connector, no OAuth flow, no `pip install`. A connector-independent
fallback for when the built-in Gmail integration fails (e.g. `insufficient
authentication scopes`).

## Why this exists

The hosted Gmail connector authenticates via OAuth and can land without read
scope, failing every search. This skill sidesteps that entirely: it logs in to
`imap.gmail.com` with your address and a **Google App Password** and reads mail
directly. Credentials live in a local, gitignored `.env` (the private overlay);
the code is the public technical contract.

## Setup (once)

1. Turn on **2-Step Verification** for the Google account.
2. Create an **App Password**: Google Account → Security → 2-Step Verification →
   App passwords (16 characters).
3. Enable **IMAP**: Gmail → Settings → Forwarding and POP/IMAP → Enable IMAP.
4. `cp .env.example .env` and fill in `GMAIL_USER` and `GMAIL_APP_PASSWORD`.

## Usage

```bash
python gmail_imap.py search --from info@rbitfinancial.com
python gmail_imap.py search --from info@rbitfinancial.com --since 2025-01-01 --json
python gmail_imap.py read   --from info@rbitfinancial.com --limit 5
python gmail_imap.py read   --uid 4821
python gmail_imap.py folders
```

Filters (for `search` and `read`): `--from`, `--to`, `--subject`, `--text`,
`--since YYYY-MM-DD`, `--before YYYY-MM-DD`, `--unread`, `--limit N` (0 = all),
`--json`. Default folder `[Gmail]/All Mail`; override with `--folder`.

Read-only: folders are opened with `readonly=True`; nothing is ever modified.

## Exit codes

| code | meaning |
|------|---------|
| 0 | success |
| 1 | usage / runtime error |
| 2 | auth error (bad app password, 2SV off, or IMAP disabled) |

## Requirements

Python 3.9+ (stdlib only). No third-party packages.
