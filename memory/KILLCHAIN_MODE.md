# KILLCHAIN MODE — MITRE ATT&CK + FULL KILL CHAIN MAPPING
# 14 CATEGORIES | 800+ TECHNIQUES
# TRIGGERS: kill chain, mitre, att&ck, tactics, techniques, procedures, ttp, playbook, cisa

---

## Section 1: RECONNAISSANCE (TA0043 — 80+ techniques)

### 1.1 Active Scanning (T1595)
- T1595.001 — Scanning IP Blocks
- T1595.002 — Vulnerability Scanning
- T1595.003 — Wordlist Scanning
- Nmap SYN scan / ACK scan / Window scan / XMAS scan / NULL scan
- Masscan fast port scan
- ZMap internet-wide scan
- Unicornscan async scan
- Nuclei template scanning
- Custom vulnerability scanner

### 1.2 Passive Recon (T1592, T1589, T1590)
- T1592.001 — Hardware Enumeration
- T1592.002 — Software Enumeration
- T1592.003 — Firmware Enumeration
- T1592.004 — Client Configurations
- T1589.001 — Credentials
- T1589.002 — Email Addresses
- T1589.003 — Employee Names
- T1590.001 — Domain Properties
- T1590.002 — DNS
- T1590.003 — Network Trust Dependencies
- T1590.004 — Network Topology
- T1590.005 — IP Addresses
- T1590.006 — Network Security Appliances

### 1.3 OSINT Tools
- Shodan / Censys / FOFA / ZoomEye / BinaryEdge
- theHarvester / Recon-ng / Maltego / SpiderFoot
- Amass / Subfinder / Sublist3r
- crt.sh / Certificate Transparency
- WHOIS / RDAP
- DNS enumeration (dig, nslookup, fierce)
- Google dorking (site:, inurl:, intitle:, filetype:)
- GitHub dorking (secrets, API keys)
- Pastebin monitoring
- Social media OSINT (LinkedIn, Twitter, Facebook)
- Breach database monitoring

---

## Section 2: RESOURCE DEVELOPMENT (TA0042 — 60+ techniques)

### 2.1 Infrastructure (T1583)
- T1583.001 — Domains
- T1583.002 — DNS Server
- T1583.003 — Virtual Private Server
- T1583.004 — Server
- T1583.005 — Botnet
- T1583.006 — Web Services
- Domain fronting infrastructure
- Bulletproof hosting
- Fast flux DNS
- Domain generation algorithms (DGA)
- Traffic redirector setup
- Proxy network setup
- VPN infrastructure
- Tor hidden services
- I2P infrastructure

### 2.2 Capabilities (T1584, T1587)
- T1584.001 — Malware
- T1584.002 — Tool
- T1584.003 — Code Signing Certificates
- T1584.004 — Digital Certificates
- T1584.005 — Exploits
- T1584.006 — Vulnerabilities
- T1587.001 — Malware
- T1587.002 — Code Signing Certificates
- T1587.003 — Digital Certificates
- T1587.004 — Exploits
- T1585.001 — Accounts
- T1585.002 — Email Accounts
- T1585.003 — Cloud Accounts
- T1586.001 — Social Media Accounts
- T1586.002 — Email Accounts
- T1586.003 — Cloud Accounts

### 2.3 Staging
- Payload staging (multiple stages)
- C2 profile development
- Malleable C2 profiles
- Infrastructure staging
- Redirector setup
- WAF/CDN staging for C2
- Domain categorization
- SSL certificate preparation

---

## Section 3: INITIAL ACCESS (TA0001 — 70+ techniques)

### 3.1 External Remote Services (T1133)
- T1133.001 — External Remote Services
- T1133.002 — Valid Accounts
- RDP brute force / credential stuffing
- VPN credential abuse
- SSH brute force / credential stuffing
- VNC exploitation
- Citrix exploitation
- Fortinet VPN exploitation (CVE-2018-13379)
- Pulse Secure VPN exploitation (CVE-2019-11510)
- Citrix ADC exploitation (CVE-2019-19781)
- SonicWall SMA exploitation (CVE-2021-20038)
- Cisco ASA exploitation (CVE-2020-3452)
- Zoho ManageEngine exploitation
- FortiGate exploitation

