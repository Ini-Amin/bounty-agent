#!/usr/bin/env python3
"""Build a local bug-bounty report draft from findings JSON.

No submission. No network. CVSS vector is only a string; no score invented.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hardening import Scope, ToolError, redact_text, utcnow  # noqa: E402


def render(finding: dict, program: str) -> str:
    def value(key: str, default: str = "-") -> str:
        return redact_text(str(finding.get(key, default) or default))

    steps = finding.get("steps", [])
    if isinstance(steps, str):
        steps = [steps]
    evidence = finding.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [evidence]

    lines = [
        f"# {value('title', 'Untitled finding')}",
        "",
        f"- Program: {program}",
        f"- Target: {value('target')}",
        f"- Severity: {value('severity', 'unrated')}",
        f"- CVSS vector: {value('cvss_vector', 'not provided')}",
        f"- CWE: {value('cwe', 'not provided')}",
        "",
        "## Summary",
        "",
        value("summary", "No summary provided."),
        "",
        "## Impact",
        "",
        value("impact", "Impact not stated."),
        "",
        "## Steps to reproduce",
        "",
    ]
    if steps:
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {redact_text(str(step))}")
    else:
        lines.append("1. Steps not provided.")
    lines += ["", "## Evidence", ""]
    if evidence:
        for item in evidence:
            lines.append(f"- `{redact_text(str(item))}`")
    else:
        lines.append("- No evidence path provided.")
    lines += [
        "",
        "## Remediation",
        "",
        value("remediation", "Not provided."),
        "",
        "## Gate",
        "",
        "- [ ] Scope verified",
        "- [ ] Impact reproduced",
        "- [ ] Evidence redacted",
        "- [ ] Human approval before submission",
        "",
        f"_Generated locally at {utcnow()}. Draft only; do not submit without review._",
        "",
    ]
    return "\n".join(lines)


def _validate_finding(finding: dict) -> None:
    """Anti-slop: reject findings missing required fields before writing."""
    missing = []
    for key in ("title", "target", "severity"):
        val = str(finding.get(key) or "").strip()
        if not val:
            missing.append(key)
    ev = finding.get("evidence") or []
    if not isinstance(ev, (list, tuple)):
        ev = [ev]
    if not any(str(e).strip() for e in ev):
        missing.append("evidence")
    if missing:
        raise ToolError(f"finding missing required field(s): {', '.join(missing)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Bug-bounty draft report builder")
    ap.add_argument("--findings", required=True, help="JSON array or object with findings[]")
    ap.add_argument("--scope", help="optional JSON scope file; validates finding targets")
    ap.add_argument("--out", default="reports/report.md")
    ap.add_argument("--allow-private", action="store_true")
    a = ap.parse_args()
    try:
        data = json.loads(Path(a.findings).read_text(encoding="utf-8"))
        findings = data.get("findings", []) if isinstance(data, dict) else data
        if not isinstance(findings, list) or not findings:
            raise ToolError("findings must be a non-empty array")
        scope = Scope.load(a.scope, allow_private=a.allow_private) if a.scope else None
        program = scope.program if scope else "unspecified"
        blocks = []
        for finding in findings:
            if not isinstance(finding, dict):
                raise ToolError("each finding must be an object")
            _validate_finding(finding)
            if scope:
                scope.check(str(finding.get("target", "")))
            blocks.append(render(finding, program))
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n\n---\n\n".join(blocks), encoding="utf-8")
        print(f"report: {out} findings={len(findings)}")
        return 0
    except (ToolError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
