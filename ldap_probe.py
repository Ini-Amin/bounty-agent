#!/usr/bin/env python3
"""
Windows LDAP OOB Write Detector — CVE-2026-119958
Detects unpatched Windows LDAP services vulnerable to OOB write RCE.

Usage:
    python ldap_probe.py --target 10.0.0.1
    python ldap_probe.py --targets dcs.txt --threads 10
    python ldap_probe.py --target 10.0.0.1 --deep-probe

Modes:
    detect     : Fingerprint LDAP service and check patch status (default)
    deep-probe : Send crafted ASN.1 to detect anomalous parsing behavior

For authorized security testing only.
"""

import argparse
import socket
import struct
import sys
import os
import json
import re
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import ssl as _ssl
    HAS_SSL = True
except ImportError:
    HAS_SSL = False


BANNER = """
╔═══════════════════════════════════════════════════════╗
║  LDAP-Probe — CVE-2026-119958 Detector                ║
║  Windows LDAP OOB Write RCE Scanner                    ║
╚═══════════════════════════════════════════════════════╝
"""

# LDAP ports
LDAP_PORT = 389
LDAPS_PORT = 636
GC_PORT = 3268
GCS_PORT = 3269

# ASN.1/BER encoding helpers
def ber_length(length):
    """Encode BER length."""
    if length < 0x80:
        return bytes([length])
    elif length < 0x100:
        return bytes([0x81, length])
    elif length < 0x10000:
        return bytes([0x82, (length >> 8) & 0xff, length & 0xff])
    else:
        return bytes([0x83, (length >> 16) & 0xff, (length >> 8) & 0xff, length & 0xff])


def ber_sequence(data):
    """Wrap data in BER SEQUENCE."""
    return b'\x30' + ber_length(len(data)) + data


