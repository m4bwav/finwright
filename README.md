# finwright

![An open ledger, a desk calculator and a closed brass padlock beside a stack of paper statements under a green desk lamp](https://raw.githubusercontent.com/m4bwav/finwright/master/.github/images/banner.jpg)

Your own net worth records and checks, kept on your machine, with an AI agent doing the clerical work and a script doing every calculation. A plugin for Claude Code (and any agent that reads skills), with one skill, a standard-library Python CLI and a guard hook.

- **What it tracks:** bank and card balances, 401(k)s and IRAs, brokerage holdings, savings bonds, the home, and loans.
- **Savings bonds:** I and EE bonds are valued from Treasury's own published value files, with no login.
- **Reports:**
  - total, liquid, investable and after-tax net worth
  - snapshot history
  - allocation drift against targets
  - 401(k) fund fees
  - money-weighted returns
  - contribution limits
  - Federal Reserve SCF benchmarks
- **Old 401(k)s:** a tracked search per former employer, built on the free DOL, SSA and IRS routes.
- **Accounts in your email:** scan exported mail (Gmail Takeout, Thunderbird, any mbox or .eml, or a mail connector's results) for statements, transfer letters, tax forms and plan notices, and see which institution holds what and for which job. Keeps no message bodies; never asks for an email password.
- **What it never does:** log in to a bank, store a password or move money. It does recommend: after the numbers it says what it would do in your place and why, and you decide, at your own risk ([Use at your own risk](#use-at-your-own-risk)).
- **Guard:** a hook runs in every Claude Code session while the plugin is installed. It blocks trades, transfers, payments, changes on money-holding services, browser actions on bank and broker sites, and shell writes to broker APIs. Each blocked call shows a one-time code, and only you typing `CONFIRM <code>` lets that exact call through once, still behind the normal permission dialog. See [skills/finwright/references/safeguards.md](skills/finwright/references/safeguards.md).

## Use at your own risk

finwright is provided as is, with no warranty of any kind (see the [licence](LICENSE)). Its author and contributors make no promise that any figure, calculation, recommendation or reference in it is correct, complete or current, and accept no liability for any loss arising from its use. That includes losses that are total and cannot be undone, such as:

- an investment that falls to zero, or a company that fails;
- a trade, transfer or payment the user makes, which cannot be reversed;
- a deadline, limit, tax rule or rate that has changed since the tool was written;
- an error in an import, a calculation or a model's reading of the results.

The recommendations come from published research and the user's own records. They are general, not a licensed adviser's advice for anyone's situation, and they can be wrong. Investments can lose some or all of their value, and new listings and single stocks most of all. Decide for yourself, never invest money you cannot afford to lose, and ask a licensed professional before any decision you could not undo.

## Install

In Claude Code:

```
/plugin marketplace add m4bwav/finwright
/plugin install finwright@finwright
```

Restart the session so the guard hook loads. Python 3.10 or newer must be on the PATH (`python`, `python3` or `py`).

## Quick start

```
python skills/finwright/scripts/fw.py init                      # creates ~/finwright-data (outside any repo)
python skills/finwright/scripts/fw.py account add checking --type cash --institution "My Bank" --last4 1234
python skills/finwright/scripts/fw.py balance set checking 4250.10 --as-of 2026-10-12 --source statement
python skills/finwright/scripts/fw.py bond add --series I --issue 2022-01 --denomination 1000
python skills/finwright/scripts/fw.py bond refresh
python skills/finwright/scripts/fw.py networth --save
python skills/finwright/scripts/fw.py history
```

Or ask the agent: "do my net worth check". The skill walks through each account, tells you what to download, and runs the script.

## Where your data lives

`$FINWRIGHT_DATA` or `~/finwright-data`: plain CSV and JSON you can open in a spreadsheet. fw.py refuses to create it inside a git repository. Keep disk encryption on, and never put the folder in a repository or a synced folder without encrypting it first (age or SOPS).

Your own standing decisions and lessons can live in a private overlay, `~/.finwright/OVERLAY.md` (or the file named by `$FINWRIGHT_OVERLAY`). The skill reads it first and never copies it into the plugin.

## Layout

- `skills/finwright/`: the skill (SKILL.md, references, `data/rates.json`, `scripts/fw.py`, its importers `scripts/fw_import.py` and the mail sweep `scripts/fw_mail.py`, evergreen companions).
- `hooks/`: the consequential-action guard.
- `research/`: the research reports the skill was built from (2026-10-12), every claim with a source.
- `tests/`: unit tests for fw.py and the guard (`python tests/test_fw.py`, `python tests/test_fw_guard.py`). Invented numbers only.
- `tools/leak_scan.py`: the maintainer's leak gate (pre-commit hook and CI), see [AGENTS.md](AGENTS.md).

## Contributing and security

Issues and pull requests are welcome. Changes to `hooks/` or to fw.py's network calls get a closer review, because other people rely on the guard. See [SECURITY.md](SECURITY.md) for reporting a problem.

## Licence

[MIT](LICENSE).
