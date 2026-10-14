# The tools people use (2026-10-12)

Read this when the user asks which app, MCP server or AI feature to use, or whether something already does a job. Counts and prices change. Re-check before recommending a purchase. Full reports: [AI tools and MCP](../../../research/2026-10-12-ai-tools-and-mcp-landscape.md), [net worth trackers](../../../research/2026-10-12-net-worth-trackers.md).

## Big AI vendors (all read-only, all through Plaid)

- **Perplexity** account linking, 2026-04-09.
- **ChatGPT Personal Finance**, 2026-05-15: US Pro preview, with an Intuit tie-in planned. It follows OpenAI's purchase of Roi.
- **Gemini** reads Plaid-linked accounts through Google Wallet.
- **Claude**: an unannounced "Claude Money" section was spotted in the iOS app around 2026-09-14. Watch it.
- **anthropics/financial-services** (about 39.6k stars) is professional tooling (comps, LBOs, KYC). Nothing in it covers a person's own accounts.

## MCP servers worth knowing

| Server | Kind | Note |
|---|---|---|
| Monarch (`api.monarch.com/mcp`) | official, OAuth, beta, **paused since 2026-06-29** | The only vendor-run multi-institution personal finance MCP. Consent grants read and write together. Use its read tools if it returns, with finwright keeping its own snapshot ([monarch.md](monarch.md)). |
| Robinhood Agentic Trading MCP | official | Reads every Robinhood account, trades only in a separate funded account. Use the read side only. |
| Copilot Money | official read-only, waitlist | A community server (84 stars) reads the Mac app's local cache with no network calls. |
| Public.com, Alpaca (1,018 stars) | official | Trading brokers. Not needed. |
| Monarch community (robcerda, 416) | community | Session in the OS keyring (check on Windows: early versions fell back to a plaintext file). Run with `MONARCH_MCP_READ_ONLY=1`. Built on the monarchmoneycommunity fork of the unmaintained hammem library. |
| Actual Budget (256), YNAB (153), Lunch Money (109), Firefly III (86) | community | Wrap a budgeting app. Investments appear as balances only. |
| IBKR (221), Schwab (jkoelker, 65, read-only default) | community | Check whether they store a password or TOTP secret before using. |
| hledger-mcp (65, `--read-only`), beanquery-mcp (53) | community | Query a plain-text ledger. A good fit if the user moves records to hledger or Beancount. |
| Ghostfolio, Wealthfolio | shipped with the app | Portfolio trackers. Ghostfolio's "restricted view" hides dollar amounts. |

Plaid's own two MCP servers are developer tools (dashboard and sandbox), not a way to read a person's own accounts. No personal-finance Claude skill has real adoption (none found above about 10 stars). Nothing covers TreasuryDirect savings bonds. That gap is the reason fw.py's bond valuation exists.

## Net worth and portfolio apps

| App | Price | Feed | Strong at | Weak at |
|---|---|---|---|---|
| Empower | free | Yodlee | net worth, 401k fee analyzer | advisor sales calls above about $100k; broken connections |
| Fidelity Full View | free | eMoney | free aggregate view | Fidelity-centric |
| Monarch | $99.99/yr | Plaid, Finicity, MX (switchable) | won the post-Mint migration; official MCP | subscription |
| Copilot | $95/yr | own | polish | no Android |
| Kubera | $250/yr | several | manual and alternative assets | price |
| ProjectionLab | $129/yr | none (manual) | retirement projections | no linking |
| Boldin | $144/yr | aggregator | retirement planning | price |
| Tiller | $99/yr | Yodlee into spreadsheets | spreadsheet control | setup |

Open source (GitHub stars on 2026-10-12):

- Maybe: 54.2k, archived July 2025. Its fork Sure has 10.5k and is active.
- Actual: 29.5k. Firefly III: 24.9k. Ghostfolio: 9.4k. Wealthfolio: 9.2k.
- Beancount: 6.1k. Ledger: 6.1k. hledger: 4.8k. GnuCash: 4.4k. Portfolio Performance: 4.1k. Paisa: 3.2k.

Only the plain-text tools and Portfolio Performance track cost basis by lot properly. Wealthfolio and Portfolio Performance show both TWR and MWR.

## What people actually do (most common first)

1. Export CSVs and ask the AI.
2. Use an aggregator app with its MCP server or API.
3. Feed SimpleFIN or Plaid into a self-hosted Actual or Firefly III.
4. Keep plain-text ledgers.

Praise goes to pulling scattered accounts together. Complaints are about arithmetic errors, who is liable for bad advice, privacy, and Plaid failing to link some institutions. r/Bogleheads removes AI-generated answers.

## Watch list for each refresh

- Claude Money: launch date, data provider, whether it is read-only.
- ChatGPT Personal Finance reaching Plus users.
- Copilot Money's official MCP leaving the waitlist.
- Official YNAB or Lunch Money MCP servers.
- Plaid's hobbyist pricing and SimpleFIN's price.
- CFPB 1033 rewrite (at OIRA since 2026-08-06).
