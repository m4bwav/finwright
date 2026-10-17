# Where the next dollar goes

How to help the user decide where spare money goes: paying down the mortgage, I bonds, cash, or investing. This is what the planning forums, blogs and research agree on, where they disagree, and the questions to settle first. The survey behind it, with every source and the rates on the day it was written: [research/2026-10-15-next-dollar-literature.md](../../../research/2026-10-15-next-dollar-literature.md). Rates move every week, so check today's before quoting one.

fw.py does the arithmetic: `mortgage` for the payoff month and what a lump sum saves, and `compare` for the after-tax yields of the choices. The model recommends with reasons, and the user decides (hard rule 6).

## Ask these before answering

1. **What is the money already sitting there earning?** Run `FW networth`, then look at the interest lines on the cash accounts (a bank activity import shows them). Large balances at a big bank's savings or money market rate (often 0.01% to 0.1%, while the national average was 0.37% and the best savings accounts and Treasury bills paid about 4% to 4.5% in October 2026) usually cost more each year than anything the next $10,000 can change. Say so first.
2. **Emergency fund:** months of spending held in cash. The usual range is 3 to 6 months. Hold more with one income, variable pay or a shaky job, and less with two stable incomes. The Bogleheads wiki says to start at one month and grow toward 3 to 12.
3. **Employer match:** is the user getting all of it? Vanguard (2026) found 26% of people prepaying a mortgage were leaving match money on the table.
4. **Other debt:** cards, car loans, student loans and their rates.
5. **Tax-advantaged room this year:** HSA, IRA or Roth IRA (for each spouse), and room left in the 401(k) (`FW limits`). Contributions to a Roth IRA (not its earnings) can be taken back out at any time, so funding one gives up less access than paying down a loan.
6. **The mortgage:** rate, monthly principal and interest (not the escrow), principal left, and whether the user itemizes deductions. With the 2026 standard deduction ($32,200 married filing jointly, $16,100 single) most households do not itemize, so their mortgage interest saves them no tax.
7. **Savings bonds:** how much of this calendar year's $10,000 per person I bond limit is used, and the fixed rate on the bonds already held (`FW bond add` records the issue month, which sets it).
8. **Federal and state marginal tax rates** (`FW config set after_tax_rate`), and how long until retirement.

## The order nearly everyone agrees on

The Bogleheads wiki ("Prioritizing investments"), the r/personalfinance flowchart and Vanguard's 2026 paper share the same top of the list:

1. A starter emergency fund.
2. The full employer match.
3. High-interest debt (cards, anything around 8% to 10% or more).
4. The full emergency fund.
5. HSA, IRA or Roth IRA, then more 401(k), up to the limits.
6. Then a choice between taxable investing, prepaying a low-rate mortgage and safe bonds (I bonds, Treasuries). This is where the sources disagree, and it is the step most "what do I do with $10k" questions are really about.

None of the flowcharts puts I bonds or mortgage prepayment ahead of tax-advantaged retirement saving.

## Paying down the mortgage

