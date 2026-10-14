# What counts and how each thing is valued

Read this when deciding an account's type, a value's source, or explaining a bond value or a return. Full sources: [method research](../../../research/2026-10-12-method-rules-and-security.md).

## Account types in fw.py

| fw.py type | What goes there | Value at | Lines it feeds |
|---|---|---|---|
| `cash` | checking, savings, money market, CDs | statement balance on the date (CDs include accrued interest) | total, liquid, investable |
| `taxable` | brokerage, vested RSU/ESPP shares | market value | total, liquid, investable |
| `tax_deferred` | traditional 401k, 403b, 457, TSP, traditional IRA | market value, vested part only | total, investable; after-tax uses `after_tax_rate` |
| `roth` | Roth 401k, Roth IRA | market value | total, investable |
| `hsa` | HSA cash and investments | market value | total, investable |
| `savings_bond` | I and EE bonds (use `fw.py bond add`, not balances) | Treasury value file for the month | total, liquid, investable |
| `real_estate` | home, land | Zillow or Redfin estimate (off-market error is about 7%) | total; after-tax subtracts `home_selling_cost_pct` |
| `vehicle` | cars, if the user chooses to count them | private-party value (KBB, Edmunds) | total |
| `other_asset` | anything else the user decides to count | stated method | total |
| `unvested` | unvested match, unvested RSUs | plan statement | shown apart, never in total |
| `mortgage` | mortgage, HELOC | payoff balance | total (not liquid) |
| `loan` | auto, student, personal | payoff balance | total, liquid |
| `credit_card` | cards | current balance including pending | total, liquid |
| `other_liability` | anything owed | payoff | total, liquid |

The SCF leaves pensions, Social Security and personal property out of net worth. finwright does too.

## Savings bonds

- Values come from Treasury's Savings Bonds Value Files (Fiscal Data API `v2/accounting/od/sb_value`, per $25 by issue year and month). They are published twice a year and on 2026-10-12 covered redemption months through 2026-11. fw.py multiplies by denomination/25. EE values are per $25 face, I values per $25 purchase.
- A value of 0 means the bond is inside its 12-month minimum hold. Before 5 years the last 3 months of interest are forfeited, and Treasury's values already subtract that.
- I bond composite rate = fixed + 2 x semiannual inflation + fixed x semiannual inflation. The fixed part lasts 30 years. The inflation part resets every six months on the bond's own issue anniversary. EE bonds pay a fixed rate and are guaranteed to double at 20 years.
- Interest is federally taxable when the bond is cashed and exempt from state tax.
- Never compound a bond value in the reply. If Treasury has no value for a month yet, say so.

## Bonds and TIPS at a broker

Net worth value = clean price / 100 x face + accrued interest. For TIPS, multiply the clean-price part by the index ratio and accrue interest on the adjusted principal. Many brokers list accrued interest apart from market value, so record the sum with `fw.py balance set`. Spot checks: FINRA TRACE (corporates), MSRB EMMA (munis).

## 401k specifics

- Use the vested balance from the plan statement. The unvested match goes in an `unvested` account.
- CIT funds have no ticker or public price. Take units and unit value from the recordkeeper and do not price them from a market API.
- Fees: the plan's 404a-5 participant fee disclosure lists each fund's expense ratio as a percentage and in dollars per $1,000. Record it with `holding set ... --expense-ratio`. Administrative fees appear in dollars on the quarterly statement.

## Returns

- `fw.py returns <account>` is a money-weighted return (XIRR): the user's own result, given when they put money in. It needs contributions recorded with `fw.py flow add`.
- The same command prints a time-weighted return: Modified Dietz in each period between two recorded balances, chain-linked. It removes the effect of when money went in, so it is the figure to set beside a fund or an index. More balance dates give a closer answer. Periods under a year are shown as a cumulative figure, not annualised (the GIPS convention).
- Fee drag: `fw.py fees --project` compounds today's holdings at an assumed growth rate (`--growth`, default 0.06) with and without each fund's expense ratio, and adds the plan's yearly admin fee (`--admin-fee`, dollars) compounded at the same rate. No new contributions are assumed, so it understates the cost for someone still saving. Report the growth rate as an assumption.
- Rebalancing: 5/25 bands (Swedroe). A class with a target of 20% or more is flagged when it drifts more than 5 points. A smaller class is flagged when it drifts more than 25% of its target.
