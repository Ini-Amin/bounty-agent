#!/usr/bin/env python3
"""
recon.py — YATIM DEEP RECON PIPELINE (RAM-SAFE)
================================================
One command. Aggressive full-surface recon. Neat report. No agent typing.
Memory discipline: capped sets, batched HTTP, no body retention, bounded workers.

Modes:
  default  — balanced deep (recommended)
  --fast   — fewer paths, lower limits
  --deep   — more sources (extra CT, port-lite, method enum, deeper wayback)

Stages:
  1  http      headers · tech · security · robots/sitemap baseline
  2  dns       A/AAAA/MX/NS/TXT/CNAME/CAA/SOA + SPF/DMARC/DKIM
  3  cert      TLS cert SAN → related hostnames (other sites on same cert)
   4  subs      crt.sh + OTX + anubis + rapidDNS + wayback + hackertarget + bufferover + subfinder + dns-brute + permutasi (parallel, capped)
  5  probe     live HTTP(S) probe of subdomains (httpx binary, bounded)
  6  paths     sensitive path probe (capped wordlist)
  7  robots    robots.txt/sitemap deep parse → more paths
  8  js        JS endpoint/secret/lib mining (no body store)
  9  wayback   historical URLs · params · interesting files
  10 emails    email/social/phone harvest (HTML+JS+wayback sample)
  11 ports     top-port TCP connect lite (no nmap needed)
  12 methods   HTTP verb enum · TRACE/PUT/CORS-preflight · WAF sniff
  13 quick     CORS reflection · open-redirect candidates
  14 report    report.md + report.json + findings/ + pocs/ + evidence/ + SUMMARY.md + metadata.json

Usage:
  python recon.py --target example.com
  python recon.py --target example.com --deep --threads 12
  python recon.py --target https://app.example.com --fast
  python recon.py --target example.com --stages dns,cert,subs,probe,report

Output:
  reports/<target_slug>_<ts>/report.md       (full dump + FINDINGS EVIDENCE w/ raw HTTP)
  reports/<target_slug>_<ts>/report.json
  reports/<target_slug>_<ts>/endpoints.txt
  reports/<target_slug>_<ts>/hosts.txt
  reports/<target_slug>_<ts>/findings/       (per-finding 8-section docs: [SEV]_<slug>.md)
  reports/<target_slug>_<ts>/pocs/           (minimal-impact verification scripts: poc_<vuln>.py)
  reports/<target_slug>_<ts>/evidence/       (recon_notes.md + <stage>_output.json, redacted)
  reports/<target_slug>_<ts>/SUMMARY.md      (severity matrix — built-in aggregator)
  reports/<target_slug>_<ts>/metadata.json   (machine-readable counts)

Policy:
  - Global rate gate ~8 req/s (5-10 rps), 429 backoff, 403 header-mutation fallback
  - Zero-False-Positive: evidence_status CONFIRMED requires raw HTTP proof
  - Secrets/Bearer tokens redacted before any file write

Dependencies: pip install requests urllib3
Optional on PATH: subfinder, httpx (ProjectDiscovery)
"""

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse as up
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("ERROR: pip install requests urllib3")
    sys.exit(1)

ROOT = Path(__file__).parent
OUTROOT = ROOT / "reports"  # reports/<slug>/
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
T = 10

# ── RAM-SAFE HARD CAPS (v2 kompleks + cepat) ───────
CAP_SUBS = 800          # max subdomains kept / probed (naik 400->800, tetap RAM aman)
CAP_WAYBACK = 6000      # max wayback rows parsed
CAP_PATHS_FAST = 40
CAP_PATHS = 90
CAP_JS = 20
CAP_PORTS = 40
CAP_EMAILS = 300
CAP_RELATED = 200
CAP_ENDPOINTS_STORE = 3000

# Flexible port set — web apps are NOT always 80/443/8080/8443.
# Scan order mixes common web, alt HTTP, app-tier, and data/infra so nonstandard
# listeners still get hit within CAP_PORTS.
TOP_PORTS = [
    # common web / alt-http
    80, 443, 8080, 8443, 8000, 8888, 3000, 5000, 5001, 9090,
    8008, 8081, 8082, 8088, 8090, 8180, 8880, 9000, 9443, 10443,
    4443, 8444, 9444, 10443, 2083, 2087, 2096, 4443, 4444, 6443,
    7443, 9443, 11443, 16443, 24443, 34443,
    # app / dev / admin UIs
    4200, 4201, 4400, 4567, 5173, 5174, 5300, 5433, 5900, 5985,
    5986, 6080, 6379, 7001, 7002, 7474, 7687, 8001, 8002, 8003,
    8008, 8010, 8085, 8090, 8161, 8500, 8501, 8530, 8531, 8765,
    8834, 8983, 9001, 9091, 9092, 9200, 9300, 9418, 9990, 9999,
    10000, 10250, 10255, 10443, 15672, 16379, 18080, 20000, 25000,
    27017, 27018, 28017, 50000, 50070, 50075, 50090, 61616,
    # infra / mail / directory / db (non-HTTP services still worth probing)
    21, 22, 23, 25, 53, 110, 135, 139, 143, 389, 445, 465, 587,
    636, 993, 995, 1433, 1521, 1604, 2049, 2375, 2376, 3128,
    3306, 3389, 5432, 5601, 5672, 5901, 5984, 6379, 7001, 8161,
    9200, 9300, 11211, 15672, 27017, 3389, 5900, 5901,
]
# de-dupe preserve order
TOP_PORTS = list(dict.fromkeys(TOP_PORTS))

# Multi-stack sensitive paths — targets are NOT always PHP.
SENSITIVE_PATHS = [
    # VCS / env / secrets (stack-agnostic)
    "/.git/HEAD", "/.git/config", "/.gitignore", "/.svn/entries",
    "/.env", "/.env.local", "/.env.backup", "/.env.prod", "/.env.staging",
    "/.DS_Store", "/.htaccess", "/.htpasswd", "/.well-known/security.txt",
    "/.aws/credentials", "/.ssh/id_rsa", "/id_rsa", "/.dockerenv",
    "/backup.zip", "/backup.sql", "/dump.sql", "/db.sql", "/database.sql",
    "/backup.tar.gz", "/site.zip", "/www.zip", "/source.zip", "/html.zip",
    "/crossdomain.xml", "/clientaccesspolicy.xml",
    "/sitemap.xml", "/sitemap_index.xml", "/robots.txt", "/humans.txt",
    "/security.txt", "/ads.txt", "/app-ads.txt", "/manifest.json",
    # PHP / classic LAMP (still common — just not assumed)
    "/config.php", "/wp-config.php.bak", "/wp-config.php~", "/wp-config.php.save",
    "/wp-config.php.old", "/wp-config.php.txt",
    "/phpinfo.php", "/info.php", "/test.php",
    "/phpmyadmin/", "/pma/", "/myadmin/", "/adminer.php", "/adminer/",
    "/wp-admin/", "/wp-login.php", "/wp-json/", "/wp-json/wp/v2/users",
    "/administrator/index.php", "/shell.php", "/c99.php", "/eval.php",
    "/upload.php", "/uploads/", "/vendor/phpunit/",
    "/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/_profiler/phpinfo", "/debug/default/view",
    # Python / Django / Flask / FastAPI
    "/settings.py", "/debug", "/_debug", "/_profiler/", "/telescope",
    "/horizon", "/_ignition/health-check",
    # Java / Spring / Tomcat / JVM
    "/actuator", "/actuator/health", "/actuator/env", "/actuator/mappings",
    "/actuator/beans", "/actuator/configprops", "/actuator/heapdump",
    "/jolokia/", "/jolokia/list", "/manager/html", "/host-manager/html",
    "/jmx-console/", "/invoker/JMXInvokerServlet",
    "/elmah.axd", "/trace.axd", "/console/login",
    # .NET / IIS / Azure
    "/web.config", "/appsettings.json", "/elmah.axd", "/trace.axd",
    "/_vti_bin/", "/_vti_inf.html", "/elmah", "/hangfire",
    # Node / JS frameworks
    "/package.json", "/package-lock.json", "/yarn.lock", "/.nvmrc",
    "/_next/static/", "/api/graphql", "/socket.io/", "/.well-known/assetlinks.json",
    # Ruby / Rails / PHP-composer neighbors
    "/Gemfile", "/Gemfile.lock", "/composer.json", "/composer.lock",
    "/config.ru", "/config/database.yml",
    # Go / Rust / generic compiled services
    "/go.mod", "/go.sum", "/Cargo.toml", "/debug/pprof/", "/debug/vars",
    "/metrics", "/health", "/healthz", "/ready", "/status",
    # config / orchestration / CI
    "/config.yml", "/config.yaml", "/config.json", "/config.xml",
    "/docker-compose.yml", "/docker-compose.yaml", "/Dockerfile",
    "/.gitlab-ci.yml", "/.github/workflows/", "/Jenkinsfile",
    "/terraform.tfstate", "/.tfstate", "/kubeconfig", "/.kube/config",
    # admin / panels / consoles (any stack)
    "/admin/", "/administrator/", "/backend/", "/console", "/debugger/",
    "/login", "/signin", "/dashboard", "/panel/",
    "/adminer/", "/pgadmin/", "/redis-commander/",
    # API / docs / schema (any stack)
    "/api/", "/api/v1/", "/api/v2/", "/api/docs", "/swagger/",
    "/swagger.json", "/swagger-ui.html", "/swagger/index.html",
    "/openapi.json", "/v2/api-docs", "/v3/api-docs",
    "/graphql", "/graphiql/", "/playground", "/api-explorer/",
    # observability / search / queue UIs
    "/solr/", "/jenkins/", "/jira/", "/grafana/", "/kibana/",
    "/server-status", "/server-info", "/serverinfo",
]

CORS_ORIGINS = [
    "https://evil.example", "https://attacker.tld", "null",
    "https://example.com.evil.tld",
]

REDIRECT_PARAMS = [
    "next", "url", "redirect", "redir", "return", "returnUrl", "return_to",
    "goto", "dest", "destination", "continue", "callback", "redirect_uri",
    "redirect_url", "target", "rurl", "out", "view", "path", "u", "r", "u1",
]

SEC_HEADERS = [
    "strict-transport-security", "content-security-policy",
    "x-frame-options", "x-content-type-options", "referrer-policy",
    "permissions-policy", "cross-origin-opener-policy",
    "cross-origin-resource-policy", "x-xss-protection",
]

TECH_MAP = {
    # CMS / ecom
    "wordpress": "WordPress", "wp-content": "WordPress", "wp-includes": "WordPress",
    "drupal": "Drupal", "joomla": "Joomla", "typo3": "TYPO3", "prestashop": "PrestaShop",
    "magento": "Magento", "shopify": "Shopify", "woocommerce": "WooCommerce",
    "ghost": "Ghost", "strapi": "Strapi", "directus": "Directus",
    # backend frameworks (any language — not PHP-only)
    "laravel": "Laravel", "symfony": "Symfony", "codeigniter": "CodeIgniter",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "tornado": "Tornado",
    "rails": "Ruby on Rails", "sinatra": "Sinatra", "phoenix": "Phoenix",
    "spring": "Spring", "spring boot": "Spring Boot", "quarkus": "Quarkus",
    "express": "Express", "koa": "Koa", "nest.js": "NestJS", "nestjs": "NestJS",
    "next.js": "Next.js", "_next/static": "Next.js", "nuxt": "Nuxt",
    "remix": "Remix", "sveltekit": "SvelteKit", "astro": "Astro",
    "gin": "Gin (Go)", "echo": "Echo (Go)", "fiber": "Fiber (Go)",
    "actix": "Actix (Rust)", "axum": "Axum (Rust)",
    "dotnet": ".NET", "asp.net": "ASP.NET", "blazor": "Blazor",
    "fastcgi": "PHP-FPM", "php": "PHP",
    # frontend
    "react": "React", "angular": "Angular", "vue": "Vue", "svelte": "Svelte",
    "jquery": "jQuery", "bootstrap": "Bootstrap", "tailwind": "Tailwind",
    "gatsby": "Gatsby", "hugo": "Hugo", "jekyll": "Jekyll", "vuepress": "VuePress",
    # servers / proxies / CDN
    "nginx": "Nginx", "apache": "Apache", "iis": "IIS", "litespeed": "LiteSpeed",
    "openresty": "OpenResty", "caddy": "Caddy", "tomcat": "Tomcat",
    "jetty": "Jetty", "undertow": "Undertow", "gunicorn": "Gunicorn",
    "uvicorn": "Uvicorn", "hypercorn": "Hypercorn", "puma": "Puma",
    "unicorn": "Unicorn", "webrick": "WEBrick",
    "cloudflare": "Cloudflare", "akamai": "Akamai", "fastly": "Fastly",
    "incapsula": "Incapsula", "sucuri": "Sucuri", "barracuda": "Barracuda",
    "awselb": "AWS ELB", "google front end": "GFE", "cloudfront": "CloudFront",
    "varnish": "Varnish", "squid": "Squid", "haproxy": "HAProxy",
    # data / search / queue
    "elasticsearch": "Elasticsearch", "opensearch": "OpenSearch",
    "rabbitmq": "RabbitMQ", "kafka": "Kafka", "redis": "Redis",
    "memcached": "Memcached", "mongodb": "MongoDB",
    # ops / observability
    "grafana": "Grafana", "kibana": "Kibana", "jenkins": "Jenkins",
    "gitlab": "GitLab", "gitea": "Gitea", "bitbucket": "Bitbucket",
    "prometheus": "Prometheus", "jaeger": "Jaeger",
    # runtimes seen in headers / body
    "node": "Node.js", "deno": "Deno", "bun": "Bun", "python": "Python",
    "ruby": "Ruby", "perl": "Perl", "go": "Go", "rust": "Rust",
    "jvm": "JVM", "openjdk": "OpenJDK",
}

WAF_HINTS = [
    (re.compile(r"(?:cf-ray|cloudflare)", re.I), "Cloudflare"),
    (re.compile(r"x-sucuri-id|x-sucuri-cache", re.I), "Sucuri"),
    (re.compile(r"x-iinfo|x-cdn", re.I), "Incapsula/Imperva"),
    (re.compile(r"x-akamai|x-akamai-transformed|akamai", re.I), "Akamai"),
    (re.compile(r"server.*awselb|awselb|aws.?waf", re.I), "AWS ALB/WAF"),
    (re.compile(r"x-amz-cf-id|x-amz-cf-pop|cloudfront", re.I), "CloudFront"),
    (re.compile(r"x-azure-ref|x-msedge-ref|azure.?front.?door", re.I), "Azure Front Door"),
    (re.compile(r"x-cache-info|x-lbite", re.I), "ArvanCloud"),
    (re.compile(r"access-denied.*please contact.*waf|web application firewall", re.I), "Generic WAF"),
    (re.compile(r"mod_security|modsecurity|snort", re.I), "ModSecurity"),
    (re.compile(r"x-dotdefender", re.I), "dotDefender"),
    (re.compile(r"f5-bigip|bigipserver|bigip", re.I), "F5 BIG-IP ASM"),
    (re.compile(r"varnish", re.I), "Varnish"),
    (re.compile(r"x-sqreen|sqreen", re.I), "Sqreen"),
    (re.compile(r"server.*yundun|yundun", re.I), "Yundun"),
    (re.compile(r"x-firewall|wallarm", re.I), "Wallarm"),
    (re.compile(r"radware|x-rw-zone", re.I), "Radware"),
    (re.compile(r"protection.*duckduckgo|proofpoint", re.I), "Proofpoint"),
    (re.compile(r"cf-chl-|cf_clearance|__cfduid|challenge-platform", re.I), "Cloudflare Challenge"),
    (re.compile(r"incap_ses|visid_incap", re.I), "Imperva Session"),
    (re.compile(r"akamai.*bot|akamai.*manager", re.I), "Akamai Bot Mgr"),
]

# CAPTCHA / bot-challenge fingerprint (body + headers) — not always the same vendor
CAPTCHA_HINTS = [
    (re.compile(r"recaptcha/api|grecaptcha|google\.com/recaptcha", re.I), "reCAPTCHA"),
    (re.compile(r"hcaptcha\.com|h-captcha", re.I), "hCaptcha"),
    (re.compile(r"turnstile\.cloudflare|cf-turnstile", re.I), "Cloudflare Turnstile"),
    (re.compile(r"geetest|gee_cap", re.I), "GeeTest"),
    (re.compile(r"funcaptcha|arkoselabs|arkose", re.I), "FunCAPTCHA/Arkose"),
    (re.compile(r"captcha\.org|g-recaptcha-response", re.I), "Generic CAPTCHA"),
    (re.compile(r"checking your browser|just a moment|attention required|verify you are human",
                re.I), "Browser Challenge"),
    (re.compile(r"enable javascript and cookies|ddos protection|ddos-guard", re.I), "DDoS Guard"),
    (re.compile(r"press & hold|hold on|slide to verify|human verification", re.I), "Interactive Challenge"),
    (re.compile(r"captcha-container|cf-challenge|challenge-form", re.I), "Challenge Form"),
]


def detect_waf_captcha(text, headers):
    """Return (waf_list, captcha_list) from response body+headers. Multi-vendor, not fixed."""
    hdr_blob = " ".join(f"{k}:{v}" for k, v in (headers or {}).items())
    body = (text or "")[:80_000]
    blob = body + " " + hdr_blob
    wafs, captchas = [], []
    for rx, name in WAF_HINTS:
        if rx.search(blob):
            if name not in wafs:
                wafs.append(name)
    for rx, name in CAPTCHA_HINTS:
        if rx.search(blob):
            if name not in captchas:
                captchas.append(name)
    return wafs, captchas


