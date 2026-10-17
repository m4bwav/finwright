# Buying a new listing (IPO): the evidence

Research pass of 2026-10-17 behind [references/new-listings.md](../skills/finwright/references/new-listings.md) and the `fw.py ipo` and `fw.py position` commands. It was prompted by a user who wanted to buy a large 2026 tech IPO "after the first-day pop" in a regular brokerage account.

Confidence:
- **H:** the primary text was read.
- **M:** the primary source was seen through a summary or only partly checked.
- **L:** secondary sources only.

## 1. First-day and long-run returns (Jay Ritter)

Sources:
- "IPOs: Underpricing", https://site.warrington.ufl.edu/ritter/files/IPOs-Underpricing.pdf (file of 2026-05-18).
- "Long-run returns on IPOs", https://site.warrington.ufl.edu/ritter/files/IPOs-long-run-returns-on-IPOs.pdf (file of 2026-10-05).

**First-day return (H):**
- US IPOs 1980 to 2025 (n = 9,343): average 19.0%, median 7.0%.
- Weighted by money raised, the average is 20.6%.
- On day one, 16.5% closed below the offer price and 13.0% closed exactly at it.
- 2025 averaged 29.3% (median 13.7%); 2024 averaged 15.3% (median 7.2%).
- Tech IPOs averaged 31.2% (n = 3,365) against 12.1% for the rest.
- Issuers with sales of $500m or more (2001 to 2025) averaged 13.3% (n = 749).

**Three-year buy-and-hold, 1980 to 2024 (Table 16f, H):**

| Bought at | Raw return | vs market | vs style-matched firms |
|---|---|---|---|
| First-day close (all IPOs, n = 9,253) | 19.1% | -20.5% (about -5.5% a year) | -8.9% |
| Offer price (all IPOs) | 36.3% | -3.3% | +8.3% |
| First-day close, tech | 21.8% | -12.7% | -0.4% |
| First-day close, sales of $1B or more (n = 866; first day 9.8%) | 32.4% | -2.1% | +0.6% |

Non-tech IPOs bought at the first close trailed the market by 24.9%.

**Spread of outcomes, 1975 to 2021 (Table 16e):**
- Bought at the first close, the average 3-year return is 21.2% but the median is -25.7% (H).
- About 60% of IPOs lost money over 3 years, and 38.5% lost more than half (M, computed from the bucket counts).
- From the offer price the median is -16.6% (H).

**Price-to-sales matters (Table 18d, sales over $100m, bought at the first close, H):**
- Under 5 times sales: first day 8.9%, 3 years 41.3% raw, -1.3% against the market.
- Over 40 times sales: first day 93.6%, 3 years -44.8% raw, -58.5% against the market. 12 of these 14 IPOs trailed the market.

**Float (Table 18e, H):** IPOs floating under 10% of their shares averaged a 32.4% first day.

**How Ritter measures market cap (H):**
- He uses the first close times basic shares across all classes.
- The fully diluted count (options, RSUs, warrants) gives a larger figure.

## 2. Lock-ups, quiet period, analysts

- **Lock-up length (H):** typically 180 days. The SEC bulletin "Investing in an IPO" says the price "may decline significantly" at expiry. The amount locked up is disclosed under "Shares Eligible for Future Sale" in the prospectus.
  - Sources: https://www.sec.gov/files/ipo-investorbulletin.pdf and https://www.sec.gov/answers/lockup.htm
- **Field and Hanka 2001 (M):** J. Finance 56(2), 1,948 lock-ups.
  - Three-day abnormal return at expiry: -1.5%.
  - Trading volume rises 40% and stays up.
  - Both effects are larger for venture-backed firms.
  - https://ideas.repec.org/a/bla/jfinan/v56y2001i2p471-500.html
- **Ofek and Richardson 2000 (M):** a 1% to 3% drop and 40% more volume at expiry, even though the date is known in advance. The drop could not be traded on profitably.
  - https://archive.nyu.edu/handle/2451/27072
- **FINRA Rule 2241(b)(2)(I) (H):** the underwriters' analysts must wait at least 10 days after an IPO.
  - The rule does not apply to Emerging Growth Companies.
  - The old 25-day figure is the NASD rule. Banks often still wait about 25 days in practice (L).
  - https://www.finra.org/rules-guidance/rulebooks/finra-rules/2241
- **Analyst initiation (M, old evidence):** Bradley, Jordan and Ritter 2003 found a 5-day abnormal return of +4.1% when coverage started. It was +6.4% with three or more analysts. A 2001-02 follow-up found 1.4%, which was not significant.

## 3. Retail access to IPO shares

- **How shares are handed out (SEC bulletin, H):** indications of interest are non-binding and feed the underwriters' order book. Most shares go to institutions and high-net-worth clients, so most individuals buy in the open market. Flipping is legal, but underwriters may refuse future allocations to people who flip.
- **FINRA Rule 5130 (H):** restricted persons are broker-dealer staff, the underwriter's finders and fiduciaries, portfolio managers, owners of broker-dealers, and their immediate family.
  - There is a 10% de minimis exemption.
  - The buyer's eligibility statement must be no older than 12 months.
- **FINRA Rule 5131 (H):**
  - A "flip" is an initial sale within 30 days.
  - A salesperson's commission cannot be clawed back for a flip unless a syndicate-wide penalty bid applies.
  - Spinning is barred.
