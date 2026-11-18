---
name: re-tools
description: "Reverse engineering — binary analysis, disassembly, decompilation, debugging."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [re, reverse, binary, disassemble, debug, decompile]
    related_skills: [blackhat-mode, exploit-tools, mobile-tools]
prerequisites:
  commands: [python]
---

# Reverse Engineering Tools

## AI LOAD INSTRUCTION

**When this skill is loaded, the agent MUST:**
1. Identify artifact type first (ELF/PE/Mach-O/APK/firmware/JS) before picking tools.
2. Prefer headless/CLI (r2, objdump, readelf, strings, nm) for automation; Ghidra/IDA for deep C decompile.
3. Never invent offsets or function names — evidence from disassembly only.
4. Output structured JSON (see Output Format) + confidence (OBSERVED/INFERRED/SPECULATIVE).
5. For mobile: Frida/objection hooks; for web: source maps / webpack first, then r2 on wasm/native.
6. No local absolute paths in artifacts; write results under repo-relative `output/` or system temp.

## DECISION TREE

```
Artifact
├─ Web JS bundle?   → source-map / beautify → grep secrets/keys → optional wasm
├─ ELF/PE binary?   → file/readelf|pefile → strings/nm → r2 (aaa, afl, pdf) → Ghidra if needed
├─ APK/IPA?         → apktool/jadx → smali/Java → Frida hooks (SSL pinning, crypto)
├─ Firmware/IoT?    → binwalk extract → filesystem → busybox/creds/keys
├─ Suspicious pack?  → entropy → UPX -d → unpack → resume static
└─ Anti-debug?      → patch jump / Frida bypass → dynamic observe
```

## QUICK REFERENCE

| Task | Command |
|------|---------|
| File identify | `file bin && readelf -h bin` / `pefile` |
| Strings | `strings -a -n 6 bin` / r2 `iz` |
| Symbols | `nm -C bin` / r2 `is` |
| Disassemble | r2: `aaa; afl; pdf @main` |
| Headless decompile | `ghidraRun` / `analyzeHeadless` |
| Compare | radiff2 old new |
| Patch | r2 `wa` / 010 / binary-edit |
| Dynamic | gdb / lldb / x64dbg / strace |

---

## When to Load This Skill

User requests:
- "reverse engineering", "RE", "disassemble", "decompile", "debug"
- "binary analysis", "crack", "patch"

---

## Static Analysis

### Ghidra

```bash
# Start
ghidraRun

# Headless analysis
analyzeHeadless PROJECT_DIR PROJECT -import binary -postScript ExportDecomp.java
```

### radare2

```bash
# Start
r2 binary

# Analysis
aaa  # Analyze all
afl  # List functions
pdf @main  # Disassemble main

# Strings
iz  # Strings in data sections
izz  # All strings

# Info
i  # File info
iI  # Detailed info

# Flags
fl  # List flags
f sym.main  # Set flag
```

### IDA

```bash
# Start
ida64 binary

# Plugins
- Hex-Rays decompiler
- IDA Python
- BinDiff
```

### Binary Ninja

```bash
# Start
binaryninja binary

# API
bn = BinaryView.open("binary")
```

---

## Dynamic Analysis

### GDB

```bash
# Start
gdb ./binary

# Breakpoints
break main
break *0x401000
break function_name

# Run
run
run arg1 arg2

# Stepping
ni  # Next instruction
si  # Step into
c   # Continue

# Examine
x/20x $rsp  # Stack
x/s $rdi  # String
info registers  # Registers
info breakpoints  # Breakpoints

# GDB Enhanced
pwndbg
gef
voltron
```

### ltrace

```bash
# Trace library calls
ltrace ./binary

# Specific functions
ltrace -e malloc+free ./binary
```

### strace

```bash
# Trace system calls
strace ./binary

# Filter
strace -e trace=open,read,write ./binary
```

### WinDbg

```bash
# Start
windbg.exe binary

# Breakpoints
bp main
bp kernel32!CreateFileW

# Run
g

# Examine
dd rsp L20
du rdi
```

---

## Decompilation

### Ghidra (Headless)

```bash
analyzeHeadless /project/dir project \
  -import binary \
  -postScript ExportDecomp.java \
  -scriptPath /scripts/dir
```

### radare2

```bash
r2 -q -c "aaa; s sym.main; pdf" binary
```

### decompyle3

```bash
decompyle3 binary.pyc > source.py
```

### Jadx

```bash
jadx app.apk -d output/
```

---

## Binary Patching

### hexedit

```bash
hexedit binary

# Commands:
# / pattern  — Search
# Enter  — Edit byte
# Ctrl+x  — Save
# Ctrl+c  — Exit
```

### radare2

```bash
r2 -w binary

# Write
wa nop  # Write NOP
wa jmp  # Write jump
wx 90  # Write hex

# Patches
wao nop  # NOP sled
wao jnz  # Invert jump
```

### Binary Diffing

```bash
# BinDiff
bindiff binary1 binary2

# radare2
r2 -q -c "aaa; s sym.main; pdf" binary1 > disasm1.txt
r2 -q -c "aaa; s sym.main; pdf" binary2 > disasm2.txt
diff disasm1.txt disasm2.txt
```

---

## Python RE Tools

### PE Parser

```python
import pefile

def parse_pe(filename):
    pe = pefile.PE(filename)
    
    print(f"Entry point: 0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08x}")
    print(f"Image base: 0x{pe.OPTIONAL_HEADER.ImageBase:08x}")
    
    for section in pe.sections:
        print(f"Section: {section.Name.decode().rstrip(chr(0))}")
        print(f"  Virtual address: 0x{section.VirtualAddress:08x}")
        print(f"  Size: {section.SizeOfRawData}")
    
    return pe
```

### ELF Parser

```python
import struct

def parse_elf(filename):
    with open(filename, 'rb') as f:
        elf = f.read()
    
    # ELF header
    magic = elf[:4]
    if magic != b'\x7fELF':
        return None
    
    # Parse header
    ei_class = elf[4]  # 1=32bit, 2=64bit
    ei_data = elf[5]   # 1=LE, 2=BE
    
    print(f"Class: {'32-bit' if ei_class == 1 else '64-bit'}")
    print(f"Endian: {'Little' if ei_data == 1 else 'Big'}")
    
    return elf
```

### String Extractor

```python
import re

def extract_strings(filename, min_length=4):
    strings = []
    with open(filename, 'rb') as f:
        data = f.read()
    
    # ASCII strings
    for match in re.finditer(b'[\x20-\x7e]{%d,}' % min_length, data):
        strings.append({
            'offset': match.start(),
            'string': match.group().decode('ascii'),
            'type': 'ascii'
        })
    
    return strings
```

---

## Output Format

```json
{
  "binary": "target",
  "format": "ELF64",
  "arch": "x86_64",
  "entry": "0x401000",
  "functions": [
    {"name": "main", "address": "0x401000", "size": 256},
    {"name": "vuln", "address": "0x401100", "size": 128}
  ],
  "strings": [
    {"offset": "0x402000", "string": "password=%s", "type": "ascii"}
  ],
  "imports": ["printf", "scanf", "system"],
  "exports": ["main"]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Permission denied | Binary not executable | chmod +x |
| Format not recognized | Unknown format | Check file type |
| Decompile failed | Obfuscated | Try different tool |
| Debug failed | Anti-debug | Bypass detection |
