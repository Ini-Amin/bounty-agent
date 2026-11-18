# ZEROCLICK MODE — ZERO-CLICK EXPLOITS & NO-INTERACTION ATTACKS
# 8 CATEGORIES | 300+ TECHNIQUES
# TRIGGERS: zeroclick, zero click, no interaction, n-day, ota, imessage, whatsapp, passive exploit

---

## Section 1: MOBILE ZERO-CLICK EXPLOITS (50+ techniques)

### 1.1 iOS Zero-Click
- iMessage zero-click (FORCEDENTRY — CVE-2021-30860, CVE-2021-30858)
- iMessage zero-click (BLASTPASS — CVE-2023-41064)
- iMessage zero-click (2024 variants — PDF via PassKit)
- iMessage zero-click (2025 — Swift parser exploits)
- FaceTime zero-click (audio/video parser bugs)
- AirDrop zero-click (object deserialization)
- Siri zero-click (voice command injection)
- HomeKit zero-click (accessory protocol abuse)
- SharePlay zero-click (media parsing)
- iMessage App Store zero-click (app bundle exploitation)
- iMessage link preview zero-click (NSItemProvider abuse)
- iMessage reaction zero-click (tapback manipulation)
- iMessage edit history zero-click (metadata abuse)
- iMessage pinned conversation zero-click
- iMessage shared-with-you zero-click

### 1.2 Android Zero-Click
- MMS zero-click (Stagefright — CVE-2015-1538/1541/1542)
- MMS zero-click (2023-2024 — MediaCodec parser)
- Google Messages zero-click (RCS parser bugs)
- Samsung Messages zero-click (ImageIO parsing)
- WhatsApp zero-click (2022 — video codec)
- Telegram zero-click (media processing)
- Signal zero-click (media handling)
- Google Duo zero-click (video call parsing)
- Nearby Share zero-click (object deserialization)
- Android System WebView zero-click
- Google Play Services zero-click
- Samsung Knox zero-click
- Huawei EMUI zero-click
- Xiaomi MIUI zero-click (system app parsing)
- Oppo ColorOS zero-click
- Vivo FuntouchOS zero-click
- OnePlus OxygenOS zero-click

### 1.3 Cross-Platform Zero-Click
- WhatsApp Business zero-click
- WeChat zero-click (media processing)
- Line zero-click (sticker/video parsing)
- Viber zero-click (media handling)
- Discord zero-click (embed parsing)
- Telegram Voice Chat zero-click
- Slack zero-click (file sharing)
- Microsoft Teams zero-click (meeting join)
- Zoom zero-click (meeting link)
- Google Meet zero-click
- WebRTC zero-click (ICE candidate)

---

## Section 2: DESKTOP ZERO-CLICK (40+ techniques)

### 2.1 Browser Zero-Click
- Chrome zero-click (V8 engine, renderer)
- Firefox zero-click (SpiderMonkey)
- Safari zero-click (JavaScriptCore)
- Edge zero-click (Chromium-based)
- Opera zero-click (Chromium-based)
- Brave zero-click (Chromium-based)
- WebKit zero-click (XMLHttpRequest/Fetch)
- PDF.js zero-click (PDF parsing)
- WebAssembly zero-click (WASM module)
- Service Worker zero-click
- SharedArrayBuffer zero-click (Spectre variant)

### 2.2 OS Zero-Click
- Windows zero-click (RPC/DCOM)
- macOS zero-click (XPC/NSXPC)
- Linux zero-click (D-Bus/IPC)
- Windows zero-click (Print Spooler — PrintNightmare)
- macOS zero-click (XPC via launchd)
- Windows zero-click (WMI event subscription)
- macOS zero-click (System Preferences parsing)
- Windows zero-click (Task Scheduler)
- macOS zero-click (Installer.app parsing)
- Windows zero-click (SMBv3 compression)

### 2.3 Application Zero-Click
- Microsoft Office zero-click (OLE/RTF)
- Adobe Reader zero-click (PDF parsing)
- Slack desktop zero-click (desktop app)
- Discord desktop zero-click (Electron)
- VS Code zero-click (extension handling)
- Zoom desktop zero-click (meeting join)
- Telegram desktop zero-click (media parsing)
- Signal desktop zero-click (media handling)
- 7-Zip zero-click (archive parsing)
- WinRAR zero-click (archive parsing — CVE-2023-38831)

