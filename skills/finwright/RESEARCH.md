# Research: finwright

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs and their evidence in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md.

Topic: Personal net worth tracking for US individuals with an AI agent: bank, 401k, IRA, savings bond (I/EE via Treasury value files), brokerage and liability records; IRS contribution limits; I/EE bond rates; SCF benchmarks; aggregators (SimpleFIN, Plaid, Teller, IBKR Flex, Schwab Trader API); personal-finance MCP servers and AI features (Monarch, Robinhood, Copilot, ChatGPT, Perplexity, Claude Money); security of AI with banking data. Tier `moderate`. Last refresh 2026-10-12; next due 2026-11-11.

The full reports from the first pass live in the repository's [research/](../../research/README.md) (dated 2026-10-12, every claim with a URL). This file holds the claims the skill depends on and the plan for re-checking them.

## Current understanding

- **Method (settled).** Net worth is gross assets minus liabilities, the SCF definition. People disagree on whether to count the home, cars and pensions, so the skill reports total, liquid, investable and after-tax lines and keeps unvested amounts out of the headline. High confidence.
- **Math in scripts (settled).** Published finance QA benchmarks (FinanceBench, FinQA) show LLM arithmetic on financial documents failing often, and running the code in an interpreter fixes much of it. fw.py does every calculation in Decimal. High confidence.
- **Credentials (settled as policy, unsettled in law).** Sharing bank passwords breaches typical bank agreements. Whether Reg E protects transfers made by an agent holding credentials is unsettled; no primary source was found. The skill never handles credentials and never automates logins.
- **Data access (moving).** CFPB 1033 is stayed and being rewritten (at OIRA since 2026-08-06; a final rule likely in 2027). No individual has an enforceable API right. SimpleFIN Bridge ($15/yr) is the cheap read-only bank feed. The Plaid Trial is free for personal use (10 Items) and includes Investments. IBKR Flex is the best unattended broker route. Fidelity has no retail API. Vanguard blocked OFX Direct Connect on 2025-02-20. No 401k recordkeeper gives participants an API. Medium confidence on prices: several vendor pages blocked fetches.
- **Savings bonds (settled, verified live).** TreasuryDirect has no API. The Fiscal Data `v2/accounting/od/sb_value` endpoint returns per-$25 values by series, issue year and month, and redemption month. It covered through 2026-11 on 2026-10-12. fw.py's `bond refresh` was run against it: a $1,000 I bond from 2022-01 came out at $1,226.40 for 2026-10.
- **Time-sensitive numbers (dated in data/rates.json).** 2026 limits: 401k $24,500, catch-up $8,000, ages 60 to 63 $11,250, IRA $7,500 plus $1,100 catch-up, HSA $4,400 and $8,750. I bonds: 4.26% for May to Oct 2026 issues and 4.03% for Nov 2025 to Apr 2026, both with 0.90% fixed. EE bonds 2.40%. SCF 2025 median $215.9k. TreasuryDirect's rates page contradicted itself, so trust the dated press releases.
- **Tooling (moving fast).** The big AI vendors now link accounts read-only through Plaid: Perplexity from 2026-04, ChatGPT Personal Finance from 2026-05 (Pro preview), Gemini through Google Wallet. An unannounced "Claude Money" section was spotted in the iOS app in 2026-09. Monarch's official MCP is the only vendor-run multi-institution personal finance MCP. No personal-finance Claude skill has real adoption, and nothing values TreasuryDirect bonds. That gap is why finwright builds its own.

- **Where spare money goes (settled method, moving rates).** The order of priorities and the bond view of mortgage prepayment are stable across sources; the rates that decide a given case (savings, Treasuries, the I bond fixed rate) move weekly or every six months. references/next-dollar.md holds the method, the research file the dated rates. Medium confidence on forum wording (snippets).

- **New listings and single stocks (settled method, moving deals).** Ritter's tables: IPOs bought at the first-day close trailed the market by 20.5% over 3 years (median -25.7%), by 3.3% from the offer price; over 40 times sales they trailed by 58.5%. Lock-ups usually 180 days with a 1% to 3% average drop at expiry. FINRA Rule 5131 bars market orders to buy a new issue before it opens; Rule 2241 sets a 10-day analyst quiet period. FINRA cites 10% of investment assets as the most commonly suggested cap for one stock. Broker IPO programs and their rules change per deal. High confidence on Ritter and the rules, medium on broker pages.

