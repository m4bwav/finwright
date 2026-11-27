"""finwright markets: read-only numbers for one ticker from a daily price file, so questions like "will it bounce
after this drop" get counts and ranges instead of guesses.

`market stats` prints returns over windows, realized volatility, drawdown from the high, the last gap, an
after-hours change, distance from an IPO price, volume against its average and moving averages. `market bounce`
counts how often a drop of at least X% in this ticker (and in a benchmark file) was followed by an up close after
1, 2 and 5 trading days. `market range` bootstraps next-N-day returns from the ticker's own daily returns with a
seed, in blocks of five days. `market sale` gives the holding period, the wash-sale window and the gain or loss of a lot.

Input is a CSV with a header holding at least `date` and `close` (and optionally `open`, `high`, `low`,
`volume`), oldest or newest first. The user supplies the file, or `market fetch` writes one: the only network
call here, a read-only GET of Tiingo's end-of-day prices with the user's own free key (kept in the OS keyring
through the optional `keyring` package, else the TIINGO_API_KEY variable; never in a file). Standard library
only otherwise; prices and money in Decimal, ratios of returns in float.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
import re
import random
import statistics
from decimal import Decimal, InvalidOperation
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from fw import DISCLAIMER, VERSION, FwError, data_dir, fmt, money, parse_date, today

THIN = 30            # our number: fewer past cases than this and a base rate is called thin
TRADING_DAYS = 252   # annualising factor for daily volatility
BLOCK = 5            # our number: days per bootstrap block (a trading week)
WINDOWS = (("1 day", 1), ("5 days", 5), ("1 month", 21), ("3 months", 63), ("1 year", 252))
TIINGO = "https://api.tiingo.com/tiingo/daily/{}/prices"
KEY_SERVICE, KEY_USER = "finwright", "tiingo"
SYMBOL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,11}$")
COLS = ("date", "open", "high", "low", "close", "volume")
NOT_ADVICE = "Past moves in this file, not a forecast and not personalised advice."


def read_prices(path: str) -> list[dict]:
    """Rows sorted oldest first: date, close (Decimal) and whichever of open/high/low/volume exist."""
    p = Path(path)
    if not p.is_file():
        raise FwError(f"no price file at {path}")
    with p.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        heads = {h.strip().lower(): h for h in reader.fieldnames or []}
        if "date" not in heads or not ({"close", "adj close"} & heads.keys()):
            raise FwError(f"{path}: need a header with date and close columns")
        ccol = heads.get("adj close") or heads["close"]
        rows = []
        for r in reader:
            raw = (r.get(ccol) or "").strip()
            if not raw or raw.lower() in ("null", "nan", "-"):
                continue
            try:
                row = {"date": parse_date(r[heads["date"]].strip()[:10]), "close": Decimal(raw)}
                for k in ("open", "high", "low", "volume"):
                    v = (r.get(heads[k]) or "").strip() if k in heads else ""
                    if v and v.lower() not in ("null", "nan", "-"):
                        row[k] = Decimal(v)
            except (InvalidOperation, ValueError) as e:
                raise FwError(f"{path}: bad row {r}: {e}") from None
            if row["close"] <= 0:
                raise FwError(f"{path}: close must be positive on {row['date']}")
            rows.append(row)
    rows.sort(key=lambda x: x["date"])
    if len(rows) < 2:
        raise FwError(f"{path}: need at least two days of prices")
    for a, b in zip(rows, rows[1:]):
        if a["date"] == b["date"]:
            raise FwError(f"{path}: {a['date']} appears twice")
    return rows


def returns(rows: list[dict]) -> list[float]:
    return [float(b["close"] / a["close"]) - 1 for a, b in zip(rows, rows[1:])]


def pc(x: float) -> str:
    return f"{x * 100:+.1f}%"


def realized_vol(rets: list[float]) -> float | None:
    """Annualised standard deviation of daily log returns; None with fewer than two returns."""
    logs = [math.log1p(r) for r in rets]
    return statistics.stdev(logs) * math.sqrt(TRADING_DAYS) if len(logs) >= 2 else None


def sma(rows: list[dict], n: int) -> Decimal | None:
    return sum((r["close"] for r in rows[-n:]), Decimal(0)) / n if len(rows) >= n else None


def stats(rows: list[dict], ipo_price: Decimal | None = None, after_hours: Decimal | None = None) -> dict:
    last, rets = rows[-1], returns(rows)
    out = {"as_of": last["date"].isoformat(), "close": last["close"], "days": len(rows), "windows": {}}
    for name, n in WINDOWS:
        if len(rows) > n:
            out["windows"][name] = float(last["close"] / rows[-1 - n]["close"]) - 1
    out["vol_1m"] = realized_vol(rets[-21:]) if len(rets) >= 21 else None
    out["vol_3m"] = realized_vol(rets[-63:]) if len(rets) >= 63 else None
    out["vol_all"] = realized_vol(rets)
    hi = max(rows, key=lambda r: r.get("high", r["close"]))
    lo = min(rows, key=lambda r: r.get("low", r["close"]))
    out["high"], out["high_date"] = hi.get("high", hi["close"]), hi["date"].isoformat()
    out["low"], out["low_date"] = lo.get("low", lo["close"]), lo["date"].isoformat()
    out["drawdown"] = float(last["close"] / out["high"]) - 1
    if "open" in last:
        out["gap"] = float(last["open"] / rows[-2]["close"]) - 1
    if after_hours is not None:
        out["after_hours"] = float(after_hours / last["close"]) - 1
    if ipo_price is not None:
        out["vs_ipo"] = float(last["close"] / ipo_price) - 1
    vols = [r["volume"] for r in rows[-21:-1] if "volume" in r]
    if "volume" in last and len(vols) >= 5 and sum(vols) > 0:
        out["volume_ratio"] = float(last["volume"] / (sum(vols) / len(vols)))
    out["sma"] = {n: sma(rows, n) for n in (20, 50, 200)}
    return out


def bounce(rows: list[dict], drop: float, horizons=(1, 2, 5)) -> dict:
    """After each day whose close fell at least `drop` (0.05 = 5%), how often was the close `h` days later higher."""
    rets = returns(rows)
    closes = [r["close"] for r in rows]
    res = {"drop": drop, "events": 0, "horizons": {}}
    idx = [i + 1 for i, r in enumerate(rets) if r <= -drop]  # index of the drop day's close
    res["events"] = len(idx)
    for h in horizons:
        fwd = [float(closes[i + h] / closes[i]) - 1 for i in idx if i + h < len(closes)]
        res["horizons"][h] = {"n": len(fwd), "up": sum(1 for f in fwd if f > 0),
                              "median": statistics.median(fwd) if fwd else None}
    allfwd = {h: [float(closes[i + h] / closes[i]) - 1 for i in range(len(closes) - h)] for h in horizons}
    res["base"] = {h: (sum(1 for f in v if f > 0) / len(v) if v else None) for h, v in allfwd.items()}
    return res


def bootstrap(rows: list[dict], days: int, paths: int, seed: int) -> dict:
    """Seeded block bootstrap of `days`-day compound returns from the file's daily returns."""
    if days < 1 or paths < 100:
        raise FwError("--days must be at least 1 and --paths at least 100")
    rets = returns(rows)
    if len(rets) < THIN:
        raise FwError(f"only {len(rets)} daily returns in the file; need at least {THIN} to bootstrap")
    rng = random.Random(seed)
    block = min(BLOCK, days)  # runs of consecutive days keep some of the clustering single-day draws lose

    def path() -> float:
        out: list[float] = []
        while len(out) < days:
            i = rng.randrange(len(rets) - block + 1)
            out.extend(rets[i:i + block])
        return math.prod(1 + r for r in out[:days]) - 1

    sims = sorted(path() for _ in range(paths))
    q = lambda p: sims[min(len(sims) - 1, int(p * len(sims)))]  # noqa: E731
    return {"days": days, "paths": paths, "seed": seed, "sample": len(rets),
            "pcts": {p: q(p / 100) for p in (5, 25, 50, 75, 95)},
            "up": sum(1 for s in sims if s > 0) / len(sims)}


