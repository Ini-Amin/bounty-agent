---
name: mobile-tools
description: "Mobile security — APK analysis, Frida hooking, SSL pinning bypass, root detection."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [mobile, android, ios, apk, frida, ssl, pinning, root]
    related_skills: [blackhat-mode, exploit-tools, re-tools]
prerequisites:
  commands: [python]
---

# Mobile Security Tools

## When to Load This Skill

User requests:
- "mobile", "android", "iOS", "APK", "Frida", "SSL pinning"
- "root detection", "bypass", "hook"

---

## APK Analysis

### Decompile

```bash
# apktool
apktool d app.apk

# jadx
jadx app.apk -d output/

# dex2jar
d2j-dex2jar app.apk -o app.jar

# JD-GUI
jd-gui app.jar
```

### Manifest Analysis

```bash
# Permissions
grep -i "permission" AndroidManifest.xml

# Activities
grep -i "activity" AndroidManifest.xml

# Services
grep -i "service" AndroidManifest.xml

# Receivers
grep -i "receiver" AndroidManifest.xml
```

### Code Analysis

```bash
# Search for secrets
grep -r "api_key\|secret\|password\|token" smali/

# Search for hardcoded URLs
grep -r "http://\|https://" smali/

# Search for crypto
grep -r "Cipher\|SecretKey\|AES\|RSA" smali/
```

### Sign & Install

```bash
# Sign
apksigner sign --ks keystore.jks app.apk

# Verify
apksigner verify --verbose app.apk

# Install
adb install app.apk

# Install with replacement
adb install -r app.apk
```

---

## Frida

### Setup

```bash
# Server
adb push frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell /data/local/tmp/frida-server &

# Check
frida-ps -U
```

### Hook Methods

```javascript
// hook.js
Java.perform(function() {
    var TargetClass = Java.use('com.target.ClassName');
    
    TargetClass.methodName.implementation = function(arg1, arg2) {
        console.log('methodName called with: ' + arg1 + ', ' + arg2);
        return this.methodName(arg1, arg2);
    };
});
```

### SSL Pinning Bypass

```javascript
// ssl_bypass.js
Java.perform(function() {
    var TrustManager = Java.registerClass({
        name: 'com.bypass.TrustManager',
        implements: [Java.use('javax.net.ssl.X509TrustManager')],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });
    
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    var ctx = SSLContext.getInstance('TLS');
    ctx.init(null, [TrustManager.$new()], null);
});
```

### Root Detection Bypass

```javascript
// root_bypass.js
Java.perform(function() {
    var RootBeer = Java.use('com.scottyab.rootbeer.RootBeer');
    RootBeer.isRooted.implementation = function() {
        return false;
    };
});
```

### Keylogger

```javascript
// keylogger.js
Java.perform(function() {
    var EditText = Android.widget.EditText;
    EditText.setText.implementation = function(text) {
        console.log('Input: ' + text);
        return this.setText(text);
    };
});
```

### Run Frida

```bash
# Spawn
frida -U -f com.target.app -l hook.js --no-pause

# Attach
frida -U com.target.app -l hook.js

# Script
frida -U -l hook.js com.target.app
```

---

## SSL Pinning

### Burp Suite

```bash
# Install Burp CA
# Android 7+
adb push Burp.crt /data/local/tmp/
adb shell su -c "cp /data/local/tmp/Burp.crt /system/etc/security/cacerts/"

# Or
adb shell su -c "mount -o remount,rw /system"
adb shell su -c "cp /data/local/tmp/Burp.crt /system/etc/security/cacerts/"
adb shell su -c "mount -o remount,ro /system"
```

### Objection

```bash
# Install
pip install objection

# Bypass SSL
objection -g com.target.app explore
android sslpinning disable
```

### Custom Certificate

```java
// TrustAllCerts.java
public class TrustAllCerts implements X509TrustManager {
    public void checkClientTrusted(X509Certificate[] chain, String authType) {}
    public void checkServerTrusted(X509Certificate[] chain, String authType) {}
    public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
}
```

---

## Storage Analysis

### Android

```bash
# Databases
adb pull /data/data/com.target.app/databases/

# Shared Preferences
adb pull /data/data/com.target.app/shared_prefs/

# Files
adb pull /data/data/com.target.app/files/

# Cache
adb pull /data/data/com.target.app/cache/
```

### iOS

```bash
# Keychain
frida -U -f com.target.app -l dump_keychain.js

# UserDefaults
frida -U -f com.target.app -l dump_defaults.js

# Files
frida -U -f com.target.app -l dump_files.js
```

---

## Python Mobile Tools

### APK Downloader

```python
import requests

def download_apk(package_name, output_dir):
    # Use apkpure or similar
    url = f"https://d.apkpure.com/b/APK/{package_name}"
    r = requests.get(url)
    with open(f"{output_dir}/{package_name}.apk", 'wb') as f:
        f.write(r.content)
```

### Manifest Parser

```python
import xml.etree.ElementTree as ET

def parse_manifest(manifest_path):
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    
    permissions = []
    for perm in root.findall('.//uses-permission'):
        permissions.append(perm.get('{http://schemas.android.com/apk/res/android}name'))
    
    return permissions
```

### Secret Scanner

```python
import os
import re

def scan_for_secrets(directory):
    secrets = []
    patterns = [
        r'api[_-]?key\s*=\s*["\']([^"\']+)["\']',
        r'secret\s*=\s*["\']([^"\']+)["\']',
        r'password\s*=\s*["\']([^"\']+)["\']',
        r'token\s*=\s*["\']([^"\']+)["\']',
    ]
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.smali', '.java', '.kt')):
                with open(os.path.join(root, file), 'r', errors='ignore') as f:
                    content = f.read()
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            secrets.append({'file': file, 'pattern': pattern, 'value': match})
    
    return secrets
```

---

## Output Format

```json
{
  "package": "com.target.app",
  "version": "1.0.0",
  "permissions": ["android.permission.INTERNET"],
  "activities": ["MainActivity", "LoginActivity"],
  "secrets": [
    {"type": "api_key", "value": "abc123", "file": "BuildConfig.java"}
  ],
  "ssl_pinning": false,
  "root_detection": true
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| APK not found | Wrong path | Check path |
| Decompile failed | Obfuscated | Use jadx for better output |
| Frida failed | Server not running | Start frida-server |
| SSL bypass failed | Wrong certificate | Install Burp CA |
| Root detected | Detection active | Use bypass script |
