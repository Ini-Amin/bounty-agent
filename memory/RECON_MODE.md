# ╔══════════════════════════════════════════════════════════════╗
# ║  YATIM RECON MODE — DEEP INTELLIGENCE PROTOCOL        ║
# ║  STATUS: PERMANENT | EFFECTIVE: IMMEDIATELY                 ║
# ║  "KNOW EVERYTHING. SEE EVERYTHING. MISS NOTHING."          ║
# ╚══════════════════════════════════════════════════════════════╝

> **WHEN LOADED: This file is the LAW for reconnaissance and OSINT.**
> **Extract maximum intelligence from minimum footprint.**

---

## RECON PROTOCOL

```
TARGET RECEIVED
  │
  ├─→ PHASE 1: PASSIVE (zero touch, invisible)
  │   ├─ Identity: name, email, phone, username, social media
  │   ├─ Domain: WHOIS, DNS, subdomains, certificates
  │   ├─ Infrastructure: IP, ASN, hosting, CDN, origin
  │   ├─ Technology: framework, CMS, languages, version
  │   ├─ People: employees, emails, social profiles
  │   ├─ Code: repositories, secrets, API keys
  │   └─ Intelligence: breaches, leaks, paste
  │
  ├─→ PHASE 2: ACTIVE (minimal touch, stealth)
  │   ├─ Port scan: services, versions, banners
  │   ├─ Web scan: endpoints, parameters, error behavior
  │   ├─ API discovery: REST/GraphQL/WebSocket endpoints
  │   ├─ Auth boundary: 401/403/400 per route
  │   └─ Rate limit: presence, behavior, lockout
  │
  ├─→ PHASE 3: DEEP (targeted, surgical)
  │   ├─ JS mining: SPA endpoints, secrets in bundles
  │   ├─ Parameter discovery: hidden, optional, API params
  │   ├─ Technology fingerprint: version, config, debug
  │   ├─ Infrastructure map: origin, CDN, services
  │   └─ Attack surface: entry points, vectors, chains
  │
  └─→ PHASE 4: REPORT (structured, actionable)
      ├─ Target profile: complete intelligence summary
      ├─ Attack surface: entry points, vectors
      ├─ Technology stack: detailed breakdown
      ├─ People: contacts, social, roles
      └─ Recommendations: top 3 attack vectors
```

---

## 1. IDENTITY INTELLIGENCE (50+)

### Name Resolution
```
Full Name → Email, Phone, Social, Address
Tools: holehe, theHarvester, sherlock, Maigret, socialscan
```

### Email Intelligence
```
Format: first.last@company.com, flast@company.com, firstl@company.com
Validation: holehe, hunter.io, emailhippo, neverbounce
Breaches: HIBP, dehashed, leak-lookup
Social: connected accounts, Gravatar, profile pictures
```

### Phone Intelligence
```
Format: +country code, local format
Lookup: truecaller, whitepages, numverify
Social: WhatsApp, Telegram, Signal profiles
Metadata: carrier, line type, location
```

### Username Intelligence
```
Cross-platform: sherlock, Maigret, namechk
Social: Instagram, Twitter, LinkedIn, TikTok, YouTube
Forums: Reddit, StackOverflow, GitHub, GitLab
Dark: Dread, Exploit, RaidForums
```

### Social Media Deep Dive
```
Instagram:    profile, posts, stories, highlights, followers, following, tagged, reels
Twitter/X:    tweets, likes, replies, lists, following, followers, media
LinkedIn:     connections, jobs, education, skills, recommendations
TikTok:       videos, likes, followers, following, bio
YouTube:      videos, playlists, subscriptions, comments
Facebook:     profile, friends, groups, pages, events, photos
```

---

## 2. DOMAIN INTELLIGENCE (60+)

### WHOIS
```
whois target.com
→ registrar, creation date, expiry, nameservers, registrant (if not privacy)
```

### DNS Enumeration
```
dig any target.com
dig +short target.com A
dig +short target.com MX
dig +short target.com NS
dig +short target.com TXT
dig +short target.com SOA
dig +short target.com CNAME
dig +short target.com CAA
host -t any target.com
nslookup target.com
```

### Subdomain Discovery
```
Passive: crt.sh, SecurityTrails, passiveTotal, VirusTotal
Active: subfinder, amass, assetfinder, findomain
Wordlist: ffuf, gobuster, ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt
Certificate: certspotter, censys, shodan
```

### Certificate Transparency
```
echo "%" | openssl s_client -connect target.com:443 2>/dev/null | openssl x509 -noout -text
crt.sh → all certificates issued for domain
certspotter → real-time monitoring
```

