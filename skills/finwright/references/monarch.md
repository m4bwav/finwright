# Monarch as a data source

Read this when the user uses Monarch, asks to connect it, or brings a Monarch export. Monarch is a source. fw.py snapshots stay the record. Full research: [monarch skill learnings](../../../research/2026-10-12-monarch-skill-learnings.md) (16 skills and 11 tools on GitHub) and [monarch web survey](../../../research/2026-10-12-monarch-web-survey.md) (directories, registries, packages, forums), both 2026-10-12.

## Routes, in order

1. **"Download account balances" CSV** (no credentials touch the agent). The user saves it to `<data>/inbox/`. Map each Monarch account name once, then import:
   ```
   FW monarch map "Everyday Checking (...1234)" checking
   FW import monarch <file> --dry-run
   FW import monarch <file>            # newest row per account; --all for the full history
   ```
   Columns `Date,Balance,Account`, liabilities negative (from open-source parsers, unverified until the first real file: record the real header in LEARNINGS.md). fw.py stores debts as the amount owed. A positive card balance is kept as a credit and flagged. Unmapped accounts stop the import and are listed. `--skip-unmapped` lists them as counted nowhere. Re-importing the same rows skips them as duplicates.
2. **Official MCP connector** (`https://api.monarch.com/mcp`, OAuth in the browser, revoke under Monarch Settings → Integrations). **Paused since 2026-06-29** after a data provider objected, with no return date as of 2026-10-10 ([web survey](../../../research/2026-10-12-monarch-web-survey.md)). When it returns: its consent screen grants read and write together (no read-only scope; Core plans allow 5 writes a day), so the guard hook is the only barrier. Name the connector so the name contains "Monarch" (it then appears as `mcp__claude_ai_Monarch__*`): the guard recognises money servers by name, and a connector called "Finance" would slip past it. Do not buy Plus for the connector. Read tools only (`GetAccounts`, `GetNetWorthHistory`, `GetInvestments` and other Get/List names). Tool names come from the live list (it is beta). Authorize once, then call. Pass explicit date ranges and report them. Save a tool result to `<data>/inbox/` as a file, then put it through fw.py (`balance set` per account, or a CSV for `import balances`). Never add the numbers up in the reply.
3. **Never:** a skill or server that installs the abandoned `monarchmoney` package or keeps a pickle session (ClawHub `silentknight87/monarch`; the monarchmoneycommunity client writes its session world-readable, issue #75), the private GraphQL API (`api.monarch.com/graphql`), browser automation of app.monarch.com, cookies, CSRF tokens, or a community server that wants the password or TOTP secret in an env var or config file. If the user insists on a community server, use robcerda/monarch-mcp-server with `MONARCH_MCP_READ_ONLY=1`, sign-in through its `login_setup.py` outside Claude, and check that its session landed in the OS keyring (Windows Credential Manager, macOS Keychain, Secret Service), not a plaintext file.

The guard hook denies every Monarch write tool under any server name (`monarch`, `Monarch_Money`, a claude.ai connector), including `refresh_accounts`: it asks every linked bank for a refresh, so it counts as an action.

## Account type map

| Monarch type / subtype | fw.py type |
|---|---|
| depository: checking, savings, money_market, cd, cash_management | `cash` |
| brokerage: brokerage, trust, ugma, utma, cryptocurrency | `taxable` |
| brokerage: st_401k, st_403b, st_457b, ira, sep_ira, simple_ira, thrift_savings_plan, pension, annuities | `tax_deferred` |
| brokerage: roth, roth_401k | `roth` |
| brokerage: health_savings_account | `hsa` |
| real_estate | `real_estate`, revalued with the user's selling-cost haircut |
| vehicle | `vehicle` |
| credit: credit_card | `credit_card` |
| loan: mortgage, home_equity | `mortgage` |
| loan: auto, student, personal, line_of_credit | `loan` |
| st_529, stock_plan, iso, nso, HRA | ask the user |

Savings bonds have no Monarch subtype. Keep valuing them from Treasury's files with `FW bond`, and never import Monarch's number for them. A 401(k) holding both pre-tax and Roth money is one Monarch account: ask the user how to split it.

## Pitfalls

- **Stale links look current.** Linked accounts silently stop updating. Use the account's last-updated date as the row date (not today), and say when Monarch reports that a connection needs re-authentication. fw.py's staleness check does the rest.
- **Hidden, closed and excluded accounts** drop out of Monarch's net worth. List them once and let the user decide whether each one counts. Record the answer in the account's notes.
- **Renamed or relinked accounts** duplicate their history. A rename breaks the name map (the import stops and lists the new name). A relink creates a second account: warn when two Monarch accounts look like the same institution and last 4.
- **Home and car values** are Zillow and VIN estimates. Record them with `--source zillow` or `--source vin_audit`.
- **Some providers report a zero balance.** Coinbase was one. A zero on a funded account is a data error, not a fact.
- **Holdings carry no asset class and no expense ratio**, and 401(k) funds often lack tickers. Classify with `--classes`.
- **Default windows truncate.** Lists stop at 31 days of balances or 1,000 transactions unless dates are passed.
- **Holdings are current only** (`GetInvestments` has no history, and Monarch has no holdings export), so save each pull as a dated file and import it with `FW import holdings`. Net worth history is daily up to 60 days, weekly beyond. Reported "phantom" stale holdings in the connector: check them against the broker.
- **"All time" change jumps** when accounts were added late, and the period change compares two single days. fw.py's own history is the comparison to quote.
- **Some institutions' connections are unreliable** on Monarch: check its own connection status board for the user's institutions, and prefer the institution's CSV where the board shows trouble.

## Cross-check, not the answer

When Monarch shows a net worth, compare it with `FW networth` and explain the gap: excluded accounts, Zillow versus the user's haircut, stale links, bonds. Never report Monarch's figure as finwright's.
