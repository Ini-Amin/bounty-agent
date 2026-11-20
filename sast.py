#!/usr/bin/env python3
"""
sast.py — static analysis runner (semgrep).

SAST layer for bug-bounty code review: find bugs in source trees before hunting.

Usage:
  python sast.py --path .                      # p/security-audit (broad)
  python sast.py --path ./src --config p/jwt   # language-specific rules

Install: pip3 install semgrep
"""
import argparse
import shutil
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="semgrep static analysis runner")
    ap.add_argument("--path", default=".", help="path to scan (default .)")
    ap.add_argument("--config", default="p/security-audit", help="semgrep config set")
    a = ap.parse_args()

    if not shutil.which("semgrep"):
        print("ERR: semgrep not found — pip install semgrep")
        return 2

    cmd = ["semgrep", f"--config={a.config}", a.path]
    print(f"$ {' '.join(cmd)}", flush=True)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        print("[sast] timeout")
        return 1
    sys.stdout.write(p.stdout or "")
    if p.stderr:
        sys.stderr.write(p.stderr)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
