#!/bin/sh
# Launcher for fw_guard.py: finds a Python 3 on Windows (Git Bash), macOS and Linux.
# No Python on the pretool path blocks the call (exit 2); on the prompt path it lets the message through.
d=$(dirname "$0")
for p in python3 python py; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" </dev/null >/dev/null 2>&1; then
    exec "$p" "$d/fw_guard.py" "$@"
  fi
done
if [ "$1" = "prompt" ]; then exit 0; fi
echo "finwright guard: no Python 3 found, blocking the call" >&2
exit 2