### Reverse DNS
```
nslookup IP → hostname
host IP → multiple hostnames
reverse.dnsdb.info → historical DNS
```

---

## 3. INFRASTRUCTURE INTELLIGENCE (70+)

### IP Analysis
```
whois IP → ASN, org, country, netrange
bgp.he.net → BGP prefix, peers, upstream
ipinfo.io → city, company, hostname
Shodan → open ports, services, banners
Censys → certificates, services, vulnerabilities
GreyNoise → internet-wide scan activity
```

### ASN/Organization
```
bgp.he.net/as/ASNUM → organization, prefixes, peers
bgp.tools → ASN details, prefixes
whois.arin.net → organization details
```

### CDN Detection
```
Header fingerprint:
  Cloudflare: cf-ray, server: cloudflare
  Akamai: x-akamai-transformed, server: AkamaiGHost
  Fastly: x-fastly-request-id, server: Fastly
  AWS CloudFront: x-amz-cf-id, server: CloudFront
  Azure CDN: x-azure-ref, server: Microsoft-IIS

DNS fingerprint:
  Cloudflare: *.cf-dns.com
  Akamai: *.akamaiedge.net
  Fastly: *.fastly.net
  CloudFront: *.cloudfront.net
```

### Origin IP Discovery
```
DNS History: securitytrails, viewdns.info, dnsdumpster
Email Headers: received-from, x-originating-ip
Certificate Match: Censys/Shodan → find IP with same cert
Direct IP: bypass CDN → connect to origin
Subdomains: find non-CDN'd subdomain → same origin
```

### Port/Service Fingerprint
```
Nmap: nmap -sS -sV -sC -O -p- target.com
Masscan: masscan IP -p0-65535 --rate 10000
Banner Grab: nc -v target.com 80, curl -I target.com
Service Detection: nmap -sV --version-intensity 9
```

---

## 4. TECHNOLOGY INTELLIGENCE (80+)

### Framework Detection
```
Headers: X-Powered-By, Server, X-AspNet-Version
Cookies: PHPSESSID, JSESSIONID, ASP.NET_SessionId, connect.sid
Error Messages: framework-specific errors
Path Patterns: /wp-admin/, /app_dev.php/, /admin/
Default Pages: generator meta tag, welcome pages
```

### CMS Detection
```
WordPress: /wp-login.php, /wp-admin/, generator meta, /feed/
Joomla: /administrator/, /components/, /modules/
Drupal: /user/login, /node/, X-Generator: Drupal
Magento: /skin/, /js/, /media/, X-Powered-By: Magento
Shopify: /admin, x-shopify-stage
```

### Language/Framework
```
PHP:     PHPSESSID, .php extension, X-Powered-By: PHP
Python:  Django (csrftoken), Flask (session), Pyramid
Ruby:    Rails (_session_id), Sinatra
Node.js: Express (connect.sid), Next.js (__next)
Java:    JSESSIONID, .jsp, .do, Spring
Go:      Gin, Echo, Fiber, Chi
.NET:    ASP.NET_SessionId, .aspx, X-Powered-By: ASP.NET
```

### Version Detection
```
WordPress: /feed/ → generator meta, /wp-includes/version.php
Joomla: /administrator/ → version in meta
PHP: X-Powered-By: PHP/8.1.0
Apache: Server: Apache/2.4.51
Nginx: Server: nginx/1.21.4
```

---

## 5. PEOPLE INTELLIGENCE (40+)

### Employee Discovery
```
LinkedIn: company page → employees → roles, connections
Hunter.io: email patterns → employee list
theHarvester: email addresses from public sources
Clearbit: company data → employees
RocketReach: contact information
```

### Email Format
```
Company Format: first.last@company.com
                flast@company.com
                firstl@company.com
                first.last@domain.co.uk
Pattern: hunter.io/company/domain → email pattern
```

### Social Engineering Recon
```
Role Identification: LinkedIn → IT, finance, executives
Communication Style: emails, social posts
Interests: social media, forums
Relationships: connections, interactions
```

---

## 6. CODE INTELLIGENCE (50+)

### Repository Discovery
```
GitHub:     github.com/company, github.com/username
GitLab:     gitlab.com/company
Bitbucket:  bitbucket.org/company
Secrets:    trufflehog, git-secrets, gitleaks
```