def _is_challenge(r):
    """True if response is a bot-challenge / WAF block (not origin content)."""
    if r is None:
        return False
    if r.status_code in (403, 429, 503, 451, 200) or True:
        _, caps = detect_waf_captcha(r.text, r.headers)
        # challenge pages: captcha present OR known challenge status+body
        body_l = (r.text or "")[:20_000].lower()
        challenge_body = any(k in body_l for k in (
            "just a moment", "checking your browser", "attention required",
            "verify you are human", "cf-browser-verification", "challenge-platform",
            "enable javascript and cookies", "ddos protection",
        ))
        if caps or challenge_body:
            # 200 with only recaptcha widget on normal page ≠ block — require block-ish status or challenge phrases
            if r.status_code in (403, 429, 503, 451) or challenge_body or any(
                    c in ("Browser Challenge", "DDoS Guard", "Interactive Challenge", "Challenge Form", "Cloudflare Turnstile")
                    for c in caps):
                return True
    return False

SECRET_RE = [
    (re.compile(r"""(?i)(?:api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*['"][A-Za-z0-9_\-]{16,}['"]"""), "api_key"),
    (re.compile(r"""(?i)aws_(?:access_key_id|secret_access_key)\s*[:=]\s*['"][A-Z0-9]{16,}['"]"""), "aws_key"),
    (re.compile(r"""(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"""), "private_key"),
    (re.compile(r"""(?i)password\s*[:=]\s*['"][^'"]{4,}['"]"""), "password_literal"),
    (re.compile(r"""(?i)(?:authorization|bearer)\s*[:=]\s*['"](?:bearer\s+)?[A-Za-z0-9_\-\.]{20,}['"]"""), "auth_token"),
    (re.compile(r"""(?i)google[_-]?api[_-]?key\s*[:=]\s*['"][A-Za-z0-9_\-]{20,}['"]"""), "google_api_key"),
    (re.compile(r"""(?i)slack[_-]?token\s*[:=]\s*['"][ox]-[A-Za-z0-9\-]{10,}['"]"""), "slack_token"),
    (re.compile(r"""(?i)gh[pousr]_[A-Za-z0-9]{36,}"""), "github_token"),
    (re.compile(r"""(?i)(?:firebase|firebaseconfig)[^;]{0,80}apiKey['\"]?\s*[:=]\s*['"][A-Za-z0-9_\-]{20,}['"]"""), "firebase_key"),
    (re.compile(r"""(?i)eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"""), "jwt"),
]

EMAIL_RE = re.compile(r"""[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}""")
PHONE_RE = re.compile(r"""(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{3,4}""")
URL_RE = re.compile(r"""https?://[^\s'"<>\)]{6,200}""")
JS_URL_RE = re.compile(r"""['"](https?://[^'"]{8,200})['"]""")
JS_PATH_RE = re.compile(r"""['"](/[A-Za-z0-9_\-./]{2,80})['"]""")
JS_FETCH_RE = re.compile(r"""(?:fetch|axios\.(?:get|post|put)|\$\.(?:get|post))\(\s*['"]([^'"]+)['"]""")
PARAM_RE = re.compile(r"""[?&]([A-Za-z_][A-Za-z0-9_]{1,40})=""")
ROBOTS_PATH_RE = re.compile(r"""^(?:Allow|Disallow|Sitemap)\s*:\s*(\S+)""", re.I | re.M)
LOC_RE = re.compile(r"""<loc>\s*([^<\s]+)\s*</loc>""", re.I)
SOCIAL_RE = re.compile(
    r"""https?://(?:www\.)?(?:facebook|twitter|x|instagram|linkedin|youtube|tiktok|github|gitlab|medium|reddit|discord|t\.me|telegram\.me|wa\.me|linkedin)\.com/[A-Za-z0-9_./\-]+""",
    re.I,
)
DOMAIN_LIKE_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$"
)


# ── RATE GATE (5-10 req/s policy) + REDACTION + ADAPTIVE HTTP ──
MIN_REQ_INTERVAL = 0.12          # global throttle ≈ 8 req/s
_RATE_LOCK = threading.Lock()
_NEXT_SLOT = [0.0]

REDACT_PATTERNS = [
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._\-+/=]{16,}"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(authorization:\s*)(?:bearer|basic|token)?\s*[A-Za-z0-9._\-+/=]{8,}"), r"\1[REDACTED]"),
    # key=value / key: value — quoted or bare, any prefix (APP_SECRET=..., "password": "...")
    (re.compile(r"(?i)([A-Za-z0-9_]*(?:api[_-]?key|apikey|token|password|passwd|secret|pwd)"
                r"['\"]?\s*[:=]\s*['\"]?)([^\s'\"&,;]{4,})"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(cookie:\s*)[^\r\n]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(set-cookie:\s*)([^=;\r\n]+=)[^;\r\n]+"), r"\1\2[REDACTED]"),
    (re.compile(r"(?i)(eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,})"), "[REDACTED_JWT]"),
    (re.compile(r"(?i)\b(gh[pousr]_[A-Za-z0-9]{20,})"), "[REDACTED_GH_TOKEN]"),
    (re.compile(r"""(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"""),
     "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?i)\b(AKIA[0-9A-Z]{16})\b"), "[REDACTED_AWS_KEY]"),
]


def redact(text):
    """Evidence hygiene: strip secrets before any disk write."""
    if not text or not isinstance(text, str):
        return text
    for rx, rep in REDACT_PATTERNS:
        text = rx.sub(rep, text)
    return text


def throttle():
    """Global rate limiter — reserve a slot, sleep outside the lock."""
    with _RATE_LOCK:
        now = time.time()
        slot = _NEXT_SLOT[0]
        _NEXT_SLOT[0] = max(now, slot) + MIN_REQ_INTERVAL
    delay = slot - time.time()
    if delay > 0:
        time.sleep(delay)


def _do_get(s, url, timeout, allow_redirects, kw):
    throttle()
    try:
        return s.get(url, timeout=timeout, allow_redirects=allow_redirects, **kw)
    except Exception:
        return None


def safe_get(s, url, timeout=T, **kw):
    """GET with rate throttle + 429 backoff + multi-vector 403/challenge fallback.

    Adaptive, not fixed: on 403/challenge tries header-mutation → UA rotate →
    Referer/XFF once each (max 3 extra tries). Marks session-level block flag
    so later stages can stop overclaiming "not present".
    """
    allow_redirects = kw.pop("allow_redirects", True)
    allow_mutation = kw.pop("allow_mutation", True)
    r = _do_get(s, url, timeout, allow_redirects, kw)
    if r is None:
        return None

    # 429 → honor Retry-After (capped), exponential-ish retry once
    if r.status_code == 429:
        ra = (r.headers.get("Retry-After") or "").strip()
        delay = float(ra) if ra.isdigit() else 1.5
        time.sleep(min(delay, 5.0))
        r2 = _do_get(s, url, timeout, allow_redirects, kw)
        if r2 is not None:
            r = r2

    # challenge / 403 / 503 → multi-vector mutation (NOT a single fixed trick)
    blocked = _is_challenge(r) or r.status_code in (403, 429, 503, 451)
    if allow_mutation and blocked:
        try:
            p = up.urlparse(url)
            path = p.path or "/"
            base_hdrs = dict(kw.pop("headers", {}) or {})
            # vector rotation — different strategies, stop on first non-block
            vectors = [
                # 1) path/IP override headers
                {**base_hdrs,
                 "X-Original-URL": path, "X-Rewrite-URL": path,
                 "X-Forwarded-For": "127.0.0.1",
                 "X-Custom-IP-Authorization": "127.0.0.1"},
                # 2) browser-like UA + referer + accept-language
                {**base_hdrs,
                 "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/131.0.0.0 Safari/537.36"),
                 "Referer": f"{p.scheme}://{p.netloc}/",
                 "Accept-Language": "en-US,en;q=0.9",
                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                # 3) XFF chain + Origin
                {**base_hdrs,
                 "X-Forwarded-For": "10.0.0.1, 172.16.0.1, 192.168.1.1",
                 "X-Real-IP": "10.0.0.1",
                 "Origin": f"{p.scheme}://{p.netloc}"},
            ]
            for i, hdrs in enumerate(vectors, 1):
                r2 = _do_get(s, url, timeout, False, {**kw, "headers": hdrs})
                if r2 is None:
                    continue
                still_block = _is_challenge(r2) or r2.status_code in (403, 429, 503, 451)
                if not still_block:
                    log(f"mutation#{i} bypass → {r2.status_code} {path}", "!")
                    r = r2
                    blocked = False
                    break
                # keep last response for evidence even if still blocked
                r = r2
            if blocked or _is_challenge(r):
                # adaptive: flag for later stages — do NOT keep hammering
                _SESSION_BLOCK[0] = True
                log(f"challenge/WAF active on {path} — later absence claims → unconfirmed", "!")
        except Exception:
            pass
    elif blocked:
        _SESSION_BLOCK[0] = True
    return r


# session-level: True when origin is behind challenge → "not found" is unconfirmed
_SESSION_BLOCK = [False]


def log(msg, tag="*"):
    print(f"[{time.strftime('%H:%M:%S')}] [{tag}] {msg}", flush=True)


def section(title):
    w = 64
    print(f"\n{'='*w}\n  {title}\n{'='*w}", flush=True)


def _end_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def normalize_target(raw: str):
    raw = raw.strip()
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    parsed = up.urlparse(raw)
    host = parsed.hostname or raw
    path = parsed.path or ""
    base = f"{parsed.scheme}://{host}"
    if parsed.port and parsed.port not in (80, 443):
        base = f"{parsed.scheme}://{host}:{parsed.port}"
    if path and path != "/":
        base = base + path.rstrip("/")
    domainish = host[4:] if host.startswith("www.") else host
    return base, host, domainish


def http_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*"})
    s.verify = True  # TLS verification ON by default; opt out via --insecure
    s.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=20))
    s.mount("http://", requests.adapters.HTTPAdapter(pool_maxsize=20))
    return s


def add_endpoint(ctx, item, kind="path"):
    """Capped endpoint store — RAM safe."""
    if not item:
        return
    if len(ctx["endpoints"]) >= CAP_ENDPOINTS_STORE:
        return
    if kind == "url":
        try:
            p = up.urlparse(item)
            if p.path:
                item = p.path
            else:
                return
        except Exception:
            return
    ctx["endpoints"].add(item)


def is_valid_sub(host: str, domain: str) -> bool:
    if not host or "@" in host or " " in host:
        return False
    host = host.lower().strip().lstrip("*.")
    if not host.endswith(domain) and host != domain:
        # still allow parent domain itself
        if host != domain:
            return False
    return bool(DOMAIN_LIKE_RE.match(host))


# ═════════════════════════════════════════════
# STAGE 1 — HTTP
# ═════════════════════════════════════════════
def stage_http(ctx) -> dict:
    section("STAGE 1/14  HTTP · TECH · SECURITY · WAF")
    s = ctx["session"]
    base = ctx["base"]
    out = {"headers": {}, "security": {}, "tech": [], "waf": [], "extras": {}, "status": None}

    r = safe_get(s, base + "/", timeout=15)
    if not r:
        log("HTTP root unreachable", "!")
        return out
    out["status"] = r.status_code
    out["final_url"] = r.url
    log(f"GET {r.status_code}  {r.url}  ({len(r.content)} bytes)", ">")

    interesting = [
        "server", "x-powered-by", "x-aspnet-version", "x-generator",
        "x-drupal-cache", "x-amz-cf-pop", "cf-ray", "x-served-by",
        "via", "x-backend-server", "x-shopify-stage", "x-runway-id",
        "set-cookie", "location", "content-type", "x-request-id",
        "x-sucuri-id", "x-iinfo", "x-akamai-transformed", "alt-svc",
        "public-key-pins", "expect-ct", "report-to", "nel",
    ]
    hdr_blob = ""
    for h in interesting:
        if h in r.headers:
            v = r.headers[h][:300]
            out["headers"][h] = v
            hdr_blob += f" {h}:{v}"
            log(f"  {h}: {v[:120]}", "·")

    present, missing = [], []
    for h in SEC_HEADERS:
        if h in r.headers:
            present.append(f"{h}: {r.headers[h][:160]}")
        else:
            missing.append(h)
    out["security"] = {"present": present, "missing": missing}
    ctx["_sec_missing"] = missing
    log(f"security headers: {len(present)} present / {len(missing)} missing", "#" if missing else "+")

    # WAF + CAPTCHA/challenge sniff (multi-vendor, adaptive)
    wafs, captchas = detect_waf_captcha(r.text, hdr_blob and {k: v for k, v in out["headers"].items()} or r.headers)
    # merge header-only WAF hits
    for rx, name in WAF_HINTS:
        if rx.search(hdr_blob) and name not in wafs:
            wafs.append(name)
    out["waf"] = wafs
    out["captcha"] = captchas
    out["challenge"] = _is_challenge(r)
    if out["challenge"]:
        _SESSION_BLOCK[0] = True
    log(f"WAF/CDN: {', '.join(wafs) or 'none detected'}", "!" if wafs else "·")
    if captchas:
        log(f"CAPTCHA/challenge: {', '.join(captchas)}", "!")
    if out["challenge"]:
        log("origin behind bot-challenge — absence claims will be marked unconfirmed", "!")

    body = (r.text or "")[:400_000].lower()
    blob_tech = body + " " + hdr_blob.lower() + " " + " ".join(f"{k}:{v}" for k, v in r.headers.items()).lower()
    tech = sorted({v for k, v in TECH_MAP.items() if k in blob_tech})
    powered = r.headers.get("X-Powered-By", "")
    if powered and powered not in tech:
        tech.append(powered)
    server = r.headers.get("Server", "")
    if server and server not in tech:
        tech.append(server)
    out["tech"] = sorted(tech, key=str.lower)
    # case-dedupe
    seen_t = {}
    for t in out["tech"]:
        seen_t.setdefault(t.lower(), t)
    out["tech"] = list(seen_t.values())
    log(f"tech: {', '.join(out['tech']) or 'unknown'}", "+")

    cookies = [
        {"name": c.name, "value": (c.value[:60] + ("…" if len(c.value) > 60 else "")),
         "secure": c.secure, "httponly": bool(c.has_nonstandard_attr("HttpOnly")),
         "samesite": c.get_nonstandard_attr("SameSite")}
        for c in s.cookies
    ]
    sc = r.headers.get("Set-Cookie", "")
    out["extras"]["set_cookie"] = sc[:400] if sc else ""
    out["extras"]["cookies"] = cookies
    if cookies:
        log(f"cookies: {', '.join(c['name'] for c in cookies)}", "·")

    # harvest emails/social from root HTML (quick)
    html = r.text or ""
    for m in EMAIL_RE.findall(html):
        ctx["emails"].add(m.lower())
    for m in SOCIAL_RE.findall(html):
        ctx["social"].add(m)
    for m in URL_RE.findall(html):
        try:
            h = up.urlparse(m).hostname or ""
            if h and h != ctx["host"]:
                if h.endswith("." + ctx["domainish"]) or h == ctx["domainish"]:
                    ctx["related_hosts"].add(h.lower())
                elif not any(x in h for x in ("w3.org", "schema.org", "google", "gstatic", "jquery", "cloudflare")):
                    ctx["external_urls"].add(m[:200])
        except Exception:
            pass

    for name, path in [
        ("robots", "/robots.txt"),
        ("sitemap", "/sitemap.xml"),
        ("security_txt", "/.well-known/security.txt"),
        ("crossdomain", "/crossdomain.xml"),
        ("favicon", "/favicon.ico"),
        ("humans", "/humans.txt"),
        ("ads", "/ads.txt"),
        ("manifest", "/manifest.json"),
        ("security_root", "/security.txt"),
    ]:
        rr = safe_get(s, base + path, timeout=10)
        if rr is not None:
            code = rr.status_code
            ln = len(rr.content)
            preview = (rr.text or "")[:150].replace("\n", " ").strip()
            out["extras"][name] = {"status": code, "len": ln, "preview": preview if code < 400 else ""}
            if code == 200 and ln > 0:
                log(f"{path} → 200 ({ln}b) {preview[:80]}", "+")
                if name in ("robots", "sitemap", "security_txt", "humans", "manifest"):
                    ctx["artifacts"][name] = rr.text[:50_000]
                # emails/social from these too
                for m in EMAIL_RE.findall(rr.text or ""):
                    ctx["emails"].add(m.lower())
            else:
                log(f"{path} → {code} ({ln}b)", "·")
        else:
            out["extras"][name] = {"status": "ERR", "len": 0}
            log(f"{path} → ERR", "!")

    # favicon hash (mmh3 optional, else sha1)
    fav = safe_get(s, base + "/favicon.ico", timeout=8)
    if fav and fav.status_code == 200 and fav.content:
        import hashlib
        out["extras"]["favicon_sha1"] = hashlib.sha1(fav.content).hexdigest()
        log(f"favicon sha1: {out['extras']['favicon_sha1']}", "+")

    eps = 0
    for m in re.findall(r"""["'](/[\w./\-]{2,80})["']""", r.text or ""):
        if not m.startswith("//"):
            add_endpoint(ctx, m)
            eps += 1
    log(f"inline endpoints: {len(ctx['endpoints'])} (this page +{eps})", "+")
    return out


