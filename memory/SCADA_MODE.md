# SCADA/ICS MODE — INDUSTRIAL CONTROL SYSTEM ATTACKS
# 12 CATEGORIES | 400+ TECHNIQUES
# TRIGGERS: scada, ics, ot, plcs, hmi, modbus, dnp3, opc, scada exploit, ot security

---

## Section 1: OT NETWORK DISCOVERY (40+ techniques)

### 1.1 Network Enumeration
- Nmap OT scanning (`-sU -p 502,20000,48000,102,47808,47809`)
- Shodan ICS search (`port:502 country:XX`)
- Censys ICS discovery (`services.banner:Modbus`)
- FOFA OT fingerprint (`app="Modbus"`)
- ZoomEye ICS (`port:502 app:"modbus"`)
- BinaryEdge ICS (`port:502 OR port:102 OR port:47808`)
- Google dorking (`inurl:/cgi-bin/ intitle:"HMI"`)
- Coda iodine DNS tunneling for OT networks
- Passive OT fingerprinting via network tap

### 1.2 Protocol Fingerprinting
- Modbus TCP/RTU fingerprinting (unit ID enumeration)
- DNP3 protocol identification (function codes)
- OPC UA/DA discovery (endpoint enumeration)
- BACnet building automation discovery
- EtherNet/IP CIP scanning
- PROFINET DCCP discovery
- IEC 61850 GOOSE sniffing
- IEC 104 telecontrol discovery
- MQTT SCADA broker discovery
- AMQP industrial message broker discovery

### 1.3 Asset Identification
- PLC brand/model identification (Siemens S7, Allen-Bradley, Schneider, ABB, Mitsubishi, Omron, Delta, Fuji)
- HMI software identification (WinCC, FactoryTalk, Ignition, Indusoft, Schneider Vijeo)
- SCADA server identification (OSIsoft PI, Wonderware, GE iFIX, AVEVA)
- RTU (Remote Terminal Unit) identification
- historian server discovery
- engineering workstation discovery
- backup server identification
- DMZ architecture mapping

---

## Section 2: MODBUS ATTACKS (45+ techniques)

### 2.1 Modbus TCP Attacks
- Function code 01-08 enumeration (read coils/discrete/holding input)
- Function code 05/15 force single/multiple coils
- Function code 06/16 force single/multiple registers
- Function code 08 diagnostics loopback
- Function code 11/12 get comm event counter/status
- Function code 17 report server ID
- Function code 43 read device identification
- Unit ID brute force (1-247)
- Modbus TCP man-in-the-middle
- Modbus TCP packet injection
- Modbus response spoofing
- Modbus fuzzing (pymodbus/fault injection)

### 2.2 Modbus RTU Attacks
- Serial line sniffing (RS-232/RS-485)
- RTU frame manipulation
- CRC bypass (known CRC calculation)
- RTU-to-TCP gateway exploitation
- Serial-to-Ethernet converter attacks
- Modbus RTU brute force
- RTU replay attacks

### 2.3 Modbus Advanced
- Modbus-to-DNP3 protocol conversion attacks
- Modbus gateway bypass
- Modbus over SSH tunnel exploitation
- Modbus over VPN leakage
- Modbus firewall rules bypass
- Modbus authentication bypass (most devices have NO auth)
- Siemens S7comm+ exploitation
- Schneider Modicon memory dump
- ABB AC500 Modbus exploitation

---

## Section 3: DNP3 ATTACKS (35+ techniques)

### 3.1 DNP3 Enumeration
- Function code 01-18 scan (read/write/operate)
- Object group enumeration (all groups)
- Class data retrieval (Class 0-3)
- Index range scanning
- Device attribute retrieval (object group 0)
- Time sync requests
- Cold/warm restart commands
- Enable/disable unsolicited responses

### 3.2 DNP3 Exploitation
- DNP3 protocol fuzzing (dnp3-fuzz, custom scripts)
- DNP3 man-in-the-middle (dnp3-proxy)
- DNP3 authentication bypass
- DNP3 secure authentication downgrade
- DNP3 serial line interception
- DNP3 gateway exploitation
- DNP3 data link layer manipulation
- DNP3 transport layer attacks
- DNP3 application layer injection

