#!/usr/bin/env python3
"""Leak gate: stop a maintainer's private details from reaching this public repository.

The patterns that matter (names of the maintainer's banks, employers, plans, paths) are not in this
file or anywhere in this repository: publishing the list would publish the facts. They come from a
deny-list kept outside the repository, plus, on the maintainer's machine, the values in their own
finwright data folder. This file only holds generic rules (home-folder paths, email addresses).

Modes (PATH defaults to the current directory):
  leak_scan.py tree [PATH]        every file in the working tree, file names included (skips .git)
  leak_scan.py history [PATH]     every commit on every ref: added lines, file names, messages, identities
  leak_scan.py staged [PATH]      the staged files and the commit identity (the pre-commit hook)
  leak_scan.py message FILE       a commit message (the commit-msg hook)

Options:
  --denylist FILE   the deny-list; default $FINWRIGHT_LEAK_DENYLIST, else `git config finwright.denylist`
  --optional        run the generic rules alone when no deny-list is found (a fork's pull request in CI)
  --data DIR        a finwright data folder whose values are also denied (default $FINWRIGHT_DATA, else
                    ~/finwright-data when it exists); --no-data skips it
  --show            print the matched text too (local use only; CI logs are public)
  --strict-identity history: every author and committer email must be a GitHub no-reply address
                    (the maintainer's check before publishing; outside contributors' commits fail it)

Deny-list format, one entry per line, `#` starts a comment:
  REGEX             denied, case-insensitive
  case: REGEX       denied, case-sensitive
  allow: REGEX      text it matches is blanked before the deny checks (for example an author credit)
  allow-data: TEXT  a data-folder value too common to deny (a common word or a large institution's name)

Exit 0 clean, 1 with findings, 2 when the setup is wrong (no deny-list, unreadable file).
Standard library only; Python 3.8 or newer.
"""
import argparse
import csv
import os
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

GENERIC = [
    ("home-folder path (Windows)", re.compile(
        r"\b[A-Za-z]:[\\/]{1,2}Users[\\/]{1,2}(?!<|%|\$|NAME\b|USERNAME\b|you\b|Public\b|Default\b)[\w.-]+",
        re.I)),
    ("home-folder path (macOS or Linux)", re.compile(
        r"(?<![\w.])/(?:Users|home)/(?!<|\$|NAME\b|USERNAME\b|you\b|user\b|runner\b|Shared\b)[a-z][\w.-]*",
        re.I)),
    ("email address", re.compile(
        r"(?<![\w.+-])[\w.+-]+@(?!users\.noreply\.github\.com\b|noreply\.github\.com\b|github\.com\b|"
        r"example\.(?:com|org|net)\b)[\w-]+(?:\.[\w-]+)*\.(?!gov\b|mil\b)[a-z]{2,}\b", re.I)),  # public-agency addresses are not personal
]
NOREPLY = re.compile(r"@users\.noreply\.github\.com$|^noreply@github\.com$", re.I)
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}


