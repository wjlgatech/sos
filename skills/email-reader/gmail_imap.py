#!/usr/bin/env python3
"""Read Gmail over IMAP using stdlib only — no pip installs.

Bypasses any MCP/OAuth connector. Authenticates with a Gmail address + a
Google *App Password* (Google Account -> Security -> 2-Step Verification ->
App passwords). Credentials are read from the environment or a local .env
file and are NEVER committed (see .gitignore: .env is ignored).

Commands:
    search   Find messages by sender / subject / date; print summaries.
    read     Print full plain-text body of matching messages.
    folders  List available IMAP folders (mailboxes).

Examples:
    python gmail_imap.py search --from info@rbitfinancial.com
    python gmail_imap.py search --from info@rbitfinancial.com --since 2025-01-01 --json
    python gmail_imap.py read --from info@rbitfinancial.com --limit 5
    python gmail_imap.py read --uid 4821

Exit codes: 0 ok, 1 usage/runtime error, 2 auth error.
"""
from __future__ import annotations

import argparse
import email
import imaplib
import json
import os
import sys
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
DEFAULT_FOLDER = '"[Gmail]/All Mail"'  # search everything, not just INBOX


def load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader (stdlib only). Does not overwrite real env vars."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def get_credentials() -> tuple[str, str]:
    user = os.environ.get("GMAIL_USER", "").strip()
    pw = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    # App passwords are shown with spaces ("abcd efgh ijkl mnop"); strip them.
    pw = pw.replace(" ", "")
    if not user or not pw:
        sys.stderr.write(
            "ERROR: set GMAIL_USER and GMAIL_APP_PASSWORD (env or .env).\n"
            "  GMAIL_USER=you@gmail.com\n"
            "  GMAIL_APP_PASSWORD=<16-char app password from Google Account>\n"
        )
        sys.exit(2)
    return user, pw


def connect(user: str, pw: str) -> imaplib.IMAP4_SSL:
    try:
        conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        conn.login(user, pw)
        return conn
    except imaplib.IMAP4.error as exc:
        sys.stderr.write(
            f"AUTH ERROR: {exc}\n"
            "Check: (1) the app password is correct, (2) 2-Step Verification is ON,\n"
            "(3) IMAP is enabled in Gmail Settings -> Forwarding and POP/IMAP.\n"
        )
        sys.exit(2)


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def build_search(args: argparse.Namespace) -> list[str]:
    """Build an IMAP SEARCH criteria list."""
    crit: list[str] = []
    if args.sender:
        crit += ["FROM", args.sender]
    if args.to:
        crit += ["TO", args.to]
    if args.subject:
        crit += ["SUBJECT", args.subject]
    if args.text:
        crit += ["TEXT", args.text]
    if args.since:
        # IMAP wants DD-Mon-YYYY, e.g. 01-Jan-2025
        crit += ["SINCE", _imap_date(args.since)]
    if args.before:
        crit += ["BEFORE", _imap_date(args.before)]
    if args.unread:
        crit += ["UNSEEN"]
    return crit or ["ALL"]


def _imap_date(iso: str) -> str:
    import datetime

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    d = datetime.date.fromisoformat(iso)
    return f"{d.day:02d}-{months[d.month - 1]}-{d.year}"


def search_uids(conn: imaplib.IMAP4_SSL, folder: str, criteria: list[str]) -> list[bytes]:
    status, _ = conn.select(folder, readonly=True)
    if status != "OK":
        sys.stderr.write(f"ERROR: cannot select folder {folder}\n")
        sys.exit(1)
    typ, data = conn.uid("search", None, *criteria)
    if typ != "OK":
        sys.stderr.write(f"ERROR: search failed ({typ})\n")
        sys.exit(1)
    return data[0].split() if data and data[0] else []


def fetch_headers(conn: imaplib.IMAP4_SSL, uid: bytes) -> dict:
    typ, data = conn.uid(
        "fetch", uid,
        "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])",
    )
    if typ != "OK" or not data or data[0] is None:
        return {}
    msg = email.message_from_bytes(data[0][1])
    when = ""
    if msg.get("Date"):
        try:
            when = parsedate_to_datetime(msg["Date"]).isoformat()
        except Exception:
            when = msg["Date"]
    return {
        "uid": uid.decode(),
        "from": _decode(msg.get("From")),
        "to": _decode(msg.get("To")),
        "subject": _decode(msg.get("Subject")),
        "date": when,
    }


