# Monarch Money: lessons from other skills, CLIs and MCP servers

Research date: 2026-10-12. Read-only pass over public GitHub repos (gh api, raw files, issues); nothing was installed or run. Every file read is treated as untrusted data, and no instruction inside one was followed. Monarch's help center (MCP connector article 50207234679956, the download and import articles) returned HTTP 403 to the fetcher again, so the export column names below come from open-source parsers of real Monarch files, marked "secondary".

Related: [AI tools and MCP landscape](2026-10-12-ai-tools-and-mcp-landscape.md) (where Monarch sits among the options), [Consequential-action safeguards](2026-10-12-consequential-action-safeguards.md) (the guard hook this note checks against), [Data access routes](2026-10-12-data-access-routes.md).

## Summary

Every unofficial Monarch tool talks to the private GraphQL endpoint the web app uses, now `https://api.monarch.com/graphql` (the old `api.monarchmoney.com` returns HTTP 525 since about 2026-02-01), and that endpoint has broken them three times this year: the domain move, a gql 4.0 signature break, and a May 2026 auth change after which the web app authenticates with session cookies plus a CSRF token rather than a `Token` header. The safest route for finwright stays the official Monarch MCP connector (`https://api.monarch.com/mcp`, OAuth in the browser, revocable under Settings → Integrations), which one community MCP (colvint) archived itself in favour of; the second-best is Monarch's own CSV downloads (`Date,Balance,Account` for balances), which need no credentials at all. For the data, the useful shapes are `accounts` (type, subtype, `currentBalance`/`displayBalance`, `isAsset`, `includeInNetWorth`, `isHidden`, `deactivatedAt`, `dataProvider`, `credential.updateRequired`, `displayLastUpdatedAt`), `portfolio.aggregateHoldings` (ticker, quantity, `basis`, `totalValue`), `snapshotsForAccount` and `aggregateSnapshots`. Liabilities come back negative, home values come from Zillow, and an institution rename in June 2026 split account histories in two for tools that keyed on names, so finwright should key on Monarch's account id. The best read-only patterns to copy are robcerda's `MONARCH_MCP_READ_ONLY` (write tools are never registered) and thedavidweng's tier table (read / remote action / mutation / destructive, with read-only mode, dry-run, per-call `--confirm` and an audit log). Most community skills ask for the Monarch password and the TOTP *secret* in environment variables; finwright should never do that.

## 1. Auth patterns, ranked by safety

| Rank | Pattern | Who uses it | Risk |
|---|---|---|---|
| 1 | **Official Monarch MCP, OAuth in the browser.** No key to paste; `mcp-remote` caches and silently refreshes the token in `~/.mcp-auth`; revoke in Monarch under Settings → Integrations; a 401 means the grant was revoked or the cache is stale. | protoLabsAI/monarch-money-plugin `skills/monarch-money/SKILL.md`; colvint/monarch-money-mcp README ("Archived in favor of the now officially supported Monarch Money Connector") | Lowest. Scoped and revocable; beta, so tool names and shapes can change and "rate limits apply". The agent never sees a credential. |
| 2 | **Monarch CSV download by the user.** No session at all. | fru-dev3/AI-Ready-Life `wealth/skills/app-monarch-money/SKILL.md` ("CSV export (Recommended for Transaction History)"); istota `money` skill (`import-csv`) | None beyond the file on disk. |
| 3 | **Ride the open browser session.** CSRF token read from the open Monarch tab plus the browser's own cookies; nothing stored. | tyler-class/Chrysalis README ("How it works"); xiaotianxt/mon `SKILL.md` (via a local `bro` bridge on 127.0.0.1:3500) | Low for credentials, but it is browser automation on a financial site, which finwright's guard already denies. |
| 4 | **Session cookies or token saved to the OS keyring, captured once outside the agent.** | robcerda/monarch-mcp-server README §"One-Time Authentication Setup" (option 1, recommended: copy the `cookie:` header from DevTools into `%APPDATA%\monarch-mcp\cookie.txt`, verified, then stored in the keyring); theFong/mmoney-cli README ("Tokens stored in OS keychain (not accessible to agents)") | Medium. The session is long-lived and grants full read and write. robcerda issue #80: on Windows the cookie blob (~950 chars) was too big for Credential Manager and **silently fell back to a plaintext file** (fixed by chunking in #113, DPAPI in #123). issue #70: on macOS the keyring probe always failed, so tokens went to plaintext. |
| 5 | **Token in a 0600 file with `env:NAME` indirection.** | thedavidweng/monarchmoney-cli `docs/auth.md` | Medium. Honest about trade-offs; the session file holds a long-lived token. |
| 6 | **Email + password + TOTP secret in env vars or MCP config.** | jamiew/monarch-mcp README; colvint README; davideasaf/monarch-money and its copies (modbender/skill-library-mcp, Geralt1983/Thanos, MalSkillBench benign set); mvanhorn printing-press (password + one-off MFA code); theFong ("MFA Secret: Full automation, long-lasting") | Highest. The TOTP secret is a permanent second factor sitting next to the password. jamiew's own README: "Your credentials grant full account access, including writes." |

