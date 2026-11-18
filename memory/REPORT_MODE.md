# ╔══════════════════════════════════════════════════════════════╗
# ║  YATIM REPORT MODE — EVIDENCE & REPORTING PROTOCOL    ║
# ║  STATUS: PERMANENT | EFFECTIVE: IMMEDIATELY                 ║
# ║  "NO EVIDENCE = NO FINDING. PROVE EVERYTHING."              ║
# ╚══════════════════════════════════════════════════════════════╝

> **WHEN LOADED: This file is the LAW for evidence and reporting.**
> **Every claim must have proof. Every finding must be verifiable.**

---

## REPORT PROTOCOL

```
FINDING IDENTIFIED
  │
  ├─→ PHASE 1: EVIDENCE CAPTURE
  │   ├─ HTTP: full request + response
  │   ├─ Command: exact command + output
  │   ├─ Code: file path + line number
  │   ├─ Screenshot: annotated, timestamped
  │   └─ Reproducibility: steps to verify
  │
  ├─→ PHASE 2: CLASSIFICATION
  │   ├─ Severity: CRITICAL / HIGH / MEDIUM / LOW / INFO
  │   ├─ Verdict: SOLID / PLAUSIBLE / OVERSTATED / UNVERIFIABLE
  │   ├─ Type: vulnerability / misconfiguration / information disclosure
  │   └─ Impact: what an attacker can achieve
  │
  ├─→ PHASE 3: DOCUMENTATION
  │   ├─ Title: clear, descriptive
  │   ├─ Summary: one paragraph
  │   ├─ Description: detailed explanation
  │   ├─ Steps: reproducible steps
  │   ├─ Evidence: HTTP req/resp, code, screenshots
  │   ├─ Impact: business impact
  │   └─ Remediation: fix recommendations
  │
  └─→ PHASE 4: SUBMISSION
      ├─ Format: structured report
      ├─ Platform: Bugcrowd, HackerOne, internal
      ├─ Compliance: follow reporting guidelines
      └─ Follow-up: respond to triage questions
```

---

## 1. EVIDENCE STANDARDS (40+)

### HTTP Evidence
```
Request:
  Method + URL + Headers + Body
  
Response:
  Status Code + Headers + Body
  
Reproducible:
  curl command or Burp request file
```

### Command Evidence
```
Command:
  exact command with parameters
  
Output:
  complete, unedited output
  
Reproducible:
  same command, same result
```

### Code Evidence
```
File:
  complete file path
  
Line:
  exact line number
  
Context:
  surrounding lines for context
```

### Screenshot Evidence
```
Annotations:
  highlight relevant areas
  
Timestamp:
  visible date/time
  
Context:
  show surrounding UI
```

### Reproducibility
```
Steps:
  numbered, clear steps
  
Prerequisites:
  what is needed before
  
Expected:
  what should happen
```

---

## 2. VERDICT HIERARCHY (20+)

### SOLID
```
Definition:   reproduced, evidence on disk, anyone can verify
Confidence:   HIGH
Evidence:     HTTP req/resp, command output, screenshots
Reproducible: YES, by anyone
```

### PLAUSIBLE
```
Definition:   consistent with evidence but not independently confirmed
Confidence:   MEDIUM
Evidence:     partial, consistent
Reproducible: MAYBE, depends on conditions
```

### OVERSTATED
```
Definition:   evidence contradicts the claim (refuted)
Confidence:   LOW
Evidence:     contradicts claim
Reproducible: NO
```

### UNVERIFIABLE
```
Definition:   cannot be tested with current access
Confidence:   UNKNOWN
Evidence:     none or insufficient
Reproducible: NO, needs auth/write
```

---

## 3. SEVERITY CLASSIFICATION (20+)

### CRITICAL
```
Impact:     complete system compromise, data breach
Examples:   unauthenticated RCE, SQL injection with data exfil, auth bypass
CVSS:       9.0-10.0
```

### HIGH
```
Impact:     significant data exposure, privilege escalation
Examples:   stored XSS, SSRF, IDOR with sensitive data
CVSS:       7.0-8.9
```

### MEDIUM
```
Impact:     limited data exposure, limited functionality impact
Examples:   reflected XSS, CSRF, information disclosure
CVSS:       4.0-6.9
```

### LOW
```
Impact:     minimal impact, defense-in-depth missing
Examples:   missing headers, verbose errors, minor misconfig
CVSS:       0.1-3.9
```

### INFO
```
Impact:     no direct security impact, informational
Examples:   technology disclosure, internal IP, version info
CVSS:       0.0
```

---

## 4. REPORT TEMPLATES (30+)

### Bugcrowd Report
```
Title: [Vulnerability Type] in [Endpoint/Feature]
Summary: One paragraph description
Steps:
  1. Step one
  2. Step two
  3. Step three
Impact: What an attacker can achieve
Remediation: How to fix
References: CVE, OWASP, etc.
```

### HackerOne Report
```
Title: [Vulnerability Type] in [Endpoint/Feature]
Summary: One paragraph description
Vulnerability Details: detailed explanation
Steps:
  1. Step one
  2. Step two
  3. Step three
Impact: What an attacker can achieve
Remediation: How to fix
Supporting Material: HTTP req/resp, screenshots
```

### Internal Report
```
Executive Summary: one paragraph, main verdict
Findings Table: ID | Title | Severity | Verification | Evidence | Endpoint
Per-Finding Detail: description, evidence, impact, fix
Unverified Section: honest about what needs auth/write
Prioritized Fix List: ordered by impact × ease
```

---

## 5. EVIDENCE COLLECTION TOOLS (20+)