- **Fidelity (M, ©2024):**
  - Needs $100k or $500k in household assets depending on the deal (workplace plan assets excluded), or premium client status.
  - Minimum indication 100 shares, and the account needs two thousand dollars.
  - The indication must be reconfirmed.
  - Allocation goes by assets, revenue to Fidelity and tenure.
- **Robinhood IPO Access (H, ©2026):**
  - A conditional offer needs 100% of the cost as buying power.
  - Allocation is random; asking for more shares does not raise the odds.
  - Retirement and joint accounts are not eligible.
  - No reconfirmation is needed within 20% of the range.
  - Selling within 30 days can block the account from IPO Access for 60 days.
- **SoFi (H, Sept 2026):**
  - A sale within 30 days brings a ban of 180 days, then 365 days, then a permanent one.
  - A $50 fee applies to sales before day 120.
- **E*TRADE (M):** US residents with an Investor Profile. Individual, joint and IRA accounts are eligible. A conditional offer gives the shares and a maximum price.
- **Schwab (L):** a "Conditional Offer to Purchase"; it publishes no thresholds.
- **Within one firm (L, 2026 reporting):**
  - Self-directed and adviser-led arms often differ. Self-directed accounts may get no IPO shares at all, while adviser clients get shares when the firm is in the syndicate.
  - In one large 2026 IPO, the retail share was reported in the low 20s of percent of the offering. Many retail orders were filled at a fraction of the size asked, or not at all.

## 4. The first trading day

- **Nasdaq IPO Cross (H):** orders are accepted from system start-up, then a 10-minute display-only period with indicative prices. A "pre-launch" period follows with no fixed length, and the lead underwriter decides when trading opens.
  - https://nasdaqtrader.com/content/ProductsServices/Trading/ipocross_fs.pdf
- **NYSE:** the designated market maker runs a manual opening auction. The commonly quoted "10am to 2pm ET" opening comes from broker blogs only (L).
- **FINRA Rule 5131(d)(4) (H):** no member may accept a market order to buy a new issue in the secondary market before trading begins, because the first trade can be far from the offer. Limit orders are allowed.
  - https://www.finra.org/rules-guidance/guidance/faqs/finra-rule-5131-frequently-asked-questions

## 5. Holding one stock

- **FINRA (H):** "no single formula or percentage"; "some experts recommend ... no more than 10 percent of total investment assets in a single stock ... and that could be too high."
  - https://www.finra.org/investors/insights/love-your-company-stock-what-to-know
- **Bessembinder 2018 (M):** about 42.6% of CRSP stocks since 1926 beat one-month Treasury bills over their lifetimes. About 4% of firms account for all net wealth creation.
- **J.P. Morgan "Agony and Ecstasy" 2014 (M):** about 40% of Russell 3000 stocks since 1980 suffered a permanent drop of 70% or more. Two-thirds lagged the index.

## 6. Staged buying against a lump sum

- **Vanguard 2012 (H) and 2023 (M):** a lump sum beat 12-month staged buying about two-thirds of the time, ending 2.3% higher on average in the US. Against 36-month staging it won about 90% of the time. Staging suits people who are very averse to losses.
- **Inference (not a cited finding):** Vanguard's result rests on diversified portfolios rising over time. For one IPO, the negative median after the first close weakens that premise. Staging an IPO buy limits timing risk and regret; it does not raise the expected return.

## 7. Reading the prospectus

- **Price range (H):** for IPOs, a range wider than $2 (price up to $10) or 20% of the high end (above $10) is not bona fide. Example: a $20 high end allows $16 to $20.
  - SEC Regulation S-K C&DI 134.04.
- **Rule 430A (H):** the effective S-1 can leave out the price. Changes up to 20% of the maximum aggregate offering go in a 424(b) prospectus within 15 business days. The final prospectus is a 424B4.
- **Splits (M):** SEC SAB Topic 4C has splits made before effectiveness shown retroactively in the S-1. Per-share prices quoted on secondary markets before a split are not comparable.

## 8. Pre-IPO secondary markets

- **SEC Investor Alert "Pre-IPO Investment Scams", 2024-06-07 (H):** pre-IPO offerings are not registered. Red flags: cold calls, claims that the IPO is imminent, hidden markups, and sellers who do not own the shares.
- **FINRA "Know the Risks of Pre-IPO Funds", 2026-08-18 (H):** without the company's approval a transfer "might be void." Holdings can sit in layers of vehicles, and fees can be large.
- **Company notices (M/L):** large AI companies declared unauthorized transfers void, including SPVs, tokens and forward contracts. Tokenized pre-IPO products reportedly fell 38% to 46% after one such notice (decrypt.co, L).
- **Share classes:** pre-IPO quote pages for one 2026 company showed prices from about $20 to over $1,000 a share for different preferred series on the same day (L).

## 9. A 2026 case: one large IPO after its first day (L, uneven sources)

- Priced at $135, about $1.8T. Up 19% on day one.
- Intraday high of $225.64 four days later.
- Then down about 40%, at or below the offer price in July.
- Back above it on August 10, and about 6% above it at the end of August.

The fall after the pop came over weeks, not hours.

Sources:
- https://www.startuphub.ai/ai-news/ipo-watch/2026/spcx-stock-nears-135-ipo-price-all-time-low-2026-07-14
- https://www.merceradvisors.com/faq/what-happened-to-spacexs-stock-price-after-its-ipo/
- https://www.dawn.com/news/2007701/retail-investors-build-big-dreams-on-small-slices-of-spacex