### 3.3 DNP3 Advanced
- DNP3-to-ICCP protocol conversion attacks
- DNP3 over serial (RS-232/RS-485) sniffing
- DNP3 master/RTU impersonation
- DNP3 event polling manipulation
- DNP3 unsolicited response injection
- DNP3 secure authentication bypass (HMAC manipulation)
- DNP3 certificate-based auth bypass
- ABB DNP3 exploitation
- GE DNP3 exploitation
- Schweitzer SEL DNP3 exploitation

---

## Section 4: OPC ATTACKS (30+ techniques)

### 4.1 OPC DA (Classic) Attacks
- COM/DCOM enumeration (OPC server discovery)
- OPC DA callback manipulation
- OPC tag enumeration (full namespace dump)
- OPC DA read/write injection
- OPC DA subscription hijacking
- OPC DA authentication bypass (Windows auth only)
- OPC DA remote code execution (COM object abuse)
- DCOM port negotiation manipulation
- OPC DA server impersonation

### 4.2 OPC UA Attacks
- OPC UA endpoint discovery
- OPC UA certificate theft
- OPC UA private key extraction
- OPC UA user authentication bypass
- OPC UA anonymous login exploitation
- OPC UA security mode downgrade (None/Sign/SignAndEncrypt)
- OPC UA policy downgrade
- OPC UA application certificate spoofing
- OPC UA session hijacking
- OPC UA subscription manipulation
- OPC UA method call injection
- OPC UA history read exploitation
- Kepware OPC UA exploitation
- Matrikon OPC UA exploitation
- Unified Automation OPC UA exploitation

### 4.3 OPC UA Advanced
- OPC UA cert store manipulation
- OPC UA trust list poisoning
- OPC UA security policy bypass
- OPC UA chunked message attacks
- OPC UA binary protocol fuzzing
- OPC UA discovery server (LDS) manipulation
- OPC UA global discovery server (GDS) abuse

---

## Section 5: PLC/HMI EXPLOITS (50+ techniques)

### 5.1 Siemens S7
- S7-1200/1500 program upload/download (without password)
- S7-300/400 MPI/DP exploitation
- TIA Portal project extraction
- Siemens LOGO! exploitation
- SIMATIC HMI panel attacks
- Siemens WinCC database exploitation
- S7comm+ protocol fuzzing
- Siemens firewall bypass
- Siemens CPU memory dump
- Siemens web server exploitation (port 80/443)
- Siemens SINEC NTP exploitation

### 5.2 Allen-Bradley/Rockwell
- CompactLogix program extraction
- ControlLogix backdoor exploitation
- EtherNet/IP CIP exploitation
- Rockwell FactoryTalk View SE attacks
- RSLogix project extraction
- Allen-Bradley boot password reset
- Rockwell Remote Endpoint attacks
- Studio 5000 project theft
- Allen-Bradley L7x/L8x exploitation
- Rockwell Stratix switch exploitation

### 5.3 Schneider Electric
- Modicon M340/M580 program extraction
- EcoStruxure Control Expert attacks
- Unity Pro project extraction
- Schneider HMI panel exploitation
- Modicon memory card extraction
- Schneider serial RTU exploitation
- Schneider Pelco camera system attacks
- Schneider STRUXON firewall bypass

### 5.4 Other PLCs
- Mitsubishi FX/Q/L series exploitation
- Omron NJ/NX/CJ series exploitation
- Delta DVP series exploitation
- Fuji FR series exploitation
- Wago 750 series exploitation
- Beckhoff TwinCAT exploitation
- CODESYS runtime exploitation (vulnerable in 400+ PLC brands)
- B&R Automation exploitation
- Keyence PLC exploitation
- IDEC PLC exploitation
- LS Electric PLC exploitation
- ABB AC500/AC500eCo exploitation
- GE RX3i/RX7i exploitation
- Yokogawa PLC exploitation