# ═════════════════════════════════════════════
# STAGE 2 — DNS
# ═════════════════════════════════════════════
def _dns_google(name: str, rtype: str) -> list:
    try:
        r = requests.get(
            "https://dns.google/resolve",
            params={"name": name, "type": rtype},
            timeout=6,
            headers={"Accept": "application/dns-json"},
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return [a.get("data", "") for a in data.get("Answer", []) if a.get("data")]
    except Exception:
        return []


def stage_dns(ctx) -> dict:
    section("STAGE 2/14  DNS RECORDS")
    domain = ctx["domainish"]
    host = ctx["host"]
    out = {}
    types = ["A", "AAAA", "MX", "NS", "TXT", "CAA", "CNAME", "SOA"]

    def q(rt):
        return rt, _dns_google(domain, rt)

    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        for rt, ans in ex.map(q, types):
            if ans:
                out[rt] = ans[:20]
                log(f"{rt:5} ({len(ans)}): {ans[0][:90]}", "+")
            else:
                log(f"{rt:5} —", "·")

    if host != domain:
        a = _dns_google(host, "A")
        if a:
            out["HOST_A"] = a
            log(f"host A: {a}", "+")

    for label, name in [
        ("dmarc", f"_dmarc.{domain}"),
        ("spf", domain),
        ("dkim", f"default._domainkey.{domain}"),
        ("mtasts", f"_mta-sts.{domain}"),
        ("dane", f"_443._tcp.{domain}"),
    ]:
        txts = _dns_google(name, "TXT")
        if txts:
            out[f"TXT_{label}"] = txts[:5]
            log(f"{label}: {txts[0][:100]}", "+")

    try:
        ips = socket.getaddrinfo(host, None)
        uniq = sorted({i[4][0] for i in ips})
        out["RESOLVED"] = uniq
        ctx["resolved_ips"] = uniq
        log(f"resolver: {uniq}", "+")
    except Exception as e:
        log(f"resolver fail: {e}", "!")
    return out


# ═════════════════════════════════════════════
# STAGE 3 — CERT (related sites via SAN)
# ═════════════════════════════════════════════
def stage_cert(ctx) -> dict:
    section("STAGE 3/14  TLS CERT · SAN → RELATED HOSTS")
    host = ctx["host"]
    domain = ctx["domainish"]
    out = {"issuer": None, "subject": None, "san": [], "related": [], "not_before": None, "not_after": None}

    def _peer(hostname, port=443):
        ctxssl = ssl.create_default_context()
        ctxssl.check_hostname = False
        ctxssl.verify_mode = ssl.CERT_NONE
        with socket.create_connection((hostname, port), timeout=8) as sock:
            with ctxssl.wrap_socket(sock, server_hostname=hostname) as ssock:
                return ssock.getpeercert(binary_form=False) or {}, ssock.getpeercert()

    # binary_form=False with CERT_NONE may return empty dict — use _test_decode or openssl-less approach
    try:
        # Python can decode via ssl if verify off using getpeercert(True) + _ssl
        raw = None
        try:
            import ssl as _ssl
            ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_NONE
            with socket.create_connection((host, 443), timeout=8) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    der = ssock.getpeercert(binary_form=True)
            # decode with cryptography if present
            try:
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                cert = x509.load_der_x509_certificate(der, default_backend())
                # SAN
                try:
                    ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                    names = list(ext.value.get_values_for_type(x509.DNSName))
                    out["san"] = names[:CAP_RELATED]
                    log(f"cert SAN: {len(names)} names", "+")
                except Exception:
                    pass
                try:
                    out["issuer"] = cert.issuer.rfc4514_string()[:200]
                    out["subject"] = cert.subject.rfc4514_string()[:200]
                    out["not_before"] = cert.not_valid_before_utc.isoformat()
                    out["not_after"] = cert.not_valid_after_utc.isoformat()
                    log(f"issuer: {out['issuer']}", "·")
                    log(f"subject: {out['subject']}", "·")
                    log(f"validity: {out['not_before']} → {out['not_after']}", "·")
                except Exception:
                    pass
            except ImportError:
                # fallback: ssl._ssl if available
                log("cryptography not installed — using ssl.decode if available", "!")
                try:
                    # pyOpenSSL alternative skip
                    pass
                except Exception:
                    pass
        except Exception as e:
            log(f"TLS connect fail: {e}", "!")
            return out
    except Exception as e:
        log(f"cert stage error: {e}", "!")
        return out

    # related hosts from SAN (same cert = often same org / other properties)
    related = []
    for name in out["san"]:
        n = name.lower().lstrip("*.")
        if not n:
            continue
        if n == domain or n.endswith("." + domain):
            if n != host:
                related.append(n)
                ctx["related_hosts"].add(n)
        else:
            # different domain entirely — "other sites"
            related.append(n)
            ctx["other_sites"].add(n)
            if DOMAIN_LIKE_RE.match(n):
                ctx["related_hosts"].add(n)
    out["related"] = sorted(set(related))[:CAP_RELATED]
    log(f"related/other from SAN: {len(out['related'])}", "#" if out["related"] else "·")
    for n in out["related"][:25]:
        log(f"  {n}", ">")
    return out


# ═════════════════════════════════════════════
# STAGE 4 — SUBDOMAINS
# ═════════════════════════════════════════════
def stage_subs(ctx) -> dict:
    section("STAGE 4/14  SUBDOMAIN DISCOVERY (multi-source, capped)")
    domain = ctx["domainish"]
    subs: set = set()
    out = {"sources": {}}
    deep = ctx["deep"]

    def keep(names, source):
        kept = 0
        for n in names:
            n = (n or "").strip().lower().lstrip("*.")
            if n and is_valid_sub(n, domain) and n not in subs:
                if len(subs) >= CAP_SUBS:
                    break
                # strip wildcard noise
                if n.startswith("*."):
                    n = n[2:]
                if DOMAIN_LIKE_RE.match(n) and (n == domain or n.endswith("." + domain)):
                    subs.add(n)
                    kept += 1
        out["sources"][source] = kept
        log(f"{source}: +{kept} (total {len(subs)}/{CAP_SUBS})", "+" if kept else "·")

    # crt.sh
    try:
        r = requests.get(
            f"https://crt.sh/?q=%.{domain}&output=json",
            timeout=25, headers={"User-Agent": UA},
        )
        names = set()
        if r.status_code == 200 and r.text.strip().startswith("["):
            for row in r.json():
                nm = (row.get("name_value") or "")
                for part in nm.splitlines():
                    part = part.strip().lower().lstrip("*.")
                    if part and "@" not in part and " " not in part:
                        names.add(part)
            keep(names, "crt.sh")
        else:
            out["sources"]["crt.sh"] = f"HTTP {r.status_code}"
            log(f"crt.sh: HTTP {r.status_code}", "!")
        del r, names
    except Exception as e:
        out["sources"]["crt.sh"] = f"ERR {type(e).__name__}"
        log(f"crt.sh: {e}", "!")

    # hackertarget (free, light)
    if deep or len(subs) < 20:
        try:
            r = requests.get(
                f"https://api.hackertarget.com/hostsearch/?q={domain}",
                timeout=15, headers={"User-Agent": UA},
            )
            if r.status_code == 200 and "error" not in r.text[:80].lower():
                names = {ln.split(",")[0].strip().lower() for ln in r.text.splitlines() if "," in ln}
                keep(names, "hackertarget")
            else:
                out["sources"]["hackertarget"] = "unavailable"
                log("hackertarget: unavailable/limit", "·")
            del r
        except Exception as e:
            out["sources"]["hackertarget"] = f"ERR {type(e).__name__}"
            log(f"hackertarget: {e}", "!")

    # wayback domain (batched)
    try:
        r = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={"url": f"*.{domain}", "output": "json", "fl": "original",
                    "collapse": "urlkey", "limit": "2500"},
            timeout=30, headers={"User-Agent": UA},
        )
        found = set()
        if r.status_code == 200 and r.text.strip().startswith("["):
            rows = r.json()[1:]
            for row in rows[:CAP_WAYBACK]:
                try:
                    h = up.urlparse(row[0]).hostname
                    if h:
                        found.add(h.lower())
                except Exception:
                    pass
            keep(found, "wayback")
        else:
            out["sources"]["wayback"] = f"HTTP {r.status_code}"
            log(f"wayback-subs: HTTP {r.status_code}", "!")
        del r, found
    except Exception as e:
        out["sources"]["wayback"] = f"ERR {type(e).__name__}"
        log(f"wayback-subs: {e}", "!")

    # bufferover TLS (if deep)
    if deep:
        try:
            r = requests.get(
                f"https://tls.bufferover.run/dns?q=.{'.'.join(domain.split('.')[-2:])}",
                timeout=15, headers={"User-Agent": UA},
            )
            if r.status_code == 200:
                data = r.json()
                names = set()
                for row in data.get("Results", []) or []:
                    # format: "ip,host"
                    parts = str(row).split(",")
                    if len(parts) >= 2:
                        names.add(parts[1].strip().lower())
                keep(names, "bufferover")
            del r
        except Exception as e:
            out["sources"]["bufferover"] = f"ERR {type(e).__name__}"
            log(f"bufferover: {e}", "!")

    # subfinder binary
    if shutil.which("subfinder"):
        try:
            p = subprocess.run(
                ["subfinder", "-d", domain, "-silent", "-timeout", "20"],
                capture_output=True, text=True, timeout=60,
            )
            names = {ln.strip().lower() for ln in p.stdout.splitlines() if ln.strip()}
            keep(names, "subfinder")
            del p, names
        except Exception as e:
            out["sources"]["subfinder"] = f"ERR {type(e).__name__}"
            log(f"subfinder: {e}", "!")
    else:
        out["sources"]["subfinder"] = "not-installed"
        log("subfinder: not on PATH (skip)", "·")

    # ── KOMPLEKS v2: parallel extra sources (OTX + anubis + rapidDNS + brute+permutasi) ──
    # Semua jalan paralel biar cepat, timeout pendek, tetap capped RAM-aman.
    def _fetch_otx():
        try:
            r = requests.get(
                f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
                timeout=15, headers={"User-Agent": UA},
            )
            if r.status_code == 200:
                names = {row.get("hostname", "").strip().lower()
                         for row in r.json().get("passive_dns", []) or []}
                return names
        except Exception as e:
            return e
        return set()

    def _fetch_anubis():
        try:
            r = requests.get(
                f"https://jldc.me/anubis/subdomains/{domain}",
                timeout=15, headers={"User-Agent": UA},
            )
            if r.status_code == 200 and r.text.strip().startswith("["):
                try:
                    return {str(x).strip().lower() for x in r.json() if x}
                except Exception:
                    pass
        except Exception as e:
            return e
        return set()

    def _fetch_rapiddns():
        try:
            r = requests.get(
                f"https://rapiddns.io/subdomain/{domain}?full=1",
                timeout=15, headers={"User-Agent": "Mozilla/5.0"},
            )
            if r.status_code == 200:
                return set(re.findall(r"([a-z0-9][a-z0-9\-\.]*\." + re.escape(domain) + r")",
                                      r.text.lower()))
        except Exception as e:
            return e
        return set()

    _BRUTE_PREFIXES = [
        "www", "mail", "api", "dev", "staging", "prod", "test", "uat", "qa",
        "admin", "portal", "app", "web", "vpn", "ftp", "smtp", "owa", "exchange",
        "intranet", "internal", "beta", "alpha", "demo", "sandbox", "cdn",
        "static", "assets", "img", "media", "blog", "shop", "store", "pay",
        "billing", "support", "help", "docs", "status", "monitor", "grafana",
        "jenkins", "git", "gitlab", "jira", "confluence", "ldap", "sso",
        "auth", "login", "oauth", "idp", "adfs", "rds", "remote", "citrix",
        "db", "sql", "mongo", "redis", "kafka", "elastic", "kibana",
        "api-dev", "api-staging", "api-prod", "admin-dev", "v1", "v2",
        "mobile", "m", "gateway", "proxy", "lb", "k8s", "cluster",
    ]

    def _dns_brute_permut():
        found = set()
        cands = {f"{p}.{domain}" for p in _BRUTE_PREFIXES}
        # permutasi env dari subs yang sudah ketemu (biar kompleks, tetap capped)
        seed = list(subs)[:60]
        for s in seed:
            try:
                label = s.split(".")[0]
                for env in ("dev-", "staging-", "prod-", "test-", "uat-", "new-", "old-"):
                    cands.add(f"{env}{label}.{domain}")
                    if len(cands) >= 220:
                        break
            except Exception:
                pass
            if len(cands) >= 220:
                break
        def _resolve(h):
            try:
                socket.setdefaulttimeout(3)
                socket.gethostbyname(h)
                return h
            except Exception:
                return None
        try:
            with cf.ThreadPoolExecutor(max_workers=min(ctx.get("threads", 10), 20)) as ex:
                for h in ex.map(_resolve, sorted(cands)):
                    if h and len(subs) + len(found) < CAP_SUBS:
                        found.add(h)
        except Exception:
            pass
        return found

    try:
        with cf.ThreadPoolExecutor(max_workers=4) as ex:
            f_otx = ex.submit(_fetch_otx)
            f_anubis = ex.submit(_fetch_anubis)
            f_rapid = ex.submit(_fetch_rapiddns)
            f_brute = ex.submit(_dns_brute_permut)
            for name, fut in (("otx", f_otx), ("anubis", f_anubis),
                              ("rapiddns", f_rapid), ("brute+permut", f_brute)):
                try:
                    res = fut.result(timeout=40)
                    if isinstance(res, Exception):
                        out["sources"][name] = f"ERR {type(res).__name__}"
                    elif res:
                        keep(res, name)
                    else:
                        out["sources"].setdefault(name, 0)
                except Exception as e:
                    out["sources"][name] = f"ERR {type(e).__name__}"
    except Exception as e:
        log(f"parallel-subs: {e}", "!")

    # prioritas celah: score subs menarik (admin/api/dev/staging/prod/internal) biar cepat ke target empuk
    _HOT = re.compile(r"(admin|api|dev|stag|prod|test|uat|qa|internal|intranet|vpn|jenkins|git|jira|grafana|kibana|elastic|sso|auth|login|portal|beta|demo|sandbox|backup|old|legacy|db|sql|mongo)", re.I)
    try:
        ranked = sorted(subs, key=lambda h: (0 if _HOT.search(h or "") else 1, h or ""))
        # taruh hot di depan ctx agar probe duluan kena yang empuk
        ctx["subdomains_hot"] = [h for h in ranked if _HOT.search(h or "")][:80]
    except Exception:
        ctx["subdomains_hot"] = []

    # merge cert SAN + related
    for n in ctx["related_hosts"]:
        if is_valid_sub(n, domain) and n not in subs and len(subs) < CAP_SUBS:
            subs.add(n)
    out["sources"]["cert_related"] = len(subs)

    # always apex + www
    for x in (domain, f"www.{domain}"):
        if x not in subs and len(subs) < CAP_SUBS:
            subs.add(x)

    # merge into other_sites same-parent
    for n in subs:
        if n != domain and not n.endswith("." + domain):
            ctx["other_sites"].add(n)

    ctx["subdomains"] = sorted(subs)
    out["total"] = len(subs)
    out["list"] = sorted(subs)
    log(f"total unique subdomains: {len(subs)} (cap {CAP_SUBS})", "#")
    for x in sorted(subs)[:40]:
        log(f"  {x}", ">")
    if len(subs) > 40:
        log(f"  … +{len(subs)-40} more", ">")
    return out


# ═════════════════════════════════════════════
# STAGE 5 — LIVE PROBE (httpx)
# ═════════════════════════════════════════════
def stage_probe(ctx) -> dict:
    section("STAGE 5/14  LIVE HOST PROBE (bounded, hot-first)")
    # hot-first: subs menarik (admin/api/dev/dll) diprobe duluan biar cepat ketemu celah
    _hot = ctx.get("subdomains_hot") or []
    _rest = [h for h in ctx.get("subdomains", []) if h not in set(_hot)]
    subs = (_hot + _rest)[:CAP_SUBS]
    out = {"tool": None, "live": [], "count": 0}
    if not subs:
        log("no subdomains to probe", "·")
        return out

    # ProjectDiscovery httpx preferred — detect (PATH may hold Python httpx CLI)
    pd_httpx = None
    if shutil.which("httpx"):
        try:
            probe = subprocess.run(
                ["httpx", "-version"],
                capture_output=True, text=True, timeout=5,
            )
            blob = (probe.stdout or "") + (probe.stderr or "")
            if re.search(r"projectdiscovery|httpx v", blob, re.I):
                pd_httpx = True
            elif re.search(r"usage: httpx \[OPTIONS\]|No such option|httpx is a package", blob, re.I):
                pd_httpx = False
            else:
                # try -l flag
                t2 = subprocess.run(
                    ["httpx", "-h"],
                    capture_output=True, text=True, timeout=5,
                )
                hblob = (t2.stdout or "") + (t2.stderr or "")
                pd_httpx = bool(re.search(r"-l, --list|-l string", hblob))
        except Exception:
            pd_httpx = False

    if pd_httpx:
        out["tool"] = "httpx-pd"
        inp = ctx["outdir"] / "_probe_in.txt"
        inp.write_text("\n".join(subs), encoding="utf-8")
        try:
            cmd = [
                "httpx", "-l", str(inp), "-silent", "-json",
                "-threads", str(min(ctx["threads"], 16)),
                "-timeout", "6", "-maxr", "1", "-fr", "-status-code",
                "-title", "-tech-detect", "-web-server",
            ]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            live = []
            for ln in p.stdout.splitlines():
                ln = ln.strip()
                if not ln.startswith("{"):
                    continue
                try:
                    j = json.loads(ln)
                except Exception:
                    continue
                entry = {
                    "url": j.get("url") or j.get("input"),
                    "status": j.get("status_code"),
                    "title": (j.get("title") or "")[:120],
                    "tech": (j.get("tech") or [])[:12],
                    "server": j.get("webserver") or j.get("server"),
                    "cname": j.get("cname") or "",
                }
                live.append(entry)
                if entry["url"]:
                    ctx["live_hosts"].add(entry["url"])
                for t in entry["tech"]:
                    if t:
                        ctx.setdefault("_probe_tech", set()).add(str(t))
                if entry["status"] and int(entry["status"]) < 400:
                    log(f"LIVE {entry['status']} {entry['url']} {entry['title'][:50]}", "+")
            out["live"] = live[:CAP_SUBS]
            out["count"] = len(out["live"])
            log(f"httpx-pd live: {out['count']}/{len(subs)}", "#")
            inp.unlink(missing_ok=True)
        except Exception as e:
            log(f"httpx-pd failed: {e}", "!")
            out["tool"] = f"ERR {type(e).__name__}"
            pd_httpx = False
        if pd_httpx and out.get("count") is not None:
            # if binary path failed mid-way fall through only when tool set ERR
            if not str(out["tool"]).startswith("ERR"):
                return out

    # fallback: python HEAD/GET bounded (always works)
    out["tool"] = "python-requests"
    s = ctx["session"]
    live = []

    def check(h):
        for scheme in ("https", "http"):
            url = f"{scheme}://{h}"
            r = safe_get(s, url, timeout=6, allow_redirects=True)
            if r is not None:
                return {
                    "url": r.url,
                    "status": r.status_code,
                    "title": (re.search(r"<title[^>]*>([^<]+)", r.text or "", re.I) or [None, ""])[1][:120] if r.text else "",
                    "tech": [],
                    "server": r.headers.get("Server", ""),
                    "cname": "",
                }
        return None

    with cf.ThreadPoolExecutor(max_workers=min(ctx["threads"], 16)) as ex:
        futs = [ex.submit(check, h) for h in subs]
        for f in cf.as_completed(futs):
            try:
                e = f.result()
            except Exception:
                e = None
            if e:
                live.append(e)
                if e["url"]:
                    ctx["live_hosts"].add(e["url"])
                if e["status"] and e["status"] < 400:
                    log(f"LIVE {e['status']} {e['url']}", "+")
    out["live"] = live
    out["count"] = len(live)
    log(f"python live: {out['count']}/{len(subs)}", "#")
    return out


