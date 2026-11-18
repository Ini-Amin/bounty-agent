---
name: report-tools
description: "Reporting — CVSS scoring, evidence capture, structured markdown reports."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [report, evidence, cvss, severity, document]
    related_skills: [blackhat-mode, exploit-tools, triage-validation]
prerequisites:
  commands: [python]
---

# Reporting Tools

## When to Load This Skill

User requests:
- "report", "evidence", "verdict", "severity", "document", "triage"

---

## CVSS Scoring

### CVSS 3.1 Calculator

```
Critical (9.0-10.0): CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
High (7.0-8.9): CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N
Medium (4.0-6.9): CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N
Low (0.1-3.9): CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N
```

### Scoring Guide

| Metric | Value | Description |
|--------|-------|-------------|
| AV:N | Network | Adjacent/Audio/None |
| AC:L | Low | Attack complexity |
| PR:N | None | Privileges required |
| UI:N | None | User interaction |
| S:U | Unchanged | Scope changed |
| C:H | High | Confidentiality impact |
| I:H | High | Integrity impact |
| A:H | High | Availability impact |

---

## Evidence Capture

### HTTP Requests

```bash
# Request with headers
curl -v -X POST URL \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}' \
  > evidence_request.txt

# Response with headers
curl -sI URL > evidence_headers.txt

# Full response
curl -s URL > evidence_response.txt
```

### Screenshots

```bash
# CLI screenshot
import subprocess
subprocess.run(['screenshot_tool', '-o', 'screenshot.png'])
```

### HAR Files

```bash
# Capture traffic
mitmdump -p 8080 -w traffic.flow

# Convert to HAR
python convert_har.py traffic.flow > evidence.har
```

---

## Report Template

```markdown
# [SEVERITY] Finding Title

## Summary
Brief description of the vulnerability.

## Affected Endpoint
`METHOD /path/to/endpoint`

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Impact
What an attacker can achieve.

## Recommendation
How to fix the issue.

## Evidence
- Request/Response
- Screenshots
- CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8

## References
- CWE-XXX
- OWASP-XXX
```

---

## Python Report Tools

### CVSS Calculator

```python
def calculate_cvss(vector):
    # Simplified CVSS calculator
    score = 0.0
    # ... implementation
    return score
```

### Report Generator

```python
def generate_report(findings):
    report = "# Security Assessment Report\n\n"
    
    for finding in findings:
        report += f"## {finding['severity']} - {finding['title']}\n\n"
        report += f"**Endpoint:** `{finding['method']} {finding['endpoint']}`\n\n"
        report += f"**Steps:**\n{finding['steps']}\n\n"
        report += f"**Impact:** {finding['impact']}\n\n"
        report += f"**CVSS:** {finding['cvss']}\n\n"
        report += "---\n\n"
    
    return report
```

---

## Output Format

```json
{
  "report": {
    "title": "Security Assessment",
    "date": "2024-01-01",
    "findings": [
      {
        "severity": "CRITICAL",
        "title": "SQL Injection",
        "endpoint": "POST /api/search",
        "cvss": 9.8,
        "steps": "1. Send payload...",
        "impact": "Full database access"
      }
    ]
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Missing evidence | Incomplete capture | Re-capture |
| CVSS wrong | Incorrect metrics | Re-score |
| Report incomplete | Missing sections | Add sections |