```
HTTP:       Burp Suite, mitmproxy, curl, httpie
SCREENSHOT: built-in, greenshot, snipping tool
COMMAND:    terminal output, PowerShell
CODE:       IDE, text editor, git
NETWORK:    Wireshark, tcpdump, nmap
FILE:       file listing, hash calculation
```

---

## 6. REPORT FORMATTING (30+)

### Markdown
```
# Title
## Summary
## Steps
1. Step one
2. Step two
## Evidence
```http
GET /endpoint HTTP/1.1
Host: target.com
```
```json
{"response": "data"}
```
## Impact
## Remediation
```

### Code Blocks
```
HTTP Request:
```http
POST /api/login HTTP/1.1
Host: target.com
Content-Type: application/json

{"username":"admin","password":"admin123"}
```

HTTP Response:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{"token":"eyJhbGciOiJIUzI1NiJ9..."}
```
```

### Screenshots
```
Annotate:    highlight relevant areas
Timestamp:   visible date/time
Context:     show surrounding UI
```

---

## 7. EVIDENCE HYGIENE (40+)

### Cookie Redaction
```
Mask:        session cookies in screenshots
Hide:        Preview annotation in Burp
Filter:      HAR file sanitization
```

### PII Black-Bar
```
Mask:        names, emails, phones, faces
Safe:        usernames, trace IDs, request bodies
```

### HAR Sanitization
```
jq filter:   remove Cookie/Set-Cookie/Authorization headers
```

### Screenshot Hygiene
```
Order:       capture sequence
Filename:    descriptive, timestamped
```

---

## 8. REPORTING CHECKLIST

```
□ Evidence collected (HTTP, command, code, screenshots)
□ Verdict assigned (SOLID/PLAUSIBLE/OVERSTATED/UNVERIFIABLE)
□ Severity classified (CRITICAL/HIGH/MEDIUM/LOW/INFO)
□ Report written (title, summary, steps, evidence, impact)
□ Evidence sanitized (cookies, PII, sensitive data)
□ Reproducibility verified (steps are clear)
□ Report formatted (markdown, code blocks)
□ Platform guidelines followed (Bugcrowd, HackerOne)
□ References included (CVE, OWASP)
□ Report reviewed (no errors, complete)
```

---

## 9. TRIAGE VALIDATION (30+)

### 7-Question Gate
```
1. Is the vulnerability real?
2. Is it reproducible?
3. Is the impact accurately assessed?
4. Is the evidence sufficient?
5. Is the report clear?
6. Is the remediation actionable?
7. Is the submission compliant?
```

### Pre-Submission Gates
```
□ No false positives (verdict is SOLID)
□ Impact is not overstated
□ Evidence is complete
□ Report is clear and actionable
```

### Always-Rejected
```
Theoretical issues without proof
Issues out of scope
Low-impact issues without chain
```

---

## 10. REPORTING TOOLS

```
REPORT:     Markdown editor, code formatter
EVIDENCE:   Burp Suite, mitmproxy, curl
SCREENSHOT: built-in, greenshot, snipping tool
HAR:        HAR editor, jq filter
TEMPLATE:   Bugcrowd/HackerOne templates
```

---

## REPORT MODE EXECUTION RULE

```
Bos says: "report" / "evidence" / "verdict" / "severity" / "document" / "triage"
YATIM does:
1. Load memory/REPORT_MODE.md
2. Confirm: "REPORT MODE LOADED. 200+ techniques. 10 sections. EVIDENCE-FIRST REPORTING."
3. Ask: finding, objective
4. Capture → Classify → Document → Submit
NO EXCUSES. NO EVIDENCE = NO FINDING.
```

---

## CYBERMES REPORT PIPELINE (diambil metodenya saja — tanpa artefak cybermes)

```
reports/<slug>/
  findings/[SEVERITY]_<vuln>.md   # per temuan: ringkasan + CVSS/CWE + akar +
                                  # prasyarat + reproduksi + HTTP mentah + PoC + dampak + remediasi
  pocs/poc_<vuln>.py              # PoC standalone runnable
  evidence/                       # trace HTTP mentah, screenshot
  SUMMARY.md                      # matriks agregat (Critical>High>Medium>Low>Info)
  metadata.json                   # hitungan machine-readable
```

Template tiap finding (9 seksi, urut):

| # | Seksi | Isi |
|---|---|---|
| 1 | Ringkasan | severity + CVSS + CWE + aset + endpoint |
| 2 | Deskripsi teknis | root cause |
| 3 | Prasyarat | auth/scope/kondisi |
| 4 | Reproduksi | langkah demi langkah |
| 5 | Bukti HTTP | request/response mentah |
| 6 | PoC minimal | python runnable |
| 7 | Dampak | skenario nyata |
| 8 | Remediasi | pendek + panjang + ref |
| 9 | Jejak | dual-account matrix (A vs B) bila auth |

LAW: hanya dampak reproduksibel yang jadi finding. Ide belum terbukti = CAND/MID.
Evasion bypass / captcha solve TIDAK PERNAH jadi finding (sarana, bukan dampak).

---

## CROSS-REFERENCE

```
REPORT_MODE.md    → this file (evidence collection, verdicts, reporting)
BLACKHAT.md       → exploitation, post-exploitation, full kill chain
RECON_MODE.md     → reconnaissance, OSINT, intelligence
PAYMENT_MODE.md   → carding, gateway, payment fraud
STEALTH_MODE.md   → anti-detection, evasion, ghost ops
PRIVESC_MODE.md   → privilege escalation
CLOUD_MODE.md     → cloud attacks
MOBILE_MODE.md    → mobile attacks
AI_MODE.md        → AI/LLM attacks
PHYSICAL_MODE.md  → physical security
```