### 5.5 HMI Exploitation
- WinCC Flexible/Comfort panel attacks
- FactoryTalk View ME/SE exploitation
- Indusoft Web Studio exploitation
- Schneider Magelis HMI attacks
- Siemens Comfort/Basic panel exploitation
- Weintek HMI exploitation
- Pro-face HMI exploitation
- MCGS HMI exploitation
- Delta DOP HMI exploitation
-威纶 (Weinview) HMI exploitation
- HMI credential extraction (SQLite/flat files)
- HMI recipe/database manipulation
- HMI historian log manipulation

---

## Section 6: OT NETWORK ATTACKS (45+ techniques)

### 6.1 OT Man-in-the-Middle
- ARP spoofing in OT networks
- VLAN hopping for OT segmentation bypass
- Span port mirroring for OT traffic capture
- HSRP/VRRP manipulation for OT gateway hijacking
- OT-specific MTM (Modbus/DNP3/OPC injection)
- Industrial protocol relay attacks
- Modbus TCP stream injection
- DNP3 frame manipulation in transit
- OPC UA certificate substitution MTM

### 6.2 OT Lateral Movement
- Flat network exploitation (OT often has NO segmentation)
- HMI-to-PLC pivot
- Historian-to-PLC pivot
- Engineering workstation exploitation
- SCADA server compromise → PLC control
- DMZ bypass techniques
- IT-to-OT lateral movement
- OT-to-IT pivot (for data exfiltration)

### 6.3 OT Denial of Service
- Modbus TCP SYN flood on port 502
- DNP3 connection exhaustion
- OPC UA session flood
- HMI web server DoS
- PLC CPU overload (write maximum register values)
- SCADA server database exhaustion
- OT network broadcast storm
- Industrial protocol fuzzing DoS

---

## Section 7: WIRELESS OT ATTACKS (30+ techniques)

### 7.1 Industrial Wireless
- WirelessHACK sniffing
- ISA100.11a protocol analysis
- WIA-PA protocol exploitation
- ZigBee industrial network attacks
- Wireless HART key extraction
- 6LoWPAN industrial network exploitation
- LoRaWAN industrial gateway attacks
- NB-IoT industrial sensor exploitation
- LTE-M industrial communication attacks

### 7.2 RF Attacks
- 900 MHz industrial frequency sniffing
- 2.4 GHz industrial WiFi attacks
- 433 MHz SCADA remote control replay
- 315 MHz industrial remote attacks
- Software Defined Radio (SDR) for OT protocol analysis
- RF jamming for industrial disruption
- RF protocol reverse engineering
- ISM band interference attacks

### 7.3 Bluetooth/BLE Industrial
- BLE industrial sensor spoofing
- Bluetooth industrial device enumeration
- BLE man-in-the-middle
- Industrial Bluetooth pairing attacks
- BLE protocol fuzzing
- Industrial wearable device attacks

---

## Section 8: HISTORIAN/ENGINEERING ATTACKS (35+ techniques)

### 8.1 Historian Attacks
- OSIsoft PI historian exploitation
- Wonderware Historian attacks
- GE Proficy Historian exploitation
- AVEVA Historian attacks
- Historian database manipulation (SQL injection)
- Historian credential extraction
- Historian API exploitation
- Historian backup manipulation
- Historian log tampering

### 8.2 Engineering Workstation Attacks
- TIA Portal project theft
- RSLogix/Studio 5000 extraction
- EcoStruxure project theft
- CODESYS development environment exploitation
- GX Works project extraction
- Sysmac Studio project theft
- TwinCAT project theft
- Engineering workstation lateral movement

### 8.3 SCADA Server Attacks
- SCADA database SQL injection
- SCADA web interface exploitation
- SCADA credential extraction
- SCADA service manipulation
- SCADA historian connection hijacking
- SCADA OPC server exploitation
- SCADA alarm manipulation
- SCADA audit log tampering

---

## Section 9: ICS MALWARE (30+ techniques)

### 9.1 Known ICS Malware
- Stuxnet (PLC logic bomb)
- TRITON/TRISIS (TRICONEX safety controller)
- Industroyer/CrashOverride (Ukraine grid)
- Industroyer2 (2022 Ukraine attack)
- XENOTIME (TRITON operator)
- CaddyWiper (Ukraine)
- HermeticWiper (Ukraine)
- IsaacWiper (Ukraine)
- WhisperGate (Ukraine)
- AcidRain (Viasat)
- VPNFilter (OT network)
- SCADAPass (PLC backdoor)
- Lloyd's Register/NERC analysis
- Diamond Sleet (OT targeting)

