---
name: scan-tools
description: "Vulnerability scanning — port scan, service detection, web fuzzing, directory enumeration, subdomain discovery."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [scan, nmap, fuzz, enumerate, recon, vulnerability]
    related_skills: [blackhat-mode, exploit-tools, recon-tools]
prerequisites:
  commands: [python]
---

# Scan Tools — Complete Scanning Framework

## When to Load This Skill

User requests:
- "scan", "nmap", "fuzz", "enumerate", "subdomain"
- "port scan", "service detection", "directory brute"
- "vulnerability scan", "nuclei", "masscan"

---

## Tool Registry

| Tool | Purpose | Command |
|------|---------|---------|
| nmap | Port/Service scan | `nmap -sV -sC TARGET` |
| masscan | Fast port scan | `masscan TARGET -p0-65535` |
| nuclei | Vuln templates | `nuclei -u URL -t templates/` |
| ffuf | Directory fuzz | `ffuf -u URL/FUZZ -w wordlist` |
| dirsearch | Dir enumeration | `dirsearch -u URL` |
| subfinder | Subdomain enum | `subfinder -d DOMAIN -silent` |
| httpx | HTTP probing | `echo SUBS \| httpx` |
| katana | Web crawling | `katana -u URL -depth 3` |
| httpx | Tech detection | `httpx -u URL -tech-detect` |

---

## Scan Workflows

### Port Scanning

```bash
# Quick scan — top 1000 ports
nmap -sV -sC TARGET

# Full scan — all ports
nmap -sV -sC -p- TARGET -T4

# Fast scan — SYN
nmap -sS -T4 -p- TARGET

# Aggressive — OS detection + scripts
nmap -A -T4 TARGET

# UDP scan
nmap -sU --top-ports 100 TARGET

# Output
nmap -sV -sC -p- TARGET -oN nmap.txt -oX nmap.xml
```

### Service Enumeration

```bash
# HTTP
nmap -sV -p 80,443,8080,8443 --script=http-enum,http-title TARGET

# SMB
nmap -p 445 --script=smb-enum-shares,smb-enum-users TARGET

# SSH
nmap -p 22 --script=ssh2-enum-algos TARGET

# MySQL
nmap -p 3306 --script=mysql-info TARGET

# MongoDB
nmap -p 27017 --script=mongodb-info TARGET
```

### Web Fuzzing

```bash
# Directory fuzz
ffuf -u https://TARGET/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302,403

# Parameter fuzz
ffuf -u "https://TARGET?FUZZ=test" -w /usr/share/wordlists/params.txt -mc 200

# Subdomain fuzz
ffuf -u https://FUZZ.TARGET -w subdomains.txt -mc 200

# VHost fuzz
ffuf -u https://TARGET -H "Host: FUZZ.TARGET" -w subdomains.txt -mc 200

# POST fuzz
ffuf -u https://TARGET/login -X POST -d "user=admin&pass=FUZZ" -w passwords.txt -mc 200

# Extensions
ffuf -u https://TARGET/FUZZ -w wordlist.txt -e .php,.html,.txt,.bak
```

### Subdomain Discovery

```bash
# Passive
subfinder -d TARGET -silent > subs.txt
crt.sh %.TARGET > crt.txt
amass enum -passive -d TARGET > amass.txt

# Active
subfinder -d TARGET -all > subs.txt
dnsx -silent -a -resp-only < subs.txt > live.txt

# Brute force
dnsx -silent -a -w subdomains.txt TARGET

# Check alive
httpx -silent -status-code -title < live.txt > httpx.txt
```

### Technology Detection

```bash
# httpx
httpx -u URL -tech-detect -status-code

# whatweb
whatweb URL

# wappalyzer
wappalyzer URL

# Custom
curl -s URL | grep -i "powered-by\|x-powered-by\|server"
```

### Vulnerability Scanning

