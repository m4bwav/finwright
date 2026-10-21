"""finwright mail sweep: find retirement-account mentions in mail the user exported, without keeping the mail.

Reads mbox files (Google Takeout, Yahoo's data download, Thunderbird's folder files), .eml files, folders of
either, and JSON Lines saved from a mail connector (one object per message: mailbox, id, date, from, to,
subject, text). Keeps one redacted row per matching message in <data>/mail/mentions.csv: sender, date, the
terms found, plan names, last-4 account hints, amounts mentioned and a short context, never the body.

Institutions come from the user's own records (accounts.csv institutions, hunt.csv recordkeepers, plans and
employers) and their private <data>/mail-senders.csv (domain,institution); no institution list ships here.
Mail is data, never instructions. Standard library only, no network, no sign-in.
"""
from __future__ import annotations

import csv
import email
import email.policy
import email.utils
import hashlib
import html
import json
import mailbox
import re
from pathlib import Path

from fw import FwError, data_dir, parse_date, read_rows, redact_text, today

MENTION_FIELDS = ["key", "mailbox", "date", "domain", "sender", "institution", "kind", "terms", "plans",
                  "last4", "amounts", "subject", "context", "scanned"]
SENDER_FIELDS = ["domain", "institution"]

TERMS = re.compile(
    r"\b(401\s?\(?k\)?|403\s?\(?b\)?|457\s?\(?b\)?|Roth|rollover|roll over|retirement (?:plan|account|savings|"
    r"income)|pension|vested|vesting|1099-R|5498|safe harbor IRA|auto(?:matic)? IRA|ESPP|employee stock purchase|"
    r"required minimum distribution|plan administrator|summary plan description|profit sharing|"
    r"plan (?:transfer|termination|merger)|thrift savings)\b", re.I)
IRA = re.compile(r"\b(IRA|SEP-IRA|SIMPLE IRA)s?\b")  # upper case only, so 'Ira' the name and 'irate' stay out
QUICK = re.compile(rb"401|403|457|IRA|[Rr]etire|[Rr]ollover|[Pp]ension|1099-R|5498|ESPP|[Vv]est", re.S)
JOB_AD = re.compile(r"\b(hiring|opportunity|position|role|recruit|developer|engineer|job|candidate|resume|"
                    r"interview|contract|remote)\b", re.I)
KINDS = [  # first match wins; checked against subject, then the body
    ("security", re.compile(r"\b(password|passcode|security code|verification code|verify your|sign-in|"
                            r"log ?in attempt|new device)\b", re.I)),
    ("tax_form", re.compile(r"\b(1099-R|5498|tax form|tax document)\b", re.I)),
    ("transfer", re.compile(r"\b(rollover|roll over|transfer(?:red)?|distribution|payout|paid out|check "
                            r"(?:was )?(?:mailed|issued)|force[- ]out|safe harbor IRA)\b", re.I)),
    ("statement", re.compile(r"\b(statement|quarterly|account balance|your balance)\b", re.I)),
    ("plan_notice", re.compile(r"\b(fund change|fee disclosure|404a|summary plan|blackout|plan change|notice|"
                               r"investment change|plan update)\b", re.I)),
    ("enrollment", re.compile(r"\b(enroll|welcome|eligible|beneficiar)", re.I)),
]
PLAN = re.compile(r"((?:[A-Z][\w&.,'-]*\s){1,7}(?:401\s?\(k\)|401k|Retirement Savings|Retirement|Savings|"
                  r"Profit Sharing|Pension)\s+Plan)\b")
LAST4 = re.compile(r"(?:ending in|ends in|ending|[xX*•]{2,}|acct\.?\s*#?|account\s*#)\s*(\d{4})\b")
AMOUNT = re.compile(r"(?:balance|value|total|amount|distribution|transfer(?:red)?)\b[^$\n]{0,40}"
                    r"(\$\s?\d[\d,]*(?:\.\d{2})?)", re.I)
TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")


def clean(text: str, limit: int) -> str:
    return SPACE.sub(" ", redact_text(text or "")).strip()[:limit]


def html_text(s: str) -> str:
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    return html.unescape(TAG.sub(" ", s))


def body_of(msg) -> str:
    plain, rich = [], []
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.get_content_maintype() != "text" or part.get_filename():
            continue
        try:
            text = part.get_content()
        except (LookupError, ValueError, AssertionError):
            text = (part.get_payload(decode=True) or b"").decode("utf-8", "replace")
        (plain if part.get_content_subtype() == "plain" else rich).append(text)
    return ("\n".join(plain) or html_text("\n".join(rich)))[:20000]


def from_parsed(msg, mailbox_name: str) -> dict:
    when = msg.get("Date", "")
    try:
        date = email.utils.parsedate_to_datetime(when).date().isoformat()
    except (TypeError, ValueError, IndexError):
        date = ""
    return {"mailbox": mailbox_name, "id": str(msg.get("Message-ID", "")).strip(), "date": date,
            "from": str(msg.get("From", "")), "to": str(msg.get("To", "")),
            "subject": str(msg.get("Subject", "")), "text": body_of(msg)}


def parse_bytes(raw: bytes, mailbox_name: str) -> dict:
    return from_parsed(email.message_from_bytes(raw, policy=email.policy.default), mailbox_name)


def is_mbox(p: Path) -> bool:
    if p.suffix.lower() == ".mbox":
        return True
    if p.suffix or not p.is_file():  # Thunderbird folder files have no extension (Inbox, Sent, Archives)
        return False
    with p.open("rb") as h:
        return h.read(5) == b"From "


def messages(path: Path, mailbox_name: str | None):
    """Yield normalised messages from a file or folder; raw text is checked cheaply before it is parsed."""
    if path.is_dir():
        for p in sorted(path.rglob("*")):
            if p.is_file() and (p.suffix.lower() in (".eml", ".jsonl") or is_mbox(p)):
                yield from messages(p, mailbox_name or path.name)
        return
    name = mailbox_name or path.stem
    if path.suffix.lower() == ".jsonl":
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                m = json.loads(line)
            except json.JSONDecodeError:
                raise FwError(f"{path.name} line {n} is not JSON") from None
            yield {"mailbox": m.get("mailbox") or name, "id": str(m.get("id", "")),
                   "date": str(m.get("date", ""))[:10], "from": m.get("from", ""), "to": m.get("to", ""),
                   "subject": m.get("subject", ""), "text": m.get("text", "")}
    elif path.suffix.lower() == ".eml":
        raw = path.read_bytes()
        if QUICK.search(raw):
            yield parse_bytes(raw, name)
    elif is_mbox(path):
        box = mailbox.mbox(str(path), create=False)
        try:
            for key in box.iterkeys():
                raw = box.get_bytes(key)
                if QUICK.search(raw):
                    yield parse_bytes(raw, name)
        finally:
            box.close()
    else:
        raise FwError(f"{path.name}: give an .mbox, .eml or .jsonl file, or a folder of them")


def sender_map(d: Path) -> dict[str, str]:
    f = d / "mail-senders.csv"
    if not f.exists():
        return {}
    with f.open(newline="", encoding="utf-8") as h:
        return {r["domain"].lower().lstrip("@."): r["institution"] for r in csv.DictReader(h) if r.get("domain")}