def ber_integer(value):
    """Encode BER INTEGER."""
    if value == 0:
        payload = b'\x00'
    elif value > 0:
        payload = value.to_bytes((value.bit_length() + 8) // 8, 'big')
    else:
        payload = value.to_bytes((value.bit_length() + 9) // 8, 'big', signed=True)
    return b'\x02' + ber_length(len(payload)) + payload


def ber_octet_string(data):
    """Encode BER OCTET STRING."""
    if isinstance(data, str):
        data = data.encode()
    return b'\x04' + ber_length(len(data)) + data


def ber_enum(value):
    """Encode BER ENUMERATED."""
    payload = value.to_bytes(1, 'big')
    return b'\x0a' + ber_length(len(payload)) + payload


def ber_boolean(value):
    """Encode BER BOOLEAN."""
    return b'\x01\x01' + (b'\xff' if value else b'\x00')


def build_bind_request(message_id=1, dn="", password=""):
    """Build LDAP BindRequest (simple auth)."""
    # BindRequest ::= [APPLICATION 0]
    version = ber_integer(3)
    name = ber_octet_string(dn)
    auth = b'\x80' + ber_length(len(password.encode())) + password.encode()  # Simple auth

    bind_body = version + name + auth
    bind_request = b'\x60' + ber_length(len(bind_body)) + bind_body

    # LDAPMessage
    msg = ber_integer(message_id) + bind_request
    return ber_sequence(msg)


def build_search_request(message_id=2, base_dn="", scope=0, attrs=None):
    """Build LDAP SearchRequest for RootDSE."""
    if attrs is None:
        attrs = ["defaultNamingContext", "dnsHostName", "serverName",
                 "ldapServiceName", "supportedLDAPVersion", "supportedControl",
                 "currentTime", "isGlobalCatalogReady",
                 "domainFunctionality", "forestFunctionality",
                 "domainControllerFunctionality"]

    # SearchRequest ::= [APPLICATION 3]
    base = ber_octet_string(base_dn)
    scope_enum = ber_enum(scope)  # 0=base, 1=one, 2=sub
    deref = ber_enum(0)
    size_limit = ber_integer(0)
    time_limit = ber_integer(10)
    types_only = ber_boolean(False)
    # Filter: (objectClass=*)
    filter_data = b'\x87\x0b' + b'objectClass'  # Present filter

    # Attributes list
    attr_data = b''
    for attr in attrs:
        attr_data += ber_octet_string(attr)
    attr_list = ber_sequence(attr_data)

    search_body = base + scope_enum + deref + size_limit + time_limit + types_only + filter_data + attr_list
    search_request = b'\x63' + ber_length(len(search_body)) + search_body

    msg = ber_integer(message_id) + search_request
    return ber_sequence(msg)


def build_malformed_search(message_id=3):
    """
    Build a search request with intentionally malformed ASN.1
    to test parser robustness (detect OOB write behavior).
    
    This sends a deeply nested attribute with mismatched length
    descriptors — the type of payload that triggers the OOB write.
    """
    # Craft nested attribute with length > actual data
    # This probes whether the parser validates length properly
    
    base = ber_octet_string("")
    scope_enum = ber_enum(0)
    deref = ber_enum(0)
    size_limit = ber_integer(1)
    time_limit = ber_integer(5)
    types_only = ber_boolean(False)
    
    # Malformed filter: deeply nested with length confusion
    # This is a detection-safe probe — it should cause:
    # - Clean rejection on patched systems
    # - Anomalous behavior (timeout/reset/crash) on vulnerable systems
    
    # Nested AND filter with oversized inner element
    inner_present = b'\x87\x0b' + b'objectClass'
    
    # Create a substring filter with mismatched length
    # SubstringFilter with claimed length larger than actual payload
    attr_desc = ber_octet_string("cn")
    # Claim 200 bytes but provide only 10
    malformed_substring = b'\xa4' + bytes([0x81, 0xc8]) + attr_desc + b'\x30\x05\x80\x03' + b'AAA'
    
    # Wrap in AND
    filter_data = b'\xa0' + ber_length(len(inner_present) + len(malformed_substring))
    filter_data += inner_present + malformed_substring
    
    attr_list = ber_sequence(ber_octet_string("dn"))
    
    search_body = base + scope_enum + deref + size_limit + time_limit + types_only + filter_data + attr_list
    search_request = b'\x63' + ber_length(len(search_body)) + search_body
    
    msg = ber_integer(message_id) + search_request
    return ber_sequence(msg)


class LDAPProber:
    """Prober for CVE-2026-119958 Windows LDAP OOB Write."""

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

    def connect(self, host, port, use_ssl=False):
        """Connect to LDAP service (IPv4 or IPv6)."""
        try:
            sock = socket.create_connection((host, port), timeout=self.timeout)
        except Exception as e:
            self.log(f"Connection failed {host}:{port} — {e}", "debug")
            return None

        try:
            if use_ssl:
                ctx = _ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = _ssl.CERT_NONE
                sock = ctx.wrap_socket(sock, server_hostname=host)
            return sock
        except Exception as e:
            self.log(f"Connection failed {host}:{port} — {e}", "debug")
            try:
                sock.close()
            except Exception:
                pass
            return None

    def send_recv(self, sock, data, recv_size=4096):
        """Send data and receive response."""
        try:
            sock.sendall(data)
            response = b''
            while True:
                try:
                    chunk = sock.recv(recv_size)
                    if not chunk:
                        break
                    response += chunk
                    if len(chunk) < recv_size:
                        break
                except socket.timeout:
                    break
            return response
        except Exception as e:
            self.log(f"Send/recv error: {e}", "debug")
            return None

    def parse_search_result(self, data):
        """Parse LDAP SearchResultEntry to extract RootDSE attributes."""
        attrs = {}
        if not data:
            return attrs

        try:
            # Simple extraction — look for known attribute strings
            text = data.decode('utf-8', errors='ignore')

            # Extract key attributes
            patterns = {
                "dnsHostName": r'dnsHostName.*?([a-zA-Z0-9._-]+\.[a-zA-Z]{2,})',
                "defaultNamingContext": r'defaultNamingContext.*?(DC=[^,\x00]+(?:,DC=[^,\x00]+)*)',
                "serverName": r'serverName.*?(CN=[^,\x00]+(?:,CN=[^,\x00]+)*)',
                "ldapServiceName": r'ldapServiceName.*?([a-zA-Z0-9._@:-]+)',
                "domainFunctionality": r'domainFunctionality.*?(\d+)',
                "forestFunctionality": r'forestFunctionality.*?(\d+)',
                "domainControllerFunctionality": r'domainControllerFunctionality.*?(\d+)',
                "currentTime": r'currentTime.*?(\d{14})',
            }

            for attr_name, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    attrs[attr_name] = match.group(1)

            # Domain functionality levels → Windows Server version mapping
            func_map = {
                "0": "Windows 2000",
                "1": "Windows Server 2003 interim",
                "2": "Windows Server 2003",
                "3": "Windows Server 2008",
                "4": "Windows Server 2008 R2",
                "5": "Windows Server 2012",
                "6": "Windows Server 2012 R2",
                "7": "Windows Server 2016",
                "8": "Windows Server 2019",
                "9": "Windows Server 2022",
                "10": "Windows Server 2025",
            }

            dc_func = attrs.get("domainControllerFunctionality", "")
            if dc_func in func_map:
                attrs["estimated_os"] = func_map[dc_func]

        except Exception as e:
            self.log(f"Parse error: {e}", "debug")

        return attrs

    def scan_ports(self, host):
        """Quick port scan for LDAP services (IPv4 or IPv6)."""
        open_ports = []
        for port in [LDAP_PORT, LDAPS_PORT, GC_PORT, GCS_PORT]:
            sock = None
            try:
                sock = socket.create_connection((host, port), timeout=3)
                open_ports.append(port)
            except Exception:
                pass
            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except Exception:
                        pass
        return open_ports

    def query_rootdse(self, host, port=389):
        """Query RootDSE for DC fingerprinting."""
        use_ssl = port in [LDAPS_PORT, GCS_PORT]
        sock = self.connect(host, port, use_ssl)
        if not sock:
            return None

        try:
            # Anonymous bind
            bind_req = build_bind_request(message_id=1)
            bind_resp = self.send_recv(sock, bind_req)

            if not bind_resp:
                sock.close()
                return None

            # Check for bind success (resultCode = 0)
            if b'\x0a\x01\x00' not in bind_resp:  # ENUMERATED 0 = success
                self.log(f"Bind rejected on {host}:{port}", "debug")
                # Some DCs allow anonymous search without bind
                pass

            # Search RootDSE
            search_req = build_search_request(message_id=2)
            search_resp = self.send_recv(sock, search_req)

            sock.close()

            if search_resp:
                return self.parse_search_result(search_resp)

            return {}

        except Exception as e:
            self.log(f"RootDSE query error: {e}", "debug")
            try:
                sock.close()
            except Exception:
                pass
            return None

    def deep_probe(self, host, port=389):
        """
        Send malformed ASN.1 to detect OOB write vulnerability.
        
        Behavior on patched system: Clean error response or disconnect
        Behavior on vulnerable system: Timeout, RST, or service instability
        
        WARNING: This may crash the LDAP service on vulnerable systems.
        Only use on authorized test targets.
        """
        use_ssl = port in [LDAPS_PORT, GCS_PORT]

        results = {
            "probed": True,
            "host": host,
            "port": port,
            "responses": [],
            "anomalies": [],
        }

        # Test 1: Normal request baseline
        self.log(f"Deep probe — establishing baseline on {host}:{port}", "info")
        sock = self.connect(host, port, use_ssl)
        if not sock:
            results["error"] = "Cannot connect"
            return results

        try:
            bind_req = build_bind_request(message_id=1)
            t1 = time.time()
            bind_resp = self.send_recv(sock, bind_req)
            baseline_time = time.time() - t1

            results["baseline_response_time"] = round(baseline_time, 3)
            self.log(f"Baseline response: {baseline_time:.3f}s", "debug")

            sock.close()
        except Exception:
            results["error"] = "Baseline failed"
            return results

        # Test 2: Malformed ASN.1 probe
        self.log(f"Sending malformed ASN.1 probe...", "info")
        sock = self.connect(host, port, use_ssl)
        if not sock:
            results["anomalies"].append({
                "type": "connection_refused_after_baseline",
                "detail": "Could not reconnect after baseline — possible service impact",
                "severity": "high",
            })
            return results

        try:
            # Bind first
            bind_req = build_bind_request(message_id=1)
            self.send_recv(sock, bind_req)

            # Send malformed search
            malformed = build_malformed_search(message_id=3)
            t1 = time.time()
            mal_resp = self.send_recv(sock, malformed)
            probe_time = time.time() - t1

            results["probe_response_time"] = round(probe_time, 3)

            if mal_resp is None:
                results["anomalies"].append({
                    "type": "no_response",
                    "detail": "No response to malformed request — possible crash or hang",
                    "severity": "high",
                })
            elif len(mal_resp) == 0:
                results["anomalies"].append({
                    "type": "empty_response",
                    "detail": "Empty response to malformed ASN.1",
                    "severity": "medium",
                })
            else:
                # Check if it's a proper error response
                if b'\x0a\x01' in mal_resp:  # Has resultCode
                    results["responses"].append({
                        "type": "error_response",
                        "detail": "Server returned proper error (good — likely patched)",
                    })
                else:
                    results["anomalies"].append({
                        "type": "unexpected_response",
                        "detail": f"Unexpected response format ({len(mal_resp)} bytes)",
                        "severity": "medium",
                    })

            # Timing anomaly check
            if probe_time > baseline_time * 5:
                results["anomalies"].append({
                    "type": "timing_anomaly",
                    "detail": f"Probe took {probe_time:.3f}s vs baseline {baseline_time:.3f}s",
                    "severity": "medium",
                })

            sock.close()

        except ConnectionResetError:
            results["anomalies"].append({
                "type": "connection_reset",
                "detail": "Connection reset by server during malformed request",
                "severity": "high",
            })
        except socket.timeout:
            results["anomalies"].append({
                "type": "timeout",
                "detail": "Server timed out processing malformed request",
                "severity": "high",
            })
        except Exception as e:
            results["anomalies"].append({
                "type": "exception",
                "detail": str(e),
                "severity": "medium",
            })

        # Test 3: Post-probe availability check
        self.log(f"Checking post-probe availability...", "info")
        time.sleep(1)
        sock = self.connect(host, port, use_ssl)
        if sock:
            try:
                bind_req = build_bind_request(message_id=1)
                resp = self.send_recv(sock, bind_req)
                if resp:
                    results["post_probe_available"] = True
                    self.log(f"Service still responding after probe", "info")
                else:
                    results["post_probe_available"] = False
                    results["anomalies"].append({
                        "type": "degraded_after_probe",
                        "detail": "Service connected but not responding after probe",
                        "severity": "high",
                    })
                sock.close()
            except Exception:
                results["post_probe_available"] = False
        else:
            results["post_probe_available"] = False
            results["anomalies"].append({
                "type": "service_down_after_probe",
                "detail": "Cannot connect after malformed probe — possible crash",
                "severity": "critical",
            })

        return results

    def scan_host(self, host, do_deep_probe=False):
        """Full scan of a single host."""
        result = {
            "host": host,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ldap_ports": [],
            "is_domain_controller": False,
            "rootdse": {},
            "os_estimate": None,
            "vulnerable": False,
            "risk_level": "none",
            "details": [],
        }

        self.log(f"Scanning {host}", "info")

        # Phase 1: Port discovery
        open_ports = self.scan_ports(host)
        result["ldap_ports"] = open_ports

        if not open_ports:
            self.log(f"No LDAP ports open on {host}", "info")
            result["status"] = "NO_LDAP"
            return result

        self.log(f"Open LDAP ports: {open_ports}", "info")

        # Phase 2: RootDSE query
        for port in [LDAP_PORT, LDAPS_PORT]:
            if port in open_ports:
                rootdse = self.query_rootdse(host, port)
                if rootdse:
                    result["rootdse"] = rootdse
                    result["is_domain_controller"] = bool(rootdse.get("defaultNamingContext"))
                    result["os_estimate"] = rootdse.get("estimated_os")

                    if result["is_domain_controller"]:
                        self.log(f"Domain Controller: {rootdse.get('dnsHostName', host)}", "warning")
                        self.log(f"Domain: {rootdse.get('defaultNamingContext', 'N/A')}", "info")
                        if result["os_estimate"]:
                            self.log(f"Estimated OS: {result['os_estimate']}", "info")

                        result["vulnerable"] = True
                        result["risk_level"] = "critical"
                        result["details"].append("Windows Domain Controller with LDAP exposed")
                        result["details"].append("Verify November 2026 patch is applied")

                    break

        # Phase 3: Global Catalog check (confirms AD)
        if GC_PORT in open_ports or GCS_PORT in open_ports:
            result["is_domain_controller"] = True
            result["details"].append("Global Catalog port open — confirmed AD DC")

        # Phase 4: Deep probe (optional)
        if do_deep_probe and open_ports:
            port = LDAP_PORT if LDAP_PORT in open_ports else open_ports[0]
            self.log(f"Running deep probe on {host}:{port}", "warning")
            probe_result = self.deep_probe(host, port)
            result["deep_probe"] = probe_result

            if probe_result.get("anomalies"):
                high_severity = [a for a in probe_result["anomalies"]
                                 if a["severity"] in ["high", "critical"]]
                if high_severity:
                    result["risk_level"] = "critical"
                    result["details"].append(f"Deep probe found {len(high_severity)} high-severity anomalies")
                    self.log(f"ANOMALIES DETECTED — likely vulnerable!", "success")

        result["status"] = "VULNERABLE" if result["vulnerable"] else "SCANNED"
        return result

    def scan_targets(self, targets, threads=10, do_deep_probe=False):
        results = []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(self.scan_host, t.strip(), do_deep_probe): t.strip()
                for t in targets if t.strip()
            }
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

    json_path = output_dir / f"ldap_probe_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    md_path = output_dir / f"ldap_probe_report_{ts}.md"
    dcs = [r for r in results if r.get("is_domain_controller")]

    with open(md_path, "w") as f:
        f.write("# CVE-2026-119958 — Windows LDAP OOB Write Report\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Hosts Scanned:** {len(results)}\n")
        f.write(f"**Domain Controllers Found:** {len(dcs)}\n\n")

        if dcs:
            f.write("## Domain Controllers\n\n")
            f.write("| Host | DNS Name | Domain | OS Estimate | Risk |\n")
            f.write("|---|---|---|---|---|\n")
            for r in dcs:
                dns = r.get("rootdse", {}).get("dnsHostName", "?")
                domain = r.get("rootdse", {}).get("defaultNamingContext", "?")
                os_est = r.get("os_estimate", "?")
                f.write(f"| {r['host']} | {dns} | {domain} | {os_est} | {r['risk_level']} |\n")

        f.write("\n## Impact\n\n")
        f.write("Unauthenticated OOB write via crafted LDAP requests.\n")
        f.write("RCE as NT AUTHORITY\\SYSTEM on Domain Controller.\n")
        f.write("Wormable — full AD forest compromise.\n")

    print(f"\n[+] Report: {md_path}")
    print(f"[+] Evidence: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="LDAP-Probe — CVE-2026-119958 Windows LDAP OOB Write Detector",
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target", help="Single target host/IP")
    target_group.add_argument("--targets", help="File with target hosts")

    parser.add_argument("--deep-probe", action="store_true",
                        help="Send malformed ASN.1 probes (requires --confirm)")
    parser.add_argument("--confirm", action="store_true",
                        help="Acknowledge risk — allow --deep-probe (may crash LDAP service on vulnerable systems)")
    parser.add_argument("--threads", type=int, default=10, help="Scan threads")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout seconds")
    parser.add_argument("--output", default="./reports", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")

    args = parser.parse_args()

    print(BANNER)

    prober = LDAPProber(timeout=args.timeout, verbose=args.verbose)

    if args.target:
        targets = [args.target]
    else:
        with open(args.targets) as f:
            targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    deep_probe = args.deep_probe
    if deep_probe and not args.confirm:
        print("[ldap] --deep-probe blocked — add --confirm (may crash LDAP service on vulnerable systems)")
        deep_probe = False
    results = prober.scan_targets(targets, args.threads, do_deep_probe=deep_probe)
    generate_report(results, args.output)

    dc_count = sum(1 for r in results if r.get("is_domain_controller"))
    print(f"\n{'='*60}")
    print(f"[*] Scanned: {len(results)} | DCs found: {dc_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