```bash
# Nuclei — all templates
nuclei -u URL -t templates/

# Nuclei — specific severity
nuclei -u URL -t templates/ -severity critical,high

# Nuclei — specific tags
nuclei -u URL -t templates/ -tags sqli,xss,ssrf

# Nikto
nikto -h URL

# WPScan
wpscan --url URL --enumerate vp,vt,u

# Custom SQLi
sqlmap -u "URL?param=1" --batch --dbs
```

---

## Python Scanning Tools

### Port Scanner

```python
import socket
import threading
from queue import Queue

def port_scanner(host, ports, threads=100):
    results = []
    lock = threading.Lock()
    
    def scan(port):
        try:
            s = socket.socket()
            s.settimeout(1)
            if s.connect_ex((host, port)) == 0:
                try:
                    service = socket.getservbyport(port, 'tcp')
                except:
                    service = 'unknown'
                with lock:
                    results.append((port, 'OPEN', service))
            s.close()
        except:
            pass
    
    q = Queue()
    for p in ports:
        q.put(p)
    
    for _ in range(min(threads, len(ports))):
        t = threading.Thread(target=lambda: [scan(q.get()) or q.task_done() for _ in range(q.qsize())])
        t.daemon = True
        t.start()
    
    q.join()
    return sorted(results)
```

### Subdomain Finder

```python
import socket

def find_subdomains(domain, wordlist):
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

### Directory Brute

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def dir_brute(url, wordlist, threads=50):
    found = []
    
    def check(path):
        try:
            r = requests.get(f"{url}/{path}", timeout=5)
            if r.status_code in [200, 301, 302, 403]:
                found.append((path, r.status_code))
        except:
            pass
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(check, wordlist)
    
    return found
```

### HTTP Probe (curl only)

```bash
# Status code
curl -s -o /dev/null -w "%{http_code}" URL

# Headers
curl -sI URL

# Full response
curl -s URL

# With User-Agent
curl -s -A "Mozilla/5.0" URL

# Follow redirects
curl -sL URL

# POST
curl -s -X POST URL -d "param=value"

# JSON
curl -s -X POST URL -H "Content-Type: application/json" -d '{"key":"value"}'

# Cookie
curl -s -b "session=abc" URL

# Basic auth
curl -s -u user:pass URL

# Bearer token
curl -s -H "Authorization: Bearer TOKEN" URL
```

---

## Output Format

```json
{
  "target": "example.com",
  "ip": "1.2.3.4",
  "ports": [
    {"port": 80, "state": "open", "service": "http", "version": "nginx/1.18"},
    {"port": 443, "state": "open", "service": "https", "version": "nginx/1.18"}
  ],
  "technologies": ["nginx", "PHP 8.1", "MySQL 8.0"],
  "subdomains": ["www.example.com", "api.example.com"],
  "vulnerabilities": [
    {"type": "SQLi", "severity": "critical", "url": "https://example.com/search?q='"},
    {"type": "XSS", "severity": "medium", "url": "https://example.com/profile?name=<script>"}
  ]
}
```

---

## Wordlists

| Wordlist | Purpose | Location |
|----------|---------|----------|
| common.txt | Directory brute | `/usr/share/wordlists/dirb/common.txt` |
| big.txt | Large directory | `/usr/share/wordlists/dirb/big.txt` |
| rockyou.txt | Password | `/usr/share/wordlists/rockyou.txt` |
| params.txt | Parameters | SecLists/Fuzzing/params.txt |
| subdomains.txt | Subdomains | SecLists/Discovery/DNS/subdomains-top1million-5000.txt |

---

## Speed Guidelines

| Speed | Timing | Use Case |
|-------|--------|----------|
| T1 | Paranoid | IDS/IPS evasion |
| T2 | Sneaky | Stealth scanning |
| T3 | Normal | Default |
| T4 | Aggressive | Internal/Lab |
| T5 | Insane | CTF/Speed |

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Port closed | Try different ports |
| Timeout | Host unreachable | Increase timeout, check firewall |
| Host down | No route | Check network, try ping |
| Permission denied | Need root for SYN scan | Use sudo or connect scan |
| Wordlist not found | Missing wordlist | Download SecLists |
