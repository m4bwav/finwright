#!/usr/bin/env python3
"""finwright: personal net worth records and checks, kept locally, math in Decimal.

Standard library only (Python 3.10+). Read-only toward every financial institution:
it never logs in, never stores a password, never moves money. The one network call
is `bond refresh`, which reads public Treasury savings bond values (no key, no login).

Data lives in a folder outside any git repository: --data DIR, else $FINWRIGHT_DATA,
else ~/finwright-data. Run `fw.py init` first.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, getcontext
from pathlib import Path

VERSION = "0.9.2"
getcontext().prec = 28
CENT = Decimal("0.01")
DISCLAIMER = ("Use at your own risk: guidance from your own records and published research, not a licensed "
              "adviser's advice. You decide, and losses, including total ones, are yours.")
RATES_FILE = Path(__file__).resolve().parent.parent / "data" / "rates.json"
SB_API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/sb_value"

ASSET_TYPES = {"cash", "taxable", "tax_deferred", "roth", "hsa", "savings_bond",
               "real_estate", "vehicle", "other_asset", "unvested"}
LIABILITY_TYPES = {"mortgage", "loan", "credit_card", "other_liability"}
LIQUID = {"cash", "taxable", "savings_bond"}
INVESTABLE = {"cash", "taxable", "tax_deferred", "roth", "hsa", "savings_bond"}
STALE_DAYS = {"cash": 45, "credit_card": 45, "taxable": 45, "loan": 100, "mortgage": 100,
              "tax_deferred": 100, "roth": 100, "hsa": 100, "unvested": 100,
              "savings_bond": 45, "real_estate": 400, "vehicle": 400,
              "other_asset": 400, "other_liability": 100}
ASSET_CLASSES = {"us_stock", "intl_stock", "bond", "cash", "real_estate", "other"}

FILES = {
    "accounts.csv": ["id", "name", "type", "institution", "last4", "notes"],
    "balances.csv": ["date", "account", "value", "source", "method", "note"],
    "holdings.csv": ["date", "account", "symbol", "asset_class", "value", "units", "expense_ratio"],
    "flows.csv": ["date", "account", "amount", "kind", "note"],
    "bonds.csv": ["id", "series", "issue_month", "denomination", "note"],
    "hunt.csv": ["id", "employer", "years", "plan", "ein", "recordkeeper", "status", "account",
                 "next", "updated", "notes"],
    "monarch-map.csv": ["monarch", "account"],
}
DEFAULT_CONFIG = {
    "after_tax_rate": "0.22",
    "home_selling_cost_pct": "0.06",
    "targets": {},
    "stale_days": {},
    "birth_year": None,
}


class FwError(Exception):
    pass


# ---------- helpers ----------

def money(text: str | int | float | Decimal) -> Decimal:
    """Parse '$1,234.50', '(12.00)', '-5', '1 234,00' is not supported (US formats only)."""
    if isinstance(text, Decimal):
        return text
    s = str(text).strip()
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(",", "").replace(" ", "")
    if s.endswith("-"):
        neg, s = True, s[:-1]
    if s in ("", "--", "n/a", "N/A"):
        raise FwError(f"not a number: {text!r}")
    try:
        v = Decimal(s)
    except InvalidOperation:
        raise FwError(f"not a number: {text!r}") from None
    return -v if neg else v


def fmt(v: Decimal) -> str:
    q = v.quantize(CENT, rounding=ROUND_HALF_UP)
    return f"-${-q:,.2f}" if q < 0 else f"${q:,.2f}"


def pct(v: Decimal) -> str:
    return f"{(v * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%"


def parse_date(s: str) -> dt.date:
    s = s.strip()
    for f in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    raise FwError(f"not a date (use YYYY-MM-DD): {s!r}")


def today() -> dt.date:
    fixed = os.environ.get("FINWRIGHT_TODAY")
    return parse_date(fixed) if fixed else dt.date.today()


def data_dir(args) -> Path:
    d = args.data or os.environ.get("FINWRIGHT_DATA") or str(Path.home() / "finwright-data")
    return Path(d).expanduser().resolve()


def git_root(p: Path) -> Path | None:
    for q in [p, *p.parents]:
        if (q / ".git").exists():
            return q
    return None


def read_rows(d: Path, name: str) -> list[dict]:
    f = d / name
    if not f.exists():
        raise FwError(f"{f} is missing; run `fw.py init` first")
    with f.open(newline="", encoding="utf-8") as h:
        return list(csv.DictReader(h))


def append_row(d: Path, name: str, row: dict) -> None:
    with (d / name).open("a", newline="", encoding="utf-8") as h:
        csv.DictWriter(h, FILES[name], lineterminator="\n").writerow(row)


def write_rows(d: Path, name: str, rows: list[dict]) -> None:
    with (d / name).open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, FILES[name], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def load_config(d: Path) -> dict:
    f = d / "config.json"
    if not f.exists():
        raise FwError(f"{f} is missing; run `fw.py init` first")
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(json.loads(f.read_text(encoding="utf-8")))
    return cfg


def load_rates() -> dict:
    return json.loads(RATES_FILE.read_text(encoding="utf-8"))


def accounts(d: Path) -> dict[str, dict]:
    return {r["id"]: r for r in read_rows(d, "accounts.csv")}


def need_account(d: Path, acct: str) -> dict:
    a = accounts(d).get(acct)
    if not a:
        raise FwError(f"unknown account {acct!r}; add it with `fw.py account add`")
    return a


def log_method(d: Path, text: str) -> None:
    with (d / "methods.log").open("a", encoding="utf-8", newline="\n") as h:
        h.write(f"{today().isoformat()} {text}\n")


def add_balances(d: Path, rows: list[dict], dry_run: bool = False, replace: bool = False) -> tuple[int, int]:
    """Record balance rows, skipping any (date, account, source) already recorded; with replace, a new
    value for the same key overwrites the old row (a re-downloaded file). Returns (written, unchanged)."""
    old = read_rows(d, "balances.csv")
    index = {(r["date"], r["account"], r["source"]): i for i, r in enumerate(old)}
    seen: set = set()
    n = dup = 0
    for row in rows:
        row = {"method": "", "note": "", **row}
        key = (row["date"], row["account"], row["source"])
        if key in seen:
            raise FwError(f"two balances for {row['account']} on {row['date']} in one import; nothing recorded")
        seen.add(key)
        i = index.get(key)
        if i is not None and (not replace or old[i]["value"] == row["value"]):
            dup += 1
            continue
        if i is None:
            index[key] = len(old)
            old.append(row)
        else:
            old[i] = row
        n += 1
    if n and not dry_run:
        write_rows(d, "balances.csv", old)
    return n, dup


def file_label(path: str) -> str:
    """A download's file name for notes and logs, with long digit runs (account numbers) cut to the last 4."""
    return re.sub(r"\d{5,}", lambda m: "****" + m.group()[-4:], Path(path).name)


def replace_holdings(d: Path, account: str, date: str, new: list[dict], symbol: str | None = None) -> int:
    """Swap in one account's holdings for a date (or one symbol's), so a re-import never doubles them."""
    rows = read_rows(d, "holdings.csv")
    keep = [r for r in rows if not (r["account"] == account and r["date"] == date
                                    and (symbol is None or r["symbol"] == symbol))]
    write_rows(d, "holdings.csv", keep + new)
    return len(rows) - len(keep)


# ---------- init / check ----------

def cmd_init(args) -> None:
    d = data_dir(args)
    root = git_root(d)
    if root and not args.allow_git:
        raise FwError(f"{d} is inside the git repository {root}; pick a folder outside any repo "
                      "(or pass --allow-git if that repo is private and the files are encrypted)")
    d.mkdir(parents=True, exist_ok=True)
    for sub in ("inbox", "snapshots", "cache"):
        (d / sub).mkdir(exist_ok=True)
    for name, cols in FILES.items():
        if not (d / name).exists():
            write_rows(d, name, [])
    if not (d / "config.json").exists():
        (d / "config.json").write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("# finwright data: never commit this folder unencrypted\n*\n", encoding="utf-8")
    print(f"finwright data folder ready: {d}")
    print("Next: `fw.py account add`, then `fw.py balance set` for each account, then `fw.py networth`.")