def sale(bought: dt.date, sold: dt.date, shares: Decimal, cost: Decimal, price: Decimal,
         buys_near: list[dt.date]) -> dict:
    """Holding period, gain and wash-sale exposure of selling one lot (IRS Pub. 550)."""
    if sold < bought:
        raise FwError("the sale date is before the purchase date")
    try:
        anniversary = bought.replace(year=bought.year + 1)
    except ValueError:  # bought on 29 February
        anniversary = dt.date(bought.year + 1, 3, 1)
    long_term = sold > anniversary  # held more than one year: the day after the anniversary
    gain = (price - cost) * shares
    lo, hi = sold - dt.timedelta(days=30), sold + dt.timedelta(days=30)
    hits = sorted(b for b in buys_near if lo <= b <= hi and b != bought)
    return {"long_term": long_term, "long_from": anniversary + dt.timedelta(days=1), "gain": gain,
            "window": (lo, hi), "wash": gain < 0 and bool(hits), "hits": hits}


# ---------- fetch (read-only, the user's own Tiingo key) ----------

_urlopen = urllib.request.urlopen  # tests replace this; no network in tests


def tiingo_key() -> str:
    try:
        import keyring  # optional third-party package; the OS keyring behind it holds the key
        k = keyring.get_password(KEY_SERVICE, KEY_USER)
        if k:
            return k
    except Exception:  # not installed, or no keyring backend on this machine
        pass
    k = os.environ.get("TIINGO_API_KEY", "").strip()
    if not k:
        raise FwError("no Tiingo key: run `fw.py market key` (needs `pip install keyring`) or set TIINGO_API_KEY "
                      "for this shell. A free key comes from tiingo.com (account, API token).")
    return k