---

## Section 3: NETWORK ZERO-CLICK (35+ techniques)

### 3.1 WiFi Zero-Click
- WiFi zero-click (KRACK — CVE-2017-13077/13078/13087/13088)
- WiFi zero-click (FragAttacks — CVE-2020-24587/24588)
- WiFi zero-click (Dragonblood — WPA3)
- WiFi zero-click (Beacon frame parsing)
- WiFi zero-click (Probe response abuse)
- WiFi zero-click (Deauthentication flood)
- WiFi zero-click (EAPOL handshake capture)
- WiFi zero-click (PMKID capture)
- WiFi zero-click (802.11w bypass)

### 3.2 Bluetooth Zero-Click
- Bluetooth zero-click (BlueBorne — CVE-2017-1000250/1000251)
- Bluetooth zero-click (BrakTooth — CVE-2021-28139)
- Bluetooth zero-click (BLURtooth — CVE-2020-15802)
- Bluetooth zero-click (SweynTooth — 12 CVEs)
- Bluetooth zero-click (BLUFFS — cache/role key attacks)
- Bluetooth zero-click (KNOB — key negotiation)
- Bluetooth zero-click (BIAS — authentication bypass)
- Bluetooth zero-click (Apple iBeacon abuse)
- Bluetooth zero-click (Google Nearby abuse)

### 3.3 Network Protocol Zero-Click
- mDNS zero-click (multicast DNS poisoning)
- LLMNR zero-click (Link-Local Multicast Name Resolution)
- NBT-NS zero-click (NetBIOS Name Service)
- DHCP zero-click (DHCP option injection)
- ARP zero-click (ARP cache poisoning)
- ICMP zero-click (ICMP redirect)
- DNS zero-click (DNS rebinding)
- UPnP zero-click (SSDP discovery abuse)
- WS-Discovery zero-click (service location)

---

## Section 4: IoT ZERO-CLICK (35+ techniques)

### 4.1 Smart Home Zero-Click
- Alexa zero-click (voice command injection from TV)
- Google Home zero-click (ultrasonic command)
- Apple HomePod zero-click (Siri shortcut abuse)
- Smart TV zero-click (HDMI-CEC command injection)
- Smart TV zero-click (DLNA/UPnP exploitation)
- Smart speaker zero-click (audio parsing)
- Smart doorbell zero-click (RTSP stream exploitation)
- Smart lock zero-click (Z-Wave/Zigbee replay)
- Smart thermostat zero-click (MQTT injection)
- Smart light zero-click (Hub protocol abuse)
- Smart plug zero-click (energy monitoring abuse)

### 4.2 Industrial IoT Zero-Click
- SCADA HMI zero-click (web interface)
- PLC zero-click (Modbus TCP exploitation)
- Building automation zero-click (BACnet)
- HVAC zero-click (protocol exploitation)
- Smart grid zero-click (IEC 61850)
- Smart meter zero-click (DLMS/COSEM)
- Sensor network zero-click (6LoWPAN)
- Gateway zero-click (MQTT injection)
- Edge device zero-click (container escape)

### 4.3 Medical IoT Zero-Click
- Pacemaker zero-click (RF exploitation)
- Insulin pump zero-click (wireless protocol)
- Infusion pump zero-click (network exploitation)
- Patient monitor zero-click (network attacks)
- Medical imaging zero-click (DICOM parsing)
- Hospital network zero-click (flat network)
- Wearable health zero-click (BLE exploitation)

---

## Section 5: OTA (OVER-THE-AIR) ATTACKS (30+ techniques)

### 5.1 Mobile OTA
- iOS OTA update interception (mitmproxy)
- Android OTA update interception
- Samsung OTA update exploitation
- OTA update signature bypass
- OTA rollback attack (version downgrade)
- OTA update server compromise
- OTA delta update manipulation
- OTA staging partition exploitation
- iOS Recovery mode OTA abuse
- Android Fastboot OTA abuse

### 5.2 Firmware OTA
- Router firmware OTA interception
- IoT firmware OTA manipulation
- Smart TV firmware OTA exploitation
- Automotive firmware OTA attacks
- Router update MITM exploitation
- Modem firmware OTA abuse
- Baseband firmware OTA attacks