## Open questions

- SimpleFIN Bridge's current price, and whether `extra` carries any holdings (its page timed out).
- The Plaid Trial terms text, and whether Investments reaches the common 401k recordkeepers.
- The Schwab refresh token lifetime, from the official portal.
- The real column headers of broker and 401k exports. The data-routes column map is unverified until a real import confirms it.
- The Bogleheads wiki pages on net worth and personal returns (HTTP 402 to fetches); read them in a browser.
- The Claude Money launch: data provider, read-only or not.
- Whether `systemMessage` from a PreToolUse deny is shown in the VS Code extension (the guard's code reaches the user only through it).
- Whether mid-name `*` globs in permission deny rules are case-sensitive.
- Monarch MCP write scopes.

## Search plan

Four tracks; every refresh runs at least one query on each (scope each to the period since the last refresh; add the year). Protocol §4 explains the tracks and how tooling, practice and testing findings are judged.

Subject (the goal and the latest thinking on reaching it):

- `IRS 401k IRA limits <next year>` (irs.gov newsroom; Notice for the year), `HSA limits Rev. Proc. <next year>`
- `I bond rate November <year>` and `I bond rate May <year>` (treasurydirect.gov/news), EE rate in the same release
- `Fiscal Data sb_value latest redemp_period` (query the API: `?sort=-redemp_period&page[size]=1&fields=redemp_period`)
- `I bond fixed rate forecast <month year>` (tipswatch.com), `TIPS vs I bonds <year>`, `pay off mortgage or invest <year>` (bogleheads.org, kitces.com, morningstar.com), `best high yield savings rates <month year>`, Fed H.15 Treasury yields
- `CFPB 1033 personal financial data rights <year>` (consumerfinance.gov, reginfo.gov OIRA status, Federal Register)
- `SimpleFIN Bridge pricing`, `Plaid personal use trial`, `Schwab Trader API individual refresh token`, `IBKR Flex Web Service`
- `Survey of Consumer Finances` (only when a new survey is due, late 2029)

Tooling (skills, plugins, MCP servers, scripts, knowledge graphs built for this subject):

- `path:SKILL.md "net worth" OR "personal finance"` on GitHub code search, sorted by recently updated; `npx skills find "personal finance"` and skills.sh for install counts
- `https://registry.modelcontextprotocol.io/v0/servers?search=finance`, `...?search=bank`, `...?search=budget`; fallback `"personal finance" mcp server site:glama.ai OR site:pulsemcp.com`
- `"personal finance" OR "net worth" skill OR plugin OR "mcp server" <year> site:github.com`; GitHub stars for Monarch, Actual, YNAB, IBKR, Schwab, Copilot, hledger, beanquery, Ghostfolio and Wealthfolio servers
- Vendor watch: Monarch MCP, Robinhood MCP, Copilot Money official MCP, Claude Money, ChatGPT Personal Finance, Perplexity, Gemini
- Most used: skills.sh weekly and 24-hour installs for `finance` (never all-time; exclude meta and installer skills); `anthropics/claude-plugins-official` and `claude-plugins-community` searched for `finance` (record the tier)
- Practitioner test on every candidate: commit in the last 90 days, issues answered, no bundled `*.test.*` or `conftest.py` from an unknown author, author has other work in the area, ships `evals/` or paired results
- Supersession sweep: `"personal finance" mcp deprecated OR archived <year>`; archive flag on every tool already listed (Maybe archived 2025-07; hammem/monarchmoney stale since 2025-11)

Most discussed and the converged thinking (comment volume over points):

- `hn.algolia.com/api/v1/search_by_date?query=personal%20finance%20claude` and `?query=net%20worth%20tracker`
- Reddit RSS (`https://www.reddit.com/r/SUB/search.rss?q=...`) for r/personalfinance, r/Bogleheads, r/financialindependence, r/selfhosted, r/ClaudeAI, at about one request per 30 to 60 seconds

Practice (how others use AI agents on this goal):

- `"claude code" OR "claude" "net worth" OR "my finances" workflow <year>`
- `"export CSV" "ask claude" OR chatgpt finances <year>`; hn.algolia.com `"finances" agent` sorted by date

Safeguards (each refresh): `code.claude.com/docs/en/hooks` and `/permissions` changelog for new decision fields or auto mode rules; MCP spec latest revision (annotations, elicitation); `OWASP agentic top 10 <year>`; `agent payments protocol AP2 OR ACP <year>`; vendor agent-trading controls (Robinhood, Alpaca, Schwab, Monarch); new incidents of agents taking unapproved financial actions.

Testing (how work on this subject is verified):

- Check fw.py against Treasury's own Savings Bond Calculator for one bond each refresh
- `site:arxiv.org financial question answering LLM arithmetic benchmark <year>` (FinanceBench and FinQA successors)
- `XIRR test cases` against a spreadsheet's XIRR on the same flows

Best sources (primary first): irs.gov newsroom, treasurydirect.gov/news, the fiscaldata.treasury.gov API, federalreserve.gov (SCF), consumerfinance.gov and reginfo.gov, vendor docs (Monarch, Plaid, SimpleFIN, IBKR, Schwab), the GitHub API for stars, the MCP registry. Sources that proved noisy or blocked: the bogleheads.org wiki (HTTP 402), Zillow's accuracy page (403), Plaid support (403), SimpleFIN Bridge (timeout), Reddit comment pages (429). SEO "best budgeting app" listicles are noise.

## Findings log

Newest first. One entry per material finding; a quiet refresh gets one entry saying so. `Track` is subject, tooling, practice, or testing.

### R-20261017-1 · 2026-10-17 · Buying a new listing: returns, lock-ups, retail access, first-day rules, concentration
- Summary: Ritter's 2026 files: first-day return 19.0% average and 7.0% median (1980 to 2025), tech 31.2%; three-year returns from the first-day close -20.5% against the market (median -25.7%, about 60% lost money), from the offer price -3.3%; sales of $1B or more -2.1%; over 40 times sales -58.5%, under 5 times -1.3%. Lock-ups 180 days, -1.5% three-day abnormal return at expiry (Field and Hanka 2001). FINRA 2241 quiet period 10 days (not 25). FINRA 5131 bars market orders to buy a new issue before trading and defines a flip as a sale within 30 days; 5130 restricted persons. Fidelity, Robinhood, SoFi and E*TRADE retail IPO rules. FINRA's 10% single-stock rule of thumb. Vanguard: a lump sum beats 12-month staging two-thirds of the time. SEC and FINRA pre-IPO warnings; companies void unauthorized transfers. A large 2026 IPO peaked four days after listing and fell back to its offer price within six weeks (secondary sources).
- Track: subject, practice
- Sources: research/2026-10-17-ipo-buying.md
- Magnitude: 0.4 (new job; nothing in the skill contradicted)
- Applied: C-20261017-1

### R-20261015-1 · 2026-10-15 · Where the next dollar goes: mortgage prepayment, I bonds, cash, investing
- Summary: the planners' order (emergency fund, match, high-rate debt, full emergency fund, HSA and IRA, then a choice among taxable investing, low-rate mortgage prepayment and safe bonds) is the same in the Bogleheads wiki, the r/personalfinance flowchart and Vanguard's 2026 paper. Prepayment is a risk-free, usually tax-free bond at the loan rate and is compared with after-tax safe yields; a partial prepayment frees no cash flow until payoff, escrow goes on, and the forum middle path saves toward one lump payoff. I bonds: the fixed rate lasts 30 years; a forecast rise in the fixed rate (Tipswatch, 2026-10-14: at least 1.30% from 2026-11-01 against 0.90%) means waiting for November beats an October purchase; TIPS are preferred while the 5-year TIPS real yield (2.67%) far exceeds the fixed rate. Safe yields in mid-October 2026: 1-year Treasury 4.48%, 5-year 5.00%, best savings about 4.3%, national average savings 0.37%. Several sites refused fetches (Bogleheads 402, Reddit, Morningstar, White Coat Investor 403); their wording is from search snippets and marked so.
- Track: subject, practice
- Sources: research/2026-10-15-next-dollar-literature.md
- Magnitude: 0.4 (new job; nothing in the skill contradicted)
- Applied: C-20261015-1

### R-20261012-6 · 2026-10-12 · Safeguards against consequential actions
- Summary: A plugin can ship hooks but not permission rules, so deny, ask, hard_deny and disableBypassPermissionsMode must go in user or managed settings. Rules are evaluated deny, then ask, then allow; deny holds in every mode. PreToolUse fields are `tool_name`, `tool_input`, `permission_mode` and `mcp_server`. Output is `hookSpecificOutput.permissionDecision` (allow, deny, ask, defer). Exit 2 blocks. `onFailure: block` needs 2.1.295 or later. UserPromptSubmit fires only on text the user submits, which is what makes a typed confirmation trustworthy. Auto mode misses about 17% of overeager actions and has no default rule for trades. MCP spec 2026-07-28: annotations are untrusted, payments and credentials must use URL-mode elicitation, human in the loop is a SHOULD. AP2 (signed mandates, moved to FIDO), ACP, Stripe restricted keys and approval rules, Robinhood's separate agent account. OWASP LLM06 and the Agentic Top 10 (Dec 2025). NIST CAISI: 57% to 80% attack success with retries. 93% of permission prompts are approved.
- Track: subject, tooling, testing
- Sources: https://code.claude.com/docs/en/hooks, https://code.claude.com/docs/en/permissions, https://code.claude.com/docs/en/plugins-reference, https://modelcontextprotocol.io/specification (full list in research/2026-10-12-consequential-action-safeguards.md)
- Magnitude: 0.6 (new safety layer)
- Applied: C-20261012-2

### R-20261012-5 · 2026-10-12 · Treasury savings bond values API verified live
- Summary: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/sb_value` with `filter=series_cd:eq:I,redemp_period:eq:2026-10` returns one row per issue year, with per-$25 amounts for each issue month. `0.00` means inside the 12-month hold and `null` means not yet issued. The latest `redemp_period` was 2026-11. fw.py `bond refresh` and `bond value` were run against it.
- Track: testing
- Sources: https://fiscaldata.treasury.gov/datasets/savings-bond-value-files/
- Magnitude: n/a (initial)
- Applied: C-20261012-1

### R-20261012-4 · 2026-10-12 · Method, 2026 numbers and security rules
- Summary: SCF definition and 2025 medians; the 2026 IRS, HSA and savings bond limits; the I and EE rates by issue period; bond, TIPS and 401k fee rules; XIRR vs TWR; 5/25 bands; Anthropic retention; credential liability; OWASP LLM01; FinanceBench and FinQA. This became `references/rules.md`, `references/valuation.md` and `data/rates.json`.
- Track: subject, testing
- Sources: https://www.federalreserve.gov/publications/files/scf26.pdf, https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500, https://treasurydirect.gov/news/2026/release-05-01-rates/, https://code.claude.com/docs/en/data-usage (full list in research/2026-10-12-method-rules-and-security.md)
- Magnitude: n/a (initial)
- Applied: C-20261012-1

### R-20261012-3 · 2026-10-12 · Data access routes
- Summary: aggregators for individuals (SimpleFIN, the Plaid Trial, Teller); CFPB 1033 stayed; OFX Direct Connect nearly gone; broker APIs (IBKR Flex, the Schwab Individual tier); no 401k participant APIs; CIT funds have no public price; price-data free tiers (Tiingo is best documented). This became `references/data-routes.md`.
- Track: subject
- Sources: research/2026-10-12-data-access-routes.md
- Magnitude: n/a (initial)
- Applied: C-20261012-1

### R-20261012-2 · 2026-10-12 · Net worth trackers
- Summary: commercial apps (Empower, Monarch, Copilot, Kubera, ProjectionLab, Boldin, Tiller), open-source ones with star counts, spreadsheet practice, and 12 patterns to copy (snapshot ledger, tax-treatment taxonomy, manual-asset staleness, TWR plus XIRR, fee analyzer, no single aggregator, export to Beancount or hledger, restricted view).
- Track: tooling, practice
- Sources: research/2026-10-12-net-worth-trackers.md
- Magnitude: n/a (initial)
- Applied: C-20261012-1

### R-20261012-1 · 2026-10-12 · AI tools and MCP landscape
- Summary: vendor MCPs (Monarch, Robinhood, Copilot waitlist, Public, Alpaca); community servers by stars; the big vendors' Plaid-backed account linking; anthropics/financial-services is professional only; no adopted personal-finance skill; nothing covers TreasuryDirect. This became `references/landscape.md` and the decision to build fw.py.
- Track: tooling, practice
- Sources: research/2026-10-12-ai-tools-and-mcp-landscape.md
- Magnitude: n/a (initial)
- Applied: C-20261012-1