def fetch_tiingo(symbol: str, start: dt.date, end: dt.date, key: str) -> list[dict]:
    """Daily rows from Tiingo, split- and dividend-adjusted, oldest first. GET only."""
    if not SYMBOL.match(symbol):
        raise FwError(f"not a ticker: {symbol!r}")
    q = urllib.parse.urlencode({"startDate": start.isoformat(), "endDate": end.isoformat(), "format": "json"})
    url = TIINGO.format(urllib.parse.quote(symbol.lower())) + "?" + q
    req = urllib.request.Request(url, headers={"Authorization": f"Token {key}", "Accept": "application/json",
                                               "User-Agent": f"finwright/{VERSION}"})
    try:
        with _urlopen(req, timeout=30) as h:
            data = json.loads(h.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        why = {401: "the key was refused", 403: "the key was refused", 404: f"no ticker {symbol.upper()}",
               429: "over the free plan's request limit; try again in an hour"}.get(e.code, f"HTTP {e.code}")
        raise FwError(f"Tiingo: {why}") from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise FwError(f"Tiingo unreachable: {e}") from None
    if isinstance(data, dict):  # an error object instead of rows
        raise FwError(f"Tiingo: {data.get('detail') or data}")
    rows = []
    for r in data:
        try:
            row = {"date": parse_date(str(r["date"])[:10]), "close": Decimal(str(r.get("adjClose", r["close"])))}
            for k, src in (("open", "adjOpen"), ("high", "adjHigh"), ("low", "adjLow"), ("volume", "adjVolume")):
                v = r.get(src, r.get(k))
                if v is not None:
                    row[k] = Decimal(str(v))
        except (KeyError, InvalidOperation, ValueError, TypeError) as e:
            raise FwError(f"Tiingo: unexpected row {r}: {e}") from None
        rows.append(row)
    return sorted(rows, key=lambda x: x["date"])


def write_prices(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([r["date"].isoformat()] + [str(r[k]) if k in r else "" for k in COLS[1:]])
    tmp.replace(path)


# ---------- commands ----------

def cmd_stats(args) -> None:
    rows = read_prices(args.prices)
    s = stats(rows, money(args.ipo_price) if args.ipo_price else None,
              money(args.after_hours) if args.after_hours else None)
    label = args.symbol.upper() if args.symbol else Path(args.prices).stem
    print(f"{label}: close {fmt(s['close'])} on {s['as_of']} ({s['days']} trading days in the file)")
    print("  Returns: " + ", ".join(f"{k} {pc(v)}" for k, v in s["windows"].items()))
    vols = [(n, s[k]) for n, k in (("1 month", "vol_1m"), ("3 months", "vol_3m"), ("whole file", "vol_all"))
            if s[k] is not None]
    if vols:
        print("  Realized volatility, annualised: " + ", ".join(f"{n} {v * 100:.0f}%" for n, v in vols)
              + f" (a typical day moves about {vols[0][1] / math.sqrt(TRADING_DAYS) * 100:.1f}%)")
    print(f"  High {fmt(s['high'])} on {s['high_date']}, low {fmt(s['low'])} on {s['low_date']}; "
          f"{pc(s['drawdown'])} from the high")
    if "gap" in s:
        print(f"  Last open against the prior close: {pc(s['gap'])}")
    if "after_hours" in s:
        print(f"  After-hours price against the close: {pc(s['after_hours'])}")
    if "vs_ipo" in s:
        print(f"  Against the IPO price {fmt(money(args.ipo_price))}: {pc(s['vs_ipo'])}")
    if "volume_ratio" in s:
        print(f"  Volume {s['volume_ratio']:.1f}x its average of the prior 20 days")
    avg = [f"{n}-day {fmt(v)} ({'above' if s['close'] > v else 'below'})" for n, v in s["sma"].items() if v]
    if avg:
        print("  Moving averages, close is: " + ", ".join(avg))
    print(f"  {NOT_ADVICE} Command: fw.py market stats")


def _print_bounce(label: str, b: dict) -> None:
    print(f"{label}: {b['events']} days closed down {b['drop'] * 100:g}% or more")
    for h, v in b["horizons"].items():
        base = b["base"][h]
        if v["n"]:
            print(f"  {h} day{'s' if h > 1 else ''} later: up {v['up']} of {v['n']} ({v['up'] / v['n'] * 100:.0f}%), "
                  f"median {pc(v['median'])}; any day in the file: up {base * 100:.0f}%")
    n = min((v["n"] for v in b["horizons"].values()), default=0)
    if n < THIN:
        print(f"  Thin sample: {n} cases is too few to tell a pattern from chance (we want {THIN} or more).")


def cmd_bounce(args) -> None:
    drop = float(money(args.drop)) / 100
    if not 0 < drop < 1:
        raise FwError("--drop is a percent above 0 and below 100")
    _print_bounce(args.symbol.upper() if args.symbol else Path(args.prices).stem, bounce(read_prices(args.prices), drop))
    if args.benchmark:
        _print_bounce(f"Benchmark {Path(args.benchmark).stem}", bounce(read_prices(args.benchmark), drop))
    print("  A share near 50% is a coin flip, whatever the story. " + NOT_ADVICE + " Command: fw.py market bounce")


def cmd_range(args) -> None:
    rows = read_prices(args.prices)
    b = bootstrap(rows, args.days, args.paths, args.seed)
    label = args.symbol.upper() if args.symbol else Path(args.prices).stem
    last = rows[-1]["close"]
    print(f"{label}: next {b['days']} trading days, {b['paths']} resamples of {b['sample']} past daily returns "
          f"(seed {b['seed']}), from {fmt(last)}:")
    for p, v in b["pcts"].items():
        print(f"  {p:>2}th percentile {pc(v):>7}  ({fmt((last * Decimal(str(1 + v))).quantize(Decimal('0.01')))})")
    print(f"  Ended higher in {b['up'] * 100:.0f}% of resamples.")
    print("  Assumes the past days in the file are a fair sample (drawn in five-day blocks); it misses news, "
          "earnings and regime changes, and a short history understates the tails. " + NOT_ADVICE
          + " Command: fw.py market range")


def long_rate_line(year: int) -> str:
    """The long-term rate thresholds for the sale year from rates.json, or a refusal to guess."""
    from fw import load_rates
    cg = load_rates().get("capital_gains", {}).get(str(year))
    if not cg:
        return f"No {year} long-term rate brackets in rates.json; refresh the skill, do not guess."
    v = cg["values"]
    def pair(k):
        return f"{fmt(money(v[k]['zero_up_to']))} / {fmt(money(v[k]['fifteen_up_to']))}"
    return (f"{year} long-term rate by taxable income: 0% up to, then 15% up to (20% above): single {pair('single')}, "
            f"joint {pair('married_joint')}, head of household {pair('head_of_household')}; plus 3.8% NIIT above "
            f"$200,000 / $250,000 MAGI. Source: Rev. Proc. 2025-32 (rates.json, checked {cg['checked']}).")


def cmd_sale(args) -> None:
    shares = money(args.shares)
    if shares <= 0:
        raise FwError("--shares must be positive")
    sold = parse_date(args.sold) if args.sold else today()
    r = sale(parse_date(args.bought), sold, shares, money(args.cost), money(args.price),
             [parse_date(x) for x in args.bought_again or []])
    word = "gain" if r["gain"] >= 0 else "loss"
    print(f"Selling {shares} shares bought {args.bought} at {fmt(money(args.cost))}, at {fmt(money(args.price))} "
          f"on {sold.isoformat()}: {word} {fmt(abs(r['gain']))}, "
          + ("long-term (held more than one year)." if r["long_term"]
             else f"short-term (taxed as ordinary income); long-term from {r['long_from'].isoformat()}."))
    lo, hi = r["window"]
    if r["gain"] < 0:
        print(f"  Wash-sale window: {lo.isoformat()} to {hi.isoformat()}. Buying the same or a substantially "
              "identical security in it (any account, an IRA or a spouse's included) disallows the loss and adds it "
              "to the new shares' basis.")
        if r["wash"]:
            print("  Purchases in the window: " + ", ".join(d.isoformat() for d in r["hits"])
                  + ": this loss would be a wash sale, at least in part.")
    elif r["long_term"]:
        print("  " + long_rate_line(sold.year))
    print("  Check the lot and basis on the broker's 1099-B; filing questions go to a CPA or enrolled agent. "
          + DISCLAIMER)


def cmd_fetch(args) -> None:
    sym = args.symbol.upper()
    end = parse_date(args.end) if args.end else today()
    start = parse_date(args.start) if args.start else end - dt.timedelta(days=round(365.25 * args.years))
    if start > end:
        raise FwError("--start is after --end")
    out = Path(args.out) if args.out else data_dir(args) / "markets" / f"{sym}.csv"
    new = fetch_tiingo(sym, start, end, tiingo_key())
    if not new:
        raise FwError(f"Tiingo returned no prices for {sym} from {start} to {end}")
    have = {r["date"]: r for r in read_prices(str(out))} if out.is_file() else {}
    # Older cached days stay unless --replace; after a split or dividend, adjusted history shifts, so replace then.
    merged = {**({} if args.replace else {d: r for d, r in have.items() if d < new[0]["date"]}),
              **{r["date"]: r for r in new}}
    rows = [merged[d] for d in sorted(merged)]
    write_prices(out, rows)
    print(f"{sym}: {len(new)} days from Tiingo ({new[0]['date']} to {new[-1]['date']}), adjusted for splits and "
          f"dividends; {len(rows)} days in {out}")
    print(f"  Next: fw.py market stats {out} --symbol {sym}. Tiingo data is for personal use; do not share the file.")


def cmd_key(args) -> None:
    try:
        import keyring
    except ImportError:
        raise FwError("the keyring package is missing: pip install keyring (or set TIINGO_API_KEY per shell)") from None
    import getpass
    if args.delete:
        keyring.delete_password(KEY_SERVICE, KEY_USER)
        print("Tiingo key removed from the keyring.")
        return
    k = getpass.getpass("Tiingo API token (not shown): ").strip()
    if not re.fullmatch(r"[A-Za-z0-9]{20,64}", k):
        raise FwError("that does not look like a Tiingo token (letters and digits)")
    keyring.set_password(KEY_SERVICE, KEY_USER, k)
    print(f"Tiingo key saved in the OS keyring as {KEY_SERVICE}/{KEY_USER}.")


def add_parsers(sub) -> None:
    m = sub.add_parser("market", help="read-only numbers for one ticker from a daily price CSV"
                       ).add_subparsers(dest="sub", required=True)
    s = m.add_parser("stats", help="returns, volatility, drawdown, gap, IPO distance, volume, moving averages")
    s.add_argument("prices", help="CSV with date and close columns")
    s.add_argument("--symbol")
    s.add_argument("--ipo-price")
    s.add_argument("--after-hours", help="an after-hours price to compare with the last close")
    s.set_defaults(fn=cmd_stats)
    s = m.add_parser("bounce", help="how often a drop of X%% was followed by up closes")
    s.add_argument("prices")
    s.add_argument("--drop", required=True, help="percent fall in one day, e.g. 5")
    s.add_argument("--benchmark", help="a second price CSV, e.g. a broad index fund")
    s.add_argument("--symbol")
    s.set_defaults(fn=cmd_bounce)
    s = m.add_parser("range", help="seeded bootstrap of next-N-day returns from the file's own history")
    s.add_argument("prices")
    s.add_argument("--days", type=int, default=5)
    s.add_argument("--paths", type=int, default=5000)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--symbol")
    s.set_defaults(fn=cmd_range)
    s = m.add_parser("sale", help="holding period, gain and wash-sale window of selling a lot")
    s.add_argument("--bought", required=True)
    s.add_argument("--cost", required=True, help="cost per share")
    s.add_argument("--shares", required=True)
    s.add_argument("--price", required=True, help="sale price per share")
    s.add_argument("--sold", help="sale date (default today)")
    s.add_argument("--bought-again", nargs="+", help="dates of other purchases of the same security")
    s.set_defaults(fn=cmd_sale)
    s = m.add_parser("fetch", help="download daily prices from Tiingo (read-only, your own key) into the data folder")
    s.add_argument("symbol")
    s.add_argument("--years", type=float, default=5, help="how far back when --start is not given (default 5)")
    s.add_argument("--start")
    s.add_argument("--end", help="default today")
    s.add_argument("--out", help="CSV to write (default <data>/markets/<SYMBOL>.csv)")
    s.add_argument("--replace", action="store_true", help="drop cached days older than this pull")
    s.set_defaults(fn=cmd_fetch)
    s = m.add_parser("key", help="save your Tiingo API token in the OS keyring (prompted, never echoed)")
    s.add_argument("--delete", action="store_true")
    s.set_defaults(fn=cmd_key)
