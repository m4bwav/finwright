# Portfolio care

What to do once `FW allocation` and `FW fees` show the picture: which account holds which fund, selling at a loss, how to rebalance, bond fund risk, a large one-off sum and retirement withdrawals. Tax figures change; check the linked IRS page before quoting one. The model recommends with reasons, and the user decides (hard rule 6).

## Which account holds what

- **The default:** when both kinds of account exist and the shelter is too small for everything, put the least tax-efficient funds in the 401(k) or IRA and fill the taxable account with what is left (*Bogleheads' Guide*, ch. 11). Shoven and Sialm (2003), Reichenstein and Vanguard's Kinniry reach the same default for taxable bonds and broad stock funds.
- **Rough order, least to most tax-efficient:** high-yield and other taxable bonds, TIPS, REITs, balanced and actively traded stock funds, small-cap and value funds, broad stock index and tax-managed funds, then I and EE bonds and municipal bonds (ch. 10, 11). Treat it as an order of thumb: the gaps change with yields and brackets.
- **Run the numbers:** `FW placement 50000 --years 30 --stock-return 0.07 --dividend 0.015 --bond-return 0.04 --cap-gains 0.15 --income 0.22`, with the user's own assumptions and more than one set. It reproduces the book's tables at the book's assumptions. Try `--shelter roth` too, since a tax-free account can reverse the answer: the book's example treats only tax-deferred accounts.
- **Where the default weakens:** Kitces notes that the simple model treats bonds as fully taxed and stocks as untaxed each year, and that higher brackets can flip a close result. Shoven and Sialm note that stocks can move to the shelter when municipal bonds are available and the stock funds are tax-inefficient. An actively traded holding belongs in the shelter whatever it holds.
- **Compare a municipal fund on after-tax yield:** divide its yield by one minus the federal rate to get the taxable yield that matches it (ch. 10), or use `FW compare` with the `none` tax kind.
- **Do not sell to tidy up.** Moving a profitable taxable holding costs tax today. Fix placement with new money and inside the shelter first.

## Selling at a loss

- A net capital loss offsets gains, then up to three thousand dollars a year of other income (half that if married filing separately), and the rest carries forward ([IRS Topic 409](https://www.irs.gov/taxtopics/tc409)).
- **The wash sale window is 61 days:** 30 days before the sale, the sale day and 30 days after. The book mentions only waiting afterwards (ch. 10), so also check purchases made before the sale. A similar but not identical fund can keep the money invested.
- **An IRA purchase counts.** Buying the same fund in the user's IRA within the window disallows the loss (Rev. Rul. 2008-5), and secondary sources say it is lost for good rather than added to basis. A spouse's purchase can count too. Have the user confirm these points with Publication 550 or a tax professional before acting.
- Loss sales only help in a taxable account. Do not quote the book's 27% harvesting gain: its simulation was not checked and depends on its assumptions.

## Timing a taxable sale

- Short-term gains are taxed as ordinary income; hold more than 12 months where possible (ch. 10, Topic 409).
- Selling a winner in January rather than December delays the tax a year (ch. 10). A buyer of a fund just before its distribution date pays tax on money that was already in the price, so wait until after it (ch. 10).
- Low-income years can suit a Roth conversion (ch. 11), or gains taxed at the 0% long-term rate; Topic 409 lists the current income limits.

## How to rebalance

`FW allocation` flags 5/25 band crossings. Once one is flagged, use the cheapest move that closes it (ch. 17):

1. Direct new contributions to what is under target.
2. Trade inside tax-deferred accounts, which costs no tax.
3. In retirement, take withdrawals from what is over target.
4. Send taxable distributions to cash and use them, rather than reinvesting in what is already high.
5. Pair a needed taxable sale with a loss sale. Sell taxable winners last and after 12 months.

An all-in-one fund rebalances itself, and it can make all of this unnecessary inside a shelter. It is a poor fit for a taxable account (ch. 10, ch. 17).

## Bond fund risk

Duration, in years, gives the rough price change for a change in rates: a 4.3-year fund loses about 4.3% if rates rise a point. Match it to when the money is needed: money due in two or three years belongs in a short-term fund or something safer (ch. 3). Higher yields then rebuild part of the loss over time.

## A windfall

An inheritance, a sale or a settlement (ch. 15):

1. Pay any tax owed on it and clear high-interest debt.
2. Put the rest in savings or a money market fund for about six months, with at most a small amount spent on celebrating. The book offers this as advice from experience, not as a measured result.
3. Work out what it can really buy, with `FW compare` and the withdrawal section below. It is usually less than it feels.
4. Then write the list of wishes, and follow [next-dollar.md](next-dollar.md). Hold off on quitting work, large gifts, a bigger house and anyone's sure thing until then.

## Withdrawals in retirement

- **The figure:** the book gives 4% of the starting balance, raised with inflation, or up to 5% of each year's balance with income that falls in bad years (ch. 20). Morningstar's 2026 estimate is 3.9% for a 30-year horizon at 90% success, excluding Social Security, with flexible methods starting as high as 5.7%. These are starting points for planning, not fixed rules, and they do not guarantee anything.
- **Sequence matters more than the average:** a bad market early does the most damage, so an average return does not make that return's percentage a safe withdrawal (ch. 20).
- **Flexibility is the main protection:** low fixed costs, a way to earn if needed, and spending that can fall in a bad year (ch. 20). Social Security pays more when it starts later, and an immediate annuity can cover basic costs; both are worth raising, and neither is a decision for this skill.
- **Longevity:** plan past life expectancy, since half of retirees outlive it. The book also warns against underspending in old age out of fear (ch. 20).

## Reviewing holdings

- **Concentration:** warn when employer stock is more than about 10% of the portfolio (Bogleheads' Guide, ch. 19; FINRA cites the same cap for any one stock). The paycheck already rides on that company.
- **Overlap:** several funds holding the same large companies (an S&P 500 fund, a total market fund and a large-cap growth fund) are one bet, not diversification (ch. 12).
- **Fees beyond the expense ratio:** `FW fees` weighs expense ratios only. Ask whether any fund charges a sales load or a 12b-1 fee, and whether an adviser or wrap account takes a percentage on top (ch. 9).

## Before a sale or a switch

Ask these before endorsing a sell, a fund switch or a new strategy (ch. 19):

1. Is this a reaction to recent news or a recent drop or run-up?
2. Would you buy this today at this price if you did not own it?
3. Does it change the allocation you set, and was that plan wrong or just uncomfortable?
4. What does the move cost in tax, loads and spreads?
5. Are you trusting a forecast, a tip or past returns?

## Claims not to repeat

- The book says allocation decides 93.6% of a portfolio's risk and return (ch. 8). Brinson, Hood and Beebower measured variation in returns over time. Ibbotson and Kaplan (2000) found about 90% over time, about 40% of the differences between funds and about 100% of the return level, and critics dispute how the last is framed.
- Using a home-equity loan to pay off credit cards (ch. 1) turns unsecured debt into debt against the house, and spending often refills the cards. Since 2018, home-equity interest is deductible only when the loan buys, builds or substantially improves the home (IRS Publication 936), so the book's tax point no longer holds for card payoffs.
- Bonds equal to one's age and the book's model portfolios are rough guides from 2014. They are starting points to discuss, not targets to set for the user.

## Sources

Read or seen 2026-11-03. Chapter numbers refer to Larimore, Lindauer and LeBoeuf, *The Bogleheads' Guide to Investing*, 2nd ed., Wiley 2014.

- [IRS Topic 409](https://www.irs.gov/taxtopics/tc409): read directly.
- From search excerpts, not the full documents: [Morningstar on 2026 withdrawal rates](https://www.morningstar.com/retirement/whats-safe-retirement-withdrawal-rate-2026); [The Tax Adviser on Rev. Rul. 2008-5](https://www.thetaxadviser.com/issues/2012/mar/casestudy-mar2012.html); [Shoven and Sialm (2003)](https://faculty.mccombs.utexas.edu/Clemens.Sialm/SSJPUBE.pdf); [Kitces on asset location](https://www.kitces.com/?p=479); [The Asset Location Decision Revisited, FPA](https://www.financialplanningassociation.org/article/journal/NOV13-asset-location-decision-revisited-0); [CFA Institute on the allocation studies](https://rpc.cfainstitute.org/blogs/enterprising-investor/2012/setting-the-record-straight-on-asset-allocation).
