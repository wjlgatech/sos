"""Self-contained tests for the email-reader skill (stdlib only, no network).

Run:  python -m pytest skills/email-reader/test_gmail_imap.py
  or:  python skills/email-reader/test_gmail_imap.py   (no pytest needed)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmail_imap as g  # noqa: E402


def test_imap_date():
    assert g._imap_date("2025-01-09") == "09-Jan-2025"
    assert g._imap_date("2024-12-31") == "31-Dec-2024"


def test_strip_html_removes_scripts_and_decodes_entities():
    html = ("<html><style>x{}</style><body>Hi&nbsp;<b>Addison</b>"
            "<script>bad()</script> &amp; bye</body></html>")
    out = g._strip_html(html)
    assert "Addison" in out
    assert "bad()" not in out
    assert "&" in out


def test_decode_rfc2047_header():
    assert g._decode("=?utf-8?B?SGVsbG8=?=") == "Hello"
    assert g._decode(None) == ""


def test_dotenv_and_credentials_strip_spaces():
    d = tempfile.mkdtemp()
    path = os.path.join(d, ".env")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('GMAIL_USER="a@b.com"\n# c\nGMAIL_APP_PASSWORD=abcd efgh\n')
    os.environ.pop("GMAIL_USER", None)
    os.environ.pop("GMAIL_APP_PASSWORD", None)
    g.load_dotenv(path)
    user, pw = g.get_credentials()
    assert user == "a@b.com"
    assert pw == "abcdefgh"  # spaces stripped


def test_build_search_default_all():
    class A:
        sender = to = subject = text = since = before = None
        unread = False
    assert g.build_search(A()) == ["ALL"]


def test_build_search_combines_criteria():
    class A:
        sender = "info@rbitfinancial.com"
        to = None
        subject = "invoice"
        text = None
        since = "2025-01-01"
        before = None
        unread = True
    crit = g.build_search(A())
    assert "FROM" in crit and "info@rbitfinancial.com" in crit
    assert "SUBJECT" in crit and "invoice" in crit
    assert "SINCE" in crit and "01-Jan-2025" in crit
    assert "UNSEEN" in crit


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
