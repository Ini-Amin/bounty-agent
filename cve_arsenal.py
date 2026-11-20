#!/usr/bin/env python3
"""
CVE Arsenal — Unified November 2026 CVE Scanner
Orchestrates all 5 CVE scanners for mass bug bounty hunting.

Usage:
    python cve_arsenal.py --target example.com --all
    python cve_arsenal.py --targets scope.txt --cve sshole,wp-toctou,h2-race
    python cve_arsenal.py --target 10.0.0.1 --cve ldap --deep-probe
    python cve_arsenal.py --targets scope.txt --all --threads 20 --output bounty_results/

CVE Modules:
    sshole    : CVE-2026-123158 — OpenSSH musl auth bypass
    wp-toctou : CVE-2026-119977 — WordPress staging directory race
    h2-race   : CVE-2026-119618 — Apache mod_http2 heap corruption
    ldap      : CVE-2026-119958 — Windows LDAP OOB write
    sonicwall : CVE-2026-19868  — SonicWall SSLVPN MFA bypass (fingerprint only)

For authorized security testing only.
"""

import argparse
import sys
import os
import json
import time
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


BANNER = """
╔═══════════════════════════════════════════════════════════╗
║  CVE Arsenal — November 2026 Unified Scanner              ║
║  5 Critical CVEs | Bug Bounty Optimized                    ║
║                                                            ║
║  Modules:                                                  ║
║    SSHole     │ CVE-2026-123158 │ OpenSSH Auth Bypass      ║
║    WP-TOCTOU  │ CVE-2026-119977 │ WordPress RCE Race       ║
║    H2-Racer   │ CVE-2026-119618 │ Apache HTTP/2 RCE        ║
║    LDAP-Probe │ CVE-2026-119958 │ Windows LDAP Worm        ║
║    SonicWall  │ CVE-2026-19868  │ SSLVPN MFA Bypass        ║
╚═══════════════════════════════════════════════════════════╝
"""

# Module mapping
CVE_MODULES = {
    "sshole": {
        "cve": "CVE-2026-123158",
        "cwe": "CWE-916",
        "name": "SSHole — OpenSSH Auth Bypass",
        "script": "sshole.py",
        "ports": [22],
        "description": "musl libc crypt() error → password hash collision",
    },
    "wp-toctou": {
        "cve": "CVE-2026-119977",
        "cwe": "CWE-362",
        "name": "WP-TOCTOU — WordPress RCE",
        "script": "wp_toctou.py",
        "ports": [80, 443],
        "description": "Upgrade staging directory exposure → config hijack → RCE",
    },
    "h2-race": {
        "cve": "CVE-2026-119618",
        "cwe": "CWE-362",
        "name": "H2-Racer — Apache mod_http2 RCE",
        "script": "h2_racer.py",
        "ports": [443, 80, 8443],
        "description": "HTTP/2 concurrent stream race → heap corruption → RCE",
    },
    "ldap": {
        "cve": "CVE-2026-119958",
        "cwe": "CWE-122",
        "name": "LDAP-Probe — Windows LDAP RCE",
        "script": "ldap_probe.py",
        "ports": [389, 636, 3268, 3269],
        "description": "Malformed ASN.1 → OOB write → SYSTEM on Domain Controller",
    },
    "sonicwall": {
        "cve": "CVE-2026-19868",
        "cwe": "CWE-306",
        "name": "SonicWall SSLVPN MFA Bypass",
        "script": None,  # Fingerprint-only mode built into arsenal
        "ports": [443, 4433],
        "description": "SAML/MFA bypass via alternate auth backend",
    },
}


