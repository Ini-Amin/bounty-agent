#!/usr/bin/env python3
"""
SSHole Scanner — CVE-2026-123158
Detects OpenSSH servers in the vulnerable version range for the musl
libc password-authentication bypass.

NVD summary (CVE-2026-123158, published 2026-11-05, source cve@mitre.org):
sshd in OpenSSH before 10.6p2 on Linux, when musl libc is used without
PAM, lacks a workaround for a password authentication bypass (related to
misinterpretation of whether a string is intended to be a password hash).
For some configurations of accounts, any password between 256 and 1024
characters succeeds. An example platform is Alpine Linux.

Detection method — banner fingerprinting ONLY:
  * Grab the SSH banner, parse the OpenSSH version.
  * Versions < 10.6p2 are in the affected range.
  * The banner cannot prove the platform runs musl without PAM, so a
    distro hint in the banner is used when present: an Alpine/musl hint
    raises confidence to VULNERABLE; a glibc-distro hint (Debian,
    Ubuntu, RHEL, ...) lowers it to LIKELY_NOT_AFFECTED; no hint means
    POSSIBLE (version in range, platform unconfirmed — verify manually).

This scanner NEVER attempts authentication. Confirming the bypass would
require trying a long password against a real account, which is an
actual authentication attempt, not fingerprinting — out of scope here.

Usage:
    python sshole.py --target 10.0.0.1
    python sshole.py --target 10.0.0.1:2222
    python sshole.py --targets hosts.txt --threads 10 --output results/

For authorized security testing only.
"""

import argparse
import json
import re
import socket
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

BANNER = """
╔═══════════════════════════════════════════════════════╗
║  SSHole — CVE-2026-123158 Scanner                     ║
║  OpenSSH musl Auth Bypass Detector                    ║
╚═══════════════════════════════════════════════════════╝
"""

CVE_ID = "CVE-2026-123158"
# Fixed in OpenSSH 10.6p2 — anything below is in the affected range.
FIXED_VERSION = (10, 6, 2)
DEFAULT_PORT = 22

# Banner distro hints. musl-based builds (Alpine) are the affected
# platform; glibc-based distro builds are not affected by this CVE
# even when the version is in range (the flaw needs musl w/o PAM).
MUSL_HINTS = ("alpine", "musl")
GLIBC_HINTS = ("debian", "ubuntu", "redhat", "rhel", "centos", "fedora",
               "suse", "sles", "opensuse", "arch", "gentoo", "slackware",
               "oracle", "rocky", "alma")


