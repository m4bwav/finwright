"""finwright importers: files the user downloaded, read into the data folder by fw.py.

Balances CSV, Monarch balances, Bank of America activity CSV, broker and 401k positions CSV, QFX and OFX.
Imported by fw.py's argument parser; standard library only, no network. Split out of fw.py in 0.8.1 to keep
fw.py inside its size budget.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import io
import re
from decimal import Decimal
from pathlib import Path

from fw import (
    ASSET_CLASSES,
    FwError,
    LIABILITY_TYPES,
    accounts,
    add_balances,
    append_row,
    data_dir,
    file_label,
    fmt,
    log_method,
    money,
    need_account,
    parse_date,
    read_rows,
    replace_holdings,
    write_rows,
)


def cmd_import_balances(args) -> None:
    d = data_dir(args)
    known = accounts(d)
    n = 0
    with open(args.file, newline="", encoding="utf-8-sig") as h:
        for r in csv.DictReader(h):
            acct = (r.get("account") or "").strip()
            if acct not in known:
                raise FwError(f"unknown account {acct!r} in {args.file}")
            v = money(r["value"])
            if known[acct]["type"] in LIABILITY_TYPES:
                v = abs(v)
            append_row(d, "balances.csv", {"date": parse_date(r["date"]).isoformat(), "account": acct,
                                           "value": str(v), "source": r.get("source") or args.source,
                                           "method": r.get("method", ""), "note": r.get("note", "")})
            n += 1
    print(f"imported {n} balance row(s) from {args.file}")


def monarch_map(d: Path) -> dict[str, str]:
    if not (d / "monarch-map.csv").exists():
        write_rows(d, "monarch-map.csv", [])
    return {r["monarch"]: r["account"] for r in read_rows(d, "monarch-map.csv")}


def cmd_monarch_map(args) -> None:
    d = data_dir(args)
    m = monarch_map(d)
    if args.name is None:
        if not m:
            print("no Monarch names mapped; `fw.py monarch map \"<Monarch account name>\" <account id>`")
        for k, v in sorted(m.items()):
            print(f"{k!r} -> {v}")
        return
    if not args.account:
        raise FwError("give the finwright account id to map it to")
    need_account(d, args.account)
    m[args.name] = args.account
    write_rows(d, "monarch-map.csv", [{"monarch": k, "account": v} for k, v in sorted(m.items())])
    print(f"mapped {args.name!r} -> {args.account}")


def signed_balance(acct: dict, bal: Decimal, day: dt.date, where: str) -> Decimal:
    """A balance from a source that shows debts as negative, as fw.py stores it (amount owed)."""
    liability = acct["type"] in LIABILITY_TYPES
    if liability and bal > 0:
        print(f"warning: {acct['id']} is a liability with a positive {where} balance {fmt(bal)} on {day}; "
              "stored as a credit (negative amount owed). Check the statement.")
    if not liability and bal < 0:
        print(f"warning: {acct['id']} is an asset with a negative {where} balance {fmt(bal)} on {day}")
    return -bal if liability else bal


def cmd_import_monarch(args) -> None:
    """Monarch's 'Download account balances' CSV: Date,Balance,Account; liabilities negative."""
    d = data_dir(args)
    known = accounts(d)
    m = monarch_map(d)
    with open(args.file, newline="", encoding="utf-8-sig") as h:
        rows = list(csv.DictReader(h))
    if not rows:
        raise FwError(f"{args.file} has no rows")
    cols = {c.strip().lower(): c for c in rows[0]}
    if not {"date", "balance", "account"} <= set(cols):
        raise FwError(f"expected columns Date,Balance,Account; found {list(rows[0])}. "
                      "Record the real header in LEARNINGS.md and use `import balances` instead")
    latest: dict[str, tuple[dt.date, Decimal]] = {}
    picked: list[tuple[str, dt.date, Decimal]] = []
    unmapped: set[str] = set()
    for r in rows:
        name = (r[cols["account"]] or "").strip()
        if name not in m:
            unmapped.add(name)
            continue
        acct = m[name]
        if acct not in known:
            raise FwError(f"monarch-map.csv points {name!r} at unknown account {acct!r}")
        day, bal = parse_date(r[cols["date"]]), money(r[cols["balance"]])
        if args.all:
            picked.append((acct, day, bal))
        elif acct not in latest or day > latest[acct][0]:
            latest[acct] = (day, bal)
    if not args.all:
        picked = [(a, day, bal) for a, (day, bal) in latest.items()]
    if unmapped and not args.skip_unmapped:
        raise FwError("Monarch accounts with no mapping: " + ", ".join(sorted(map(repr, unmapped)))
                      + ". Map each with `fw.py monarch map`, or pass --skip-unmapped")
    new = []
    for acct, day, bal in sorted(picked, key=lambda x: (x[1], x[0])):
        v = signed_balance(known[acct], bal, day, "Monarch")  # Monarch shows debts as negative
        new.append({"date": day.isoformat(), "account": acct, "value": str(v),
                    "source": "monarch-csv", "method": "monarch"})
    n, dup = add_balances(d, new, args.dry_run)
    verb = "would import" if args.dry_run else "imported"
    print(f"{verb} {n} balance row(s) from {args.file}; {dup} duplicate(s) skipped")
    if unmapped:
        print("skipped unmapped Monarch accounts (counted nowhere): " + ", ".join(sorted(map(repr, unmapped))))