Flagged for asking for secrets in plaintext:

- **davideasaf/monarch-money** (and the copies in modbender/skill-library-mcp, Geralt1983/Thanos): `MONARCH_EMAIL`, `MONARCH_PASSWORD`, `MONARCH_MFA_SECRET` all marked **required**, and it tells the user to *disable and re-enable 2FA* to get the base32 secret, and offers `auth login -e ... -p password --mfa-secret SECRET` on the command line (visible in the process table and shell history). Session cached at `~/.mm/session.json`.
- **jamiew/monarch-mcp, colvint/monarch-money-mcp**: password and TOTP secret in `claude_desktop_config.json` / `.mcp.json` / docker `-e` flags.
- **theFong/mmoney-cli**: offers `-p yourpassword --mfa-secret` on the command line, though it recommends interactive login.
- **istota-project/istota**: `MONARCH_SESSION_ID` and `MONARCH_CSRFTOKEN` cookies, kept in its encrypted secrets table (better than env).
- **mattebad/monarch-studentaid-sync**: Monarch cookies or password in `.env`, plus a Gmail app password to read MFA emails over IMAP. Fine for its purpose; the opposite of finwright's posture.

Nothing read looked malicious. davideasaf/monarch-money sits in **lxyeternal/MalSkillBench** under `Dataset/Skills/benign/monarch-money` because that set is the 4,000 "most-downloaded skills, used as the false-positive set" (README); guarddog and malguard both scored it clean (`Experiment/Results/supplychain/*/benign/monarch-money/result.json`). Its presence there means "popular", not "suspect". Two notes of caution: robcerda's README carries a referral link, and the reason-machines/mcp-skills file is an auto-generated restatement of robcerda's README (it lists `create_transaction`, `delete_transaction`, `bulk_categorize_transactions` and `set_budget_amount` as plain prompts with no confirmation advice), so it should not be used as a skill.

Gotchas, with sources:

