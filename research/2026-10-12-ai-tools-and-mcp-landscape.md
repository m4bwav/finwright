# AI tools, MCP servers and plugins for personal finance: landscape on 2026-10-12

Research for finwright, a personal-finance plugin for US individuals tracking bank accounts, 401(k)s, bonds (including TreasuryDirect savings bonds) and other investments, with a net worth they compute themselves. Track A covers the AI-native tools: MCP servers, Claude plugins and skills, what the big AI vendors ship, AI-heavy consumer apps, and what people say about using them.

All facts were checked on 2026-10-12 unless a row says otherwise. GitHub star counts and push dates come from `gh api repos/OWNER/REPO` on that day; download counts come from api.npmjs.org (last month) and pypistats.org (last month). Stars are a rough popularity signal only, and npm counts for `npx`-launched MCP servers are inflated because each client start can count as a download.

Related: this is Track A; the other research notes in [this folder](./) cover the rest of the finwright research.

## 1. The short version

- The biggest change of 2026 is that the large AI vendors now link bank accounts themselves, all through Plaid and all read-only: Perplexity (April 9), ChatGPT Personal Finance (May 15, Pro preview), Gemini through Google Wallet, and Anthropic is testing "Claude Money" in the iOS app (spotted 2026-09-14, not announced).
- Consumer finance apps are shipping official remote MCP connectors: Monarch (`https://api.monarch.com/mcp`, beta, OAuth sign-in, write needs permission), Robinhood (Agentic Trading MCP, reads all Robinhood accounts, trades only in a separate funded account), Public.com (trading MCP), Alpaca (official, 1,018 stars). Copilot Money has an official read-only MCP on a waitlist.
- Plaid's own MCP servers are for developers (dashboard diagnostics, sandbox toolkit). Neither hands an agent a person's live bank data.
- In the open-source world, the most-starred finance MCP servers wrap an app that already does the aggregation: Monarch (robcerda, 416 stars), Actual Budget (s-stefanov, 256), YNAB (calebl, 153), Lunch Money (akutishevsky, 109), Firefly III (etnperlong, 86), Copilot Money (84). Plain-text accounting has smaller ones: hledger-mcp (65), beanquery-mcp (53).
- Anthropic's own `anthropics/financial-services` repo (39,568 stars) is for professionals (banking, PE, fund admin, advisors). Nothing in it targets an individual's own net worth.
- Nobody, official or community, covers TreasuryDirect: no API, no aggregator, only scraper scripts with 1 to 3 stars. That is a real gap finwright has to fill by hand.

## 2. MCP servers for personal finance data

### 2.1 Official (vendor-run) servers