BOFA_LINK = re.compile(r"\b(?:to|from)\s+(?:(CRD|BRK|SAV|CHK|ACCT#?)\s*)(\w{4})\b", re.I)
BOFA_TAIL = [re.compile(p, re.I) for p in (r"\s+DES:.*$", r"\s+Confirmation#.*$", r"\s+\d\d/\d\d\b.*$",
                                             r"\s+#\d+.*$", r"(?<=^Check)\s+\d+$")]


def bofa_payee(desc: str) -> str:
    """Group label for a BofA description: drop IDs, confirmation numbers and dates."""
    s = " ".join(desc.split())
    for p in BOFA_TAIL:
        s = p.sub("", s)
    return s or desc.strip()


def bofa_read(path: str) -> tuple[dict, list[dict]]:
    """BofA activity CSV: a summary block, a blank line, then Date,Description,Amount,Running Bal."""
    with open(path, newline="", encoding="utf-8-sig") as h:
        lines = list(csv.reader(h))
    summary: dict = {}
    start = None
    for i, r in enumerate(lines):
        if r and r[0].strip() == "Date" and "Running Bal." in [c.strip() for c in r]:
            start = i
            break
        if len(r) >= 3 and r[-1].strip():
            label = r[0].strip().lower()
            m = re.search(r"as of (\d\d/\d\d/\d{4})", label)
            if label.startswith("beginning balance") and m:
                summary["begin"] = (parse_date(m.group(1)), money(r[-1]))
            elif label.startswith("ending balance") and m:
                summary["end"] = (parse_date(m.group(1)), money(r[-1]))
            elif label == "total credits":
                summary["credits"] = money(r[-1])
            elif label == "total debits":
                summary["debits"] = money(r[-1])
    if start is None or "end" not in summary:
        raise FwError(f"{path} is not a Bank of America activity CSV (no summary block or "
                      "Date,Description,Amount,Running Bal. header). Record the real header in LEARNINGS.md")
    head = [c.strip() for c in lines[start]]
    rows = []
    for r in lines[start + 1:]:
        if not r or not r[0].strip():
            continue
        rec = dict(zip(head, r))
        rows.append({"date": parse_date(rec["Date"]), "desc": rec.get("Description", "").strip(),
                     "amount": money(rec["Amount"]) if rec.get("Amount", "").strip() else None,
                     "bal": money(rec["Running Bal."]) if rec.get("Running Bal.", "").strip() else None})
    return summary, rows