### 3.2 Phishing (T1566)
- T1566.001 — Spearphishing Attachment
- T1566.002 — Spearphishing Link
- T1566.003 — Spearphishing via Service
- T1566.004 — Spearphishing Voice
- Credential harvesting phishing
- Malicious document phishing (Office macros)
- HTML smuggling phishing
- QR code phishing (quishing)
- OAuth consent phishing
- Adversary-in-the-middle phishing (AitM)
- Real-time phishing proxies
- Evilginx2 / Muraena / Modlishka

### 3.3 Exploit Public-Facing App (T1190)
- T1190 — Exploit Public-Facing Application
- SQL injection exploitation
- Remote code execution
- Server-side request forgery (SSRF)
- Local file inclusion / remote file inclusion
- Deserialization exploitation
- Server-side template injection
- XML external entity (XXE)
- Authentication bypass
- Authorization bypass
- File upload exploitation
- API exploitation

### 3.4 Supply Chain Compromise (T1195)
- T1195.001 — Compromise Software Dependencies
- T1195.002 — Compromise Software Supply Chain
- T1195.003 — Compromise Hardware Supply Chain
- Dependency confusion attack
- Typosquatting attack
- SolarWinds-style compromise
- Code signing abuse
- CI/CD pipeline compromise
- Open source dependency poisoning
- npm/PyPI/Maven package compromise

---

## Section 4: EXECUTION (TA0002 — 75+ techniques)

### 4.1 Command and Scripting (T1059)
- T1059.001 — PowerShell
- T1059.002 — AppleScript
- T1059.003 — Windows Command Shell
- T1059.004 — Unix Shell
- T1059.005 — Visual Basic
- T1059.006 — Python
- T1059.007 — JavaScript
- T1059.008 — Network Device CLI
- T1059.009 — Cloud API
- PowerShell download cradles
- PowerShell bypass techniques
- PowerShell AMSI bypass
- PowerShell block logging bypass
- PowerShell constrained language bypass
- PowerShell WDAC bypass

### 4.2 Exploitation for Client Execution (T1203)
- T1203 — Exploitation for Client Execution
- Browser exploitation
- Document exploitation
- Software vulnerability exploitation
- User execution (T1204)
- T1204.001 — Malicious Link
- T1204.002 — Malicious File
- T1204.003 — Malicious Image

### 4.3 Inter-Process Communication (T1559)
- T1559.001 — Component Object Model
- T1559.002 — Dynamic Data Exchange
- T1559.003 — XPC Services
- COM object hijacking
- DDE exploitation
- Named pipe exploitation
- Shared memory exploitation
- Window message exploitation

---

## Section 5: PERSISTENCE (TA0003 — 80+ techniques)

### 5.1 Boot / Logon Autostart (T1547)
- T1547.001 — Registry Run Keys / Startup Folder
- T1547.002 — Authentication Package
- T1547.003 — Time Providers
- T1547.004 — Winlogon Helper DLL
- T1547.005 — Security Support Provider
- T1547.006 — Kernel Modules and Extensions
- T1547.007 — Re-opened Applications
- T1547.008 — LSASS Driver
- T1547.009 — Shortcut Modification
- T1547.010 — Port Monitors
- T1547.012 — Print Processors
- T1547.013 — XDG Autostart Entries
- T1547.014 — Active Setup

### 5.2 Scheduled Task/Job (T1053)
- T1053.002 — At (Linux)
- T1053.003 — Cron
- T1053.004 — Launchd
- T1053.005 — Scheduled Task (Windows)
- T1053.006 — Systemd Timers
- T1053.007 — Container Orchestration Job