def cmd_check(args) -> None:
    d = data_dir(args)
    problems, notes = [], []
    root = git_root(d)
    if root:
        problems.append(f"data folder {d} is inside git repository {root}")
    if not d.exists():
        problems.append(f"data folder {d} does not exist; run `fw.py init`")
    rates = load_rates()
    t = today()
    for key, nd in rates.get("next_change", {}).items():
        if t >= parse_date(nd["date"]):
            problems.append(f"rates.json {key} was due to change on {nd['date']} ({nd['what']}); "
                            "refresh the skill before trusting it")
    if d.exists():
        notes.extend(stale_warnings(d, load_config(d), t))
        if (d / "inbox").exists():
            waiting = [p.name for p in (d / "inbox").iterdir() if p.is_file()]
            if waiting:
                notes.append(f"{len(waiting)} file(s) waiting in inbox/: {', '.join(sorted(waiting)[:8])}")
    for p in problems:
        print(f"PROBLEM {p}")
    for n in notes:
        print(f"note    {n}")
    if not problems and not notes:
        print("ok: data folder outside git, rates current, no stale balances")
    if problems:
        sys.exit(1)


# ---------- accounts / balances / holdings / flows ----------

def cmd_account_add(args) -> None:
    d = data_dir(args)
    t = args.type
    if t not in ASSET_TYPES | LIABILITY_TYPES:
        raise FwError(f"type must be one of {sorted(ASSET_TYPES | LIABILITY_TYPES)}")
    if args.last4 and not re.fullmatch(r"[A-Za-z0-9]{4}", args.last4):
        raise FwError("--last4 takes exactly four letters or digits (as the bank shows them, e.g. 9Z99); never store a full account number")
    rows = read_rows(d, "accounts.csv")
    if any(r["id"] == args.id for r in rows):
        raise FwError(f"account {args.id!r} already exists")
    append_row(d, "accounts.csv", {"id": args.id, "name": args.name or args.id, "type": t,
                                   "institution": args.institution or "", "last4": args.last4 or "",
                                   "notes": args.notes or ""})
    print(f"added {args.id} ({t})")


def cmd_account_update(args) -> None:
    d = data_dir(args)
    rows = read_rows(d, "accounts.csv")
    row = next((r for r in rows if r["id"] == args.id), None)
    if row is None:
        raise FwError(f"no account {args.id!r}; `fw.py account list` shows them")
    if args.type and args.type not in ASSET_TYPES | LIABILITY_TYPES:
        raise FwError(f"type must be one of {sorted(ASSET_TYPES | LIABILITY_TYPES)}")
    if args.last4 and not re.fullmatch(r"[A-Za-z0-9]{4}", args.last4):
        raise FwError("--last4 takes exactly four letters or digits; never store a full account number")
    for field in ("name", "type", "institution", "last4"):
        if getattr(args, field):
            row[field] = getattr(args, field)
    if args.note:
        entry = f"{today().isoformat()}: {args.note}"
        row["notes"] = f"{row['notes']} | {entry}" if row["notes"] else entry
    write_rows(d, "accounts.csv", rows)
    print(f"updated {args.id}: {row['institution']}  {row['name']} ({row['type']})")


def cmd_account_list(args) -> None:
    d = data_dir(args)
    for a in accounts(d).values():
        tail = f" ...{a['last4']}" if a["last4"] else ""
        print(f"{a['id']:<20} {a['type']:<16} {a['institution']}{tail}  {a['name']}")


def cmd_balance_set(args) -> None:
    d = data_dir(args)
    a = need_account(d, args.account)
    v = money(args.value)
    if a["type"] in LIABILITY_TYPES:
        v = abs(v)  # stored as amount owed
    date = parse_date(args.as_of).isoformat() if args.as_of else today().isoformat()
    append_row(d, "balances.csv", {"date": date, "account": args.account, "value": str(v),
                                   "source": args.source, "method": args.method or "",
                                   "note": args.note or ""})
    print(f"{args.account} = {fmt(v)} as of {date} ({args.source})")


def cmd_holding_set(args) -> None:
    d = data_dir(args)
    need_account(d, args.account)
    if args.asset_class not in ASSET_CLASSES:
        raise FwError(f"asset class must be one of {sorted(ASSET_CLASSES)}")
    er = str(money(args.expense_ratio)) if args.expense_ratio else ""
    date = parse_date(args.as_of).isoformat() if args.as_of else today().isoformat()
    sym = args.symbol.upper()
    replace_holdings(d, args.account, date, [{"date": date, "account": args.account, "symbol": sym,
                                              "asset_class": args.asset_class, "value": str(money(args.value)),
                                              "units": args.units or "", "expense_ratio": er}], sym)
    print(f"{args.account} {args.symbol.upper()} = {fmt(money(args.value))} ({args.asset_class}) as of {date}")


def cmd_flow_add(args) -> None:
    d = data_dir(args)
    need_account(d, args.account)
    append_row(d, "flows.csv", {"date": parse_date(args.date).isoformat(), "account": args.account,
                                "amount": str(money(args.amount)), "kind": args.kind, "note": args.note or ""})
    print(f"flow {args.account} {fmt(money(args.amount))} on {args.date} ({args.kind})")