class SSHoleScanner:
    """Banner-fingerprint scanner for CVE-2026-123158."""

    def __init__(self, timeout=10, verbose=False):
        self.timeout = timeout
        self.verbose = verbose
        self.lock = threading.Lock()

    def log(self, msg, level="info"):
        prefix = {"info": "[*]", "success": "[+]", "warning": "[!]",
                  "error": "[-]", "debug": "[D]"}.get(level, "[*]")
        if level == "debug" and not self.verbose:
            return
        with self.lock:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"{ts} {prefix} {msg}")

    @staticmethod
    def parse_target(target):
        """Accept host, host:port, or ssh://host[:port]."""
        value = (target or "").strip()
        if "://" not in value:
            value = "ssh://" + value
        parsed = urlparse(value)
        host = parsed.hostname
        port = parsed.port or DEFAULT_PORT
        return host, port

    @staticmethod
    def parse_version(banner):
        """Parse OpenSSH_X.YpZ from a banner -> (X, Y, Z) or None."""
        match = re.search(r"OpenSSH_(\d+)\.(\d+)(?:p(\d+))?", banner or "")
        if not match:
            return None
        major, minor, patch = match.groups()
        return (int(major), int(minor), int(patch) if patch is not None else 0)

    @staticmethod
    def platform_hint(banner):
        """Best-effort platform signal from the banner distro tag."""
        text = (banner or "").lower()
        if any(h in text for h in MUSL_HINTS):
            return "musl"
        if any(h in text for h in GLIBC_HINTS):
            return "glibc"
        return "unknown"

    def grab_banner(self, host, port):
        """Dual-stack TCP connect, read one SSH banner line."""
        last_err = None
        try:
            infos = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                       socket.SOCK_STREAM)
        except socket.gaierror as e:
            return None, f"DNS resolve failed: {e}"
        for family, socktype, proto, _canon, sockaddr in infos:
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                sock.settimeout(self.timeout)
                sock.connect(sockaddr)
                data = sock.recv(256)
                return data.decode("utf-8", "ignore").strip(), None
            except OSError as e:
                last_err = e
            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass
        return None, f"connect failed: {last_err}"

    def scan_target(self, target):
        """Fingerprint a single target."""
        host, port = self.parse_target(target)
        result = {
            "target": target,
            "host": host,
            "port": port,
            "cve": CVE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "banner": None,
            "openssh_version": None,
            "version_tuple": None,
            "vulnerable_version": None,
            "platform_hint": "unknown",
            "vulnerable": False,
            "risk_level": "none",
            "status": "UNKNOWN",
            "details": [],
        }

        if not host:
            result["status"] = "ERROR"
            result["details"].append("could not parse host from target")
            return result

        self.log(f"Scanning {host}:{port}", "info")
        banner, err = self.grab_banner(host, port)
        if err:
            result["status"] = "ERROR"
            result["details"].append(err)
            self.log(f"{host}:{port} — {err}", "debug")
            return result

        result["banner"] = banner
        if not banner or not banner.startswith("SSH-"):
            result["status"] = "NOT_SSH"
            result["details"].append("no SSH banner (not an SSH service)")
            return result

        version = self.parse_version(banner)
        if version is None:
            result["status"] = "UNKNOWN_VERSION"
            result["details"].append("SSH banner present but no OpenSSH version found")
            return result

        result["version_tuple"] = version
        result["openssh_version"] = "%d.%dp%d" % version
        in_range = version < FIXED_VERSION
        result["vulnerable_version"] = in_range
        hint = self.platform_hint(banner)
        result["platform_hint"] = hint

        if not in_range:
            result["status"] = "NOT_VULNERABLE"
            result["details"].append(
                f"OpenSSH {result['openssh_version']} >= 10.6p2 (patched)")
            return result

        # Version is in the affected range; the platform decides.
        if hint == "musl":
            result["vulnerable"] = True
            result["risk_level"] = "critical"
            result["status"] = "VULNERABLE"
            result["details"].append(
                f"OpenSSH {result['openssh_version']} < 10.6p2 with musl hint "
                "(Alpine/musl platform — bypass condition likely met)")
        elif hint == "glibc":
            result["risk_level"] = "low"
            result["status"] = "LIKELY_NOT_AFFECTED"
            result["details"].append(
                f"OpenSSH {result['openssh_version']} < 10.6p2 but banner "
                "indicates a glibc distro build (CVE needs musl without PAM)")
        else:
            result["risk_level"] = "medium"
            result["status"] = "POSSIBLE"
            result["details"].append(
                f"OpenSSH {result['openssh_version']} < 10.6p2; platform "
                "(musl vs glibc, PAM) cannot be confirmed from the banner — "
                "verify manually (e.g. Alpine Linux target)")

        self.log(f"{host}:{port} — {result['status']} "
                 f"(OpenSSH {result['openssh_version']}, hint={hint})",
                 "warning" if result["vulnerable"] else "info")
        return result

    def scan_targets(self, targets, threads=10):
        results = []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(self.scan_target, t.strip()): t.strip()
                       for t in targets if t.strip()}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    self.log(f"Error: {e}", "error")
        return results


def generate_report(results, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = output_dir / f"sshole_scan_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    md_path = output_dir / f"sshole_report_{ts}.md"
    vuln = [r for r in results if r.get("vulnerable")]
    possible = [r for r in results if r.get("status") == "POSSIBLE"]

    with open(md_path, "w") as f:
        f.write("# CVE-2026-123158 — OpenSSH musl Auth Bypass Report\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Targets:** {len(results)} | **Vulnerable:** {len(vuln)} "
                f"| **Possible:** {len(possible)}\n\n")
        f.write("Detection is banner fingerprinting only — no authentication "
                "was attempted.\n\n")

        if vuln:
            f.write("## Vulnerable Targets\n\n")
            f.write("| Target | OpenSSH | Platform hint |\n")
            f.write("|---|---|---|\n")
            for r in vuln:
                f.write(f"| {r['target']} | {r.get('openssh_version', '?')} "
                        f"| {r.get('platform_hint', '?')} |\n")

        if possible:
            f.write("\n## Possible (version in range, platform unconfirmed)\n\n")
            for r in possible:
                f.write(f"- **{r['target']}** — OpenSSH "
                        f"{r.get('openssh_version', '?')}\n")

        f.write("\n## Technical Details\n\n")
        f.write("sshd in OpenSSH before 10.6p2 on Linux, when musl libc is "
                "used without PAM, misinterprets whether a string is a "
                "password hash; for some account configurations any password "
                "between 256 and 1024 characters succeeds.\n")

    print(f"\n[+] Report: {md_path}")
    print(f"[+] Evidence: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="SSHole — CVE-2026-123158 OpenSSH musl Auth Bypass Detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target", help="Single target host or host:port")
    target_group.add_argument("--targets", help="File with target hosts")

    parser.add_argument("--threads", type=int, default=10, help="Scan threads (default: 10)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout (default: 10)")
    parser.add_argument("--output", default="./reports", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print(BANNER)

    scanner = SSHoleScanner(timeout=args.timeout, verbose=args.verbose)

    if args.target:
        targets = [args.target]
    else:
        with open(args.targets) as f:
            targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    results = scanner.scan_targets(targets, args.threads)
    generate_report(results, args.output)

    vuln_count = sum(1 for r in results if r.get("vulnerable"))
    print(f"\n{'='*60}")
    print(f"[*] Scanned: {len(results)} | Vulnerable: {vuln_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