- **It is a bond.** Every dollar of principal prepaid earns the loan's rate with no risk. That return is tax-free when the interest would not have been itemized. Compare it with **after-tax safe yields of similar length** (Treasuries, CDs, savings, I bonds), not with stock returns (Bogleheads, finiki, Early Retirement Now, Ben Felix, Allan Roth, Jonathan Clements). Kitces adds a risk premium of about 5 points to the mortgage rate before stocks are worth choosing instead of the prepayment.
- **Rate bands that recur:** JL Collins (in Christine Benz's *How to Retire*) prepays nothing at 3% or less, pays off at 6% or more, and calls 3% to 6% a matter of comfort. When safe yields after tax beat the loan rate ("positive carry", Early Retirement Now), holding the bonds wins on yield and on access. When the loan rate is well above them, prepaying beats every safe asset.
- **A partial prepayment frees no cash flow.** On a fixed-rate loan the payment stays the same until the balance reaches zero (Kitces 2016; lenders' own pages). The money is out of reach at once, and getting it back takes a new loan. The interest saved arrives slowly. A recast (a lump sum, often a five-thousand-dollar minimum, plus a small fee) lowers the payment, but not every loan allows it, and FHA, VA and USDA loans never do.
- **Escrow goes on.** Payoff ends principal and interest only. Property tax and insurance are still due, now paid directly. `FW mortgage` prints the principal-and-interest figure, which is the cash flow that payoff frees.
- **The forum middle path:** keep the money liquid in safe assets that earn about the loan's rate, and pay the loan off in one lump when the pile matches the balance (or when the user wants it gone, such as before retirement). Until then the money keeps both its return and its access.
- **Peace of mind is a real reason.** Mr. Money Mustache ("the Peace and Quiet of Cash"), Benz and Clements accept a lower expected return to be debt-free. Early Retirement Now and Kitces show that a mortgage in retirement adds sequence-of-returns risk, because withdrawals for fixed payments come out early. A German panel study (Will and Renz, 2024) found owners with a mortgage less satisfied with life than owners without one. Research on non-mortgage debt links it to distress (Brown, Taylor and Price 2005). Amromin, Huang and Sialm (2007) found that about 38% of households who prepaid would have done better in a tax-deferred account.
- **Concentration:** prepaying adds to home equity, which cannot be sold piece by piece. When the home is already most of net worth (`FW networth` by type), say so.

## I bonds

- **Rules:** $10,000 per person (SSN) per calendar year, electronic only, through TreasuryDirect. The paper bonds bought with a tax refund have been discontinued. A bond must be held 12 months, and cashing it before 5 years costs the last 3 months of interest. Interest is federal-taxable, state-free, and can be deferred until redemption.
- **The fixed rate is what lasts.** The composite rate is the fixed rate plus inflation, reset every 6 months. A bond keeps the fixed rate of its purchase month for 30 years. New rates are announced on 1 May and 1 November (`FW bond rates`; the next date is in rates.json).
- **Timing:** buying at the end of a period locks the current rate for 6 months. That pays off only when the next fixed rate is expected to be the same or lower. When forecasters expect it to rise (Tipswatch publishes the inflation part, which is already fixed by the CPI, and a fixed-rate estimate before each reset), wait for the new period. Interest counts for the whole month of purchase, so buying late in a month costs nothing.
- **Two calendar years, one rate:** a household that has not used this year's limit can buy in November or December and again in January, both at the same November fixed rate.
- **I bonds or TIPS:** when the 5-year TIPS real yield sits far above the I bond fixed rate, the forums prefer TIPS (Tipswatch, 2026: "advantage TIPS"). TIPS fit best inside an IRA, because outside one their inflation adjustment is taxed every year.
- **Role:** after their first 12 months, I bonds work as a second layer of the emergency fund. They are never the first layer (White Coat Investor, Tipswatch).
- **Old bonds:** a bond with a 0% fixed rate earns only inflation. Whether to cash it and buy at a higher fixed rate depends on the deferred tax that comes due on redemption and the 3-month penalty before 5 years. `FW bond value` shows each bond's value.

## Cash

- High-yield savings, a government money market fund and Treasury bills all pay roughly the short-term rate. Treasury interest is free of state tax, and savings interest is not. The emergency fund belongs here, not in I bonds in their first year and not in prepaid principal.
- **A money market fund is not a bond fund.** Users often fear that moving savings to a brokerage puts the emergency fund at risk. A government or Treasury money market fund keeps its price at one dollar a share, holds Treasury bills and repurchase agreements backed by Treasuries that mature within days or weeks, and can be sold on any business day. Government money market funds have kept the one-dollar price through every crisis, including 2008, when the fund that fell below a dollar was a prime fund holding Lehman debt. A bond fund (intermediate or long Treasury, total bond) has no fixed price, and its value moves with interest rates. Many lost 10% or more in 2022, so a bond fund is not an emergency fund. Treasury bills held directly can be sold before they mature at prices that move very little. A money market fund is not FDIC-insured; its backing is the Treasury debt it holds. Before moving the whole emergency fund, the user can move part of it and make one test withdrawal back to checking, to see how fast the money comes back.
- **Check the fund's fee before calling it cash done.** A full-service broker often offers a retail share class of a Treasury money fund with expenses around half a percent or more. That class can trail Treasury bills by most of a percentage point. A Treasury-bill ETF (expense ratios around 0.06% to 0.14%) has no minimum beyond one share, trades without commission at most brokers and settles the next business day. Treasury bills bought online in the secondary market pay the full rate in thousand-dollar steps. Compare the fund's 7-day yield with the 3-month bill rate (Fed H.15). `FW returns` on the account shows what the user actually earned once their deposits are recorded with `FW flow add`.
- Some banks give relationship tiers (card reward boosts, fee waivers) for combined balances, and those balances often include an affiliated brokerage. Moving idle cash to Treasury bills or a money market fund inside that brokerage can keep the tier while earning the market rate. Check the bank's current rules.

## Investing

- Tax-advantaged room first (match, HSA, IRA, 401(k)), then taxable. Over long periods stocks are expected to beat a low mortgage rate, but they promise nothing, so `compare` leaves them out. That is a separate decision about risk and time horizon. Recommend the kind of fund (a broad, low-cost index fund fits most people) and the account it goes in; a single stock is a separate, smaller bet ([new-listings.md](new-listings.md)).

## How to answer

1. Collect the facts above (`FW networth`, `FW limits`, `FW bond rates`, the user's answers).
2. Run `FW mortgage --rate R --payment PI --lump AMOUNT` (or `--original` and `--term` to work out the payment) and `FW compare AMOUNT --years N --option ...` with today's rates, which the user can confirm on their bank's and Treasury's pages. Name each rate's source and date.
3. Answer in the order above: fix the idle cash first, then the earliest step the user has not finished. For a low-rate loan, explain the after-tax comparison, the cash flow point and the lump-sum middle path. Recommend one, with the trade-off in their own numbers and what would change the answer; the user decides.
4. End with fw.py's disclaimer line.