- **Domain move.** `api.monarchmoney.com` → HTTP 525; use `api.monarch.com`; web app moved to `app.monarch.com` (hammem/monarchmoney #184, #179, #196). hammem's library (537 stars) is unmaintained since 2025-11; the maintained fork is bradleyseanf/monarchmoneycommunity (157 stars, pushed 2026-10-12), which robcerda builds on.
- **May 2026 auth change.** The web app sends session cookies (`session_id`, `csrftoken`, plus Cloudflare `cf_clearance`, `__cf_bm`) instead of an `Authorization: Token` header; token-only auth "may no longer" work (robcerda #65, README option 3; hemaaanth/skills `monarch/SKILL.md` "authenticates GraphQL with session cookies plus CSRF/browser client headers"). thedavidweng ADR 0001 still uses `Authorization: Token` and also needs `Client-Platform: web` and a desktop Chrome User-Agent, because default UAs are rejected.
- **Short sessions.** Tokens expiring in 30 minutes to 3 hours (hammem #139) came from logins without device trust. robcerda now requests `trusted_device=True` and rejects short-lived tokens (README "Session Expired or 401 within an hour"); keithah says saved sessions "can last several months". A `monarchDeviceUUID` from browser localStorage is part of the trusted-device story (theFong README, georgeck README).
- **Email OTP on a new device** even with MFA off (robcerda README "Email Verification Required"; hemaaanth `--email-otp`).
- **Cloudflare.** Programmatic password login is "sometimes gated by Cloudflare for unfamiliar IPs or rapid retries"; cookie auth avoids the login endpoint (robcerda README). Logins from Azure were rejected from 2025-11 (hammem #171). HTTP 429 on first login attempt (hammem #196).
- **SSO accounts** (Google, Apple sign-in) cannot use password login; set a Monarch password first (bstncartwright `skills/monarch-cli/SKILL.md`, mattebad README).
- **Long cookie paste truncates** at 1024 bytes on POSIX terminals (robcerda #82); use a file.
- **Rate limits.** The official MCP is beta with rate limits (protoLabsAI SKILL.md). For the private API, thedavidweng retries 3 times with 500 ms, 1 s, 2 s backoff (ADR 0001); jamiew shares one login across integration tests "to avoid MFA reuse and login throttling".
- **One approval, not one per call.** With the OAuth bridge, a burst of parallel tool calls can each open an auth tab; protoLabsAI calls `monarch_ensure_authorized` once and waits before fanning out.

## 2. Data model

### Account fields (`GetAccounts`, `fragment AccountFields`; hammem/monarchmoney `monarchmoney/monarchmoney.py` lines 133-215)

`id`, `displayName`, `mask`, `type {name display}`, `subtype {name display}`, `currentBalance`, `displayBalance`, `isAsset`, `isHidden`, `hideFromList`, `includeInNetWorth`, `includeBalanceInNetWorth`, `syncDisabled`, `deactivatedAt`, `isManual`, `dataProvider`, `dataProviderAccountId`, `displayLastUpdatedAt`, `updatedAt`, `holdingsCount`, `manualInvestmentsTrackingMethod`, `credential {id updateRequired disconnectedFromDataProviderAt dataProvider institution {name status}}`, `institution {id name}`.

What matters for fw.py:

- `id` is the stable key. Names are not: keithah/monarchmoney-enhanced #45 reports that around 2026-06-12 Monarch changed masked names from `(...*****8211)` to `(...8211)`, which "creates double accounts" in tools that key on names. Chrysalis keys mappings by id "preserved even if you change the name".
- `displayLastUpdatedAt` is the freshness date to put in `balances.csv`, not today's date.
- `credential.updateRequired` / `disconnectedFromDataProviderAt` mean the balance is stale because the link broke. robcerda has `get_account_sync_health(stale_after_days?)`; hemaaanth's watcher groups accounts by `credential.id` because one broken connection stales several accounts at once.
- `includeInNetWorth`, `isHidden`, `deactivatedAt` decide whether Monarch counts the account; finwright must decide for itself and say so.
- `dataProvider` shows where a value came from: `plaid`, `finicity`, `mx`, `zillow` (home), `vin_audit` (car), empty for manual (home-assistant/core `tests/components/monarch_money/fixtures/get_accounts.json`).

### Account types and subtypes (Monarch `accountTypeOptions`, captured 2025-06-02 in Fazekas-Solutions/YnabToMonarch `public/static-data/monarchAccountTypes.json`; group names confirmed by sanghviharshit/ha-monarchmoney and Chrysalis `setup/setup.js`)

| Monarch type (group) | Subtypes | fw.py type |
|---|---|---|
| `depository` (asset) | checking, savings, money_market, cd, cash_management, prepaid, paypal | `cash` |
| `brokerage` (asset) | brokerage, non_taxable_brokerage_account, mutual_fund, cryptocurrency, trust, ugma, utma, stock_plan, iso, nso | `taxable` (stock_plan/iso/nso unvested parts → `unvested`) |
| `brokerage` | st_401k, st_401a, st_403b, st_457b, ira, sep_ira, simple_ira, sarsep_pension, keogh_plan, thrift_savings_plan, profit_sharing_plan, pension, retirement, fixed_annuity, variable_annuity | `tax_deferred` |
| `brokerage` | roth, roth_401k | `roth` |
| `brokerage` | health_savings_account (health_reimbursement_arrangement is not an asset the user owns) | `hsa` |
| `brokerage` | st_529, education_savings_account | `other_asset` (or a 529 type if fw.py adds one) |
| `real_estate` (asset) | primary_home, secondary_home, rental_property | `real_estate` |
| `vehicle` (asset) | car, boat, motorcycle, ... | `vehicle` |
| `valuables`, `other_asset` (asset) | | `other_asset` |
| `credit` (liability) | credit_card | `credit_card` |
| `loan` (liability) | mortgage, home_equity, home | `mortgage` |
| `loan` | auto, student, consumer, line_of_credit, business, ... | `loan` |
| `other_liability` (liability) | other | `other_liability` |

There is no savings bond subtype; I and EE bonds would be a manual `other_asset` in Monarch, and fw.py should keep valuing them from Treasury's files rather than importing Monarch's number. Canadian and UK subtypes (rrsp, tfsa, isa, ...) do not apply. A 401(k) holding pre-tax and Roth money is one Monarch account; Chrysalis 1.2.0 splits one account across several destinations by percentage, and notes the split "does not update itself".

### Balances and history

| Need | GraphQL operation (hammem names) | Tool names seen |
|---|---|---|
| Current balance per account | `GetAccounts` → `currentBalance`, `displayBalance` | official MCP: discover from live list; robcerda `get_accounts`; bstncartwright `monarch accounts list` |
| Daily balance, all accounts, from a date | `GetAccountRecentBalances(startDate)` → `accounts { id recentBalances }` (default 31 days) | `monarch accounts balances --start-date`; hemaaanth `recent-balances`; keithah fixed a broken variant to use `recentBalances` (#37) |
| One account's full history | `AccountDetails_getAccount` → `snapshotsForAccount(accountId) { date signedBalance }` | robcerda `get_account_balance_history`; jamiew `get_account_history` (paginated, local date bounds) |
| Net worth over time | `GetAggregateSnapshots(filters {startDate endDate accountType})` → `{date balance}` | robcerda `get_net_worth(start_date?, end_date?, account_type?)` |
| Net worth by type, month or year | `GetSnapshotsByAccountType(startDate, timeframe)` → `{accountType month balance}`; `month` is `YYYY-MM` | robcerda `get_net_worth_by_account_type` |

`signedBalance` is the field to use for liabilities; it is negative for debts.

### Holdings (`Web_GetHoldings`, `portfolio(input {accountIds, startDate, endDate, includeHiddenHoldings: true})`; hammem lines 728-795)

`aggregateHoldings.edges.node`: `quantity`, `basis`, `totalValue`, `lastSyncedAt`, `holdings[] {ticker name type typeDisplay closingPrice isManual}`, `security {ticker name type typeDisplay currentPrice currentPriceUpdatedAt closingPrice}`.

Mapping to `holdings.csv` (`date,account,symbol,asset_class,value,units,expense_ratio`): `symbol` ← `security.ticker` (fall back to `holdings[0].ticker`, then name for funds without tickers, common in 401(k)s); `value` ← `totalValue`; `units` ← `quantity`; `asset_class` is not in Monarch (only `typeDisplay` such as equity, mutual fund, ETF, cash) so fw.py must classify; `expense_ratio` is not in Monarch; `date` ← `lastSyncedAt` date. jamiew adds `get_all_holdings` that groups by brokerage account and skips other types. istota's portfolio skill ships 30 symbols pre-classified and makes classification retroactive (one row per symbol, applied to every past snapshot).

## 3. Monarch CSV formats (secondary: from parsers of real exports)

- **Transactions** (Settings → Data → Download transactions, or per account via Edit → Download transactions; at most 10,000 rows per download, 5,000 or fewer advised per a search-result summary of help article 15526600975764): `Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags`, with a ninth `Owner` column in newer files. Dates ISO `YYYY-MM-DD` (istota also accepts `MM/DD/YYYY`); `Amount` signed, negative = money out. No balances in this file. Sources: bex-co/beancount-io `skills/.claude/skills/beancount-migrate/references/monarch.md`; istota `src/istota/money/core/importers/monarch_csv.py`.
- **Account balances** ("Download account balances", also the per-account balance history): flat `Date,Balance,Account`, one end-of-day row per account per date, assets positive, **liabilities negative** ("you owe $21,818" → `-21818.66`). Sources: raolivei/canopy `backend/services/monarch/balances_parser.py`; LemurTech/Net-Worth-Navigator `src/csv_importer.py`; KofTwentyTwo/carl `docs/MONARCH-IMPORT.md`.
- **Balance history import** (into Monarch, for reference): one account per file, `Date,Balance`, unique dates (help article 14882425704212 via search summary; chrisgelhaus/qifutil `cmd/balance_history.go`).

This file is the cheapest Monarch route for fw.py: `Account` is the display name, so fw.py needs a name → account-id map file and must flip liability signs (it already stores liabilities with `abs()`). Record the real headers from the first real download in the skill's LEARNINGS.md, since these are secondary.

## 4. Read-only enforcement patterns

- **Do not register write tools at all.** robcerda `MONARCH_MCP_READ_ONLY=1`: "the mutating tools are never registered ... a model that was talked into a write by a merchant name or memo it read back cannot invoke a tool that is not there." Leaves 30 of 58 tools. On by default in its Docker image, off elsewhere (README "Strongest option: read only mode"; #98, #154).
- **Keep approval prompts for every write; the README lists them** and calls `refresh_accounts` side-effecting too, "since it posts a refresh request to your institutions" (robcerda README "Recommended: require approval for mutating tools").
- **Tiers.** thedavidweng ADR 0002: Read always allowed; Remote action (`accounts refresh`) blocked by read-only; Mutation and Destructive need `--confirm` every call, no "yes to all"; `--dry-run` returns a plan with no remote call; every confirmed mutation goes to `~/.monarchmoney-cli/audit/YYYY-MM-DD.jsonl` (no credentials or financial detail).
- **Two keys for risky writes.** hemaaanth `monarch/SKILL.md`: every side effect needs `--confirm`, and higher-risk ones also need `MONARCH_ALLOW_WRITE=1`. It also lists dangerous private mutations (`resetAndSyncAccount`, `deleteSyncedTransactions`, `deleteSyncedSnapshots`, `transferAccountDataAsync`) to never run casually.
- **Read-only GraphQL escape hatch.** mvanhorn printing-press `query` refuses GraphQL files containing `mutation`; writes dry-run unless `--yes`; "do not guess ambiguous targets from merchant names or amounts".
- **One exact target, no retries.** xiaotianxt/mon: one transaction id per write, never fuzzy or batch, never retries a mutation, `outcome-unknown` is not success.
- **Server-side silent failures.** robcerda #115: mutating tools ignored GraphQL payload-level `errors`, so rejected writes reported success. #118: a rule with zero criteria plus `apply_to_existing` could recategorize all history. #119: `add_transaction_tag` could delete tags. These are why finwright never writes.
- **Read-only by statement only** (weak): bstncartwright ("Assume the tool is read-only"), protoLabsAI ("Treat the connector as read-only"). Fine as text, not enforcement.

**Check against finwright's guard** (`hooks/fw_guard.py`): `guard_mcp` tokenizes the server name, so `mcp__monarch__*`, `mcp__Monarch_Money__*` (robcerda's suggested name "Monarch Money") and a claude.ai connector name containing "Monarch" are all treated as a money server, and any tool whose first word is not a read verb is gated. That covers `refresh_accounts`, `update_account`, `upload_account_balance_history` and the login and logout tools. Read tools such as `get_account_sync_health`, `get_transactions_needing_review` and `search_transactions` pass. The shell path blocks POST to `api.monarch.com`, which also blocks GraphQL *reads* by curl; that is fine, because finwright should not call the private API at all.

## 5. Data-quality pitfalls

- **Liability sign.** Credit cards and loans are negative in `currentBalance`, `signedBalance` and the balances CSV (home-assistant fixture: credit card `-200.0`; canopy parser). A paid-off mortgage shows `-0.0`. fw.py's `abs()` on liabilities is right, but a credit card with a credit balance (positive) would wrongly turn into debt; flag positive liability values instead of flipping them blindly.
- **Zero balances from some providers.** Chrysalis 1.0.6: Coinbase reports `currentBalance` 0 while `displayBalance` holds the value. Prefer `displayBalance` when `currentBalance` is 0 and they differ, and say so.
- **Home value is a Zillow estimate** (`dataProvider: "zillow"`) and the mortgage is a separate account. Treygec/Monarch-ProjectionLab-Bridge #1: the home value was overwritten with the loan balance by a bad mapping. fw.py should tag a Zillow value `method=zestimate` and keep its own selling-cost haircut.
- **Car value** comes from `vin_audit`; tag `method=vin_audit`.
- **Renamed accounts duplicate history** in name-keyed tools (keithah #45). Key on Monarch `id`.
- **Relinked accounts duplicate.** hemaaanth notes `transferAccountDataAsync` exists for "duplicate/reconnected-account repair", which means a relink creates a new account id and the old one lingers. On import, fw.py should warn when two Monarch ids map to the same institution + last4.
- **Stale linked accounts** look current. Use `displayLastUpdatedAt` as the row date and `credential.updateRequired` as a warning; fw.py's `STALE_DAYS` then does the rest.
- **Hidden, closed and excluded accounts.** `isHidden`, `deactivatedAt`, `includeInNetWorth=false`. Monarch's net worth leaves them out; finwright should list them and let the user decide once per account. istota: "excluding an account hides it from every total" is better than deleting history.
- **Hidden transactions** are not returned by default since 2025 (hammem #168, `transactionVisibility: all_transactions`); irrelevant to balances, relevant to any flows import.
- **Holdings gaps.** No asset class, no expense ratio; `basis` can be null; manual holdings exist (`isManual`) and keithah's update and delete holding calls do not work (#44). 401(k) funds often lack tickers.
- **Manual accounts never refresh.** Anything `isManual` is only as fresh as the last time someone typed it.
- **Truncated pages.** jamiew #16: a spending summary silently stopped at 1,000 transactions; bstncartwright notes default windows (31 days for balances, 30 for transactions, current month for budgets). Always pass explicit dates and report them.
- **Dates as objects.** robcerda #54 and theFong #29: date objects that fail JSON serialization; treat dates as strings.

## 6. Worth copying, and what to avoid

Good:

- protoLabsAI's skill text is the closest to finwright's posture: authorize once before fanning out calls, pick the narrowest tool with filters, "report real numbers with their as-of context (account, period, currency)", "never from memory or estimation", read-only, discover tool names from the live list because the MCP is beta.
- bstncartwright: "When reporting date-based results, include the exact start and end dates used."
- xiaotianxt/mon: "aggregate first" rather than printing raw transactions; never print tokens or cookies.
- robcerda: the write-tool list and the reason for read-only mode (prompt injection through merchant names and memos).
- thedavidweng: the tier table and the audit log line per mutation.
- Chrysalis: key by id, skip (not zero) an account that disappeared, partial-success reporting, a 0% split never writes, sync history showing every source.
- istota: re-importing an identical file is a no-op that reports `duplicate`; `--replace` for a same-day re-export; `--dry-run` parses and previews.

Bad:

- Asking for the TOTP secret, or telling the user to reset 2FA to read it (davideasaf and copies).
- Credentials as command-line flags (davideasaf, theFong, thedavidweng all warn or allow).
- Treating `refresh_accounts` as harmless (reason-machines lists "Refresh all my account balances from the banks" as a plain prompt).
- Bulk writes driven by search results (reason-machines `bulk_categorize_transactions`; adbertram's rule create and delete commands).
- Depending on the hammem library (unmaintained, wrong domain).
- Hard-coding personal paths and private agents into a public skill (one skill hard-coded its author's macOS home folder).

## What finwright should adopt

1. **Monarch route order in the skill text:** (a) Monarch's "Download account balances" CSV → `fw.py import balances` with a Monarch name map; (b) the official MCP connector, read tools only; (c) never the private GraphQL API, cookies, tokens or passwords. Sources: colvint README (archived for the official connector); protoLabsAI SKILL.md; canopy balances parser.
2. **A `--from monarch` mode (or a mapping file) for `import balances`** that reads `Date,Balance,Account`, maps `Account` to a finwright id through `monarch-map.csv` (Monarch name or id → fw account), takes the newest row per account by default, keeps the sign check from pitfall 1, and refuses unknown names with a list of them. Sources: canopy, Net-Worth-Navigator, carl.
3. **Key on Monarch account id when the MCP is the source;** keep the name only as a label. Source: keithah #45; Chrysalis setup.
4. **Freshness from the source:** row date = `displayLastUpdatedAt` date, `source=monarch-mcp` or `monarch-csv`, `method` = `dataProvider` (`plaid`, `finicity`, `mx`, `zillow`, `vin_audit`, `manual`), `note` carries `updateRequired` when set. Source: hammem `AccountFields`; robcerda `get_account_sync_health`; home-assistant fixture.
5. **Type mapping table** from section 2 in the skill's reference, with "ask the user" for 529, stock plans and HRA. Source: YnabToMonarch `monarchAccountTypes.json`.
6. **Listing excluded accounts** (`isHidden`, `deactivatedAt`, `includeInNetWorth=false`) at import and asking once whether each counts, stored in `accounts.csv` notes. Source: hammem fields; istota exclude rule.
7. **Holdings import from MCP `get_account_holdings` output saved to a file:** symbol, `totalValue`, `quantity`, `lastSyncedAt`; asset class from fw.py's own classification with an "unclassified" prompt. Source: hammem `Web_GetHoldings`; istota classification rules.
8. **Monarch's net worth only as a cross-check,** never as the record; report the difference and its main cause (excluded accounts, Zillow, stale links). Source: fru-dev3 ("cross-check against the vault's own net worth calculation"); finwright decision of 2026-10-12.
9. **Skill wording to copy:** "authorize once, then call"; "every number from a tool result or a file, with its as-of date"; "pass explicit date ranges and report them"; "aggregate before printing". Sources: protoLabsAI, bstncartwright, xiaotianxt/mon.
10. **Guard test cases** for `mcp__Monarch_Money__refresh_accounts`, `mcp__Monarch_Money__upload_account_balance_history`, `mcp__claude_ai_Monarch__update_account` (all must gate) and `..._get_account_sync_health` (must pass). Source: robcerda tool table; finwright `hooks/fw_guard.py`.
11. **If the user ever runs a community MCP anyway:** robcerda with `MONARCH_MCP_READ_ONLY=1`, auth via `login_setup.py` outside Claude, and a check on Windows that the session landed in Credential Manager and not a plaintext file. Source: robcerda README and #80.

## Avoid

- Storing or asking for the Monarch password, TOTP secret, session cookie, CSRF token or device UUID anywhere finwright reads (davideasaf, jamiew, colvint, theFong, istota, mattebad).
- Any write tool, including `refresh_accounts`, `upload_account_balance_history` and `update_account` (robcerda write list).
- Calling `api.monarch.com/graphql` directly, browser automation on `app.monarch.com`, or extensions that read the tab's CSRF token (Chrysalis, xiaotianxt/mon): the guard denies these and they break on every web-app change.
- Name-keyed account matching (keithah #45).
- Taking Monarch's net worth or Zillow home value as the answer without saying where it came from.
- Unbounded queries with default windows (jamiew #16; bstncartwright defaults).
- The reason-machines and adbertram skill files as templates.

## Sources

Stars and last push from `gh api repos/OWNER/REPO` on 2026-10-12.

| Repo | Stars | Last push | What it is | Link |
|---|---|---|---|---|
| mvanhorn/printing-press-library (`library/payments/monarch-money/SKILL.md`; `cli-skills/pp-monarch-money` is a generated mirror) | 2,061 | 2026-10-12 | Go CLI skill: accounts, cashflow, dry-run transaction writes, mutation-refusing `query` | https://github.com/mvanhorn/printing-press-library |
| openaccountant/skills (`shared/bank-sync/SKILL.md`) | 88 | 2026-04-09 | Plaid bank sync for "Wilson"; mentions Monarch only as an alternative | https://github.com/openaccountant/skills |
| modbender/skill-library-mcp (`data/monarch-money/SKILL.md`) | 16 | 2026-09-28 | Copy of davideasaf's skill | https://github.com/modbender/skill-library-mcp |
| xiaotianxt/mon | 0 | 2026-09-03 | CLI over the logged-in browser tab via a local bridge; one-id writes, dry-run | https://github.com/xiaotianxt/mon |
| fru-dev3/AI-Ready-Life (`wealth/skills/app-monarch-money/SKILL.md`) | 17 | 2026-08-19 | Playwright or CSV export; net worth as cross-check | https://github.com/fru-dev3/AI-Ready-Life |
| reason-machines/mcp-skills (`skills/monarch-money-mcp-server/SKILL.md`) | 6 | 2026-10-09 | Auto-generated skill restating robcerda's README | https://github.com/reason-machines/mcp-skills |
| etdofreshai/monarch-money-ingestor | 0 | 2026-06-02 | Transactions into Postgres, `MONARCH_TOKEN`, upsert on `monarch_id` | https://github.com/etdofreshai/monarch-money-ingestor |
| davideasaf/monarch-money | 2 | 2026-01-26 | TS CLI skill; requires email, password, TOTP secret | https://github.com/davideasaf/monarch-money |
| hemaaanth/skills (`monarch/SKILL.md`) | 0 | 2026-09-20 | Python CLI; cookie auth; `--confirm` plus `MONARCH_ALLOW_WRITE`; sync-health watcher | https://github.com/hemaaanth/skills |
| Geralt1983/Thanos (`Skills/monarch-money/SKILL.md`) | 1 | 2026-04-21 | Copy of davideasaf's skill plus cron recategorization | https://github.com/Geralt1983/Thanos |
| protoLabsAI/monarch-money-plugin (`skills/monarch-money/SKILL.md`) | 0 | 2026-06-18 | Official Monarch MCP via `mcp-remote` OAuth; read-only by statement | https://github.com/protoLabsAI/monarch-money-plugin |
| adbertram/cli-tools (`_repo/skills/monarch-cli/SKILL.md`) | 6 | 2026-10-13 | Personal CLI skill with rules CRUD and review agents | https://github.com/adbertram/cli-tools |
| bstncartwright/monarch-cli (`skills/monarch-cli/SKILL.md`) | 0 | 2026-03-09 | Read-only CLI skill: balances, holdings, history, raw GraphQL | https://github.com/bstncartwright/monarch-cli |
| LionisIAm/points-activity (`skills/monarch-import/SKILL.md`) | 0 | 2026-06-03 | Scaffold importer into Monarch; "never delete" rule | https://github.com/LionisIAm/points-activity |
| istota-project/istota (`src/istota/skills/money/skill.md`, `src/istota/money/core/importers/monarch_csv.py`) | 14 | 2026-10-13 | Beancount money skill with Monarch sync and CSV import; portfolio snapshots | https://github.com/istota-project/istota |
| lxyeternal/MalSkillBench | 60 | 2026-06-10 | Malicious-skill benchmark; Monarch skill is in the benign set | https://github.com/lxyeternal/MalSkillBench |
| robcerda/monarch-mcp-server | 416 | 2026-10-12 | Most-used Monarch MCP (58-60 tools), keyring session, read-only mode | https://github.com/robcerda/monarch-mcp-server |
| jamiew/monarch-mcp | 25 | 2026-09-29 | MCP; password and TOTP secret in env | https://github.com/jamiew/monarch-mcp |
| colvint/monarch-money-mcp | 16 | 2026-07-09 | MCP, archived in favour of the official connector | https://github.com/colvint/monarch-money-mcp |
| wesm/moneyflow | 275 | 2026-10-13 | Terminal finance UI with Monarch and YNAB backends | https://github.com/wesm/moneyflow |
| theFong/mmoney-cli | 39 | 2026-10-05 | Python CLI; keychain session; holdings and snapshots | https://github.com/theFong/mmoney-cli |
| thedavidweng/monarchmoney-cli | 31 | 2026-10-11 | Go CLI; tiered mutation safety, audit log, ADRs | https://github.com/thedavidweng/monarchmoney-cli |
| hammem/monarchmoney | 537 | 2025-11-13 | Original Python API (unmaintained); GraphQL queries quoted above | https://github.com/hammem/monarchmoney |
| bradleyseanf/monarchmoneycommunity | 157 | 2026-10-12 | Maintained community fork of hammem | https://github.com/bradleyseanf/monarchmoneycommunity |
| keithah/monarchmoney-enhanced | 24 | 2026-09-18 | Fork with holdings, session validation; account-rename issue #45 | https://github.com/keithah/monarchmoney-enhanced |
| tyler-class/Chrysalis | 17 | 2026-10-13 | Chrome extension: Monarch balances to ProjectionLab via the tab's CSRF token | https://github.com/tyler-class/Chrysalis |
| georgeck/projectionlab-monarchmoney-import | 23 | 2026-03-07 | Scripts: Monarch balances to ProjectionLab by account id | https://github.com/georgeck/projectionlab-monarchmoney-import |
| mattebad/monarch-studentaid-sync | 10 | 2026-08-31 | Writes student loan balances into Monarch manual accounts; dry-run and duplicate guard | https://github.com/mattebad/monarch-studentaid-sync |
| Fazekas-Solutions/YnabToMonarch (`public/static-data/monarchAccountTypes.json`) | 9 | 2026-06-12 | Captured Monarch account type and subtype list | https://github.com/Fazekas-Solutions/YnabToMonarch |
| home-assistant/core (`tests/components/monarch_money/fixtures/get_accounts.json`) | 91,420 | 2026-10-13 | Sample account payload: signs, `dataProvider` values | https://github.com/home-assistant/core |
| raolivei/canopy (`backend/services/monarch/balances_parser.py`) | 1 | 2026-06-23 | Parser for the `Date,Balance,Account` export | https://github.com/raolivei/canopy |
| bex-co/beancount-io (`skills/.claude/skills/beancount-migrate/references/monarch.md`) | 297 | 2026-10-12 | Monarch transactions CSV format notes | https://github.com/bex-co/beancount-io |
| Treygec/Monarch-ProjectionLab-Bridge (issue #1) | 3 | 2026-04-20 | Zillow home value overwritten by mortgage balance | https://github.com/Treygec/Monarch-ProjectionLab-Bridge |
| Monarch help center, articles 50207234679956, 15526600975764, 14882425704212 | n/a | n/a | MCP connector, downloading history, importing balance history; all HTTP 403 to the fetcher on 2026-10-12 | https://help.monarch.com/hc/en-us/articles/50207234679956-Monarch-MCP-Connector |