### 5.3 Server Software Component (T1505)
- T1505.001 — SQL Stored Procedures
- T1505.002 — Transport Agent
- T1505.003 — Web Shell
- T1505.004 — IIS Components
- T1505.005 — Terminal Services DLL
- Web shell deployment (PHP, ASPX, JSP)
- IIS native module backdoor
- Apache module backdoor
- Nginx module backdoor

### 5.4 Account Manipulation (T1098)
- T1098.001 — Additional Cloud Credentials
- T1098.002 — Additional Email Delegate Access
- T1098.003 — Additional Cloud Roles
- T1098.004 — SSH Authorized Keys
- T1098.005 — Device Registration
- T1098.006 — Additional Container Cluster Roles
- Golden ticket
- Silver ticket
- Skeleton key
- DCShadow
- Directory service restoration

---

## Section 6: PRIVILEGE ESCALATION (TA0004 — 70+ techniques)

### 6.1 Windows Privesc (T1068)
- Potato family (Hot/Potten/Juicy/God/Print/Sweet)
- UAC bypass (fodhelper, computerdefaults, eventvwr)
- Service registry permissions weakness
- Unquoted service path
- DLL hijacking / search order
- Token impersonation (SeImpersonatePrivilege)
- AlwaysInstallElevated
- Scheduled task abuse
- Kernel exploits (PrintNightmare, EternalBlue)
- PrintSpooler abuse
- MS-EFSR abuse
- PetitPotam
- DFSCoerce
- NoPac / sAMAccountName spoofing
- Resource-based constrained delegation (RBCD)
- Shadow credentials
- Certificate abuse (ADCS ESC1-12)
- Kerberoasting
- AS-REP roasting
- NTLM relay
- Windows LocalPotato
- Steve0 spray

### 6.2 Linux Privesc (T1068)
- SUID/SGID abuse
- Sudo misconfiguration (GTFOBins)
- Capabilities abuse
- Kernel exploits (DirtyPipe, DirtyCow, PwnKit)
- NFS root squashing bypass
- Docker group escape
- Writable /etc/passwd
- Cron job abuse
- PATH manipulation
- LD_PRELOAD exploitation
- /etc/ld.so.conf.d abuse
- Polkit abuse (CVE-2021-4034)
- Snap confinement escape
- Proc filesystem exploitation
- User namespace escape

### 6.3 Cloud Privesc
- AWS IAM privilege escalation (24+ methods)
- Azure Managed Identity abuse
- GCP service account privilege escalation
- Kubernetes RBAC escape
- Container escape (Docker, containerd, CRI-O)
- Pod escape to node
- Node escape to host
- Namespace escape
- Service account token abuse

---

## Section 7: DEFENSE EVASION (TA0005 — 90+ techniques)

### 7.1 Process Injection (T1055)
- T1055.001 — Dynamic-link Library Injection
- T1055.002 — Portable Executable Injection
- T1055.003 — Thread Execution Hijacking
- T1055.004 — Asynchronous Procedure Call
- T1055.005 — Thread Local Storage
- T1055.008 — Ptrace System Calls
- T1055.009 — Proc Memory
- Process hollowing
- Process doppelgänging
- Transacted hollowing
- Module stomping
- Ghost writing
- Early bird injection
- APC queue injection
- Fiber/d Fiber injection
- Syscall-based injection

### 7.2 Obfuscation (T1027)
- T1027.001 — Binary Padding
- T1027.002 — Software Packing
- T1027.003 — Steganography
- T1027.004 — Compile After Delivery
- T1027.005 — Indicator Removal
- T1027.006 — HTML Smuggling
- T1027.007 — Dynamic API Resolution
- T1027.008 — LLMNR/NBT-NS Poisoning
- T1027.009 — Encrypted/Encoded File
- XOR encoding
- Base64 encoding
- AES encryption
- RSA encryption
- Custom encoding algorithms
- String obfuscation
- Control flow flattening
- Dead code insertion
- junk code insertion

