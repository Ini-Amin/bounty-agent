---
name: mitre-tools
description: "MITRE ATT&CK mapping — tactics, techniques, procedures (TTP) alignment."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [mitre, attck, ttp, tactics, techniques]
    related_skills: [blackhat-mode, report-tools]
prerequisites:
  commands: [python]
---

# MITRE ATT&CK Mapping Tools

## When to Load This Skill

User requests:
- "MITRE", "ATT&CK", "TTP", "tactics", "techniques"

---

## Tactics (14)

```
TA0043  Reconnaissance
TA0042  Resource Development
TA0001  Initial Access
TA0002  Execution
TA0003  Persistence
TA0004  Privilege Escalation
TA0005  Defense Evasion
TA0006  Credential Access
TA0007  Discovery
TA0008  Lateral Movement
TA0009  Collection
TA0011  Command and Control
TA0010  Exfiltration
TA0040  Impact
```

## Key Techniques

### Initial Access

```
T1190  Exploit Public-Facing Application
T1133  External Remote Services
T1200  Hardware Additions
T1566  Phishing
T1078  Valid Accounts
```

### Execution

```
T1059  Command and Scripting Interpreter
T1203  Exploitation for Client Execution
T1053  Scheduled Task/Job
T1204  User Execution
T1047  Windows Management Instrumentation
```

### Persistence

```
T1098  Account Manipulation
T1136  Create Account
T1543  Create or Modify System Process
T1547  Boot or Logon Autostart Execution
T1505  Server Software Component
T1053  Scheduled Task/Job
```

### Privilege Escalation

```
T1548  Abuse Elevation Control Mechanism
T1134  Access Token Manipulation
T1547  Boot or Logon Autostart Execution
T1068  Exploitation for Privilege Escalation
T1055  Process Injection
```

### Defense Evasion

```
T1070  Indicator Removal
T1027  Obfuscated Files or Information
T1055  Process Injection
T1562  Impair Defenses
T1078  Valid Accounts
T1140  Deobfuscate/Decode Files or Information
```

### Credential Access

```
T1110  Brute Force
T1003  OS Credential Dumping
T1056  Input Capture
T1557  Adversary-in-the-Middle
T1552  Unsecured Credentials
T1555  Credentials from Password Stores
```

### Lateral Movement

```
T1210  Exploitation of Remote Services
T1570  Lateral Tool Transfer
T1021  Remote Services
T1550  Use Alternate Authentication Material
T1080  Taint Shared Content
```

### Command & Control

```
T1071  Application Layer Protocol
T1573  Encrypted Channel
T1572  Protocol Tunneling
T1090  Proxy
T1105  Ingress Tool Transfer
```

### Exfiltration

```
T1041  Exfiltration Over C2 Channel
T1048  Exfiltration Over Alternative Protocol
T1567  Exfiltration Over Web Service
T1029  Scheduled Transfer
```

---

## Python MITRE Tools

### TTP Mapper

```python
def map_finding_to_mitre(finding):
    mapping = {
        'sql injection': 'T1190',
        'xss': 'T1059.007',
        'ssrf': 'T1090',
        'rce': 'T1059',
        'idor': 'T1078',
        'file upload': 'T1505',
    }
    
    for key, technique in mapping.items():
        if key in finding.lower():
            return technique
    
    return None
```

### Report Enrichment

```python
def enrich_report(findings):
    enriched = []
    
    for finding in findings:
        technique = map_finding_to_mitre(finding['type'])
        enriched.append({
            **finding,
            'mitre_technique': technique,
            'mitre_tactic': get_tactic(technique)
        })
    
    return enriched
```

---

## Output Format

```json
{
  "finding": "SQL Injection",
  "mitre": {
    "tactic": "Initial Access",
    "technique": "T1190",
    "name": "Exploit Public-Facing Application"
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No mapping | Unknown finding | Manual mapping |
| Wrong technique | Ambiguous finding | Review manually |
