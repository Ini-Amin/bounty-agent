#!/usr/bin/env python3
"""Run allowlisted recon binaries against scope-validated targets only.

No shell. No credential capture. No destructive flags. Nuclei is opt-in.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hardening import (  # noqa: E402
    Scope, ToolError, redact_text, run_allowlisted, utcnow, write_json, write_jsonl,
)

ALLOWED = {"subfinder", "httpx", "katana", "nuclei"}
DEFAULT_TOOLS = ["subfinder", "httpx", "katana"]


def build_command(tool: str, host: str, url: str) -> list[str]:
    if tool == "subfinder":
        return ["subfinder", "-d", host, "-silent"]
    if tool == "httpx":
        return ["httpx", "-u", url, "-silent", "-status-code", "-title", "-tech-detect"]
    if tool == "katana":
        return ["katana", "-u", url, "-silent", "-depth", "2"]
    if tool == "nuclei":
        return ["nuclei", "-u", url, "-silent", "-severity", "critical,high", "-rate-limit", "10"]
    raise ToolError(f"unknown tool: {tool}")


def load_targets(args) -> list[str]:
    targets: list[str] = []
    if args.target:
        targets.extend(args.target)
    if args.targets:
        targets.extend(
            line.strip()
            for line in Path(args.targets).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not targets:
        raise ToolError("no targets; use --target or --targets")
    return list(dict.fromkeys(targets))


def main() -> int:
    ap = argparse.ArgumentParser(description="Scope-gated recon runner")
    ap.add_argument("--scope", required=True, help="JSON scope file")
    ap.add_argument("--target", action="append", help="target host or URL (repeatable)")
    ap.add_argument("--targets", help="file with one target per line")
    ap.add_argument("--out", default="reports/recon", help="output directory")
    ap.add_argument("--tools", default=",".join(DEFAULT_TOOLS), help="comma-separated allowlisted tools")
    ap.add_argument("--active", action="store_true", help="include nuclei (active, rate-limited)")
    ap.add_argument("--dry-run", action="store_true", help="print commands only")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--allow-private", action="store_true", help="override private-IP block for lab use")
    a = ap.parse_args()

    try:
        scope = Scope.load(a.scope, allow_private=a.allow_private)
        targets = load_targets(a)
        tools = [x.strip() for x in a.tools.split(",") if x.strip()]
        if a.active and "nuclei" not in tools:
            tools.append("nuclei")
        unknown = sorted(set(tools) - ALLOWED)
        if unknown:
            raise ToolError(f"tools not allowlisted: {', '.join(unknown)}")

        validated = []
        for target in targets:
            validated.append(scope.check(target))

        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        rows: list[dict] = []
        missing: list[str] = []

        for item in validated:
            for tool in tools:
                cmd = build_command(tool, item["host"], item["url"])
                row = {
                    "at": utcnow(),
                    "program": scope.program,
                    "target": item["url"],
                    "host": item["host"],
                    "tool": tool,
                    "command": " ".join(redact_text(part) for part in cmd),
                    "dry_run": a.dry_run,
                }
                if a.dry_run:
                    rows.append(row)
                    print(f"{tool}: {row['command']}")
                    continue
                if not shutil.which(tool):
                    row.update({"status": "missing", "error": f"{tool} not in PATH"})
                    rows.append(row)
                    missing.append(tool)
                    continue
                try:
                    result = run_allowlisted(tool, cmd[1:], ALLOWED, timeout=a.timeout)
                    lines = result["stdout"].splitlines()[:1000]
                    row.update({
                        "status": "ok" if result["returncode"] == 0 else "nonzero",
                        "returncode": result["returncode"],
                        "output": lines,
                        "stderr": result["stderr"].splitlines()[:100],
                        "truncated": result["truncated"],
                    })
                except ToolError as exc:
                    row.update({"status": "error", "error": str(exc)})
                rows.append(row)

        write_jsonl(out / "recon.jsonl", rows)
        write_json(out / "summary.json", {
            "at": utcnow(),
            "program": scope.program,
            "targets": [x["url"] for x in validated],
            "tools": tools,
            "dry_run": a.dry_run,
            "missing": sorted(set(missing)),
            "rows": len(rows),
        })
        print(f"recon: {len(rows)} rows -> {out}")
        return 0
    except (ToolError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
