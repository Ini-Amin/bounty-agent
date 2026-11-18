---
name: validate
description: Gate validasi temuan bug bounty sebelum dilaporkan.
---

# Validate — Bug Bounty Finding Gate

Jangan lapor sebelum gate ini lolos.

## 7 pertanyaan
1. Apakah target dalam scope program?
2. Apakah celah benar-benar ada (bukan teori)?
3. Apakah ada impact nyata?
4. Apakah bisa direproduksi?
5. Apakah bukti cukup (request/response/screenshot)?
6. Apakah tidak termasuk known issue / duplicate?
7. Apakah remediasi bisa dijelaskan?

## Keputusan
- Semua ya → PASS
- Satu no → KILL / DOWNGRADE / CHAIN REQUIRED

Output: `PASS`, `KILL`, `DOWNGRADE`, atau `CHAIN REQUIRED` + alasan.