def cmd_config_set(args) -> None:
    d = data_dir(args)
    cfg = load_config(d)
    key, val = args.key, args.value
    if key == "target":
        cls, _, share = val.partition("=")
        if cls not in ASSET_CLASSES:
            raise FwError(f"asset class must be one of {sorted(ASSET_CLASSES)}")
        cfg["targets"][cls] = str(money(share))
        shown = f"target {cls}={share}"
    elif key in ("after_tax_rate", "home_selling_cost_pct"):
        cfg[key] = str(money(val))
        shown = f"{key}={val}"
    elif key == "birth_year":
        cfg[key] = int(val)
        shown = f"birth_year={val}"
    else:
        raise FwError("key must be after_tax_rate, home_selling_cost_pct, birth_year or target")
    (d / "config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    log_method(d, f"config {shown}")
    print(f"set {shown} (logged in methods.log; history before today used the old method)")


# ---------- savings bonds ----------

def sb_cache(d: Path, series: str, period: str) -> Path:
    return d / "cache" / f"sb_value-{series}-{period}.json"


def cmd_bond_add(args) -> None:
    d = data_dir(args)
    series = args.series.upper()
    if series not in ("I", "EE", "E"):
        raise FwError("series must be I, EE or E")
    if not re.fullmatch(r"\d{4}-\d{2}", args.issue):
        raise FwError("--issue is the issue month, YYYY-MM")
    denom = money(args.denomination)
    if denom <= 0:
        raise FwError("denomination must be positive (face value for EE/E, purchase amount for I)")
    rows = read_rows(d, "bonds.csv")
    bid = args.id or f"{series}-{args.issue}-{len(rows) + 1}"
    append_row(d, "bonds.csv", {"id": bid, "series": series, "issue_month": args.issue,
                                "denomination": str(denom), "note": args.note or ""})
    print(f"added bond {bid}: series {series}, issued {args.issue}, {fmt(denom)}")


def fetch_sb_period(series: str, period: str) -> list[dict]:
    q = urllib.parse.urlencode({"filter": f"series_cd:eq:{series},redemp_period:eq:{period}",
                                "page[size]": "200"})
    req = urllib.request.Request(f"{SB_API}?{q}", headers={"User-Agent": f"finwright/{VERSION}"})
    with urllib.request.urlopen(req, timeout=30) as h:
        return json.load(h)["data"]


def cmd_bond_refresh(args) -> None:
    d = data_dir(args)
    period = args.month or today().strftime("%Y-%m")
    series_needed = sorted({r["series"] for r in read_rows(d, "bonds.csv")}) or ["I", "EE"]
    for s in series_needed:
        rows = fetch_sb_period(s, period)
        if not rows:
            print(f"Treasury has not published series {s} values for {period} yet "
                  "(files cover through the month listed in the latest semiannual release)")
            continue
        sb_cache(d, s, period).write_text(json.dumps(rows), encoding="utf-8")
        print(f"cached series {s} values for {period} ({len(rows)} issue years)")


MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def bond_value(d: Path, bond: dict, period: str) -> tuple[Decimal | None, str]:
    f = sb_cache(d, bond["series"], period)
    if not f.exists():
        return None, f"no cached values for {period}; run `fw.py bond refresh --month {period}`"
    year, month = bond["issue_month"].split("-")
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r["issue_year"] == year:
            raw = r[f"issue_{MONTHS[int(month) - 1]}_amt"]
            if raw in ("null", "", None):
                return None, "Treasury publishes no value for that issue month in this period"
            per25 = Decimal(raw)
            if per25 == 0:
                return Decimal(0), "inside the 12-month minimum hold (value 0 until then)"
            # EE/E values are per $25 face; I values are per $25 purchase
            units = money(bond["denomination"]) / Decimal(25)
            return (per25 * units).quantize(CENT, rounding=ROUND_HALF_UP), "Treasury value file"
    return None, f"issue year {year} not in the series {bond['series']} file"


def bonds_total(d: Path, period: str) -> tuple[Decimal, list[str]]:
    total, notes = Decimal(0), []
    for b in read_rows(d, "bonds.csv"):
        v, why = bond_value(d, b, period)
        if v is None:
            notes.append(f"bond {b['id']}: {why}")
        else:
            total += v
            if v == 0:
                notes.append(f"bond {b['id']}: {why}")
    return total, notes


def cmd_bond_value(args) -> None:
    d = data_dir(args)
    period = args.month or today().strftime("%Y-%m")
    total = Decimal(0)
    for b in read_rows(d, "bonds.csv"):
        v, why = bond_value(d, b, period)
        shown = fmt(v) if v is not None else "unknown"
        print(f"{b['id']:<20} {b['series']:<3} issued {b['issue_month']}  {fmt(money(b['denomination'])):>12}"
              f"  value {shown:>12}  ({why})")
        total += v or 0
    print(f"total savings bond value for {period}: {fmt(total)}")
    issue_months = [b["issue_month"] for b in read_rows(d, "bonds.csv") if b["series"] == "I"]
    young = [m for m in issue_months if months_between(m, period) < 60]
    if young:
        print("note: I bonds under 5 years old lose the last 3 months of interest if cashed; "
              "Treasury's values already subtract that")


def months_between(a: str, b: str) -> int:
    ay, am = map(int, a.split("-"))
    by, bm = map(int, b.split("-"))
    return (by - ay) * 12 + (bm - am)


# ---------- net worth ----------

def latest_balances(d: Path, as_of: dt.date) -> dict[str, dict]:
    out = {}
    for r in read_rows(d, "balances.csv"):
        if parse_date(r["date"]) <= as_of:
            prev = out.get(r["account"])
            if not prev or r["date"] >= prev["date"]:
                out[r["account"]] = r
    return out


def stale_warnings(d: Path, cfg: dict, as_of: dt.date) -> list[str]:
    limits = dict(STALE_DAYS)
    limits.update(cfg.get("stale_days") or {})
    acc = accounts(d)
    lat = latest_balances(d, as_of)
    out = []
    for aid, a in acc.items():
        if a["type"] == "savings_bond":
            continue
        b = lat.get(aid)
        if not b:
            out.append(f"{aid}: no balance recorded")
            continue
        age = (as_of - parse_date(b["date"])).days
        if age > limits.get(a["type"], 100):
            out.append(f"{aid}: balance is {age} days old (from {b['date']}, {b['source']})")
    return out


def compute_networth(d: Path, as_of: dt.date) -> dict:
    cfg = load_config(d)
    acc = accounts(d)
    lat = latest_balances(d, as_of)
    by_type: dict[str, Decimal] = {}
    lines = []
    bond_rows = read_rows(d, "bonds.csv")
    bond_notes: list[str] = []
    for aid, a in acc.items():
        # A savings_bond account's balance (a TreasuryDirect total) counts until bonds are listed
        # one by one with `bond add`; then the Treasury value files replace it.
        if a["type"] == "savings_bond" and bond_rows:
            if aid in lat:
                bond_notes.append(f"{aid}: balance ignored; bonds.csv values the bonds individually")
            continue
        b = lat.get(aid)
        if not b:
            continue
        v = Decimal(b["value"])
        by_type[a["type"]] = by_type.get(a["type"], Decimal(0)) + v
        lines.append({"account": aid, "type": a["type"], "value": str(v), "as_of": b["date"],
                      "source": b["source"]})
    period = as_of.strftime("%Y-%m")
    if bond_rows:
        bt, notes = bonds_total(d, period)
        bond_notes += notes
        by_type["savings_bond"] = by_type.get("savings_bond", Decimal(0)) + bt
        lines.append({"account": "savings bonds", "type": "savings_bond", "value": str(bt),
                      "as_of": period, "source": "Treasury value file"})
    assets = sum((v for t, v in by_type.items() if t in ASSET_TYPES - {"unvested"}), Decimal(0))
    liabilities = sum((v for t, v in by_type.items() if t in LIABILITY_TYPES), Decimal(0))
    total = assets - liabilities
    liquid = (sum((by_type.get(t, Decimal(0)) for t in LIQUID), Decimal(0))
              - sum((by_type.get(t, Decimal(0)) for t in LIABILITY_TYPES - {"mortgage"}), Decimal(0)))
    investable = sum((by_type.get(t, Decimal(0)) for t in INVESTABLE), Decimal(0))
    rate = Decimal(str(cfg["after_tax_rate"]))
    sell = Decimal(str(cfg["home_selling_cost_pct"]))
    after_tax = total - by_type.get("tax_deferred", Decimal(0)) * rate - by_type.get("real_estate", Decimal(0)) * sell
    return {
        "as_of": as_of.isoformat(),
        "total": str(total), "assets": str(assets), "liabilities": str(liabilities),
        "liquid": str(liquid), "investable": str(investable), "after_tax_estimate": str(after_tax),
        "unvested_not_counted": str(by_type.get("unvested", Decimal(0))),
        "by_type": {t: str(v) for t, v in sorted(by_type.items())},
        "assumptions": {"after_tax_rate": str(rate), "home_selling_cost_pct": str(sell)},
        "lines": lines,
        "warnings": stale_warnings(d, cfg, as_of) + bond_notes,
        "version": VERSION,
    }


def percent_view(nw: dict) -> dict:
    """The net worth report as shares of total assets, with no dollar amounts and no account names."""
    assets = Decimal(nw["assets"])
    if assets <= 0:
        raise FwError("no assets recorded, so there is nothing to show as shares")
    share = lambda v: str((Decimal(v) / assets).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))  # noqa: E731
    return {"as_of": nw["as_of"],
            "of_assets": {"net_worth": share(nw["total"]), "liabilities": share(nw["liabilities"]),
                          "liquid": share(nw["liquid"]), "investable": share(nw["investable"])},
            "assets_by_type": {t: share(v) for t, v in nw["by_type"].items()
                               if t in ASSET_TYPES - {"unvested"}},
            "warnings": len(nw["warnings"]), "version": nw["version"]}


def cmd_networth(args) -> None:
    d = data_dir(args)
    as_of = parse_date(args.as_of) if args.as_of else today()
    nw = compute_networth(d, as_of)
    if args.save:
        (d / "snapshots" / f"{nw['as_of']}.json").write_text(json.dumps(nw, indent=2) + "\n", encoding="utf-8")
    if args.percent_only:
        shares = percent_view(nw)
        if args.json:
            print(json.dumps(shares, indent=2))
            return
        print(f"Net worth shares as of {shares['as_of']}  (fw.py {VERSION}; no dollar amounts shown)")
        for k, label in (("net_worth", "Net worth"), ("liabilities", "Liabilities"), ("liquid", "Liquid net worth"),
                         ("investable", "Investable assets")):
            print(f"  {label:<20} {pct(Decimal(shares['of_assets'][k])):>9} of assets")
        print("  Assets by type:")
        for t, v in shares["assets_by_type"].items():
            print(f"    {t:<18} {pct(Decimal(v)):>9}")
        if shares["warnings"]:
            print(f"  {shares['warnings']} warning(s) hidden in this view; run `networth` without --percent-only")
        print(DISCLAIMER)
        return
    if args.json:
        print(json.dumps(nw, indent=2))
        return
    D = Decimal
    print(f"Net worth as of {nw['as_of']}  (fw.py {VERSION})")
    print(f"  Total net worth      {fmt(D(nw['total'])):>16}   assets {fmt(D(nw['assets']))} - liabilities {fmt(D(nw['liabilities']))}")
    print(f"  Liquid net worth     {fmt(D(nw['liquid'])):>16}   cash + taxable + savings bonds - debts other than the mortgage")
    print(f"  Investable assets    {fmt(D(nw['investable'])):>16}   cash + brokerage + retirement + HSA + savings bonds")
    print(f"  After-tax estimate   {fmt(D(nw['after_tax_estimate'])):>16}   tax-deferred x (1 - {nw['assumptions']['after_tax_rate']}),"
          f" home less {pct(D(nw['assumptions']['home_selling_cost_pct']))} selling cost")
    if D(nw["unvested_not_counted"]):
        print(f"  Unvested (not counted) {fmt(D(nw['unvested_not_counted'])):>14}")
    print("  By type:")
    for t, v in nw["by_type"].items():
        sign = "-" if t in LIABILITY_TYPES else " "
        print(f"    {sign} {t:<16} {fmt(D(v)):>16}")
    for w in nw["warnings"]:
        print(f"  warning: {w}")
    if args.save:
        print(f"  saved snapshots/{nw['as_of']}.json")
    print(DISCLAIMER)


