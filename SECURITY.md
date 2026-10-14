# Security policy

## Reporting a problem

Open an issue or a pull request and I'll take a look. A pull request with the fix is the quickest route.

You can also report privately: open the repository's **Security** tab and choose **Report a vulnerability**.

This is a one-person project with no bug bounty and no response deadline. I'll reply when I can and say what I plan to do. Good-faith testing on your own copy is welcome.

## Supported versions

Only the latest release on the default branch gets fixes.

## Scope

The skill's instructions, `fw.py` and the guard hook run on your machine with your agent's permissions, next to your financial records. In scope:

- anything that leads the agent or fw.py to run commands, write files, fetch URLs or send data beyond what the skill says it does (fw.py's one network call is the public Treasury savings bond values API);
- instructions planted in a statement, CSV, web page or tool result the skill reads (prompt injection);
- any way past the guard hook: a trade, transfer, payment, write on a money-holding service or browser action on a financial site that runs without the user's typed one-time code, or a code the model can see, guess or forge;
- fw.py writing the data folder inside a git repository, or storing more than the last four characters of an account number.

Out of scope: bugs in the agent tool itself (Claude Code, Copilot, Codex, Cursor), in MCP servers or in the financial services themselves; report those to their makers.
