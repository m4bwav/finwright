# Changelog: finwright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261013-5 · 2026-10-13 · Form 5500 search through the EFAST2 JSON API
- because: L-006
- files: references/old-401ks.md (The search, step 3)
- Step 3 now gives the JSON API route an agent can use when the search page refuses a fetch, the filing PDF location, and the PEO participating-employer check.

### C-20261013-4 · 2026-10-13 · Repository public; CI and security settings on
- because: user request (make the repository public)
- files: none in the skill (repository settings only)
- The repository is now public, so the CI jobs (tests, size budget, leak gate) run on every push. Secret scanning, push protection, private vulnerability reporting, Dependabot alerts, approval for fork pull request workflows and branch protection on master (the leak-gate and budget checks must pass; no force push, no deletion) are on.

### C-20261013-3 · 2026-10-13 · Public release: written for any user, private overlay, leak gate
- because: user request (publish the plugin for any user)
- files: SKILL.md (Step 0, Hard rules, Other jobs, Maintenance), every reference, LEARNINGS.md, RESEARCH.md, evals/evals.json, research/ (new, from the first research pass), tools/leak_scan.py (new), .githooks/ (new), .github/workflows/ci.yml (new), README.md, AGENTS.md, SECURITY.md, LICENSE
- The skill and references now speak of "the user". Step 0 reads an optional private overlay (`$FINWRIGHT_OVERLAY`, else `~/.finwright/OVERLAY.md`) for the user's own decisions and lessons, which win over the defaults and never enter the plugin. Lessons were rewritten with neutral evidence. The research reports moved into `research/` with personal notes removed. A leak scanner runs as a pre-commit hook and in CI against a deny-list kept outside the repository. An f-string that only Python 3.12+ parsed was fixed (L-005). Licence MIT. Version 0.5.0.

### C-20261013-2 · 2026-10-13 · Savings bond account totals count in net worth
- because: L-003
- files: scripts/fw.py (compute_networth), tests
- A `savings_bond` account's balance (a TreasuryDirect or aggregator total) now counts until bonds are listed one by one with `bond add`; from then on the Treasury value files replace it and a warning says the balance is ignored, so nothing is counted twice. Before, the balance was silently dropped.

### C-20261013-1 · 2026-10-13 · Bank of America activity CSV import
- because: user request (import Bank of America activity CSVs), L-001
- files: scripts/fw.py (import bofa, bofa_read, bofa_payee; --last4 accepts letters; hunt add prints the given next step), SKILL.md (Other jobs), references/data-routes.md (Bank of America section), tests
- Added `fw.py import bofa FILE ACCOUNT [--monthly] [--dry-run]` for the bank's activity CSV. It checks begin + credits + debits = ending and every running balance, records the ending balance (and each month's last running balance with --monthly, the ending balance standing for its own month), skips duplicates, refuses liability accounts, and prints payees grouped with IDs and confirmation numbers dropped plus the linked accounts (CRD, BRK, ACCT#) marked tracked or not. `--last4` now takes four letters or digits because some banks show linked brokerage numbers with letters (for example `BRK 9Z99`).

### C-20261012-3 · 2026-10-12 · Old 401(k) hunt, Monarch import, Bank of America routes
- because: user request (old 401(k) search, bank CSV routes, Monarch learnings), research reports 2026-10-12 finding-old-401ks, monarch-skill-learnings, monarch-web-survey
- files: scripts/fw.py (hunt, monarch map, import monarch), SKILL.md (description, Other jobs, References), references/old-401ks.md (new), references/monarch.md (new), references/data-routes.md (Bank of America section), references/safeguards.md (Monarch), references/landscape.md (Monarch rows), tests
- Added `fw.py hunt` to track one search per former employer with status, plan, EIN, recordkeeper, next step and dated notes, and a guide built on the free DOL, SSA and IRS sweeps. Added `fw.py monarch map` and `fw.py import monarch` for Monarch's balances CSV: name map, newest row per account, liabilities negated rather than passed through abs() so a card in credit is kept and flagged, unmapped accounts listed, duplicates skipped, dry run. Recorded that Bank of America has no API or MCP and ended OFX on 2025-09-30, and that Monarch's official connector is paused and grants write with read. Guard tests now cover Monarch server-name variants and the official PascalCase tool names.

### C-20261012-2 · 2026-10-12 · Consequential-action guard and safeguards reference
- because: user request ("make sure that its studied the latest in safe guards so that a transaction or other consequential action isn't made without the user's explicit permission"), R-20261012-6
- files: hooks/hooks.json, hooks/fw_guard.py, hooks/fw_guard.sh, tests/test_fw_guard.py, SKILL.md (Hard rules, References), references/safeguards.md (new), references/rules.md (rule 3), evals/evals.json (outcome-3)
- Added a PreToolUse and UserPromptSubmit guard that runs in every session. It denies trades, transfers, payments, writes on money servers, browser actions on financial sites and shell writes to broker APIs. Only the user's typed one-time code releases the exact call once, and then the native dialog still asks. The guard refuses outright in bypass or dontAsk mode. The settings-level deny, ask and hard_deny block is proposed in safeguards.md and not applied, because a plugin cannot ship it and it is the user's configuration. The research draft was hardened: the prompt path fails open so a crash cannot block every message, `check` is no longer a read verb (check_deposit), money servers are matched by name token instead of substring, shell POSTs to broker APIs are covered, and the hook uses the sh-launcher form because the Claude Code it was built on was 2.1.281.

### C-20261012-1 · 2026-10-12 · Created as an evergreen unit
- because: user request
- files: SKILL.md, RESEARCH.md, LEARNINGS.md, evergreen.json (skills: also TESTS.md and evals/evals.json)
- Initial version. Tier `moderate`, interval 30d. See R-20261012-1 for the research basis; the first test run, for a skill, is logged in TESTS.md.
