#!/bin/sh
# Launcher for fw_guard.py: finds a Python 3 on Windows (Git Bash), macOS and Linux.
# No Python on the pretool path blocks the call (exit 2); on the prompt path it lets the message through.
# One Python start per call: the Windows Store alias stubs (WindowsApps) are skipped, since a stub
# takes about 170 ms just to fail, and the version check runs inside the Python that runs the guard.
d=$(dirname "$0")
for p in python3 python py; do
  q=$(command -v "$p" 2>/dev/null) || continue
  case "$q" in *WindowsApps*) continue ;; esac
  exec "$q" -c "import sys, runpy
if sys.version_info < (3, 8):
    sys.stderr.write('finwright guard: Python 3.8+ needed\n')
    sys.exit(2 if sys.argv[2:3] == ['pretool'] else 0)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')" "$d/fw_guard.py" "$@"
done
if [ "$1" = "prompt" ]; then exit 0; fi
echo "finwright guard: no Python 3 found, blocking the call" >&2
exit 2
