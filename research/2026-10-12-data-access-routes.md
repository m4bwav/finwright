# Data access routes for a personal net-worth tool (Track C)

Research date: 2026-10-12. Every source below was checked on 2026-10-12 unless a different date is given. Where only secondary sources were reachable (several primary pages returned 403, 404 or timed out), the claim is marked "secondary" and should be confirmed before code depends on it.

Scope: how a US individual can get their own data out of banks, brokerages, a 401k, savings bonds and other investments, and where free price data comes from, for a local, read-only finwright skill set.

Related: [2026-10-12-method-rules-and-security.md](2026-10-12-method-rules-and-security.md) (Track on method rules and security, written in the same session).

## 1. Aggregators an individual can use directly

| Service | Can one hobbyist get live access in 2026? | Cost | Data | Notes |
|---|---|---|---|---|
| SimpleFIN Bridge | Yes, it is built for this | $1.50/month or $15/year, up to 25 institutions and 25 apps | Balances and transactions; investment holdings not in the published protocol | Read-only by design; token pasted by the user; one Access URL with Basic Auth |
| Plaid Trial plan | Yes, for teams created on or after 2026-04-15 (US/CA), "Personal use" signup | Free, capped at 10 Production Items (removing an Item does not free a slot) | Transactions, Balance, Investments, Liabilities, Statements and more | Replaced Limited Production for new teams; auto-approved for most |
| Teller | Yes, free developer tier | Free up to 100 live connections; paid Transactions $0.30 per enrollment per month | Balances, transactions, identity | US banks only (claims 7,000+ institutions); no brokerages |
| MX | Developer sandbox; production through sales | Not published | Banks, some investments | Not realistic for one person (secondary) |
| Finicity (Mastercard) | Sandbox only; production through sales | Not published | Banks, investments | Not realistic for one person (secondary) |
| Yodlee | Developer sandbox; paid plans reported from about $500/month | Not realistic | Broad, including investments | Secondary |
| Akoya | A network for aggregators and institutions, not open to individuals | n/a | Token-based API from Fidelity and big banks | Reached indirectly through Plaid, Yodlee and others |

Sources:
- SimpleFIN protocol (setup token, `/claim`, `/accounts` with `start-date`, `end-date`, `pending`, `balances-only`; balances and transactions only; 402 when payment lapses): https://www.simplefin.org/protocol.html (checked 2026-10-12).
- SimpleFIN Bridge price "$1.50 per month, or $15.00 per year", 25 institutions and 25 apps: search snippet of https://bridge.simplefin.org (the page itself timed out on 2026-10-12, so this is from the search index). The Bridge redirects to https://beta-bridge.simplefin.org/. Third-party guide describing partial brokerage support: https://www.mintlify.com/we-promise/sure/integrations/simplefin (secondary).
- Plaid Trial plan (free, 10 Production Items, teams created on or after 2026-04-15, "Personal use" at dashboard.plaid.com/signup, eight products including Investments, no new Limited Production for US/CA): https://support.plaid.com/hc/en-us/articles/39994173227159-What-is-the-Plaid-Trial-plan and https://support.plaid.com/hc/en-us/articles/16110110883479 (both returned 403 to the fetcher; content read from search snippets 2026-10-12). Plaid billing overview: https://plaid.com/docs/account/billing. Plaid CLI `plaid trial` command: https://plaid.com/docs/resources/cli/ .
- Plaid Portal for consumers (see and revoke connections, delete data at my.plaid.com): https://support-my.plaid.com/hc/en-us/articles/4420192760855-What-is-the-Plaid-Portal .
- Teller free tier and prices: https://teller.io/ and https://docs.rutter.com/platforms/banking/teller (secondary for the price list; teller.io/pricing returned 404 on 2026-10-12).
- MX, Finicity, Yodlee developer terms: https://www.itechguides.com/products/mx/ , https://apispine.com/yodlee-vs-finicity (secondary, low confidence).
- Akoya origin (incubated at Fidelity, spun off 2020 with 11 banks and The Clearing House): https://bankinnovation.net/allposts/biz-lines/retail/fidelity-spins-off-akoya-in-latest-data-sharing-business-shake-up/ ; PNC blocked screen scraping 2023-11-01 and moved to Akoya: https://advisor.morningstar.com/Enterprise/VTC/October2023OpenBankingUpdate.pdf .