def cmd_history(args) -> None:
    d = data_dir(args)
    snaps = sorted((d / "snapshots").glob("*.json"))
    if not snaps:
        print("no snapshots yet; run `fw.py networth --save`")
        return
    method_dates = set()
    if (d / "methods.log").exists():
        # only valuation settings break the series; import lines in the log do not
        method_dates = {ln.split(" ", 1)[0] for ln in (d / "methods.log").read_text(encoding="utf-8").splitlines()
                        if ln.split(" ")[1:2] == ["config"]}
    print(f"{'date':<12}{'total':>16}{'change':>16}{'liquid':>16}{'investable':>16}")
    prev_total, prev_date = None, ""
    for f in snaps:
        s = json.loads(f.read_text(encoding="utf-8"))
        tot = Decimal(s["total"])
        ch = fmt(tot - prev_total) if prev_total is not None else ""
        changed = prev_date and any(prev_date < m <= s["as_of"] for m in method_dates)
        mark = "  (method changed)" if changed else ""
        print(f"{s['as_of']:<12}{fmt(tot):>16}{ch:>16}{fmt(Decimal(s['liquid'])):>16}{fmt(Decimal(s['investable'])):>16}{mark}")
        prev_total, prev_date = tot, s["as_of"]


# ---------- allocation / fees ----------

def latest_holdings(d: Path, as_of: dt.date | None = None) -> list[dict]:
    rows = [r for r in read_rows(d, "holdings.csv") if as_of is None or r["date"] <= as_of.isoformat()]
    last = {}
    for r in rows:
        if r["date"] > last.get(r["account"], ""):
            last[r["account"]] = r["date"]
    return [r for r in rows if r["date"] == last[r["account"]]]


def cmd_allocation(args) -> None:
    d = data_dir(args)
    cfg = load_config(d)
    hs = latest_holdings(d)
    if not hs:
        print("no holdings recorded; use `fw.py holding set` or `fw.py import holdings`")
        return
    by_cls: dict[str, Decimal] = {}
    for h in hs:
        by_cls[h["asset_class"]] = by_cls.get(h["asset_class"], Decimal(0)) + Decimal(h["value"])
    total = sum(by_cls.values(), Decimal(0))
    targets = {k: Decimal(str(v)) for k, v in (cfg.get("targets") or {}).items()}
    print(f"Allocation across {len(hs)} holding(s), total {fmt(total)}  (latest date per account)")
    print(f"  {'class':<12}{'value':>16}{'actual':>10}{'target':>10}{'drift':>10}")
    for cls in sorted(set(by_cls) | set(targets)):
        v = by_cls.get(cls, Decimal(0))
        actual = v / total if total else Decimal(0)
        tgt = targets.get(cls)
        if tgt is None:
            print(f"  {cls:<12}{fmt(v):>16}{pct(actual):>10}")
            continue
        drift = actual - tgt
        # 5/25 bands: absolute 5 points for big targets, relative 25% for small ones
        band = Decimal("0.05") if tgt >= Decimal("0.20") else tgt * Decimal("0.25")
        flag = "  REBALANCE BAND CROSSED" if abs(drift) > band else ""
        print(f"  {cls:<12}{fmt(v):>16}{pct(actual):>10}{pct(tgt):>10}{pct(drift):>10}{flag}")
    if targets and sum(targets.values()) != 1:
        print(f"  warning: targets add up to {pct(sum(targets.values()))}, not 100%")
    print(DISCLAIMER)


def cmd_fees(args) -> None:
    d = data_dir(args)
    hs = [h for h in latest_holdings(d) if not args.account or h["account"] == args.account]
    known = [h for h in hs if h["expense_ratio"]]
    if not known:
        print("no expense ratios recorded; add them with `fw.py holding set ... --expense-ratio 0.0004` "
              "(from the plan's 404a-5 fee disclosure or the fund page)")
        return
    val = sum((Decimal(h["value"]) for h in known), Decimal(0))
    cost = sum((Decimal(h["value"]) * Decimal(h["expense_ratio"]) for h in known), Decimal(0))
    print(f"Weighted expense ratio {pct(cost / val)} on {fmt(val)}: about {fmt(cost)} a year in fund expenses")
    missing = [h["symbol"] for h in hs if not h["expense_ratio"]]
    if missing:
        print(f"  no expense ratio for: {', '.join(missing)}")
    if args.project:
        fee_projection(known, val, money(args.growth), money(args.admin_fee) if args.admin_fee else Decimal(0))
    else:
        print("  Plan administrative fees are separate; they appear in dollars on the quarterly statement. "
              "`fees --project --admin-fee <dollars a year>` shows what both cost over 10 to 30 years.")
    print(DISCLAIMER)


def fee_projection(hs: list[dict], val: Decimal, g: Decimal, admin: Decimal) -> None:
    """What fund expenses and a yearly admin fee take from today's holdings, compounded, with no new money."""
    if not Decimal(0) <= g < 1:
        raise FwError("--growth is a yearly rate as a decimal, like 0.06")
    print(f"  Fee drag on the {fmt(val)} with a known expense ratio, at an assumed {pct(g)} a year before fees, "
          "no new contributions:")
    print(f"    {'years':<7}{'fund expenses':>16}{'admin fees':>14}{'total lost':>16}{'value with fees':>18}")
    for n in (10, 20, 30):
        gross = sum((Decimal(h["value"]) * (1 + g) ** n for h in hs), Decimal(0))
        net = sum((Decimal(h["value"]) * (1 + g - Decimal(h["expense_ratio"])) ** n for h in hs), Decimal(0))
        fees_fv = admin * (((1 + g) ** n - 1) / g if g else Decimal(n))  # each year's fee, compounded
        print(f"    {n:<7}{fmt(gross - net):>16}{fmt(fees_fv):>14}{fmt(gross - net + fees_fv):>16}"
              f"{fmt(net - fees_fv):>18}")
    print("  An assumption, not a forecast: change it with --growth. Admin fees come from the plan's 404a-5 "
          "disclosure or the quarterly statement.")


# ---------- returns ----------

def xirr(flows: list[tuple[dt.date, Decimal]]) -> Decimal:
    """Annual money-weighted return. flows: investor view (deposits negative, ending value positive)."""
    if not any(a < 0 for _, a in flows) or not any(a > 0 for _, a in flows):
        raise FwError("XIRR needs at least one deposit and one ending value")
    t0 = min(t for t, _ in flows)

    def npv(r: Decimal) -> Decimal:
        return sum((a / (1 + r) ** (Decimal((t - t0).days) / Decimal(365)) for t, a in flows), Decimal(0))

    lo, hi = Decimal("-0.99"), Decimal("10")
    flo, fhi = npv(lo), npv(hi)
    if flo * fhi > 0:
        raise FwError("XIRR has no solution between -99% and 1000% for these flows")
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = npv(mid)
        if abs(fm) < Decimal("0.0000001"):
            break
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return mid


def twr(points: list[tuple[dt.date, Decimal]], flows: list[tuple[dt.date, Decimal]]) -> tuple[Decimal, int, int]:
    """Time-weighted return: Modified Dietz between each pair of recorded balances, chain-linked.
    points: (date, balance) oldest first; flows: (date, money into the account). A flow on a
    balance date belongs to the period that ends there. Returns (cumulative return, periods, days)."""
    growth, n, span = Decimal(1), 0, 0
    for (a, va), (b, vb) in zip(points, points[1:]):
        days = Decimal((b - a).days)
        inside = [(t, f) for t, f in flows if a < t <= b]
        net = sum((f for _, f in inside), Decimal(0))
        base = va + sum((f * Decimal((b - t).days) / days for t, f in inside), Decimal(0))
        if va == 0 and base == 0:
            continue  # the account was empty and nothing came in until the period's last day
        if base <= 0:
            raise FwError(f"no time-weighted return for {a} to {b}: the starting balance plus weighted "
                          "deposits is not positive")
        growth *= 1 + (vb - va - net) / base
        n += 1
        span += (b - a).days
    return growth - 1, n, span