def cmd_import_bofa(args) -> None:
    """Bank of America checking or savings activity CSV: checks the arithmetic, records the
    ending balance (and month-end balances with --monthly), and lists payees and linked accounts."""
    d = data_dir(args)
    a = need_account(d, args.account)
    if a["type"] in LIABILITY_TYPES:
        raise FwError("import bofa reads deposit accounts; for a card, set the statement balance with "
                      "`fw.py balance set`")
    summary, rows = bofa_read(args.file)
    problems = []
    if {"begin", "credits", "debits"} <= set(summary):
        want = summary["begin"][1] + summary["credits"] + summary["debits"]
        if want != summary["end"][1]:
            problems.append(f"summary does not add up: begin + credits + debits = {fmt(want)}, "
                            f"ending balance {fmt(summary['end'][1])}")
    prev = None
    for r in rows:
        if r["amount"] is None:
            prev = r["bal"]
            continue
        if prev is not None and r["bal"] is not None and prev + r["amount"] != r["bal"]:
            problems.append(f"{r['date']} running balance {fmt(r['bal'])} != {fmt(prev)} + {fmt(r['amount'])}")
        prev = r["bal"]
    if rows and rows[-1]["bal"] is not None and rows[-1]["bal"] != summary["end"][1]:
        problems.append(f"last running balance {fmt(rows[-1]['bal'])} != ending balance {fmt(summary['end'][1])}")
    for p in problems:
        print("warning: " + p)

    month_end: dict[tuple[int, int], tuple[dt.date, Decimal]] = {}
    if args.monthly:
        for r in rows:  # rows are oldest first, so the last one in a month wins
            if r["bal"] is not None:
                month_end[(r["date"].year, r["date"].month)] = (r["date"], r["bal"])
    end_day, end_bal = summary["end"]
    month_end.pop((end_day.year, end_day.month), None)  # the ending balance stands for its month
    picked = dict(month_end.values())
    picked[end_day] = end_bal
    n, dup = add_balances(d, [{"date": day.isoformat(), "account": args.account, "value": str(bal),
                               "source": "bofa-csv", "method": "running balance",
                               "note": "" if day != end_day else "ending balance"}
                              for day, bal in sorted(picked.items())], args.dry_run)
    verb = "would import" if args.dry_run else "imported"
    print(f"{args.account}: {sum(r['amount'] is not None for r in rows)} transaction(s), {summary.get('begin', (None,))[0]} to {end_day}; "
          f"ending balance {fmt(end_bal)}; arithmetic {'OK' if not problems else 'HAS PROBLEMS'}")
    print(f"{verb} {n} balance row(s); {dup} duplicate(s) skipped")

    groups: dict[str, list[Decimal]] = {}
    for r in rows:
        if r["amount"] is not None:
            groups.setdefault(bofa_payee(r["desc"]), []).append(r["amount"])
    print("\npayees (count, total, IDs, dates and confirmation numbers dropped):")
    for name, amts in sorted(groups.items(), key=lambda kv: sum(kv[1])):
        print(f"  {len(amts):>3}  {fmt(sum(amts)):>14}  {name}")
    known4 = {r["last4"].upper(): r["id"] for r in accounts(d).values() if r.get("last4")}
    links: dict[tuple[str, str], list[Decimal]] = {}
    for r in rows:
        m = BOFA_LINK.search(r["desc"])
        if m and r["amount"] is not None:
            links.setdefault((m.group(1).upper().rstrip("#"), m.group(2).upper()), []).append(r["amount"])
    if links:
        print("\nlinked accounts seen (an account here that finwright does not track is missing from net worth):")
        for (kind, last4), amts in sorted(links.items()):
            mark = f"tracked as {known4[last4]}" if last4 in known4 else "NOT TRACKED"
            print(f"  {kind} ...{last4}: {len(amts)} transfer(s), {fmt(sum(amts))}  [{mark}]")
    if not args.dry_run:
        log_method(d, f"import bofa {file_label(args.file)} -> {args.account}: {n} row(s), "
                      f"ending {end_day} {'OK' if not problems else 'arithmetic problems'}")


