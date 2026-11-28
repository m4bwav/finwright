"""Run finwright's trigger and decoy cases headless, one fresh `claude -p` per run.

Evidence: a Skill tool_use whose input names finwright in the stream-json trace.
Every run points FINWRIGHT_DATA at an invented fixture folder and FINWRIGHT_OVERLAY at an invented
overlay, and runs in an empty cwd with no tools pre-allowed, so the skill reads neither the user's real
records nor their overlay. A run can still list the home folder; keep OUT_DIR and its traces local.
Usage: python tools/run_trigger_evals.py skills/finwright/evals/evals.json OUT_DIR [runs]
OUT_DIR/fixture-data must hold an invented data folder (`fw.py --data OUT_DIR/fixture-data init`, then accounts
and balances with made-up figures). OUT_DIR belongs outside every repository.
Set EVAL_PLUGIN_DIR to a finwright checkout to load it with --plugin-dir (needed when the installed plugin is
disabled or parked). A run whose session did not load finwright at all stops the script with exit 3, so a
missing plugin never reads as "the description did not trigger".
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

evals_path, out = Path(sys.argv[1]), Path(sys.argv[2])
runs = int(sys.argv[3]) if len(sys.argv) > 3 else 1
out.mkdir(parents=True, exist_ok=True)
cwd = out / "cwd"
cwd.mkdir(exist_ok=True)
claude = shutil.which("claude") or "claude"  # Windows CreateProcess cannot run the bare name of a .cmd shim
overlay = out / "fixture-overlay" / "OVERLAY.md"
if not overlay.exists():
    overlay.parent.mkdir(parents=True, exist_ok=True)
    overlay.write_text("# Overlay (invented, for evals)\n\n- Institutions: Example Bank, Example Recordkeeper.\n",
                       encoding="utf-8")
env = dict(os.environ, FINWRIGHT_DATA=str(out / "fixture-data"), FINWRIGHT_OVERLAY=str(overlay),
           FINWRIGHT_TODAY="2026-10-14")
extra = ["--plugin-dir", os.environ["EVAL_PLUGIN_DIR"]] if os.environ.get("EVAL_PLUGIN_DIR") else []
cases = [e for e in json.loads(evals_path.read_text(encoding="utf-8"))["evals"] if e["kind"] == "trigger"]
results = []
for c in cases:
    hits = 0
    for n in range(1, runs + 1):
        trace = out / f"{c['id']}-run{n}.jsonl"
        p = subprocess.run([claude, "-p", c["prompt"], "--output-format", "stream-json", "--verbose",
                            "--max-turns", "3", *extra], cwd=cwd, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        trace.write_text(p.stdout, encoding="utf-8")
        invoked, loaded = [], None
        for line in p.stdout.splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if isinstance(ev, dict) and ev.get("type") == "system" and ev.get("subtype") == "init":
                loaded = any("finwright" in str(x) for x in ev.get("skills") or [])
            msg = ev.get("message") if isinstance(ev, dict) else None
            for block in (msg.get("content") or [] if isinstance(msg, dict) else []):
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                    invoked.append(str(block.get("input", {}).get("skill", "")))
        if loaded is False:
            print(f"{c['id']} run {n}: finwright is not loaded in the session (disabled or parked?); "
                     "set EVAL_PLUGIN_DIR to the checkout. Trace: " + str(trace), file=sys.stderr)
            sys.exit(3)
        fired = any("finwright" in s for s in invoked)
        hits += fired
        print(f"{c['id']} run {n}: skills {invoked or 'none'} -> {'finwright' if fired else 'no finwright'}",
              flush=True)
    want = not c.get("decoy")
    passed = (hits == runs) if want else (hits == 0)
    results.append({"id": c["id"], "decoy": bool(c.get("decoy")), "hits": hits, "runs": runs, "passed": passed})
(out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
