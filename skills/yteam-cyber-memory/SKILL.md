---
name: yteam-cyber-memory
description: >-
  Durable memory for the Y-TEAM CYBER project — repo, current state, decisions,
  bugs found, architecture, and the operator's working preferences. Load at the
  START of any Y-TEAM / ghost_* session so context is not lost. Triggers: Y-TEAM,
  y-team-cyber, ghost_, [REDACTED], obfs4 bridge, burner, 0-leak, src layout.
---

# Y-TEAM CYBER — Project Memory

## Identitas Proyek
- **Repo**: `github.com/[REDACTED]/y-team-cyber` (PUBLIC)
- **Local**: `D:\Y-TEAM-CYBER`
- **Branch aktif**: `main` (satu-satunya)
- **Versi**: 2.7.0
- **Operator**: Bos (senior red team). Commit author: `[REDACTED]`.
- **Tim**: `JinzoU-MwM` (kolaborator; pernah fix `d9d386e` platform-flag live lookup).
- **Tujuan**: portable anti-leak OPSEC stack (Tor + bridge + persona + vault),
  Windows/macOS/Linux, 0-leak dari target & ISP.

## Status Terkini (per akhir sesi)
- **236 test passed**, ruff bersih, CI hijau 3 OS (ubuntu/windows/macos).
- Struktur: **src layout** — 47 modul di `src/ghost/`, root cuma 19 file.
- **0-leak TERVERIFIKASI**: IP asli tidak bocor, DNS via Tor, IPv6 no direct,
  WebRTC blocked, NTP sync, request tanpa proxy = NONE, persona 0 plaintext.
- **obfs4 bridge WORKING** (port 9060) → ISP tidak bisa deteksi Tor.
- **burner email WORKING** (mail.tm, gratis, bisa banyak).

## Riwayat Keputusan Penting

| Keputusan | Alasan |
|---|---|
| Pindah ke `src/` layout | root tadinya 64 file (42 modul numpah) = berantakan |
| `ghost_paths.py` (ROOT resolver) | data runtime (personas/state/evidence) harus di ROOT, bukan src/ghost/ |
| Dual-mode import (package + flat) | `python -m ghost.X` DAN `import ghost_plat` harus jalan |
| Fail-closed untuk semua jaringan | Tor mati = request gagal, BUKAN fallback ke IP asli |
| obfs4 bridge (bukan direct Tor) | direct Tor = ISP bisa deteksi via DPI |
| Burner via mail.tm | 1secmail mati (403); mail.tm API resmi, gratis |
| CI matrix 3 OS | buktikan "works on all OS" secara nyata |

## Bug yang Pernah Ketemu & Difix (pola berulang)

1. **`dirname(__file__)` untuk path data** → file nyasar ke `src/ghost/`.
   PATTERN: selalu `BASE = ghost_paths.ROOT`. Cek: `src/ghost/{personas,ghost_state}` kosong.
   Pernah kena: `persona_gen.save`, `ghost_audit.STATE`, `ghost_guard` x2, `ghost_browser`.
2. **Hardcode path lokal** (`C:\Program Files\...`, `D:\omp`) → pakai env → PATH → standar OS → repo bundle.
3. **Request tanpa proxy** → bocor IP. Cek `tests/test_failclosed.py`.
4. **Killswitch Windows terbalik** (block tor.exe alih-alih allow) → fail-closed (Allow tor + Block all).
5. **`os.path_exists` typo** → `NameError` pasca-UAC.
6. **`ghost_master` tanpa `main()`** → entry point ImportError.
7. **burner create 422 collision** → retry 5x + rotasi domain.
8. **Test pollution** (monkeypatch sys.platform / reload modul) → CI Linux crash.
   JANGAN patch `sys.platform`;pakai `IS_WIN/IS_LINUX/IS_MAC` flag + fixture autouse reset.
9. **DNS leak browser** (camoufox tanpa `network.proxy.socks_remote_dns`) → difix.
10. **NTP tidak sinkron** (Leap Indicator 3) → `ghost_elevate ntp`.

## Preferensi Kerja Bos
- Bahasa: **Indonesia** (chat), teknis English OK.
- Gaya: **langsung, teknis, no fluff**. Jangan minta konfirmasi berlebihan.
- Harus **dicoba nyata** ("sudah lu coba?") — bukan cuma dibaca.
- **"Full"** = semua aspek, jangan setengah. **"Rapi"** = struktur bersih.
- **Jangan pakai akun/email asli** — pakai burner (gratis, banyak).
- **0-leak** termasuk dari ISP (butuh bridge obfs4).
- Setelah kerja: **commit → push via Tor → verifikasi GitHub = lokal**.
- Matikan Tor + bersihin cache setelah selesai.

## Setup Cepat Sesi Baru
```powershell
cd D:\Y-TEAM-CYBER
# 1. nyalain Tor (unduh bundle kalau belum ada)
start tor\tor.exe --SocksPort 9050
# 2. bridge obfs4 (stealth)
start tor\tor.exe -f ghost_state\bridges\torrc-bridge
# 3. test
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q -m "not live"
# 4. verify guard
python -m ghost.ghost_guard
```

## Batas Jujur (dari THREATMODEL)
- Aman dari **target** & **ISP** (dengan bridge).
- BUKAN anonim dari: exit node (lihat target), Cloudflare/WARP (lihat IP asli),
  penegak hukum + subpoena (ISP+Cloudflare bisa diminta).
- Global adversary / timing correlation = di luar scope.
- Identitas (email asli, login akun asli) = jaringan tidak bisa sembunyikan.
