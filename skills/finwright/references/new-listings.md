# Buying a new listing (IPO) or one stock

How to help a user who wants to buy a company that is going public, or any single stock: when they can buy, what price is reasonable, how much, and through which broker. The evidence, with sources and confidence, is in [research/2026-10-17-ipo-buying.md](../../../research/2026-10-17-ipo-buying.md). fw.py does the arithmetic (`ipo`, `position`). The model recommends with reasons, and the user places any order (hard rules 2 and 6).

## Ask these before answering

1. **Where does this sit in the order?** A single stock comes after the steps in [next-dollar.md](next-dollar.md): emergency fund, the full match, high-interest debt and tax-advantaged room. Check those first (`FW networth`, `FW limits`).
2. **How much, against what?** `FW position <amount> --symbol <ticker> --monthly-spend <amount>` shows the buy as a share of investable assets and checks the emergency fund after it.
3. **Which broker and account?**
   - Getting shares at the offer price needs a broker in the offering's retail syndicate, an eligible account, and often a minimum in assets.
   - Anyone can buy once the stock trades.
4. **What does the prospectus say?** Find the price range, the share count after the offering, the latest revenue and the lock-up terms in the S-1/A, then the 424B4 for the final terms. Use SEC EDGAR, not news pages, once it is filed.
5. **Does the model have a stake?** If the company is the model's maker, or competes with it, say so at the start.

## The evidence that should shape the answer

- **The first-day pop is usually the worst price.**
  - US IPOs from 1980 to 2025 rose 19% on average on day one (median 7%); tech IPOs rose 31%.
  - Bought at the first-day close and held 3 years, IPOs trailed the market by 20.5%. Bought at the offer price, they trailed it by 3.3% (Ritter).
  - The median IPO bought at the first close lost 25.7% over 3 years, and about 60% lost money.
  - Large companies (sales of $1B or more) did better: about 2% behind the market from the first close.
- **The fall after the pop can take weeks.**
  - One large 2026 IPO priced at $135 and peaked four days later at about $225.
  - It was back at or below $135 within about six weeks, and above it again two months after listing.
- **The revenue multiple matters most.**
  - IPOs priced over 40 times sales trailed the market by 58.5% over 3 years. Under 5 times sales, by 1.3%.
  - `FW ipo` prints the multiple and flags anything over 40.
- **Lock-up expiry**, usually 180 days after the offering:
  - The price falls 1% to 3% on average around expiry and trading volume jumps about 40%.
  - Releases can come early, and the prospectus gives the terms ("Shares Eligible for Future Sale").
- **Analyst coverage** can start 10 days after the IPO (FINRA Rule 2241). The old studies found a few percent rise when coverage started, and later ones found less. It is not a reliable signal.
- **One stock is a big bet.**
  - FINRA cites the common "no more than 10% of investment assets in one stock" and says even that "could be too high".
  - Most individual stocks trail Treasury bills over their lifetimes. A few big winners carry the whole market (Bessembinder).
  - `position` bands: 5% or less is ordinary; over 5% up to 10% is a large holding; over 10% is concentrated.
- **Staged buying** does not raise the expected return:
  - A lump sum beats spreading the buy over 12 months about two-thirds of the time for a diversified portfolio (Vanguard 2012, 2023).
  - For one new stock, whose median path after the pop is down, a ladder of limit orders below the first-day price is a reasonable way to limit regret and timing risk.
  - Say plainly that this is the reason for the ladder.

## Getting shares at the offer price

- An indication of interest is a non-binding, conditional offer. Most shares go to institutions and wealthy clients.
- Retail fills are often a fraction of the request, or nothing at all.
- Brokers that run retail IPO programs, and what each asked for in 2026:

  | Broker | What it asked for (2026) |
  |---|---|
  | Fidelity | $100k or $500k in household assets, depending on the deal |
  | Robinhood | 100% of the cost as buying power; random allocation; no retirement or joint accounts |
  | SoFi | Its own program |
  | E*TRADE | An Investor Profile; individual, joint and IRA accounts eligible |
  | Schwab | A conditional offer; publishes no thresholds |

- Each offering picks its own brokers, so check the deal's announcement.
- **One firm can differ by account type.** A bank-owned or full-service firm may give IPO shares to adviser clients but none to its self-directed accounts. It may also have no shares at all when it is not in the syndicate. Tell the user to ask the firm about the specific deal.
- **Flipping:** selling within 30 days. It is legal, but brokers penalize it:
  - Robinhood: up to 60 days without IPO access.
  - SoFi: a ban of 180 days, then 365 days, then permanent, plus a fee on early sales.
- **Restricted persons** (FINRA Rule 5130) cannot buy at the offer price at all. These are broker-dealer staff, portfolio managers and their immediate family.

## The first trading day

- A large IPO opens when the lead underwriter is ready: Nasdaq's IPO Cross, or the NYSE opening auction. That is often late morning or later, not 9:30.
- **FINRA Rule 5131 bars market orders** to buy a new issue before it opens. Use limit orders all day, because the first trade can be far from the offer price.
- An order placed before the open sits until the stock trades. Keep its limit where the user would still be happy to own it.

## Prices that mislead

- **Pre-IPO quotes** (Forge, secondary platforms, tokenized "pre-stocks") do not carry over:
  - They are for other share classes, before splits.
  - Companies have declared unauthorized transfers void.
  - The SEC and FINRA warn about pre-IPO scams and fees.
- **Per-share prices in the news before the prospectus** are guesses. Compare deals by market value: per-share price times shares outstanding.
- **A price range** in the S-1/A may be at most 20% wide when the high end is above $10. The final price can still land outside it.

## How to answer

1. Collect the facts: `FW networth`, the steps in next-dollar.md, the prospectus numbers, and the broker and account.
2. Run the numbers:
   - `FW ipo --valuation <values> --revenue-q <quarter> --shares <count> --list-date <date>` (or `--price <low> <high>` with `--shares`) for per-share prices, the multiple and the dates.
   - `FW position <amount> --symbol <ticker> --monthly-spend <amount> --price <first-day price> --below 0 10 20` for the size and a ladder.
3. Recommend:
   - **A size.** Usually 5% of investable assets or less for one new stock, and only from money past the earlier steps.
   - **An entry plan.** No market orders; a ladder of limits below the first-day price over the weeks after listing; the lock-up date marked.
   - **What would change the answer.** A multiple far above peers, the user's emergency fund, or a fill at the offer price.
   - Use the user's own numbers. The user decides and places the orders.
4. Say plainly that a new listing can lose most or all of its value, that the user acts at their own risk, and that the money should be money they can afford to lose. End with fw.py's disclaimer line.
