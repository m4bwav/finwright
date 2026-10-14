# Learnings: finwright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md (LEARNINGS-FORMAT). Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first, by meaning (`evergreen.py search "<the lesson>" --kinds learnings` finds near-duplicates in every registered unit): add / update / retire / none. Trigger and Hypothesis are required. Promote after three confirmations; retire when harmful > helpful.

Entries here are public. They never name the user's institutions, employers, plans, account nicknames, figures or local paths; a lesson that needs those goes to the user's private overlay (`~/.finwright/OVERLAY.md`), with a neutral version here when the lesson is general.

## Active

### L-001 · 2026-10-13 · `bofa-activity-csv-shape`: Bank of America activity CSVs have a summary block and no account number
- Trigger: Bank of America activity CSVs carry no account identifier, and repeat downloads are named stmt.csv, stmt(1).csv.
- Hypothesis: the bank exports the same layout for every deposit account; only the download order tells them apart.
- Rule: ask which account each file is, or tell them apart by content (for example, deposits from an employer), then `fw.py import bofa <file> <account> --monthly`; check the printed linked accounts for ones net worth does not track.
- Evidence: C-20261013-1; the arithmetic check passes on sample files
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-002 · 2026-10-13 · `memory-of-old-401ks-is-unreliable`: check old downloads before marking an employer as no plan
- Trigger: people often do not link a PEO-run plan to the employer, so they report "no plan" when there was one; an old statement in a downloads folder is often the only trace.
- Hypothesis: PEO-run plans carry the PEO's name, not the employer's, so people do not connect them to the job.
- Rule: before `hunt update --status no_plan`, search the user's downloads and documents folders for 401k, stmt, recordkeeper and PEO names, and check W-2 box 12 D for those years; ask whether the employer used a PEO.
- Evidence: general pattern; see research/2026-10-12-finding-old-401ks.md
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-003 · 2026-10-13 · `bond-account-balance-dropped`: a savings bond total entered as a balance vanished from net worth
- Trigger: a savings bond total entered as one balance (as aggregators show it); `balance set` on a savings_bond account recorded it, but `networth` left it out without a warning.
- Hypothesis: compute_networth skipped every savings_bond account because bonds were meant to be valued from bonds.csv only.
- Rule: fixed in C-20261013-2; after any new account type gets its first balance, confirm `networth` "By type" shows it.
- Evidence: C-20261013-2, test_bond_account_total_until_bonds_listed
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-004 · 2026-10-13 · `aggregator-overview-finds-old-plans`: an account overview found more old 401(k)s than the hunt
- Trigger: aggregator and bank "linked accounts" pages often still list plans from former employers, under the sponsor's legal name or a PEO's name, and forced-out small balances as trust company IRAs.
- Hypothesis: aggregators keep linked plan accounts after the job ends; the plan name is the sponsor's legal name or the PEO's, not the brand name on the resume.
- Rule: early in a hunt, ask the user for any overview they already have (a bank's or broker's linked accounts page, Empower, Fidelity NetBenefits) and match sponsor legal names and PEOs to resume employers before starting Form 5500 searches.
- Evidence: general pattern
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-005 · 2026-10-13 · `fstring-same-quotes-need-312`: fw.py promised Python 3.10 but only parsed on 3.12+
- Trigger: an f-string reused its own double quotes inside a replacement field (`f"{sum(r["amount"] ...)}"`); tests passed on 3.14 while 3.10 and 3.11 could not import the file.
- Hypothesis: PEP 701 (3.12) made that legal, so a newer local Python hides the break.
- Rule: run the tests on the oldest supported Python before a release (`py -3.11` here; CI runs 3.10); use the other quote kind inside replacement fields.
- Evidence: T-20261013-1
- Scope: repo
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-006 · 2026-10-13 · `efast2-json-api`: the Form 5500 search page refuses agents, its JSON API does not
- Trigger: a hunt needs Form 5500 filings for several former employers; efast.dol.gov/5500Search is a script-driven page and a plain fetch gets nothing useful.
- Hypothesis: the page calls a public search API that answers any GET carrying a browser User-Agent.
- Rule: query `https://www.efast.dol.gov/services/afs?q.parser=lucene&size=200&q=<field>:<value>` (fields `plansponsor`, `planname`, `ein`), read `pdfpath` from each hit and fetch the filing from `https://efast2-filings-public.s3.amazonaws.com/prd` + that path. For an employer with no plan of its own, search the PEO plans and read their participating-employer lists. Recorded in references/old-401ks.md step 3.
- Evidence: a three-employer search found two terminated plans (one merged into an acquirer's plan, one fully paid out) and one PEO participation, all from public filings.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-007 · 2026-10-13 · `home-value-listing-sites-refuse-agents`: the big listing sites gave no home estimate to an agent
- Trigger: the user asked the agent to look up their home's value; a Redfin property URL returned HTTP 405 to a fetch and a web search surfaced no Zillow page for the address.
- Hypothesis: the large listing sites block automated fetches; local brokerages publish their own comps-based estimate pages per property, often keyed by the county appraisal district id, and those load.
- Rule: search the address with the brokerage-site results in mind, fetch that page, record the estimate with `balance set home <value> --source <site> --method comps-avm`, keep the URL in the user's overlay so the next revaluation is one fetch, and cross-check against the mortgage servicer's equity estimate when the user has one.
- Evidence: one lookup, two refused routes and one that worked, 2026-10-13
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-13

### L-008 · 2026-10-14 · `pr-merge-commit-uses-web-email`: GitHub's pull request merge commit carried the maintainer's personal email
- Trigger: the first pull request on the repository failed the CI leak gate. The branch's commit used the no-reply identity and passed locally; the history scan flagged only the merge commit GitHub builds to test a pull request (refs/pull/N/merge), whose author was the account's web-commit email.
- Hypothesis: GitHub authors web-made commits (test merges, merge and squash buttons) with the account's primary email unless "Keep my email addresses private" is on, so a repository can be clean while every GitHub-made commit is not.
- Rule: before a public repository takes pull requests, turn on "Keep my email addresses private" (github.com/settings/emails). Until then, land the maintainer's own branches by fast-forwarding master, not with a merge or squash button, and treat a leak-gate failure on a merge commit as real.
- Evidence: CI run on pull request 1, 2026-10-14: tree clean, history 1 finding on the GitHub merge commit only
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-14
