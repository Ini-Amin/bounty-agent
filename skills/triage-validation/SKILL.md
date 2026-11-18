---
name: triage-validation
description: Triage cepat temuan bug bounty — filter false positive sebelum PoC penuh.
---

# Triage Validation

Tujuan: memotong temuan lemah sebelum masuk pelaporan.

## Langkah
1. Cek scope dan program policy.
2. Cek apakah perilaku konfirmasi server-side, bukan hanya client-side.
3. Cek apakah impact berubah: data, akses, state, atau akun.
4. Cek apakah butuh auth khusus / user other.
5. Cek apakah ada rate limit, CSRF, atau token yang menghalangi.
6. Cek apakah bukti bisa direproduksi minimal 2x.
7. Tentukan severity awal: info / low / medium / high / critical.

## Output
```text
STATUS: PASS | KILL | DOWNGRADE | NEEDS_MORE
SEVERITY: ...
REASON: ...
NEXT: ...
```
