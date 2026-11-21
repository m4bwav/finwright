# Market data sources and base rates for read-only stock analysis

Checked: 2026-11-21. Scope: what a local Python stdlib script in finwright can call for daily prices, published base rates the plugin may quote, US tax rules for lots, and volatility method notes. Read-only analysis, no trading.

Verification key: **[V]** = page or search result read on 2026-11-21. **[R]** = canonical primary source cited from prior knowledge, not re-read today; re-verify before quoting a number in user-facing output.

## 1. Daily price history sources

### Stooq CSV
- URL format: `https://stooq.com/q/d/l/?s=aapl.us&i=d` (optional `d1=YYYYMMDD&d2=YYYYMMDD`). US tickers take the `.us` suffix. [V] https://www.quantstart.com/articles/an-introduction-to-stooq-pricing-data/
- **No longer keyless.** Since March 2026 downloads need a per-user `apikey` obtained by solving a captcha at `https://stooq.com/q/d/?s=^dji&get_apikey`; a keyless request returned "Access denied" in October 2026. [V] https://opserver.de/ubb7/ubbthreads.php?ubb=showflat&Number=489362 and https://financialliterature.com/data/stooq/
- Scripted clients are also reported to get a JavaScript proof-of-work page instead of CSV, plus an unpublished daily hit quota. [V] https://financialliterature.com/data/stooq/
- Format: CSV Date,Open,High,Low,Close,Volume. End-of-day only, no after-hours. Terms: no published API terms. Reliability for a stdlib script: now poor.

### Yahoo Finance chart endpoint
- `https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1y&interval=1d` (query2 is a mirror). Undocumented, no key; returns JSON with timestamps, OHLCV and adjclose; `includePrePost=true` adds pre/post-market bars on intraday intervals. Behaviour seen widely in open-source clients such as yfinance. [R] https://github.com/ranaroussi/yfinance
- Needs a browser-like User-Agent; endpoints have intermittently required a cookie/crumb and returned HTTP 429 under load. [R] https://github.com/ranaroussi/yfinance/issues
- Terms: Yahoo's Terms of Service forbid automated access/scraping not expressly permitted and the yfinance README states the data is "intended for personal use only" and points to Yahoo's terms. [R] https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html and https://github.com/ranaroussi/yfinance
- Verdict: works for personal use at the user's own risk; a public plugin should not make it the default or bundle it silently. Offer as opt-in with a terms warning.

### Alpha Vantage
- Free key required (instant signup). Free tier: 25 requests per day. `TIME_SERIES_DAILY` free; adjusted daily is premium. JSON or CSV (`datatype=csv`). [R] https://www.alphavantage.co/support/#api-key and https://www.alphavantage.co/premium/
- Terms allow personal use; redistribution restricted. [R] https://www.alphavantage.co/terms_of_service/
- Good fit: each user brings own key; 25/day is enough for a small watchlist with local caching.

### Tiingo
- Free key required. Free plan limits (as published): about 50 requests/hour, 1,000/day, 500 unique symbols/month; end-of-day prices with adjusted fields; IEX intraday also available. JSON or CSV. [R] https://www.tiingo.com/about/pricing and https://www.tiingo.com/documentation/end-of-day
- Free plan is for personal/internal use; redistribution needs a commercial plan. [R] https://www.tiingo.com/about/pricing
- Strong fit: generous limits, documented API, adjusted closes.

### Nasdaq Data Link (ex-Quandl)
- Free key; free US equity EOD dataset (WIKI) was discontinued in 2018; current equity prices are paid. [R] https://data.nasdaq.com/databases/WIKIP and https://docs.data.nasdaq.com/
- Not useful for free daily stock prices.

### SEC EDGAR
- Filings and XBRL facts only (no prices). Keyless; must send a descriptive `User-Agent` with contact info; max 10 requests per second. Public domain US government data. [R] https://www.sec.gov/os/accessing-edgar-data and https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Use for fundamentals, IPO dates (S-1/424B), lockup terms from prospectus.

### FRED
- Free key for the API; also keyless CSV `https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500`. Series SP500 covers only the last 10 years (licensing) and is index level, not total return. Terms permit use with attribution; some series carry third-party copyright. [R] https://fred.stlouisfed.org/series/SP500 and https://fred.stlouisfed.org/legal/
- Use for benchmarks and risk-free rate (DGS3MO), not stocks.