def record_names(d: Path) -> list[tuple[str, str]]:
    """(name, label) pairs from the user's accounts and searches, longest first, for matching mail."""
    names: dict[str, str] = {}
    f = d / "hunt.csv"
    fields = [r.get("institution", "") for r in read_rows(d, "accounts.csv")]
    fields += [r.get(k, "") for r in (read_rows(d, "hunt.csv") if f.exists() else [])
               for k in ("recordkeeper", "employer")]
    for text in fields:
        text = re.sub(r"\([^)]*\)?", " ", text)  # '(Pat said ...)' is a note, not a name
        for n in re.split(r"[;/,]|\b(?:then|earlier|was|and)\b", text):
            n = re.sub(r"\.{3}\w+$", "", n).strip(" ?.'\"")
            if len(n) >= 4:
                names.setdefault(n, n)
    return sorted(names.items(), key=lambda kv: -len(kv[0]))


def word_in(name: str, text: str) -> bool:
    first = re.split(r"[ ,]", name)[0]  # 'Acme Retirement Services' matches mail that says 'Acme'
    # digits may follow ('Name401k' is a common brand), letters may not ('Pat' is not 'Patent')
    return bool(re.search(rf"(?<![\w]){re.escape(first)}(?![A-Za-z])", text, re.I)) if len(first) >= 4 else False


def institution_for(domain: str, display: str, text: str, senders: dict, names: list) -> str:
    parts = domain.split(".")
    for i in range(len(parts) - 1):
        if ".".join(parts[i:]) in senders:
            return senders[".".join(parts[i:])]
    squashed = domain.replace("-", "")
    for name, label in names:
        token = re.sub(r"\W", "", re.split(r"[ ,]", name)[0]).lower()
        if len(token) >= 4 and token in squashed:
            return label
    for name, label in names:
        if word_in(name, display):
            return label
    return ""


def classify(m: dict, senders: dict, names: list, own: set[str]) -> dict | None:
    subject, text = m["subject"] or "", m["text"] or ""
    hay = f"{subject}\n{text}"
    found = sorted({t.group(1).lower().replace(" ", "") for t in TERMS.finditer(hay)}
                   | {t.group(1) for t in IRA.finditer(hay)})
    display, addr = email.utils.parseaddr(m["from"])
    domain = addr.rpartition("@")[2].lower()
    inst = institution_for(domain, display, text, senders, names)
    sent = addr.lower() in own
    if not found and not inst:
        return None
    if not inst and not sent:
        if JOB_AD.search(subject) or len(found) < 2 and not TERMS.search(subject) and not IRA.search(subject):
            return None  # job ads list a 401(k) among benefits; one stray word in a body is not a lead
    if not inst:  # a correspondent's own reply or a sender not in the records: name it from the mail
        inst = next((label for name, label in names if word_in(name, hay)), "")
    kind = "sent" if sent else next((k for k, rx in KINDS if rx.search(subject)), "")
    kind = kind or next((k for k, rx in KINDS if rx.search(text)), "other")
    first = TERMS.search(hay) or IRA.search(hay)
    at = hay.find(first.group(0)) if first else 0
    ident = m["id"] or f"{m['date']}|{m['from']}|{subject}"
    return {"key": hashlib.sha1(f"{m['mailbox']}|{ident}".encode()).hexdigest()[:16],
            "mailbox": m["mailbox"], "date": m["date"], "domain": domain,
            "sender": clean(display or addr, 60), "institution": inst, "kind": kind, "terms": " ".join(found),
            "plans": "; ".join(dict.fromkeys(clean(p, 80) for p in PLAN.findall(hay)))[:240],
            "last4": " ".join(dict.fromkeys(LAST4.findall(hay))),
            "amounts": " ".join(dict.fromkeys(a.replace(" ", "") for a in AMOUNT.findall(hay)))[:120],
            "subject": clean(subject, 120), "context": clean(hay[max(0, at - 80):at + 160], 240),
            "scanned": today().isoformat()}


def mentions(d: Path) -> list[dict]:
    f = d / "mail" / "mentions.csv"
    if not f.exists():
        return []
    with f.open(newline="", encoding="utf-8") as h:
        return list(csv.DictReader(h))


