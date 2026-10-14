# Net-worth and investment-tracking software: survey (Track B)

Checked: 2026-10-12, unless a row says otherwise. Researcher: AI research pass for the finwright plugin.
Scope: what commercial and open source tools do for a US individual tracking bank accounts, a 401k, bonds and other investments, and which of their ideas finwright should copy.

Related: [2026-10-12-data-access-routes.md](2026-10-12-data-access-routes.md) (how data gets in) and [2026-10-12-method-rules-and-security.md](2026-10-12-method-rules-and-security.md) (calculation rules and security). Read this file when choosing features or comparing finwright with existing products.

Source quality note: many "2026 pricing" pages on the web are affiliate or comparison sites (getfinny, costbench, fincomparelab, subger, mezzi). Where I could reach the vendor's own page I cite that; where I could not, the row says so. GitHub figures come from the GitHub API (`gh api repos/...`) and PyPI figures from the PyPI JSON API, both read on 2026-10-12.

## 1. Commercial tools

| Tool | Price (checked 2026-10-12) | Users / scale | Aggregator | Good for 401k, bonds, investments | Weak spots |
|---|---|---|---|---|---|
| Empower Personal Dashboard (ex Personal Capital) | Free dashboard; paid advisory about 0.49% to 0.89% of assets (third-party figures) | 3.5M+ users as of 2023-01-31 (Empower's own claim, relayed by search; no newer official figure found) | Yodlee (Empower's own support notice names Yodlee as "our aggregation partner") | Retirement Fee Analyzer (fund expense ratios plus plan admin and advice fees), Investment Checkup against allocation models, retirement planner, holdings view | Linking is a lead source for advisor sales calls, reported at $100k+ linked; sync breaks per institution (Shareworks blocked Yodlee on 2026-08-20); no phone support for the free tier per user reports |
| Monarch (monarch.com) | $14.99/month or $99.99/year Core; Plus tier not priced on the page; code WELCOME 30% off first year | No user count published; "100,000+ reviews, 4.9"; $75M Series B May 2025 at a reported $850M valuation after the Mint shutdown surge | Plaid, Mastercard Data Connect (ex Finicity) and MX, user can switch provider per connection | Net worth, investments view, Zillow home value, VIN car value; Plus "go deeper on your investments" plus forecasting | Provider outages on its status page (Finicity, MX, Plaid incidents); some Fidelity NetBenefits logins fail on all three providers (Jan 2026 Reddit report) |
| Copilot Money | $95/year or monthly plan; 1-month trial | Not published | Not named on the pricing page | Net worth across stocks, crypto, real estate (Zillow URL); live holding estimates; allocation by equity, crypto, ETF, cash | iPhone, iPad, Mac and web only; no Android app |
| Kubera | Essentials $250/year, Black $2,500/year, Gold $10,000/year; 14-day trial | Not published on the site; third-party "$47B tracked" claim unverified | Several aggregators chosen per institution (not named on the site; third-party review names Plaid, Yodlee, Flinks, Salt Edge); "Web Sync" reads balances from sites without connectors | Best manual-asset model of the group: tickers, private stocks and LP positions with IRR and capital calls, physical assets with an "AI appraiser", net worth in BTC, Fast Forward projections | Price; aimed at high net worth and alternatives rather than a simple 401k plus bank setup |
| ProjectionLab | Basic free; Premium $129/year; Pro $549/year (advisors) | 30k MAUs in Dec 2024 (founder's Show HN title); $100k ARR in Apr 2023 | None: help page says it does not link accounts; balances come from plugins (YNAB, Monarch, community browser extensions for Vanguard and Alight) | Planning, not tracking: Monte Carlo, historical backtesting, Roth conversions, withdrawal strategies, tax estimation | You update balances yourself or through third-party plugins |
| Boldin (ex NewRetirement) | Basic free; PlannerPlus $144/year (page says it rises to $168/year on 10/15); advisor checkup $3,200 | "250,000+ people planning with Boldin" (own page) | Links accounts "via the top 3 aggregators" (not named) | Retirement planning with 100+ inputs, what-if scenarios | Planner more than tracker; linking only on the paid tier |
| Tiller | $99/year, 30-day trial | Not published | Yodlee (Google Workspace listing); one third-party review adds Plaid | Daily balances and transactions into Google Sheets or Excel; Foundation Template includes net worth; community Net Worth Snapshot Sheet keeps a 12-month trend table | Everything else is your spreadsheet work; Yodlee outages hit it (Tiller runs an institution outage dashboard) |
| Quicken Simplifi | $3.99/month billed annually (list $6.99) | Not found | Not named | Investments dashboard, performance over time | Users miss Classic's lot history and cost-basis detail; repeated prompts to fix cost basis on cash positions |
| Quicken Classic | Deluxe $6.99/mo, Premier $7.99/mo, Business & Personal $10.99/mo (annual, on sale) | Not found | Not named | Premier: cost basis, total gain/loss, capital gains estimator for mixed lots, Morningstar Portfolio X-ray | Desktop only (Windows, Mac); subscription for desktop software |
| YNAB | $109/year or $14.99/month; 34-day trial | Not found | Not named on pricing page | Investment and retirement accounts only as off-budget "tracking accounts" that count toward net worth | No holdings; YNAB says investment and HSA accounts do not import transactions |
| Rocket Money | Free tier; Premium about $7 to $14/month pay-what-you-think-is-fair | 5M+ members (App Store claim relayed by FinCompareLab, unverified) | Not checked | Net worth is a Premium feature: linked accounts minus liabilities plus a home value estimate | Built around subscriptions and bill negotiation, light on investments |
| Fidelity Full View | Free for Fidelity customers | Not published | eMoney Advisor (Fidelity affiliate) | Outside accounts plus manual assets and liabilities; a new version recently added net worth and cash flow over time, custom sub-categories, transaction rules | Manual values stay static; credit card and student loan linking "planned"; a 2026-08-09 third-party post says the relaunch forced relinking (not confirmed by Fidelity) |
| Credit Karma Net Worth | Free | Not published | Intuit (Mint's connections, "17,000+ institutions" on the migration page) | Assets, debts and investments in one place; Mint net worth history could be transferred | Credit Karma says Net Worth "is not widely available to all members"; at launch only for credit scores above 720; no budgeting, investment insights were promised later |
| Wealthfront Path | Free, no Wealthfront account needed | Not checked | Links outside accounts | Projects net worth and retirement from linked accounts, Social Security, contributions | Projections "for illustrative purposes only"; manual entry gives less accurate results per Wealthfront |

Sources (all checked 2026-10-12):
- Empower fee analyzer: https://support-personalwealth.empower.com/hc/en-us/articles/201169600-Retirement-Fee-Analyzer-Calculations-Overview
- Empower Yodlee notice (Shareworks, 2026-08-20): https://support-personalwealth.empower.com/hc/en-us/articles/42872219453847-Shareworks-by-Morgan-Stanley-Site-Blocking-Issue-as-of-August-20-2026
- Empower user count (3.5M as of 2023-01-31, via search summary of empower.com): https://www.empower.com/refer
- Empower sales calls (third-party, commercially motivated): https://www.mezzi.com/blog/empower-free-dashboard-vs-advisor-pitch-reading-real-product and https://www.bestroboadvisors.org/?p=911
- Empower quality complaints, 2025: https://unitq.com/unitq-scorecards/personalcapital
- Monarch pricing: https://www.monarch.com/pricing
- Monarch providers: https://help.monarch.com/hc/en-us/articles/360048393352
- Monarch outages: https://status.monarch.com/cm7wduh1f001dhk2t9n5js5md and https://status.monarch.com/clxoq6aad1546beobo70etjp7
- Monarch Series B: https://www.retailbankerinternational.com/news/monarch-secures-75m-funding/ and https://coverager.com/monarch-raises-75-million/
- Monarch Fidelity NetBenefits report (Reddit mirror, Jan 2026): https://reddit.sentinel-team.org/posts/1qkd1f7/snapshots/2026-01-24T07%3A40%3A22.40417Z
- Monarch feature roundup (Zillow, VIN): https://robberger.com/net-worth-calculators/
- Copilot pricing and platforms: https://copilot.money/pricing
- Kubera: https://www.kubera.com/ (pricing on the home page; /pricing returned 404)
- Kubera aggregator names (third-party): https://jeangalea.com/kubera-review
- ProjectionLab pricing: https://projectionlab.com/pricing ; linking: https://projectionlab.com/help/can-i-link-accounts ; MAUs: https://news.ycombinator.com/item?id=42450913 ; ARR: https://news.ycombinator.com/item?id=35591648
- Boldin pricing: https://www.boldin.com/retirement/pricing/
- Tiller pricing: https://www.tiller.com/pricing/ ; Yodlee: https://gsuite.google.com/marketplace/app/tiller_money_feeds/417666986289 ; snapshot template: https://tiller.com/community-templates/net-worth-snapshot-sheet/ ; outage dashboard: https://help.tiller.com/en/articles/2841201-using-the-institution-outage-dashboard
- Quicken plans: https://www.quicken.com/compare ; Simplifi lot complaints: https://community.simplifimoney.com/discussion/comment/18060/ and https://community.simplifimoney.com/discussion/comment/68169/
- YNAB pricing: https://www.ynab.com/pricing ; tracking accounts: https://support.ynab.com/en_us/tracking-investment-accounts-a-guide-r1Bzjxd05.md
- Rocket Money pricing: https://www.rocketmoney.com/learn/personal-finance/how-much-does-rocket-money-cost ; net worth: https://framer.rocketmoney.com/faq ; member claim: https://www.fincomparelab.com/?p=717
- Fidelity Full View FAQ: https://www.fidelity.com/go/full-view-faqs ; relaunch claim (third-party): https://www.mezzi.com/blog/fidelity-retired-old-full-view-what-broke-what-to-use-instead
- Credit Karma: https://www.creditkarma.com/lp/mint-to-credit-karma-net-worth and https://www.creditkarma.com/about/releases/credit-karma-net-worth
- Wealthfront Path: https://www.wealthfront.com/blog/introducing-free-financial-planning/ and https://support.wealthfront.com/hc/en-us/articles/115000311703-What-are-the-benefits-of-linking-my-outside-accounts-to-Wealthfront

### The Mint shutdown story

Intuit announced on 2023-10-31 that Mint would close and its users would move to Credit Karma, with a chance to export Mint data first; final shutdown landed in early 2024 (sources disagree on the exact day, March 2024 is the most cited). Credit Karma did not take over Mint's budgets, and its Net Worth feature was limited ("not widely available"). Monarch was the main winner: an early favorite on r/mintuit, then a reported 20-fold surge in paying subscribers and the May 2025 Series B. Sources: https://www.pcworld.com/article/2125596/the-popular-mint-budgeting-tool-is-shutting-down.html , https://www.mymoneyblog.com/mint-to-credit-karma-transition-alternatives.html , https://www.revenuememo.com/p/who-owns-monarch-money (20-fold figure, weak source), Ask HN thread https://news.ycombinator.com/item?id=38179611 (all checked 2026-10-12).

Lesson: a free tool tied to a parent company's other business can vanish or shrink; the user's data should live in files they own, with an export they can open without the app.

### Why sync breaks (context for every aggregated tool)

- Aggregators reach banks through a mix of APIs and screen scraping; institutions block scrapers (Shareworks blocking Yodlee in Aug 2026, Plaid "not permitted" for some Fidelity connections while Finicity still worked). https://feedback.lunchmoney.app/institution-status-requests/p/ability-to-sync-fidelity-investments-accounts
- Fidelity incubated Akoya (bank-owned API network, spun off 2020); critics fear it becomes a chokepoint. https://paymentexpert.com/2020/02/20/api-start-up-akoya-becomes-joint-owned-coalition-with-11-us-banks/
- The CFPB's Section 1033 open banking rule (Oct 2024) is not in force: a court enjoined enforcement and a "Personal Financial Data Rights Reconsideration" proposal went to OIRA in Aug 2026, including whether banks may charge fees for access. https://www.consumerfinancemonitor.com/2026/08/06/cfpb-sends-new-section-1033-open-banking-proposal-to-oira-for-review/ and https://openbankingtracker.com/guides/section-1033-status
- A 2026-09-27 r/personalfinance commenter chose a manual-only app because "all the apps that connect to banks etc end up crashing eventually." https://www.reddit.com/r/personalfinance/comments/1wr2avt/net_worth_tracker_recommendations/

## 2. Open source, self-hosted and local-first

GitHub numbers from the GitHub API on 2026-10-12.

| Project | Stars | Last release | License | Kind | Import routes | Lots / performance | Multi-currency | Net worth |
|---|---|---|---|---|---|---|---|---|
| Ghostfolio | 9,443 | 3.85.0, 2026-10-12 | AGPL-3.0 | Web wealth tracker (Angular, NestJS), Docker | Import/export of activities (JSON API and CSV), data sources Yahoo, CoinGecko, manual; paid cloud with professional data | Return on Average Investment (ROAI) incl. dividends for Today to Max; holdings by account | Yes (per activity currency) | Yes, investments focus; has an MCP server for AI clients (read with or without monetary values, optional import) |
| Maybe Finance | 54,230 | v0.6.0, 2025-07-24 | AGPL-3.0 | Rails app; archived | Was Plaid, CSV | Holdings, net worth | Yes | Yes; repo archived, final release, company pivoted to business forecasting |
| Sure (Maybe fork) | 10,494 | v0.7.5-hotfix.2, 2026-10-06 | AGPL-3.0 | Community fork of Maybe, Docker | Plaid, SimpleFIN, SnapTrade, Interactive Brokers, Coinbase, Enable Banking, Lunch Flow, Mercury, CSV, Actual import (from repo tree) | Holdings model, trades | Yes | Yes, dashboard with net worth, cash flow and an AI assistant |
| Actual Budget | 29,462 | v26.10.0, 2026-10-02 | MIT | Local-first envelope budget with optional sync server | SimpleFIN, GoCardless, Enable Banking, Pluggy, Akahu (sync-server source tree), OFX/QFX/QIF/CSV | No holdings; investments as off-budget balance accounts | Limited | Built-in net worth report (all accounts over time) |
| Firefly III | 24,883 | v6.7.9, 2026-10-11 | AGPL-3.0 | Self-hosted PHP double-entry manager | Separate Data Importer (845 stars): CSV, CAMT.052/053, SimpleFIN, Enable Banking, GoCardless (winding down), Lunch Flow, Spectre (free access ended 2025-10-31) | No investment lots | Yes | Asset accounts and net worth charts; budgeting focus |
| Beancount | 6,074 | 3.2.3 on PyPI, 2026-05-05 | GPL-2.0 | Plain-text double-entry, Python | beangulp importers (0.2.0, 2025-01), beancount-import (474 stars, v1.4.0 2024-04, active commits 2026-08), any CSV/OFX via plugins | Strong: cost basis per lot with booking methods (FIFO, LIFO, strict) | Yes, commodities of any kind | Balance sheet; net worth through Fava |
| Fava | 2,589 | 1.30.16 on PyPI, 2026-08-18 | MIT | Web UI for Beancount | Upload via importers | Holdings, gains, charts | Yes | Net worth chart over time, balance sheet |
| beanprice | 123 | 2.1.0 on PyPI, 2025-10-18 | GPL-2.0 | Price fetcher for Beancount | Yahoo and other sources | n/a | n/a | n/a |
| hledger | 4,764 | 1.52.4 stable 2026-09-10; 1.99.5 preview of hledger 2 on 2026-10-01 | GPL-3.0 | Plain-text accounting, Haskell | CSV rules files (rich), `hledger get` price merging | hledger 2 previews add real lot tracking (`{}` cost basis, FIFO-style disposals, `--lots`, `--gain`); `roi` command gives TWR and IRR | Yes | `balancesheet`, hledger-web; users find net worth plots hard (Dec 2025 r/plaintextaccounting) |
| Ledger | 6,054 | v3.4.1, 2025-10-26 | BSD-style | Original plain-text accounting, C++ | CSV convert | Lots via `{}` | Yes | Balance reports |
| GnuCash | 4,374 | 5.17, 2026-09-27 | GPL | Desktop double-entry | QIF, OFX (with duplicate matching), CSV, HBCI for German banks | Stock and mutual fund quotes (Finance::Quote), portfolio valuation report, lots | Yes | Balance sheet and charts |
| Portfolio Performance | 4,098 | 0.89.0, 2026-10-11 | EPL-1.0 | Desktop Java (plus iOS and Android apps) | PDF statements from 90+ banks and brokers (Europe heavy), CSV | True time-weighted rate of return (TTWROR) and IRR; FIFO and moving-average gains (0.86.1 fixed FX on FIFO) | Yes, ECB rates | Portfolio and accounts, rebalancing to target allocation |
| Wealthfolio | 9,171 | v3.9.1, 2026-09-27 | AGPL-3.0 | Local-first desktop (Tauri), mobile, Docker self-host | CSV free; optional paid "Connect" for 30+ brokerages (read-only); custom price feeds | True time-weighted and money-weighted returns, benchmark vs S&P 500 or any ETF | Yes | Assets and liabilities over time; v3.6 (Jul 2026) widened it to spending; AI assistant and MCP server |
| Paisa | 3,224 | v0.7.6, 2026-09-06 | AGPL-3.0 | Web UI on Ledger journals, Docker | CSV, Excel and PDF to Ledger via templates | Allocation targets, retirement planning; price providers for mutual funds, NPS, stocks (India first) | INR default, USD/EUR supported | Yes; manual revaluation of houses, cars, land |
| Budget Zen | 114 | archived (last push 2025-02-27) | AGPL | Simple encrypted budget web app | Manual | None | Basic | No; dead, skip |
| Lunch Money (paid, closed source) | n/a | n/a | Commercial | Hosted budgeting with multi-currency | Plaid, plus other feeds; public API | Investment balances via sync | Strong, its launch selling point | Yes. Price: pricing page lists $100/year or $10/month "set your own price"; blog says annual minimum rose from $50 to $60 on 2026-03-15 (pricing page returned 403 to my fetcher, figures from search summary) |

Sources (checked 2026-10-12):
- GitHub API: `gh api repos/<owner>/<repo>` and `/releases/latest` for each repo above; Sure integrations from `gh api repos/we-promise/sure/git/trees/main?recursive=1` and `app/models`; Actual from `packages/sync-server/src`.
- PyPI JSON: https://pypi.org/pypi/beancount/json , https://pypi.org/pypi/fava/json , https://pypi.org/pypi/beangulp/json , https://pypi.org/pypi/beanprice/json
- Ghostfolio README: https://github.com/ghostfolio/ghostfolio ; Premium price only from third parties (about $40 to $48/year): https://www.findmymoat.com/vs/ghostfolio-vs-myinvestor (ghostfol.io/en/pricing did not render prices for my fetcher)
- Maybe wind-down: https://github.com/maybe-finance/maybe and https://news.ycombinator.com/item?id=44681477 ; Sure: https://github.com/we-promise/sure
- Actual reports: https://actualbudget.org/docs/reports-filters/reports
- Firefly data importer providers: https://docs.firefly-iii.org/how-to/data-importer/import/third-party-providers/ ; SimpleFIN quota issue mentioned in that search: https://docs.firefly-iii.org/tutorials/data-importer/simplefin/
- SimpleFIN Bridge: $1.50/month or $15/year, up to 25 institutions and 25 apps, daily refresh; holdings with quantity and cost basis for some brokerages (per Sure's docs). https://bridge.simplefin.org and https://www.mintlify.com/we-promise/sure/integrations/simplefin
- hledger changelog and lot spec: https://github.com/hledgerorg/hledger/blob/master/hledger/CHANGES.md and https://github.com/hledgerorg/hledger/blob/master/doc/SPEC-lots.md
- GnuCash features: https://www.gnucash.org/features.phtml
- Portfolio Performance: https://www.portfolio-performance.info/en/ ; PDF import: https://help.portfolio-performance.info/en/getting-started/updating-portfolio/ ; FIFO fix: https://newreleases.io/project/github/portfolio-performance/portfolio/release/0.86.1
- Wealthfolio: https://wealthfolio.app/ and https://github.com/wealthfolio/wealthfolio
- Paisa: https://paisa.fyi/
- Lunch Money: https://lunchmoney.app/blog/an-update-to-our-annual-plan-minimum-effective-march-15-2026 and https://lunchmoney.app/pricing

Takeaways:
- For lot-accurate cost basis and gains, the plain-text tools (Beancount, Ledger, hledger 2) and Portfolio Performance are the reference implementations. Of the app-style tools, only Wealthfolio advertises both TWR and MWR.
- Budgeting tools (Actual, Firefly III, YNAB) treat investments as a balance; net worth works, investment analysis does not.
- SimpleFIN Bridge ($15/year) is the cheap aggregator the self-hosted world standardised on (Actual, Firefly III, Sure). It refreshes once a day.
- Two investment trackers (Ghostfolio, Wealthfolio) ship MCP servers so an AI client can read the portfolio. That is the same shape as finwright: an agent working on local data.

## 3. Spreadsheet approaches

- Tiller: bank feeds into Google Sheets or Excel daily; the community "Net Worth Snapshot Sheet" stores one row per snapshot and charts 12 months of trend. https://tiller.com/community-templates/net-worth-snapshot-sheet/ (checked 2026-10-12)
- Rob Berger's free investment tracking sheet (often linked from Bogleheads): Holdings tab (account, ticker, shares, asset class from a drop-down; price, value and weighted expense ratio calculated via Google Finance) and Asset Class tab (target vs actual, dollar over/under, red flag when a class drifts 20% of its target). https://robberger.com/investment-tracking-spreadsheet/ (checked 2026-10-12)
- GOOGLEFINANCE limits: a Google employee on the issue tracker says Google Finance is "broken for things like mutual funds"; that matters for 401k funds and collective investment trusts that have no ticker at all. Workarounds are paid add-ons, Yahoo connectors, or typing prices in. https://issuetracker.google.com/issues/288828159 (checked 2026-10-12)
- Bogleheads wiki "Spreadsheets" page returned HTTP 402 to my fetcher; I could not read it.
- Cadence: monthly is the norm. r/Bogleheads posts such as "9 years of net worth tracking" (2025-12-01) and "9.5 years of net worth tracking" (2026-06-01) show long-running half-yearly or monthly snapshot histories (titles read via RSS; comments not readable, 429). Sellers of trackers describe monthly use, and an early-retirement.org member has kept week-end values since 1998. YNAB users report updating investment balances "monthly or less frequently". https://www.reddit.com/r/Bogleheads/comments/1pbnj64/9_years_of_net_worth_tracking/ , https://www.early-retirement.org/threads/net-worth-spreadsheet.15590/post-319409 (checked 2026-10-12)
- Typical fields across templates: date, account, institution, account type (cash, taxable, tax-deferred, Roth, HSA, real estate, vehicle, liability), owner, balance, asset class split, cost basis (taxable only), expense ratio, notes; a summary row of total assets, total liabilities, net worth, and change since the last snapshot.
- r/Bogleheads, 2026-09-18: "How are you calculating your actual return against the index when you deposit every month?" shows the TWR vs MWR confusion that a tool should answer. https://www.reddit.com/r/Bogleheads/comments/1wjuu1t/how_are_you_calculating_your_actual_return/

## 4. Popularity and sentiment

Reddit: I read search RSS feeds (`/r/SUB/search.rss?q=...&t=year`) for r/personalfinance, r/Bogleheads, r/selfhosted and r/plaintextaccounting on 2026-10-12. r/financialindependence returned HTTP 429 twice, and most single-thread comment feeds also hit 429, so I read comments only for one thread. Counts are mentions in the 25 newest relevant posts' bodies, not in comments.

- r/personalfinance (25 posts, Oct 2025 to Sep 2026): Empower 4, Monarch 4, spreadsheet 3, Fidelity 3, Quicken/Simplifi 2, Rocket Money 2, Plaid 2, Excel 2, YNAB, Copilot, Credit Karma, Actual 1 each. Titles include "Good alternative to net worth tracker on Fidelity?", "Monarch over Simplifi?", "Any app/website that can help me visualize my historical net worth?". In the one thread I could read (2026-09-26), answers were "Fidelity Full View or Empower; if you want budgeting pay for Monarch or YNAB", "a piece of paper will do", and the manual-only app remark quoted above.
- r/Bogleheads: posts are about net worth itself, not apps; "What do you use for portfolio tracking?" (2026-06-22) exists but its comments were rate limited.
- r/selfhosted: Actual dominates ("Has anyone used Actual Budget?", and "n8n + Actual Budget + SimpleFIN + Claude" automation post, 2026-04-21); Wealthfolio v3.6 release post (2026-07-08).
- r/plaintextaccounting: new front ends keep appearing (hledger PWA "hedger" 2026-10-12, Beanie Budgets iOS app 2026-09, GlidePath files-first planner with a monthly close 2026-07); a Dec 2025 post asks how to get a net worth plot out of hledger at all.

Hacker News (Algolia API, checked 2026-10-12), top story per tool:

| Tool | Top story | Points | Comments | Date |
|---|---|---|---|---|
| Wealthfolio | Show HN: private, open-source investment tracker | 924 | 263 | 2024-09-06 |
| ProjectionLab | Show HN: I spent 2 years building a personal finance simulator | 766 | 288 | 2023-07-24 |
| Wealthfolio 2.0 | Show HN: now mobile and Docker | 676 | 215 | 2025-11-21 |
| Paisa | Show HN: open-source personal finance manager | 662 | 273 | 2023-09-22 |
| Ghostfolio | Open-source wealth management software | 456 | 150 | 2023-08-31 |
| Firefly III | Self-hosted financial manager | 397 | 152 | 2019-09-09 |
| Beancount | Double-entry accounting from text files | 229 | 123 | 2022-01-30 |
| Beancount | My Beancount books are 95% automatic after 3 years | 229 | 97 | 2025-03-05 |
| Lunch Money | Show HN, multi-currency budgeting | 229 | 132 | 2019-08-27 |
| hledger | Robust plain text accounting | 236 | 94 | 2019-05-26 |

URLs: https://news.ycombinator.com/item?id=41465735 , https://news.ycombinator.com/item?id=36849502 , https://news.ycombinator.com/item?id=46006016 , https://news.ycombinator.com/item?id=37613054 , https://news.ycombinator.com/item?id=37337482 , https://news.ycombinator.com/item?id=20916920 , https://news.ycombinator.com/item?id=30138434 , https://news.ycombinator.com/item?id=43268454 , https://news.ycombinator.com/item?id=20811287 , https://news.ycombinator.com/item?id=20012499

Comparison articles (robberger.com, freenance.io, affiliate sites) agree on a simple consensus: Empower is the free default for net worth and 401k fees, Monarch is the paid all-in-one, Tiller is the spreadsheet pick, Kubera is for alternatives and crypto, ProjectionLab and Boldin are for planning. https://robberger.com/net-worth-calculators/ (checked 2026-10-12)

## 5. Feature patterns worth copying

Snapshot history. Every tool that people keep for years stores dated balances, not just today's totals: Tiller's snapshot rows, Fava's net worth chart, Credit Karma importing Mint's net worth history, the Bogleheads "9.5 years" posts. Manual values must keep their last-updated date (Fidelity notes they "remain static until you manually update it").

Account categories. The useful split for a US individual is by tax treatment and liquidity: cash (checking, savings, CDs, money market), taxable brokerage, tax-deferred (traditional 401k, 403b, traditional IRA), Roth (Roth 401k, Roth IRA), HSA, 529, I bonds and EE bonds (TreasuryDirect, no feed), real estate, vehicles, other physical or private assets, and liabilities (mortgage, auto, student, credit cards). YNAB's split of budget vs tracking accounts and Kubera's assets vs debts both map onto it.

Manual-asset handling. Kubera (any asset, AI appraiser, private positions with IRR), Monarch (Zillow, VIN), Copilot (Zillow URL), Paisa (manual price entries to revalue a house or car) and Fidelity (static manual values) all treat manual assets as first class. Pattern: an asset has a valuation method (ticker, manual, formula like bond accrual, external estimate) and a valuation date.

Asset allocation views. Rob Berger's sheet and Empower's Investment Checkup: target vs actual by asset class, drift threshold, dollar amount to move, ideally across all accounts at once (asset location). Copilot shows equity, ETF, crypto, cash.

Performance. Two numbers answer two questions. Time-weighted return (TWR, Portfolio Performance's TTWROR) removes the effect of deposit timing and compares the investments with an index; money-weighted return (MWR, IRR or XIRR) includes timing and says what the user's own money earned. Portfolio Performance and Wealthfolio show both; hledger's `roi` gives both; Ghostfolio uses ROAI. The Bogleheads "deposit every month" question is exactly this.

Fee analysis. Empower's Retirement Fee Analyzer adds fund expense ratios to plan administrative and advice fees, and notes 401k plan fees range from 0% in large plans to over 1% in small ones; the figures are in the plan's required fee disclosure. Rob Berger's sheet computes a weighted expense ratio per portfolio.

Retirement projections. ProjectionLab (Monte Carlo, historical backtests, Roth conversions, withdrawal order, taxes), Boldin (100+ inputs, what-ifs), Wealthfront Path (from linked accounts plus Social Security), Kubera Fast Forward. All label projections as illustrative.

Data ownership and resilience. Mint's closure, Maybe's archive, Budget Zen's archive, and every aggregator outage argue for local files, documented formats and an import path that does not depend on one aggregator.

## What finwright should copy

1. Keep a dated snapshot ledger as the core record: one row per account per date (monthly by default, plus ad hoc), with balance, source (feed, statement, manual), and as-of date. Net worth is computed from snapshots, never stored alone.
2. Use a fixed account taxonomy with tax treatment and liquidity: cash, taxable, tax-deferred, Roth, HSA, 529, savings bonds, real estate, vehicles, other assets, and each liability type. Report net worth by category and "liquid vs illiquid" and "pre-tax vs after-tax".
3. Treat manual assets as first class: each has a valuation method (ticker price, manual value, bond accrual, estimate) and a staleness warning when the value is older than a threshold (for example 90 days for a house, 35 days for a 401k).
4. Track holdings and lots for taxable accounts in a plain-text form close to Beancount or hledger 2 syntax (`{}` cost basis, FIFO default), so the user can audit or move the data to those tools later. For 401k funds without tickers, accept unit price and units from the quarterly statement.
5. Show both TWR and MWR (XIRR) per account and overall, with one sentence explaining which question each answers, and a benchmark comparison like Wealthfolio's.
6. Build an allocation view across all accounts: target vs actual by asset class, drift flag (a Rob Berger style 20%-of-target band is a sane default), and the dollar amount to rebalance, noting which accounts can rebalance without tax.
7. Copy Empower's fee analyzer: weighted expense ratio per account plus the 401k plan's admin and advice fees from its fee disclosure, projected as dollars lost over 10, 20 and 30 years.
8. Offer a simple retirement projection (deterministic first, Monte Carlo later), clearly labelled illustrative, and leave deep planning to ProjectionLab or Boldin by exporting balances they can read.
9. Do not depend on one aggregator. Imports should accept statement CSV, OFX/QFX, PDF text, and optionally SimpleFIN ($15/year, daily refresh) as the cheap feed; every import is idempotent and keeps the source file.
10. Keep all data in local, documented files with a one-command export (CSV and a Beancount or hledger journal), so a shutdown like Mint's or Maybe's never strands the history.
11. Follow Ghostfolio's MCP permission idea: a "restricted view" mode that shows percentages and allocation without dollar amounts, for sharing or for less trusted AI contexts.
12. Avoid what users complain about: sales funnels (Empower), opaque connection failures (show which source failed and when it last worked), and cost-basis nagging on cash positions (Simplifi).