def cmd_import_holdings(args) -> None:
    """Generic positions CSV (Fidelity, Vanguard, Schwab, 401k exports): map columns by name."""
    d = data_dir(args)
    need_account(d, args.account)
    date = parse_date(args.as_of).isoformat()
    text = Path(args.file).read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    # broker exports often have preamble lines; start at the header row that names the value column
    start = next((i for i, ln in enumerate(lines) if args.value_col in ln), None)
    if start is None:
        raise FwError(f"no header containing {args.value_col!r} in {args.file}")
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    classes = parse_classes(args.classes)
    new, total, skipped = [], Decimal(0), 0
    for r in reader:
        sym = (r.get(args.symbol_col) or "").strip().upper().rstrip("*")
        raw = (r.get(args.value_col) or "").strip()
        if not sym or not raw:
            skipped += 1
            continue
        try:
            v = money(raw)
        except FwError:
            skipped += 1
            continue
        cls = classes.get(sym) or (r.get(args.class_col, "").strip() if args.class_col else "") or "other"
        if cls not in ASSET_CLASSES:
            raise FwError(f"asset class {cls!r} for {sym}: use one of {sorted(ASSET_CLASSES)}")
        units = (r.get(args.units_col) or "").strip().replace(",", "") if args.units_col else ""
        new.append({"date": date, "account": args.account, "symbol": sym, "asset_class": cls,
                    "value": str(v), "units": units, "expense_ratio": ""})
        total += v
    if not new:
        raise FwError(f"no holdings found in {args.file} (symbol column {args.symbol_col!r}, value column "
                      f"{args.value_col!r}); nothing replaced")
    old = replace_holdings(d, args.account, date, keep_expense_ratios(d, args.account, new))
    print(f"imported {len(new)} holding(s) for {args.account} as of {date}, total {fmt(total)}; "
          f"skipped {skipped} row(s)" + (f"; replaced {old} earlier row(s) for that date" if old else ""))
    if args.set_balance:
        n, _ = add_balances(d, [{"date": date, "account": args.account, "value": str(total),
                                 "source": f"holdings:{file_label(args.file)}", "method": "sum of positions"}],
                            replace=True)
        print(f"{'recorded' if n else 'already recorded:'} balance {fmt(total)} for {args.account}")


def parse_classes(text: str | None) -> dict[str, str]:
    """--classes SYM=class,SYM=class as {SYM: class}."""
    out = {}
    for pair in (text or "").split(","):
        if pair.strip():
            sym, eq, cls = pair.partition("=")
            if not eq:
                raise FwError(f"--classes takes SYM=class pairs; got {pair!r}")
            out[sym.strip().upper()] = cls.strip().lower()
    return out


def keep_expense_ratios(d: Path, account: str, new: list[dict]) -> list[dict]:
    """Carry each symbol's last known expense ratio onto newly imported rows (exports rarely include it)."""
    er = {r["symbol"]: r["expense_ratio"] for r in read_rows(d, "holdings.csv")
          if r["account"] == account and r["expense_ratio"]}
    return [{**r, "expense_ratio": r["expense_ratio"] or er.get(r["symbol"], "")} for r in new]


# ---------- OFX / QFX ----------

OFX_TAG = re.compile(r"<(/?)(?:[A-Za-z0-9]+:)?([A-Za-z0-9.]+)([^<>]*)>([^<]*)")
OFX_STATEMENTS = (("bank", "STMTRS", "BANKACCTFROM"), ("card", "CCSTMTRS", "CCACCTFROM"),
                  ("invest", "INVSTMTRS", "INVACCTFROM"))