def fetch_body(conn: imaplib.IMAP4_SSL, uid: bytes) -> str:
    typ, data = conn.uid("fetch", uid, "(RFC822)")
    if typ != "OK" or not data or data[0] is None:
        return ""
    msg = email.message_from_bytes(data[0][1])
    return _extract_text(msg)


def _extract_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        # Prefer text/plain; fall back to stripped text/html.
        plain, html = "", ""
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            if ctype == "text/plain" and not plain:
                plain = _payload(part)
            elif ctype == "text/html" and not html:
                html = _payload(part)
        return plain or _strip_html(html)
    if msg.get_content_type() == "text/html":
        return _strip_html(_payload(msg))
    return _payload(msg)


def _payload(part: email.message.Message) -> str:
    try:
        raw = part.get_payload(decode=True)
        if raw is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")
    except Exception:
        return ""


def _strip_html(html: str) -> str:
    import re

    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    return re.sub(r"[ \t]+\n", "\n", re.sub(r"\n{3,}", "\n\n", text)).strip()


def cmd_folders(conn: imaplib.IMAP4_SSL, args: argparse.Namespace) -> int:
    typ, data = conn.list()
    if typ != "OK":
        return 1
    for line in data:
        print(line.decode(errors="replace"))
    return 0


def cmd_search(conn: imaplib.IMAP4_SSL, args: argparse.Namespace) -> int:
    uids = search_uids(conn, args.folder, build_search(args))
    uids = uids[-args.limit:] if args.limit else uids
    uids = list(reversed(uids))  # newest first
    results = [fetch_headers(conn, u) for u in uids]
    results = [r for r in results if r]
    if args.json:
        print(json.dumps({"count": len(results), "messages": results}, indent=2))
    else:
        if not results:
            print("No matching messages.")
        for r in results:
            print(f"[{r['uid']}] {r['date']}")
            print(f"  From:    {r['from']}")
            print(f"  Subject: {r['subject']}")
            print()
        print(f"{len(results)} message(s).")
    return 0


def cmd_read(conn: imaplib.IMAP4_SSL, args: argparse.Namespace) -> int:
    if args.uid:
        uids = [args.uid.encode()]
    else:
        uids = search_uids(conn, args.folder, build_search(args))
        uids = uids[-args.limit:] if args.limit else uids
        uids = list(reversed(uids))
    out = []
    for u in uids:
        hdr = fetch_headers(conn, u)
        body = fetch_body(conn, u)
        if args.json:
            out.append({**hdr, "body": body})
        else:
            print("=" * 72)
            print(f"[{hdr.get('uid','?')}] {hdr.get('date','')}")
            print(f"From:    {hdr.get('from','')}")
            print(f"To:      {hdr.get('to','')}")
            print(f"Subject: {hdr.get('subject','')}")
            print("-" * 72)
            print(body.strip() or "(no text body)")
            print()
    if args.json:
        print(json.dumps({"count": len(out), "messages": out}, indent=2))
    return 0


def main(argv: list[str]) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Read Gmail over IMAP (stdlib only).")
    p.add_argument("--folder", default=DEFAULT_FOLDER,
                   help=f'IMAP folder (default {DEFAULT_FOLDER})')
    sub = p.add_subparsers(dest="command", required=True)

    def add_filters(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--from", dest="sender", help="sender email/substring")
        sp.add_argument("--to", dest="to", help="recipient email/substring")
        sp.add_argument("--subject", help="subject substring")
        sp.add_argument("--text", help="full-text substring")
        sp.add_argument("--since", help="ISO date YYYY-MM-DD (on/after)")
        sp.add_argument("--before", help="ISO date YYYY-MM-DD (before)")
        sp.add_argument("--unread", action="store_true", help="unread only")
        sp.add_argument("--limit", type=int, default=25, help="max messages (0=all)")
        sp.add_argument("--json", action="store_true", help="JSON output")

    sp_s = sub.add_parser("search", help="list matching message summaries")
    add_filters(sp_s)

    sp_r = sub.add_parser("read", help="print full bodies of matching messages")
    add_filters(sp_r)
    sp_r.add_argument("--uid", help="fetch a single message by UID")

    sub.add_parser("folders", help="list IMAP folders")

    args = p.parse_args(argv)

    user, pw = get_credentials()
    conn = connect(user, pw)
    try:
        if args.command == "folders":
            return cmd_folders(conn, args)
        if args.command == "search":
            return cmd_search(conn, args)
        if args.command == "read":
            return cmd_read(conn, args)
        return 1
    finally:
        try:
            conn.logout()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
