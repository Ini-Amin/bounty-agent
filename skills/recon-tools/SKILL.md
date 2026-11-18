---
name: recon-tools
description: "Reconnaissance toolkit — OSINT, subdomain scan, port enumeration, service detection."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [recon, osint, scanning, enumeration, intel]
    related_skills: [blackhat-carding, blackhat-exploit]
prerequisites:
  commands: [python, nmap, subfinder, httpx]
---

# Blackhat Recon Skill

## When to Use

User requests:
- "recon", "osint", "investigate", "profile", "intel"
- "scan target", "enumerate services", "find vulnerabilities"
- "subdomain scan", "port scan", "service detection"
- Any reconnaissance related request

## Core Principle

**Exhaustive, continuous, methodical.**

Gather everything. Leave no stone unturned.

## Tool Registry

| Tool | Purpose | Command |
|------|---------|---------|
| `nmap` | Port scanning | `nmap -sV -sC TARGET` |
| `subfinder` | Subdomain enumeration | `subfinder -d TARGET -silent` |
| `httpx` | HTTP probing | `echo SUBS \| httpx -silent -status-code` |
| `katana` | Web crawling | `katana -u URL -silent -depth 3` |
| `nuclei` | Vulnerability scanning | `nuclei -u URL -t templates/` |
| Python scripts | Custom recon | See tools below |

## Recon Workflow

### Phase 1: Passive Recon

```bash
# Subdomain enumeration
subfinder -d TARGET -silent > subdomains.txt

# DNS resolution
cat subdomains.txt | dnsx -silent -a -resp-only > live.txt

# Technology detection
cat live.txt | httpx -silent -title -tech-detect > tech.txt
```

### Phase 2: Active Scanning

```bash
# Port scanning
nmap -sV -sC -p- TARGET -oN nmap.txt

# Directory fuzzing
ffuf -u URL/FUZZ -w wordlist.txt -mc 200,301,302,403

# Parameter mining
cat urls.txt | paramspider -quiet > params.txt
```

### Phase 3: Web Analysis

```bash
# JavaScript analysis
katana -u URL -silent -depth 3 -jc > js_urls.txt

# Secret extraction
cat js_urls.txt | grep -iE "(api|key|token|secret|password)" > secrets.txt

# API endpoint discovery
cat js_urls.txt | grep -E "(api|v1|v2|graphql|rest)" > api_endpoints.txt
```

### Phase 4: Vulnerability Assessment

```bash
# Nuclei scan
nuclei -u URL -t templates/ -severity critical,high,medium -o vulns.txt

# SQL injection test
sqlmap -u "URL?param=1" --batch --banner

# XSS test
dalfox url URL --silence
```

## Python Recon Tools

### IP Lookup
```python
import requests
def ip_lookup(ip):
    resp = requests.get(f"http://ip-api.com/json/{ip}")
    return resp.json()
```

### Port Scanner
```python
import socket
def port_scan(host, ports):
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    return open_ports
```

### Subdomain Brute
```python
import socket
def subdomain_brute(domain, wordlist):
    found = []
    for sub in wordlist:
        try:
            hostname = f"{sub}.{domain}"
            socket.gethostbyname(hostname)
            found.append(hostname)
        except:
            pass
    return found
```

## Output Format

```json
{
  "target": "example.com",
  "subdomains": ["www.example.com", "api.example.com"],
  "open_ports": [80, 443, 8080],
  "technologies": ["nginx", "PHP", "MySQL"],
  "vulnerabilities": [
    {"type": "SQLi", "severity": "critical", "url": "URL?id=1"},
    {"type": "XSS", "severity": "medium", "url": "URL?q=test"}
  ]
}
```

## Report Generation

After recon, generate report:

```bash
# Create report directory
mkdir -p reports/TARGET

# Save results
echo "Recon Report for TARGET" > reports/TARGET/RECON.md
echo "========================" >> reports/TARGET/RECON.md
cat subdomains.txt >> reports/TARGET/RECON.md
cat nmap.txt >> reports/TARGET/RECON.md
cat vulns.txt >> reports/TARGET/RECON.md
```
