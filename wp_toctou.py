#!/usr/bin/env python3
"""
WP-TOCTOU Scanner — CVE-2026-119977
Detects WordPress sites running a core version in the affected range
for the predictable staging-path RCE during full-package core upgrades.

NVD summary (CVE-2026-119977, published 2026-10-31, source
security@wordfence.com): WordPress Core is vulnerable to Remote Code
Execution in versions 4.7 through 7.1.3, due to predictable,
web-accessible staging paths used during full-package core upgrades.
This makes it possible for unauthenticated attackers to execute code
on the server during the upgrade window.

Detection method — GET-only fingerprinting:
  * Confirm the target is WordPress (generator meta, wp-content /
    wp-includes markers, readme.html).
  * Determine the core version (generator meta, readme.html, ?ver=
    asset parameters) and compare against the affected range
    4.7.0–7.1.3.
  * As an extra signal, record whether /wp-content/upgrade/ responds
    (staging directory web-accessibility). The staging paths only
    exist during an upgrade, so this is a weak signal, not a verdict.

This scanner NEVER writes files, NEVER attempts to plant or execute
code, and NEVER triggers an upgrade. A VULNERABLE verdict means the
version is in the affected range; exploitation additionally requires
an active core-upgrade window, which this scanner does not create.

Usage:
    python wp_toctou.py --target https://example.com
    python wp_toctou.py --targets hosts.txt --threads 10 --output results/

For authorized security testing only.
"""

import argparse
import json
import re
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

BANNER = """
╔═══════════════════════════════════════════════════════╗
║  WP-TOCTOU — CVE-2026-119977 Scanner                  ║
║  WordPress Staging-Path RCE Detector                  ║
╚═══════════════════════════════════════════════════════╝
"""

CVE_ID = "CVE-2026-119977"
# Affected: WordPress Core 4.7.0 through 7.1.3 (inclusive).
VULN_MIN = (4, 7, 0)
VULN_MAX = (7, 1, 3)

UA = "Mozilla/5.0 (X11; Linux x86_64) WP-TOCTOU-Detector/1.0"


