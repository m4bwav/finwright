# Monarch Money: web survey of skills, MCP servers and integrations

Research date: 2026-10-12. This was a read-only pass over directories, registries (official MCP registry, npm, PyPI, ClawHub, skills.sh, Smithery, Glama), Reddit r/MonarchMoney (public RSS), Hacker News (Algolia API), vendor blogs and GitHub repos that the companion note does not cover. Nothing was installed or run, all content was treated as untrusted data, and no instruction found in it was followed. help.monarch.com still returns HTTP 403 to the fetcher, so anything that help center says is quoted from search snippets or from pages that cite it, and is marked "secondary".

Related: [Monarch skill learnings](2026-10-12-monarch-skill-learnings.md) covers the 27 GitHub repos this survey skipped (robcerda, jamiew, colvint, hammem and the rest), and this note builds on it. Also see [Consequential-action safeguards](2026-10-12-consequential-action-safeguards.md), since the guard-hook lessons in section 3 apply there, and [AI tools and MCP landscape](2026-10-12-ai-tools-and-mcp-landscape.md).

## Summary

Monarch's official MCP connector (`https://api.monarch.com/mcp`, OAuth 2.1 with PKCE and dynamic client registration) opened as a beta in mid-June 2026. It was **paused on 2026-06-29** after "one of our data providers" raised a data-portability question, and as of 2026-10-12 it is still paused. A Monarch staff post on 2026-08-19 gave no date for a return, pointed users to CSV export and community tools, and Reddit threads from 2026-10-04 to 2026-10-10 still report no news. The connector asked for read **and** write access on one consent screen, with no read-only scope. Core-plan accounts were capped at 5 writes a day, and Plus lifted the cap. Its contract had 41 tools in PascalCase: 17 reads (`GetAccounts`, `GetNetWorthHistory`, `GetInvestments` and others) and 24 writes with no shared prefix (`UpdateAccountBalanceHistory`, `ContributeToGoal`, `ReportIssue` and others). That list comes from a community mirror that claims to copy it exactly (tyvsmith). For finwright, the practical route on day one is therefore Monarch's own CSV downloads. Balances export as `Date,Balance,Account` across all accounts. Transactions export as `Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags` plus newer `Owner` and `Business Entity` columns. Holdings have **no export at all**. When the official connector returns, the guard should **allow only the read tools by name** rather than try to block writes by pattern, and it must also match whatever server prefix the connector gets. Unofficial access now runs on HttpOnly session cookies plus a CSRF token. Scripted password login sits behind Cloudflare, CAPTCHA and email OTP, and sessions last about two months. Every unofficial route therefore means handing an agent a long-lived full-access session, which finwright should not do.

## 1. The official Monarch MCP connector

