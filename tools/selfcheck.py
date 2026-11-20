#!/usr/bin/env python3
"""Local self-check for hardened tools. No network, no external binaries."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hardening import Scope, ToolError, redact_text, safe_run, sha256_text  # noqa: E402
from recon_run import build_command  # noqa: E402
from report_build import render  # noqa: E402


def expect_error(fn, label: str) -> None:
    try:
        fn()
    except (ToolError, ValueError):
        return
    raise AssertionError(f"expected rejection: {label}")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scope_path = root / "scope.json"
        scope_path.write_text(json.dumps({
            "program": "selfcheck",
            "in_scope": ["example.com", "*.example.com"],
            "out_of_scope": ["admin.example.com"],
            "allow_private": False,
        }), encoding="utf-8")
        scope = Scope.load(scope_path)

        ok = scope.check("https://example.com/path")
        assert ok["host"] == "example.com"
        assert scope.check("sub.example.com")["host"] == "sub.example.com"

        expect_error(lambda: scope.check("https://evil.test"), "out of scope")
        expect_error(lambda: scope.check("https://admin.example.com"), "explicit deny")
        expect_error(lambda: scope.check("http://169.254.169.254/"), "metadata IP")
        expect_error(lambda: scope.check("https://user:pass@example.com"), "credentials")
        expect_error(lambda: scope.check("ftp://example.com"), "scheme")

        secret = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz"
        red = redact_text(secret)
        assert "abcdefghijklmnopqrstuvwxyz" not in red
        assert "REDACTED" in red
        assert "[REDACTED_EMAIL]" in redact_text("mail: tester@example.com")

        assert sha256_text("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

        run = safe_run([sys.executable, "-c", "print('ok')"], timeout=10)
        assert run["returncode"] == 0 and run["stdout"].strip() == "ok"

        cmd = build_command("subfinder", "example.com", "https://example.com/")
        assert cmd == ["subfinder", "-d", "example.com", "-silent"]

        report = render({
            "title": "Reflected XSS",
            "target": "https://example.com/search",
            "severity": "medium",
            "cvss_vector": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:P/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N",
            "cwe": "CWE-79",
            "summary": "Parameter q is reflected unsafely.",
            "impact": "Script execution in victim session.",
            "steps": ["Open URL", "Enter payload"],
            "evidence": ["evidence_xss.png"],
            "remediation": "Encode output and set CSP.",
        }, "selfcheck")
        assert "Human approval before submission" in report
        assert "CVSS:4.0" in report

    # Import smoke for every tool module (catches NameError-style runtime bugs)
    import importlib
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    for mod_name in ("recon", "cve_arsenal", "h2_racer", "ldap_probe",
                     "webauto", "param_discover", "sast"):
        importlib.import_module(mod_name)
    import h2_racer as _h2
    assert callable(_h2.urlparse)

    print("SELFCHECK_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
