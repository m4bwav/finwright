# Markets: one ticker's numbers, base rates and a sale

Read this when the user asks what a stock will do next ("will it bounce Monday", "is this the bottom", "dead cat bounce?"), how a holding has moved, how big a position should be, or what selling a lot costs in tax. Research: [market data sources and base rates](../../../research/2026-11-21-market-data-and-base-rates.md) (2026-11-21; entries marked [R] there were cited from memory and need a re-check before a figure is quoted).

## Getting prices

fw.py reads a daily price CSV with a header holding `date` and `close` (or `adj close`); `open`, `high`, `low` and `volume` add the gap, range and volume lines. Newest-first or oldest-first both work.

- `FW market fetch <ticker> [--years 5 | --start D] [--end D] [--replace]`: a read-only GET of Tiingo's end-of-day prices, adjusted for splits and dividends, into `<data>/markets/<TICKER>.csv`. Later pulls keep older cached days; after a split or dividend use `--replace` so the adjusted history lines up. Tiingo's free plan allows about 50 requests an hour and is for personal use, so never share the file.
- The key is the user's own free Tiingo token. `FW market key` prompts for it without echo and saves it in the OS keyring (needs `pip install keyring`); `TIINGO_API_KEY` in the shell works as a fallback. Never ask the user to paste the token into chat, never write it to a file, never put it in a URL.
- Without a key, the user can download a CSV from their broker's history export or a data site and keep it in their data folder.

## Commands

- `FW market stats <csv> --symbol <ticker> [--ipo-price P] [--after-hours P]`: returns over 1 day, 5 days, 1, 3 and 12 months; realized volatility annualised with the square root of 252 and the typical daily move; high, low and drawdown; the last gap; an after-hours price against the close; distance from the IPO price; volume against its prior 20-day average; 20, 50 and 200-day moving averages.
- `FW market bounce <csv> --drop 5 [--benchmark <index csv>]`: every day that closed down at least 5%, and how many were higher 1, 2 and 5 trading days later, with the median move, next to the share of all days that were up. Under 30 cases it says the sample is thin.
- `FW market range <csv> --days 5 [--paths 5000 --seed 1]`: a seeded bootstrap in five-day blocks of the ticker's own daily returns: the 5th to 95th percentile of the next N days and the share of resamples that ended higher. Needs at least 30 returns.
- `FW market sale --bought D --cost C --shares N --price P [--sold D] [--bought-again D ...]`: gain or loss, short or long term (long-term means held more than one year) and the date it turns long-term, the 61-day wash-sale window and any listed purchase inside it.
- Sizing: `FW position <amount> --symbol <ticker>` (concentration bands against investable assets; see [new-listings.md](new-listings.md)).

## What the research says, to quote with the numbers

- **Short-term reversal is small and unreliable.** Stocks that fell 10% or more in a day rose on average a little under 2% over the next two days in one older study, much of it bid-ask bounce, and drops with news tend to keep drifting. After costs there is little edge. So a "bounce Monday" call is close to a coin flip unless this ticker's own `market bounce` count says otherwise, with enough cases.
- **New listings:** a first-day pop of about 18% on average, then years of trailing similar companies; lock-up expiry has averaged a fall of one to three percent around the date; analyst coverage starting at the end of the quiet period has averaged a small rise. Averages over hundreds of listings, not a forecast for one.
- **A broad index is up on a little over half of days**, and about the same after a down day. Compute it from the benchmark file instead of quoting a fixed figure.

## How to answer "will it go up / bounce / fall"

1. Run `market stats` and `market bounce` (with a broad-index benchmark when the user has one) and `market range` for the horizon they asked about.
2. Lead with the count: "of N past drops this size, M were higher two days later (P%); any day: Q%". If P is within about ten points of 50% or N is under 30, say it is a coin flip on this evidence. Never present a coin flip as a likely outcome.
3. Give the range as amounts in the user's own position ("a 5-to-95 range of roughly -12% to +11% over five days, about $X either way on your holding"), per rule 17. No risk labels.
4. Scenarios, each with its evidence and what would prove it wrong (a close back above the prior high; earnings; lock-up date from `FW ipo`).
5. Advice per rule 15: what you would do in their place, sized with `FW position` against investable assets; a sale with `market sale` for the tax side, never an order. Name what flips the call.
6. End with the disclaimer: past moves, not a forecast, not personalised advice; they act at their own risk and could lose some or all of it.

## Tax facts for a sale (check before quoting)

- Long-term means held more than one year; short-term gains are taxed as ordinary income.
- Wash sale (IRS Pub. 550): a loss is disallowed if the same or a substantially identical security is bought within 30 days before or after the sale, in any account the user or their spouse controls, an IRA included; the loss is added to the new shares' basis and their holding period carries over.
- Losses offset gains, then up to three thousand dollars a year of ordinary income; the rest carries forward.
- 2026 long-term rate brackets are in the research file from a secondary source; they are not in `data/rates.json` yet, so do not quote them until the IRS revenue procedure has been read and the entry added.