### 9.2 ICS Malware Development
- PLC logic injection code
- HMI backdoor implant
- SCADA server RAT
- Modbus DDoS malware
- DNP3 protocol exploitation malware
- OPC UA exploitation framework
- ICS-specific C2 channels (Modbus/DNP3 covert)
- OT-aware evasion techniques
- Industrial protocol covert channels

### 9.3 ICS Malware Analysis
- PLC logic analysis (Siemens S7, Allen-Bradley)
- HMI binary analysis
- SCADA malware reverse engineering
- Industrial protocol PCAP analysis
- ICS malware sandbox escape
- ICS-specific YARA rules
- ICS malware IOCs (MITRE ATT&CK for ICS)

---

## Section 10: OT SECURITY BYPASS (40+ techniques)

### 10.1 OT Firewall Bypass
- Industrial protocol encapsulation
- OT firewall rule enumeration
- Protocol-specific bypass (Modbus/DNP3/OPC)
- OT firewall NAT traversal
- OT firewall rule manipulation
- Industrial DMZ bypass
- OT firewall VLAN hopping
- OT firewall application layer bypass

### 10.2 OT Authentication Bypass
- Default credential exploitation (ALL major PLCs)
- No authentication exploitation (most OT devices)
- Engineering software authentication bypass
- HMI authentication bypass
- SCADA server credential dump
- OPC UA authentication bypass
- Modbus RTU authentication bypass (CRC only)
- DNP3 authentication bypass

### 10.3 OT Encryption Bypass
- Modbus TCP plaintext exploitation
- DNP3 plaintext exploitation
- OPC UA security mode downgrade
- Industrial protocol SSL/TLS stripping
- OT VPN bypass techniques
- Industrial certificate spoofing
- OT key management exploitation

---

## Section 11: OT FORENSICS (25+ techniques)

### 11.1 OT Evidence Collection
- PLC logic dump for evidence
- HMI screenshot capture
- SCADA server memory dump
- OT network PCAP collection
- Industrial protocol log extraction
- Engineering workstation forensic image
- Historian database export
- OT historian log correlation

### 11.2 OT Incident Response
- OT network isolation procedures
- PLC logic restoration from backup
- HMI factory reset procedures
- SCADA server recovery
- OT network segmentation enforcement
- Industrial protocol monitoring
- OT-specific threat hunting
- OT IoC extraction from PLCs

### 11.3 OT Attribution
- PLC logic analysis for APT attribution
- Industrial protocol fingerprinting
- OT malware family identification
- Threat actor TTP mapping (MITRE ATT&CK for ICS)
- ICS-specific threat intelligence
- PLC manipulation timestamp analysis
- OT network traffic pattern analysis

---

## Section 12: OT MITIGATION (30+ techniques)

### 12.1 OT Hardening
- PLC access control implementation
- HMI password hardening
- SCADA server hardening
- OT network segmentation (Purdue model)
- Industrial DMZ design
- OT firewall rule optimization
- Industrial protocol encryption (TLS for Modbus)
- OPC UA security best practices
- OT backup strategy
- OT patch management

### 12.2 OT Monitoring
- Industrial network intrusion detection (OT-NIDS)
- PLC logic change detection
- SCADA anomaly detection
- Industrial protocol deep packet inspection
- OT-specific SIEM integration
- Industrial honeypot deployment
- OT network baseline establishment
- Industrial threat hunting

### 12.3 OT Compliance
- NIST SP 800-82 (ICS security)
- IEC 62443 (industrial automation security)
- NERC CIP (critical infrastructure)
- NIST Cybersecurity Framework for ICS
- CISA ICS defense recommendations
- TLP (Traffic Light Protocol) for ICS sharing
- E-ISAC (Electricity ISAC) membership
- S4 (S4 Conference) research

---

*SCADA MODE — For targets with industrial control systems*
*Supports: Siemens, Allen-Bradley, Schneider, ABB, Mitsubishi, Omron, CODESYS, + 400 other brands*