What is realistic for one hobbyist in 2026:
1. SimpleFIN Bridge for bank and card accounts: cheapest, simplest, read-only, and the protocol is tiny (one GET). It does not give positions, so it is a balances source for investment accounts at best.
2. Plaid Trial for up to 10 logins, especially for the Investments product (holdings and investment transactions) at brokerages and 401k recordkeepers that Plaid reaches. Ten Items is enough for one household if used carefully; a deleted Item still counts, so test against Sandbox first.
3. Teller as a free bank-only alternative.
4. MX, Finicity, Yodlee and Akoya are not realistic for an individual.

Caveat on all aggregators: data leaves the user's computer and passes through a third party, so "locally" holds only for storage and computation, not for collection.

## 2. The open banking rule (CFPB Section 1033)

Status as of 2026-10-12:
- The 2024 final rule (12 CFR Part 1033) was published 2024-11-18 with compliance dates from 2026-04-01 (largest providers) to 2030-04-01. Source: https://files.consumerfinance.gov/f/documents/cfpb_personal-financial-data-rights-final-rule_2024-10.pdf and https://www.consumerfinance.gov/compliance/compliance-resources/other-applicable-requirements/personal-financial-data-rights/ (page last modified 2026-01-06, checked 2026-10-12).
- 2025-08-22: CFPB issued an Advance Notice of Proposed Rulemaking (reconsideration) covering who may be an authorized third party, security, privacy, and whether banks may charge fees. Comments closed 2025-10-21. Source: https://www.federalregister.gov/documents/2025/08/22/2025-16139/personal-financial-data-rights-reconsideration .
- 2025-10-29: the court in Forcht Bank, N.A., et al. v. CFPB (E.D. Ky.) stayed the compliance dates; reporting describes CFPB as enjoined from enforcing the rule until it finishes reconsideration. Sources: the CFPB page above; https://www.cozen.com/news-resources/publications/2026/section-1033-compliance-date-open-banking-rule-enjoined-and-under-reconsideration ; https://www.mvalaw.com/data-points/cfpb-enjoined-from-enforcing-personal-financial-data-rights-rule-1033 .
- 2026-08-06: CFPB sent a revised proposal (the "Personal Financial Data Rights Reconsideration" NPRM) to OIRA. As of 2026-09-28 it was still under review; reporting expects it to replace the fee ban with a conditional fee approach and to tighten the authorized-representative standard. A projected path is NPRM late 2026, comments early 2027, final rule mid to late 2027. Sources: https://www.consumerfinancemonitor.com/2026/08/06/cfpb-sends-new-section-1033-open-banking-proposal-to-oira-for-review/ (403 to the fetcher; snippet) and https://risktemplate.com/blog/2026-09-28-cfpb-section-1033-rewrite-data-access-fees-open-banking-fintech-2026/ (secondary). I found no publication in the Federal Register as of 2026-10-12.
- Bank fees: JPMorgan Chase signed paid data-access contracts with Plaid (September 2025), then Yodlee, Morningstar and Akoya (November 2025); prices undisclosed. Sources: https://news.bloomberglaw.com/banking-law/jpmorgan-plaid-data-fee-deal-shifts-open-banking-battlefield and https://www.emarketer.com/content/jpmorgan-open-banking-fees-plaid-yodlee-morningstar .
- FDX: the CFPB recognized the Financial Data Exchange as a standard-setting body in January 2025, recognition through January 2030; FDX API v6.4 (2025) is the latest version I found. Sources: https://financialdataexchange.org/fdx-feed/fdx-recognized-by-cfpb-as-a-standard-setting-body-a-step-forward-for-open-banking/ and https://openbankingtracker.com/standards/fdx (secondary for version).

What it means for a personal tool: there is no enforceable consumer right to API access today, and FDX endpoints are offered to approved aggregators, not to individuals. Banks may start passing data fees through to aggregators, which could raise SimpleFIN or Plaid prices or drop small banks. Design finwright so the aggregator is one optional input among file imports, not the foundation.

## 3. Direct bank routes