### After-hours data
Only Yahoo (`includePrePost`) and Tiingo IEX intraday give extended-hours figures among these; EOD sources give regular-session closes. [R] sources above.

### Recommendation (ranked)
1. **Tiingo** (user's own free key): documented, adjusted EOD, generous limits, terms clear for personal use.
2. **Alpha Vantage** (user's own free key): fallback; 25/day means cache aggressively.
3. **Yahoo chart endpoint**: opt-in only, personal use, explicit terms warning, expect breakage.
4. **Stooq**: only if the user pastes their captcha-issued apikey; scripted access unreliable since 2026.
5. **FRED** for benchmarks, **SEC EDGAR** for filings/IPO facts. Skip Nasdaq Data Link.
All: cache locally, never ship a shared key in the public repo.

## 2. Published base rates

### Short-term reversal
- Jegadeesh (1990): monthly returns negatively autocorrelated; decile spread of about 2.5% per month from a one-month reversal strategy. [R] Journal of Finance 45(3), https://doi.org/10.1111/j.1540-6261.1990.tb05110.x
- Lehmann (1990): weekly losers outperform weekly winners the following week; contrarian portfolio profits on the order of 1.2-1.8% per week before costs, largely eaten by bid-ask bounce and costs. [R] QJE 105(1), https://doi.org/10.2307/2937816
- Cox and Peterson (1994): after single-day drops of 10%+ in large stocks, reversal over days 1-3 is mostly explained by bid-ask bounce; the stocks then underperform over days 4-20 (no overreaction). [R] Journal of Finance 49(1), https://doi.org/10.1111/j.1540-6261.1994.tb04427.x
- Bremer and Sweeney (1991): Fortune 500 stocks falling 10%+ in a day rebounded about 1.8% over the next two days. [R] Journal of Finance 46(2), https://doi.org/10.1111/j.1540-6261.1991.tb02688.x
- Chan (2003): large price moves without news show reversal; moves with public news show drift (continuation). [R] Journal of Financial Economics 70(2), https://doi.org/10.1016/S0304-405X(03)00146-6
- Nagel (2012): short-term reversal profits behave like liquidity-provision returns, highest when volatility (VIX) is high. [R] Review of Financial Studies 25(7), https://doi.org/10.1093/rfs/hhs066
- Plugin takeaway: a 1-3 day bounce of about 1-2% after a big drop is a documented average, but small after costs, smaller with news, and followed by drift in some samples. Not a reliable per-stock signal.

### Dead cat bounce
- Most-cited work is the Cox-Peterson and Chan results above. A study framed explicitly as "dead cat bounce" (Fischer et al.) could not be verified on 2026-11-21; do not cite it until located. [V: search not attempted further]

### IPOs
- First-day return: average about 18-19% for US IPOs 1980-2024 (equal-weighted). [R] Jay Ritter, IPO data, https://site.warrington.ufl.edu/ritter/ipo-data/
- Long-run underperformance: Ritter (1991) found 1975-84 IPOs returned about 34% over three years vs about 61% for size/industry-matched firms. [R] Journal of Finance 46(1), https://doi.org/10.1111/j.1540-6261.1991.tb03743.x
- Loughran and Ritter (1995): 1970-90 IPOs averaged about 5% per year over five years vs about 12% for size-matched non-issuers. [R] Journal of Finance 50(1), https://doi.org/10.1111/j.1540-6261.1995.tb05166.x
- Ritter's updated tables show 3-year buy-and-hold returns for IPOs trailing market and style benchmarks on average, with large variation by era. [R] https://site.warrington.ufl.edu/ritter/ipo-data/
- Lockup expiry: Field and Hanka (2001) found a statistically significant abnormal return of about -1 to -3% (roughly -1.9% on average over a three-day window) around lockup expiration, with volume up about 40%; bigger for VC-backed firms. [R] Journal of Finance 56(2), https://doi.org/10.1111/0022-1082.00345
- Quiet period expiry: Bradley, Jordan and Ritter (2003) found about +4% abnormal return over five days around the quiet-period end (25 days then) for firms receiving analyst initiations, near zero otherwise. [R] Journal of Finance 58(1), https://doi.org/10.1111/1540-6261.00517
- Note: SEC rule changes (2005 offering reform, JOBS Act 2012) shortened/changed quiet periods; current practice is 10 days for EGCs' underwriters by FINRA rule 2241, 25 days typical. [R] https://www.finra.org/rules-guidance/rulebooks/finra-rules/2241

### Daily up-rate of the S&P 500
- The S&P 500 closes higher on roughly 53% of trading days over long samples (about 53-54% since 1950). Computable directly from FRED SP500 or any EOD series; the plugin should compute its own figure from data rather than quote a constant. [R] https://fred.stlouisfed.org/series/SP500
- After down days: daily index returns have weak, era-dependent autocorrelation (slightly positive pre-1990s, slightly negative since), so the next-day up probability after a down day sits near the unconditional ~53%. Compute from data; do not quote a fixed edge. [R] Lo and MacKinlay (1988), Review of Financial Studies 1(1), https://doi.org/10.1093/rfs/1.1.41

## 3. US tax rules relevant to lots

### Wash sale (IRS Publication 550)
- A loss is disallowed if, within 30 days before or after the sale (a 61-day window), the taxpayer buys substantially identical stock or securities, acquires them in a fully taxable trade, or acquires a contract or option to buy them. Purchases in an IRA or Roth IRA also trigger it. [R] https://www.irs.gov/publications/p550 (section "Wash Sales")
- The disallowed loss is added to the cost basis of the new shares, and the holding period of the old shares is added to the new shares' holding period. [R] same
- "Substantially identical" is not defined numerically; stock of a different company is generally not substantially identical. [R] same

### Holding period
- Long-term if held more than one year; one year or less is short-term. Count from the day after acquisition through the day of sale. [R] https://www.irs.gov/publications/p550 and https://www.irs.gov/taxtopics/tc409
- Short-term gains are taxed at ordinary rates. [R] https://www.irs.gov/taxtopics/tc409

### 2026 long-term capital gains thresholds (Rev. Proc. 2025-32, section 4.03), taxable income
| Filing status | 0% up to | 15% up to | 20% above |
|---|---|---|---|
| Single | $49,450 | $545,500 | $545,500 |
| Married filing jointly / surviving spouse | $98,900 | $613,700 | $613,700 |
| Married filing separately | $49,450 | $306,850 | $306,850 |
| Head of household | $66,200 | $579,600 | $579,600 |
| Estates and trusts | $3,300 | $16,250 | $16,250 |

[V] https://www.currentfederaltaxdevelopments.com/blog/2025/10/9/2026-inflation-adjustments-for-tax-professionals-revenue-procedure-2025-32-analysis ; primary: https://www.irs.gov/pub/irs-drop/rp-25-32.pdf [R]
- 2025 comparison: single 0% ceiling $48,350, 15% ceiling $533,400. [V] same secondary source
- Also applies: 3.8% net investment income tax above $200,000 (single) / $250,000 (MFJ) modified AGI; these thresholds are not indexed. [R] https://www.irs.gov/taxtopics/tc559
- Capital loss deduction limit against ordinary income: three thousand dollars (half that married filing separately), carryforward of the rest. [R] https://www.irs.gov/taxtopics/tc409

## 4. Volatility and bootstrap notes

- Realized volatility: standard deviation of daily log returns times sqrt(252) (about 252 US trading days per year); weekly uses sqrt(52), monthly sqrt(12). The square-root-of-time rule assumes i.i.d. returns; autocorrelation and volatility clustering make it biased over long horizons. [R] Hull, Options, Futures and Other Derivatives (ch. on volatility); Lo (2002), "The Statistics of Sharpe Ratios", Financial Analysts Journal, https://doi.org/10.2469/faj.v58.n4.2453
- Use log returns from adjusted closes so splits and dividends do not create fake jumps.
- Bootstrap caveats:
  - Plain i.i.d. resampling of daily returns destroys volatility clustering and autocorrelation, understating tail risk of multi-day paths. Use a block or stationary bootstrap (Politis and Romano 1994). [R] JASA 89(428), https://doi.org/10.1080/01621459.1994.10476870
  - The sample window decides the answer: a bull-market window bootstraps bullish futures. Show the window used.
  - Survivorship: resampling a stock that still exists ignores ones that went to zero.
  - Few events (e.g. 20 past lockup expiries) give wide intervals; report the interval and the count, not just a mean.
  - Bootstrapped ranges are descriptive history, not forecasts; label them so.