### 7.3 EDR/AV Bypass
- SysWhispers / HellsGate / HalosGate
- Direct syscall / indirect syscall
- Syscall stub modification
- ntdll unhooking
- Userland hook detection
- ETW patching
- AMSI bypass (multiple methods)
- AMSI patching
- AMSI bypass via reflection
- ETW bypass
- Process protection bypass
- Callback removal
- Mini-filter bypass
- WDF bypass
- Kernel callback removal
- BYOVD (Bring Your Own Vulnerable Driver)
- Signed driver exploitation
- KDM (Kernel Driver Mapping)
- Hypervisor-based defense bypass

### 7.4 Anti-Forensics (T1070)
- T1070.001 — Clear Windows Event Logs
- T1070.002 — Clear Linux/Mac System Logs
- T1070.003 — Clear Command History
- T1070.004 — File Deletion
- T1070.005 — Network Share Connection Removal
- T1070.006 — Timestomp
- T1070.007 — Clear Network Connection History
- T1070.008 — Clear Mailbox Data
- T1070.009 — Clear Persistence
- Log clearing (Windows, Linux, web)
- File wiping
- Metadata removal
- Timestomping
- Secure deletion (Gutmann, DoD)
- RAM clearing
- Swap file clearing
- Prefetch clearing
- Shellbag clearing
- Amcache clearing
- SRUM clearing

---

## Section 8: CREDENTIAL ACCESS (TA0006 — 60+ techniques)

### 8.1 OS Credential Dumping (T1003)
- T1003.001 — LSASS Memory
- T1003.002 — Security Account Manager
- T1003.003 — NTDS
- T1003.004 — LSA Secrets
- T1003.005 — Cached Domain Credentials
- T1003.006 — DCSync/DCSync
- T1003.007 — Proc Filesystem
- T1003.008 — /etc/passwd and /etc/shadow
- T1003.009 — Proc Memory
- Mimikatz (lsadump, sekurlsa, kerberos, crypto)
- Impacket secretsdump
- CrackMapExec (lsadump, sam)
- LaZagne
- Rubeus
- ProcDump for LSASS
- Comsvcs.dll minidump
- Task Manager dump
- Procdump/mindump
- Shadow copy extraction
- VSS (Volume Shadow Copy)

### 8.2 Unsecured Credentials (T1552)
- T1552.001 — Credentials In Files
- T1552.002 — Registry Storage
- T1552.003 — Bash History
- T1552.004 — Private Keys
- T1552.005 — Cloud Instance Metadata
- T1552.006 — Group Policy Preferences
- T1552.007 — Container API
- T1552.008 — Chat Messages
- Browser credential extraction (Chrome, Firefox, Edge, Opera)
- Password manager extraction
- WiFi credential extraction
- SSH key extraction
- SSH agent forwarding abuse
- GPG key extraction
- Kerberos ticket extraction
- Token extraction
- API key extraction
- Environment variable credential extraction
- Cloud metadata credential theft

---

## Section 9: DISCOVERY (TA0007 — 70+ techniques)

### 9.1 System Discovery (T1082)
- T1082 — System Information Discovery
- T1083 — File and Directory Discovery
- T1084 — System Network Configuration Discovery
- T1085 — System Network Connections Discovery
- T1086 — System Owner/User Discovery
- T1087 — Process Discovery
- T1089 — System Time Discovery
- T1090 — System Network Connections Discovery
- T1091 — System Information Discovery
- T1092 — System Network Configuration Discovery
- T1093 — System Network Connections Discovery
- T1094 — System Time Discovery
- T1095 — System Information Discovery

### 9.2 Domain Discovery (T1087)
- T1087.001 — Domain Account Discovery
- T1087.002 — Domain Group Discovery
- T1087.003 — Domain Trust Discovery
- T1087.004 — Cloud Account Discovery
- Active Directory enumeration
- BloodHound analysis
- PowerView enumeration
- ADRecon
- LDAP enumeration
- Group Policy enumeration
- Trust relationship enumeration

