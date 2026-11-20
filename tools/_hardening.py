"""Shared hardening helpers for BOUNTY tools.

Stdlib only. No shell, no implicit network, no secret storage.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import threading
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

MAX_OUTPUT = 2_000_000
ENV_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "NO_COLOR", "TERM")
BLOCKED_HOSTS = {"localhost", "metadata.google.internal", "metadata", "instance-data"}

_RESOLVE_CACHE: dict = {}


def _resolved_addrs(host: str, timeout_s: float = 2.0) -> set:
    """Best-effort DNS resolve with timeout (getaddrinfo has none).

    On timeout/failure returns empty set; Scope.check then allows the
    target (the user explicitly asked for that host).
    """
    if host in _RESOLVE_CACHE:
        return set(_RESOLVE_CACHE[host])
    out: set = set()

    def _run():
        try:
            for _fam, _typ, _proto, _canon, addr in socket.getaddrinfo(host, None):
                if addr:
                    out.add(addr[0])
        except Exception:
            pass

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    th.join(timeout_s)
    if not th.is_alive():
        _RESOLVE_CACHE[host] = set(out)
    return set(out)


class ToolError(Exception):
    """Hardening/validation failure."""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_host(host: str) -> str:
    h = (host or "").strip().lower().rstrip(".")
    if h.startswith("[") and h.endswith("]"):
        h = h[1:-1]
    return h


def _host_match(pattern: str, host: str) -> bool:
    p = normalize_host(pattern)
    h = normalize_host(host)
    if not p or not h:
        return False
    if p.startswith("*."):
        return h.endswith(p[1:])
    return p == h


def _path_match(pattern: str, path: str) -> bool:
    p = pattern or "*"
    value = path or "/"
    if p == "/":
        return value in ("", "/")
    if not p.startswith("/"):
        p = "/" + p
    return fnmatch(value, p)


def _entry_matches(entry: str, host: str, path: str) -> bool:
    e = (entry or "").strip()
    if not e:
        return False
    if "://" in e:
        parts = urlsplit(e)
        return _host_match(parts.hostname or "", host) and _path_match(parts.path, path)
    if "/" in e:
        hostpart, pathpart = e.split("/", 1)
        return _host_match(hostpart, host) and _path_match("/" + pathpart, path)
    return _host_match(e, host)


def redact_text(text: str) -> str:
    if not text:
        return text
    value = str(text)
    value = re.sub(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        value,
        flags=re.S,
    )
    value = re.sub(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\b", "[REDACTED_JWT]", value)
    value = re.sub(r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_AWS_KEY]", value)
    value = re.sub(
        r"(?i)\b(authorization|x-api-key|api[_-]?key|token|secret|password|client_secret)\b\s*[:=]\s*['\"]?(?:Bearer\s+)?[^\s'\",;]+",
        r"\1=[REDACTED]",
        value,
    )
    value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", "Bearer [REDACTED]", value)
    value = re.sub(r"(?i)\b(cookie|set-cookie)\b\s*[:=]\s*[^\r\n;]+", r"\1=[REDACTED]", value)
    value = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]", value)
    return value


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    sensitive = {"authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token", "proxy-authorization"}
    out: dict[str, str] = {}
    for key, value in (headers or {}).items():
        if str(key).strip().lower() in sensitive:
            out[str(key)] = "[REDACTED]"
        else:
            out[str(key)] = redact_text(str(value))
    return out


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: str | Path, data: Any) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return target


def safe_run(cmd: list[str], timeout: int = 60, max_output: int = MAX_OUTPUT) -> dict[str, Any]:
    if not cmd or not isinstance(cmd, list) or not all(isinstance(part, str) for part in cmd):
        raise ToolError("command must be a non-empty list of strings")
    if timeout <= 0 or timeout > 3600:
        raise ToolError("timeout must be 1-3600")
    binary = cmd[0]
    exe = binary if os.path.isabs(binary) else shutil.which(binary)
    if not exe:
        raise ToolError(f"binary not found: {binary}")
    env = {k: os.environ[k] for k in ENV_KEYS if k in os.environ}
    env.setdefault("PATH", os.defpath)
    try:
        proc = subprocess.run(
            [exe, *cmd[1:]],
            capture_output=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolError(f"timeout after {timeout}s: {binary}") from exc
    stdout = proc.stdout.decode("utf-8", "ignore") if isinstance(proc.stdout, bytes) else str(proc.stdout or "")
    stderr = proc.stderr.decode("utf-8", "ignore") if isinstance(proc.stderr, bytes) else str(proc.stderr or "")
    truncated = False
    if len(stdout) > max_output:
        stdout = stdout[:max_output] + "\n[TRUNCATED]"
        truncated = True
    if len(stderr) > max_output:
        stderr = stderr[:max_output] + "\n[TRUNCATED]"
        truncated = True
    return {
        "binary": binary,
        "returncode": proc.returncode,
        "stdout": redact_text(stdout),
        "stderr": redact_text(stderr),
        "truncated": truncated,
        "at": utcnow(),
    }


def run_allowlisted(binary: str, args: list[str], allowed: set[str], timeout: int = 60) -> dict[str, Any]:
    if binary not in allowed:
        raise ToolError(f"binary not allowlisted: {binary}")
    return safe_run([binary, *args], timeout=timeout)


class Scope:
    def __init__(self, data: dict[str, Any], allow_private: bool = False):
        if not isinstance(data, dict):
            raise ToolError("scope file must contain a JSON object")
        self.program = str(data.get("program") or "unspecified")
        self.in_scope = [str(x) for x in data.get("in_scope", []) if str(x).strip()]
        self.out_of_scope = [str(x) for x in data.get("out_of_scope", []) if str(x).strip()]
        self.allow_private = bool(data.get("allow_private", False)) or bool(allow_private)
        if not self.in_scope:
            raise ToolError("scope has no in_scope entries")

    @classmethod
    def load(cls, path: str | Path, allow_private: bool = False) -> "Scope":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data, allow_private=allow_private)

    def check(self, target: str) -> dict[str, Any]:
        value = (target or "").strip()
        if not value:
            raise ToolError("empty target")
        if value.startswith("//"):
            value = "https:" + value
        if "://" not in value:
            value = "https://" + value
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https"):
            raise ToolError(f"scheme not allowed: {parts.scheme}")
        if parts.username or parts.password:
            raise ToolError("credentials in URL are not allowed")
        host = normalize_host(parts.hostname or "")
        if not host:
            raise ToolError("target has no host")
        if host.lower() in BLOCKED_HOSTS:
            raise ToolError(f"blocked host: {host}")
        if host.lower().endswith((".local", ".internal")):
            raise ToolError(f"blocked local/internal host: {host}")
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            ip = None
        if ip is not None:
            if ip.is_link_local or ip == ipaddress.ip_address("169.254.169.254"):
                raise ToolError("metadata/link-local address blocked")
            if not self.allow_private and (ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast):
                raise ToolError(f"private/special address blocked: {host}")
        else:
            # Hostname — best-effort resolve with timeout; reject when any
            # resolved address is link-local/metadata or private/loopback/
            # reserved/multicast (unless allow_private). TOCTOU (rebinding
            # between check and fetch) cannot be fully closed here.
            resolved = _resolved_addrs(host)
            for a in sorted(resolved):
                try:
                    rip = ipaddress.ip_address(a)
                except ValueError:
                    continue
                if rip.is_link_local or rip == ipaddress.ip_address("169.254.169.254"):
                    raise ToolError(f"metadata/link-local address resolved for {host}: {a}")
                if not self.allow_private and (
                        rip.is_private or rip.is_loopback or rip.is_reserved or rip.is_multicast):
                    raise ToolError(f"private/special address resolved for {host}: {a}")
        path = parts.path or "/"
        if any(_entry_matches(entry, host, path) for entry in self.out_of_scope):
            raise ToolError(f"target is out of scope: {host}{path}")
        if not any(_entry_matches(entry, host, path) for entry in self.in_scope):
            raise ToolError(f"target is not in scope: {host}{path}")
        normalized = urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))
        return {"url": normalized, "host": host, "path": path, "program": self.program}