def cmd_returns(args) -> None:
    d = data_dir(args)
    need_account(d, args.account)
    as_of = parse_date(args.as_of) if args.as_of else today()
    bal = latest_balances(d, as_of).get(args.account)
    if not bal:
        raise FwError(f"no balance for {args.account} on or before {as_of}")
    hist = sorted((r for r in read_rows(d, "balances.csv") if r["account"] == args.account),
                  key=lambda r: r["date"])
    start, end = parse_date(hist[0]["date"]), parse_date(bal["date"])
    # investor view: the opening balance and each contribution are money paid in (negative),
    # the closing balance is money that could be taken out (positive)
    flows = [(start, -Decimal(hist[0]["value"]))] if Decimal(hist[0]["value"]) and start < end else []
    flows += [(parse_date(r["date"]), -Decimal(r["amount"])) for r in read_rows(d, "flows.csv")
              if r["account"] == args.account and (start < parse_date(r["date"]) <= end or
                                                   (not flows and parse_date(r["date"]) <= end))]
    flows.append((end, Decimal(bal["value"])))
    r = xirr(flows)
    print(f"{args.account}: money-weighted return (XIRR) {pct(r)} a year from {min(t for t, _ in flows)} "
          f"to {bal['date']} over {len(flows)} cash flow(s)")
    points = {row["date"]: Decimal(row["value"]) for row in hist if row["date"] <= bal["date"]}  # last per day
    deposits = [(parse_date(row["date"]), Decimal(row["amount"])) for row in read_rows(d, "flows.csv")
                if row["account"] == args.account]
    if len(points) > 1:
        try:
            tw, periods, days = twr(sorted((parse_date(k), v) for k, v in points.items()), deposits)
        except FwError as e:
            print(f"  time-weighted return: not available ({e})")
            tw, periods, days = None, 0, 0
    if len(points) > 1 and tw is not None and periods:
        shown = f"{pct((1 + tw) ** (Decimal(365) / days) - 1)} a year" if days >= 365 and tw > -1 else \
            f"{pct(tw)} over {days} days (not annualised under a year)"
        print(f"  time-weighted return (Modified Dietz, chain-linked over {periods} period(s)) {shown}")
        print("  XIRR is the user's own result, timing of deposits included; time-weighted is what the "
              "investments did, the number to set beside a fund or index.")
    print("  Deposits and contributions are flows into the account; record them with `fw.py flow add`.")
    print(DISCLAIMER)


# ---------- where a sum goes ----------

def level_payment(principal: Decimal, rate: Decimal, months: int) -> Decimal:
    """Monthly principal and interest on a fixed-rate loan; rate is a yearly percent like 3.875."""
    r = rate / 1200
    if r == 0:
        return (principal / months).quantize(CENT, rounding=ROUND_HALF_UP)
    return (principal * r / (1 - (1 + r) ** -months)).quantize(CENT, rounding=ROUND_HALF_UP)


def amortize(bal: Decimal, rate: Decimal, payment: Decimal, extra: Decimal = Decimal(0)) -> tuple[int, Decimal]:
    """Payments left on a fixed-rate loan and the interest paid on the way, interest rounded to the cent monthly."""
    r = rate / 1200
    months, interest = 0, Decimal(0)
    while bal > 0:
        i = (bal * r).quantize(CENT, rounding=ROUND_HALF_UP)
        if payment + extra <= i:
            raise FwError("the payment does not cover the interest; --payment is principal and interest only")
        interest += i
        bal = bal + i - payment - extra
        if bal < 1:  # cents left by a rounded payment ride on the last one, as servicers do
            bal = Decimal(0)
        months += 1
        if months > 1200:
            raise FwError("more than 100 years to pay off; check the inputs")
    return months, interest


def month_after(day: dt.date, n: int) -> str:
    m = day.year * 12 + day.month - 1 + n
    return f"{m // 12}-{m % 12 + 1:02d}"


def cmd_mortgage(args) -> None:
    d = data_dir(args)
    as_of = parse_date(args.as_of) if args.as_of else today()
    rate = money(args.rate)
    if args.balance:
        bal, where = money(args.balance), "given"
    else:
        latest = latest_balances(d, as_of)
        ids = [args.account] if args.account else [
            a for a, r in accounts(d).items() if r["type"] == "mortgage" and a in latest]
        if len(ids) != 1 or ids[0] not in latest:
            raise FwError(f"pass --balance or --account (found {len(ids)} mortgage balances)")
        bal, where = abs(Decimal(latest[ids[0]]["value"])), f"{ids[0]} as of {latest[ids[0]]['date']}"
    if args.payment:
        pay, how = money(args.payment), ""
    elif args.original and args.term:
        pay, how = level_payment(money(args.original), rate, args.term), " (scheduled, from --original and --term)"
    else:
        raise FwError("pass --payment (monthly principal and interest, no escrow) or --original and --term")
    extra, lump = money(args.extra or 0), money(args.lump or 0)
    if not Decimal(0) <= lump <= bal:
        raise FwError("--lump must be between 0 and the balance")
    n0, i0 = amortize(bal, rate, pay, extra)
    plus = f" plus {fmt(extra)} extra principal" if extra else ""
    print(f"Mortgage {fmt(bal)} ({where}) at {rate}%: principal and interest {fmt(pay)} a month{how}{plus}")
    print(f"  Paid off {month_after(as_of, n0)} ({n0} payments), {fmt(i0)} interest still to pay")
    if lump:
        n1, i1 = amortize(bal - lump, rate, pay, extra)
        print(f"  With {fmt(lump)} paid now: paid off {month_after(as_of, n1)} ({n0 - n1} payments sooner), "
              f"{fmt(i0 - i1)} less interest")
        print(f"  The payment stays {fmt(pay + extra)} a month until then: the {fmt(lump)} frees no monthly cash "
              "until the loan is gone, and getting it back out takes a new loan.")
        print(f"  It earns the loan's rate, {rate}% a year, with no risk; that is tax-free when the mortgage "
              "interest is not itemized (most households take the standard deduction).")
    print("  Escrow (property tax, insurance) goes on after payoff; it is not in these figures.")
    print(DISCLAIMER)


TAX_KINDS = {"none": "not taxed", "full": "federal and state", "federal": "federal only",
             "deductible": "interest itemized"}


def compare_option(spec: str, rates: dict) -> tuple[str, Decimal, str]:
    """NAME=RATE[:TAX] with RATE a yearly percent, or 'ibond' for the current I bond composite rate."""
    if spec.strip().lower() == "ibond":
        cur = next((p for p in rates["savings_bond_rates"] if p["series"] == "I"), None)
        if not cur:
            raise FwError("no I bond rate in rates.json")
        return f"I bond (to {cur['to']})", Decimal(cur["composite"]), "federal"
    name, eq, rest = spec.partition("=")
    rate, _, kind = rest.partition(":")
    kind = kind or "full"
    if not eq or not name or kind not in TAX_KINDS:
        raise FwError(f"option {spec!r}: use NAME=RATE[:TAX], TAX one of {', '.join(TAX_KINDS)}, or 'ibond'")
    return name, money(rate), kind


def cmd_compare(args) -> None:
    cfg = load_config(data_dir(args))
    fed = money(args.federal) if args.federal else money(cfg["after_tax_rate"])
    state = money(args.state)
    amount, years = money(args.amount), args.years
    rates = load_rates()
    rows = []
    for spec in args.option:
        name, rate, kind = compare_option(spec, rates)
        cut = {"none": Decimal(0), "federal": fed}.get(kind, fed + state)
        y = rate / 100 * (1 - cut)
        rows.append((y, name, rate, kind, amount * (1 + y) ** years))
    rows.sort(key=lambda r: r[0], reverse=True)
    print(f"{fmt(amount)} for {years} years, federal {pct(fed)}, state {pct(state)}; "
          "after-tax yield, best first:")
    print(f"  {'option':<26}{'rate':>8}  {'taxed':<18}{'after tax':>10}{'after ' + str(years) + ' years':>18}")
    for y, name, rate, kind, fv in rows:
        print(f"  {name[:25]:<26}{str(rate) + '%':>8}  {TAX_KINDS[kind]:<18}{pct(y):>10}{fmt(fv):>18}")
    print("  Fixed and today's rates only: a stock fund has no promised rate, so it is a separate choice about risk. "
          "Savings and I bond rates move; I bond tax can be deferred to redemption, which this ignores.")
    print("  Access differs: savings same day, Treasury bills at maturity, an I bond after 12 months (3 months' "
          "interest lost before 5 years), a mortgage prepayment only through a new loan.")
    print(DISCLAIMER)


# ---------- new listings and single positions ----------

SCALE = {"K": 3, "M": 6, "B": 9, "T": 12}
QUIET_DAYS = 10  # FINRA Rule 2241: underwriters' analysts wait 10 days after an IPO
CONCENTRATION = (Decimal("0.05"), Decimal("0.10"))  # bands in references/new-listings.md


def big(text: str) -> Decimal:
    """money() that also reads K, M, B and T: 16.8B, 1.5T."""
    s = str(text).strip().replace("$", "")
    v = money(s[:-1]) * Decimal(10) ** SCALE[s[-1].upper()] if s and s[-1].upper() in SCALE else money(s)
    if abs(v) >= Decimal(10) ** 18:
        raise FwError(f"too large: {text!r}")
    return v