- OFX Direct Connect: dying. The GnuCash wiki says most if not all banks that offered it had stopped by 2024, and ofxhome.com no longer exists. Source: https://wiki.gnucash.org/wiki/OFX . Bank of America reportedly dropped it a few years ago: https://lists.gnucash.org/pipermail/gnucash-user/2025-April/116178.html . Vanguard blocked all Direct Connect sessions on 2025-02-20 and pointed users to Web Connect (manual QFX download): https://community.quicken.com/discussion/7960283/merged-not-able-to-update-any-vanguard-accts and https://www.banktivity.com/support/articles/?p=4231 . Fidelity's endpoint `https://ofx.fidelity.com/ftgw/OFX/clients/download` is still listed in the GnuCash table but its current status is unverified.
- ofxtools / ofxget (Python): `ofxget list` shows known server nicknames; request types `prof`, `acctinfo`, `stmt`, `stmtend`, `tax1099`; `--write` saves config, `--savepass` stores the password in the OS keyring; Chase needs a generated CLIENTUID and a website identity check within 7 days. Source: https://ofxtools.readthedocs.io/en/latest/client.html . Worth keeping as a parser for downloaded OFX/QFX files even where the server route is gone.
- File downloads (CSV, QFX/OFX "Web Connect", PDF statements): the one route every institution still offers. Quicken states Web Connect (QFX) downloads continue to be supported even where Direct Connect ended (Quicken community, link above). PDF statements are the fallback for anything else and can be parsed locally.
- Consumer bank APIs: effectively none for individuals at major US banks; access is through aggregators.

## 4. Brokerages and retirement accounts

| Institution | Individual API? | Practical route |
|---|---|---|
| Charles Schwab | Yes: Trader API, "Individual" product, two approval steps (developer account, then product access); 120 non-order requests per minute; OAuth with about 30-minute access tokens and a 7-day refresh token that needs a browser login to renew | API for positions and balances, with a weekly re-login; or CSV export |
| Interactive Brokers | Yes: Flex Web Service (token plus query id, XML/CSV of positions, trades, cash, NAV), optional IP lock, you choose token lifetime | Best fully unattended read-only route of any broker |
| Fidelity | No retail API | CSV downloads (Portfolio Positions, Account History); aggregators reach it through Akoya |
| Vanguard | No API; Direct Connect blocked 2025-02 | CSV or QFX download from the website |
| E*Trade | Yes, OAuth 1.0a, keys after intent survey and agreement; tokens die at midnight ET | Possible but daily login makes it near manual |
| Alpaca, Tradier | Yes, API-first brokers | Only relevant if the user holds accounts there |
| Robinhood | Official API for crypto only (launched 2024-05-30); none for stocks | CSV/statements, or aggregator |

Sources:
- Schwab: approval flow and 120 requests/min https://wealth-lab.com/Discussion/Schwab-broker-extension-Beta-release-11565 (secondary); 7-day refresh token with no programmatic renewal https://github.com/48n116w/tda_to_schwab and https://cran.nics.utk.edu/cran/web/packages/schwabr/readme/README.html (secondary; developer.schwab.com returned 403). Portal: https://developer.schwab.com .
- IBKR Flex Web Service (enable in Performance & Reports > Flex Queries; new token invalidates old; chosen lifetime; optional IP restriction): https://www.ibkrguides.com/clientportal/performanceandstatements/flex-web-service.htm . Query sections (Open Positions, Cash Report, NAV): https://docs.rs/crate/ib-flex/0.2.3 (secondary).
- Fidelity CSV files `Portfolio_Positions_*.csv` and `History_for_Account_*`: https://beancount.io/fr/tools/csv-to-beancount/fidelity and Fidelity FAQ https://fidelity.com/customer-service/faqs-exporting-account-information .
- E*Trade OAuth 1.0a and midnight ET expiry: https://cran.nics.utk.edu/cran/web/packages/etrader/readme/README.html (secondary).
- Robinhood Crypto Trading API: https://robinhood.com/us/en/newsroom/robinhood-crypto-trading-api/ (2024-05-30). Stocks: no official API per https://blog.traderspost.io/article/does-robinhood-have-an-api (secondary, 2025-09).
- Alpaca docs: https://docs.alpaca.markets/ .