def check_sonicwall(host, port=443, timeout=10):
    """Fingerprint SonicWall SSLVPN for CVE-2026-19868."""
    try:
        import requests
        from urllib3.exceptions import InsecureRequestWarning
        import warnings
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    except ImportError:
        return {"error": "requests not installed"}

    result = {
        "host": host,
        "cve": "CVE-2026-19868",
        "is_sonicwall": False,
        "sslvpn_detected": False,
        "version_info": None,
        "vulnerable": False,
    }

    # Common SonicWall SSLVPN paths
    paths = [
        "/cgi-bin/welcome",
        "/auth.html",
        "/auth1.html",
        "/remote/login",
        "/__extraweb__/virtualoffice/",
        "/dana-na/auth/url_default/welcome.cgi",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for scheme in ["https"]:
        base = f"{scheme}://{host}:{port}" if port != 443 else f"{scheme}://{host}"

        try:
            r = requests.get(base, timeout=timeout, verify=False,
                             allow_redirects=True, headers=headers)

            # Check response headers and body for SonicWall indicators
            server = r.headers.get("Server", "").lower()
            body = r.text.lower()

            sonicwall_sigs = [
                "sonicwall", "sslvpn", "sonic", "dell sonicwall",
                "netextender", "virtual office", "sma",
            ]

            for sig in sonicwall_sigs:
                if sig in server or sig in body:
                    result["is_sonicwall"] = True
                    break

            # Check specific SSLVPN login page
            if result["is_sonicwall"]:
                for path in paths:
                    try:
                        r2 = requests.get(f"{base}{path}", timeout=timeout,
                                          verify=False, headers=headers)
                        if r2.status_code == 200 and any(
                            s in r2.text.lower() for s in ["sslvpn", "login", "authentication"]
                        ):
                            result["sslvpn_detected"] = True
                            break
                    except Exception:
                        continue

            if result["sslvpn_detected"]:
                result["vulnerable"] = True
                result["detail"] = ("SonicWall SSLVPN detected — verify SAML config and "
                                    "firmware version for CVE-2026-19868")

        except Exception as e:
            result["error"] = str(e)

    return result


def run_arsenal(targets, modules, output_dir, threads=10, deep_probe=False, verbose=False):
    """Run selected CVE modules against targets."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {
        "scan_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "targets_count": len(targets),
        "modules_run": modules,
        "results": {},
        "summary": {},
    }

    base_dir = Path(__file__).parent

    for mod_key in modules:
        mod_info = CVE_MODULES.get(mod_key)
        if not mod_info:
            print(f"[-] Unknown module: {mod_key}")
            continue

        print(f"\n{'='*60}")
        print(f"[*] Running: {mod_info['name']}")
        print(f"[*] CVE: {mod_info['cve']}")
        print(f"[*] Targets: {len(targets)}")
        print(f"{'='*60}\n")

        module_results = []

        if mod_key == "sonicwall":
            # Built-in SonicWall scanner
            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = {executor.submit(check_sonicwall, t): t for t in targets}
                for future in as_completed(futures):
                    try:
                        r = future.result()
                        module_results.append(r)
                        if r.get("is_sonicwall"):
                            print(f"[+] SonicWall detected: {r['host']}")
                    except Exception as e:
                        print(f"[-] Error: {e}")

        elif mod_key == "sshole":
            try:
                from sshole import SSHoleScanner
                scanner = SSHoleScanner(verbose=verbose)
                module_results = scanner.scan_targets(targets, threads=threads)
            except ImportError:
                print(f"[-] sshole.py NOT FOUND in repo — reporting {len(targets)} target(s) as UNAVAILABLE")
                module_results = [
                    {"host": t, "status": "UNAVAILABLE",
                     "cve": mod_info["cve"], "cwe": mod_info["cwe"],
                     "details": ["sshole.py missing from repo — restore before use"]}
                    for t in targets
                ]

        elif mod_key == "wp-toctou":
            try:
                from wp_toctou import WPTOCTOUScanner
                scanner = WPTOCTOUScanner(verbose=verbose)
                module_results = scanner.scan_targets(targets, threads=threads)
            except ImportError:
                print(f"[-] wp_toctou.py NOT FOUND in repo — reporting {len(targets)} target(s) as UNAVAILABLE")
                module_results = [
                    {"host": t, "status": "UNAVAILABLE",
                     "cve": mod_info["cve"], "cwe": mod_info["cwe"],
                     "details": ["wp_toctou.py missing from repo — restore before use"]}
                    for t in targets
                ]

        elif mod_key == "h2-race":
            try:
                from h2_racer import H2RaceProber
                prober = H2RaceProber(verbose=verbose)
                module_results = prober.scan_targets(targets, threads=threads)
            except ImportError:
                print(f"[-] Cannot import h2_racer module")

        elif mod_key == "ldap":
            try:
                from ldap_probe import LDAPProber
                prober = LDAPProber(verbose=verbose)
                module_results = prober.scan_targets(targets, threads=threads,
                                                      do_deep_probe=deep_probe)
            except ImportError:
                print(f"[-] Cannot import ldap_probe module")

        # Store results
        all_results["results"][mod_key] = module_results

        # Count findings
        vuln_count = sum(1 for r in module_results
                         if r.get("vulnerable") or r.get("exploitable") or
                         r.get("status") in ["VULNERABLE", "EXPLOITABLE"])

        all_results["summary"][mod_key] = {
            "cve": mod_info["cve"],
            "cwe": mod_info["cwe"],
            "scanned": len(module_results),
            "vulnerable": vuln_count,
            "unavailable": sum(1 for r in module_results if r.get("status") == "UNAVAILABLE"),
        }

        print(f"\n[*] {mod_info['name']}: {vuln_count}/{len(module_results)} vulnerable")

    # Save combined results
    ts = all_results["scan_id"]
    json_path = output_dir / f"cve_arsenal_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    # Generate combined report
    md_path = output_dir / f"cve_arsenal_report_{ts}.md"
    with open(md_path, "w") as f:
        f.write("# CVE Arsenal — Bug Bounty Scan Report\n\n")
        f.write(f"**Date:** {all_results['timestamp']}\n")
        f.write(f"**Targets:** {all_results['targets_count']}\n")
        f.write(f"**Modules:** {', '.join(all_results['modules_run'])}\n\n")

        f.write("## Summary\n\n")
        f.write("| Module | CVE | CWE | Scanned | Vulnerable |\n")
        f.write("|---|---|---|---|---|\n")

        total_vuln = 0
        for mod_key, summary in all_results["summary"].items():
            status = f"🔴 {summary['vulnerable']}" if summary['vulnerable'] else f"✅ {summary['vulnerable']}"
            f.write(f"| {mod_key} | {summary['cve']} | {summary['cwe']} | {summary['scanned']} | {status} |\n")
            total_vuln += summary["vulnerable"]

        f.write(f"\n**Total Findings: {total_vuln}**\n\n")

        # Unavailable modules surfaced (anti silent-skip)
        unavail_notes = [
            f"{s.get('unavailable', 0)}/{s['scanned']} unavailable — {mod_key}: {s['cve']} (CWE {s.get('cwe','-')}) — module file missing (restore before use)"
            for mod_key, s in all_results["summary"].items() if s.get("unavailable")
        ]
        if unavail_notes:
            f.write("## Unavailable modules\n\n")
            for n in unavail_notes:
                f.write(f"- {n}\n")
            f.write("\n")

        # Detail per module
        for mod_key, mod_results in all_results["results"].items():
            vuln_results = [r for r in mod_results
                            if r.get("vulnerable") or r.get("exploitable") or
                            r.get("status") in ["VULNERABLE", "EXPLOITABLE"]]
            if vuln_results:
                f.write(f"## {CVE_MODULES[mod_key]['name']}\n\n")
                f.write(f"- CVE: {CVE_MODULES[mod_key]['cve']} · CWE: {CVE_MODULES[mod_key]['cwe']}\n\n")
                for r in vuln_results:
                    host = r.get("host") or r.get("target", "?")
                    f.write(f"- **{host}** — {r.get('status', 'VULNERABLE')}\n")
                    for detail in r.get("details", []):
                        f.write(f"  - {detail}\n")
                f.write("\n")

    print(f"\n{'='*60}")
    print(f"[+] Combined Report: {md_path}")
    print(f"[+] JSON Evidence: {json_path}")
    print(f"[+] Total Findings: {total_vuln}")
    print(f"{'='*60}")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="CVE Arsenal — Unified November 2026 CVE Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --target example.com --all
  %(prog)s --targets scope.txt --cve sshole,wp-toctou
  %(prog)s --target 10.0.0.1 --cve ldap --deep-probe
  %(prog)s --targets scope.txt --all --threads 20 --output bounty/
        """,
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target", help="Single target")
    target_group.add_argument("--targets", help="File with targets")

    parser.add_argument("--all", action="store_true", help="Run all CVE modules")
    parser.add_argument("--cve", help="Comma-separated modules: sshole,wp-toctou,h2-race,ldap,sonicwall")
    parser.add_argument("--deep-probe", action="store_true", help="Enable deep probing (LDAP)")
    parser.add_argument("--threads", type=int, default=10, help="Threads (default: 10)")
    parser.add_argument("--output", default="./reports", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    parser.add_argument("--list-modules", action="store_true", help="List available modules")

    args = parser.parse_args()

    print(BANNER)

    if args.list_modules:
        print("Available modules:\n")
        for key, info in CVE_MODULES.items():
            print(f"  {key:12s} │ {info['cve']:18s} │ {info['name']}")
            print(f"  {' '*12} │ {' '*18} │ {info['description']}")
            print()
        return

    # Determine modules to run
    if args.all:
        modules = list(CVE_MODULES.keys())
    elif args.cve:
        modules = [m.strip() for m in args.cve.split(",")]
        for m in modules:
            if m not in CVE_MODULES:
                print(f"[-] Unknown module: {m}")
                print(f"[*] Available: {', '.join(CVE_MODULES.keys())}")
                sys.exit(1)
    else:
        print("[-] Specify --all or --cve <modules>")
        sys.exit(1)

    # Load targets
    if args.target:
        targets = [args.target]
    else:
        with open(args.targets) as f:
            targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    print(f"[*] Targets: {len(targets)}")
    print(f"[*] Modules: {', '.join(modules)}")
    print()

    run_arsenal(targets, modules, args.output, args.threads, args.deep_probe, args.verbose)


if __name__ == "__main__":
    main()