# ═════════════════════════════════════════════
# STAGE 6 — PATHS
# ═════════════════════════════════════════════
def stage_paths(ctx) -> dict:
    section("STAGE 6/14  SENSITIVE PATH PROBE")
    s = ctx["session"]
    base = ctx["base"]
    threads = ctx["threads"]
    paths = SENSITIVE_PATHS[:CAP_PATHS_FAST] if ctx["fast"] else SENSITIVE_PATHS[:CAP_PATHS]
    # merge robots-derived
    for p in ctx.get("robots_paths", [])[:20]:
        if p.startswith("/") and p not in paths:
            paths.append(p)
    hits = []

    host = ctx["host"]

    def probe(path):
        url = base + path if path.startswith("/") else base + "/" + path
        r = safe_get(s, url, timeout=7, allow_redirects=False, allow_mutation=True)
        if r is None:
            return path, None, 0, "", "", None
        code, ln = r.status_code, len(r.content)
        evidence = None
        # capture raw HTTP proof for non-boring responses (zero-false-positive gate)
        if code not in (404, 400, 405, None):
            try:
                req_lines = [
                    f"GET {path} HTTP/1.1",
                    f"Host: {host}",
                    f"User-Agent: {UA[:60]}",
                    "Accept: */*",
                ]
                resp_hdrs = "\n".join(f"{k}: {v}" for k, v in list(r.headers.items())[:40])
                body_snip = (r.text or "")[:600]
                evidence = {
                    "url": url,
                    "request": "\n".join(req_lines),
                    "response": f"HTTP/1.1 {code} {getattr(r, 'reason', '')}\n{resp_hdrs}\n\n{body_snip}",
                }
            except Exception:
                evidence = None
        return path, code, ln, r.headers.get("Content-Type", ""), r.headers.get("Location", ""), evidence

    done = 0
    with cf.ThreadPoolExecutor(max_workers=threads) as ex:
        futs = [ex.submit(probe, p) for p in paths]
        for f in cf.as_completed(futs):
            path, code, ln, ctype, loc, evidence = f.result()
            done += 1
            if code and code not in (404, 400, 405):
                if code in (200, 204, 301, 302, 307, 401, 403, 500) and (ln != 0 or code in (401, 403)):
                    entry = {"path": path, "status": code, "len": ln, "type": ctype[:60],
                             "location": loc[:160]}
                    if evidence:
                        entry["evidence"] = evidence
                        entry["url"] = evidence.get("url")
                    hits.append(entry)
                    add_endpoint(ctx, path)
                    log(f"{code} {path} ({ln}b)" + (f" → {loc}" if loc else ""),
                        "!" if code in (200, 500) else "+")
            if done % 25 == 0:
                log(f"progress {done}/{len(paths)}", "·")

    hits.sort(key=lambda h: (0 if h["status"] == 200 else 1, h["path"]))
    log(f"interesting paths: {len(hits)} / {len(paths)} probed", "#" if hits else "·")
    return {"probed": len(paths), "hits": hits}


# ═════════════════════════════════════════════
# STAGE 7 — ROBOTS / SITEMAP DEEP
# ═════════════════════════════════════════════
def stage_robots(ctx) -> dict:
    section("STAGE 7/14  ROBOTS + SITEMAP DEEP PARSE")
    s = ctx["session"]
    base = ctx["base"]
    out = {"robots_paths": [], "sitemaps": [], "sitemaps_urls": [], "disallowed": []}
    ctx["robots_paths"] = []

    robots = ctx["artifacts"].get("robots") or ""
    if not robots:
        rr = safe_get(s, base + "/robots.txt", timeout=8)
        if rr and rr.status_code == 200:
            robots = rr.text or ""
    if robots:
        paths = []
        for m in ROBOTS_PATH_RE.finditer(robots):
            val = m.group(1).strip()
            if val.startswith("http"):
                out["sitemaps"].append(val)
            elif val.startswith("/"):
                paths.append(val)
                # interesting disallow
                low = val.lower()
                if any(k in low for k in ("admin", "api", "internal", "debug", "backup", "upload", "private", "staging", "test", ".git", "config")):
                    out["disallowed"].append(val)
        out["robots_paths"] = sorted(set(paths))[:80]
        ctx["robots_paths"] = out["robots_paths"]
        log(f"robots paths: {len(out['robots_paths'])} (interesting disallow: {len(out['disallowed'])})",
            "!" if out["disallowed"] else "+")
        for p in out["disallowed"][:20]:
            log(f"  DISALLOW {p}", "!")
    else:
        log("no robots.txt", "·")

    # sitemaps from robots + default
    sitemaps = list(out["sitemaps"])
    if not sitemaps:
        sitemaps = [base + "/sitemap.xml"]
    seen_loc = set()
    for sm in sitemaps[:5]:
        rr = safe_get(s, sm, timeout=10)
        if not rr or rr.status_code != 200:
            continue
        body = rr.text or ""
        locs = LOC_RE.findall(body)
        if not locs:
            # try json sitemap or plain list
            locs = re.findall(r"https?://[^\s\"'<>]+", body)[:50]
        out["sitemaps"].append(sm) if sm not in out["sitemaps"] else None
        for u in locs[:200]:
            if u in seen_loc:
                continue
            seen_loc.add(u)
            out["sitemaps_urls"].append(u)
            try:
                p = up.urlparse(u)
                if p.path:
                    add_endpoint(ctx, p.path)
            except Exception:
                pass
        # harvest emails/social from sitemap? unlikely but cheap
        for m in EMAIL_RE.findall(body):
            ctx["emails"].add(m.lower())
        log(f"sitemap {up.urlparse(sm).path}: +{len(locs)} urls", "+")
    out["sitemaps_urls"] = out["sitemaps_urls"][:500]
    log(f"sitemap urls total: {len(out['sitemaps_urls'])}", "+")
    return out


# ═════════════════════════════════════════════
# STAGE 8 — JS
# ═════════════════════════════════════════════
def stage_js(ctx) -> dict:
    section("STAGE 8/14  JS ENDPOINT + SECRET + LIB MINING")
    s = ctx["session"]
    base = ctx["base"]
    out = {"scripts": [], "endpoints": [], "secrets": [], "apis": [], "libs": []}

    # also mine JS linked from live hosts (few)
    pages = [base + "/"]
    for u in list(ctx["live_hosts"])[:3]:
        pages.append(u if u.endswith("/") else u + "/")

    abs_scripts = []
    inline_count = 0
    for page in pages[:4]:
        r = safe_get(s, page, timeout=10)
        if not r:
            continue
        scripts = re.findall(r"""<script[^>]+src=["']([^"']+)["']""", r.text or "", re.I)
        for sc in scripts:
            abs_scripts.append(up.urljoin(r.url, sc))
        inline = re.findall(r"<script(?![^>]+src=)[^>]*>(.*?)</script>", r.text or "", re.I | re.S)
        inline_count += len(inline)
        for blk in inline:
            # process inline without storing all
            for rx, label in SECRET_RE:
                for hit in rx.findall(blk):
                    if isinstance(hit, tuple):
                        hit = hit[0]
                    out["secrets"].append({"type": label, "match": str(hit)[:120]})
            for m in JS_PATH_RE.findall(blk):
                if any(x in m for x in ("/api", "/v1", "/graphql", "/admin", "/auth", "/user", "/internal")):
                    out["apis"].append(m)
                add_endpoint(ctx, m)
            for m in EMAIL_RE.findall(blk):
                ctx["emails"].add(m.lower())
        del r, inline

    # dedupe scripts, cap
    abs_scripts = list(dict.fromkeys(abs_scripts))[:CAP_JS]
    out["scripts"] = abs_scripts
    log(f"scripts: {len(abs_scripts)} external, {inline_count} inline blocks", "+")

    def fetch_js(u):
        try:
            rr = s.get(u, timeout=8)
            if rr.status_code == 200:
                return u, (rr.text or "")[:400_000]
        except Exception:
            pass
        return u, ""

    with cf.ThreadPoolExecutor(max_workers=min(8, ctx["threads"])) as ex:
        for u, txt in ex.map(fetch_js, abs_scripts):
            if not txt:
                continue
            log(f"  fetched …{up.urlparse(u).path[-50:]} ({len(txt)}b)", ">")
            # libs versions
            for lib_rx in [
                (re.compile(r"jquery[.-](\d+\.\d+(?:\.\d+)?)", re.I), "jQuery"),
                (re.compile(r"bootstrap[.-](\d+\.\d+(?:\.\d+)?)", re.I), "Bootstrap"),
                (re.compile(r"react[.-](\d+\.\d+(?:\.\d+)?)", re.I), "React"),
                (re.compile(r"vue[.@/-](\d+\.\d+(?:\.\d+)?)", re.I), "Vue"),
                (re.compile(r"angular[.-](\d+\.\d+(?:\.\d+)?)", re.I), "Angular"),
                (re.compile(r"lodash[.-](\d+\.\d+(?:\.\d+)?)", re.I), "Lodash"),
                (re.compile(r"axios[.-](\d+\.\d+(?:\.\d+)?)", re.I), "Axios"),
                (re.compile(r"webpack[.-](\d+\.\d+(?:\.\d+)?)", re.I), "Webpack"),
            ]:
                m = lib_rx[0].search(txt)
                if m:
                    out["libs"].append({"name": lib_rx[1], "version": m.group(1)})
            for rx, label in SECRET_RE:
                for hit in rx.findall(txt):
                    if isinstance(hit, tuple):
                        hit = hit[0]
                    out["secrets"].append({"type": label, "match": str(hit)[:120]})
            for m in JS_PATH_RE.findall(txt):
                if any(x in m for x in ("/api", "/v1", "/v2", "/graphql", "/admin", "/auth",
                                         "/user", "/account", "/internal", "/debug", "/upload")):
                    out["apis"].append(m)
                add_endpoint(ctx, m)
            for m in JS_FETCH_RE.findall(txt):
                out["apis"].append(m)
            for m in JS_URL_RE.findall(txt):
                try:
                    ph = up.urlparse(m).hostname or ""
                    if ph and ph not in (ctx["host"],) and not ph.endswith(ctx["domainish"]):
                        if ph not in ("w3.org",):
                            ctx["external_urls"].add(m[:200])
                    else:
                        out["apis"].append(up.urlparse(m).path or m)
                except Exception:
                    pass
            for m in EMAIL_RE.findall(txt):
                ctx["emails"].add(m.lower())
            del txt

    # dedupe
    out["apis"] = sorted(set(out["apis"]))[:400]
    out["endpoints"] = sorted({a for a in out["apis"] if a.startswith("/")})[:400]
    seen_s, uniq_s = set(), []
    for sec in out["secrets"]:
        k = (sec["type"], sec["match"])
        if k not in seen_s:
            seen_s.add(k)
            uniq_s.append(sec)
    out["secrets"] = uniq_s[:50]
    seen_l, uniq_l = set(), []
    for lib in out["libs"]:
        k = (lib["name"], lib["version"])
        if k not in seen_l:
            seen_l.add(k)
            uniq_l.append(lib)
    out["libs"] = uniq_l

    log(f"js endpoints: {len(out['endpoints'])}  api-like: {len(out['apis'])}  "
        f"secrets: {len(out['secrets'])}  libs: {len(out['libs'])}",
        "#" if out["secrets"] else "+")
    for sec in out["secrets"][:10]:
        log(f"  SECRET[{sec['type']}]: {sec['match'][:80]}", "!")
    for lib in out["libs"][:8]:
        log(f"  LIB {lib['name']}@{lib['version']}", "·")
    return out


# ═════════════════════════════════════════════
# STAGE 9 — WAYBACK
# ═════════════════════════════════════════════
def stage_wayback(ctx) -> dict:
    section("STAGE 9/14  WAYBACK · PARAMS · INTERESTING")
    domain = ctx["domainish"]
    out = {"count": 0, "param_urls": [], "interesting": [], "params": [], "other_hosts": []}
    limit = 4000 if ctx["fast"] else CAP_WAYBACK
    try:
        r = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={
                "url": f"{domain}/*",
                "output": "json",
                "fl": "original,statuscode,mimetype",
                "collapse": "urlkey",
                "limit": str(limit),
                "filter": "statuscode:200",
            },
            timeout=45, headers={"User-Agent": UA},
        )
        if r.status_code != 200 or not r.text.strip().startswith("["):
            log(f"wayback: HTTP {r.status_code}", "!")
            return out
        rows = r.json()[1:]
        originals = []
        for row in rows:
            try:
                originals.append(row[0])
            except Exception:
                pass
        out["count"] = len(originals)
        log(f"archived URLs: {len(originals)}", "+")

        param_urls, params_set, interesting = [], set(), []
        hosts_seen = set()
        kw = (
            ".env", ".git", "backup", "dump", "sql", "config", "secret",
            "token", "internal", "debug", "admin", "upload", "export",
            "phpinfo", "wp-config", "credential", "password", "key",
            "swagger", "graphql", "actuator", ".bak", ".old", ".zip",
        )
        for u in originals:
            if "?" in u:
                if len(param_urls) < 500:
                    param_urls.append(u)
                for pm in PARAM_RE.findall(u):
                    if len(params_set) < 400:
                        params_set.add(pm)
            if any(k in u.lower() for k in kw) and len(interesting) < 300:
                interesting.append(u)
            try:
                h = up.urlparse(u).hostname
                if h and h not in hosts_seen and len(hosts_seen) < 200:
                    hosts_seen.add(h)
                    if h == domain or h.endswith("." + domain):
                        if h not in ctx["subdomains"]:
                            ctx["subdomains"].append(h)
                    else:
                        ctx["other_sites"].add(h)
                        out["other_hosts"].append(h)
                if len(originals) and "?" not in u:
                    p = up.urlparse(u)
                    if p.path:
                        add_endpoint(ctx, p.path)
            except Exception:
                pass

        out["param_urls"] = sorted(set(param_urls))
        out["params"] = sorted(params_set)
        out["interesting"] = sorted(set(interesting))
        out["other_hosts"] = sorted(set(out["other_hosts"]))[:100]
        log(f"with params: {len(param_urls)} · unique params: {len(out['params'])}", "+")
        log(f"interesting historical: {len(out['interesting'])}",
            "!" if out["interesting"] else "·")
        log(f"other hosts from wayback: {len(out['other_hosts'])}",
            "!" if out["other_hosts"] else "·")
        for u in out["interesting"][:15]:
            log(f"  {u[:120]}", ">")
        for h in out["other_hosts"][:10]:
            log(f"  OTHER {h}", "!")
        del r, rows, originals
    except Exception as e:
        log(f"wayback: {e}", "!")
    return out


# ═════════════════════════════════════════════
# STAGE 10 — EMAILS / SOCIAL
# ═════════════════════════════════════════════
def stage_emails(ctx) -> dict:
    section("STAGE 10/14  EMAIL · SOCIAL · CONTACT HARVEST")
    s = ctx["session"]
    base = ctx["base"]
    out = {"emails": [], "social": [], "phones": [], "pages_scanned": 0}

    # scan root + a few live pages + wayback samples
    pages = [base + "/"]
    for u in list(ctx["live_hosts"])[:4]:
        pages.append(u)
    # sample wayback interesting
    wb = (ctx["results"].get("wayback") or {})
    for u in (wb.get("interesting") or [])[:3]:
        pages.append(u)
    for u in (wb.get("param_urls") or [])[:2]:
        pages.append(u)

    seen_pages = set()
    for page in pages:
        if page in seen_pages or len(ctx["emails"]) >= CAP_EMAILS:
            continue
        seen_pages.add(page)
        rr = safe_get(s, page, timeout=8)
        if not rr or not rr.text:
            continue
        out["pages_scanned"] += 1
        body = rr.text[:300_000]
        for m in EMAIL_RE.findall(body):
            em = m.lower()
            # filter obvious garbage
            if any(x in em for x in ("example.com", "sentry", "w3.org", "schema.org", "godaddy", "godaddy.com")):
                continue
            if "@." in em or em.endswith("@") or ".." in em:
                continue
            ctx["emails"].add(em)
        for m in SOCIAL_RE.findall(body):
            ctx["social"].add(m)
        # mailto: links
        for m in re.findall(r"""mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})""", body, re.I):
            ctx["emails"].add(m.lower())
        del body

    # also from artifacts
    for key, txt in ctx["artifacts"].items():
        for m in EMAIL_RE.findall(txt or ""):
            ctx["emails"].add(m.lower())

    # phone: only from root-ish content already partially — skip heavy NER
    out["emails"] = sorted(ctx["emails"])[:CAP_EMAILS]
    out["social"] = sorted(ctx["social"])[:100]
    log(f"emails: {len(out['emails'])}  social: {len(out['social'])}  pages: {out['pages_scanned']}",
        "!" if out["emails"] else "·")
    for e in out["emails"][:15]:
        log(f"  {e}", ">")
    for u in out["social"][:10]:
        log(f"  {u[:100]}", ">")
    return out


