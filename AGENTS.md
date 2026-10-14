# AGENTS.md

Rules for any AI agent (Claude Code, Copilot, Cursor, Codex, Gemini CLI) working in this repository. `CLAUDE.md` imports this file and `.github/copilot-instructions.md` points here.

## What this is

A public plugin with one skill, `skills/finwright/`. It keeps a person's own net worth records and runs their net worth check, on their machine.

- `SKILL.md` covers when to use it and in what order.
- `references/` holds the rules, valuation, data routes and the tools landscape.
- `data/rates.json` holds the time-sensitive limits, bond rates and benchmarks, each with its source and check date.
- `scripts/fw.py` is the single-file standard-library CLI that stores the records and does all the math.
- The evergreen companions are RESEARCH, CHANGELOG, LEARNINGS, TESTS, MAINTENANCE, `evergreen.json` and `evals/evals.json`.
- `hooks/` holds the consequential-action guard: `hooks.json`, `fw_guard.sh` and `fw_guard.py`. It runs on every MCP, Bash and PowerShell call and every user prompt, in every session, while the plugin is installed.
- `research/` holds the research reports the skill was built from.
- Unit tests are in `tests/` (`test_fw.py`, `test_fw_guard.py`, `test_leak_scan.py`).
- `tools/leak_scan.py` is the leak gate; `.githooks/` runs it before every commit.

## Rules

- **No personal data in this repository, ever.** Nobody's balances, account numbers, institution logins, statement text, employers, plan names, local paths or email addresses. A user's records live in their data folder (`$FINWRIGHT_DATA`, default `~/finwright-data`), outside every git repository; fw.py refuses to create it inside one. Their own decisions and lessons live in their private overlay (`~/.finwright/OVERLAY.md`). Tests, evals, LEARNINGS entries, commit messages and issues use invented figures and say "the user".
- **Leak gate.** The maintainer's clone runs `tools/leak_scan.py` as a pre-commit and commit-msg hook (`git config core.hooksPath .githooks`) against a deny-list kept outside this repository (`git config finwright.denylist <path>` or `$FINWRIGHT_LEAK_DENYLIST`), plus the values in their own data folder. CI runs it over the tree and the full history with the deny-list from the `LEAK_DENYLIST` secret. Never add the deny-list, or anything copied from it, to this repository. Never skip the hook (`--no-verify`). Commits use the GitHub no-reply address (`git config user.email`); the scanner refuses any other.
- **Outside pull requests are never auto-merged.** The maintainer reviews every change by hand, and any change to `hooks/`, to `.githooks/`, to `tools/leak_scan.py`, to `.github/workflows/`, or to a network call in fw.py needs the maintainer's explicit review and approval, whoever wrote it. Agents never approve or merge such a change on their own.
- **The safety rules in `skills/finwright/references/rules.md` are product requirements.**
  - The skill and the script never handle credentials and never automate a financial login.
  - They never move money, trade or contact an institution.
  - They never compute a reported number outside fw.py.
  - The guard hook denies any consequential action unless the user types its one-time code. Never weaken it, widen its read list, or add an allow path without the maintainer's explicit go-ahead.
- `fw.py` stays one standard-library Python file (3.10 or newer) that runs on Windows, macOS and Linux. It prints UTF-8 with LF line endings. Money is `Decimal`, never float. The only network call is the public Treasury savings bond values API. Any future connector reads a token from the OS keyring and is read-only.
- Every change to the script has a test in `tests/test_fw.py`. Every change to the guard has a test in `tests/test_fw_guard.py`. Run `python tests/test_fw.py` and `python tests/test_fw_guard.py` from the repository root before committing.
- Size budget: green while fw.py is under 1,200 lines and SKILL.md under 120; yellow up to 2,000 lines of fw.py (say so in the pull request); red above that, so split the connectors into their own module. CI prints the counts.
- Time-sensitive numbers live only in `data/rates.json`, with a source URL and checked date per entry. A new year's limits or a new bond period is a new entry, never an edit of an old one.
- The skill is an evergreen unit. Before editing it, read `skills/finwright/evergreen.json`. If `next_due` has passed or `contradiction` is set, say so and refresh after the task (`evergreen-refresh`, or `skills/finwright/MAINTENANCE.md`). Log every change in `skills/finwright/CHANGELOG.md` with its reason. Lessons go to `LEARNINGS.md` with a code name, neutral evidence and no real figures.
- A release bumps the version in `.claude-plugin/plugin.json`, `plugin.json`, `VERSION` in `fw.py`, `metadata.version` in SKILL.md and `version` in `evergreen.json` together. Hooks load at session start, so a new version needs a new session.
- No top-level `bin/` folder: Cowork refuses to install a plugin that has one.
- No AI attribution anywhere: no Co-Authored-By trailers and no "generated with" lines in commits, pull requests or files.
- Link documents with relative markdown links, never wikilinks.