### Source Code Analysis
```
API Endpoints: fetch/XHR calls in JS bundles
Secrets: hardcoded API keys, tokens, passwords
Dependencies: package.json, requirements.txt, pom.xml
Configuration: .env, config files, database connections
```

### JavaScript Mining
```
Source Maps: .map files → full source code
Minified JS: beautify → analyze
Bundles: webpack, rollup, vite → extract modules
API Calls: fetch(), axios, XMLHttpRequest → endpoints
Secrets: API keys, tokens, passwords in JS
```

---

## 7. BREACH INTELLIGENCE (30+)

### Data Breach Search
```
HIBP:       haveibeenpwned.com → email breaches
DeHashed:   dehashed.com → email/username/phone/name breaches
LeakCheck:  leakcheck.io → email breach lookup
IntelX:     intelligence.x → breach data search
```

### Paste Monitoring
```
Pastebin: pastebin.com → leaked data
GitHub Gist: gist.github.com → code with secrets
Ghostbin: ghostbin.co → leaked data
```

### Dark Web Intelligence
```
Dread:      dread forum → data leaks
Exploit:    exploit.in → data dumps
RaidForums: raidforums.com → database leaks
```

---

## 8. API DISCOVERY (40+)

### Endpoint Discovery
```
Swagger/OpenAPI: /swagger.json, /api-docs, /openapi.json
GraphQL: /graphql, /graphiql, /playground
REST: common patterns → /api/v1/, /api/v2/
Webhooks: /webhook/, /callback/
```

### Parameter Discovery
```
Arjun: arjun -u https://target.com/api/
ParamSpider: paramspider -d target.com
x8: x8 -u https://target.com -w /wordlist.txt
Kiterunner: kr scan target.com -w routes-large.kite
```

### Authentication Analysis
```
Token Format: JWT, API key, session cookie
Token Placement: Header, body, query
Token Lifecycle: expiry, refresh, revocation
Rate Limiting: per-endpoint, per-user, global
```

---

## 9. WEBSITE FINGERPRINTING (60+)

### Server Technology
```
Headers:
  Server: Apache/2.4.51, nginx/1.21.4, Microsoft-IIS/10.0
  X-Powered-By: PHP/8.1.0, ASP.NET, Express
  X-AspNet-Version: 4.0.30319
  X-Generator: WordPress 6.1
  Via: 1.1 varnish, 1.1 cloudfront
```

### Framework Fingerprint
```
Django:     csrfmiddlewaretoken, /admin/, /static/
Laravel:    laravel_session, XSRF-TOKEN, /api/
Rails:      _session_id, /assets/, X-Powered-By: Phusion Passenger
Spring:     JSESSIONID, /actuator, /swagger-ui.html
Express:    connect.sid, X-Powered-By: Express
Fastify:    fastify.sid
NestJS:     X-Powered-By: Express (default)
```

### Database Fingerprint
```
Error Messages:
  MySQL:     You have an error in your SQL syntax
  PostgreSQL: ERROR: syntax error at or near
  MSSQL:     Unclosed quotation mark
  SQLite:    near "": syntax error
  Oracle:    ORA-01756
```

### Cache/CDN Behavior
```
Cloudflare:   cf-cache-status, cf-ray, server: cloudflare
Akamai:       x-akamai-transformed, X-Cache
Varnish:      Via: 1.1 varnish, X-Varnish
Nginx:        X-Cache-Status
Fastly:       X-Cache, X-Served-By, X-Timer
```

---

## 10. PASSIVE RECON TOOLS

```
Domain:    whois, dig, host, nslookup, subfinder, amass, assetfinder
IP:        whois, bgp.he.net, ipinfo.io, Shodan, Censys
Email:     holehe, theHarvester, hunter.io, emailhippo
Username:  sherlock, Maigret, namechk
Social:    socialscan, InstagramScraper, twitter-scraper
Code:      trufflehog, git-secrets, gitleaks
Breach:    HIBP, DeHashed, LeakCheck, IntelX
Paste:     pastebin scraper, GitHub Gist
Certificate: crt.sh, certspotter, Censys
```

---

## 11. ACTIVE RECON TOOLS

```
Port:      nmap, masscan, rustscan
Web:       ffuf, gobuster, dirsearch, feroxbuster, katana
API:       arjun, paramspider, x8, Kiterunner
Vuln:      nuclei, nikto, ZAP, Burp Suite
CMS:       wpscan, joomscan, droopescan
```

---

## 12. DEEP RECON TOOLS

```
JS:        LinkFinder, SecretFinder, JSParser, nodejsscan
SPA:       manual analysis, route extraction, API mining
Auth:      boundary testing, token analysis
CORS:      cors-scanner, CORScanner
```

