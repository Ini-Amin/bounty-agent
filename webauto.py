#!/usr/bin/env python3
"""
webauto.py — quick automated web scan layer (nuclei + dalfox) for bug bounty.

Automated tier on top of the manual suite: nuclei templates at low rate
(-c 5, -silent), dalfox XSS scan if installed. Targets: single or a file
with one URL per line. Output goes to stdout.

Usage:
  python webauto.py --target https://target.com
  python webauto.py --targets live.txt --c 8
  python webauto.py --target T --skip-dalfox
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DALFOX_INSTALL_HINT = "go install github.com/hahwul/dalfox/v4@latest"


def run(cmd, timeout):
    print(f"$ {' '.join(cmd)}", flush=True)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[webauto] timeout after {timeout}s", flush=True)
        return 1
    except Exception as e:
        print(f"[webauto] error: {e}", flush=True)
        return 1
    sys.stdout.write(p.stdout or "")
    if p.stderr:
        sys.stderr.write(p.stderr)
    print(f"[webauto] rc={p.returncode}", flush=True)
    return p.returncode


def normalize(targets):
    out = []
    for t in targets:
        t = t.strip()
        if not t:
            continue
        if not t.startswith(("http://", "https://")):
            t = "https://" + t
        out.append(t)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Quick automated web scan (nuclei + dalfox)")
    ap.add_argument("--target", action="append", help="target URL (repeatable)")
    ap.add_argument("--targets", help="file with one target per line")
    ap.add_argument("--c", type=int, default=5, help="nuclei concurrency (default 5)")
    ap.add_argument("--skip-dalfox", action="store_true", help="skip dalfox XSS scan")
    ap.add_argument("--timeout", type=int, default=600, help="per-tool timeout seconds (default 600)")
    a = ap.parse_args()

    targets = normalize(list(a.target or []))
    if a.targets:
        targets += normalize(Path(a.targets).read_text(encoding="utf-8").splitlines())
    if not targets:
        print("ERR: no targets — use --target or --targets")
        return 2
    if not shutil.which("nuclei"):
        print("ERR: nuclei not found — install via tools.json or bootstrap.py")
        return 2

    cmd = ["nuclei", "-silent", "-c", str(a.c)]
    for t in targets:
        cmd += ["-u", t]
    rc = run(cmd, a.timeout)

    if not a.skip_dalfox:
        if shutil.which("dalfox"):
            for t in targets:
                run(["dalfox", t], a.timeout)
        else:
            print(f"[webauto] dalfox not installed — skip (install: {DALFOX_INSTALL_HINT})")

    print(f"[webauto] done — nuclei rc={rc}")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