| Server | Vendor | Transport and auth | Read or write | What it reaches | Source (checked 2026-10-12) |
|---|---|---|---|---|---|
| Monarch MCP Connector (beta) | Monarch | Remote, `https://api.monarch.com/mcp`; add as a custom connector, sign in to Monarch in the browser | Read; write (for example re-categorising) only with permission | Everything in Monarch: accounts, transactions, budgets, net worth | [Monarch help center](https://help.monarch.com/hc/en-us/articles/50207234679956-Monarch-MCP-Connector) (page returned 403 to the fetcher; content taken from the search snippet) |
| Robinhood Agentic Trading MCP (beta since 2026-05-27) | Robinhood | Remote, `https://agent.robinhood.com/mcp/trading`; `claude mcp add robinhood-trading --transport http ...` | Reads balances, positions, history across the customer's Robinhood accounts; trades only inside a separate funded "Agentic account", cash only | Robinhood only | [Robinhood support](https://www.robinhood.com/us/en/support/articles/agentic-trading-overview/), [Finder](https://www.finder.com/stock-trading/robinhood-agentic-accounts) |
| Public.com MCP | Public | Claude Desktop template; one directory says hosted OAuth at mcp.public.com, Public's guide describes a local process (not resolved) | Read and live trading; Public says trades through MCP are deemed authorised by you | Public brokerage and IRA | [Public API docs](https://public.com/api/docs/templates/claude-desktop-mcp), [Public MCP page](https://public.com/mcp-trading) |
| alpacahq/alpaca-mcp-server | Alpaca | Local, API key | Read and trade | Alpaca brokerage | [GitHub](https://github.com/alpacahq/alpaca-mcp-server): 1,018 stars, pushed 2026-10-12, MIT; PyPI `alpaca-mcp-server` 42,247 downloads last month |
| Copilot Money official MCP | Copilot Money | Waitlist | Read-only; the beta does not yet show Plaid-connected accounts | Copilot Money data | Stated in the [community copilot-money-mcp README](https://github.com/ignaciohermosillacornejo/copilot-money-mcp); I found no Copilot announcement |
| Plaid Dashboard MCP | Plaid | Remote, `https://api.dashboard.plaid.com/mcp/`; OAuth client_credentials, `mcp:dashboard` scope, 15-minute tokens | Read-only diagnostics | Item debugging, Link analytics, usage. Not consumer balances or transactions | [Plaid docs](https://plaid.com/docs/resources/mcp/) |
| plaid/ai-coding-toolkit | Plaid | Local | Sandbox only | Mock data, docs search, sandbox tokens | [GitHub](https://github.com/plaid/ai-coding-toolkit): 31 stars, pushed 2026-09-11, MIT |
| beancount.io hosted MCP | beancount.io (commercial) | Remote, OAuth 2.1 or static token | Read (BQL) and edit with dry-run, edits land as git commits | A ledger hosted at beancount.io | [beancount.io/mcp](https://beancount.io/mcp); listed in the official MCP registry as `io.beancount/beancount` |

I found no official MCP server from YNAB, Lunch Money, Fidelity, Schwab, Vanguard, Empower or TreasuryDirect (searches on 2026-10-12). Schwab and Fidelity are covered only by community servers.

### 2.2 Community servers, ranked by GitHub stars

Read/write and data-access columns come from each README (grepped on 2026-10-12).

| Rank | Repository | Stars | Last push | License | Read or write | How it gets data |
|---|---|---|---|---|---|---|
| 1 | [robcerda/monarch-mcp-server](https://github.com/robcerda/monarch-mcp-server) | 416 | 2026-10-12 | MIT | Read and write | Monarch's private GraphQL API through the MonarchMoneyCommunity fork; sign-in happens outside Claude (browser session cookies recommended, or email, password and TOTP), session saved to the OS keyring |
| 2 | [s-stefanov/actual-mcp](https://github.com/s-stefanov/actual-mcp) | 256 | 2026-10-12 | MIT | Read and write (create and delete transactions, categories, rules) | Your own Actual Budget server URL and password; npm `actual-mcp` 2,375 downloads last month |
| 3 | [code-rabi/interactive-brokers-mcp](https://github.com/code-rabi/interactive-brokers-mcp) | 221 | 2026-07-21 | MIT | Read and trade | IBKR OAuth in the browser, or headless with password and TOTP in config; Flex Web Service token for statements |
| 4 | [calebl/ynab-mcp-server](https://github.com/calebl/ynab-mcp-server) | 153 | 2026-10-05 | MIT | Read and write | YNAB personal access token in an env var; optional Cloudflare Worker mode keeps the token as a Worker secret behind GitHub sign-in |
| 5 | [akutishevsky/lunchmoney-mcp](https://github.com/akutishevsky/lunchmoney-mcp) | 109 | 2026-08-03 | MIT | Full CRUD, bulk delete, balance history | Lunch Money API token; uses TOON encoding to save tokens; npm 23,782 downloads last month (inflated by npx) |
| 6 | [rgarcia/ynab-mcp-server](https://github.com/rgarcia/ynab-mcp-server) | 97 | 2026-07-16 | MIT | Read and write, "with custom skills" | YNAB token |
| 7 | [etnperlong/firefly-iii-mcp](https://github.com/etnperlong/firefly-iii-mcp) | 86 | 2025-06-12 | MIT | Read and write | Firefly III personal access token; tool presets to cut token use |
| 8 | [ignaciohermosillacornejo/copilot-money-mcp](https://github.com/ignaciohermosillacornejo/copilot-money-mcp) | 84 | 2026-10-12 | MIT | Default read-only from the local cache with zero network calls; `--live-reads` and `--write` opt in | Reads the Copilot Mac app's local LevelDB/Firestore cache; live mode uses a browser session |
| 9 | [sudowealth/schwab-mcp](https://github.com/sudowealth/schwab-mcp) | 81 | 2025-06-02 | none | Read | Schwab developer API OAuth |
| 10 | [agigante80/actual-mcp-server](https://github.com/agigante80/actual-mcp-server) | 66 | 2026-10-13 | MIT | Read and write | Actual server URL, password, budget sync id |
| 11 | [jkoelker/schwab-mcp](https://github.com/jkoelker/schwab-mcp) | 65 | 2026-10-07 | MIT | Read-only by default; trading needs a Discord or Signal approval backend | Schwab OAuth in the browser, token file in `~/.local/share/schwab-mcp/token.yaml` |
| 12 | [iiAtlas/hledger-mcp](https://github.com/iiAtlas/hledger-mcp) | 65 | 2026-02-28 | MIT | `--read-only` flag (recommended), otherwise add, remove with dry-run, rewrite | Local hledger journal files, follows `include`s |
| 13 | [vanto/beanquery-mcp](https://github.com/vanto/beanquery-mcp) | 53 | 2025-04-01 | MIT | Read (BQL) | Local Beancount file |
| 14 | [oliverames/ynab-mcp-server](https://github.com/oliverames/ynab-mcp-server) | 40 | 2026-10-11 | MIT | Read-only defaults, gated writes | YNAB token |
| 15 | [verygoodplugins/robinhood-mcp](https://github.com/verygoodplugins/robinhood-mcp) | 39 | 2026-07-29 | MIT | Read-only | Robinhood login (unofficial); now overshadowed by Robinhood's official MCP |
| 16 | [jamiew/monarch-mcp](https://github.com/jamiew/monarch-mcp) | 25 | 2026-09-29 | MIT | Read and write | Monarch credentials, run locally; PyPI `monarch-mcp-jamiew` 1,189 last month |
| 17 | [mhajder/ghostfolio-mcp](https://github.com/mhajder/ghostfolio-mcp) | 22 | 2026-10-12 | AGPL-3.0 | Read and write | Ghostfolio URL and API token; PyPI 433 last month |
| 18 | [henfrydls/actual-budget-mcp](https://github.com/henfrydls/actual-budget-mcp) | 13 | 2026-10-13 | MIT | Safe writes: every delete previews first | Actual server |
| 19 | [StdioA/beancount-mcp](https://github.com/StdioA/beancount-mcp) | 11 | 2025-05-08 | MIT | Query and add transactions | Local Beancount file |
| 20 | [jackstein21/tiller-mcp-server](https://github.com/jackstein21/tiller-mcp-server) | 10 | 2026-04-18 | MIT | Read | Tiller's Google Sheet |
| 21 | [JosueM1109/personal-finance-mcp](https://github.com/JosueM1109/personal-finance-mcp) | 8 | 2026-04-20 | MIT | Read-only | Your own Plaid developer keys, self-hosted |
| - | [duckling1169/simplefin-mcp](https://github.com/duckling1169/simplefin-mcp), [aminamos/simplefin-mcp](https://github.com/aminamos/simplefin-mcp) | 0 | 2026-10-02 / 2026-09-03 | MIT | Read | SimpleFIN access URL |
| - | Wealthfolio MCPs ([datamoc/WFmcp](https://github.com/datamoc/WFmcp), [toomy1992/wealthfolio-mcp](https://github.com/toomy1992/wealthfolio-mcp)) | 1 each | 2026 | none | Read | Local Wealthfolio data; one README says Wealthfolio's built-in AI makes it obsolete |
| - | [jaketuring999/fidelity-mcp](https://github.com/jaketuring999/fidelity-mcp) | 0 | 2026-10-11 | none | Read-only | Unofficial; accounts, holdings, tax lots |

Search method: `gh search repos "<app> mcp" --sort stars` for each app named in the brief, plus the official registry (`registry.modelcontextprotocol.io/v0/servers?search=...`), on 2026-10-12. Smithery, PulseMCP, mcp.so and Glama list mostly the same projects (for example [Glama's Monarch listing](https://glama.ai/mcp/servers/jamiew/monarch-mcp), [mcpservers.org Actual listing](https://mcpservers.org/en/servers/agigante80/actual-mcp-server)); the official registry also holds Monarch entries from pulsemcp, jamiew and others, several YNAB servers (smirnovlabs hosted OAuth, hs737 "read-only by default"), and `ai.senaro/personal-finance` (deterministic calculators for 401k, mortgages and payoff, with each rule cited).

### 2.3 Base platforms the servers wrap (for scale)

| Project | Stars | Last push | License | Note |
|---|---|---|---|---|
| [maybe-finance/maybe](https://github.com/maybe-finance/maybe) | 54,230 | 2025-07-24 | AGPL-3.0 | Archived; the company shut down. [we-promise/sure](https://github.com/we-promise/sure) (10,494 stars, active) is the community continuation |
| [actualbudget/actual](https://github.com/actualbudget/actual) | 29,462 | 2026-10-12 | MIT | Bank sync through SimpleFIN or GoCardless |
| [firefly-iii/firefly-iii](https://github.com/firefly-iii/firefly-iii) | 24,883 | 2026-10-12 | AGPL-3.0 | |
| [ghostfolio/ghostfolio](https://github.com/ghostfolio/ghostfolio) | 9,443 | 2026-10-12 | AGPL-3.0 | Investment and net worth tracker |
| [wealthfolio/wealthfolio](https://github.com/wealthfolio/wealthfolio) | 9,171 | 2026-10-13 | AGPL-3.0 | Local desktop app with a built-in assistant (local Ollama or cloud) per its [App Store listing](https://apps.apple.com/app/id6732888445) |
| [beancount/beancount](https://github.com/beancount/beancount) | 6,074 | 2026-08-23 | GPL-2.0 | |
| [hledgerorg/hledger](https://github.com/hledgerorg/hledger) | 4,764 | 2026-10-12 | GPL-3.0 | |
| [hammem/monarchmoney](https://github.com/hammem/monarchmoney) | 537 | 2025-11-13 | MIT | The unofficial Monarch library most servers started on. Unmaintained: open issues since January 2026 report the API domain move from api.monarchmoney.com to api.monarch.com and a gql 4.0 break; forks ([keithah/monarchmoney-enhanced](https://github.com/keithah/monarchmoney-enhanced), the MonarchMoneyCommunity fork) carry it now |

### 2.4 Security models seen

- Best: vendor-run remote MCP with OAuth sign-in in the browser, scoped and revocable (Monarch, Robinhood, Plaid Dashboard). Credentials never sit in a config file.
- Good: local server, read-only by default, writes behind a flag (copilot-money-mcp, hledger-mcp `--read-only`, oliverames YNAB, jkoelker Schwab with out-of-band Discord or Signal approval for trades).
- Common and weak: long-lived API tokens or email, password and TOTP secret in `.mcp.json` or env vars (most YNAB, Lunch Money, Firefly, IBKR headless, older Monarch servers). The colvint Monarch README itself warns the MFA secret "gives full access to your account" ([mcpservers.org](https://mcpservers.org/en/servers/colvint/monarch-money-mcp)).
- Reminder that applies to all of them: a local server still sends the numbers to whichever hosted model you connect. The copilot-money-mcp README says it plainly: using it with a hosted model means "knowingly sharing your financial data with that AI provider".
- Claude Code routines: an HN commenter warned that in routine mode all MCP tools, including write tools, are always allowed ([HN 47894690](https://news.ycombinator.com/item?id=47894690)). A read-only server is the only safe default for unattended runs.

## 3. Claude plugins and skills

| Item | Popularity | What it is | Source (checked 2026-10-12) |
|---|---|---|---|
| [anthropics/financial-services](https://github.com/anthropics/financial-services) ("Claude for Financial Services" marketplace) | 39,568 stars, pushed 2026-09-21, Apache-2.0 | 10 named agents (pitch, earnings reviewer, model builder, GL reconciler, KYC screener...) and vertical plugins (financial-analysis core, investment-banking, equity-research, private-equity, fund-admin, operations, claude-for-financial-advisors), plus LSEG and S&P partner plugins. Connectors are professional data vendors (FactSet, Morningstar, S&P, Moody's, PitchBook, LSEG, Daloopa, Box, Egnyte). Install: `claude plugin marketplace add anthropics/financial-services` then `claude plugin install financial-analysis@claude-for-financial-services`. Nothing targets an individual's own accounts; outputs are framed as drafts for a qualified professional | Repo README |
| [JoelLewis/finance_skills](https://github.com/JoelLewis/finance_skills) | 206 stars, pushed 2026-07-18, MIT | 81 skills across 7 plugins for financial services work (trading ops, exchange connectivity and the like). Professional, not personal | Repo |
| mohitagw15856/pm-claude-skills `net-worth-statement` | Registry listing only | Builds an assets-minus-liabilities statement with liquidity and debt ratios and a tracking cadence | [claudeskills.info](https://claudeskills.info/skills/mohitagw15856/pm-claude-skills/net-worth-statement/) |
| Monarch, Copilot Money, "wealth-flow" net worth summary, afrexai personal-finance skills | Registry listings only | Monarch skill drives Playwright or reads a CSV export; wealth-flow builds a monthly balance table and flags any account moving more than $500 without explanation | [claudskills.com](https://claudskills.com/skills/monarch-money/), [wealth-flow](https://claudskills.com/skills/wealth-flow-build-net-worth-summary/), [afrexai](https://claudskills.com/skills/afrexai-personal-finance/) |
| Claude connectors directory | - | A July 2026 review found no consumer "check my bank account" connector in Anthropic's directory; Plaid's listing there is the developer tools one | [Carly blog, 2026-07-16](https://www.usecarly.com/blog/claude-plaid-integration/) |
| "Claude Money" (unannounced) | Press | A Money section in a Claude iOS test build ("Understand your money with Claude", link your bank accounts), spotted around 2026-09-14. Anthropic has not confirmed provider, scope, read-only status or date | [BleepingComputer](https://bleepingcomputer.com/news/artificial-intelligence/anthropic-wants-claude-to-analyze-your-bank-account-and-financial-data), [Cybernews](https://cybernews.com/ai-news/anthropic-claude-bank/), [TechRepublic](https://www.techrepublic.com/article/news-anthropic-claude-money-bank-accounts/) |

No personal-finance Claude skill or plugin has meaningful adoption yet (none above 10 stars that I could find on 2026-10-12). The popular pattern is MCP server plus ad hoc prompting, not a packaged skill.

## 4. Big-AI consumer finance features

| Vendor | What shipped | Access and scope | Source (checked 2026-10-12) |
|---|---|---|---|
| OpenAI | ChatGPT Personal Finance preview, 2026-05-15, built with Plaid; "Finances" in the sidebar or "@Finances, connect my accounts"; dashboard of portfolio performance, spending, subscriptions, upcoming bills. Intuit integration on the roadmap (tax impact of a stock sale, card approval odds). Followed the April 2026 acqui-hire of Hiro's team; the October 2025 Roi acqui-hire (one person, Roi shut down 2025-10-15) came first | US Pro only at launch, Plus later; read-only per press; 12,000+ institutions | [Plaid blog](https://plaid.com/blog/chatgpt-personal-finance-plaid/), [The Next Web](https://thenextweb.com/news/openai-chatgpt-personal-finance-plaid), [OpenAI post](https://openai.com/index/personal-finance-chatgpt/) (403 to the fetcher), [TechCrunch on Roi](https://techcrunch.com/2025/10/03/with-its-latest-acqui-hire-openai-is-doubling-down-on-personalized-consumer-ai/) |
| Perplexity | Plaid integration widened on 2026-04-09 from brokerage to checking, savings, cards and loans (mortgage, auto, student); Perplexity Computer builds net worth dashboards, budget trackers, debt payoff planners | Desktop, US and Canada signed-in users; Computer features Pro and Max | [Plaid blog](https://plaid.com/blog/plaid-perplexity-ai-financial-insights-integration/), [Perplexity blog](https://hub-prod.perplexity.ai/hub/blog/plaid-integration-provides-full-view-of-personal-finances) |
| Google | Gemini reads Google Wallet transactions from Plaid-linked bank and card accounts (spending questions, budgets); cannot buy or change accounts; unlinking does not delete processed history. Experian credit app in Gemini | US, 18+, gradual rollout | [Android Authority](https://androidauthority.com/google-wallet-gemini-integration-3716563), [Financial IT](https://financialit.net/news/infrastructure/experian-becomes-first-personal-finance-app-integrated-google-gemini) |
| Microsoft | No consumer account-linking feature found; Copilot for Finance is enterprise (Excel, Dynamics, SAP) | - | [UC Today](https://uctoday.com/what-is-microsoft-copilot-for-finance-the-latest-copilot) |
| Anthropic | Claude Money in test only (section 3) | - | as above |

Pattern: every vendor uses Plaid, and every one is read-only. None of them covers TreasuryDirect, and the big brokerages (Fidelity especially) are the usual weak spot in Plaid coverage (a Driggsby founder on HN: "some like Fidelity aren't" covered, [HN 47894690](https://news.ycombinator.com/item?id=47894690)).

## 5. AI-first and AI-heavy consumer apps

| App | AI feature | Evidence (checked 2026-10-12) |
|---|---|---|
| Monarch | AI Assistant launched in the 2025-12-18 Winter Release; plus the official MCP connector (section 2.1). Core $99.99/yr, Plus $199/yr | [Monarch blog](https://www.monarch.com/blog/winter-release), [Penny Hoarder](https://www.thepennyhoarder.com/budgeting/monarch-money-review/) |
| Copilot Money | Copilot Intelligence (categorisation) and Money Assistant chat (beta); official read-only MCP on a waitlist | [Copilot FAQ](https://www.copilot.money/faq) |
| Robinhood | Cortex (analysis, December 2025); Agentic Trading MCP (May 2026, crypto added July) | [Crypto Briefing](https://cryptobriefing.com/robinhood-agentic-trading-crypto-equities/), Robinhood support page above |
| Public.com | Alpha research assistant (2023); investor-defined AI agents announced 2026-03-31; official MCP | [FX News Group](https://fxnewsgroup.com/forex-news/retail-forex/public-introduces-ai-based-investing-co-pilot-alpha/), [e-commerce.news](https://e-commerce.news/story/public-rolls-out-ai-agents-to-automate-trading-strategies) |
| Origin | "AI Advisor", marketed as the first SEC-regulated AI financial adviser (through Origin Investment Advisory, CRD 305353); $99/yr | [Business Wire](https://www.businesswire.com/news/home/20250909759834/en/Origin-Unveils-First-AI-Financial-Advisor-Regulated-by-the-SEC-Outsmarts-Every-Leading-AI-Model-on-the-CFP-Exam) |
| Cleo | Chat-first budgeting app ("roast mode"), tens of millions of registered users, about $280M ARR mid-2025 per Sacra (secondary) | [CB Insights](https://www.cbinsights.com/company/cleo-ai) |
| Rocket Money | Subscription cancelling and bill negotiation; company claims 10M+ users | [Bankrate](https://www.bankrate.com/banking/savings/ai-apps-to-help-you-save-money/) |
| Schwab, Fidelity, Vanguard | No named customer-facing chat assistant launch found in 2026; Schwab talks of AI investment on its Q2 2026 call | [Webull transcript](https://www.webull.com/news/15265729153868800) |
| Range, Kubera, Empower, Wealthfront, Albert | Searches returned nothing specific for 2026 AI launches; not verified | - |

## 6. What people actually say

Hacker News (Algolia API, 2026-10-12):

- [Could a Claude Code routine watch my finances?](https://news.ycombinator.com/item?id=47894690) (2026-04-24, 83 points, 138 comments) is the main thread. Points made: a Plaid staffer said Plaid had just opened a hobbyist-friendly self-serve sign-up, so an individual can now get production keys; SimpleFIN Bridge (used by Actual Budget) and Tiller (Google Sheets) recommended as cheap individual-friendly feeds; one user syncs Tiller to Supabase and lets Claude or Codex query it, with Monte Carlo cash-flow forecasts; another wrote a Lunch Money CLI with an LLM and runs tagging rules by cron; one user had the Vanguard holdings pulled over MCP, then dividend dates researched and turned into calendar events. Skeptics: "Tiller works great ... it's never going to hallucinate", liability when an LLM gives bad advice, and "how little people care about their data" when handing transactions to AI companies.
- [Show HN: Fungible](https://news.ycombinator.com/item?id=48271942) (2026-05-25, 30 points): local terminal finance app, your own Plaid keys or CSV, optional BYO-key chatbot and MCP server; [repo](https://github.com/tomfunk/fungible) 114 stars, Plaid tokens encrypted at rest under `~/.fungible/`. Commenters liked "local agent and local files for everything" and asked for ledger or beancount storage.
- Many small Show HNs for MCP-first finance apps (Cadence Money "no AI features, just an MCP server", Cairn "read-only by construction", Pane, Finlynq), all under 10 points: the idea is common, no winner yet.
- The ChatGPT Plaid launch got little HN traction (3 points, [48150893](https://news.ycombinator.com/item?id=48150893)); top reply to the OpenAI post: "Surely there's no way this could go wrong!" ([48161189](https://news.ycombinator.com/item?id=48161189)).

Reddit (search RSS, 2026-10-12; several feeds returned HTTP 429 and could not be read: r/fatFIRE, r/MonarchMoney, r/ynab searches; r/ClaudeAI and r/Bogleheads worked on retry):

- r/ChatGPT [Does anyone trust ChatGPT enough to connect their bank account?](https://www.reddit.com/r/ChatGPT/comments/1v1v8ze/does_anyone_trust_chatgpt_enough_to_connect_their/) (2026-07-20): split. "No way I'm linking those accounts ... I choose what I share with it and when" against a user who links checking, Schwab, Robinhood, an Edward Jones IRA and a 401k because it gathers scattered accounts in one place, and who says uploading a CSV is "functionally the same thing".
- r/ClaudeAI [I built my own Monarch-style finance dashboard](https://www.reddit.com/r/ClaudeAI/comments/1wr140j/i_built_my_own_monarchstyle_finance_dashboard/) (2026-09-26): SimpleFIN into Actual Budget as a local backend, React front end built on a Pro plan. Typical of the "build it yourself with Claude" posts (also a QuickBooks replacement post, [1ut0krp](https://www.reddit.com/r/ClaudeAI/comments/1ut0krp/what_magic_have_you_created_using_claude_heres/)).
- r/selfhosted [LamPyrid, an MCP server for Firefly III](https://www.reddit.com/r/selfhosted/comments/1qg8xn5/lampyrid_a_simple_mcp_server_for_firefly_iii/) (2026-01-18): paste receipt and bill images into a dedicated Claude chat and let it log them.
- r/Bogleheads [Why do Bogleheads discourage AI search?](https://www.reddit.com/r/Bogleheads/comments/1py0ajm/why_do_bogleheads_discourage_use_of_ai_search_for/) (2025-12-28): the sub removes AI-generated answers, mirroring the Bogleheads forum rule that AI content is not dependable. Many posts still say "ChatGPT told me..." and ask humans to check it.
- r/personalfinance: a user could not link a Santander Openbank account to "ChatGPT Finance" through Plaid (MFA incompatibility, [1vwnpyk](https://www.reddit.com/r/personalfinance/comments/1vwnpyk/plaid_will_not_link_with_openbank_santander/)); coverage gaps are the most common complaint.

Common workflows, in rough order of how often they came up: export CSVs and paste or upload them (with account numbers masked, [Table Wealth](https://www.tablewealth.com/blog/claude-analyze-your-finances)); an aggregator app (Monarch, Lunch Money, YNAB, Copilot, Tiller) plus its MCP server or API; SimpleFIN or Plaid into a self-hosted Actual or Firefly; plain-text ledgers queried by an agent.

## 7. Top picks for finwright

Ranked by what finwright should do with each.

**Reuse as optional data sources (do not rebuild):**

1. Monarch official MCP connector, if the user uses or adopts Monarch. It is the only vendor-run, OAuth, multi-institution personal finance MCP today, and it already computes net worth. finwright should read from it and keep its own snapshot, not depend on it as the record.
2. Robinhood's official MCP for any Robinhood holdings (read side only). Ignore the trading side.
3. For a self-hosted, credential-light route: SimpleFIN Bridge (individual-friendly, cheap; price to confirm on the official site) or Plaid's new hobbyist self-serve tier with the user's own keys. Either can feed a local store.

**Wrap or learn from (patterns worth copying):**

4. copilot-money-mcp's three-mode design (local read-only default, opt-in live reads, opt-in writes) and its blunt warning about hosted models. finwright should ship read-only by default.
5. hledger-mcp and beanquery-mcp: a plain-text ledger as the durable record, with the agent querying it. A dated, git-tracked snapshot file per account (CSV or a ledger) is easy to audit and needs no third party.
6. jkoelker/schwab-mcp's out-of-band approval for any write, and henfrydls/actual-budget-mcp's "every delete previews first".
7. akutishevsky/lunchmoney-mcp's TOON encoding for token-efficient responses, and etnperlong's tool presets to cut tool-list size.
8. `ai.senaro/personal-finance` in the MCP registry: deterministic calculators that cite their rule. finwright's net worth and 401k math should be scripted and deterministic, never model arithmetic.

**Build ourselves (gaps nobody fills):**

9. TreasuryDirect savings bonds. No API, no aggregator, no MCP. Plan for manual entry of each bond (series, issue date, face value) with value computed from Treasury's published redemption tables, or a periodic manual export. The existing scripts ([DougForrest valuation app](https://github.com/DougForrest/treasurydirect-bulk-valuation-app), [Get-BondValues.ps1](https://github.com/dreary-ennui/Get-BondValues.ps1)) show the redemption-value lookup is feasible.
10. 401k: Plaid coverage of recordkeepers is uneven (Fidelity is the commonly named gap). Plan for statement or CSV import as a first-class path.
11. A net worth snapshot and history that the user owns locally, computed by a script from whatever sources they connect, with manual assets (home, car, bonds) as plain entries. This is the piece every product keeps inside its own cloud, and it is what the HN and Reddit "build it yourself" crowd keeps rebuilding.

**Avoid:**

- anthropics/financial-services as a base: it is professional tooling (comps, LBOs, KYC); borrow only its plugin layout.
- Servers that keep a password or TOTP secret in `.mcp.json` (older Monarch, IBKR headless). Prefer OAuth or a revocable read-only token.
- Anything that trades. The goal is tracking and net worth.
- Building around the unmaintained hammem/monarchmoney library.

Watch list for the next refresh: Claude Money (launch, provider, read-only or not), ChatGPT Personal Finance reaching Plus and the Intuit tie-in, Copilot Money's official MCP leaving the waitlist, whether YNAB or Lunch Money ship official servers, and Plaid's hobbyist pricing.