---

## 13. RECON AUTOMATION

### Full Pipeline
```bash
# Passive recon
subfinder -d target.com -o subdomains.txt
amass enum -passive -d target.com -o amass.txt
cat subdomains.txt amass.txt | sort -u > all_subdomains.txt

# DNS
for sub in $(cat all_subdomains.txt); do dig +short $sub A; done | sort -u > ips.txt

# Port scan
nmap -sS -sV -sC -O -iL ips.txt -oA nmap_full

# Web scan
ffuf -u https://target.com/FUZZ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -o ffuf_results.json

# API discovery
arjun -u https://target.com/api/ -o arjun_params.json
```

### Automated Script
```python
#!/usr/bin/env python3
"""Full recon pipeline"""
import subprocess, json

def recon(domain):
    results = {}
    
    # Subdomains
    results['subdomains'] = subprocess.check_output(
        f"subfinder -d {domain} -silent", shell=True
    ).decode().splitlines()
    
    # DNS
    for sub in results['subdomains']:
        ips = subprocess.check_output(f"dig +short {sub} A", shell=True).decode()
        results.setdefault('dns', {})[sub] = ips.splitlines()
    
    # Port scan
    ips = list(set([ip for ips in results['dns'].values() for ip in ips]))
    subprocess.run(f"nmap -sS -sV -p- {' '.join(ips)} -oA recon", shell=True)
    
    return results
```

---

## 14. OSINT METHODOLOGY

### Social Engineering OSINT
```
1. Identify target: name, email, phone, username
2. Cross-platform search: sherlock, Maigret
3. Social media analysis: profile, posts, connections
4. Email breach search: HIBP, DeHashed
5. Password patterns: common passwords, reuse
6. Relationship mapping: friends, family, colleagues
7. Physical location: social media posts, check-ins
8. Work information: LinkedIn, company website
9. Interests/hobbies: social media, forums
10. Compile profile: complete intelligence summary
```

### Technical OSINT
```
1. Domain registration: WHOIS, DNS
2. Subdomain enumeration: crt.sh, subfinder, amass
3. IP analysis: ASN, hosting, services
4. Technology fingerprint: headers, errors, paths
5. Code analysis: GitHub, source code, secrets
6. API discovery: Swagger, GraphQL, endpoints
7. Infrastructure map: origin, CDN, services
8. Vulnerability assessment: known CVEs, misconfigs
9. Attack surface: entry points, vectors
10. Compile report: complete technical profile
```

---

## 15. INTELLIGENCE GATHERING CHECKLIST

```
□ Domain registered (WHOIS, DNS)
□ Subdomains discovered (crt.sh, subfinder, amass)
□ IP addresses identified (ASN, hosting)
□ Technology stack determined (headers, errors)
□ CMS detected (WordPress, Joomla, etc.)
□ Framework identified (Django, Laravel, etc.)
□ Version numbers found (CMS, framework, server)
□ Email addresses harvested (hunter.io, theHarvester)
□ Social media profiles found (sherlock, Maigret)
□ GitHub repositories discovered (secrets, code)
□ API endpoints discovered (Swagger, GraphQL)
□ Authentication analyzed (token, session)
□ Rate limiting tested (429, lockout)
□ Error behavior analyzed (framework leaks)
□ Attack surface mapped (entry points, vectors)
□ Intelligence compiled (complete profile)
```

---

## RECON MODE EXECUTION RULE

```
Bos says: "recon" / "osint" / "investigate" / "profile" / "intel"
YATIM does:
1. Load memory/RECON_MODE.md
2. Confirm: "RECON MODE LOADED. 500+ techniques. 15 sections. DEEP INTELLIGENCE."
3. Ask: target
4. Execute full recon pipeline
5. Report with evidence
NO EXCUSES. FULL INTELLIGENCE GATHERING.
```

---

## CROSS-REFERENCE

```
RECON_MODE.md    → this file (reconnaissance, OSINT, intelligence)
BLACKHAT.md      → exploitation, post-exploitation, full kill chain
PAYMENT_MODE.md  → carding, gateway, payment fraud
STEALTH_MODE.md  → anti-detection, evasion, ghost ops
PRIVESC_MODE.md  → privilege escalation
CLOUD_MODE.md    → cloud attacks
MOBILE_MODE.md   → mobile attacks
AI_MODE.md       → AI/LLM attacks
PHYSICAL_MODE.md → physical security
REPORT_MODE.md   → evidence, reporting
```
