"""finwright goals: targets with a date window and a priority class, funded from account shares.

`goal add` records a goal, `goal list` shows funded, gap, months left and the monthly saving needed with no
growth, and `goal check` runs a seeded Monte Carlo of the chance of reaching each goal and prints every
assumption it used. Goals live in <data>/goals.csv. Standard library only, no network.

Priority classes: essential (safety net, shelter, health, dependants), important (keeping the standard of
living), aspirational (dreams and large bets). Lower classes never draw on money an essential goal needs.
"""
from __future__ import annotations

import csv
import math
import random
from decimal import Decimal
from pathlib import Path

from fw import (DISCLAIMER, FwError, accounts, data_dir, fmt, latest_balances, latest_holdings, money,
                parse_date, today)

GOAL_FIELDS = ["id", "name", "target", "earliest", "by", "class", "accounts", "monthly", "note"]
CLASSES = ("essential", "important", "aspirational")
# Real (after inflation) yearly return and volatility per asset class. Ours, round and modest; not forecasts.
ASSUME = {"us_stock": (0.05, 0.16), "intl_stock": (0.05, 0.18), "bond": (0.015, 0.06), "cash": (0.005, 0.01),
          "real_estate": (0.03, 0.12), "other": (0.03, 0.15)}
SAFE = {"cash", "bond"}
STOCK = {"us_stock", "intl_stock"}
TYPE_CLASS = {"cash": "cash", "savings_bond": "bond", "real_estate": "real_estate"}
FLAG_PROB = 0.70      # our number: below this a goal is flagged for review
SHORT_YEARS = 5       # our number: an essential goal this close should sit mostly in safe assets


def goals_file(d: Path) -> Path:
    return d / "goals.csv"


def read_goals(d: Path) -> list[dict]:
    f = goals_file(d)
    if not f.exists():
        return []
    with f.open(newline="", encoding="utf-8") as h:
        return list(csv.DictReader(h))


def write_goals(d: Path, rows: list[dict]) -> None:
    with goals_file(d).open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, GOAL_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def parse_shares(text: str, known: dict) -> list[tuple[str, Decimal]]:
    out = []
    for part in filter(None, (p.strip() for p in (text or "").split(","))):
        acct, _, share = part.partition(":")
        if acct not in known:
            raise FwError(f"unknown account {acct!r} in --accounts")
        s = Decimal(share) if share else Decimal(1)
        if not 0 < s <= 1:
            raise FwError(f"share for {acct} must be above 0 and at most 1, got {share}")
        out.append((acct, s))
    return out


def months_between(a, b) -> int:
    return max(0, (b.year - a.year) * 12 + b.month - a.month)


def goal_mix(d: Path, shares, bals, holds) -> dict[str, Decimal]:
    """Dollars per asset class behind one goal: holdings where recorded, else the account type's class."""
    acc = accounts(d)
    mix: dict[str, Decimal] = {}
    for acct, s in shares:
        hs = [h for h in holds if h["account"] == acct]
        if hs:
            for h in hs:
                mix[h["asset_class"]] = mix.get(h["asset_class"], Decimal(0)) + Decimal(h["value"]) * s
        elif acct in bals:
            cls = TYPE_CLASS.get(acc[acct]["type"], "other")
            mix[cls] = mix.get(cls, Decimal(0)) + Decimal(bals[acct]["value"]) * s
    return mix


def simulate(start: float, monthly: float, weights: dict[str, float], assume: dict, m_lo: int, m_hi: int,
             target: float, paths: int, seed: int) -> float:
    """Share of paths whose value reaches the target in any month of the window [m_lo, m_hi]."""
    mu = sum(w * assume[c][0] for c, w in weights.items())
    vol = sum(w * assume[c][1] for c, w in weights.items())  # full correlation: wider spread, on purpose
    m_mu, m_sd = math.log1p(mu) / 12 - (vol ** 2) / 24, vol / math.sqrt(12)
    rng = random.Random(seed)
    hits = 0
    for _ in range(paths):
        v = start
        if m_lo == 0 and v >= target:
            hits += 1
            continue
        for m in range(1, m_hi + 1):
            v = v * math.exp(rng.gauss(m_mu, m_sd)) + monthly
            if m >= m_lo and v >= target:
                hits += 1
                break
    return hits / paths


def cmd_goal_add(args) -> None:
    d = data_dir(args)
    rows = read_goals(d)
    if any(r["id"] == args.id for r in rows):
        raise FwError(f"goal {args.id!r} already exists")
    by = parse_date(args.by)
    earliest = parse_date(args.earliest) if args.earliest else by
    if earliest > by:
        raise FwError("--earliest is after --by")
    target = money(args.target)
    if target <= 0:
        raise FwError("--target must be above zero")
    parse_shares(args.accounts, accounts(d))
    rows.append({"id": args.id, "name": args.name or args.id, "target": str(target), "earliest": earliest.isoformat(),
                 "by": by.isoformat(), "class": args.cls, "accounts": args.accounts or "",
                 "monthly": str(money(args.monthly)) if args.monthly else "0", "note": args.note or ""})
    write_goals(d, rows)
    print(f"added goal {args.id}: {fmt(target)} between {earliest} and {by} ({args.cls})")