def positive(text: str, what: str, parse=money) -> Decimal:
    v = parse(text)
    if v <= 0:
        raise FwError(f"{what} must be above zero: {text!r}")
    return v


def short(v: Decimal, unit: str = "$") -> str:
    for k in ("T", "B", "M"):
        if abs(v) >= Decimal(10) ** SCALE[k]:
            return f"{unit}{(v / Decimal(10) ** SCALE[k]).quantize(CENT, rounding=ROUND_HALF_UP)}{k}"
    return fmt(v) if unit else f"{v:,}"


def quarter_end(day: dt.date) -> dt.date:
    """The last day of the calendar quarter that holds `day`."""
    m = (day.month - 1) // 3 * 3 + 3
    return dt.date(day.year + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1)


def cmd_ipo(args) -> None:
    shares = positive(args.shares, "--shares", big) if args.shares else None
    if shares is not None and shares < 1:
        raise FwError("--shares is a share count, at least 1")
    if args.revenue_q and args.revenue:
        raise FwError("pass --revenue (a year) or --revenue-q (latest quarter), not both")
    revenue = (positive(args.revenue, "--revenue", big) if args.revenue else
               positive(args.revenue_q, "--revenue-q", big) * 4 if args.revenue_q else None)
    prices = [positive(p, "--price") for p in args.price or []]
    values = [positive(v, "--valuation", big) for v in args.valuation or []]
    offer = positive(args.offer, "--offer") if args.offer else None
    if args.lockup_days < 0:
        raise FwError("--lockup-days cannot be negative")
    if (prices and not shares) or not (prices or values or args.list_date):
        raise FwError("pass --valuation, or --price with --shares, or --list-date")
    day = parse_date(args.list_date) if args.list_date else None
    rows = [(p * shares, p) for p in prices] + [(v, v / shares if shares else None) for v in values]
    if rows:
        rev = (f"; revenue {short(revenue)} a year" + (" (latest quarter x 4)" if args.revenue_q else "")
               if revenue else "")
        print(f"New listing: {short(shares, '') + ' shares' if shares else 'no share count given'}{rev}")
        print(f"  {'market value':>16}{'per share':>16}{'x revenue':>12}{'vs offer':>11}")
        for cap, per in sorted(rows):
            ps = f"{(cap / revenue).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}x" if revenue else "-"
            vs = pct(per / offer - 1) if offer and per else "-"
            print(f"  {short(cap):>16}{fmt(per) if per else '-':>16}{ps:>12}{vs:>11}")
        print("  Market value = per-share price x the share count in the prospectus (basic shares of every class; "
              "counting options and RSUs makes it larger). Pre-IPO quotes are for other share classes and splits, "
              "so they do not carry over.")
        if revenue and any(cap / revenue > 40 for cap, _ in rows):
            print("  Over 40 times revenue: in Ritter's data, IPOs priced there trailed the market by 58.5% over "
                  "3 years when bought at the first close (references/new-listings.md).")
    if day:
        dates = [(day + dt.timedelta(days=QUIET_DAYS),
                  f"underwriters' analysts may publish ({QUIET_DAYS} days, FINRA Rule 2241)"),
                 (quarter_end(day + dt.timedelta(days=1)),
                  "first quarter end as a public company (calendar quarters); its results come weeks later"),
                 (day + dt.timedelta(days=args.lockup_days),
                  f"lock-up ends ({args.lockup_days} days from listing; prospectuses often count from pricing, a "
                  "day earlier, and early releases are common)")]
        print(f"Dates after a {day.isoformat()} listing (check the prospectus):")
        for when, what in sorted(dates):
            print(f"  {when.isoformat()}  {what}")
    print(DISCLAIMER)


def cmd_position(args) -> None:
    d = data_dir(args)
    as_of = parse_date(args.as_of) if args.as_of else today()
    amount = positive(args.amount, "amount")
    spend = money(args.monthly_spend) if args.monthly_spend else None
    if (spend is not None and spend < 0) or args.emergency_months < 0:
        raise FwError("--monthly-spend and --emergency-months cannot be negative")
    price = positive(args.price, "--price") if args.price else None
    below = [money(s) for s in args.below or ["0"]]
    if any(not Decimal(0) <= s < 100 for s in below):
        raise FwError("--below steps are percents from 0 up to (not including) 100")
    nw = compute_networth(d, as_of)
    held = sum((Decimal(h["value"]) for h in latest_holdings(d, as_of)
                if args.symbol and h.get("symbol", "").upper() == args.symbol.upper()), Decimal(0))
    stake = amount + held
    label = args.symbol.upper() if args.symbol else "one stock"
    print(f"If you buy {fmt(amount)} of {label}" + (f" (already holding {fmt(held)})" if held else "")
          + f", against the records as of {nw['as_of']}:")
    for key, name in (("investable", "investable assets"), ("liquid", "liquid net worth"),
                      ("total", "total net worth")):
        base = Decimal(nw[key])
        if base > 0:
            print(f"  {pct(stake / base):>9} of {name} ({fmt(base)})")
    inv = Decimal(nw["investable"])
    low, high = CONCENTRATION
    if inv <= 0:
        print("  no investable assets recorded, so concentration cannot be measured")
    else:
        share = stake / inv
        print("  " + ("over 10% of investable assets: a concentrated position" if share > high else
                      "over 5% and up to 10% of investable assets: a large single holding" if share > low else
                      "5% of investable assets or less"))
    if spend is not None:
        need = spend * args.emergency_months
        left = Decimal(nw["by_type"].get("cash", "0")) - amount
        print(f"  Cash after paying {fmt(left)}; {args.emergency_months} months of spending is {fmt(need)}: "
              + ("the emergency fund stays whole" if left >= need else f"{fmt(need - left)} short of it"))
    if price:
        part = (amount / len(below)).quantize(CENT, rounding="ROUND_DOWN")
        print(f"  A ladder of limit orders you could place, {fmt(part)} each, from a {fmt(price)} reference price:")
        spent, empty = Decimal(0), False
        for s in below:
            lim = (price * (1 - s / 100)).quantize(CENT, rounding=ROUND_HALF_UP)
            n = (part / lim).quantize(Decimal("0.0001") if args.fractional else Decimal(1), rounding="ROUND_DOWN")
            spent += n * lim
            empty = empty or n == 0
            print(f"    limit {fmt(lim):>12} ({s}% below): {n} shares, {fmt(n * lim)}")
        print(f"  At most {fmt(spent)} if every order fills; a limit order fills only at its price or better, "
              "so the lower ones may never fill.")
        if empty:
            print("  An order buys no whole share at that price: use fewer steps, or --fractional if the broker "
                  "sells fractions.")
    print(DISCLAIMER)


# ---------- reference numbers ----------

def cmd_limits(args) -> None:
    rates = load_rates()
    year = str(args.year or today().year)
    lim = rates["limits"].get(year)
    if not lim:
        have = ", ".join(sorted(rates["limits"]))
        raise FwError(f"no limits for {year} in rates.json (have {have}); refresh the skill, do not guess")
    print(f"Contribution limits for {year} (source: {lim['source']}, checked {lim['checked']})")
    for k, v in lim["values"].items():
        print(f"  {k:<34} {fmt(Decimal(v))}")
    for n in lim.get("notes", []):
        print(f"  note: {n}")


def cmd_bond_rates(args) -> None:
    rates = load_rates()
    for p in rates["savings_bond_rates"]:
        print(f"  {p['series']:<3} issued {p['from']} to {p['to']}: composite {p['composite']}%"
              f" (fixed {p['fixed']}%)  source {p['source']}")
    nc = rates.get("next_change", {}).get("i_bond_rate")
    if nc:
        print(f"  next announcement: {nc['date']}")


def cmd_benchmark(args) -> None:
    rates = load_rates()
    scf = rates["scf"]
    age = args.age
    if age is None:
        cfg = load_config(data_dir(args))
        if not cfg.get("birth_year"):
            raise FwError("pass --age or set birth_year with `fw.py config set birth_year 1970`")
        age = today().year - int(cfg["birth_year"])
    band = next(b for b in scf["median_by_age"] if b["min"] <= age <= b["max"])
    print(f"{scf['survey']} median household net worth, age {band['label']}: {fmt(Decimal(band['median']))}"
          f" (all households {fmt(Decimal(scf['median_all']))})")
    print(f"  The SCF counts households, not people; a single person's number does not compare one to one. Source: {scf['source']}")


# ---------- redaction ----------