| Fact | Detail | Source |
|---|---|---|
| Endpoint | `https://api.monarch.com/mcp`, added as a custom connector; the user signs in to Monarch in the browser to authorize | help.monarch.com article 50207234679956 (secondary, via search snippet); jsilets/monarch-mcp-ui on Glama |
| Auth | OAuth 2.1 + PKCE with dynamic client registration; each user approves on Monarch's own consent screen | jsilets/monarch-mcp-ui (Glama listing) |
| Scope | The consent screen asks for **read and write**. No read-only scope was reported anywhere | jsilets (Glama); Truthifi comparison ("read and write access to your transactions, budgets, categories, and cash flow data", "does not execute bank transfers") |
| Write cap | 5 writes a day on standard/Core; Monarch Plus removes the cap | jsilets (Glama); Reddit 2026-06-18 "My Experience with MCP and Codex in Monarch Plus" ("Core plan limits MCP writes to five per day") |
| Clients | Official guides for Claude Desktop, Claude Code, Gemini CLI and Cursor; ChatGPT on the web only, on paid plans | help.monarch.com (secondary, via search snippet) |
| Timeline | Open beta "rolling out" (Reddit June roundup, 2026-06-17); paused 2026-06-29; help page updated 2026-06-30; still paused at the staff update of 2026-08-19 and in user threads up to 2026-10-10 | Reddit r/MonarchMoney (u/Kait_Monarch, u/ozzie_monarch); tyvsmith README; mcpyet.com |
| On restore | Users connected before June 29 "should get an email", and their authentication stays intact, so no re-authorization is needed | help.monarch.com (secondary, via search snippet) |
| Why paused | A data aggregator or institution objected over data portability. Monarch cites the unsettled CFPB 1033 rule; one user suspects Plaid/MX will never allow it | Reddit 2026-08-19 "MCP Update — Still Paused"; Reddit 2026-08-07 "Mcp access never happening imo" |
| Tool names (41) | Reads: `GetAccounts, GetTransactions, GetBudget, GetCashFlow, GetCategories, GetGoals, GetInvestments, GetMerchants, GetNetWorthHistory, GetRealEstate, GetRecurring, GetSpendingByCategory, GetTags, GetCreditScoreHistory, GetHouseholdMembers, GetBusinesses, ListRules`. Writes: `CreateTag, UpdateTag, DeleteTag, CreateCategory, UpdateCategory, DeleteCategory, CreateMerchant, UpdateMerchant, MergeMerchants, CreateRule, DeleteRule, CreateTransaction, UpdateTransaction, DeleteTransaction, BulkUpdateTransactions, BulkRecategorizeTransactions, UpdateTransactionSplits, CreateGoal, UpdateGoal, DeleteGoal, ContributeToGoal, WithdrawFromGoal, UpdateAccountBalanceHistory, ReportIssue` | tyvsmith/monarch-money-remote-mcp `src/tools/index.ts`, which says it mirrors "that connector's 41-tool contract (same names, arguments, and semantics)". **Secondary**: not checked against Monarch itself |

Data shapes in the mirror (secondary, but the descriptions read as if copied from the official ones):

- `GetAccounts` returns per account: `id, name, notes, type, sub_type, is_asset, is_manual, is_hidden, balance` (display, positive), `signed_balance, mask, institution, owner, business, closed`. Loans add `apr, minimum_payment, interest_rate, remaining_term`, and credit cards add `credit_limit`. It also returns `total_assets, total_liabilities, net_worth`, counting only accounts with `includeInNetWorth`. Filters take type display names ("Cash", "Investments", "Credit Cards", "Loans", "Real Estate"), subtype names ("401k", "Brokerage (Taxable)") and an ownership JSON (`{"scope":"household"|"user", ...}`).
- `GetNetWorthHistory(start_date, end_date?, include_account_breakdown?)` returns readings of `date, net_worth, assets, liabilities` (liabilities as a positive number). Readings are **daily up to 60 days and weekly beyond that**. With the breakdown it also returns per-account balances on each date and an `account_changes` list sorted by size.
- `GetInvestments(start_date, end_date)`: "Holdings are always current — this tool cannot show past portfolio composition." The date range only sets the period change. Each holding has `name, ticker, type, asset_class, quantity, price, value, cost_basis, allocation_percent, period_change, total_gain` and per-account `quantity/value`. The summary has `total_value, total_cost_basis, total_gain, one_day_change`.
- Four write tools take `dry_run: true`: `BulkUpdateTransactions`, `BulkRecategorizeTransactions`, `UpdateTransactionSplits` and `UpdateAccountBalanceHistory`.

What users reported while it ran (Reddit):
- Write approvals were slow. Every edit needed its own approval, and bulk clean-up was faster by exporting CSV, letting an AI fix it, and re-importing it by hand. The MCP had no CSV import or export tool (2026-06-18).
- Through the MCP, a brokerage account showed **holdings that appeared in neither the Monarch web app nor the bank**, which looked like stale cached entries, and re-authenticating did not clear them (2026-06-30 "MCP server uncovering hidden investment holdings").
- People upgraded to Plus/Pro for the MCP and then lost it. Monarch refunded or downgraded on request (2026-07-08, 2026-09-08).
- One user spent days cleaning data "to make the MCP more useful" (2026-06-30). The quality of data in Monarch decides the quality of answers.

## 2. Auth and access for unofficial routes (new findings beyond the companion note)