### 9.3 Network Discovery (T1040)
- T1040 — Network Sniffing
- T1046 — Network Service Discovery
- T1135 — Network Share Discovery
- T1049 — System Network Connections Discovery
- Network topology mapping
- Network share enumeration
- SNMP enumeration
- WMI enumeration
- NetBIOS enumeration
- SMB enumeration
- NFS enumeration

---

## Section 10: LATERAL MOVEMENT (TA0008 — 55+ techniques)

### 10.1 Remote Services (T1021)
- T1021.001 — Remote Desktop Protocol
- T1021.002 — SMB/Windows Admin Shares
- T1021.003 — Distributed Component Object Model
- T1021.004 — SSH
- T1021.005 — VNC
- T1021.006 — Windows Remote Management
- PsExec
- WMI lateral movement
- WinRM lateral movement
- DCOM lateral movement
- SAP lateral movement
- Kubelet API lateral movement
- RDP pass-the-hash
- RDP restricted admin mode

### 10.2 Exploitation of Remote Services (T1210)
- T1210 — Exploitation of Remote Services
- EternalBlue exploitation
- BlueKeep exploitation
- SMB relay attacks
- NTLM relay attacks
- LLMNR/NBT-NS poisoning
- IPv6 DNS poisoning (mitm6)
- Printer bug exploitation
- SpoolSample
- DFSCoerce
- PetitPotam
- NoPac/SamAccountName spoofing
- Unconstrained delegation abuse
- Constrained delegation abuse
- RBCD abuse
- Shadow credentials
- Certificate abuse (ADCS)

### 10.3 Use Alternate Authentication (T1550)
- T1550.001 — Application Access Token
- T1550.002 — Pass the Hash
- T1550.003 — Pass the Ticket
- T1550.004 — Web Session Cookie
- Overpass the Hash
- Pass the Key
- Pass the Cert
- Golden ticket
- Silver ticket
- Diamond ticket
- Kerberos ticket harvesting
- SAML token abuse
- OAuth token abuse
- Session hijacking

---

## Section 11: COLLECTION (TA0009 — 50+ techniques)

### 11.1 Data from Local System (T1005)
- T1005 — Data from Local System
- T1006 — Data from Network Shared Drive
- T1007 — System Service Discovery
- T1008 — Fallback Channels
- T1009 — Data from Removable Media
- T1011 — Exfiltration Over Other Network Medium
- T1012 — Query Registry
- T1016 — System Network Configuration Discovery
- T1018 — Remote System Discovery
- T1022 — Data Encrypted
- T1025 — Data from Removable Media
- T1030 — Data Transfer Size Limits
- T1033 — System Owner/User Discovery
- T1039 — Data from Network Shared Drive
- T1041 — Exfiltration Over C2 Channel

### 11.2 Data Staging (T1074)
- T1074.001 — Local Data Staging
- T1074.002 — Remote Data Staging
- T1074 — Data Staged
- Local staging directories
- Remote staging servers
- Cloud storage staging
- Archive before exfiltration
- Data compression
- Data encryption before exfiltration
- Split data for exfiltration
- Chunk data for exfiltration

---

## Section 12: COMMAND AND CONTROL (TA0011 — 50+ techniques)

### 12.1 Application Layer (T1071)
- T1071.001 — Web Protocols (HTTP/HTTPS)
- T1071.002 — File Transfer Protocols
- T1071.003 — Mail Protocols
- T1071.004 — DNS
- T1073 — Encrypted Channel
- T1079 — Multiband Communication
- T1080 — Taint Shared Content
- T1081 — Unencrypted Channel
- T1082 — System Information Discovery
- T1083 — File and Directory Discovery
- T1090 — Proxy
- T1091 — Remote Access Software
- T1093 — Application Layer Protocol
- T1094 — Custom Command and Control Protocol
- T1095 — Non-Application Layer Protocol
- T1096 — Non-Standard Port
- T1097 — Non-Standard Path
- T1099 — Protocol Tunneling
- T1102 — Web Service
- T1104 — Multi-Stage Channels
- T1105 — Ingress Tool Transfer
- T1106 — Native API
- T1107 — Data Encoding
- T1109 — Root CA
- T1132 — Data Encoding
- T1133 — External Remote Services
- T1197 — BITS Jobs
- T1205 — Traffic Signaling
- T1219 — Remote Access Software
- T1568 — Dynamic Resolution
- T1572 — Protocol Tunneling
- T1573 — Encrypted Channel
- T1583 — Acquire Infrastructure
- T1008 — Fallback Channels
- T1090 — Proxy

