# Finding old 401(k)s from former employers

Read this when the user asks to find, track down or consolidate retirement money from previous jobs. Full research with sources: [finding old 401ks](../../../research/2026-10-12-finding-old-401ks.md) (checked 2026-10-12). The user does every sign-in, letter and call. The agent keeps the list with `fw.py hunt`, prepares the call notes and reads documents they download (redacted first).

## 1. One-time sweeps (they cover every employer at once)

1. **DOL Retirement Savings Lost and Found** (lostandfound.dol.gov, live since 2024-12-27). Sign-in is an ID-verified Login.gov account (SSN, non-VoIP phone, driver's license photos). Covers private employer and union plans, both pensions and 401(k)s. It does not cover IRAs, government plans or some church plans. A hit means they were in a plan once, not that money is still there. Its data is old Form 8955-SSA filings plus voluntary reports.
2. **SSA-L99-C1 notice**: free letter to SSA ERISA Correspondence Group, PO Box 33007, Baltimore MD 21290-3307 (address from a PBGC template letter, not found on ssa.gov). It lists plan name, plan number, administrator and an estimated vested value.
3. **IRS Wage and Income transcripts** (irs.gov, Get Transcript; the current year plus nine prior years). Note every W-2 with box 12 code D (401k) or AA (Roth 401k), every 1099-R (code G = direct rollover; 7 or 1 = paid out) and every 5498 (an IRA received money, often a safe-harbor IRA).
4. Jobs older than ten years: **Form SSA-7050** itemized earnings lists every employer ($61, about 120 days).
5. **Unclaimed money**: MissingMoney.com plus each state they lived in; PBGC's unclaimed pension search; the National Registry of Unclaimed Retirement Benefits (PenChecks still links it).

## 1b. Check what the user already has linked

Before the per-employer searches, ask for any overview that lists linked accounts (a bank's or broker's external accounts page, an aggregator such as Empower or Monarch, Fidelity NetBenefits). Plans show the sponsor's legal name, which is often not the brand on the resume, or a PEO's name when the employer used one, so match those to the resume. A safe-harbor or "auto-IRA" account at a trust company usually holds a small balance a plan forced out after the job ended.

## 2. Per employer: `fw.py hunt`

```
FW hunt add acme --employer "Acme Widgets Inc." --years 2011-2014 --note "W-2 2012 box 12 D"
FW hunt update acme --status searching --plan "Acme 401(k) Plan 001" --ein 12-3456789 --recordkeeper Empower
FW hunt update acme --status found --next "ask Empower for rollover forms" --note "ref 12345, J. Smith"
FW account add acme401k --type tax_deferred --institution Empower --last4 1234
FW hunt update acme --status rolled_over --account acme401k
FW hunt list
```

Statuses: `to_search`, `searching`, `found`, `merged`, `rolled_over`, `cashed_out`, `unclaimed`, `no_plan`, `closed`. A search stays open until it is closed, cashed out, has no plan, or is rolled over with `--account` set, so the money is counted once in net worth. Notes are dated automatically. Never put an SSN or a full account number in a note.

Steps for each employer:
1. Legal name and former names, years, city and state, parent or acquirer.
2. Evidence of a plan: W-2 box 12 D/AA or box 13 ticked, old statements, the SSA-L99, a Lost and Found hit.
3. **Form 5500 search** on efast.dol.gov by sponsor name or EIN: plan name and number, EIN, administrator, recordkeeper (Schedule C or the audit report), and whether the latest filing is final (merged or terminated). Line 4 shows earlier sponsor names. FreeERISA is a backup.
4. Merged: find the successor plan's 5500. Terminated: the final filing says where the assets went. Employer gone: EBSA Abandoned Plan search names the firm closing it out. Bankruptcy does not touch 401(k) money (it is in trust). Pension: PBGC search.
5. The user calls the recordkeeper with the script below.
6. "Paid out" or "rolled over": get the date, amount, and payee or receiving custodian (often Inspira, formerly Millennium Trust, or PenChecks), then contact that custodian. A check never cashed may be with a state.
7. Stuck: EBSA Benefits Advisor, 1-866-444-3272 or askebsa.dol.gov. Free, and they can contact the plan for the user.

Small balances: since 2024 a plan may pay out $7,000 or less without consent. Over $1,000 must go to a default safe-harbor IRA; $1,000 or less is usually mailed as a check. Auto-portability rule: the final rule went to OMB on 2026-09-14 (trade press), not yet in effect, so also check later employers' 401(k) statements for incoming transfers.

## 3. Call script (for the user)

> "I'm a former employee of [employer], [year] to [year]. Is there a balance under my Social Security number in the [plan name], plan number [001], EIN [xx-xxxxxxx]?"
> If yes: "What is the balance and as-of date? Can I get online access, a current statement and the rollover forms?"
> If no: "Was a distribution made? Date, amount, check or rollover? If an IRA, which custodian? If a check, was it cashed?"
> Wrong company: "Who is the current recordkeeper or successor plan?"
> Always: "Can I have a reference number and your name?"

Have ready: legal and former names, SSN, date of birth, current and old addresses (identity questions ask for old ones), employment dates, employee ID, plan name, number and EIN, any old statement or 1099-R. Record the reference number and name with `--note`.

## 4. Scams

- Every route above is free. A "lost 401(k) finder" who wants a percentage, an up-front fee or a login is a red flag.
- DOL never calls, texts or emails for a password or code, and DOL staff cannot search the database for anyone. Type lostandfound.dol.gov and login.gov by hand.
- Unsolicited rollover calls after a search push annuities. Never move money on a call the user did not start; call back on a number from the Form 5500 or a statement.
- What to do with found money (leave it, roll it to a current plan or an IRA) is the user's decision. Explaining the options is fine; recommending a product is not.
