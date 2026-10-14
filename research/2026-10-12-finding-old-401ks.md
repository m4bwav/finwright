# Finding old 401(k)s and other retirement accounts from former employers

Research date: 2026-10-12. Every source was checked on 2026-10-12 unless a different date is given. Several primary pages (dol.gov newsroom, efast.dol.gov, missingmoney.com, inspirafinancial.com, unclaimedretirementbenefits.com) returned HTTP 403 or 404 to automated fetches; claims resting only on secondary coverage are marked **(secondary)** and claims not confirmed anywhere are marked **(unverified)**. Confirm both before code or advice depends on them.

Scope: how one US individual traces workplace retirement money from past jobs, including balances that were force-cashed-out, rolled into a default (safe-harbor) IRA, moved after a merger or bankruptcy, or paid out when a plan terminated. finwright never signs in anywhere; the user does every Login.gov sign-in, phone call and letter, and finwright records the results.

Related: [2026-10-12-data-access-routes.md](2026-10-12-data-access-routes.md) (getting data out of accounts once found), [2026-10-12-method-rules-and-security.md](2026-10-12-method-rules-and-security.md).

## Summary

No single place lists every old account, so the search runs on several tracks at once. The DOL's Retirement Savings Lost and Found database (live since 27 December 2024) is the best first stop, but it only lists private-sector employer and union plans, it was first populated with people aged 65 or older plus historical Form 8955-SSA records, and a hit only proves you were in a plan, not that money is still owed. The SSA will mail a Form SSA-L99-C1 notice listing plans that reported you as a separated participant with a vested benefit. For each former employer, the plan name, EIN and administrator can be found from the plan's Form 5500 on efast.dol.gov; mergers usually move the account into the buyer's plan, bankruptcy does not reach plan assets (they are held in trust), and abandoned plans are wound up by a qualified termination administrator listed in EBSA's Abandoned Plan search. Balances of $7,000 or less (the SECURE 2.0 limit since 2024, up from $5,000) can be forced out without consent: $1,000 or less is usually paid by check, and $1,000.01 to $7,000 must go to a safe-harbor IRA at a provider such as Inspira Financial (formerly Millennium Trust) or PenChecks Trust. Uncashed checks and some small balances end up as state unclaimed property (MissingMoney.com). W-2 box 12 code D and the IRS Wage and Income transcript (ten years) show which employers took 401(k) deferrals; SSA's itemized earnings statement (Form SSA-7050, paid) lists every employer for older years. All of these searches are free; anyone charging to "find your 401(k)" is selling what you can do yourself, and the DOL never calls, texts or emails for sign-in codes.

## 1. DOL Retirement Savings Lost and Found database

**What it is.** An online database built under SECURE 2.0 section 303, which added ERISA section 523 and told the DOL to build it by 29 December 2024. EBSA launched the public search on 27 December 2024. URL: https://lostandfound.dol.gov/ . It is "an information database only": it does not decide eligibility and pays nothing.

**Status in 2026.** Live and reachable on 2026-10-12. The page shows no "last updated" date. No 2026 DOL rule or notice widening its data was found; the DOL said it would "gradually expand" the database through further notice and comment **(secondary: ASPPA, December 2024)**. Usage reported in press coverage: from launch to the end of 2025, about 236,269 unique visitors, of whom 69,712 (29.5%) found a plan tied to their SSN **(secondary: CNBC via rethinking65.com; figures not found on dol.gov)**.

**How to use it.**
1. Create or use a Login.gov account and complete identity proofing: legal name, date of birth, SSN, a mobile phone (or a landline, not VoIP) for phone verification, and front and back photos of a driver's license or state ID. US passports and military IDs were not accepted at the time of checking. If you cannot use the phone number on record, the site says there is no alternative route.
2. Sign in at lostandfound.dol.gov; the results list only plans linked to the account holder's own SSN.
3. For each plan listed, contact the plan administrator shown. DOL staff cannot search for you. If the contact details are dead, call an EBSA Benefits Advisor at 1-866-444-3272 or https://askebsa.dol.gov . Technical problems: RSLFSupport@dol.gov; Login.gov problems: https://login.gov/help .
4. Opting out (blocking anyone from seeing data linked to your SSN) needs no Login.gov account; opting back in does.

