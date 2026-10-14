# Net worth method, 2026 rules and AI safety for finwright

Research track D for finwright, the personal-finance plugin that lets a person compute and track their own net worth with Claude Code. Researched 2026-10-12. Every source below was checked on 2026-10-12 unless a different date is given.

Related: [research index](./) (other tracks of the same research pass sit next to this file).

How to read this file: sections 1 to 6 follow the brief; the last section, "Rules finwright should enforce", is the part to turn into skill text and script checks. Numbers marked **[TS]** are time-sensitive, and the table in section 3 says when each one next changes.

---

## 1. Net worth method

### 1.1 The definition

Net worth is gross assets minus liabilities. The Federal Reserve's Survey of Consumer Finances (SCF) uses exactly that definition: "Net worth is the difference between families' gross assets and their liabilities" (Table 2 note, [Changes in U.S. Family Finances from 2022 to 2025](https://www.federalreserve.gov/publications/files/scf26.pdf), Oct 2026). Matching the SCF definition matters if finwright compares the user to the SCF benchmarks (1.5), because the SCF counts retirement accounts at their full balance and counts the home at the owner's estimate of its value.

The Bogleheads wiki is the recognised community reference for this kind of method, but bogleheads.org returned HTTP 402 to automated fetches on 2026-10-12, so no Bogleheads wording is quoted here. Forum practice found instead (early-retirement.org threads, [example](https://www.early-retirement.org/goto/post?id=2321409)) is split on whether to include the home, cars and pensions. That split is the reason to report several net worth lines rather than one.

### 1.2 What to include and how to value it

| Item | Include | Value at | Notes |
|---|---|---|---|
| Checking, savings, money market, CDs | Yes | Statement balance on the snapshot date | CDs: principal plus accrued interest; subtract the early-withdrawal penalty in the "liquid" line. |
| Taxable brokerage | Yes | Market value (shares times closing price on the snapshot date) | Keep cost basis per lot alongside (section 2.4) so an after-tax estimate is possible. |
| Traditional 401k / 403b / IRA | Yes | Market value (gross) | Also show an after-tax estimate: balance times (1 minus an assumed retirement marginal rate). The rate is the user's assumption, stored in config, never invented by the model. |
| Roth 401k / Roth IRA | Yes | Market value | Already after tax if qualified. |
| HSA | Yes | Market value, cash plus invested | Tax-free for qualified medical spending; treat like Roth in the after-tax line, with a note. |
| Unvested employer match, unvested RSUs | **No** in the headline | Show separately as "unvested" | Not yet owned; forfeitable on leaving. Count only the vested balance from the plan statement. |
| Vested RSUs / ESPP shares | Yes | Market value | Already income-taxed at vest; capital gains from vest price. |
| I bonds, EE bonds | Yes | TreasuryDirect current value | TreasuryDirect values already exclude the last 3 months of interest for bonds under 5 years old (section 4.1). |
| Bonds and TIPS held at a broker | Yes | Market value plus accrued interest (dirty price) | Section 4.2. |
| Home | Yes, but separate line | Automated estimate (Zillow, Redfin) minus estimated selling costs | Zestimate median error is about 1.8% for on-market and about 7% for off-market homes per secondary reports of Zillow's page ([theclose.com](https://theclose.com/how-accurate-is-zillow-zestimate/); Zillow's own page refused automated fetch, 403). A home not on the market should be treated as plus or minus 7% or worse. The selling-cost percentage (commission, transfer tax, concessions) is a user assumption in config. |
| Vehicles | Optional line | Private-party value (KBB, Edmunds), or zero | Many people exclude them; finwright should let the user choose once and keep the choice. |
| Mortgage, HELOC | Yes | Payoff balance (not the statement principal) | The payoff quote includes accrued interest to the payoff date. |
| Auto, student, personal loans | Yes | Payoff balance | |
| Credit cards | Yes | Current balance including pending, not the last statement balance | Paying in full monthly does not make the balance zero on the snapshot date. |
| Pensions, Social Security | No in the headline | Optional present-value line | The SCF does not count defined-benefit pension or Social Security wealth in net worth. |
| Personal property (furniture, collectibles) | No | | Illiquid and hard to value; inflates the number. |

### 1.3 Report several lines, not one

- **Total net worth**: all included assets minus all liabilities (the SCF-comparable number).
- **Liquid net worth**: cash, taxable brokerage, I/EE bonds past 12 months, minus non-mortgage liabilities. Excludes retirement accounts, home and vehicles.
- **Investable assets**: cash plus all investment accounts, no home, no debts.
- **After-tax net worth estimate**: traditional balances discounted by the assumed tax rate, taxable brokerage minus estimated capital gains tax on unrealised gains, home net of selling costs.

### 1.4 Snapshot cadence and consistency rules

- One snapshot per month, dated the last calendar day (or the last business day), is a common and sufficient cadence; quarterly is fine for long-run tracking. Daily tracking adds noise from market moves and no decisions.
- Use the same date for every account in a snapshot. If a statement date differs, record the actual as-of date per line, so the snapshot shows stale lines.
- Never change a valuation method silently (for example switching the home from Zillow to Redfin, or adding the car). Record method changes in the snapshot log with a date, and if possible restate history or mark the break.
- Store raw inputs (balance, price, as-of date, source) and compute totals in a script; never store only the total.

### 1.5 Benchmark: Federal Reserve SCF 2025 (latest edition)

The 2025 SCF was released 2026-10-09 ([press release](https://federalreserve.gov/newsevents/pressreleases/other20261009a.htm); [report PDF](https://www.federalreserve.gov/publications/files/scf26.pdf), Table 2, read from page 12 of the PDF). Thousands of 2025 dollars. **[TS]** The next SCF is the 2028 survey, released around late 2029.

| Age of reference person | Median 2022 | Median 2025 | Mean 2025 |
|---|---|---|---|
| All families | 211.1 | 215.9 | 1,241.5 |
| Under 35 | 42.7 | 33.0 | 135.4 |
| 35 to 44 | 148.4 | 155.6 | 681.9 |
| 45 to 54 | 270.6 | 253.7 | 1,244.5 |
| 55 to 64 | 398.9 | 411.9 | 1,878.0 |
| 65 to 74 | 448.6 | 431.3 | 1,897.6 |
| 75 or more | 367.3 | 504.9 | 1,962.2 |

The SCF unit is the family (household), not the individual, so a single person's number is not directly comparable to a married household's. Use the median, not the mean (the mean is pulled up by the top tail). Interactive data: [SCF chart tool](https://www.federalreserve.gov/econres/scf/dataviz/scf/chart/).

---

## 2. Investment analysis a personal tool should do

### 2.1 Asset allocation and drift

Classify every holding into asset classes (US stock, international stock, bonds, TIPS, cash, real estate, other), using fund look-through for target-date and balanced funds where the user supplies the fund's breakdown. Compute current weights across all accounts as one portfolio, compare to target weights stored in config, and report drift in percentage points.

### 2.2 Rebalancing bands

The widely cited 5/25 rule, credited to Larry Swedroe, rebalances when a large asset class drifts 5 percentage points from target, or a small class drifts by 25% of its own target, whichever is smaller (for a 10% target the band is 7.5% to 12.5%) ([A Wealth of Common Sense](https://awealthofcommonsense.com/2014/03/larry-swedroe-525-rebalancing-rule/), [White Coat Investor](https://www.whitecoatinvestor.com/rebalancing-the-525-rule/)). A common practice is to check on a fixed schedule (quarterly or annually) and act only if a band is breached. finwright should report band breaches and suggest where new money goes first (contributions into the underweight class), but say that rebalancing in taxable accounts can realise gains, and leave the decision to the user.

### 2.3 Fees, expense ratios and the 401k fee disclosure (Form 404a-5)

Plan administrators of participant-directed plans must give each participant a disclosure under 29 CFR 2550.404a-5 ([Cornell LII text](https://www.law.cornell.edu/cfr/text/29/2550.404a-5)). It contains:

- Plan-related information: how to give investment instructions, designated investment alternatives, brokerage windows; **administrative expenses** (recordkeeping, legal, accounting) not included in fund expenses and how they are allocated; **individual expenses** (loan fees, QDRO processing, advice).
- Quarterly statements showing the dollar amount of administrative and individual fees actually charged.
- Investment-related information in a dated comparative chart: 1, 5 and 10-year average annual total returns against a broad-based benchmark, **total annual operating expense as a percentage and in dollars per $1,000 invested**, and shareholder-type fees.
- Timing: annual disclosure at least once in any 14-month period; quarterly fee statements at least once in any 3-month period.

What finwright should compute from it: weighted average expense ratio of the user's actual holdings; annual dollar cost (balance times expense ratio, plus the quarterly admin fees from statements); a comparison against the cheapest fund in the same asset class in the plan's menu; and a long-run cost projection labelled as a projection. All of this is arithmetic for a script.

### 2.4 Returns: time-weighted vs money-weighted

- **Time-weighted return (TWR)** removes the effect of contributions and withdrawals; it measures the investments (what fund prospectuses report). Needs a valuation at every cash flow, or an approximation such as Modified Dietz between valuations.
- **Money-weighted return (MWR, IRR, XIRR)** is the discount rate that sets the present value of all dated cash flows plus the ending value to zero; it measures the user's actual experience including the timing of their contributions. XIRR handles irregular dates.
- For a personal tracker, XIRR per account and for the whole portfolio is the more useful number; TWR (or Modified Dietz) is the right number to compare against a benchmark index. (The Bogleheads wiki page "Calculating personal returns" covers both; it could not be fetched on 2026-10-12, HTTP 402.) Computing XIRR needs every contribution, withdrawal, fee and transfer with its date, so finwright must store cash flows, not just balances. Contributions to a 401k from payroll count as external cash flows; dividends reinvested inside the account do not.

### 2.5 Cost basis, tax lots, dividends

Store each purchase as a lot (date, shares, price, fees). Reinvested dividends create new lots. Report unrealised gain per lot and short-term vs long-term status (held more than one year). Track dividends and interest received per year by account, and separate qualified from ordinary dividends when the 1099-DIV gives the split. Basis for retirement accounts is irrelevant except for after-tax (non-deductible) contributions, which should be tracked as basis (Form 8606 for IRAs). The broker's 1099-B is the authority for reported basis; finwright's lots are a cross-check.

---

## 3. 2026 numbers

All **[TS]**. Annual retirement and HSA limits are set once a year; I bond rates change every May 1 and November 1.

| Item | 2026 value | Source | Next change |
|---|---|---|---|
| 401k / 403b / 457 / TSP elective deferral (402(g)) | $24,500 (2025: $23,500) | [IRS IR-2025-111, Notice 2025-67](https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500) | 2027 limits, expected Oct to Nov 2026 |
| Catch-up, age 50 and over | $8,000 (total $32,500) | same | same |
| Super catch-up, ages 60 to 63 (SECURE 2.0) | $11,250 instead of $8,000 (total $35,750) | same | same |
| Annual additions limit, 415(c) | $72,000 | [Notice 2025-67 analysis](https://www.currentfederaltaxdevelopments.com/blog/2025/11/13/annual-adjustments-to-retirement-plan-limitations-analysis-of-notice-2025-67-for-2026) | same |
| Roth catch-up wage threshold (414(v)(7)) | Catch-ups must be Roth if 2025 FICA wages from the plan sponsor exceeded $150,000 (up from $145,000) | same; [PlanSponsor](https://www.plansponsor.com/what-is-the-wage-threshold-requiring-roth-catch-ups-in-2026/) | indexed yearly |
| IRA contribution limit | $7,500 (2025: $7,000) | IRS IR-2025-111 | 2027 limits |
| IRA catch-up, age 50 and over | $1,100 (now indexed) | same | same |
| HSA, self-only | $4,400 | Rev. Proc. 2025-19 ([summary](https://www.currentfederaltaxdevelopments.com/blog/2025/5/1/irs-issues-2026-inflation-adjustments-for-hsas-and-excepted-benefit-hras-rev-proc-2025-19)) | 2027 limits were due around May 2026; check before 2027 |
| HSA, family | $8,750 | same | same |
| HSA catch-up, age 55 and over | $1,000 (fixed by statute) | same | not indexed |
| HDHP minimum deductible | $1,700 self / $3,400 family | same | yearly |
| I bond / EE bond purchase limit | $10,000 per calendar year per SSN for each series, electronic only; paper I bonds via tax refund ended 2025-01-01 | [TreasuryDirect I bonds](https://treasurydirect.gov/savings-bonds/i-bonds/), [EE bonds](https://treasurydirect.gov/savings-bonds/ee-bonds/) | fixed by regulation |
| I bond, Nov 2025 to Apr 2026 issues | Composite 4.03% (fixed 0.90%, semiannual inflation 1.56%) | [TreasuryDirect rates page](https://treasurydirect.gov/savings-bonds/i-bonds/i-bonds-interest-rates/), [comparing EE and I](https://treasurydirect.gov/savings-bonds/comparing-ee-and-i-bonds) | historical |
| I bond, May to Oct 2026 issues | Composite 4.26% (fixed 0.90%, annualised inflation 3.34%, six-month CPI-U change 1.67%) | [Treasury release 2026-05-01](https://treasurydirect.gov/news/2026/release-05-01-rates/) | **Nov 2026 rate due on or about 2026-11-01; not announced as of 2026-10-12** |
| EE bond, May to Oct 2026 issues | 2.40% fixed, doubles at 20 years | same | Nov 2026 |
| EE bond, Nov 2025 to Apr 2026 issues | 2.50% fixed | comparing EE and I page | historical |

The Roth catch-up rule in detail: SECURE 2.0 section 603 makes catch-up contributions Roth-only for employees whose prior-year FICA wages from that employer exceeded the threshold. Final regulations were issued 2025-09-15 ([IRS IR-2025-91](https://www.irs.gov/newsroom/treasury-irs-issue-final-regulations-on-new-roth-catch-up-rule-other-secure-2point0-act-provisions)). The regulations themselves apply from 2027, but the statutory requirement applies from 2026 (Notice 2023-62's administrative transition ended 2025-12-31), and plans may comply in 2026 with a reasonable good-faith interpretation. For a user: if they are 50 or over and earned more than $150,000 in FICA wages from their employer in 2025, their 2026 catch-ups go in as Roth.

Data quirk: on 2026-10-12 TreasuryDirect's I bond rates page showed 4.26% in its calculation example while some of its text and its mirrors still said 4.03%. The dated press releases are the reliable source; finwright should keep a dated table of rates per issue period rather than scrape "the current rate".

---

## 4. Bonds math

### 4.1 I bonds and EE bonds

- **I bond composite rate** = fixed + (2 x semiannual inflation) + (fixed x semiannual inflation), rounded to two decimals of a percent. Example: 0.0090 + 2(0.0167) + 0.0090(0.0167) = 0.04255, shown as 4.26%. The fixed rate lasts the bond's 30-year life; the inflation part resets every six months on the bond's own issue anniversary, not on May 1 or November 1. The composite cannot go below zero ([TreasuryDirect rates page](https://treasurydirect.gov/savings-bonds/i-bonds/i-bonds-interest-rates/)).
- **Accrual**: interest accrues monthly from the first day of the issue month and compounds semiannually (the six months' interest is added to principal) ([I bonds page](https://treasurydirect.gov/savings-bonds/i-bonds/)).
- **Redemption**: not before 12 months; before 5 years the last 3 months of interest are forfeited. TreasuryDirect and the Savings Bond Calculator already show values net of that penalty for bonds under 5 years.
- **EE bonds**: fixed rate for 20 years, Treasury guarantees the value doubles at 20 years (a one-time top-up if needed, an effective 3.5% a year), 30-year maturity, same 12-month and 3-month rules ([EE bonds page](https://treasurydirect.gov/savings-bonds/ee-bonds/)).
- **Valuation rule for finwright**: take the value from the TreasuryDirect account or the Savings Bond Calculator for the snapshot month. Do not re-derive it by compounding in the model; if a script reproduces it (for forecasts), check the script against TreasuryDirect values, because Treasury computes values on a $25 unit with its own rounding.
- Interest is federally taxable, state-tax-exempt, and reportable on redemption or maturity by default (or yearly if elected). An after-tax line should subtract the deferred federal tax on accrued interest.

### 4.2 Bonds held at a broker

- **Clean price** excludes accrued interest; **dirty (invoice) price** = clean price + accrued interest. Brokers quote clean prices; the buyer pays the seller the accrued interest since the last coupon ([FINRA, Understanding Bond Yield and Return](https://www.finra.org/investors/insights/bond-yield-return); clean/dirty terms are standard market usage, also visible in [FINRA Rule 4210 guide](https://www.finra.org/sites/default/files/2024-08/4210-interp-change-guide-2024.pdf)).
- **Accrued interest** = coupon payment x (days since last coupon / days in coupon period). Day count convention is actual/actual for Treasuries and 30/360 for most corporates and munis (standard convention; the script must take the convention per bond as data).
- **Net worth value** of a bond = (clean price / 100 x face value) + accrued interest. Many brokers show market value excluding accrued interest and list accrued interest separately; add it.
- **Yield to maturity**: the discount rate that equates the bond's remaining cash flows to its dirty price (FINRA, same page). TRACE data shows yield to worst for callable bonds. Solve numerically in a script.

### 4.3 TIPS

Principal is adjusted by CPI; interest is paid every six months at the fixed coupon (never below 0.125%) on the adjusted principal; at maturity the holder gets the greater of adjusted or original principal ([TreasuryDirect TIPS](https://www.treasurydirect.gov/marketable-securities/tips/)). Adjusted principal = face x index ratio, where the index ratio is the reference CPI for the date divided by the reference CPI at issue; Treasury publishes daily index ratios. Broker quotes for TIPS are on a real (unadjusted) basis, so market value = clean price / 100 x face x index ratio, plus accrued interest on the adjusted principal. The inflation accretion is taxable each year as income (phantom income) in a taxable account.

### 4.4 Bond ladders

A ladder is a set of bonds (often Treasuries or TIPS) maturing in successive years to match planned spending. finwright should list rungs by maturity year, show face value, coupon, maturity value (for TIPS, inflation-adjusted), and flag gaps against a spending plan. Value the ladder at market for net worth, and separately show the "hold to maturity" cash flows, which do not change with prices.

---

## 5. Security and privacy of AI plus personal finance

### 5.1 Never give bank credentials to the model or the agent

- Credentials typed into a chat or a file the agent reads are sent to the model provider as part of the prompt and stored in local transcripts. Claude Code stores session transcripts in **plaintext** under `~/.claude/projects/` for 30 days by default (`cleanupPeriodDays`) ([Claude Code data usage](https://code.claude.com/docs/en/data-usage)).
- Bank agreements commonly make the customer liable for transactions made or authorised with their user ID and password and disclaim losses from sharing them with third-party services (examples: [Altamaha Bank](https://www.altamaha.bank/_/kcms-doc/1673/64714/Online-Banking-Agreement-and-Disclosure.pdf), [TD internet banking agreement](https://publish.td.com/content/dam/tdb/document/pdf/personal-banking/internet-banking-agreement.pdf); Canada's regulator warns of the same, [FCAC](https://www.canada.ca/en/financial-consumer-agency/news/2018/03/consumer-alert-fcac-reminds-consumers-of-the-risks-in-giving-banking-information-to-third-party-online-services.html)). Users should read their own banks' agreements before any automated access.
- **Regulation E** (12 CFR 1005.6) caps consumer liability for unauthorized electronic fund transfers at $50, $500 or unlimited depending on how fast the consumer reports ([CFPB official interpretation](https://www.consumerfinance.gov/rules-policy/regulations/1005/interp-6)). The CFPB's 2021 EFT FAQs say a transfer after a consumer is tricked into sharing credentials is still unauthorized and that negligence cannot be weighed ([summary](https://www.consumerfinancialserviceslawmonitor.com/2021/07/cfpb-updates-electronic-fund-transfers-faqs/)). But Reg E excludes transfers by a person the consumer has furnished the access device to and authorised, unless the consumer has told the bank that person is no longer authorised (1005.2(m)). Voluntarily handing credentials to a tool or agent is the weakest position: a bank can argue that what the agent did was authorised. No source found addresses agents or aggregators directly; treat this as unsettled.
- **Open banking**: the CFPB's Section 1033 rule (final 2024-10-22) aimed to move the industry away from credential-based screen scraping to token-based developer interfaces ([CFPB press release](https://www.consumerfinance.gov/archive/newsroom/cfpb-finalizes-personal-financial-data-rights-rule-to-boost-competition-protect-privacy-and-give-families-more-choice-in-financial-services/)). It is under reconsideration (ANPR 2025-08-22) and enforcement is enjoined by a federal court while that runs ([Cooley](https://www.cooley.com/news/insight/2025/2025-08-27-cfpb-reconsiders-section-1033-rule-signaling-potential-overhaul-of-personal-financial-data-rights-framework), [Open Banking Tracker](https://openbankingtracker.com/regulation/usa-1033)). **[TS]** Check status before relying on any 1033 rights.

### 5.2 Preferred data routes, safest first

1. Manual entry of balances, or the user downloading CSV / OFX / QFX / PDF statements themselves and dropping them in an inbox folder the scripts parse.
2. A read-only, token-based aggregator API (OAuth to the bank, scoped read-only, revocable) used by a deterministic script, with the token in the OS credential store, never in the repo or the prompt.
3. Never: an agent driving a browser through a bank login. That puts the password and one-time codes in the agent's context and transcripts, makes the agent able to move money, exposes it to prompt injection from the bank's own pages and ads, and can breach the bank's terms (5.1).

### 5.3 Local-first storage and encryption at rest

- Keep data on the user's own computer in a folder outside any git remote, or in a private repo with the data files encrypted.
- **Disk**: Windows Home editions have no BitLocker manager but may offer Device Encryption, which turns BitLocker on for the OS and fixed drives when the hardware supports it (TPM, Secure Boot); check Settings > Privacy & security > Device encryption ([Microsoft](https://support.microsoft.com/en-us/windows/device-encryption-in-windows-cf7e2b6f-3e70-4882-9532-18633605b7df)).
- **Files**: [age](https://github.com/FiloSottile/age) for whole-file encryption; [SOPS](https://github.com/getsops/sops) encrypts YAML/JSON/ENV/INI files with age, PGP or cloud KMS backends and keeps structure diffable. [git-crypt](https://github.com/AGWA/git-crypt) does not encrypt file names, commit messages or other metadata, cannot revoke access, leaks file length and change timing, and its author says it is not the best tool for encrypting most of a repository; if a whole repo must be encrypted, its README points to git-remote-gcrypt.
- **Git**: a private GitHub repo is still a third-party copy. Put raw statements and account data in `.gitignore` by default, add a pre-commit check that refuses unencrypted data files and full account numbers, and never push finance data to a public repo. Remember git history keeps anything committed once.

### 5.4 What goes to the model provider (Anthropic, Claude Code)

From [Claude Code data usage](https://code.claude.com/docs/en/data-usage) and [Updates to Consumer Terms](https://www.anthropic.com/news/updates-to-our-consumer-terms) (announced 2025-08-28; decision deadline 2025-10-08):

| Plan | Training | Retention |
|---|---|---|
| Consumer (Free, Pro, Max), training setting on | Used to train new models, including Claude Code sessions | 5 years |
| Consumer, training setting off | Not used | 30 days |
| Commercial (Team, Enterprise, API, Bedrock, Vertex) | Not used unless the customer opts in (Development Partner Program) | 30 days standard; zero data retention per organisation by agreement |

- Everything the agent reads (file contents, tool results) is part of the prompt and leaves the machine over TLS. A file the agent never opens is not sent.
- `/feedback`, `/bug` and `/share` send transcripts that are kept 5 years; the optional "can Anthropic look at your session transcript" survey follow-up uploads transcripts and the raw session log, kept up to 6 months. Disable with `DISABLE_FEEDBACK_COMMAND=1` and `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1`, or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`.
- Turning training off later does not remove data already used in a training run.
- Recommendation: the user should confirm the training toggle at claude.ai/settings/data-privacy-controls is off for finance work, and finwright should design so the model sees summaries and redacted figures rather than raw statements.

### 5.5 Prompt injection

OWASP ranks prompt injection first (LLM01:2025). Indirect injection comes from external content the model reads, such as files and web pages; OWASP says no known method fully prevents it and recommends least privilege, running privileged functions in code rather than through the model, human approval for high-risk actions, labelling untrusted content, and deterministic output validation ([OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)). For finwright the untrusted inputs are bank statements, PDFs, emails, broker messages and web pages (fund pages, Zillow). A statement memo line or an emailed "statement" can carry instructions. Mitigations: parse statements with scripts, not by having the model read them; give the model parsed numbers, not raw text; no tool that can move money, send email or post anywhere exists in the plugin; any web fetch is for prices only and its text is treated as data.

### 5.6 Redaction

Store account numbers as the last 4 digits only, and refer to accounts by a nickname ("Fidelity 401k"). Strip full account numbers, routing numbers, SSNs, addresses and dates of birth from imported files before anything the model reads. Add a script check (regex for 8+ digit runs, SSN pattern, routing-number checksum) that runs before the model is shown a file and before any commit.

---

## 6. Disclaimers, scope and the arithmetic rule

### 6.1 Scope

finwright is a personal record-keeping and calculation tool. It is not investment, tax or legal advice, it does not recommend specific securities, and it does not act on accounts. It may describe allocation drift, fees and limits factually and show the arithmetic, and it should say when a question needs a professional.

### 6.2 When to defer to a professional

- **Fiduciary investment adviser** (a registered investment adviser owes an ongoing fiduciary duty; a broker-dealer under Regulation Best Interest owes a best-interest duty only at the time of a recommendation) ([SEC, Clayton speech on Reg BI and the adviser fiduciary duty](https://www.sec.gov/newsroom/speeches-statements/clayton-regulation-best-interest-investment-adviser-fiduciary-duty)): portfolio construction beyond a simple target, annuities, insurance, concentrated stock, retirement income plans.
- **CPA or enrolled agent** (only attorneys, CPAs and enrolled agents can represent taxpayers before the IRS; IRS Directory of Preparers lists credentialed preparers) ([IRS](https://irs.gov/newsroom/choosing-a-reputable-tax-preparer-is-vital-to-tax-security)): Roth conversions, backdoor or mega-backdoor Roth, excess contribution fixes, RSU/ESPP tax, wash sales across accounts, state tax, estimated payments, anything that files a form.
- **Attorney**: estate planning, beneficiary designations disputes, divorce (QDRO), disputes with a bank over unauthorized transfers.
- **The plan administrator or the bank** for what the plan or account actually allows (vesting schedule, loan rules, Roth catch-up implementation).

### 6.3 LLMs doing financial arithmetic: known failure modes

- **FinanceBench** (Islam et al. 2023, [arXiv:2311.11944](https://arxiv.org/abs/2311.11944)): GPT-4-Turbo with a retrieval system incorrectly answered or refused 81% of 150 sample questions about public-company filings.
- **FinQA** (Chen et al. 2021, [arXiv:2109.00122](https://arxiv.org/pdf/2109.00122)): best neural model 61.24% execution accuracy vs 91.16% for human experts; error analysis shows multi-step arithmetic, unit conversions and number-to-year mismatches.
- **XFinBench** (2025, [arXiv:2508.15861](https://arxiv.org/pdf/2508.15861)): in o1's financial calculation errors the main causes were intermediate rounding and applying the wrong formula.
- **FinanceReasoning** (2025, [arXiv:2506.05828](https://arxiv.org/pdf/2506.05828)) and **FinQAPT** (2024, [arXiv:2410.13959](https://arxiv.org/pdf/2410.13959)): wrong formula for the conditions, misreading the problem, and errors with large numbers or many decimals.
- **Program of Thoughts** (Chen et al. 2022, [arXiv:2211.12588](https://arxiv.org/pdf/2211.12588)): having the model write a program and letting an interpreter compute beat chain-of-thought by about 12% on average across math and financial QA datasets. This is the empirical case for "the model writes or calls the script, the script does the math".
- The models in these studies are older than current ones, but the failure types (rounding, formula choice, misread units and dates, lost digits) are structural, and a net worth total is a sum of dozens of numbers where one silent slip is invisible.

Rule: every number finwright reports comes from a deterministic script (Python with `decimal.Decimal` for money, never binary floats for currency; XIRR and YTM by a tested numerical solver), run on the stored data, with the script's output quoted verbatim. The model chooses which script to run and explains the result; it never adds, multiplies, compounds or rounds in its head.

---

## Rules finwright should enforce

1. **No credentials, ever.** The model and the agent never receive, store, type or read bank, broker or 401k passwords, PINs, one-time codes or security answers. If the user pastes one, the agent tells them to change it and does not repeat it.
2. **No browser automation of financial logins.** The plugin has no tool that logs into a bank or broker. Data comes from manual entry, files the user downloads, or a read-only token API called by a script.
3. **Read-only by design.** No feature moves money, places trades, changes contributions or sends messages. Suggestions are text for the user to act on themselves.
4. **All math in scripts.** Every total, return, fee, tax estimate, bond value and limit check is computed by a tested script using decimal arithmetic. The model quotes the script output and shows which script and inputs produced it. A number without a script run behind it is not reported.
5. **Raw inputs with as-of dates and sources.** Store per line: account nickname, value, as-of date, source (statement, TreasuryDirect, Zillow, manual), method. Totals are derived, never stored as the only record.
6. **Consistent methods, logged changes.** Valuation choices (home source and selling-cost percentage, vehicles in or out, after-tax rate) live in one config file; changing one writes a dated log entry and marks the break in history.
7. **Several net worth lines.** Always report total, liquid and investable net worth, plus an after-tax estimate whose assumptions are printed next to it. Unvested match and unvested RSUs are shown separately and never in the headline.
8. **Liabilities at payoff, cards at current balance.** Mortgage and loans at payoff balance; credit cards at current balance including pending.
9. **Bonds at dirty price.** Broker-held bonds and TIPS are valued at clean price plus accrued interest (TIPS times index ratio); savings bonds at the TreasuryDirect value for the month.
10. **Time-sensitive numbers live in a dated data file.** Contribution limits, I/EE bond rates per issue period and SCF benchmarks sit in one file with source URL and checked date; scripts refuse to use a limit for a year that is not in the file, and the skill flags the file as stale after the next change date (2027 limits by about November 2026; I bond rates every May 1 and November 1; next SCF late 2029).
11. **Untrusted content is data.** Statements, PDFs, emails and web pages are parsed by scripts; the model sees parsed fields, and any instruction-like text inside them is ignored and flagged.
12. **Redact before the model reads.** A redaction script strips full account and routing numbers, SSNs, birth dates and addresses before the model sees any imported file; accounts are named by nickname and last 4 digits.
13. **Local-first, encrypted at rest.** Data lives on the user's own computer with disk encryption on; data files that go into any git repo are age- or SOPS-encrypted; raw statements are gitignored; a pre-commit hook blocks unencrypted data and account-number patterns. Never a public remote.
14. **Minimise what reaches the provider.** The agent works from summaries and redacted figures; finance sessions run with the training setting off and with `/feedback` and transcript-sharing surveys disabled; local transcripts are cleaned on the default 30-day cycle or shorter.
15. **Stay in scope and defer.** Every report carries a one-line note that it is personal record keeping, not financial, tax or legal advice. Tax-form questions go to a CPA or enrolled agent, portfolio and product decisions to a fee-only fiduciary adviser, plan rules to the plan administrator.
16. **Benchmarks with caveats.** SCF comparisons use the median for the user's age band, say that the SCF unit is a household, and give the survey year.

## Gaps to close in a later pass

- Bogleheads wiki pages (Net worth, Calculating personal returns, Rebalancing) were blocked to automated fetch (HTTP 402); read them in a browser and add wording if useful.
- Zillow's own accuracy page returned 403; the Zestimate error figures above are from a secondary source.
- The 2027 IRS limits and the November 2026 I bond rate were not yet published on 2026-10-12.
- No primary source found on Regulation E treatment of transfers made by an AI agent holding the consumer's credentials.