REDACTIONS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), lambda m: "***-**-****"),
    (re.compile(r"\b(?:\d[ -]?){8,19}\d\b"), lambda m: "****" + re.sub(r"\D", "", m.group())[-4:]),
    (re.compile(r"\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/(?:19|20)\d{2}\b(?=.*\b(?:birth|DOB)\b)", re.I),
     lambda m: "**/**/****"),
]


def redact_text(text: str) -> str:
    for pat, rep in REDACTIONS:
        text = pat.sub(rep, text)
    return text


HUNT_STATUS = {
    "to_search": "find the plan on the employer's Form 5500 (efast.dol.gov); check W-2 box 12 D/AA for those years",
    "searching": "call the recordkeeper on the Form 5500 (script in references/old-401ks.md); then missingmoney.com",
    "found": "add it with `fw.py account add` and record the balance; then decide on a rollover",
    "rolled_over": "link the receiving account with --account so it is counted once",
    "cashed_out": "nothing to collect; keep the note (check the 1099-R year) and close it",
    "merged": "find the successor plan's recordkeeper on its Form 5500 and call them",
    "unclaimed": "claim it from the state unclaimed property office or the IRA provider yourself",
    "no_plan": "no plan found for these years; closed",
    "closed": "done",
}


def hunt_rows(d: Path) -> list[dict]:
    if not (d / "hunt.csv").exists():
        write_rows(d, "hunt.csv", [])
    return read_rows(d, "hunt.csv")


def hunt_status(s: str) -> str:
    if s not in HUNT_STATUS:
        raise FwError(f"status must be one of {sorted(HUNT_STATUS)}")
    return s


def hunt_ein(s: str | None) -> str:
    if not s:
        return ""
    if not re.fullmatch(r"\d{2}-?\d{7}", s):
        raise FwError("--ein takes a 9-digit employer EIN like 12-3456789")
    return s if "-" in s else f"{s[:2]}-{s[2:]}"


def cmd_hunt_add(args) -> None:
    d = data_dir(args)
    rows = hunt_rows(d)
    if any(r["id"] == args.id for r in rows):
        raise FwError(f"search {args.id!r} already exists; use `fw.py hunt update`")
    note = f"{today().isoformat()}: {args.note}" if args.note else ""
    append_row(d, "hunt.csv", {"id": args.id, "employer": args.employer, "years": args.years or "",
                               "plan": args.plan or "", "ein": hunt_ein(args.ein),
                               "recordkeeper": args.recordkeeper or "", "status": "to_search",
                               "account": "", "next": args.next or "", "updated": today().isoformat(),
                               "notes": note})
    print(f"added search {args.id} ({args.employer}); next: {args.next or HUNT_STATUS['to_search']}")


def cmd_hunt_update(args) -> None:
    d = data_dir(args)
    rows = hunt_rows(d)
    row = next((r for r in rows if r["id"] == args.id), None)
    if row is None:
        raise FwError(f"no search {args.id!r}; `fw.py hunt list` shows them")
    if args.status:
        row["status"] = hunt_status(args.status)
    for field in ("plan", "recordkeeper", "years", "next"):
        if getattr(args, field):
            row[field] = getattr(args, field)
    if args.ein:
        row["ein"] = hunt_ein(args.ein)
    if args.account:
        need_account(d, args.account)
        row["account"] = args.account
    if args.note:
        entry = f"{today().isoformat()}: {args.note}"
        row["notes"] = f"{row['notes']} | {entry}" if row["notes"] else entry
    row["updated"] = today().isoformat()
    write_rows(d, "hunt.csv", rows)
    print(f"{args.id}: {row['status']}; next: {row['next'] or HUNT_STATUS[row['status']]}")


def cmd_hunt_list(args) -> None:
    d = data_dir(args)
    rows = hunt_rows(d)
    if not rows:
        print("no searches yet; add one per former employer with `fw.py hunt add`")
        return
    open_ = 0
    for r in rows:
        done = r["status"] in ("cashed_out", "no_plan", "closed") or (
            r["status"] == "rolled_over" and r["account"])
        open_ += not done
        bits = [r["years"], r["plan"], f"EIN {r['ein']}" if r["ein"] else "", r["recordkeeper"],
                f"-> {r['account']}" if r["account"] else ""]
        print(f"{r['id']:<16} {r['status']:<12} {r['employer']}  " + "  ".join(b for b in bits if b))
        if not done:
            print(f"{'':<16} next: {r.get('next') or HUNT_STATUS[r['status']]}")
        if r["notes"]:
            print(f"{'':<16} notes: {r['notes']}")
    print(f"{open_} of {len(rows)} searches open (last updated {max(r['updated'] for r in rows)})")