401k recordkeepers:
- Fidelity NetBenefits: transaction history downloads exist (CSV, sometimes QIF, plan dependent); a positions file is reported both as missing and as present, so it varies by plan. Sources: https://www.fundmanagersoftware.com/faq_fidelitynb.php and https://www.fundmanagersoftware.com/forum/viewtopic.php?p=28540 (secondary).
- Empower: Quicken downloads broke in 2023; the CSV a user got had dates and amounts only, no fund or shares. Source: https://community.quicken.com/discussion/comment/20342753 (secondary). The Empower Personal Dashboard (ex Personal Capital) exports transactions to CSV: https://support-personalwealth.empower.com/hc/en-us/articles/18679551671703-Export-Transactions-To-A-CSV-File-Through-Our-Web-Application .
- Vanguard, Principal, John Hancock, Voya: I found no participant API. The universal route is the quarterly statement PDF plus the balance page; aggregators (Plaid Investments, Yodlee, MX) reach many of them, coverage varies per plan.
- CIT funds with no ticker: prices come from the recordkeeper portal or fund fact sheet; CUSIPs do not resolve on public quote sites; a few CITs have Nasdaq Fund Network symbols. Sources: https://www.im.natixis.com/en-us/insights/portfolio-construction/2025/evaluating-collective-investment-trusts-cits and https://www.marketsmedia.com/wilmington-trust-nasdaq-provide-symbols-for-cits/ . Practical rule for finwright: value 401k CIT holdings at the balance the recordkeeper reports (units times unit value from the statement), and do not try to price them from a market API.

## 5. Bonds