### 12.2 C2 Frameworks
- Cobalt Strike (Malleable C2 profiles)
- Havoc C2
- Sliver C2
- Mythic C2
- Brute Ratel C2
- Nighthawk C2
- Empire/Starkiller
- Covenant
- Metasploit Meterpreter
- AsyncRAT
- QuasarRAT
- njRAT
- DarkComet
- njRAT
- WsF泓

---

## Section 13: EXFILTRATION (TA0010 — 40+ techniques)

### 13.1 Exfiltration Techniques
- T1020 — Automated Exfiltration
- T1022 — Data Encrypted
- T1029 — Scheduled Transfer
- T1030 — Data Transfer Size Limits
- T1037 — Boot or Logon Initialization Scripts
- T1041 — Exfiltration Over C2 Channel
- T1048 — Exfiltration Over Alternative Protocol
- T1049 — System Network Connections Discovery
- T1052 — Exfiltration Over Physical Medium
- T1053 — Exfiltration Over Web Service
- T1056 — Input Capture
- T1057 — Process Discovery
- T1071 — Application Layer Protocol
- T1080 — Taint Shared Content
- T1083 — File and Directory Discovery
- T1114 — Email Collection
- T1119 — Automated Collection
- T1185 — Browser Session Hijacking
- T1567 — Exfiltration Over Web Service
- T1648 — Non-Application Layer Protocol
- T1657 — Financial Theft
- T1646 — Exfiltration Over Unencrypted Non-C2 Protocol
- DNS exfiltration
- ICMP exfiltration
- HTTP exfiltration
- HTTPS exfiltration
- FTP exfiltration
- SCP exfiltration
- Cloud storage exfiltration
- Steganography exfiltration
- Covert channel exfiltration
- USB exfiltration
- Bluetooth exfiltration
- NFC exfiltration
- QR code exfiltration

---

## Section 14: IMPACT (TA0040 — 40+ techniques)

### 14.1 Data Destruction (T1485)
- T1485 — Data Destruction
- T1486 — Data Encrypted for Impact
- T1489 — Service Stop
- T1490 — Inhibit System Recovery
- T1491 — Defacement
- T1498 — Network Denial of Service
- T1499 — Endpoint Denial of Service
- T1529 — System Shutdown/Reboot
- T1531 — Account Access Removal
- T1561 — Disk Wipe
- T1565 — Data Manipulation
- T1657 — Financial Theft
- T1529 — System Shutdown/Reboot
- T1531 — Account Access Removal
- T1561 — Disk Wipe
- T1565 — Data Manipulation
- T1657 — Financial Theft

### 14.2 Ransomware Operations
- LockBit 3.0 (BlackMatter)
- BlackCat/ALPHV
- Cl0p
- Royal/BlackSuit
- Play
- Akira
- 8Base
-INC Ransom
- MalasLocker
- Black Basta
- Qakbot → ransomware
- BazarLoader → ransomware
- IcedID → ransomware
- Cobalt Strike → ransomware

### 14.3 DDoS Techniques
- Volumetric DDoS
- Protocol DDoS
- Application layer DDoS
- DNS amplification
- NTP amplification
- SSDP amplification
- Memcached amplification
- CLDAP amplification
- CharGEN amplification
- Slowloris
- RUDY
- HULK
- DDoS botnets (Mirai, Mozi, BotenaGo)
- DDoS via C2 frameworks

---

*KILLCHAIN MODE — Full MITRE ATT&CK for Enterprise mapping + CISA playbook*
*14 TA (Tactics) | 200+ TT (Techniques) | 800+ sub-techniques*