def goal_state(d: Path):
    rows = read_goals(d)
    if not rows:
        return None
    acc, now = accounts(d), today()
    bals, holds = latest_balances(d, now), latest_holdings(d, now)
    out = []
    used: dict[str, Decimal] = {}
    for r in sorted(rows, key=lambda r: (CLASSES.index(r["class"]), r["by"])):
        shares = parse_shares(r["accounts"], acc)
        for a, s in shares:
            used[a] = used.get(a, Decimal(0)) + s
        funded = sum((Decimal(bals[a]["value"]) * s for a, s in shares if a in bals), Decimal(0))
        out.append({**r, "shares": shares, "funded": funded, "mix": goal_mix(d, shares, bals, holds),
                    "m_lo": months_between(now, parse_date(r["earliest"])),
                    "m_hi": months_between(now, parse_date(r["by"]))})
    over = [f"{a} is promised {s:.0%} across goals" for a, s in used.items() if s > 1]
    return out, over


def cmd_goal_list(args) -> None:
    st = goal_state(data_dir(args))
    if st is None:
        print("no goals yet; add one with `fw.py goal add`")
        return
    rows, over = st
    print(f"{'goal':<14}{'class':<14}{'target':>14}{'funded':>14}{'gap':>14}{'months':>8}{'per month':>14}")
    for r in rows:
        gap = max(Decimal(r["target"]) - r["funded"], Decimal(0))
        per = gap / r["m_hi"] if r["m_hi"] else gap
        print(f"{r['id']:<14}{r['class']:<14}{fmt(Decimal(r['target'])):>14}{fmt(r['funded']):>14}{fmt(gap):>14}"
              f"{r['m_hi']:>8}{fmt(per):>14}")
    print("  per month = the gap spread over the months left, with no growth")
    for w in over:
        print(f"  warning: {w}")


def cmd_goal_check(args) -> None:
    st = goal_state(data_dir(args))
    if st is None:
        print("no goals yet; add one with `fw.py goal add`")
        return
    rows, over = st
    assume = dict(ASSUME)
    for a in args.assume or []:
        cls, _, rv = a.partition("=")
        if cls not in assume or ":" not in rv:
            raise FwError(f"--assume takes class=return:volatility, e.g. us_stock=0.05:0.16; got {a!r}")
        r_, v_ = rv.split(":")
        assume[cls] = (float(r_), float(v_))
    print(f"Goal check: {args.paths} paths, seed {args.seed}, monthly steps, today's dollars")
    for r in rows:
        total = sum(r["mix"].values(), Decimal(0))
        weights = {c: float(v / total) for c, v in r["mix"].items()} if total else {"cash": 1.0}
        p = simulate(float(r["funded"]), float(r["monthly"] or 0), weights, assume, r["m_lo"], r["m_hi"],
                     float(r["target"]), args.paths, args.seed)
        flags = []
        if p < FLAG_PROB:
            flags.append(f"below {FLAG_PROB:.0%}: talk the plan over")
        stock = sum(w for c, w in weights.items() if c in STOCK)
        if r["class"] == "essential" and r["m_hi"] < SHORT_YEARS * 12 and stock > 0.5:
            flags.append(f"essential goal under {SHORT_YEARS} years held mostly in stocks")
        if not r["shares"]:
            flags.append("no accounts assigned")
        mix = ", ".join(f"{c} {w:.0%}" for c, w in sorted(weights.items(), key=lambda x: -x[1]))
        print(f"  {r['id']:<14}{r['class']:<14}{p:>7.0%}  target {fmt(Decimal(r['target']))} in "
              f"{r['m_lo']}-{r['m_hi']} months, funded {fmt(r['funded'])} + {fmt(Decimal(r['monthly'] or 0))}/month; {mix}")
        for f in flags:
            print(f"    flag: {f}")
    for w in over:
        print(f"  warning: {w}")
    print("Assumptions (real yearly return / volatility; ours, not forecasts; override with --assume):")
    for c, (mu, vol) in assume.items():
        print(f"  {c:<12} {mu:.1%} / {vol:.1%}")
    print("  Classes treated as fully correlated (wider spread); no fees or taxes; a goal counts as reached the "
          "first month in its window that the value meets the target; holdings mix where recorded, else the "
          "account type.")
    print(DISCLAIMER)


def add_parsers(sub) -> None:
    g = sub.add_parser("goal", help="goals with a target, a date window and a priority class").add_subparsers(
        dest="sub", required=True)
    s = g.add_parser("add")
    s.add_argument("id")
    s.add_argument("--name")
    s.add_argument("--target", required=True, help="amount in today's dollars")
    s.add_argument("--by", required=True, help="latest date the money is needed")
    s.add_argument("--earliest", help="earliest date it may be needed (default --by)")
    s.add_argument("--class", dest="cls", required=True, choices=CLASSES)
    s.add_argument("--accounts", help="id[:share],... e.g. savings:0.5,brokerage")
    s.add_argument("--monthly", help="planned saving toward it per month")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_goal_add)
    g.add_parser("list").set_defaults(fn=cmd_goal_list)
    s = g.add_parser("check", help="seeded Monte Carlo chance of reaching each goal")
    s.add_argument("--paths", type=int, default=2000)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--assume", action="append", help="class=return:volatility, repeatable")
    s.set_defaults(fn=cmd_goal_check)