**Coverage.** Private-sector employer and union plans, both defined benefit pensions and defined contribution plans such as 401(k)s. Not covered: IRAs (including safe-harbor rollover IRAs, unless an administrator reported the IRA provider), government plans, certain religious organization plans, Social Security, and a deceased spouse's benefits.

**Where the data comes from.**
- Historical Form 8955-SSA records from the SSA, "some of which may be outdated" (lostandfound.dol.gov; the page gives no year range and uses a 2005 filing as an example of stale data). Form 8955-SSA is where plans report separated participants with a deferred vested benefit; it is not updated when the person later rolls over or cashes out, so a hit can be for money already paid.
- Voluntary submissions by plan administrators and recordkeepers through an intake portal (lostandfound-intake.dol.gov). The November 2024 EBSA fact sheet asked only for the name and SSN of each participant who has separated from service, is owed a benefit and is age 65 or older, plus current administrator contact details, updated at least yearly. Submission is voluntary. Earlier plans to receive 8955-SSA data straight from the IRS stalled when the IRS declined to release it **(secondary: PSCA, April 2024)**; the live site now says it holds SSA 8955-SSA history, so some data sharing evidently happened, but the terms were not found on a primary page **(unverified)**.
- Commercial business search tools to fill in missing or outdated administrator contact details.

Practical consequence: someone under 65 may get a hit from old 8955-SSA data but will not be covered by the voluntary recordkeeper feed, and an empty result proves nothing.

**What results look like.** A list of retirement plans linked to your SSN, each with the plan name and plan administrator contact information (and, where reported, an IRA trustee or annuity issuer **(secondary: beancount.io, 2026-09-25)**). Results show that you "participated in a retirement plan at some point"; benefits may have been paid in a lump sum, rolled over or annuitized. Only the plan administrator can confirm what is owed.

## 2. SSA Notice of Potential Private Retirement Benefit Information (Form SSA-L99-C1)

**What it is.** A notice the SSA mails using information the IRS forwards from plan administrators' Form 8955-SSA filings. The SSA sends it automatically to people who apply for Social Security benefits and must also provide it on request. There is one notice per plan that reported you, so a person may get several or none.

**What it lists** (SSA POMS RM 03253.002): plan name; a 12-digit plan number (the 9-digit EIN plus the 3-digit plan number); plan administrator name, address and EIN; and deferred vested benefit details: plan year reported, estimated amount and payment frequency, annuity type codes, units or shares at separation, and value of account. The dollar figures are estimates and may be wrong (PBGC). Plans report when a benefit is earned, not when it is paid, so the notice does not prove money is still owed. SSA is not the source of the data and usually cannot answer questions about it; questions go to EBSA.

