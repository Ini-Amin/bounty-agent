#!/usr/bin/env python3
"""
param_discover.py — hidden parameter discovery (arjun preferred, paramspider fallback).

Auth-bypass / mass-assignment hunting needs hidden params — run on live URLs.

Usage:
  python param_discover.py --url https://target.com
  python param_discover.py --url https://target.com --threads 30

Install (one of):
  pip install arjun
  pip install paramspider
"""
import argparse
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


def run(cmd, timeout):
    print(f"$ {' '.join(cmd)}", flush=True)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("[param_discover] timeout", flush=True)
        return 1
    except Exception as e:
        print(f"[param_discover] error: {e}", flush=True)
        return 1
    sys.stdout.write(p.stdout or "")
    if p.stderr:
        sys.stderr.write(p.stderr)
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Hidden parameter discovery (arjun preferred, paramspider fallback)")
    ap.add_argument("--url", required=True, help="target URL (or domain)")
    ap.add_argument("--threads", type=int, default=40, help="arjun threads (default 40)")
    ap.add_argument("--timeout", type=int, default=600, help="timeout seconds (default 600)")
    a = ap.parse_args()

    url = a.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if shutil.which("arjun"):
        return run(["arjun", "-u", url, "-t", str(a.threads)], a.timeout)
    if shutil.which("paramspider"):
        host = urlsplit(url).hostname or ""
        if not host:
            print("ERR: cannot extract host from URL")
            return 2
        return run(["paramspider", "-d", host], a.timeout)
    print("ERR: neither arjun nor paramspider installed — pip install arjun")
    return 2


if __name__ == "__main__":
    sys.exit(main())