# ═════════════════════════════════════════════
# STAGE 11 — PORT LITE
# ═════════════════════════════════════════════
def stage_ports(ctx) -> dict:
    section("STAGE 11/14  PORT LITE (top list, no nmap)")
    out = {"host": ctx["host"], "open": [], "scanned": 0}
    # resolve fresh
    try:
        infos = socket.getaddrinfo(ctx["host"], None)
        ips = sorted({i[4][0] for i in infos})
    except Exception:
        ips = ctx.get("resolved_ips") or []
    if not ips:
        log("no IP for port scan", "!")
        return out
    ip = ips[0]
    # pick a spread of ports within cap — not just the first N web ports
    if ctx["fast"]:
        # keep common web + a slice of alt/infra so nonstandard listeners still show
        web_core = [p for p in TOP_PORTS if p in (80, 443, 8080, 8443, 8000, 3000, 5000, 8888, 8443, 9443, 8081, 8090)]
        rest = [p for p in TOP_PORTS if p not in web_core]
        ports = list(dict.fromkeys(web_core + rest))[: max(20, CAP_PORTS // 2)]
    else:
        # stride-sample across full list so we don't stop before reaching non-web ports
        stride = max(1, len(TOP_PORTS) // CAP_PORTS)
        ports = TOP_PORTS[::stride][:CAP_PORTS]
        # always force-include the standard web set if room
        for p in (80, 443, 8080, 8443):
            if p in TOP_PORTS and p not in ports and len(ports) < CAP_PORTS + 8:
                ports.append(p)
    ports = list(dict.fromkeys(ports))
    log(f"scan {len(ports)} ports on {ip}", ">")

    def check(pn):
        try:
            with socket.create_connection((ip, pn), timeout=0.6):
                return pn
        except Exception:
            return None

    with cf.ThreadPoolExecutor(max_workers=min(ctx["threads"], 20)) as ex:
        for fut in cf.as_completed([ex.submit(check, p) for p in ports]):
            out["scanned"] += 1
            r = fut.result()
            if r:
                out["open"].append(r)
                log(f"OPEN {r}/tcp", "!")
    out["open"].sort()
    log(f"open ports: {out['open'] or 'none in top list'}", "#" if out["open"] else "·")
    return out


# ═════════════════════════════════════════════
# STAGE 12 — METHODS
# ═════════════════════════════════════════════
def stage_methods(ctx) -> dict:
    section("STAGE 12/14  HTTP METHODS · TRACE/PUT · WAF")
    s = ctx["session"]
    base = ctx["base"]
    out = {"allowed": [], "trace": None, "put": None, "options": None, "waf_block": False}

    # OPTIONS
    try:
        r = s.options(base + "/", timeout=8)
        allow = r.headers.get("Allow") or r.headers.get("Public") or ""
        out["options"] = {"status": r.status_code, "allow": allow[:200]}
        log(f"OPTIONS → {r.status_code} Allow={allow or '-'}", "+")
        for m in re.split(r"[,\s]+", allow):
            m = m.strip().upper()
            if m and m not in out["allowed"] and m not in ("GET", "HEAD", "OPTIONS"):
                out["allowed"].append(m)
    except Exception as e:
        log(f"OPTIONS: {e}", "!")

    # TRACE
    try:
        r = s.request("TRACE", base + "/", timeout=8)
        out["trace"] = r.status_code
        log(f"TRACE → {r.status_code}" + (" (XST risk!)" if r.status_code == 200 else ""),
            "!" if r.status_code == 200 else "·")
        if r.status_code == 200:
            out["allowed"].append("TRACE")
    except Exception:
        out["trace"] = "ERR"

    # PUT / DELETE / PATCH (just verb, no body abuse beyond tiny)
    for verb in ("PUT", "DELETE", "PATCH", "PROPFIND"):
        try:
            r = s.request(verb, base + "/", timeout=6,
                          data=b"y" if verb in ("PUT", "PATCH") else None)
            if r.status_code not in (404, 405, 501):
                out["allowed"].append(f"{verb}:{r.status_code}")
                log(f"{verb} → {r.status_code}", "!" if r.status_code < 300 else "·")
        except Exception:
            pass

    # WAF block detect via classic sqli probe (timing not needed — just signature)
    try:
        r = s.get(base + "/?id=1'", timeout=8)
        blob = (r.text or "")[:5000]
        if re.search(r"web application firewall|access denied|blocked by|403 forbidden.*waf", blob, re.I) or r.status_code == 403:
            out["waf_block"] = True
            log(f"WAF block hint on probe: HTTP {r.status_code}", "!")
        else:
            log(f"probe: HTTP {r.status_code} (no obvious WAF block page)", "·")
    except Exception:
        pass

    return out


# ═════════════════════════════════════════════
# STAGE 13 — QUICK (CORS / REDIRECT)
# ═════════════════════════════════════════════
def stage_quick(ctx) -> dict:
    section("STAGE 13/14  CORS · OPEN REDIRECT")
    s = ctx["session"]
    base = ctx["base"]
    out = {"cors": [], "open_redirect": [], "notes": []}

    for origin in CORS_ORIGINS:
        try:
            r = s.get(base + "/", headers={"Origin": origin}, timeout=8)
            acao = r.headers.get("Access-Control-Allow-Origin", "")
            acac = r.headers.get("Access-Control-Allow-Credentials", "")
            if acao:
                entry = {"origin": origin, "acao": acao, "acac": acac,
                         "reflects": acao == origin or acao == "*"}
                out["cors"].append(entry)
                log(f"CORS {origin} → ACAO={acao} ACAC={acac}", "!" if entry["reflects"] else "+")
            else:
                log(f"CORS {origin} → no ACAO", "·")
        except Exception as e:
            log(f"CORS {origin}: {e}", "!")
        time.sleep(0.1)

    try:
        r = s.options(base + "/", headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        }, timeout=8)
        acao = r.headers.get("Access-Control-Allow-Origin", "")
        methods = r.headers.get("Access-Control-Allow-Methods", "")
        if acao:
            out["cors"].append({"preflight": True, "acao": acao, "methods": methods})
            log(f"preflight ACAO={acao} methods={methods}",
                "!" if acao in ("*", "https://evil.example") else "+")
    except Exception:
        pass

    probe_urls = []
    for p in REDIRECT_PARAMS[:8]:
        probe_urls.append(f"{base}/?{p}=https://evil.example")
    for ep in list(ctx["endpoints"])[:6]:
        if any(k in ep for k in ("redirect", "login", "logout", "continue", "next")):
            sep = "&" if "?" in ep else "?"
            probe_urls.append(base + ep + sep + "url=https://evil.example")

    for u in probe_urls[:14]:
        try:
            r = s.get(u, timeout=7, allow_redirects=False)
            loc = r.headers.get("Location", "")
            body = (r.text or "")[:3000]
            if loc and "evil.example" in loc:
                out["open_redirect"].append({"url": u[:160], "location": loc[:200], "status": r.status_code})
                log(f"OPEN REDIRECT: {u[:90]} → {loc[:70]}", "!")
            elif "evil.example" in body and r.status_code == 200:
                out["notes"].append(f"reflected: {u[:120]}")
                log(f"reflected probe: {u[:90]}", "·")
        except Exception:
            pass
        time.sleep(0.08)

    if not out["open_redirect"]:
        log("no open-redirect confirmed in quick pass", "·")
    return out


# ═════════════════════════════════════════════
# FINDING HELPERS — evidence gate · CWE/CVSS stub · per-finding template
# ═════════════════════════════════════════════
def _slugify(s, maxlen=54):
    s = re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")
    s = re.sub(r"_+", "_", s)
    return (s[:maxlen].rstrip("_")) or "finding"


def _cwe_cvss(f):
    """CWE + CVSS v3.1 stub — recalculate with real context before submission."""
    t = f["title"]
    if "Missing security header" in t:
        h = t.rsplit(":", 1)[-1].strip().lower()
        if h == "strict-transport-security":
            return "CWE-319", "5.3 [STUB]"
        if h == "content-security-policy":
            return "CWE-1021", "5.3 [STUB]"
        if h in ("x-frame-options", "cross-origin-opener-policy", "cross-origin-resource-policy"):
            return "CWE-1021", "5.4 [STUB]"
        if h == "x-content-type-options":
            return "CWE-16", "5.3 [STUB]"
        if h == "referrer-policy":
            return "CWE-200", "5.3 [STUB]"
        return "CWE-693", "5.3 [STUB]"
    if "Secret in JS" in t:
        return "CWE-798", "9.1 [STUB]"
    if "HTTP TRACE enabled" in t:
        return "CWE-693", "5.3 [STUB]"
    if "Open redirect" in t:
        return "CWE-601", "6.1 [STUB]"
    if "CORS reflection" in t:
        return "CWE-942", "6.1 [STUB]"
    if re.match(r"HTTP (PUT|DELETE|PATCH):\d+ allowed", t):
        return "CWE-749", "7.5 [STUB]"
    if t.startswith("Path ") and "→ 200" in t:
        tl = t.lower()
        if any(k in tl for k in (".env", ".git", "backup", ".sql", "id_rsa", "credential",
                                 "config", "phpunit", "eval-stdin", "dump")):
            return "CWE-538", "7.5 [STUB]"
        if any(k in tl for k in ("phpinfo", "info.php", "server-status", "server-info")):
            return "CWE-200", "5.3 [STUB]"
        return "CWE-200", "5.3 [STUB]"
    if t.startswith("Path ") and ("→ 401" in t or "→ 403" in t):
        return "CWE-284", "5.3 [STUB]"
    if t.startswith("Path ") and "→ 500" in t:
        return "CWE-209", "5.3 [STUB]"
    if t.startswith("Open port"):
        m = re.search(r"Open port (\d+)", t)
        pn = int(m.group(1)) if m else 0
        if pn in (3306, 5432, 6379, 27017, 9200, 11211):
            return "CWE-200", "7.5 [STUB]"
        return "CWE-284", "5.3 [STUB]"
    if "Interesting robots" in t:
        return "CWE-200", "3.7 [STUB]"
    return "—", "— [not scored]"


def _remediation_hint(f):
    t = f["title"]
    if "Missing security header" in t:
        return (f"Add `{t.rsplit(':', 1)[-1].strip()}` at edge/WAF or app framework "
                f"(`always set ...`).")
    if "Secret in JS" in t:
        return ("Rotate the exposed secret; move server-side values out of client bundles; "
                "scope tokens down; purge from CDN/cache.")
    if "HTTP TRACE enabled" in t:
        return "Disable TRACE at the web server (`TraceEnable off` / remove from method allow-list)."
    if "Open redirect" in t:
        return "Allow-list redirect targets; reject absolute/attacker-controlled URLs in the parameter."
    if "CORS reflection" in t:
        return ("Return ACAO only for trusted origins; never combine reflected origin with "
                "`Access-Control-Allow-Credentials: true`.")
    if re.match(r"HTTP (PUT|DELETE|PATCH):\d+ allowed", t):
        return ("Block unauthenticated write verbs at reverse proxy/WAF; enforce auth + CSRF "
                "on state-changing methods.")
    if t.startswith("Path "):
        return ("Remove or auth-gate the resource; deny at reverse proxy; rotate any credentials "
                "found inside; scan history/CDN copies.")
    if t.startswith("Open port"):
        return "Close or firewall to trusted ranges; bind admin interfaces to localhost/VPN."
    if "Interesting robots" in t:
        return "Treat Disallow as public knowledge — enforce server-side authz on those paths."
    if t.startswith("Cert "):
        return "Monitor cert lifecycle via CT; renew before expiry; pin only with rotation plan."
    if "WAF" in t:
        return "Info only — WAF presence noted for payload tuning, not a vulnerability."
    return "Verify exposure, apply least privilege, retest with raw HTTP proof."


def _synth_evidence(f, ctx):
    """Build raw-HTTP proof from values captured verbatim during stages."""
    det = f.get("detail") or {}
    if det.get("evidence"):
        return det["evidence"]
    base, host, title, st = ctx["base"], ctx["host"], f["title"], f["stage"]

    def _req(method, pathq, extra=None):
        lines = [f"{method} {pathq} HTTP/1.1", f"Host: {host}",
                 f"User-Agent: {UA[:56]}", "Accept: */*"]
        for k, v in (extra or {}).items():
            lines.append(f"{k}: {v}")
        return "\n".join(lines)

    if st == "paths" and det.get("path"):
        return {
            "url": det.get("url") or base + det["path"],
            "request": _req("GET", det["path"]),
            "response": (f"HTTP/1.1 {det.get('status')}\n"
                         f"Content-Type: {det.get('type', '')}\n"
                         f"Content-Length: {det.get('len')}\n"
                         f"Location: {det.get('location', '')}\n\n"
                         f"[{det.get('len')} body bytes captured in report.json → "
                         f"results.paths.hits[].evidence]"),
        }
    if "Missing security header" in title:
        http = ctx["results"].get("http") or {}
        present = (http.get("security") or {}).get("present") or []
        missing_h = title.rsplit(":", 1)[-1].strip()
        resp_lines = "\n".join(present[:25]) or "(selected headers: none)"
        return {
            "url": base + "/",
            "request": _req("GET", "/"),
            "response": (f"HTTP/1.1 {http.get('status')}\n{resp_lines}\n\n"
                         f"[HEADER ABSENT from actual response: {missing_h}]"),
        }
    if st == "quick" and "CORS reflection" in title:
        origin = det.get("origin") or "https://evil.example"
        extra_resp = ""
        if det.get("methods"):
            extra_resp += f"Access-Control-Allow-Methods: {det['methods']}\n"
        return {
            "url": base + "/",
            "request": _req("GET", "/", {"Origin": origin}),
            "response": (f"HTTP/1.1 200\n"
                         f"Access-Control-Allow-Origin: {det.get('acao', '')}\n"
                         f"Access-Control-Allow-Credentials: {det.get('acac', '')}\n"
                         f"{extra_resp}\n"
                         f"[headers verbatim from stage 13 response]"),
        }
    if st == "quick" and "Open redirect" in title:
        full = det.get("url") or base + "/"
        try:
            p = up.urlparse(full)
            pathq = (p.path or "/") + (("?" + p.query) if p.query else "")
        except Exception:
            pathq = "/"
        return {
            "url": full,
            "request": _req("GET", pathq),
            "response": (f"HTTP/1.1 {det.get('status')}\n"
                         f"Location: {det.get('location', '')}\n\n"
                         f"[Location reflects attacker-controlled origin — stage 13 proof]"),
        }
    if "HTTP TRACE enabled" in title:
        meth = ctx["results"].get("methods") or {}
        return {
            "url": base + "/",
            "request": _req("TRACE", "/"),
            "response": f"HTTP/1.1 {meth.get('trace')}\n[TRACE accepted — request echoed, XST risk]",
        }
    if re.match(r"HTTP (PUT|DELETE|PATCH):\d+ allowed", title):
        parts = title.split()
        verb = parts[1].split(":")[0]
        code = parts[1].split(":")[1]
        return {
            "url": base + "/",
            "request": _req(verb, "/", {"Content-Length": "1"} if verb in ("PUT", "PATCH") else None),
            "response": f"HTTP/1.1 {code}\n[server did not reject {verb} — stage 12 proof]",
        }
    return None


def _assign_evidence(f, ctx):
    """Zero-False-Positive Gate: CONFIRMED only with raw HTTP proof.

    Anti-overclaim: if origin is challenge-blocked, 'not found' style absences
    and synthesized header evidence stay OBSERVED/SPECULATIVE — never CONFIRMED
    from a challenge page.
    """
    det = f.get("detail") or {}
    http_res = (ctx.get("results") or {}).get("http") or {}
    if not isinstance(http_res, dict):
        http_res = {}
    blocked = bool(_SESSION_BLOCK[0]) or bool(http_res.get("challenge"))

    # WAF presence note is observational only — never a vuln claim
    if "WAF/CDN detected" in f["title"] or "CAPTCHA" in f["title"] or "challenge" in f["title"].lower():
        f["evidence_status"] = "OBSERVED"
        return

    if det.get("evidence") or f.get("evidence"):
        ev = det.get("evidence") or f.get("evidence")
        # if we only synthesized from a challenge/403 page, downgrade
        resp_l = ((ev or {}).get("response") or "")[:3000].lower()
        if blocked and any(k in resp_l for k in (
                "just a moment", "checking your browser", "attention required",
                "verify you are human", "cf-browser-verification", "enable javascript")):
            f["evidence"] = ev
            f["evidence_status"] = "OBSERVED"
            f["evidence_note"] = "captured from challenge page — not origin; verify after clearance"
            return
        f["evidence"] = ev
        f["evidence_status"] = "CONFIRMED"
        return

    synthable = (
        "Missing security header" in f["title"]
        or f["stage"] == "paths"
        or "Open redirect" in f["title"]
        or "CORS reflection" in f["title"]
        or "HTTP TRACE enabled" in f["title"]
        or bool(re.match(r"HTTP (PUT|DELETE|PATCH):\d+ allowed", f["title"]))
    )
    # under challenge: path absences / missing headers may be challenge artifacts
    if synthable:
        if blocked and f["stage"] in ("paths", "http", "methods"):
            f["evidence_status"] = "SPECULATIVE"
            f["evidence_note"] = "origin challenge-blocked — retest after WAF clearance before reporting"
            return
        ev = _synth_evidence(f, ctx)
        if ev:
            f["evidence"] = ev
            f["evidence_status"] = "CONFIRMED"
            return
    if f["stage"] == "wayback" or "Historical interesting" in f["title"]:
        f["evidence_status"] = "SPECULATIVE"
    else:
        f["evidence_status"] = "OBSERVED"


def _finding_full_md(f, ctx):
    """8-section finding document (English, submission-ready structure)."""
    sev = f["severity"].upper()
    cwe, cvss = _cwe_cvss(f)
    evs = f.get("evidence_status", "OBSERVED")
    det = f.get("detail") or {}
    endpoint = (det.get("url")
                or (ctx["base"] + det["path"] if det.get("path") else None)
                or f.get("url")
                or (ctx["base"] + "/"))
    L = []
    L.append(f"# Vulnerability Report: {f['title']}")
    L.append("")
    L.append("## 1. Executive Summary")
    L.append("")
    L.append("| Field | Value |")
    L.append("|-------|-------|")
    L.append(f"| Title | {f['title']} |")
    L.append(f"| Severity | `{f['severity']}` |")
    L.append(f"| CVSS v3.1 | {cvss} |")
    L.append(f"| CWE | {cwe} |")
    L.append(f"| Affected asset | `{ctx['host']}` |")
    L.append(f"| Endpoint | `{endpoint}` |")
    L.append(f"| Evidence status | **{evs}** |")
    L.append(f"| Source stage | `{f['stage']}` |")
    L.append("")
    L.append("## 2. Technical Description & Root Cause")
    L.append("")
    L.append(f"{f['title']}")
    L.append("")
    if det.get("path"):
        L.append(f"Resource `{det['path']}` returned HTTP `{det.get('status')}` "
                 f"({det.get('len')} bytes) without access control appropriate to its sensitivity.")
        L.append("")
    L.append("## 3. Prerequisites & Environment")
    L.append("")
    L.append(f"- Auth state: none (unauthenticated probe)")
    L.append(f"- Mode: `{ctx['meta']['mode']}` · threads={ctx['threads']}")
    L.append(f"- Target base: `{ctx['base']}`")
    L.append(f"- Scope: authorized assessment — non-destructive, rate-limited")
    L.append("")
    L.append("## 4. Step-by-Step Reproduction")
    L.append("")
    L.append(f"1. `python recon.py --target {ctx['meta'].get('target_raw') or ctx['domainish']} "
             f"--stages {f['stage']},report`")
    if det.get("path"):
        L.append(f"2. `curl -sk -D- {ctx['base']}{det['path']} | head -40`")
        L.append("3. Confirm status/body matches Raw HTTP block below.")
    else:
        L.append(f"2. Inspect `evidence/{f['stage']}_output.json` for the stage payload.")
        L.append("3. Confirm values match Raw HTTP block below (if CONFIRMED).")
    L.append("")
    L.append("## 5. Raw HTTP Request & Response")
    L.append("")
    ev = f.get("evidence")
    if ev:
        L.append("```http")
        L.append(redact(ev.get("request", "")))
        L.append("```")
        L.append("")
        L.append("```http")
        L.append(redact(ev.get("response", "")))
        L.append("```")
    else:
        L.append("_No raw capture for this finding (OBSERVED/SPECULATIVE). Reproduce via step 1._")
    L.append("")
    L.append("## 6. Controlled Minimal-Impact PoC")
    L.append("")
    if det.get("path"):
        L.append("```python")
        L.append("# GET-only verification — no destructive action")
        L.append("import sys, requests")
        L.append("requests.packages.urllib3.disable_warnings()")
        L.append(f"base = sys.argv[1] if len(sys.argv) > 1 else {ctx['base']!r}")
        L.append(f"r = requests.get(base.rstrip('/') + {det['path']!r}, timeout=10,")
        L.append("                 verify=True, allow_redirects=False,")
        L.append('                 headers={"User-Agent": "YATIM-Security-Auditor/1.0"})')
        L.append('print(f"HTTP {r.status_code} len={len(r.content)}")')
        L.append("print(r.text[:500])")
        L.append("```")
        L.append("")
        L.append(f"Standalone copy: `pocs/poc_{_slugify(f.get('title') or det['path'], maxlen=48)}.py`")
    else:
        L.append("_See step 1 stage command — finding derives from stage output, not a single URL fetch._")
    L.append("")
    L.append("## 7. Impact Assessment")
    L.append("")
    L.append(f"- Severity: `{f['severity']}` (CVSS stub `{cvss}` — recalc with program scope)")
    if "Secret in JS" in f["title"]:
        L.append("- Credential exposure may allow account/API abuse until rotated.")
    elif det.get("path") and "→ 200" in f["title"]:
        L.append("- Unauthenticated read of sensitive material (config/source/backup class).")
    elif "Open redirect" in f["title"]:
        L.append("- Phishing/token-theft vector when chained with auth flows.")
    elif "CORS reflection" in f["title"]:
        L.append("- Cross-origin credentialed read possible if ACAC=true with reflected origin.")
    else:
        L.append("- Information disclosure / configuration weakness (context-dependent).")
    L.append("")
    L.append("## 8. Remediation Guidance")
    L.append("")
    L.append(f"- **Short-term:** {_remediation_hint(f)}")
    L.append("- **Long-term:** enforce deny-by-default at proxy; add CI check for the control; monitor regression via headers/pathscan.")
    L.append("- **Reference:** OWASP Top 10 / CWE mapping above.")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"_Generated by YATIM recon.py finding writer · {_end_iso()} · evidence={evs}_")
    L.append("")
    return "\n".join(L)


def _write_poc(poc_dir, f, ctx):
    """Minimal-impact GET verification script for path findings."""
    det = f.get("detail") or {}
    if not det.get("path"):
        return None
    path = det["path"]
    vuln_slug = _slugify(f.get("title") or path, maxlen=48)
    fn = poc_dir / f"poc_{vuln_slug}.py"
    code = f'''#!/usr/bin/env python3
"""Minimal-impact verification PoC — GET only, non-destructive.
Usage: python {fn.name} [base_url]
"""
import sys
import requests

requests.packages.urllib3.disable_warnings()
UA = "YATIM-Security-Auditor/1.0"
PATH = {path!r}


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else {ctx["base"]!r}
    url = base.rstrip("/") + PATH
    try:
        r = requests.get(url, timeout=10, verify=True, allow_redirects=False,
                         headers={{"User-Agent": UA, "Accept": "*/*"}})
    except requests.RequestException as e:
        print(f"REQUEST ERROR: {{e}}")
        return 1
    print(f"GET {{url}}")
    print(f"HTTP {{r.status_code}}  len={{len(r.content)}}  type={{r.headers.get('Content-Type', '')}}")
    print("--- response headers ---")
    for k, v in list(r.headers.items())[:30]:
        print(f"{{k}}: {{v}}")
    print("--- body preview (500) ---")
    print((r.text or "")[:500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    fn.write_text(code, encoding="utf-8")
    return fn.name


# ═════════════════════════════════════════════
# STAGE 14 — REPORT
# ═════════════════════════════════════════════
def _aggregate_builtin(outdir) -> str:
    """Built-in report aggregator — no external script, no subprocess.

    Parses findings/*.md → writes SUMMARY.md + metadata.json in the same dir.
    Returns status string.
    """
    try:
        sev_order = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4,
                     "INFORMATIONAL": 5, "UNKNOWN": 6}
        find_dir = outdir / "findings"
        poc_dir = outdir / "pocs"
        ev_dir = outdir / "evidence"
        parsed = []
        if find_dir.exists():
            for fp in sorted(find_dir.glob("*.md")):
                if fp.name.lower() in ("summary.md", "readme.md"):
                    continue
                content = fp.read_text(encoding="utf-8", errors="replace")
                tm = re.search(r"^#\s+(?:Vulnerability Report:\s*)?(.+)$", content, re.M)
                title = tm.group(1).strip() if tm else fp.stem
                sm = re.search(r"(?:Severity)\s*[:|]\s*\*?`?([A-Za-z]+)`?\*?", content, re.I)
                if sm:
                    sev = sm.group(1).strip().upper()
                else:
                    pm = re.search(r"^(?:\[)?(CRITICAL|HIGH|MEDIUM|LOW|INFO|INFORMATIONAL)(?:\])?",
                                   fp.name, re.I)
                    sev = pm.group(1).upper() if pm else "UNKNOWN"
                if sev == "INFO":
                    sev = "INFORMATIONAL"
                cvss_m = re.search(r"CVSS(?:\s*v3\.1)?\s*(?:Score)?\s*[:|]\s*\*?`?([0-9\.]+[^\n|`]*)", content, re.I)
                cvss = cvss_m.group(1).strip() if cvss_m else "N/A"
                cwe_m = re.search(r"CWE\s*[:|]\s*\*?`?(CWE-\d+[^,\n\*\|`]*)", content, re.I)
                cwe = cwe_m.group(1).strip() if cwe_m else "N/A"
                ep_m = re.search(r"(?:Affected Endpoint|Affected Asset|Endpoint)\s*[:|]\s*`?([^`\n|]+)", content, re.I)
                endpoint = ep_m.group(1).strip() if ep_m else "N/A"
                parsed.append({
                    "file_name": fp.name, "relative_path": f"findings/{fp.name}",
                    "title": title, "severity": sev, "cvss": cvss, "cwe": cwe,
                    "endpoint": endpoint,
                    "last_modified": datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                })
        parsed.sort(key=lambda x: (sev_order.get(x["severity"], 99), x["title"]))
        pocs = [p.name for p in sorted(poc_dir.glob("*"))] if poc_dir.exists() else []
        evidence = [e.name for e in sorted(ev_dir.glob("*"))] if ev_dir.exists() else []
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}
        for item in parsed:
            if item["severity"] in counts:
                counts[item["severity"]] += 1
        data = {
            "target": outdir.name,
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_findings": len(parsed),
            "severity_summary": counts,
            "findings": parsed, "pocs": pocs, "evidence_files": evidence,
        }
        (outdir / "metadata.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        # SUMMARY.md
        lines = [
            f"# Security Assessment Summary: `{data['target']}`", "",
            f"- **Generated At**: {data['scan_time']}",
            f"- **Total Confirmed Findings**: {data['total_findings']}",
            f"- **Severity Breakdown**: Critical: {counts['CRITICAL']} | "
            f"High: {counts['HIGH']} | Medium: {counts['MEDIUM']} | "
            f"Low: {counts['LOW']} | Info: {counts['INFORMATIONAL']}",
            "", "---", "", "## Findings Matrix", "",
            "| Severity | Title | CVSS v3.1 | CWE | Endpoint | Report |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        if not parsed:
            lines.append("| - | *No confirmed vulnerabilities reported* | - | - | - | - |")
        else:
            for f in parsed:
                lines.append(
                    f"| `{f['severity']}` | {f['title']} | {f['cvss']} | {f['cwe']} "
                    f"| `{f['endpoint']}` | [{f['file_name']}]({f['relative_path']}) |")
        lines += ["", "---", "", "## PoC Scripts (`pocs/`)", ""]
        lines += [f"- [`pocs/{p}`](pocs/{p})" for p in pocs] or ["- *None.*"]
        lines += ["", "## Evidence (`evidence/`)", ""]
        lines += [f"- [`evidence/{e}`](evidence/{e})" for e in evidence] or ["- *None.*"]
        lines.append("")
        (outdir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
        return "SUMMARY.md + metadata.json (built-in)"
    except Exception as e:
        log(f"builtin aggregator error: {type(e).__name__}: {e}", "!")
        return f"failed {type(e).__name__}"


def stage_report(ctx) -> dict:
    section("STAGE 14/14  REPORT GENERATION")
    host = ctx["host"]
    outdir = ctx["outdir"]
    results = ctx["results"]
    meta = ctx["meta"]
    meta["duration_s"] = round(time.time() - meta.get("started_ts", time.time()), 1)
    meta["finished"] = _end_iso()

    eps = sorted(ctx["endpoints"])
    (outdir / "endpoints.txt").write_text("\n".join(eps) + ("\n" if eps else ""), encoding="utf-8")

    hosts_all = sorted(
        set(ctx["subdomains"]) | set(ctx["related_hosts"]) | set(ctx["other_sites"])
        | set(h.split("//", 1)[-1].split("/", 1)[0] for h in ctx["live_hosts"] if "//" in h)
    )
    (outdir / "hosts.txt").write_text("\n".join(hosts_all) + ("\n" if hosts_all else ""), encoding="utf-8")

    if ctx["emails"]:
        (outdir / "emails.txt").write_text("\n".join(sorted(ctx["emails"])) + "\n", encoding="utf-8")

    # findings
    findings = []
    http = results.get("http") or {}
    for h in (http.get("security") or {}).get("missing", []):
        findings.append({"severity": "info", "title": f"Missing security header: {h}", "stage": "http"})
    for w in http.get("waf") or []:
        findings.append({"severity": "info", "title": f"WAF/CDN detected: {w}", "stage": "http"})

    cert = results.get("cert") or {}
    if cert.get("not_after"):
        findings.append({
            "severity": "info",
            "title": f"Cert validity: {cert.get('not_before','?')} → {cert.get('not_after')}",
            "stage": "cert",
        })
    if cert.get("san"):
        findings.append({
            "severity": "info",
            "title": f"Cert SAN hosts: {len(cert['san'])} (related/other sites enumerated)",
            "stage": "cert",
        })

    for hit in (results.get("paths") or {}).get("hits", []):
        path_l = hit["path"].lower()
        sev = "high" if hit["status"] == 200 and any(
            k in path_l for k in (".env", ".git", "backup", "sql", "config", "credential", "id_rsa", "phpunit", "eval-stdin")
        ) else "medium" if hit["status"] in (200, 401, 500) else "low"
        findings.append({"severity": sev, "title": f"Path {hit['path']} → {hit['status']} ({hit['len']}b)",
                         "stage": "paths", "detail": hit})

    rob = results.get("robots") or {}
    for p in rob.get("disallowed", [])[:20]:
        findings.append({"severity": "info", "title": f"Interesting robots disallow: {p}", "stage": "robots"})

    js = results.get("js") or {}
    for s in js.get("secrets", []):
        findings.append({"severity": "critical", "title": f"Secret in JS [{s['type']}]: {s['match'][:60]}", "stage": "js"})

    ports = results.get("ports") or {}
    for pn in ports.get("open", []):
        sev = "medium" if pn in (22, 3389, 3306, 5432, 6379, 27017, 9200) else "info"
        findings.append({"severity": sev, "title": f"Open port {pn}/tcp on {ports.get('host')}", "stage": "ports"})

    meth = results.get("methods") or {}
    if meth.get("trace") == 200:
        findings.append({"severity": "medium", "title": "HTTP TRACE enabled (XST risk)", "stage": "methods"})
    if meth.get("waf_block"):
        findings.append({"severity": "info", "title": "WAF block page on SQLi probe", "stage": "methods"})
    for m in meth.get("allowed") or []:
        if m.startswith("PUT:") or m.startswith("DELETE:"):
            code = m.split(":")[-1]
            if code and code.isdigit() and int(code) < 300:
                findings.append({"severity": "medium", "title": f"HTTP {m} allowed", "stage": "methods"})

    quick = results.get("quick") or {}
    for c in quick.get("cors", []):
        if c.get("reflects") or (c.get("preflight") and c.get("acao") in ("*", "https://evil.example")):
            findings.append({"severity": "medium",
                             "title": f"CORS reflection ACAO={c.get('acao')} Origin={c.get('origin', 'preflight')}",
                             "stage": "quick", "detail": c})
    for o in quick.get("open_redirect", []):
        findings.append({"severity": "medium",
                         "title": f"Open redirect: {o['url']} → {o['location']}",
                         "stage": "quick", "detail": o})

    wb = results.get("wayback") or {}
    for u in (wb.get("interesting") or [])[:40]:
        findings.append({"severity": "info", "title": f"Historical interesting: {u[:120]}", "stage": "wayback"})
    for h in (wb.get("other_hosts") or [])[:30]:
        findings.append({"severity": "info", "title": f"Other site host (wayback): {h}", "stage": "wayback"})

    emails = results.get("emails") or {}
    if emails.get("emails"):
        findings.append({"severity": "info", "title": f"Emails harvested: {len(emails['emails'])}", "stage": "emails"})

    probe = results.get("probe") or {}
    if probe.get("count"):
        findings.append({"severity": "info", "title": f"Live subdomains: {probe['count']}", "stage": "probe"})

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: order.get(f["severity"], 9))
    ctx["findings"] = findings

    # evidence gate + artifact dirs (findings/pocs/evidence)
    find_dir = outdir / "findings"
    poc_dir = outdir / "pocs"
    ev_dir = outdir / "evidence"
    for d in (find_dir, poc_dir, ev_dir):
        d.mkdir(parents=True, exist_ok=True)

    ev_counts = {"CONFIRMED": 0, "OBSERVED": 0, "SPECULATIVE": 0}
    for i, f in enumerate(findings, 1):
        f["id"] = i
        _assign_evidence(f, ctx)
        ev_counts[f.get("evidence_status", "OBSERVED")] += 1

    # per-finding 8-section docs (critical/high/medium/low) + minimal-impact PoCs
    n_finding_files = 0
    n_pocs = 0
    for f in findings:
        if f["severity"] in ("critical", "high", "medium", "low"):
            sev_up = f["severity"].upper()
            # findings/[SEVERITY]_<vuln>.md
            fname = f"[{sev_up}]_{_slugify(f['title'])}.md"
            _fp = find_dir / fname
            if _fp.exists():
                fname = f"[{sev_up}_{f['id']:03d}]_{_slugify(f['title'])}.md"
                _fp = find_dir / fname
            _fp.write_text(redact(_finding_full_md(f, ctx)), encoding="utf-8")
            f["_file"] = fname
            n_finding_files += 1
        if f["severity"] in ("critical", "high", "medium"):
            if _write_poc(poc_dir, f, ctx):
                n_pocs += 1

    # evidence/: token-economy — full stage payloads on disk, report stays summarized
    for st_name, res in results.items():
        try:
            (ev_dir / f"{st_name}_output.json").write_text(
                redact(json.dumps(res, indent=2, default=str)), encoding="utf-8")
        except Exception:
            pass

    # evidence/: recon_notes — info findings + negative-test summary
    notes = ["# Recon Notes — info findings, negative tests, context",
             "",
             f"Target: `{ctx['base']}` · mode: `{ctx['meta']['mode']}` · {_end_iso()}",
             "",
             "## Evidence status counts",
             "",
             f"- CONFIRMED (raw HTTP proof): {ev_counts['CONFIRMED']}",
             f"- OBSERVED (stage output): {ev_counts['OBSERVED']}",
             f"- SPECULATIVE (heuristic, verify live): {ev_counts['SPECULATIVE']}",
             "",
             "## Info-severity findings (not vulnerability claims)",
             ""]
    for f in findings:
        if f["severity"] == "info":
            notes.append(f"- ({f['stage']}) [{f.get('evidence_status','OBSERVED')}] {f['title']}")
    notes += ["",
              "## Negative tests (this pass)",
              "",
              f"- Sensitive paths probed: {(results.get('paths') or {}).get('probed', 0)} "
              f"→ interesting hits: {len((results.get('paths') or {}).get('hits') or [])}",
              f"- Open-redirect confirmed: {len((results.get('quick') or {}).get('open_redirect') or [])}",
              f"- CORS reflection confirmed: "
              f"{sum(1 for c in (results.get('quick') or {}).get('cors') or [] if c.get('reflects'))}",
              f"- JS secrets matched (verify before claiming): {len((results.get('js') or {}).get('secrets') or [])}",
              ""]
    (ev_dir / "recon_notes.md").write_text("\n".join(notes), encoding="utf-8")

    fb = {sev: sum(1 for f in findings if f["severity"] == sev)
          for sev in ("critical", "high", "medium", "low", "info")}

    report = {
        "meta": meta,
        "summary": {
            "stages_run": meta["stages"],
            "mode": "deep" if ctx["deep"] else ("fast" if ctx["fast"] else "default"),
            "tech": (http.get("tech") or []) + list(ctx.get("_probe_tech") or []),
            "waf": http.get("waf") or [],
            "subdomains": len(ctx["subdomains"]),
            "live_subdomains": probe.get("count", 0),
            "related_hosts": len(ctx["related_hosts"]),
            "other_sites": sorted(ctx["other_sites"]),
            "endpoints": len(eps),
            "path_hits": len((results.get("paths") or {}).get("hits", [])),
            "secrets": len(js.get("secrets") or []),
            "emails": len(ctx["emails"]),
            "open_ports": ports.get("open") or [],
            "findings_by_sev": fb,
            "evidence_status": ev_counts,
            "zero_fp_gate": "CONFIRMED requires raw HTTP proof; SPECULATIVE must be verified live before reporting",
            "artifact_dirs": {"findings": n_finding_files, "pocs": n_pocs, "evidence": "evidence/"},
            "next_actions": [
                f"[{f['severity'].upper()}/{f.get('evidence_status','OBSERVED')}] ({f['stage']}) {f['title']}"
                for f in findings if f["severity"] in ("critical", "high", "medium")
            ][:20],
        },
        "results": results,
        "findings": findings,
        "endpoints": eps,
        "hosts": hosts_all,
        "emails": sorted(ctx["emails"]),
        "social": sorted(ctx["social"]),
        "other_sites": sorted(ctx["other_sites"]),
        "external_urls": sorted(ctx["external_urls"]),
    }
    (outdir / "report.json").write_text(
        redact(json.dumps(report, indent=2, default=str)), encoding="utf-8")

    sm = report["summary"]
    md = []

    def _bullet_list(items, limit=None, fmt="`{}`"):
        """Full dump helper for AI agent readability."""
        seq = list(items) if items else []
        if limit is not None:
            seq = seq[:limit]
        if not seq:
            md.append("_ (empty)_")
            return
        for it in seq:
            if isinstance(it, dict):
                md.append(f"- {json.dumps(it, ensure_ascii=False, default=str)}")
            else:
                s = str(it).replace("|", "\\|")
                md.append(f"- {fmt.format(s)}")
        if limit is not None and len(list(items) if items else []) > limit:
            md.append(f"- _… +{len(list(items)) - limit} more (see report.json)_")

    md.append(f"# Recon Report — `{host}`")
    md.append("")
    md.append("## Meta")
    md.append("")
    md.append("| Field | Value |")
    md.append("|-------|-------|")
    md.append(f"| Target | {ctx['base']} |")
    md.append(f"| Host | {host} |")
    md.append(f"| Domain | {ctx['domainish']} |")
    md.append(f"| Mode | **{sm['mode']}** |")
    md.append(f"| Started | {meta['started']} |")
    md.append(f"| Finished | {meta['finished']} |")
    md.append(f"| Duration | {meta['duration_s']}s |")
    md.append(f"| Stages | {', '.join(meta['stages'])} |")
    md.append(f"| Threads | {meta['threads']} |")
    md.append(f"| Caps | subs={CAP_SUBS} paths={CAP_PATHS} wayback={CAP_WAYBACK} js={CAP_JS} ports={CAP_PORTS} |")
    md.append("")

    md.append("## AI AGENT BRIEF")
    md.append("")
    md.append("> Machine-oriented summary. Full lists follow in each stage section.")
    md.append("> Prefer this file alone; `report.json` has raw stage payloads if needed.")
    md.append("")
    md.append(f"- **target_url**: `{ctx['base']}`")
    md.append(f"- **apex_domain**: `{ctx['domainish']}`")
    md.append(f"- **tech_stack**: {', '.join(dict.fromkeys(sm['tech'])) or 'unknown'}")
    md.append(f"- **waf_cdn**: {', '.join(sm['waf']) or 'none'}")
    md.append(f"- **subdomain_count**: {sm['subdomains']}")
    md.append(f"- **live_subdomain_count**: {sm['live_subdomains']}")
    md.append(f"- **related_hosts_cert**: {sm['related_hosts']}")
    md.append(f"- **other_sites_count**: {len(sm['other_sites'])}")
    md.append(f"- **endpoint_count**: {sm['endpoints']}")
    md.append(f"- **sensitive_path_hits**: {sm['path_hits']}")
    md.append(f"- **js_secret_count**: {sm['secrets']}")
    md.append(f"- **email_count**: {sm['emails']}")
    md.append(f"- **open_ports**: {sm['open_ports'] or []}")
    md.append(f"- **findings**: {fb}")
    md.append(f"- **evidence_status**: {ev_counts}")
    md.append("- **zero_fp_gate**: only `CONFIRMED` (raw HTTP proof) may be claimed as a vulnerability; "
              "`SPECULATIVE` requires live verification before reporting")
    md.append(f"- **artifacts**: report.md · report.json · endpoints.txt · hosts.txt"
              + (" · emails.txt" if ctx["emails"] else "")
              + f" · findings/ ({n_finding_files}) · pocs/ ({n_pocs}) · evidence/ (recon_notes + stage dumps)"
              + " · SUMMARY.md · metadata.json (aggregator)")
    md.append("")
    md.append("**Next actions for agent (priority):**")
    md.append("")
    prio = [f for f in findings if f["severity"] in ("critical", "high", "medium")]
    if not prio:
        md.append("1. No critical/high/medium findings. Proceed to exploit recon on live hosts + interesting paths.")
    else:
        for i, f in enumerate(prio[:15], 1):
            md.append(f"{i}. [{f['severity'].upper()}/{f.get('evidence_status', 'OBSERVED')}] "
                      f"({f['stage']}) {f['title']}")
    md.append("")

    md.append("## Summary")
    md.append("")
    md.append(f"- **Tech:** {', '.join(dict.fromkeys(sm['tech'])) or 'unknown'}")
    if sm["waf"]:
        md.append(f"- **WAF/CDN:** {', '.join(sm['waf'])}")
    md.append(f"- **Subdomains:** {sm['subdomains']} · **Live:** {sm['live_subdomains']}")
    md.append(f"- **Related hosts (cert/org):** {sm['related_hosts']}")
    md.append(f"- **Other sites seen:** {len(sm['other_sites'])}")
    md.append(f"- **Endpoints:** {sm['endpoints']} · **Path hits:** {sm['path_hits']}")
    md.append(f"- **Secrets:** {sm['secrets']} · **Emails:** {sm['emails']}")
    md.append(f"- **Open ports:** {', '.join(str(p) for p in sm['open_ports']) or 'none in top list'}")
    md.append(f"- **Findings:** " + (", ".join(f"{k}={v}" for k, v in fb.items() if v) or "none"))
    md.append("")

    # ── FINDINGS (all + evidence blocks) ──
    md.append("## Findings")
    md.append("")
    if not findings:
        md.append("_No findings._")
        md.append("")
    else:
        md.append("### Overview")
        md.append("")
        md.append("| # | Severity | Evidence | Stage | Title | File |")
        md.append("|---|----------|----------|-------|-------|------|")
        for f in findings:
            title = f["title"].replace("|", "\\|")
            fl = f"`findings/{f['_file']}`" if f.get("_file") else "—"
            md.append(f"| {f.get('id','')} | `{f['severity']}` | `{f.get('evidence_status','OBSERVED')}` "
                      f"| {f['stage']} | {title} | {fl} |")
        md.append("")
        md.append("### Grouped by severity")
        md.append("")
        for sev in ("critical", "high", "medium", "low", "info"):
            group = [f for f in findings if f["severity"] == sev]
            if not group:
                continue
            md.append(f"#### {sev.upper()} ({len(group)})")
            for f in group:
                md.append(f"- ({f['stage']}) [{f.get('evidence_status','OBSERVED')}] {f['title']}")
            md.append("")
        md.append("### Evidence blocks (raw HTTP)")
        md.append("")
        md.append("> **Zero-False-Positive Gate** — `CONFIRMED` = raw HTTP request/response proof captured.")
        md.append("> `OBSERVED` = reproducible stage output (status/header/port) without full raw capture.")
        md.append("> `SPECULATIVE` = heuristic match; verify live before reporting.")
        md.append("> CVSS/CWE values are `[STUB]` — recalculate with program scope before submission.")
        md.append("")
        detailed = [f for f in findings
                    if f["severity"] in ("critical", "high", "medium", "low")][:40]
        if not detailed:
            md.append("_No critical/high/medium/low findings — nothing meets the evidence-block threshold._")
            md.append("")
        else:
            for f in detailed:
                cwe, cvss = _cwe_cvss(f)
                evs = f.get("evidence_status", "OBSERVED")
                det = f.get("detail") or {}
                endpoint = (det.get("url")
                            or (ctx["base"] + det["path"] if det.get("path") else None)
                            or f.get("url")
                            or (ctx["base"] + "/"))
                md.append(f"#### [{f.get('id')}] {f['severity'].upper()} — {f['title']}")
                md.append("")
                md.append("| Field | Value |")
                md.append("|-------|-------|")
                md.append(f"| Evidence status | **{evs}** |")
                md.append(f"| CWE | {cwe} |")
                md.append(f"| CVSS v3.1 | {cvss} |")
                md.append(f"| Stage | `{f['stage']}` |")
                md.append(f"| Endpoint | `{endpoint}` |")
                md.append(f"| Finding file | `findings/{f.get('_file') or ''}` |")
                md.append("")
                md.append("**Step-by-step repro:**")
                md.append("")
                md.append(f"1. `python recon.py --target {ctx['meta'].get('target_raw') or ctx['domainish']} "
                          f"--stages {f['stage']},report`")
                if det.get("path"):
                    md.append(f"2. `curl -sk -D- {ctx['base']}{det['path']} | head -40`")
                else:
                    md.append(f"2. Inspect `evidence/{f['stage']}_output.json`.")
                md.append("")
                ev = f.get("evidence")
                if ev:
                    md.append("**Raw HTTP Request**")
                    md.append("")
                    md.append("```http")
                    md.append(redact(ev.get("request", "")))
                    md.append("```")
                    md.append("")
                    md.append("**Raw HTTP Response**")
                    md.append("")
                    md.append("```http")
                    md.append(redact(ev.get("response", "")))
                    md.append("```")
                else:
                    md.append("_No raw capture (OBSERVED/SPECULATIVE) — reproduce via stage command above._")
                md.append("")
                md.append(f"**Remediation:** {_remediation_hint(f)}")
                md.append("")

    # ── STAGE DETAILS (numbered 1..N, no letter suffixes) ──
    md.append("## Stage Details")
    md.append("")
    _sec_n = 0

    def _sec(title):
        nonlocal _sec_n
        _sec_n += 1
        md.append(f"### {_sec_n}. {title}")
        md.append("")

    if http:
        _sec("HTTP / Tech / WAF")
        md.append(f"- Status: `{http.get('status')}` · Final: `{http.get('final_url','')}`")
        if http.get("waf"):
            md.append(f"- WAF: {', '.join(http['waf'])}")
        md.append(f"- Tech: {', '.join(http.get('tech') or [])}")
        md.append("### Response headers (full selected)")
        md.append("")
        for k, v in (http.get("headers") or {}).items():
            md.append(f"- `{k}: {v}`")
        sec = http.get("security") or {}
        md.append("")
        md.append("### Security headers present")
        md.append("")
        _bullet_list(sec.get("present") or [], fmt="{}")
        md.append("")
        md.append("### Security headers missing")
        md.append("")
        _bullet_list(sec.get("missing") or [], fmt="`{}`")
        md.append("")
        ex = http.get("extras") or {}
        md.append("### Well-known / robots baseline")
        md.append("")
        for name in ("robots", "sitemap", "security_txt", "crossdomain", "favicon",
                     "humans", "ads", "manifest", "security_root"):
            if name in ex:
                e = ex[name]
                md.append(f"- `{name}`: status={e.get('status')} len={e.get('len')}" +
                          (f" preview=`{e.get('preview','')[:120]}`" if e.get("preview") else ""))
        if ex.get("favicon_sha1"):
            md.append(f"- favicon_sha1: `{ex['favicon_sha1']}`")
        if ex.get("set_cookie"):
            md.append(f"- set_cookie: `{ex['set_cookie']}`")
        ck = ex.get("cookies") or []
        if ck:
            md.append("### Cookies")
            for c in ck:
                md.append(f"- `{json.dumps(c, ensure_ascii=False)}`")
        md.append("")

    if cert and (cert.get("san") or cert.get("issuer")):
        _sec("TLS Certificate")
        if cert.get("issuer"):
            md.append(f"- **Issuer:** {cert['issuer']}")
        if cert.get("subject"):
            md.append(f"- **Subject:** {cert['subject']}")
        if cert.get("not_before"):
            md.append(f"- **Validity:** {cert['not_before']} → {cert['not_after']}")
        md.append("")
        md.append(f"### SAN names (ALL {len(cert.get('san') or [])})")
        md.append("")
        _bullet_list(cert.get("san") or [])
        md.append("")
        md.append(f"### Related / other sites from cert ({len(cert.get('related') or [])})")
        md.append("")
        _bullet_list(cert.get("related") or [])
        md.append("")

    dns = results.get("dns") or {}
    if dns:
        _sec("DNS")
        md.append("| Type | Values |")
        md.append("|------|--------|")
        for rt, ans in dns.items():
            if isinstance(ans, list) and ans:
                joined = ", ".join(f"`{a}`" for a in ans)
                md.append(f"| {rt} | {joined} |")
        md.append("")

    if probe:
        _sec("Live Subdomains (ALL)")
        md.append(f"Tool: `{probe.get('tool')}` · Live: **{probe.get('count', 0)}**")
        md.append("")
        live_list = probe.get("live") or []
        if live_list:
            md.append("| Status | URL | Title | Server | Tech |")
            md.append("|--------|-----|-------|--------|------|")
            for e in live_list:
                title = (e.get("title") or "").replace("|", "\\|")
                tech_s = ", ".join(e.get("tech") or []) if e.get("tech") else ""
                md.append(f"| {e.get('status')} | {e.get('url')} | {title} | {e.get('server') or ''} | {tech_s} |")
            md.append("")
        else:
            md.append("_No live hosts returned (all down or probe skipped)._")
            md.append("")

    subs_r = results.get("subs") or {}
    if subs_r:
        _sec("Subdomains (ALL)")
        md.append(f"Total: **{subs_r.get('total',0)}** · sources: `{json.dumps(subs_r.get('sources',{}))}`")
        md.append("")
        _bullet_list(subs_r.get("list") or [])
        md.append("")

    if hosts_all:
        _sec("Combined hosts.txt (ALL)")
        md.append(f"({len(hosts_all)} hosts — also written to hosts.txt)")
        md.append("")
        _bullet_list(hosts_all)
        md.append("")

    if rob and (rob.get("disallowed") or rob.get("sitemaps_urls") or rob.get("robots_paths")):
        _sec("Robots / Sitemap")
        if rob.get("robots_paths"):
            md.append(f"### All robots paths ({len(rob['robots_paths'])})")
            md.append("")
            _bullet_list(rob["robots_paths"])
            md.append("")
        if rob.get("disallowed"):
            md.append(f"### Interesting Disallow ({len(rob['disallowed'])})")
            md.append("")
            _bullet_list(rob["disallowed"])
            md.append("")
        if rob.get("sitemaps"):
            md.append("### Sitemap indexes")
            md.append("")
            _bullet_list(rob["sitemaps"])
            md.append("")
        if rob.get("sitemaps_urls"):
            md.append(f"### Sitemap URLs ({len(rob['sitemaps_urls'])})")
            md.append("")
            _bullet_list(rob["sitemaps_urls"])
            md.append("")

    if (results.get("paths") or {}).get("hits") is not None:
        hits = (results.get("paths") or {}).get("hits") or []
        probed = (results.get("paths") or {}).get("probed", 0)
        _sec("Sensitive Paths")
        md.append(f"Probed: {probed} · Interesting hits: **{len(hits)}**")
        md.append("")
        if hits:
            md.append("| Status | Path | Size | Type | Location |")
            md.append("|--------|------|------|------|----------|")
            for h in hits:
                md.append(f"| {h['status']} | `{h['path']}` | {h['len']} | {h.get('type','')} | {h.get('location','')} |")
            md.append("")
        else:
            md.append("_No interesting path hits in this pass._")
            md.append("")

    if js and (js.get("secrets") or js.get("apis") or js.get("libs") or js.get("scripts")):
        _sec("JS Mining")
        if js.get("scripts"):
            md.append(f"### Scripts ({len(js['scripts'])})")
            md.append("")
            _bullet_list(js["scripts"])
            md.append("")
        if js.get("libs"):
            md.append(f"### Libraries ({len(js['libs'])})")
            md.append("")
            for lib in js["libs"]:
                md.append(f"- {lib['name']} `{lib['version']}`")
            md.append("")
        if js.get("secrets"):
            md.append(f"### Secrets ({len(js['secrets'])}) — ACTION REQUIRED")
            md.append("")
            _bullet_list(js["secrets"], fmt="{}")
            md.append("")
        if js.get("apis"):
            md.append(f"### API-like paths ({len(js['apis'])})")
            md.append("")
            _bullet_list(js["apis"])
            md.append("")
        if js.get("endpoints"):
            md.append(f"### JS endpoints ({len(js['endpoints'])})")
            md.append("")
            _bullet_list(js["endpoints"])
            md.append("")

    if wb:
        _sec("Wayback Surface")
        md.append(f"- Archived: {wb.get('count',0)} · params unique: {len(wb.get('params') or [])}")
        md.append(f"- Param URLs: {len(wb.get('param_urls') or [])} · Interesting: {len(wb.get('interesting') or [])}")
        md.append(f"- Other hosts: {len(wb.get('other_hosts') or [])}")
        md.append("")
        if wb.get("params"):
            md.append(f"### Query params (ALL unique {len(wb['params'])})")
            md.append("")
            md.append(", ".join(f"`{p}`" for p in wb["params"]))
            md.append("")
        if wb.get("param_urls"):
            md.append(f"### URLs with params ({len(wb['param_urls'])})")
            md.append("")
            _bullet_list(wb["param_urls"])
            md.append("")
        if wb.get("other_hosts"):
            md.append(f"### Other hosts (ALL {len(wb['other_hosts'])})")
            md.append("")
            _bullet_list(wb["other_hosts"])
            md.append("")
        if wb.get("interesting"):
            md.append(f"### Interesting historical (ALL {len(wb['interesting'])})")
            md.append("")
            _bullet_list(wb["interesting"])
            md.append("")

    if ports:
        _sec("Open Ports")
        md.append(f"- Host/IP target: `{ports.get('host')}` · Scanned: {ports.get('scanned',0)}")
        md.append(f"- Open: " + (", ".join(f"`{p}`" for p in (ports.get("open") or [])) or "none in top list"))
        md.append("")

    if meth:
        _sec("HTTP Methods / WAF")
        md.append(f"- OPTIONS: `{json.dumps(meth.get('options'), ensure_ascii=False)}`")
        md.append(f"- TRACE: `{meth.get('trace')}` · WAF block hint: `{meth.get('waf_block')}`")
        if meth.get("allowed"):
            md.append(f"- Notable verbs: {', '.join(meth['allowed'])}")
        md.append("")

    if emails and (emails.get("emails") or emails.get("social")):
        _sec("Emails / Social (ALL)")
        if emails.get("emails"):
            md.append(f"### Emails ({len(emails['emails'])})")
            md.append("")
            _bullet_list(emails["emails"])
            md.append("")
        if emails.get("social"):
            md.append(f"### Social ({len(emails['social'])})")
            md.append("")
            _bullet_list(emails["social"], fmt="{}")
            md.append("")

    if ctx["other_sites"]:
        _sec("Other Sites (outside apex — ALL)")
        md.append("Discovered via cert SAN / wayback / content — related properties:")
        md.append("")
        _bullet_list(sorted(ctx["other_sites"]))
        md.append("")

    if ctx["external_urls"]:
        _sec("External URLs seen (sample ALL capped store)")
        _bullet_list(sorted(ctx["external_urls"])[:500])
        md.append("")

    if eps:
        _sec("Endpoints (ALL from endpoints.txt)")
        md.append(f"({len(eps)} paths — also in endpoints.txt)")
        md.append("")
        _bullet_list(eps)
        md.append("")

    if quick and (quick.get("cors") or quick.get("open_redirect") or quick.get("notes")):
        _sec("Quick Checks")
        if quick.get("cors"):
            md.append("### CORS")
            for c in quick["cors"]:
                md.append(f"- `{json.dumps(c, ensure_ascii=False)}`")
            md.append("")
        if quick.get("open_redirect"):
            md.append("### Open redirect candidates")
            for o in quick["open_redirect"]:
                md.append(f"- `{o['url']}` → `{o['location']}` (status {o.get('status')})")
            md.append("")
        if quick.get("notes"):
            md.append("### Notes")
            for n in quick["notes"]:
                md.append(f"- {n}")
            md.append("")

    # stage errors if any
    errs = {k: v for k, v in results.items() if isinstance(v, dict) and v.get("error")}
    if errs:
        md.append("## Stage errors")
        md.append("")
        for k, v in errs.items():
            md.append(f"- `{k}`: {v['error']}")
        md.append("")

    # artifacts footer
    md.append("## Artifacts")
    md.append("")
    md.append("| Artifact | Path |")
    md.append("|----------|------|")
    md.append("| Full report | `report.md` |")
    md.append("| Machine JSON | `report.json` (redacted) |")
    md.append("| Endpoints | `endpoints.txt` |")
    md.append("| Hosts | `hosts.txt` |")
    if ctx["emails"]:
        md.append("| Emails | `emails.txt` |")
    md.append(f"| Findings | `findings/` ({n_finding_files}) |")
    md.append(f"| PoCs | `pocs/` ({n_pocs}) |")
    md.append("| Evidence | `evidence/` (recon_notes + stage dumps, redacted) |")
    md.append("| Summary index | `SUMMARY.md` · `metadata.json` |")
    md.append("")

    md.append("---")
    md.append("")
    md.append(f"_Generated by YATIM recon.py · {_end_iso()}_")
    md.append(f"_Evidence gate: CONFIRMED={ev_counts['CONFIRMED']} · "
              f"OBSERVED={ev_counts['OBSERVED']} · SPECULATIVE={ev_counts['SPECULATIVE']}_")
    md.append("")
    (outdir / "report.md").write_text(redact("\n".join(md)), encoding="utf-8")

    # built-in aggregator → SUMMARY.md + metadata.json (no external subprocess)
    _agg_status = _aggregate_builtin(outdir)

    log(f"report.md   → {outdir / 'report.md'}", "+")
    log(f"report.json → {outdir / 'report.json'} (redacted)", "+")
    log(f"endpoints   → {outdir / 'endpoints.txt'} ({len(eps)})", "+")
    log(f"hosts       → {outdir / 'hosts.txt'} ({len(hosts_all)})", "+")
    log(f"findings/   → {n_finding_files} per-finding docs", "+")
    log(f"pocs/       → {n_pocs} minimal-impact scripts", "+")
    log(f"evidence/   → recon_notes.md + {len(results)} stage dumps (redacted)", "+")
    log(f"aggregator  → {_agg_status}", "+")

    print()
    print("=" * 64)
    print("  RECON COMPLETE")
    print("=" * 64)
    print(f"  target      : {ctx['base']}")
    print(f"  mode        : {sm['mode']}")
    print(f"  tech/waf    : {', '.join(dict.fromkeys(sm['tech'])) or '-'} / {', '.join(sm['waf']) or '-'}")
    print(f"  subdomains  : {sm['subdomains']}  live={sm['live_subdomains']}")
    print(f"  related     : {sm['related_hosts']}  other_sites={len(sm['other_sites'])}")
    print(f"  endpoints   : {sm['endpoints']}  path_hits={sm['path_hits']}")
    print(f"  secrets     : {sm['secrets']}  emails={sm['emails']}")
    print(f"  open ports  : {', '.join(str(p) for p in sm['open_ports']) or '-'}")
    print(f"  findings    : " + (", ".join(f"{k}={v}" for k, v in fb.items() if v) or "none"))
    print(f"  evidence    : CONF={ev_counts['CONFIRMED']} OBS={ev_counts['OBSERVED']} "
          f"SPEC={ev_counts['SPECULATIVE']}")
    print(f"  duration    : {meta['duration_s']}s")
    print(f"  output      : {outdir}")
    print(f"              : findings/={n_finding_files} pocs/={n_pocs} evidence/=redacted "
          f"aggregator={_agg_status}")
    print("=" * 64)
    print()
    report["summary"]["aggregator"] = _agg_status
    return report


# ═════════════════════════════════════════════
# RUNNER
# ═════════════════════════════════════════════
STAGE_FUNCS = {
    "http": stage_http,
    "dns": stage_dns,
    "cert": stage_cert,
    "subs": stage_subs,
    "probe": stage_probe,
    "paths": stage_paths,
    "robots": stage_robots,
    "js": stage_js,
    "wayback": stage_wayback,
    "emails": stage_emails,
    "ports": stage_ports,
    "methods": stage_methods,
    "quick": stage_quick,
    "report": stage_report,
}
ALL_STAGES = list(STAGE_FUNCS.keys())

STAGE_HINTS = {
    "http": "headers · tech · security · WAF/CDN sniff · favicon hash",
    "dns": "A/AAAA/MX/NS/TXT/CNAME/CAA/SOA · SPF/DMARC/DKIM/MTA-STS",
    "cert": "TLS SAN → related hosts + OTHER SITES on same cert",
    "subs": "crt.sh + OTX + anubis + rapidDNS + wayback + hackertarget + bufferover + subfinder + brute+permutasi (parallel, hot-first)",
    "probe": "live HTTP(S) check subdomains via httpx (bounded, hot-first: admin/api/dev/staging duluan)",
    "paths": "sensitive path probe (.git/.env/backup/panel/api)",
    "robots": "robots Disallow deep + sitemap URL harvest",
    "js": "JS endpoints · secrets · lib versions · API paths",
    "wayback": "historical URLs · query params · interesting files · other hosts",
    "emails": "email/social/mailto harvest from pages + wayback sample",
    "ports": "top-port TCP connect lite (no nmap)",
    "methods": "OPTIONS/TRACE/PUT/DELETE · WAF block probe",
    "quick": "CORS reflection · open-redirect candidates",
    "report": "report.md + report.json + endpoints/hosts + findings/ + pocs/ + evidence/ + SUMMARY.md + metadata.json",
}


def run(target, stages, threads, fast, deep, as_json, insecure=False) -> int:
    base, host, domainish = normalize_target(target)
    ts = time.strftime("%Y%m%d_%H%M%S")
    outdir = OUTROOT / f"{host}_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)

    # adjust caps by mode
    global CAP_PATHS, CAP_JS, CAP_WAYBACK, CAP_SUBS, CAP_PORTS
    if fast:
        CAP_PATHS = CAP_PATHS_FAST
        CAP_JS = 12
        CAP_WAYBACK = 2500
        CAP_SUBS = 150
        CAP_PORTS = 20
    elif deep:
        CAP_PATHS = 120
        CAP_JS = 30
        CAP_WAYBACK = 8000
        CAP_SUBS = 600
        CAP_PORTS = 50

    stages = [s for s in stages if s in STAGE_FUNCS]
    if "report" not in stages and any(s != "report" for s in stages):
        stages.append("report")
    if not stages:
        stages = list(ALL_STAGES)

    threads = max(4, min(threads, 20))

    ctx = {
        "base": base,
        "host": host,
        "domainish": domainish,
        "session": http_session(),
        "endpoints": set(),
        "subdomains": [],
        "related_hosts": set(),
        "other_sites": set(),
        "external_urls": set(),
        "live_hosts": set(),
        "emails": set(),
        "social": set(),
        "artifacts": {},
        "robots_paths": [],
        "resolved_ips": [],
        "results": {},
        "findings": [],
        "threads": threads,
        "fast": fast,
        "deep": deep,
        "outdir": outdir,
        "_probe_tech": set(),
        "_sec_missing": [],
        "meta": {
            "target_raw": target,
            "base": base,
            "host": host,
            "domain": domainish,
            "started": _end_iso(),
            "stages": stages,
            "threads": threads,
            "fast": fast,
            "deep": deep,
            "mode": "deep" if deep else ("fast" if fast else "default"),
            "started_ts": time.time(),
            "duration_s": 0,
            "finished": "",
        },
    }

    if insecure:
        ctx["session"].verify = False
    mode = "DEEP" if deep else ("FAST" if fast else "DEFAULT")
    print(f"""
============================================================
  YATIM · DEEP RECON PIPELINE  [{mode}]
  target   : {base}
  host     : {host}
  stages   : {', '.join(stages)}
  threads  : {threads}   caps: subs={CAP_SUBS} paths={CAP_PATHS} wayback={CAP_WAYBACK}
  output   : {outdir}
============================================================""", flush=True)

    t0 = time.time()
    for st in stages:
        fn = STAGE_FUNCS[st]
        st_t0 = time.time()
        if st == "report":
            ctx["meta"]["duration_s"] = round(time.time() - t0, 1)
            ctx["meta"]["finished"] = _end_iso()
        try:
            ctx["results"][st] = fn(ctx)
        except Exception as e:
            log(f"stage {st} FAILED: {type(e).__name__}: {e}", "X")
            ctx["results"][st] = {"error": f"{type(e).__name__}: {e}"}
        log(f"stage {st} done in {time.time()-st_t0:.1f}s", "+")

    meta = ctx["meta"]
    meta["duration_s"] = round(time.time() - t0, 1)
    meta["finished"] = _end_iso()
    meta["target_raw"] = target

    if as_json:
        rj = outdir / "report.json"
        if rj.exists():
            data = json.loads(rj.read_text(encoding="utf-8"))
            print(json.dumps({
                "outdir": str(outdir),
                "summary": data.get("summary", {}),
                "findings": data.get("findings", [])[:60],
            }, indent=2, default=str))
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="recon.py",
        description="YATIM deep multi-stage recon pipeline (RAM-safe, one command, neat report).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""modes:
  (default)  balanced deep
  --fast     lower caps, fewer paths
  --deep     extra sources (bufferover, more ports/paths/js/wayback)

stages:
  http dns cert subs probe paths robots js wayback emails ports methods quick report

examples:
  python recon.py --target example.com
  python recon.py --target example.com --deep --threads 12
  python recon.py --target example.com --fast
  python recon.py --target app.example.com --stages http,dns,cert,subs,probe,report
  python recon.py --list-stages

output:
  reports/<slug>_<ts>/report.md  report.json  endpoints.txt  hosts.txt
  reports/<slug>_<ts>/findings/[SEV]_<slug>.md  pocs/  evidence/
  reports/<slug>_<ts>/SUMMARY.md  metadata.json  (built-in aggregator)""",
    )
    p.add_argument("--target", "-t", required=False, help="domain or URL")
    p.add_argument("--stages", "-s", default=",".join(ALL_STAGES),
                   help="comma list (default: all)")
    p.add_argument("--threads", type=int, default=10, help="workers 4-20 (default 10)")
    p.add_argument("--fast", action="store_true", help="reduced caps")
    p.add_argument("--deep", action="store_true", help="aggressive extra sources + higher caps")
    p.add_argument("--json", action="store_true", help="print summary JSON to stdout")
    p.add_argument("--list-stages", action="store_true", help="print stages and exit")
    p.add_argument("--insecure", action="store_true",
                   help="Disable TLS verification for HTTP fetches (opt-in; default verifies)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_stages:
        for s in ALL_STAGES:
            print(f"  {s:10} {STAGE_HINTS.get(s, '')}")
        return 0
    if not args.target:
        print("ERROR: --target required (or use --list-stages)")
        return 2
    if args.fast and args.deep:
        print("ERROR: --fast and --deep are mutually exclusive")
        return 2
    stages = [x.strip().lower() for x in args.stages.split(",") if x.strip()]
    bad = [x for x in stages if x not in STAGE_FUNCS]
    if bad:
        print(f"ERROR: unknown stages: {bad}\nvalid: {ALL_STAGES}")
        return 2
    return run(args.target, stages, args.threads, args.fast, args.deep, args.json,
               insecure=args.insecure)


if __name__ == "__main__":
    sys.exit(main())