def cmd_redact(args) -> None:
    text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    out = redact_text(text)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"wrote redacted copy to {args.out}")
    else:
        sys.stdout.write(out)


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:  # python -I leaves the script's folder off the path
        sys.path.insert(0, here)
    import fw_import as fwi  # the importers, loaded here so `import fw` stays acyclic
    import fw_mail as fwm
    p = argparse.ArgumentParser(prog="fw.py", description=__doc__.split("\n")[0])
    p.add_argument("--data", help="data folder (default $FINWRIGHT_DATA or ~/finwright-data)")
    p.add_argument("--version", action="version", version=f"finwright {VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create the data folder")
    s.add_argument("--allow-git", action="store_true")
    s.set_defaults(fn=cmd_init)
    sub.add_parser("check", help="safety and freshness checks").set_defaults(fn=cmd_check)

    acc = sub.add_parser("account", help="add, update or list accounts").add_subparsers(dest="sub", required=True)
    s = acc.add_parser("add")
    s.add_argument("id")
    s.add_argument("--type", required=True)
    s.add_argument("--name")
    s.add_argument("--institution")
    s.add_argument("--last4")
    s.add_argument("--notes")
    s.set_defaults(fn=cmd_account_add)
    s = acc.add_parser("update", help="rename, retype or re-home an account; --note appends a dated note")
    s.add_argument("id")
    for flag in ("--type", "--name", "--institution", "--last4", "--note"):
        s.add_argument(flag)
    s.set_defaults(fn=cmd_account_update)
    acc.add_parser("list").set_defaults(fn=cmd_account_list)

    bal = sub.add_parser("balance", help="record a balance").add_subparsers(dest="sub", required=True)
    s = bal.add_parser("set")
    s.add_argument("account")
    s.add_argument("value")
    s.add_argument("--as-of")
    s.add_argument("--source", default="manual")
    s.add_argument("--method")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_balance_set)

    imp = sub.add_parser("import", help="import files the user downloaded").add_subparsers(dest="sub", required=True)
    s = imp.add_parser("balances", help="CSV with date,account,value[,source,method,note]")
    s.add_argument("file")
    s.add_argument("--source", default="import")
    s.set_defaults(fn=fwi.cmd_import_balances)
    s = imp.add_parser("monarch", help="Monarch 'Download account balances' CSV (Date,Balance,Account)")
    s.add_argument("file")
    s.add_argument("--all", action="store_true", help="every dated row, not just the newest per account")
    s.add_argument("--skip-unmapped", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=fwi.cmd_import_monarch)
    s = imp.add_parser("bofa", help="Bank of America checking/savings activity CSV (summary + Running Bal.)")
    s.add_argument("file")
    s.add_argument("account")
    s.add_argument("--monthly", action="store_true", help="also record each month's last running balance")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=fwi.cmd_import_bofa)
    s = imp.add_parser("ofx", help="QFX or OFX download: bank and card balances, brokerage positions")
    s.add_argument("file")
    s.add_argument("--account", help="the account, when the file holds one statement and no last 4 matches")
    s.add_argument("--classes", help="SYM=class,SYM=class for brokerage positions")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=fwi.cmd_import_ofx)
    mo = sub.add_parser("monarch", help="map Monarch account names to finwright accounts").add_subparsers(
        dest="sub", required=True)
    s = mo.add_parser("map")
    s.add_argument("name", nargs="?")
    s.add_argument("account", nargs="?")
    s.set_defaults(fn=fwi.cmd_monarch_map)
    s = imp.add_parser("holdings", help="broker or 401k positions CSV")
    s.add_argument("file")
    s.add_argument("--account", required=True)
    s.add_argument("--as-of", required=True)
    s.add_argument("--symbol-col", default="Symbol")
    s.add_argument("--value-col", default="Current Value")
    s.add_argument("--units-col")
    s.add_argument("--class-col")
    s.add_argument("--classes", help="SYM=class,SYM=class")
    s.add_argument("--set-balance", action="store_true", help="also record the sum as the account balance")
    s.set_defaults(fn=fwi.cmd_import_holdings)

    hol = sub.add_parser("holding", help="record one holding").add_subparsers(dest="sub", required=True)
    s = hol.add_parser("set")
    s.add_argument("account")
    s.add_argument("symbol")
    s.add_argument("value")
    s.add_argument("--asset-class", required=True)
    s.add_argument("--units")
    s.add_argument("--expense-ratio", help="decimal, 0.0004 for 0.04%%")
    s.add_argument("--as-of")
    s.set_defaults(fn=cmd_holding_set)

    fl = sub.add_parser("flow", help="record a contribution or withdrawal").add_subparsers(dest="sub", required=True)
    s = fl.add_parser("add")
    s.add_argument("account")
    s.add_argument("amount", help="positive = money into the account, negative = out")
    s.add_argument("--date", required=True)
    s.add_argument("--kind", default="contribution")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_flow_add)

    cf = sub.add_parser("config", help="valuation settings").add_subparsers(dest="sub", required=True)
    s = cf.add_parser("set")
    s.add_argument("key")
    s.add_argument("value")
    s.set_defaults(fn=cmd_config_set)

    bd = sub.add_parser("bond", help="savings bonds").add_subparsers(dest="sub", required=True)
    s = bd.add_parser("add")
    s.add_argument("--series", required=True)
    s.add_argument("--issue", required=True, help="YYYY-MM")
    s.add_argument("--denomination", required=True)
    s.add_argument("--id")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_bond_add)
    s = bd.add_parser("refresh", help="download Treasury values for a month")
    s.add_argument("--month")
    s.set_defaults(fn=cmd_bond_refresh)
    s = bd.add_parser("value")
    s.add_argument("--month")
    s.set_defaults(fn=cmd_bond_value)
    bd.add_parser("rates").set_defaults(fn=cmd_bond_rates)

    s = sub.add_parser("networth", help="net worth report")
    s.add_argument("--as-of")
    s.add_argument("--save", action="store_true", help="write snapshots/DATE.json")
    s.add_argument("--json", action="store_true")
    s.add_argument("--percent-only", action="store_true", help="shares of assets only, no dollars or account names")
    s.set_defaults(fn=cmd_networth)
    sub.add_parser("history", help="snapshots over time").set_defaults(fn=cmd_history)
    sub.add_parser("allocation", help="asset allocation and drift").set_defaults(fn=cmd_allocation)
    s = sub.add_parser("fees", help="weighted expense ratio and fee drag")
    s.add_argument("--account")
    s.add_argument("--project", action="store_true", help="dollars lost to fees over 10, 20 and 30 years")
    s.add_argument("--growth", default="0.06", help="assumed yearly return before fees for --project")
    s.add_argument("--admin-fee", help="plan admin fees in dollars a year (404a-5 disclosure) for --project")
    s.set_defaults(fn=cmd_fees)
    s = sub.add_parser("returns", help="money-weighted (XIRR) and time-weighted return for an account")
    s.add_argument("account")
    s.add_argument("--as-of")
    s.set_defaults(fn=cmd_returns)
    s = sub.add_parser("limits", help="contribution limits for a year")
    s.add_argument("--year", type=int)
    s.set_defaults(fn=cmd_limits)
    s = sub.add_parser("benchmark", help="SCF median net worth for an age")
    s.add_argument("--age", type=int)
    s.set_defaults(fn=cmd_benchmark)
    hu = sub.add_parser("hunt", help="track the search for old employer retirement plans").add_subparsers(
        dest="sub", required=True)
    s = hu.add_parser("add")
    s.add_argument("id")
    s.add_argument("--employer", required=True)
    s.add_argument("--years", help="employment years, e.g. 2011-2014")
    s.add_argument("--plan")
    s.add_argument("--ein")
    s.add_argument("--recordkeeper")
    s.add_argument("--next", help="the next step, e.g. 'call Empower, ask for 1099-R'")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_hunt_add)
    s = hu.add_parser("update")
    s.add_argument("id")
    s.add_argument("--status", choices=sorted(HUNT_STATUS))
    s.add_argument("--years")
    s.add_argument("--plan")
    s.add_argument("--ein")
    s.add_argument("--recordkeeper")
    s.add_argument("--account", help="the fw.py account the money is now in")
    s.add_argument("--next", help="the next step; replaces the default hint")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_hunt_update)
    hu.add_parser("list").set_defaults(fn=cmd_hunt_list)
    ma = sub.add_parser("mail", help="find retirement-account mentions in exported mail (mbox, eml, jsonl)"
                        ).add_subparsers(dest="sub", required=True)
    s = ma.add_parser("scan")
    s.add_argument("paths", nargs="+", help="mbox, .eml or .jsonl files, or folders of them")
    s.add_argument("--mailbox", help="label for these messages, e.g. the address they came from")
    s.add_argument("--me", nargs="+", help="the user's own addresses, so their sent mail is marked 'sent'")
    s.add_argument("--since", help="skip mail before this date")
    s.set_defaults(fn=fwm.cmd_mail_scan)
    s = ma.add_parser("sender", help="name the institution behind a sender domain (kept in the data folder)")
    s.add_argument("domain")
    s.add_argument("institution")
    s.set_defaults(fn=fwm.cmd_mail_sender)
    s = ma.add_parser("report", help="mentions grouped by institution, with plans, account endings and links")
    s.add_argument("--institution")
    s.add_argument("--all", action="store_true", help="every message, not only transfers, tax forms, "
                   "statements and the user's own mail")
    s.add_argument("--limit", type=int, default=8)
    s.set_defaults(fn=fwm.cmd_mail_report)
    s = sub.add_parser("mortgage", help="payoff date, interest left and what a lump sum or extra principal saves")
    s.add_argument("--rate", required=True, help="yearly rate in percent, e.g. 3.875")
    s.add_argument("--payment", help="monthly principal and interest, without escrow")
    s.add_argument("--original", help="original loan amount, to work out the scheduled payment")
    s.add_argument("--term", type=int, help="original term in months, e.g. 360")
    s.add_argument("--balance", help="principal left (default: the mortgage account's latest balance)")
    s.add_argument("--account")
    s.add_argument("--extra", help="extra principal each month")
    s.add_argument("--lump", help="a one-time prepayment now")
    s.add_argument("--as-of")
    s.set_defaults(fn=cmd_mortgage)
    s = sub.add_parser("compare", help="after-tax yield of places a sum could go (savings, Treasuries, I bonds, "
                       "paying down a loan)")
    s.add_argument("amount")
    s.add_argument("--option", action="append", required=True,
                   help="NAME=RATE[:none|full|federal|deductible], or ibond; repeat for each")
    s.add_argument("--years", type=int, default=5)
    s.add_argument("--federal", help="marginal federal rate (default: config after_tax_rate)")
    s.add_argument("--state", default="0", help="marginal state rate, e.g. 0.05")
    s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("ipo", help="a new listing in numbers: per-share price, market value, revenue multiple, "
                       "dates after listing")
    s.add_argument("--valuation", nargs="+", help="company values: 1.5T 2T")
    s.add_argument("--price", nargs="+", help="per-share prices (the prospectus range: 120 140)")
    s.add_argument("--shares", help="shares outstanding after the offering, from the prospectus: 12.5B")
    s.add_argument("--revenue", help="revenue for a year: 67B")
    s.add_argument("--revenue-q", help="latest quarter's revenue, annualised x 4: 16.8B")
    s.add_argument("--offer", help="the offer price, to show each price against it")
    s.add_argument("--list-date", help="first trading day, for the quiet period and lock-up dates")
    s.add_argument("--lockup-days", type=int, default=180)
    s.set_defaults(fn=cmd_ipo)
    s = sub.add_parser("position", help="what a single-stock buy would be against the records: concentration, "
                       "emergency fund, a ladder of limit orders")
    s.add_argument("amount")
    s.add_argument("--symbol", help="ticker, to add what is already held")
    s.add_argument("--monthly-spend", help="monthly spending, to check the emergency fund after the buy")
    s.add_argument("--emergency-months", type=int, default=6)
    s.add_argument("--price", help="reference price for the ladder")
    s.add_argument("--below", nargs="+", help="percents below --price, one limit order each: 0 10 20")
    s.add_argument("--fractional", action="store_true", help="the broker sells fractional shares")
    s.add_argument("--as-of")
    s.set_defaults(fn=cmd_position)
    s = sub.add_parser("redact", help="mask account numbers and SSNs in a text file")
    s.add_argument("file")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_redact)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", newline="\n")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
    except FwError as e:
        print(f"fw.py: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.modules.setdefault("fw", sys.modules[__name__])  # fw_import's `from fw import` gets this module
    sys.exit(main())