class Rules:
    def __init__(self):
        self.deny = []       # (label, compiled)
        self.allow = []      # compiled
        self.allow_data = set()

    def load_denylist(self, path):
        for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            label = f"deny-list line {n}"
            try:
                if line.startswith("allow-data:"):
                    self.allow_data.add(line[11:].strip().lower())
                elif line.startswith("allow:"):
                    self.allow.append(re.compile(line[6:].strip(), re.I))
                elif line.startswith("case:"):
                    self.deny.append((label, re.compile(line[5:].strip())))
                else:
                    self.deny.append((label, re.compile(line, re.I)))
            except re.error as e:
                raise SystemExit(f"leak_scan: {path} line {n} is not a valid regex: {e}")

    def load_data(self, folder):
        """Deny the values in a finwright data folder: last4s, amounts, names (not free-text notes). Never printed."""
        d = Path(folder)

        def rows(name):
            p = d / name
            if not p.exists():
                return []
            with p.open(encoding="utf-8", newline="") as h:
                return list(csv.DictReader(h))

        words, last4s, amounts = set(), set(), set()
        for r in rows("accounts.csv"):
            words.update([r.get("name", ""), r.get("institution", "")])
            if r.get("last4"):
                last4s.add(r["last4"].strip())
        for r in rows("hunt.csv"):
            words.update(r.get(k, "") for k in ("employer", "plan", "ein", "recordkeeper"))
        for r in rows("monarch-map.csv"):
            words.add(r.get("monarch", ""))
        for name in ("balances.csv", "holdings.csv", "flows.csv"):
            for r in rows(name):
                for k in ("value", "amount"):
                    try:
                        v = abs(Decimal(r.get(k) or "x"))
                    except InvalidOperation:
                        continue
                    if v >= 100:
                        amounts.add(v)
        for w in words:
            for part in re.split(r"[;|]", w or ""):
                part = part.strip()
                if len(part) >= 5 and part.lower() not in self.allow_data and re.search(r"[A-Za-z]", part):
                    self.deny.append(("data folder: a name", re.compile(r"(?<!\w)" + re.escape(part) + r"(?!\w)", re.I)))
        for l4 in last4s:
            if re.fullmatch(r"\w{4}", l4) and not re.fullmatch(r"(19|20)\d\d", l4):
                self.deny.append(("data folder: a last4", re.compile(r"(?<![\w,])(?<!\d\.)" + re.escape(l4) + r"(?![\w,]|\.\d)", re.I)))
        for v in amounts:
            q = v.quantize(Decimal("0.01"))
            forms = {f"{q}", f"{q:,}"}
            if q == q.to_integral_value():
                forms.add(f"{int(q):,}")
            for f in forms:
                self.deny.append(("data folder: an amount", re.compile(r"(?<![\d.,])" + re.escape(f) + r"(?![\d]|[.,]\d)")))

    def check(self, text):
        """Yield (label, matched text) for every finding in one line."""
        for a in self.allow:
            text = a.sub(lambda m: " " * len(m.group(0)), text)
        for label, rx in GENERIC + self.deny:
            for m in rx.finditer(text):
                yield label, m.group(0)


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if r.returncode:
        raise SystemExit(f"leak_scan: git {' '.join(args)} failed: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "replace")


def is_binary(data):
    return b"\0" in data[:8192]


def scan_text(rules, where, text, out):
    for n, line in enumerate(text.splitlines(), 1):
        for label, hit in rules.check(line):
            out.append((f"{where}:{n}", label, hit))


def mode_tree(rules, root, out):
    for dp, dns, fns in os.walk(root):
        dns[:] = [x for x in dns if x not in SKIP_DIRS]
        for f in fns:
            p = Path(dp) / f
            rel = p.relative_to(root).as_posix()
            for label, hit in rules.check(rel):
                out.append((f"{rel} (file name)", label, hit))
            try:
                data = p.read_bytes()
            except OSError as e:
                raise SystemExit(f"leak_scan: cannot read {rel}: {e}")
            if not is_binary(data):
                scan_text(rules, rel, data.decode("utf-8", "replace"), out)


def mode_history(rules, root, out, strict_identity=False):
    log = git(root, "log", "--all", "--format=%x01%h%x02%an%x02%ae%x02%cn%x02%ce%x02%B%x03")
    for rec in log.split("\x01")[1:]:
        h, an, ae, cn, ce, rest = rec.split("\x02", 5)
        body = rest.split("\x03", 1)[0]
        for who, email in (("author", ae), ("committer", ce)):
            if strict_identity and not NOREPLY.search(email.strip()):
                out.append((f"commit {h}", f"{who} email is not a GitHub no-reply address", email))
        for label, hit in rules.check(f"{an} {ae} {cn} {ce}"):
            out.append((f"commit {h} (names)", label, hit))
        scan_text(rules, f"commit {h} (message)", body, out)
    current, commit = "?", "?"
    for line in git(root, "log", "--all", "-p", "--no-color", "--no-ext-diff", "--format=commit %h").splitlines():
        if line.startswith("commit "):
            commit = line[7:]
        elif line.startswith("diff --git "):
            current = line.split(" b/", 1)[-1]
            for label, hit in rules.check(current):
                out.append((f"commit {commit} {current} (file name)", label, hit))
        elif line.startswith("+") and not line.startswith("+++"):
            for label, hit in rules.check(line[1:]):
                out.append((f"commit {commit} {current}", label, hit))


def mode_staged(rules, root, out):
    email = git(root, "config", "user.email").strip()
    if not NOREPLY.search(email):
        out.append(("git config user.email", "commit identity is not a GitHub no-reply address", email))
    names = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0")
    for rel in filter(None, names):
        for label, hit in rules.check(rel):
            out.append((f"{rel} (file name)", label, hit))
        r = subprocess.run(["git", "-C", str(root), "show", f":{rel}"], capture_output=True)
        if r.returncode == 0 and not is_binary(r.stdout):
            scan_text(rules, rel, r.stdout.decode("utf-8", "replace"), out)


def find_denylist(arg, root):
    if arg:
        return arg
    if os.environ.get("FINWRIGHT_LEAK_DENYLIST"):
        return os.environ["FINWRIGHT_LEAK_DENYLIST"]
    r = subprocess.run(["git", "-C", str(root), "config", "finwright.denylist"], capture_output=True)
    return r.stdout.decode("utf-8", "replace").strip() or None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Leak gate for the public finwright repository.")
    ap.add_argument("mode", choices=["tree", "history", "staged", "message"])
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--denylist")
    ap.add_argument("--optional", action="store_true")
    ap.add_argument("--data")
    ap.add_argument("--no-data", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--strict-identity", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")

    root = Path(a.path).resolve()
    repo = Path.cwd() if a.mode == "message" else root  # git runs commit-msg at the top of the work tree
    rules = Rules()
    dl = find_denylist(a.denylist, repo)
    if dl and Path(dl).is_file():
        rules.load_denylist(dl)
        source = "deny-list"
    elif a.optional:
        source = "generic rules only (no deny-list)"
    else:
        print("leak_scan: no deny-list found. Set FINWRIGHT_LEAK_DENYLIST or "
              "`git config finwright.denylist <path>`; the list lives outside this repository.")
        return 2
    data = None if a.no_data else (a.data or os.environ.get("FINWRIGHT_DATA") or str(Path.home() / "finwright-data"))
    if data and Path(data).is_dir():
        rules.load_data(data)
        source += " + data folder"

    out = []
    if a.mode == "tree":
        mode_tree(rules, root, out)
    elif a.mode == "history":
        mode_history(rules, root, out, a.strict_identity)
    elif a.mode == "staged":
        mode_staged(rules, root, out)
    else:
        scan_text(rules, "commit message", root.read_text(encoding="utf-8", errors="replace"), out)

    if out:
        print(f"leak_scan {a.mode}: {len(out)} finding(s) ({source}); nothing may be committed or pushed until they are gone:")
        for where, label, hit in out:
            print(f"  {where}: {label}" + (f": {hit!r}" if a.show else ""))
        return 1
    print(f"leak_scan {a.mode}: clean ({source})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