### 5.3 Infrastructure OTA
- CDN-based OTA manipulation
- Cloud-based OTA exploitation
- OTA certificate pinning bypass
- OTA signature verification bypass
- OTA integrity check bypass
- OTA version comparison abuse
- OTA rollback protection bypass

---

## Section 6: PASSIVE EXPLOITATION (25+ techniques)

### 6.1 Passive Reconnaissance
- OSINT automation (zero interaction with target)
- Passive DNS collection
- Certificate transparency monitoring
- Shodan/Censys passive scanning
- Social media passive profiling
- Code repository passive analysis
- Paste site monitoring
- Breach database monitoring
- Dark web monitoring
- WHOIS/RDAP passive analysis
- BGP passive monitoring
- Traffic pattern passive analysis

### 6.2 Passive Collection
- Network traffic passive collection (span port/tap)
- DNS passive collection (resolver logs)
- Email passive collection (MX records)
- Certificate passive collection (CT logs)
- WiFi passive collection (monitor mode)
- Bluetooth passive collection (BLE scanning)
- RFID passive collection (NFC reader)
- RF passive collection (SDR monitoring)

### 6.3 Passive Credential Harvesting
- Credential passive collection (breach databases)
- Password hash passive collection (leaked dumps)
- API key passive collection (GitHub dorking)
- Token passive collection (paste sites)
- Cookie passive collection (XSS staging)
- Session passive collection (network sniffing)
- SSH key passive collection (known_hosts)
- Certificate passive collection (private key leaks)

---

## Section 7: ZERO-DAY EXPLOITATION (30+ techniques)

### 7.1 Zero-Day Discovery
- Fuzzing protocols for zero-days (AFL++, LibFuzzer)
- Binary analysis for zero-days (Ghidra, IDA)
- Source code audit for zero-days
- Web application fuzzing for zero-days
- API fuzzing for zero-days
- Mobile app analysis for zero-days
- Browser engine fuzzing for zero-days
- OS kernel fuzzing for zero-days
- Hypervisor fuzzing for zero-days
- Compiler-based fuzzing (SanitizerCoverage)

### 7.2 Zero-Day Development
- Exploit development from zero-day
- Shellcode development for zero-day
- ROP chain construction for zero-day
- Heap spray for zero-day
- Use-after-free exploitation
- Buffer overflow exploitation
- Integer overflow exploitation
- Type confusion exploitation
- Out-of-bounds read/write exploitation
- Race condition exploitation

### 7.3 Zero-Day Delivery
- Zero-day via phishing (spear-phishing)
- Zero-day via watering hole
- Zero-day via supply chain
- Zero-day via physical access
- Zero-day via network proximity
- Zero-day via mobile proximity
- Zero-day via Bluetooth proximity
- Zero-day via NFC proximity
- Zero-day via WiFi proximity
- Zero-day via QR code

---

## Section 8: ZERO-CLICK DEFENSES & EVASION (25+ techniques)

### 8.1 Zero-Click Evasion
- Anti-sandbox detection (environment checks)
- Anti-VM detection (timing-based)
- Anti-analysis detection (debugger checks)
- Anti-emulation detection (behavioral)
- Anti-integrity detection (patch checks)
- Anti-memory detection (ASLR/DEP)
- Anti-heuristic detection (code obfuscation)
- Anti-network detection (air gap)
- Anti-physical detection (tamper detection)

### 8.2 Zero-Click Persistence
- Boot-level persistence (bootkit)
- Kernel-level persistence (rootkit)
- User-level persistence (registry/run keys)
- Service-level persistence (system service)
- Scheduled task persistence
- DLL hijacking persistence
- WMI event subscription persistence
- Browser extension persistence
- Application plugin persistence
- Firmware persistence (UEFI)

### 8.3 Zero-Click Detection
- Network IDS for zero-click delivery
- Host-based detection (EDR)
- Memory scanning for zero-day
- Behavioral analysis detection
- Sandboxing detection (Cuckoo)
- Taint analysis detection
- Control flow integrity detection
- Address space layout detection
- Hardware security module detection
- Trusted execution environment detection

---

*ZEROCLICK MODE — For no-interaction exploit chains*
*Works on iOS, Android, Desktop, IoT, Network, and Industrial systems*