**How to request it.** No fee was found on any page. The PBGC publishes a fillable request letter (https://www.pbgc.gov/sites/default/files/documents/l99-request-letter-fillable.pdf) addressed to:

> OCO Office of Earnings Operations, Attention: ERISA Correspondence Group, P.O. Box 33007, Baltimore, MD 21290-3307

The letter gives full name, SSN, date of birth, name of the former employer and its EIN (if known), a certification that you are the person named, the return address, signature and date, and asks for "a Form SSA-L99-C1 Potential Private Pension Benefit Information Notice." The address and process were not found on an ssa.gov page **(the PBGC letter is the only source; confirm with SSA at 1-800-772-1213 before mailing if in doubt)**. Processing time was not published.

**Use.** It is the closest thing to a list of every plan that ever reported you as a vested leaver. It gives the EIN and plan number, which feed straight into the Form 5500 search below.

## 3. Finding the plan from the employer name

**Form 5500 search (primary, free).** Most ERISA plans file a Form 5500 or 5500-SF every year, publicly searchable through EFAST2 at https://www.efast.dol.gov/5500search/ (help page: https://www.efast.dol.gov/5500Search/help/help.html). Search by plan sponsor name, plan name, EIN (with or without the hyphen) or acknowledgement ID; the plan name is usually the employer name plus the plan type, and `*` works as a wildcard. What a filing gives you:
- Line 1: plan name and three-digit plan number (001, 002 ...).
- Line 2: plan sponsor name, address and EIN.
- Line 3: plan administrator (if different from the sponsor).
- Line 4: prior sponsor name and EIN, which is how name changes and mergers show up.
- Schedule C and the attached audit report often name the recordkeeper and trustee (for example Fidelity, Empower, Principal).
- The final-year filing is marked as a final return, and the plan's assets show as transferred or distributed; that is the signal the plan terminated or merged.
Since 2022 some plans file as part of a defined contribution group (DCG) filing, so the plan may sit inside a provider's group filing. The search UI blocked automated fetches on 2026-10-12; the fields above come from DOL's help page and the Form 5500 itself.

**FreeERISA** (https://freeerisa.benefitspro.com/, run by Judy Diamond Associates) indexes Form 5500s with free registration and a "dynamic name search" that follows sponsor name changes. A third-party monitor showed its login returning 403 in late July 2026 **(secondary; check before relying on it)**. It adds convenience, not data; the EFAST2 search is the primary source.

**Merged or acquired employer.** In an acquisition, the old 401(k) is usually merged into the buyer's plan or terminated and paid out. Search Form 5500 for the old plan's last filing (it shows the plan as merged or terminated) and the buyer's plan (line 4 may list the old sponsor). Then call the buyer's HR or benefits center, or the recordkeeper of the buyer's plan, with the old plan name and EIN. EBSA's "What You Should Know About Your Retirement Plan" says to ask the plan administrator and use the Summary Plan Description and benefit statements. If a plan terminates, participants become 100% vested.

**Bankrupt or vanished employer.**
- 401(k) money must be held in trust or an insurance contract, and the employer's creditors have no claim on it (DOL FAQs about Retirement Plans and ERISA; DOL fact sheet on employee benefits in bankruptcy). The risk is deferrals withheld from pay but never sent to the plan; EBSA investigates those.
- Abandoned plans: when the sponsor has disappeared, a qualified termination administrator (QTA; a bank, insurer or similar) winds up the plan under EBSA's Abandoned Plan Program. Search by plan or employer name at https://www.askebsa.dol.gov/AbandonedPlanSearch/ ; it shows whether a plan is being or has been terminated and the QTA's contact details. If you do not respond to the QTA's termination notice within 30 days, it generally rolls the balance to an IRA; balances of $1,000 or less may instead go to an interest-bearing insured bank account or a state unclaimed property fund. Reasonable termination expenses may already have been deducted.
- A DOL rule to let Chapter 7 bankruptcy trustees use the Abandoned Plan Program was proposed in December 2012 (dol.gov release ebsa20121211); whether and when it was finalized was not confirmed in this pass **(unverified)**.

**Defined benefit pensions (PBGC).** If an old employer had a traditional pension that ended, search PBGC's unclaimed benefits database (last name plus last four of the SSN) at https://www.pbgc.gov/workers-retirees/find-unclaimed-retirement-benefits/search-unclaimed (updated quarterly; last update shown 5 August 2026). PBGC's Missing Participants Program has also covered defined contribution plans (401(k), profit sharing, money purchase, ESOP, 403(b)(7)) that terminated on or after 1 January 2018, but only when the plan chose to use it. Check the transferred-plans and notification-plans spreadsheets linked from https://www.pbgc.gov/workers-retirees/learn/find-your-retirement-benefits ; for a transferred plan call 1-800-400-7242 and say it is about an "MP" benefit; for a notification plan contact the named insurer or IRA provider directly. Ongoing plans, even frozen ones, are not in these lists.

## 4. Small balances: cash-outs, safe-harbor IRAs, unclaimed property and auto-portability

**The rules.** A plan may pay out a former employee's vested balance without consent when it is $7,000 or less; SECURE 2.0 section 304 raised the limit from $5,000 for distributions after 31 December 2023 (IRS Notice 2026-13 safe harbor explanations; IRS Form 1099-R instructions). Amounts from earlier rollovers into the plan may be ignored when testing the limit. If the forced distribution is more than $1,000 and the person makes no election, the plan must roll it directly to an IRA (the automatic rollover rule); $1,000 or less is usually just paid by check, with tax withheld. The DOL safe harbor for picking the IRA provider requires a capital-preserving default investment (often an FDIC-insured deposit), which can earn very little while fees continue.

So for each old job, the money may be: still in the plan; rolled into a safe-harbor IRA (balance about $1,000 to $7,000, or up to $5,000 before 2024); paid by a check that was never cashed; or escheated to a state.

**Who commonly holds safe-harbor (automatic rollover) IRAs.**
- **Inspira Financial**, the current name of Millennium Trust Company and PayFlex (confirmed in an Inspira comment letter on the DOL docket 1210-AC21). Its own site blocked automated fetches; third-party guides say claiming runs through inspirafinancial.com ("claim retirement account") with the SSN and an account number from the plan's notice, or by phone **(secondary)**. Millennium Trust ran a free SSN-based missing-account search from about 2015 **(secondary, status today unverified)**.
- **PenChecks Trust**: its individuals page (https://penchecks.com/individuals/mybenefitelection/) has "I'm searching for lost retirement funds left behind with a former employer" and a "Search for lost funds" button; phone 800-541-3938; claims through https://my.penchecks.com/ .
- **National Registry of Unclaimed Retirement Benefits** (https://www.unclaimedretirementbenefits.com/), a PenChecks subsidiary since 2005 and free for participants. On 2026-10-12 PenChecks' own page still linked to it as its lost-funds search, so it appears to be operating, but the site itself refused the automated fetch **(partly verified)**. It only holds records that subscribing plan sponsors or administrators chose to post.
- Others named in industry coverage include the big recordkeepers' own IRA arms and Retirement Clearinghouse **(secondary)**. The plan's Form 5500 final filing, the termination or force-out notice, a Form 1099-R for the year of the rollover, and a Form 5498 from the IRA custodian all name the receiving custodian.

The fastest way to find a safe-harbor IRA is usually the Form 1099-R (the plan reported a direct rollover, code G) and Form 5498 (the IRA reported the contribution), both of which show up on the IRS Wage and Income transcript (section 5).

**State unclaimed property.** Uncashed distribution checks and abandoned IRAs can be turned over to the state of the owner's last known address. Search every state you have lived in through MissingMoney.com, the free multi-state search run by NAUPA (https://www.missingmoney.com/ ; NAUPA at https://unclaimed.org/), and the individual state site for states that do not take part. NAUPA also runs the States Unclaimed Retirement Clearinghouse for plans reporting uncashed retirement checks. Claims are free on the state site; private "finders" charge a percentage (some states cap these fees) **(cap details unverified)**.

**Auto-portability.** The Portability Services Network (PSN), owned by large recordkeepers (Alight, Fidelity, Empower, TIAA, Principal and Vanguard per press reports, with Retirement Clearinghouse running it), automatically moves small balances (now up to $7,000) from an old plan via an intermediate IRA into the participant's new employer's plan, if both plans take part and the person does not opt out. About 21,000 plan sponsors had adopted it by a recent 30 September count **(secondary, year not stated)**. SECURE 2.0 section 120 created the fee exemption; the DOL proposed its regulation in January 2024 and sent the final rule to OIRA on 14 September 2026; it had not been published as of the September 2026 reports found **(secondary: ASPPA, PSCA, NAPA, September 2026)**. No public participant lookup was found. Practical consequence: a small balance from an old job may already have moved into a later employer's 401(k); check each later plan's statement for an incoming "portability" or "rollover" transaction.

## 5. Old W-2s and IRS transcripts as evidence

- **W-2 box 12 code D** is elective deferrals to a 401(k) (including SIMPLE 401(k) and catch-up amounts); **code AA** is designated Roth 401(k) contributions. Code E is 403(b), G is 457(b), and EE is Roth 457(b). Box 13 "Retirement plan" ticked means the employee was an active participant in some employer plan that year (it is also ticked for employer-only contributions). A code D or AA amount for an employer proves a 401(k) account existed (IRS General Instructions for Forms W-2 and W-3, 2026).
- **IRS Wage and Income transcript**: covers the current tax year and nine prior years, from information returns filed with the IRS: W-2, 1099 series (so 1099-R distributions and rollovers), 1098 and 5498 (IRA contributions and rollovers in, which reveal safe-harbor IRAs). Current-year data posts around the first week of February. If there are more than about 85 documents for a year, the online account will not generate it and you must file Form 4506-T. Order through the IRS Individual Online Account (the user signs in; ID.me or Login.gov) or Form 4506-T (https://www.irs.gov/individuals/transcript-types-and-ways-to-order-them).
- **Older than ten years**: the SSA itemized statement of earnings lists every employer's name and address with yearly earnings for any years requested, via Form SSA-7050 (https://www.ssa.gov/forms/ssa-7050.html). Fees found: $61 non-certified, $96 certified itemized (FY 2025 amounts; confirm before paying); allow about 120 days. The free my Social Security earnings record shows yearly totals only, without employer names. This gives the list of employers to check; it does not show 401(k) participation.

## 6. Per-employer checklist

Run this once per former employer. finwright can hold the list and the results; the user does the sign-ins, letters and calls.

**A. One-time sweeps (do first, they cover all employers at once)**
1. Lost and Found database (Login.gov). Save the result list.
2. Mail the SSA-L99-C1 request letter.
3. Pull IRS Wage and Income transcripts for the last ten years; note every W-2 with box 12 D/AA, every 1099-R (code G = direct rollover; code 7 or 1 = paid out) and every 5498.
4. If jobs go back more than ten years, order the SSA-7050 itemized statement for those years.
5. MissingMoney.com plus each state lived in; PBGC unclaimed search; NRURB / PenChecks search.

**B. Per employer**
1. Write down: employer legal name (and any former names), years worked, city and state, any parent company or acquirer.
2. Did it have a plan? Evidence: W-2 box 12 D/AA, box 13 ticked, old statements, the SSA-L99 notice, or a Lost and Found hit.
3. Find the plan on EFAST2 Form 5500 search: plan name, plan number, sponsor EIN, administrator, recordkeeper (Schedule C or audit report), and whether the latest filing is a final return (merged, terminated).
4. If merged: find the successor plan and its recordkeeper. If terminated: check the final filing for where assets went. If abandoned: search the EBSA Abandoned Plan list for the QTA. If a defined benefit pension: PBGC search and PBGC MP spreadsheets.
5. Call the recordkeeper (or the employer's HR or benefits center) with the script below.
6. If the recordkeeper says "paid out" or "rolled over": ask for the date, amount, payee or receiving IRA custodian and account number, then contact that custodian (Inspira, PenChecks, other) or check the 1099-R/5498 on the transcript. If a check was never cashed, search state unclaimed property.
7. If nothing works: EBSA Benefits Advisor, 1-866-444-3272 or askebsa.dol.gov (free; they can contact plans on your behalf).
8. Record the result (below) and decide what to do with the money (leave it, roll it into a current plan or IRA); that decision is the user's.

**What to have ready for a call**: full legal name and any former names; SSN; date of birth; current address and every address used while employed there (identity questions often ask for an old address); employment dates; employee ID if known; plan name, plan number and EIN from the Form 5500; any old statement, 1099-R or letter. Never give a password or a one-time code to anyone who calls you.

**Call script (recordkeeper or plan administrator)**

> "Hi, I'm a former employee of [employer], where I worked from [year] to [year]. I'm trying to find out whether I still have a balance in the [plan name], plan number [001], EIN [xx-xxxxxxx]. Can you look up whether there is an account under my Social Security number?"
>
> If yes: "What is the current balance and as-of date? Is the account active, and can I get online access? Please mail or email me a current statement and the forms to roll it over."
>
> If no account: "Can you tell me whether a distribution was made, and if so, the date, the amount, and whether it was paid by check or rolled over to an IRA? If it went to an IRA, which custodian and account number? If a check was issued, was it cashed?"
>
> If they are not the right company: "Do you know who the current recordkeeper or successor plan is, or who handled the plan when it ended or merged?"
>
> Before hanging up: "Can I have a reference number for this call and your name?"

**What to record** (one row per plan; this is the shape finwright should store):

| Field | Example |
|---|---|
| Former employer (legal name; former names) | Acme Widgets Inc. (formerly Acme Tool Co.) |
| Years employed | 2009-2013 |
| Plan name and number | Acme Widgets 401(k) Plan, 001 |
| Sponsor EIN | 12-3456789 |
| Plan type | 401(k), DB pension, 403(b), ... |
| Recordkeeper / administrator now holding it | Empower |
| Evidence of participation | W-2 2011 box 12 D; SSA-L99; Lost and Found hit |
| Status | active / merged into X / terminated / paid out / rolled to IRA / escheated / not found |
| Where it is now | account at recordkeeper, IRA at Inspira #..., state of OH unclaimed property |
| Balance and as-of date | 4,812.33 as of 2026-10-12 |
| Date checked, method, reference number, contact name | 2026-10-12, phone, ref 12345, J. Smith |
| Next action and due date | request rollover forms, 2026-10-26 |

Store account numbers redacted (last four) per finwright's privacy rules.

## 7. Scams to avoid

- **Paid "lost 401(k) finder" services.** Everything above is free: Lost and Found, the SSA-L99 notice, Form 5500 search, the Abandoned Plan search, PBGC, NRURB, MissingMoney.com and EBSA's Benefits Advisors. The Lost and Found site says DOL charges no fee and warns against paying anyone who offers to recover funds on DOL's behalf (paraphrased from the page by the fetch tool; wording not quoted exactly). Some fee-based "consolidation" services are legitimate businesses, but they are paid by moving your money into their products; treat any finder who wants a percentage, a fee up front or your login as a red flag.
- **DOL or Login.gov impersonation.** Quoted from lostandfound.dol.gov: "DOL will never call, text, or email you to ask for your password, one-time passcode, or other sign-in information." DOL staff cannot search the database for you, so a caller offering to "check the DOL database" for you is not DOL. Type lostandfound.dol.gov and login.gov yourself rather than clicking links. No DOL alert describing a specific Lost and Found phishing campaign was found in this pass.
- **Rollover pressure.** Unsolicited calls after a Lost and Found search or a termination notice urging a rollover into an annuity or a particular IRA. Verify any QTA through the EBSA Abandoned Plan search and any custodian through the plan's own documents before acting.
- **Never move money on a call you did not start.** Call back on a number from the Form 5500, a statement or the company's official site.

## Sources (all checked 2026-10-12 unless noted)

Primary:
- DOL Retirement Savings Lost and Found database: https://lostandfound.dol.gov/
- AskEBSA, Lost and Found opt-out and use page: https://www.askebsa.dol.gov/WebIntake/home.aspx/optout
- EBSA fact sheet, Retirement Savings Lost and Found information collection request (18 Nov 2024): https://www.dol.gov/sites/dolgov/files/ebsa/about-ebsa/our-activities/resource-center/fact-sheets/retirement-savings-lost-and-found-information-collection-request.pdf
- EBSA filing instructions for plan administrators: https://www.dol.gov/sites/dolgov/files/EBSA/laws-and-regulations/laws/secure-2.0/instruction-for-lost-and-found-act2022.pdf
- EBSA Lost and Found supporting statement (PRA): https://dol.gov/sites/dolgov/files/EBSA/laws-and-regulations/laws/secure-2.0/lost-and-found-supporting-statement-act2022.pdf
- DOL news release, start of information collection (18 Nov 2024; 403 to fetch, title only): https://www.dol.gov/newsroom/releases/ebsa/ebsa20241118-0
- EBSA Abandoned Plan Program: https://www.dol.gov/agencies/ebsa/employers-and-advisers/plan-administration-and-compliance/abandoned-plan-program
- EBSA Abandoned Plan search: https://www.askebsa.dol.gov/AbandonedPlanSearch/
- EBSA, What You Should Know About Your Retirement Plan: https://www.dol.gov/agencies/ebsa/about-ebsa/our-activities/resource-center/publications/what-you-should-know-about-your-retirement-plan
- EBSA FAQs about Retirement Plans and ERISA: https://www.dol.gov/agencies/ebsa/about-ebsa/our-activities/resource-center/faqs/retirement-plans-and-erisa
- EBSA fact sheet, employee benefits in bankruptcy: https://www.dol.gov/sites/dolgov/files/ebsa/about-ebsa/our-activities/resource-center/fact-sheets/employee-benefits-bankruptcy.pdf
- DOL release, proposed rule for Chapter 7 trustees (Dec 2012): https://www.dol.gov/newsroom/releases/ebsa/ebsa20121211
- EFAST2 Form 5500 search: https://www.efast.dol.gov/5500search/ (403 to fetch) and help: https://www.efast.dol.gov/5500Search/help/help.html
- PBGC, Notice of Potential Private Retirement Benefit Information: https://www.pbgc.gov/about/advocate/resources/ssa-notice
- PBGC SSA-L99 request letter: https://www.pbgc.gov/sites/default/files/documents/l99-request-letter-fillable.pdf
- SSA POMS RM 03253.002 (SSA-L99-C1 contents): https://secure.ssa.gov/poms.NSF/lnx/0103253002
- SSA POMS RM 03258.003 (ERISA correspondence): https://secure.ssa.gov/POMS.nsf/lnx/0103258003
- SSA Form SSA-7050: https://www.ssa.gov/forms/ssa-7050.html and FAQ: https://www.ssa.gov/faqs/en/questions/KA-02507.html
- PBGC, Find your retirement benefits: https://www.pbgc.gov/workers-retirees/learn/find-your-retirement-benefits
- PBGC unclaimed benefits search: https://www.pbgc.gov/search-unclaimed-pensions
- PBGC press release, Missing Participants Program extended to 401(k) and other plans (2017): https://www.pbgc.gov/news/press/pr17-12
- IRS, Transcript types and ways to order them: https://www.irs.gov/individuals/transcript-types-and-ways-to-order-them
- IRS, General Instructions for Forms W-2 and W-3 (2026): https://www.irs.gov/instructions/iw2w3
- IRS, Common errors on Form W-2 codes for retirement plans: https://www.irs.gov/retirement-plans/common-errors-on-form-w-2-codes-for-retirement-plans
- IRS Notice 2026-13, safe harbor explanations ($7,000 thresholds): https://www.irs.gov/pub/irs-drop/n-26-13.pdf
- IRS Instructions for Forms 1099-R and 5498 (2026): https://www.irs.gov/instructions/i1099r
- IRS, Rollovers of retirement plan and IRA distributions: https://www.irs.gov/retirement-plans/plan-participant-employee/rollovers-of-retirement-plan-and-ira-distributions
- NAUPA: https://unclaimed.org/ ; MissingMoney.com: https://www.missingmoney.com/ (403 to fetch)
- PenChecks, individuals: https://penchecks.com/individuals/mybenefitelection/
- National Registry of Unclaimed Retirement Benefits: https://www.unclaimedretirementbenefits.com/ (403 to fetch)
- DOL docket 1210-AC21 comment from Inspira Financial: https://www.dol.gov/sites/dolgov/files/ebsa/laws-and-regulations/rules-and-regulations/public-comments/1210-AC21/00008.pdf

Secondary (used where primary pages were missing or blocked):
- ASPPA, Final automatic portability rule nearing the finish line (Sept 2026): https://www.asppa-net.org/news/2026/9/final-automatic-portability-rule-nearing-the-finish-line/
- PSCA, Auto-portability final rule nears final stage (Sept 2026): https://www.psca.org/news/psca-news/2026/9/auto-portability-final-rule-nears-final-stage/
- PSCA, Lost retirement accounts and data collection (Dec 2025): https://www.psca.org/news/psca-news/2025/12/lost-retirement-accounts-and-data-collection/
- PSCA, DOL turns to recordkeepers for help with Lost and Found (Apr 2024): https://www.psca.org/news/psca-news/2024/4/dol-turns-recordkeepers-help-lost-and-found-database/
- PLANADVISER, DOL's Lost and Found database goes live: https://www.planadviser.com/dols-retirement-savings-lost-found-database-goes-live/
- rethinking65.com, Can't find your old 401(k)? (usage figures): https://rethinking65.com/cant-find-your-old-401k-check-out-this-new-dol-tool/
- beancount.io guide (2026-09-25): https://beancount.io/blog/2026/09/25/lost-401k-dol-retirement-savings-lost-found-database-guide
- Faegre Drinker on EBSA missing-participant guidance (Mar 2026): https://www.faegredrinker.com/en/insights/publications/2026/3/heather-bader-comments-on-dols-guidance-for-locating-missing-participants-in-plansponsor
- PLANSPONSOR, PSN adoption: https://www.plansponsor.com/nearly-21000-plan-sponsors-have-adopted-psn-auto-portability
- PLANSPONSOR, Millennium Trust missing-account search (c. 2015): https://www.plansponsor.com/participants-can-search-for-missing-accounts-online/
- FreeERISA help: https://freeerisa.benefitspro.com/help/