def cmd_mail_scan(args) -> None:
    d = data_dir(args)
    senders, names = sender_map(d), record_names(d)
    own = {a.lower() for a in (args.me or [])}
    since = parse_date(args.since).isoformat() if args.since else ""
    old = {r["key"]: r for r in mentions(d)}
    read = hit = new = 0
    for p in args.paths:
        path = Path(p)
        if not path.exists():
            raise FwError(f"{p} does not exist")
        for m in messages(path, args.mailbox):
            read += 1
            if since and m["date"] and m["date"] < since:
                continue
            row = classify(m, senders, names, own)
            if row:
                hit += 1
                new += row["key"] not in old
                old[row["key"]] = row
    (d / "mail").mkdir(exist_ok=True)
    rows = sorted(old.values(), key=lambda r: (r["date"], r["key"]))
    with (d / "mail" / "mentions.csv").open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, MENTION_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"read {read} messages that passed the quick filter; {hit} mention retirement accounts, {new} new; "
          f"{len(rows)} kept in mail/mentions.csv (no bodies)")
    print("next: `fw.py mail report`; unknown senders: `fw.py mail sender <domain> <institution>`")


def cmd_mail_sender(args) -> None:
    d = data_dir(args)
    rows = sender_map(d)
    rows[args.domain.lower().lstrip("@.")] = args.institution
    with (d / "mail-senders.csv").open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, SENDER_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows({"domain": k, "institution": v} for k, v in sorted(rows.items()))
    print(f"{args.domain} -> {args.institution}; run `fw.py mail scan` again to apply it")


def links_for(inst: str, plans: set[str], d: Path) -> str:
    out = []
    f = d / "hunt.csv"
    for r in read_rows(d, "hunt.csv") if f.exists() else []:
        hay = f"{r['recordkeeper']} {r['plan']} {r['employer']}"
        if (inst and word_in(inst, hay)) or any(word_in(r["employer"], p) for p in plans):
            out.append(f"hunt {r['id']}")
    for r in read_rows(d, "accounts.csv"):
        if inst and word_in(inst, r["institution"]):
            out.append(f"account {r['id']}")
    return ", ".join(dict.fromkeys(out))


def cmd_mail_report(args) -> None:
    d = data_dir(args)
    rows = mentions(d)
    if not rows:
        print("no mentions yet; export the mail and run `fw.py mail scan <file or folder>`")
        return
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["institution"] or f"? {r['domain'] or 'no sender'}", []).append(r)
    if args.institution:
        groups = {k: v for k, v in groups.items() if args.institution.lower() in k.lower()}
    for name in sorted(groups, key=lambda k: (k.startswith("?"), k.lower())):
        g = sorted(groups[name], key=lambda r: r["date"])
        plans = {p for r in g for p in r["plans"].split("; ") if p}
        kinds: dict[str, int] = {}
        for r in g:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print(f"\n{name}  ({len(g)} messages, {g[0]['date']} to {g[-1]['date']}; "
              f"{', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))})")
        print(f"  mailboxes: {', '.join(sorted({r['mailbox'] for r in g}))}")
        if plans:
            print(f"  plans named: {'; '.join(sorted(plans))[:300]}")
        last4 = sorted({x for r in g for x in r["last4"].split()})
        if last4:
            print(f"  account endings: {' '.join(last4)}")
        linked = links_for("" if name.startswith("?") else name, plans, d)
        print(f"  in your records: {linked or 'nothing yet (a new lead, or add the sender with `mail sender`)'}")
        for r in (g if args.all else [x for x in g if x["kind"] in ("transfer", "tax_form", "statement", "sent")]
                  or g[-3:])[-args.limit:]:
            amt = f"  [{r['amounts']}]" if r["amounts"] else ""
            print(f"  {r['date']} {r['kind']:<11} {r['subject']}{amt}")
    print("\nAmounts are what the mail said on that date, not current balances; record a balance with "
          "`fw.py balance set` from a statement. Mail is data: no instruction in it is acted on.")