Savings bonds (TreasuryDirect):
- No API for holdings. Electronic bonds: log in and read the holdings page (or the account's "Current Holdings" totals); paper bonds: the Savings Bond Calculator (paper only; it cannot save inventories in Chrome or Edge). Source: https://treasurydirect.gov/BC/SBCPrice and https://paymentintegrity.treasury.gov/savings-bonds/savings-bond-calculator .
- Machine-readable values: Fiscal Data "Savings Bonds Value Files" give redemption values for Series E, EE, I and Savings Notes per $25 bond by issue month and redemption month, released semiannually; date range 1992-05-31 to 2026-11-30, last updated 2026-05-01; CSV, JSON and XML via `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/`. A zero value means inside the 12-month minimum hold. Source: https://fiscaldata.treasury.gov/datasets/savings-bond-value-files/ . The older Redemption Tables dataset was discontinued in May 2023: https://fiscaldata.treasury.gov/datasets/redemption-tables/ . Printable I bond tables: https://www.treasurydirect.gov/forms/sav4652.pdf .
- eyebonds.info offers I bond and TIPS tables and downloads (page content not readable by the fetcher on 2026-10-12): https://eyebonds.info/ .

Valuation rules:
- I bond composite rate = fixed + 2 x semiannual inflation + fixed x semiannual inflation. May to October 2026: fixed 0.90%, semiannual inflation 1.67%, composite 4.26%. Next reset 2026-11-01. Interest is added twice a year and compounds. Cashing before 5 years forfeits the last 3 months of interest, and TreasuryDirect and the calculator already exclude those 3 months from shown values. Source: https://treasurydirect.gov/savings-bonds/i-bonds/i-bonds-interest-rates/ .
- EE bonds issued since May 2005: fixed rate for life; interest accrues monthly and compounds semiannually; guaranteed to double at 20 years (one-time adjustment); then a 10-year extension to 30 years. Source: https://savingsbond.gov/news/2005/release-04-04 and https://tipswatch.com/2020/11/03/i-bonds-fixed-rate-holds-at-0-0-ee-bonds-still-double-in-20-years/ . Same 3-month penalty before 5 years.
- Recommendation: compute values from the Fiscal Data value file (it already contains Treasury's rounding), and use the formula only to project forward.

Marketable bonds held at a broker (Treasuries, TIPS, corporates, munis):
- Use the broker's own position value; it includes a price and usually shows accrued interest separately. Net worth should add accrued interest to clean price (dirty price), or use the broker's total.
- Free independent checks: FINRA TRACE for corporate and agency trades (free for personal, noncommercial use) and MSRB EMMA for municipal trades. Sources: https://www.finra.org/sites/default/files/AppSupportDoc/p015158.pdf and https://msrb.org/Press-Releases/MSRB-Launches-New-Tool-EMMA-Improve-Investor-Access-Municipal-Securities-Pricing .
- Treasury yield curves: Treasury Daily Interest Rate XML feed (par yield curve, bill rates, real yield curve, monthly filter `field_tdr_date_value_month=yyyymm`): https://home.treasury.gov/treasury-daily-interest-rate-xml-feed . Fiscal Data API for Treasury datasets: https://fiscaldata.treasury.gov/api-documentation/ . FRED also carries Treasury constant maturity series.

## 6. Free market price data

| Source | Free limit | Key needed | Mutual fund NAV | Terms for personal use |
|---|---|---|---|---|
| Yahoo Finance via yfinance | Unofficial; IP-level 429 blocks after bursts (anecdotal ~100 requests then pause) | No | Yes (tickers like VFIAX) | yfinance says personal use only, not affiliated with Yahoo; Yahoo terms restrict automated collection |
| Stooq | CSV now needs an API key (since about March 2026), daily hit quota; bulk ZIP database | Yes (via CAPTCHA) | Limited | Check site terms |
| Alpha Vantage | 25 requests per day | Yes | Not stated on pricing page | Paid from $49.99/month |
| Tiingo | 50 requests/hour, 1,000/day, 500 unique symbols/month, 1 GB/month | Yes | Yes (lists 45k+ ETFs and mutual funds) | "own personal use"; Power $30/month |
| Financial Modeling Prep | 250 calls/day, end-of-day data | Yes | Limited | Display or redistribution needs agreement |
| Finnhub | About 60 calls/minute | Yes | Not on free tier (secondary) | Non-commercial |
| Twelve Data | 8 credits/minute, 800/day | Yes | NAV only on Pro | "personal, internal, and non-commercial" |
| FRED | Not published; may be capped at any time | Yes | No (macro and rates) | Third-party series need owner permission beyond personal use; required notice text |
| OpenFIGI | 25 mapping requests/minute without key, 25 per 6 seconds with key | Optional | n/a: maps CUSIP to FIGI and ticker | Free and open |

Sources:
- yfinance rate limits: https://github.com/ranaroussi/yfinance/discussions/2431 ; Yahoo terms: https://legal.yahoo.com/us/en/yahoo/terms/product-atos/finance/index.html .
- Stooq key requirement: https://github.com/pydata/pandas-datareader/issues/1012 ; bulk files https://stooq.com/db/h/ .
- Alpha Vantage: https://www.alphavantage.co/premium/ .
- Tiingo: https://www.tiingo.com/about/pricing .
- FMP: https://site.financialmodelingprep.com/de/education/other/do-you-need-a-credit-card-to-use-financial-modeling-prep (FMP FAQ: 429 after the daily cap, no charge); limits from https://multiples.vc/compare/fmp-api-alternatives (secondary).
- Finnhub: https://github.com/Finnhub-Stock-API/finnhub-js/issues/2 and https://metacpan.org/pod/Finance::Quote::Finnhub (secondary; finnhub.io/pricing did not render).
- Twelve Data: https://twelvedata.com/pricing .
- FRED terms: https://fred.stlouisfed.org/docs/api/terms_of_use.html .
- OpenFIGI: https://www.openfigi.com/api/documentation .

For a net-worth tool that prices once a day, Tiingo's free tier is the best documented primary source with explicit personal-use terms and mutual fund coverage; yfinance is a convenient fallback with no key but no guarantee. Cache every price locally with its date and source, so a failed fetch falls back to the last known price instead of breaking the total.

## 7. Screen scraping and AI browser agents

- Sharing credentials with a third party usually breaches the bank's online banking agreement; whether Regulation E protection for unauthorized transfers survives that is unsettled, and Reg E bars agreements from imposing more liability than the regulation allows. Source: https://www.dwt.com/blogs/financial-services-law-advisor/2019/12/open-banking-api-liability and https://legalclarity.org/screen-scraping-financial-data-risks-and-legal-status/ (secondary).
- Banks are moving aggregators off scraping onto token APIs (PNC 2023, Akoya), and bot-like logins trip fraud controls and MFA challenges; a locked account is a real cost.
- AI browser agents: prompt injection in logged-in sessions is a documented attack class (Brave's Comet research; Black Hat USA 2026 found Comet, Opera's AI browser and ChatGPT Atlas still vulnerable; OpenAI said in December 2025 that prompt injection is unlikely ever to be fully solved). Sources: https://www.malwarebytes.com/blog/news/2025/08/ai-browsers-could-leave-users-penniless-a-prompt-injection-warning and https://aviatrix.ai/threat-research-center/no-perfect-fix-ai-browser-prompt-injection-flaws-2026/ (secondary).
- Security view for finwright: the agent should never log in to a bank, brokerage, TreasuryDirect or recordkeeper, never hold passwords or MFA codes, and never drive a browser on a financial site. The user logs in themselves and drops downloaded files into an inbox folder; the agent only reads files and read-only tokens (SimpleFIN Access URL, IBKR Flex token, Plaid access tokens) stored in the OS keyring.

## Recommended data routes

Ranking key: safety first (read-only, no credentials with the agent), then cost, then effort. "Inbox" means the user downloads the file themselves and saves it into a finwright inbox folder that the skill parses locally.

| Account type | 1st choice | 2nd choice | 3rd choice | Avoid |
|---|---|---|---|---|
| Checking, savings, credit cards | Inbox: CSV or QFX download monthly (free, safest, 5 minutes) | SimpleFIN Bridge ($15/year, read-only, automatic balances and transactions) | Plaid Trial (free, 10 Items) or Teller (free, 100 connections) | OFX Direct Connect (mostly gone), scraping |
| Taxable brokerage at IBKR | IBKR Flex Web Service with an IP-locked token (free, unattended, read-only) | Inbox: Flex or activity CSV | Plaid Investments | Trading APIs with order scope |
| Schwab | Inbox: positions CSV | Schwab Trader API, Individual tier, read-only use, weekly re-login | Plaid Investments | Storing Schwab login |
| Fidelity, Vanguard brokerage or IRA | Inbox: positions and history CSV (Fidelity Portfolio_Positions, Vanguard CSV or QFX) | Plaid Investments (via Akoya for Fidelity) | SimpleFIN for balances only | Direct Connect, scraping |
| 401k (NetBenefits, Empower, Vanguard, Principal, John Hancock, Voya) | Inbox: quarterly statement PDF or balance-page CSV; take the reported balance and units; CIT funds at the recordkeeper's unit value | Plaid Investments if the recordkeeper is covered | Manual entry of balance | Pricing CITs from market APIs |
| Savings bonds (I, EE) | Holdings entered once (series, issue month, denomination) from TreasuryDirect, valued locally from the Fiscal Data Savings Bonds Value Files (free, no login) | Formula with composite rate for projections | Savings Bond Calculator for paper bonds | Agent logging in to TreasuryDirect |
| Marketable Treasuries, TIPS, corporates, munis at a broker | Broker's position value including accrued interest, from the same CSV or API as the account | TRACE (corporate) or EMMA (muni) for a spot check | Yield curve from Treasury XML feed for estimating | Third-party bond price scrapers |
| Price data for stocks, ETFs, mutual funds | Tiingo free tier with local cache | yfinance fallback, polite pacing | Alpha Vantage or Twelve Data for spot gaps; OpenFIGI to map CUSIPs to tickers | Any route that needs redistribution rights |
| Rates and macro | FRED and Treasury XML feed | Fiscal Data API | n/a | n/a |

Overall shape: build finwright file-first (CSV, QFX/OFX via ofxtools parser, PDF statements), with optional connectors in this order of value: IBKR Flex, SimpleFIN Bridge, Plaid Trial, Schwab Trader API. Keep the agent out of every login, keep tokens in the OS keyring, and treat the CFPB 1033 situation as a reason not to depend on any one aggregator.

## Open questions to verify before building

1. SimpleFIN Bridge current price and whether it returns any holdings in `extra` (bridge page timed out on 2026-10-12).
2. Plaid Trial terms text (support pages returned 403); confirm whether Investments works on the Trial for the common 401k recordkeepers.
3. Schwab refresh token lifetime on the official portal (secondary sources say 7 days).
4. Which institutions still offer QFX downloads, and which 401k plans allow a positions file.
5. Whether the CFPB NPRM has cleared OIRA (check reginfo.gov) at the next refresh.
