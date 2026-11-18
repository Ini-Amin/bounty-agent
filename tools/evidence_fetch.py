#!/usr/bin/env python3
"""Fetch one in-scope URL as redacted evidence. No redirects, no cookies, no auth."""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hardening import (  # noqa: E402
    Scope, ToolError, redact_headers, redact_text, sha256_text, utcnow, write_json,
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ToolError(f"redirect blocked: {code} -> {newurl}")

    def http_error_302(self, req, fp, code, msg, headers):
        raise ToolError("redirect blocked (302)")


def fetch(url: str, timeout: int = 15, max_bytes: int = 1_000_000) -> dict:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "BOUNTY-evidence/1.0", "Accept": "text/html,application/json,text/plain"},
    )
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        status = resp.status
        headers = dict(resp.headers.items())
        raw = resp.read(max_bytes + 1)
    truncated = len(raw) > max_bytes
    if truncated:
        raw = raw[:max_bytes]
    body = raw.decode("utf-8", "ignore")
    return {
        "at": utcnow(),
        "url": url,
        "status": status,
        "headers": redact_headers(headers),
        "body": redact_text(body),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "truncated": truncated,
        "body_sha256": sha256_text(body),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Redacted evidence fetcher")
    ap.add_argument("--scope", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", default="reports/evidence")
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--max-bytes", type=int, default=1_000_000)
    ap.add_argument("--allow-private", action="store_true")
    a = ap.parse_args()
    try:
        scope = Scope.load(a.scope, allow_private=a.allow_private)
        checked = scope.check(a.url)
        result = fetch(checked["url"], timeout=a.timeout, max_bytes=a.max_bytes)
        result["program"] = scope.program
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha256(checked["url"].encode()).hexdigest()[:16]
        path = write_json(out / f"evidence_{name}.json", result)
        (out / f"evidence_{name}.txt").write_text(result["body"], encoding="utf-8")
        print(f"evidence: {path} sha256={result['raw_sha256'][:16]}")
        return 0
    except (ToolError, OSError, ValueError, urllib.error.URLError) as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