class WPTOCTOUScanner:
    """GET-only fingerprint scanner for CVE-2026-119977."""

    def __init__(self, timeout=10, verbose=False, verify_ssl=True):
        self.timeout = timeout
        self.verbose = verbose
        self.verify_ssl = verify_ssl
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
    def parse_version(version_str):
        """Parse a WordPress version like '6.7.1' or '4.7' -> (x, y, z)."""
        if not version_str:
            return None
        match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(version_str))
        if not match:
            return None
        major, minor, patch = match.groups()
        return (int(major), int(minor), int(patch) if patch is not None else 0)

    @staticmethod
    def is_vulnerable_version(version_tuple):
        if not version_tuple:
            return None
        return VULN_MIN <= version_tuple <= VULN_MAX

    def _get(self, url):
        """Single GET with the scanner's TLS policy; None on any failure."""
        try:
            resp = requests.get(url, timeout=self.timeout,
                                verify=self.verify_ssl,
                                allow_redirects=True,
                                headers={"User-Agent": UA})
            return resp
        except requests.RequestException as e:
            self.log(f"GET {url} failed: {e}", "debug")
            return None

    def _fetch_homepage(self, target):
        """Fetch the homepage, trying https then http for bare hosts."""
        value = (target or "").strip()
        if value.startswith(("http://", "https://")):
            resp = self._get(value)
            return (value, resp) if resp is not None else (value, None)
        for scheme in ("https", "http"):
            url = f"{scheme}://{value}"
            resp = self._get(url)
            if resp is not None:
                return url, resp
        return f"https://{value}", None

    @staticmethod
    def _extract_version(html, headers):
        """Best-effort WordPress version from HTML and headers."""
        # 1. Generator meta tag (most reliable when present).
        match = re.search(
            r'<meta\s+name=["\']generator["\']\s+content=["\']WordPress\s+([\d.]+)',
            html or "", re.I)
        if match:
            return match.group(1), "generator meta"
        # 2. readme.html ("Version X.Y.Z").
        match = re.search(r"Version\s+([\d.]+)", html or "")
        if match:
            return match.group(1), "readme.html"
        # 3. ?ver=X.Y.Z asset parameters (common, weakest signal).
        versions = re.findall(r"[?&]ver=(\d+\.\d+(?:\.\d+)?)", html or "")
        if versions:
            return versions[0], "?ver= parameter"
        return None, None

    def scan_target(self, target):
        """Fingerprint a single target."""
        parsed = urlparse(target if "://" in (target or "") else "https://" + (target or ""))
        result = {
            "target": target,
            "host": parsed.hostname,
            "port": parsed.port,
            "cve": CVE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wordpress_detected": False,
            "version": None,
            "version_tuple": None,
            "version_source": None,
            "vulnerable_version": None,
            "upgrade_dir_status": None,
            "vulnerable": False,
            "risk_level": "none",
            "status": "UNKNOWN",
            "details": [],
        }

        if not HAS_REQUESTS:
            result["status"] = "ERROR"
            result["details"].append("requests library not installed")
            return result

        self.log(f"Scanning {target}", "info")
        base_url, resp = self._fetch_homepage(target)
        if resp is None:
            result["status"] = "ERROR"
            result["details"].append("homepage unreachable (https and http)")
            return result

        base = base_url.rstrip("/") + "/"
        html = resp.text or ""
        lowered = html.lower()

        # WordPress detection markers.
        wp_markers = ["/wp-content/", "/wp-includes/", "wp-json",
                      "wordpress", "wp-emoji"]
        is_wp = any(m in lowered for m in wp_markers)
        version, source = self._extract_version(html, resp.headers)

        # Fallback: readme.html usually carries the version line.
        if is_wp and not version:
            readme = self._get(urljoin(base, "readme.html"))
            if readme is not None and readme.status_code == 200:
                version, source = self._extract_version(readme.text, readme.headers)
                if version:
                    is_wp = True

        result["wordpress_detected"] = is_wp
        if not is_wp:
            result["status"] = "NOT_WORDPRESS"
            result["details"].append("no WordPress markers on homepage")
            return result

        result["details"].append("WordPress detected")
        if version:
            result["version"] = version
            result["version_source"] = source
            result["version_tuple"] = self.parse_version(version)

        # Extra signal: is the upgrade staging directory web-accessible?
        # Staging paths only exist during an upgrade, so this is a weak
        # signal and never decides the verdict on its own.
        upgrade = self._get(urljoin(base, "wp-content/upgrade/"))
        if upgrade is not None:
            result["upgrade_dir_status"] = upgrade.status_code
            if upgrade.status_code == 200:
                result["details"].append(
                    "/wp-content/upgrade/ responds 200 (staging dir web-accessible)")

        vuln_ver = self.is_vulnerable_version(result["version_tuple"])
        result["vulnerable_version"] = vuln_ver

        if vuln_ver is True:
            result["vulnerable"] = True
            result["risk_level"] = "critical"
            result["status"] = "VULNERABLE"
            result["details"].append(
                f"WordPress {version} is in the affected range 4.7.0–7.1.3; "
                "exploitation additionally requires an active core-upgrade window")
        elif vuln_ver is False:
            result["status"] = "NOT_VULNERABLE"
            result["details"].append(
                f"WordPress {version} is outside the affected range 4.7.0–7.1.3")
        else:
            result["risk_level"] = "medium"
            result["status"] = "POSSIBLE"
            result["details"].append(
                "WordPress detected but version could not be determined — "
                "verify manually")

        self.log(f"{target} — {result['status']} "
                 f"(WP {result['version'] or '?'})",
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

    json_path = output_dir / f"wp_toctou_scan_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    md_path = output_dir / f"wp_toctou_report_{ts}.md"
    vuln = [r for r in results if r.get("vulnerable")]
    possible = [r for r in results if r.get("status") == "POSSIBLE"]

    with open(md_path, "w") as f:
        f.write("# CVE-2026-119977 — WordPress Staging-Path RCE Report\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Targets:** {len(results)} | **Vulnerable:** {len(vuln)} "
                f"| **Possible:** {len(possible)}\n\n")
        f.write("Detection is GET-only fingerprinting — no files were "
                "written and no upgrade was triggered.\n\n")

        if vuln:
            f.write("## Vulnerable Targets\n\n")
            f.write("| Target | WordPress | Upgrade dir |\n")
            f.write("|---|---|---|\n")
            for r in vuln:
                f.write(f"| {r['target']} | {r.get('version', '?')} "
                        f"| {r.get('upgrade_dir_status', '?')} |\n")

        if possible:
            f.write("\n## Possible (WordPress detected, version unknown)\n\n")
            for r in possible:
                f.write(f"- **{r['target']}**\n")

        f.write("\n## Technical Details\n\n")
        f.write("WordPress Core 4.7–7.1.3 uses predictable, web-accessible "
                "staging paths during full-package core upgrades, allowing "
                "unauthenticated attackers to execute code on the server "
                "during the upgrade window.\n")

    print(f"\n[+] Report: {md_path}")
    print(f"[+] Evidence: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="WP-TOCTOU — CVE-2026-119977 WordPress Staging-Path RCE Detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target", help="Single target URL or host")
    target_group.add_argument("--targets", help="File with target URLs/hosts")

    parser.add_argument("--threads", type=int, default=10, help="Scan threads (default: 10)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout (default: 10)")
    parser.add_argument("--output", default="./reports", help="Output directory")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Skip SSL verification")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not HAS_REQUESTS:
        print("[-] requests required: pip install requests")
        sys.exit(1)

    print(BANNER)

    scanner = WPTOCTOUScanner(
        timeout=args.timeout,
        verbose=args.verbose,
        verify_ssl=not args.no_verify_ssl,
    )

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