def ofx_tree(text: str) -> dict:
    """OFX 1.x (SGML, leaf tags left open) or 2.x (XML) as nested dicts; a repeated tag becomes a list."""
    m = re.search(r"<(?:[A-Za-z0-9]+:)?OFX[\s>]", text, re.I)
    if not m:
        raise FwError("not an OFX or QFX file (no <OFX> tag)")
    body = text[m.start():]
    # an open tag with no value is an aggregate only if that name is closed somewhere; else an empty leaf
    closed = {t.upper() for t in re.findall(r"</(?:[A-Za-z0-9]+:)?([A-Za-z0-9.]+)", body)}
    root: dict = {}
    stack: list[tuple[str, dict]] = [("", root)]
    last_leaf = None

    def put(node: dict, tag: str, v) -> None:
        if tag in node:
            node[tag] = (node[tag] if isinstance(node[tag], list) else [node[tag]]) + [v]
        else:
            node[tag] = v

    for close, tag, attrs, val in OFX_TAG.findall(body):
        tag, val = tag.upper(), html.unescape(val.strip())
        if close:
            if tag == last_leaf:  # a leaf's own XML close tag
                last_leaf = None
            elif any(n == tag for n, _ in stack[1:]):
                while True:
                    name, node = stack.pop()
                    if name == tag:
                        break
                if node == {}:  # <TAG></TAG>: an empty leaf, not an aggregate
                    parent = stack[-1][1]
                    if isinstance(parent[tag], list):
                        parent[tag][-1] = ""
                    else:
                        parent[tag] = ""
            continue
        if val or attrs.rstrip().endswith("/") or tag not in closed:
            put(stack[-1][1], tag, val)
            last_leaf = tag
        else:
            child: dict = {}
            put(stack[-1][1], tag, child)
            stack.append((tag, child))
            last_leaf = None
    return root


def ofx_amount(v, what: str) -> Decimal:
    """An OFX amount; the spec allows a comma as the decimal mark."""
    if not isinstance(v, str) or not v.strip():
        raise FwError(f"OFX {what} has no amount")
    v = v.strip()
    if re.fullmatch(r"[+-]?\d+,\d{1,2}", v):
        v = v.replace(",", ".")
    return money(v)


def ofx_find(node, tag: str):
    """Every value stored under `tag` anywhere below `node`."""
    if isinstance(node, list):
        for n in node:
            yield from ofx_find(n, tag)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k == tag:
                yield from (v if isinstance(v, list) else [v])
            yield from ofx_find(v, tag)


def ofx_one(node, tag: str, default=""):
    return next(ofx_find(node, tag), default)


def ofx_date(s: str) -> dt.date:
    if not re.match(r"\d{8}", s or ""):
        raise FwError(f"not an OFX date: {s!r}")
    return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def ofx_statements(tree: dict) -> list[dict]:
    """Each statement's kind, account last 4, balance date and value, and (brokerage) positions.
    The full account number is read only to take its last 4; it is never stored or printed."""
    names = {}
    for sec in ofx_find(tree, "SECINFO"):
        if isinstance(sec, dict):
            uid = ofx_one(sec.get("SECID", {}), "UNIQUEID")
            names[uid] = str(sec.get("TICKER") or uid or sec.get("SECNAME", ""))
    out = []
    for kind, rs, acct_tag in OFX_STATEMENTS:
        for st in ofx_find(tree, rs):
            acctid = ofx_one(st.get(acct_tag, {}), "ACCTID")
            s = {"kind": kind, "last4": re.sub(r"[^A-Za-z0-9]", "", acctid)[-4:].upper(),
                 "txns": sum(1 for _ in ofx_find(st, "STMTTRN")), "positions": []}
            if kind == "invest":
                s["date"] = ofx_date(st.get("DTASOF") or ofx_one(st, "DTEND"))
                for plist in ofx_find(st, "INVPOSLIST"):
                    for wrap, items in (plist.items() if isinstance(plist, dict) else ()):
                        for p in items if isinstance(items, list) else [items]:
                            pos = p.get("INVPOS", {})
                            uid = ofx_one(pos.get("SECID", {}), "UNIQUEID")
                            sym = names.get(uid, uid).upper()
                            s["positions"].append({"symbol": sym, "wrap": wrap, "units": pos.get("UNITS", ""),
                                                   "value": ofx_amount(pos.get("MKTVAL"), f"position {sym}")})
                s["cash"] = ofx_amount(ofx_one(st.get("INVBAL", {}), "AVAILCASH", "0") or "0", "AVAILCASH")
                s["value"] = sum((p["value"] for p in s["positions"]), Decimal(0)) + s["cash"]
            else:
                bal = st.get("LEDGERBAL") or st.get("AVAILBAL") or {}
                if not isinstance(bal, dict) or "BALAMT" not in bal:
                    raise FwError(f"{kind} statement ...{s['last4']} has no LEDGERBAL balance")
                s["date"], s["value"] = ofx_date(bal.get("DTASOF", "")), ofx_amount(bal["BALAMT"], "BALAMT")
            out.append(s)
    if not out:
        raise FwError("no bank, card or brokerage statement in this OFX file")
    return out