- **Cookie sessions replaced bearer tokens.** "Monarch's web app now uses an HttpOnly session cookie, and scripted logins are blocked by bot protection / reCAPTCHA… Sessions last roughly 60 days" (pbassham/monarch-money-api README, npm 0.0.8, 2026-09-16). echomodel/monarch-access: the session is "an HttpOnly session cookie plus a CSRF token… A session lasts about two months". The cookies are `session_id`, `csrftoken` and `monarchDeviceUUID`. In monarchmoneycommunity issue #40 (2026-05-15, 20 comments), tokens stopped working for some users from that day and the fix sent cookies with an `X-Csrftoken` header and an `Origin`/`Referer` of `app.monarch.com`. The rollout was uneven, since the maintainer's own login kept working.
- **Login throttles and challenges.** `/auth/login/` gates a new device behind an email OTP, "plus per-IP throttling and a Cloudflare bot challenge" (PulseMCP `monarch-money-mcp-server` README). tyvsmith treats `RATE_LIMIT` (HTTP 429), `CAPTCHA_REQUIRED` and `EMAIL_OTP_REQUIRED` as a signal for a one-hour cooldown, so that a transient lockout "doesn't escalate". Steadro/monarch-mcp: the token login is "heavily rate-limited (HTTP 429)" and unavailable to Google/Apple SSO accounts, and logging out of Monarch kills the cookie the server depends on.
- **Session files.** monarchmoneycommunity (PyPI, 53.5k downloads/month, the de-facto client) writes its session as a **pickle at mode 0644** (open issue #75, 2026-08-25). Loading a pickle can run code, and other local users can read the file. mikelane/monarch-mcp writes `session.json` at 0600 and never stores the password or MFA secret. crcatala/monarch-cli and simplemind-dev keep it in the OS keyring/Keychain. The PulseMCP server encrypts `session.enc`, but under a **default passphrase** unless `MONARCH_SESSION_PASSPHRASE` is set, which makes that encryption obfuscation only.
- **Browser cookie capture has its own risks.** echomodel reads cookies over Chrome's remote-debugging port and warns that "any program on the machine can drive that Chrome and read its cookies while it runs". On macOS, "Always Allow" on the Keychain prompt would expose every Chrome cookie. claudskills.com's mirror of the AI-Ready-Life skill points Playwright at a whole Chrome profile.
- **Home Assistant** has had a core `monarch_money` integration since 2024.10 (96 active installs). It logs in with username, password and MFA and exposes balance, age and owner sensors per account. The HACS version (sanghviharshit/ha-monarchmoney, 39 stars) also accepts a TOTP secret.
- No Raycast, Zapier or n8n integration was found. richardadonnell/monarch-money-mcp exposes a REST `/api/*` for n8n and Zapier alongside `/mcp`.

## 3. Read-only enforcement patterns seen

| Pattern | Who | Strength |
|---|---|---|
| Write tools never registered unless an env flag is set (`MONARCH_ENABLE_WRITES=1`, `MONARCH_MCP_READ_ONLY` defaulting to 1, `--enable-write`, `--allow-writes`, `MONARCH_CLIENT_ENABLE_WRITES=1`) | tyvsmith; rlorenzo/Monarch-Skills (pins robcerda with `${MONARCH_MCP_READ_ONLY:-1}`; "29 tools withheld at startup", so "a model talked into a write by a merchant name it read back has nothing to call"); vargahis; simplemind-dev; jribnik | Strong, because the tool is absent from the list |
| Tool-group allowlists (`MONARCH_ENABLED_TOOL_GROUPS=readonly`, `MONARCH_ENABLED_TOOLS=...`) | PulseMCP `monarch-money-mcp-server` (official MCP registry `com.pulsemcp/monarch-money`) | Strong if set; **the default exposes everything** |
| In-tool login withheld in read-only mode, "because writing a session counts as durable-state mutation" | rlorenzo (citing robcerda `read_only.py`) | Good detail |
| Typed confirm strings on destructive writes (`confirm` = the tag's name, `"<merchant> <amount>"`, or `str(count)` from a fresh preview) | jribnik/monarch-mcp | Good, but it lives in the server, not in a hook |
| Read-before-write interlock: a balance-history upload needs the `expected_token` digest from a fresh download, refuses if the history changed, and returns `previous_snapshots` for rollback | echomodel/monarch-access | Very good for the one write finwright might ever want |
| Read-only by design: no write tool exists | abekek/monarch-mcp-python, alexpriest/monarch-mcp-server, simplemind-dev (default) | Strongest, but these servers still take a full-access session |
| Official connector | No read-only scope; client approval prompts only | Weak: the consent covers writes, so the guard hook is the only barrier |

## 4. CSV exports and imports (Monarch's own files)

- **Balances export**: one file for all accounts, header `Date,Balance,Account`. Seen in LemurTech/Net-Worth-Navigator `src/csv_importer.py` (rejects files without those three) and ChrisQGeorge/Monarch-Backfill-Balance-History-From-Transactions. Liabilities are negative. Secondary, from parsers.
- **Balances import**: **one account per file**, columns `Date` (YYYY-MM-DD) and `Balance`; the account is chosen in the import dialog. Duplicate dates and future dates are rejected, and liabilities use `-` or parentheses (help.monarch.com articles 14882425704212 and 41843105489300, secondary via snippets). Re-importing the multi-account export therefore fails ("multiple balances per date", Reddit 2026-05-30). echomodel: an upload **replaces the whole history**, sets the current balance to the last row, and creates no transactions.
- **Transactions export**: `Date, Merchant, Category, Account, Original Statement, Notes, Amount, Tags`, with Account at index 3 and Amount at index 6 per ChrisQGeorge. A `Business Entity` column appeared around March 2026 (Reddit 2026-03-20), and `Owner` is mentioned in the companion note. Negative means money out, including on credit cards. Downloads stop at 10,000 rows and Monarch suggests 5,000 or fewer (card-savvy.com / beancount.io snippets, secondary). The path is Settings → Data, or per account via Edit → Download transactions.
- **Holdings**: **no export button**. Printing to PDF cuts off after about 6 holdings in Chrome and is blank in Safari (Reddit 2026-10-05). The MM-Tweaks browser extension (101 stars, 5,000+ installs) is the usual workaround. There is no net-worth snapshot export either (feature request, 2026-05-11).
- The **balance download sometimes just spins** (Reddit 2026-02-26), and the user found no fix.
- "CSV import by id" launched by August 2026, so transactions can be exported, edited and re-imported (staff post, 2026-08-19).

## 5. Data pitfalls for a net worth check

- **The "two-day problem"**: Monarch's period change compares exactly two daily points, so a paycheck or bill on either day skews it (Reddit 2026-01-05). finwright's own snapshots avoid this, so keep its money-weighted math.
- **"All time" starts before the data does**, because accounts added late create jumps in the net worth graph (Reddit 2026-03-23, 2026-05-16). Treat the first appearance of an account as a new account, not a gain.
- **401(k) Roth/traditional split is not exposed**: one total balance only (John Hancock, Reddit 2026-04-17).
- **Reconnecting can create a duplicate account** (TSP, Reddit 2026-04-23). A provider switch moved 401(k) contributions from credit to debit (Reddit 2026-10-09). Since September 2026, switching providers keeps history (roundup 2026-09-30). Key on Monarch's account id and watch for twins.
- **Stale or phantom holdings** through the MCP (above), and dead connections that keep serving the last balance silently. rlorenzo's `monarch-doctor` skill groups by `credential_id`, treats `manual` and `sync_disabled` as not broken, trusts `needs_reauth` over a recent `last_updated_at`, treats a $0 balance on a broken link as unknown, and never suggests deleting an account, because that rewrites past net worth.
- **Monarch's built-in AI assistant** was "just so stupid" for one Plus user (2026-06-18). It was upgraded in September 2026 to answer net worth change questions; that is not checked here.

## 6. Security flags

- **Ask for a password plus the TOTP secret in env or config**: canfie1d/monarch-mcp-server, ezra-quemuel/monarch-mcp, keithah/monarchmoney-ts-mcp (Smithery badge), alexpriest/monarch-mcp-server (`MONARCH_TOTP_SECRET`, deployed on Railway), richardadonnell/monarch-money-mcp, frapbod/monarch-mcp, abekek (optional), npm `monarch-api` (`MONARCH_MFA_SECRET`), npm `@hakimelek/monarchmoney` (`mfaSecretKey`), PulseMCP server (`MONARCH_PASSWORD`, plus a one-time TOTP code, not the secret).
- **ClawHub `silentknight87/monarch`** (678 downloads, 12 installs, 2026-05-11) has the agent `pip install monarchmoney`. That is the abandoned hammem package, which broke at the `api.monarch.com` domain move. It stores a pickle session and exposes `refresh`, a remote action, alongside the reads. Avoid it.
- **Name collisions, not Monarch Money**: npm `monarchai`/`cymela` (a coding agent that installs a **`monarch` command**, the same command name as several Monarch Money CLIs); `teachskillofskills-ai/MONARCH-MCP` (an MCP control plane named Monarch); `@pipeworx/mcp-monarch-initiative`, `QuentinCody`, `openpharma-org`, `nickzren`, `rguyton` (the biomedical Monarch Initiative); skills.sh `monarch-database` entries. None looked malicious, but install by full name only.
- **Vendor pages with conflicting claims**: Truthifi has one page saying the official server is "in beta" and another saying "no official MCP server" (both dated around June). OpenBudget (2026-08-12) says Monarch "does not publish its own MCP server". mcpyet.com says it is official and paused. These are marketing pages for competitors, so trust Monarch's own posts.
- mjstramel/monarch-money-mcp is listed on Glama as "Proprietary / Private".
- No package had install scripts (npm `preinstall`/`postinstall` checked on 7 packages). Nothing was flagged as malware.

## Adopt

1. **Start with the CSV route**: `fw.py import balances` should accept Monarch's multi-account `Date,Balance,Account` file, keep the latest row per account, and keep liabilities negative. Source: LemurTech/Net-Worth-Navigator `csv_importer.py`; ChrisQGeorge backfill tool.
2. **Write the guard as an allowlist of the 17 read tool names** (`Get*`, `ListRules`), so every other `mcp__<server>__*` call on a Monarch server is blocked, including `ReportIssue`, `ContributeToGoal` and `MergeMerchants`, which a pattern on "create|update|delete" would miss. Source: tyvsmith `src/tools/index.ts`.
3. **Match the server prefix the user actually gets**: a claude.ai custom connector or a differently named entry will not be `mcp__monarch__`. Have the guard key on a configurable list of server names and test it against the real name once connected. Source: rlorenzo plugin registers `monarch-money`; claude.ai connectors appear in Claude Code as `mcp__claude_ai_<Name>__`.
4. **Use `GetNetWorthHistory` with `include_account_breakdown` for a "what moved" report, and remember the weekly granularity beyond 60 days**. For an exact series, snapshot daily in fw.py. Source: tyvsmith `read/net-worth.ts`.
5. **Snapshot holdings yourself**, because Monarch keeps no history of holdings and has no holdings export. `fw.py` should save `GetInvestments` output (ticker, quantity, value, cost_basis) on each run. Source: tyvsmith `read/investments.ts`; Reddit 2026-10-05.
6. **Add a connection-health check before trusting a balance**, following rlorenzo's `monarch-doctor` rules (group by credential, `needs_reauth` beats a recent timestamp, $0 on a broken link is unknown, never delete). Source: rlorenzo/Monarch-Skills `skills/monarch-doctor/SKILL.md`.
7. **Key accounts on Monarch's id and flag twins** (same institution, similar name, one going stale as the other starts). Source: Reddit TSP duplicate (2026-04-23) and provider switch (2026-10-09).
8. **Keep the login out of the agent's tools** even when connected: rlorenzo withholds the in-client login in read-only mode, and finwright should equally never expose a "sign in" action. Source: rlorenzo README.
9. **If finwright ever writes a balance history back to Monarch** (not planned), copy echomodel's read-before-write interlock and back up first. Source: echomodel/monarch-access README.

## Avoid

1. **Any route that gives the agent a Monarch session** (cookie, token, password, TOTP secret). Unofficial sessions have full read and write access, last about two months, and there is no read-only scope. Source: pbassham README; echomodel README; jsilets (official consent is read+write too).
2. **Pickle or 0644 session files**, and "encrypted" files with a default passphrase. Source: monarchmoneycommunity issue #75; PulseMCP README.
3. **The abandoned `monarchmoney` (hammem) package and skills built on it**, such as ClawHub `silentknight87/monarch`. Source: ClawHub API; monarchmoneycommunity README.
4. **Re-importing Monarch's balance export as is**: the importer wants one account per file. Source: Reddit 2026-05-30; help.monarch.com (secondary).
5. **Treating Monarch's period change or "all time" graph as performance**. Source: Reddit 2026-01-05, 2026-03-23.
6. **Relying on the official connector being back**: it has been paused for over three months with no date. Source: Reddit 2026-08-19 staff post, 2026-10-10 user thread.
7. **Paying for Plus for the MCP**: the write cap is irrelevant to a read-only skill, and the MCP is down anyway. Source: Reddit 2026-06-18, 2026-09-08.
8. **Automated scripted logins**: Cloudflare, CAPTCHA and email OTP, plus throttling, can lock an account out. Source: PulseMCP README; tyvsmith README.
9. **Installing by short name**: `monarch` the command and "Monarch" the MCP can mean a coding agent or a biomedical graph. Source: npm search; official MCP registry search.

## Sources

| Name | Where listed | Type | Popularity signal | Last update | Link | Checked |
|---|---|---|---|---|---|---|
| Monarch MCP Connector help article | help.monarch.com | Official doc (403; via snippets) | n/a | 2026-06-30 | https://help.monarch.com/hc/en-us/articles/50207234679956-Monarch-MCP-Connector | 2026-10-12 |
| "MCP Update — Still Paused" (u/ozzie_monarch) | Reddit r/MonarchMoney | Official staff post | n/a | 2026-08-19 | https://www.reddit.com/r/MonarchMoney/comments/1vsrcyg/mcp_update_still_paused/ | 2026-10-12 |
| Recent Updates Roundup, June 2026 (u/Kait_Monarch) | Reddit | Official staff post | n/a | 2026-06-17 | https://www.reddit.com/r/MonarchMoney/comments/1u8lw4f/recent_updates_roundup_june_2026/ | 2026-10-12 |
| Recent Updates Roundup, September 2026 | Reddit | Official staff post | n/a | 2026-09-30 | https://www.reddit.com/r/MonarchMoney/comments/1wu576i/recent_updates_roundup_september_2026/ | 2026-10-12 |
| "My Experience with MCP and Codex in Monarch Plus" | Reddit | User report | n/a | 2026-06-18 | https://www.reddit.com/r/MonarchMoney/comments/1u9bfd0/my_experience_with_mcp_and_codex_in_monarch_plus/ | 2026-10-12 |
| "MCP server uncovering hidden investment holdings" | Reddit | User report | n/a | 2026-06-30 | https://www.reddit.com/r/MonarchMoney/comments/1ujt5e9/mcp_server_uncovering_hidden_investment_holdings/ | 2026-10-12 |
| "Losing my interest with the MCP lag" (and 10 similar threads) | Reddit | User reports | n/a | 2026-10-10 | https://www.reddit.com/r/MonarchMoney/comments/1x2ozfy/losing_my_interest_with_the_mcp_lag/ | 2026-10-12 |
| "Impossible to export or even print Investment Holdings" | Reddit | User report | n/a | 2026-10-05 | https://www.reddit.com/r/MonarchMoney/comments/1wyjklf/impossible_to_export_or_even_print_investment/ | 2026-10-12 |
| "Can't import account balances?" | Reddit | User report | n/a | 2026-05-30 | https://www.reddit.com/r/MonarchMoney/comments/1tscbjr/cant_import_account_balances/ | 2026-10-12 |
| "How to avoid the two-day problem?" | Reddit | User report | n/a | 2026-01-05 | https://www.reddit.com/r/MonarchMoney/comments/1q4r3r1/how_to_avoid_the_twoday_problem/ | 2026-10-12 |
| tyvsmith/monarch-money-remote-mcp | GitHub | MCP mirror of the official contract (Cloud Run) | 0 stars | pushed 2026-09-11 | https://github.com/tyvsmith/monarch-money-remote-mcp | 2026-10-12 |
| jsilets/monarch-mcp-ui | Glama (GitHub repo 404 now) | Proxy UI over the official MCP | not shown | not shown | https://glama.ai/mcp/servers/jsilets/monarch-mcp-ui | 2026-10-12 |
| rlorenzo/Monarch-Skills | GitHub | 6 Claude Code skills + pinned read-only robcerda | 0 stars | pushed 2026-09-25 | https://github.com/rlorenzo/Monarch-Skills | 2026-10-12 |
| echomodel/monarch-access | GitHub | CLI, SDK, MCP | 1 star | 2026-10-02 | https://github.com/echomodel/monarch-access | 2026-10-12 |
| bradleyseanf/monarchmoneycommunity | GitHub, PyPI | Python client (maintained fork) | 157 stars; 53,532 downloads/month | 1.6.0 on 2026-09-20; pushed 2026-10-12 | https://github.com/bradleyseanf/monarchmoneycommunity | 2026-10-12 |
| monarchmoneycommunity issue #40 (auth change) | GitHub | Breakage thread | 20 comments | 2026-05-15 | https://github.com/bradleyseanf/monarchmoneycommunity/issues/40 | 2026-10-12 |
| monarchmoneycommunity issue #75 (pickle, 0644) | GitHub | Security issue | open | 2026-08-25 | https://github.com/bradleyseanf/monarchmoneycommunity/issues/75 | 2026-10-12 |
| monarch-money-mcp-server (PulseMCP, tadasant) | npm; official MCP registry `com.pulsemcp/monarch-money` | MCP server | 318 downloads/month | 0.0.13, 2026-07-06 | https://www.npmjs.com/package/monarch-money-mcp-server | 2026-10-12 |
| monarch-money-api (pbassham) | npm, GitHub | JS client | 33 stars; 1,338 downloads/month | 0.0.8, 2026-09-16 | https://github.com/pbassham/monarch-money-api | 2026-10-12 |
| monarchmoney (keithah, TS) | npm | JS client | 5,975 downloads/month | 1.1.3, 2025-09-28 | https://www.npmjs.com/package/monarchmoney | 2026-10-12 |
| keithah/monarchmoney-ts-mcp | GitHub, Smithery, Glama | MCP server | 11 stars | 2026-10-06 | https://github.com/keithah/monarchmoney-ts-mcp | 2026-10-12 |
| @hakimelek/monarchmoney | npm; official MCP registry | JS client + MCP | 280 downloads/month | 0.3.1, 2026-03-15 | https://github.com/hakimelek/monarchmoney-node | 2026-10-12 |
| monarch-money-ts (chernetsov) | npm, GitHub | TS client | 9 stars; 534 downloads/month | 0.3.0, 2026-09-28 | https://github.com/chernetsov/monarch-money-ts | 2026-10-12 |
| monarch-api (brysonreece) | npm | TS SDK | 14 downloads/month | 0.1.1, 2026-03-11 | https://www.npmjs.com/package/monarch-api | 2026-10-12 |
| monarch-mcp (vargahis) | PyPI; official MCP registry; Glama; mcp.so | MCP server (robcerda fork, read-only default) | 704 downloads/month | 0.1.4, 2026-06-12 | https://github.com/vargahis/monarch-mcp | 2026-10-12 |
| monarch-cli (crcatala) | PyPI, GitHub | CLI, read-only default, keyring, dry-run | 7 stars; 270 downloads/month | 0.2.1, 2026-09-22 | https://github.com/crcatala/monarch-cli | 2026-10-12 |
| simplemind-dev/monarch-money-mcp-cli | GitHub | MCP + CLI, read-only default, Keychain | 1 star | 2026-10-03 | https://github.com/simplemind-dev/monarch-money-mcp-cli | 2026-10-12 |
| mikelane/monarch-mcp | GitHub | MCP, session.json 0600 | 5 stars | 2026-07-27 | https://github.com/mikelane/monarch-mcp | 2026-10-12 |
| jribnik/monarch-mcp | GitHub | MCP with typed confirm strings | 0 stars | 2026-10-06 | https://github.com/jribnik/monarch-mcp | 2026-10-12 |
| Steadro/monarch-mcp | GitHub | MCP, cookie auth | 1 star | 2026-06-04 | https://github.com/Steadro/monarch-mcp | 2026-10-12 |
| abekek/monarch-mcp-python | GitHub | Read-only MCP on AWS Bedrock AgentCore | 0 stars | 2026-07-19 | https://github.com/abekek/monarch-mcp-python | 2026-10-12 |
| alexpriest/monarch-mcp-server | GitHub | Read-only claude.ai connector (password + TOTP secret) | 0 stars | 2026-09-10 | https://github.com/alexpriest/monarch-mcp-server | 2026-10-12 |
| richardadonnell/monarch-money-mcp | GitHub | MCP + REST (n8n/Zapier) | 4 stars | 2026-08-21 | https://github.com/richardadonnell/monarch-money-mcp | 2026-10-12 |
| canfie1d, ezra-quemuel, frapbod, oyemecarnal, erikrubstein, mjstramel Monarch MCPs | GitHub, Glama | MCP servers | 0-4 stars | 2025-05 to 2026-10 | https://github.com/search?q=monarch+mcp&type=repositories | 2026-10-12 |
| LemurTech/Net-Worth-Navigator | GitHub, Reddit | Net worth projection tool (CSV parser) | n/a | 2026-07 | https://github.com/LemurTech/Net-Worth-Navigator | 2026-10-12 |
| ChrisQGeorge/Monarch-Backfill-Balance-History-From-Transactions | GitHub | Balance CSV tool | n/a | n/a | https://github.com/ChrisQGeorge/Monarch-Backfill-Balance-History-From-Transactions | 2026-10-12 |
| silentknight87/monarch | ClawHub | Skill (avoid) | 678 downloads, 12 installs | 2026-05-11 | https://clawhub.ai/silentknight87/skills/monarch | 2026-10-12 |
| davideasaf/monarch-money (ClawHub listing of a covered repo) | ClawHub, skills.sh | Skill | 3,372 downloads, 105 installs (ClawHub); 1 install (skills.sh) | 2026-05-11 | https://clawhub.ai/davideasaf/skills/monarch-money | 2026-10-12 |
| claudskills.com monarch-money (mirror of AI-Ready-Life) | claudskills.com | Skill mirror | n/a | n/a | https://claudskills.com/skills/monarch-money/SKILL.md | 2026-10-12 |
| Home Assistant `monarch_money` | home-assistant.io | Core integration | 96 active installs | since 2024.10 | https://www.home-assistant.io/integrations/monarch_money/ | 2026-10-12 |
| sanghviharshit/ha-monarchmoney | GitHub, HACS | HA integration | 39 stars | 2026-07-31 | https://github.com/sanghviharshit/ha-monarchmoney | 2026-10-12 |
| RobertParesi/Monarch-Money-Tweaks | GitHub, Chrome/Firefox/Safari stores | Browser extension (reports, holdings export) | 101 stars; 5,000+ installs | 2026-09-16 | https://github.com/RobertParesi/Monarch-Money-Tweaks | 2026-10-12 |
| Official MCP registry search "monarch" | registry.modelcontextprotocol.io | Registry | no Monarch-published entry | 2026-10-12 | https://registry.modelcontextprotocol.io/v0/servers?search=monarch | 2026-10-12 |
| mcpyet.com Monarch Money | mcpyet.com | Directory | n/a | verified 2026-08-10 | https://mcpyet.com/mcp/monarch-money/ | 2026-10-12 |
| Truthifi comparison and provider page | truthifi.com | Competitor marketing (conflicting) | n/a | Jun 2026 | https://truthifi.com/comparisons/truthifi-vs-monarch-money | 2026-10-12 |
| OpenBudget "Does Monarch Money Work with Claude?" | openbudget.sh | Competitor marketing | n/a | 2026-08-12 | https://www.openbudget.sh/blog/does-monarch-money-connect-to-claude | 2026-10-12 |
| HN comment "I feed live monarch money data to fable" | news.ycombinator.com | User report | n/a | 2026-08-02 | https://news.ycombinator.com/item?id=49141034 | 2026-10-12 |

Not found: no Monarch entry on Smithery's search API, no Raycast/Zapier/n8n integrations, no first-person blog post about Monarch with Claude beyond Reddit and one HN comment, and no official Monarch developer API.