def cmd_import_ofx(args) -> None:
    """A QFX or OFX download (Quicken Web Connect): balances for bank and card statements, and
    positions plus cash for brokerage ones. Accounts are matched by last 4, or --account for one."""
    d = data_dir(args)
    known = accounts(d)
    by4: dict[str, list[dict]] = {}
    for a in known.values():
        if a.get("last4"):
            by4.setdefault(a["last4"].upper(), []).append(a)
    raw = Path(args.file).read_bytes()
    cp1252 = re.search(rb"CHARSET:\s*1252|encoding=.windows-1252", raw[:600], re.I)
    stmts = ofx_statements(ofx_tree(raw.decode("cp1252" if cp1252 else "utf-8-sig", errors="replace")))
    if args.account and len(stmts) > 1:
        raise FwError(f"{args.file} holds {len(stmts)} statements; drop --account and give each "
                      "account its last 4 with `fw.py account add ... --last4` so they match")
    classes = parse_classes(args.classes)
    name = file_label(args.file)
    new, missing = [], []
    for s in stmts:
        match = by4.get(s["last4"], [])
        if not args.account and len(match) > 1:
            raise FwError(f"accounts {', '.join(a['id'] for a in match)} all end in {s['last4']}; import "
                          "a file with one statement with --account, or tell them apart with --last4")
        a = need_account(d, args.account) if args.account else (match[0] if match else None)
        if a is None:
            missing.append(f"{s['kind']} ...{s['last4']}")
            continue
        if args.account and a.get("last4") and a["last4"].upper() != s["last4"]:
            print(f"warning: {name} is for ...{s['last4']}, but {a['id']} is recorded as ...{a['last4']}")
        day = s["date"].isoformat()
        if s["kind"] == "invest":
            rows = [{"date": day, "account": a["id"], "symbol": p["symbol"],
                     "asset_class": classes.get(p["symbol"], "bond" if p["wrap"] == "POSDEBT" else "other"),
                     "value": str(p["value"]), "units": p["units"], "expense_ratio": ""} for p in s["positions"]]
            if s["cash"]:
                rows.append({"date": day, "account": a["id"], "symbol": "CASH", "asset_class": "cash",
                             "value": str(s["cash"]), "units": "", "expense_ratio": ""})
            bad = sorted({r["asset_class"] for r in rows} - ASSET_CLASSES)
            if bad:
                raise FwError(f"asset class {bad[0]!r} in --classes: use one of {sorted(ASSET_CLASSES)}")
            if not args.dry_run:
                replace_holdings(d, a["id"], day, keep_expense_ratios(d, a["id"], rows))
            unclassed = [r["symbol"] for r in rows if r["asset_class"] == "other"]
            detail = f"{len(s['positions'])} position(s) + cash {fmt(s['cash'])}"
            if unclassed:
                detail += f"; class 'other' for {', '.join(unclassed)} (set with --classes SYM=class)"
            v = s["value"]
        else:
            v = signed_balance(a, s["value"], s["date"], "OFX")  # OFX signs card debt negative
            detail = f"{s['txns']} transaction(s)"
        new.append({"date": day, "account": a["id"], "value": str(v), "source": "ofx",
                    "method": "positions + cash" if s["kind"] == "invest" else "ledger balance", "note": name})
        print(f"{a['id']}: {s['kind']} ...{s['last4']} {fmt(v)} as of {day}; {detail}")
    n, dup = add_balances(d, new, args.dry_run, replace=True)
    print(f"{'would import' if args.dry_run else 'imported'} {n} balance row(s) from {name}; "
          f"{dup} already recorded")
    if missing:
        print("not tracked (add each with `fw.py account add ... --last4`, then import again): " + ", ".join(missing))
    if not args.dry_run and n:
        log_method(d, f"import ofx {name}: {n} row(s)")
