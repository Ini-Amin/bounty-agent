---
name: yteam-cyber-ops
description: >-
  Operate the Y-TEAM CYBER anti-leak OPSEC stack (github.com/[REDACTED]/y-team-cyber)
  on Windows/Linux/macOS. Use when running/reviewing/deploying the ghost_* stack: Tor+obfs4
  bridge (undetectable to ISP), burner emails, personas/vault, preflight guard, panic/wipe,
  platform per-OS setup, dependency gate, CI matrix. Triggers: Y-TEAM, ghost_, yteam,
  obfs4, bridge, burner, persona, vault, preflight, killswitch, ghost_run, ghost_master.
---

# Y-TEAM CYBER — Operations Skill

Anti-leak OPSEC stack. Repo: `github.com/[REDACTED]/y-team-cyber` (branch `main`).
Local: `D:\Y-TEAM-CYBER`. Versi saat ini: **2.7.0**. Operator: **Bos**.

## Struktur (src layout — sudah rapi)

```
D:\Y-TEAM-CYBER\
├── src/ghost/        # 47 modul (.py). Entry: ghost_run, ghost_master, ghost_deps
├── platform/         # windows/ linux/ macos/ installer + runner (guard salah-OS)
├── tests/            # conftest + 6 test file (~236 test)
├── docs/             # INDEX SETUP RUNBOOK OPS THREATMODEL PORTABLE PLATFORMS GIT-VIA-TOR
├── .github/workflows # CI matrix ubuntu+windows+macos + lint
├── ghost_state/ personas/ evidence/   # data runtime (gitignored, DI ROOT)
├── tor/              # bundle tor.exe + lyrebird.exe + pt_config.json (gitignored)
├── FILE_INDEX.md     # PETA semua file
├── Makefile tasks.bat pyproject.toml requirements*.txt
```

Root: **19 file** saja (0 file .py di root). Semua modul wajib di `src/ghost/`.

## Cara Jalan (WAJIB install deps dulu)

```bash
# gate dependency (fail-closed — semua aksi operasional ditolak kalau kurang)
python -m ghost.ghost_deps info
python -m ghost.ghost_deps check --full
python -m ghost.ghost_deps install --full     # kalau kurang

# launcher lintas-OS (deteksi OS otomatis)
python -m ghost.ghost_run info
python -m ghost.ghost_run check
python -m ghost.ghost_run preflight

# entry point terinstal (pip install -e .)
yteam status | yteam-run info | yteam-deps check
```

Installer per-OS: `platform/windows/install.ps1`, `platform/linux/install.sh`,
`platform/macos/install.command` (install FULL + verifikasi gate).

## Arsitektur Kunci (JANGAN diubah tanpa paham)

- **Dual-mode import**: `python -m ghost.X` (package) DAN `import ghost_plat` (flat).
  `src/ghost/__init__.py` menambahkan folder package ke `sys.path`.
- **`ghost_paths.py`** — resolver ROOT project. Data runtime (`personas/`,
  `ghost_state/`, `evidence/`) ada di ROOT, BUKAN di `src/ghost/`.
  Semua modul pakai `BASE = ghost_paths.ROOT`. JANGAN pakai `dirname(__file__)`
  untuk path data (bug: file nyasar ke `src/ghost/`).
- **Fail-closed**: Tor mati → request GAGAL, bukan fallback ke IP asli.
  Semua request pakai `proxies=` (socks5h). Dijaga `tests/test_failclosed.py`.

## Tor & obfs4 Bridge (ISP tidak bisa deteksi)

```
mode direct : socks5h://127.0.0.1:9050  → ISP bisa lihat "user pakai Tor" (DPI)
mode bridge : socks5h://127.0.0.1:9060  → obfs4, ISP lihat HTTPS biasa (STEALTH)
```

```bash
# setup bridge (butuh tor/ + lyrebird + pt_config.json)
python -m ghost.ghost_bridge build      # 7 bridge obfs4 asli dari pt_config.json
# jalankan: ghost_state/bridges/run_bridge_tor.bat
python -m ghost.ghost_fullchain use     # aktifkan mode bridge (marker)
python -m ghost.ghost_fullchain status  # cek: "bridge mode: YES"
```

`ghost_net.active_port()` auto-pilih 9060 (bridge) atau 9050 (direct).

## Burner Email (gratis, banyak, tanpa akun asli)

```bash
python -m ghost.ghost_burner create [n]     # bikin n email burner ASLI (mail.tm)
python -m ghost.ghost_burner inbox <email> <pw>   # baca OTP/verifikasi
python -m ghost.ghost_burner domains        # daftar domain mail.tm
python -m ghost.ghost_burner gen <region>   # identitas burner + checklist
python -m ghost.ghost_burner hygiene        # checklist anti-korelasi
```

Aturan besi: JANGAN pakai email/nomor asli. Satu akun = satu identitas baru.
Semua request burner lewat Tor (fail-closed).

## Persona & Vault

```bash
python -m ghost.vault status          # cek key + file plaintext
python -m ghost.vault encrypt <file>  # enkripsi
python -m ghost.ghost_master new      # persona baru (auto-encrypt kalau vault aktif)
```
- `.vault_key` di ROOT (random 32-byte; JANGAN pakai passphrase lemah).
- Persona tersimpan `.json.enc` di `personas/`. Plaintext = leak.
- `.vault_key` hilang = persona tidak bisa dibuka. Backup terpisah.

## Gerbang Wajib Sebelum Operasi

```bash
python -m ghost.ghost_master preflight    # harus: "SIAP OPERASI"
python -m ghost.ghost_guard               # 7-check (G0..G7). VERDICT: AMAN = PASS=.. FAIL=0
python -m ghost.ghost_fpguard check       # konsistensi fingerprint
```
G-check: G0 Tor up · G1 jalur Tor (exit != asli) · G2 DNS bukan ISP ·
G3 IPv6 no direct · G4 echo IP · G6 NTP sync · G7 exit-country vs persona.

## Audit & Cleanup

```bash
python -m ghost.ghost_zeroleak       # audit 12 vektor
python -m ghost.ghost_deepaudit      # 14 vektor lanjutan
python -m ghost.ghost_wipe clean     # residu device
python -m ghost.ghost_panic          # DARURAT: kill + shred + NEWNYM
python -m ghost.ghost_elevate full   # hardening admin (NTP/IPv6/DNS/killswitch/MAC)
```
`ghost_elevate ntp` → fix jam (timing fingerprint). Butuh UAC/sudo.

## Git via Tor (push aman)

```powershell
platform\git-tor.ps1 check|setup|start-tor|push|pull|unset-proxy
```
Atau manual:
```powershell
git -c http.proxy=socks5h://127.0.0.1:9050 -c https.proxy=socks5h://127.0.0.1:9050 push origin main
```
Manual start Tor: `tor\tor.exe --SocksPort 9050` atau `-f ghost_state/bridges/torrc-bridge`.

## Test & Lint

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q -m "not live"   # ~236 pass
python -m ruff check .                                                       # harus bersih
```
`test_live.py` butuh Tor hidup (auto-skip kalau mati).

## Aturan Kerja (dari pengalaman nyata)

1. **Coba beneran, jangan cuma baca kode.** Bug nyata (state_path nyasar, 422
   collision, BASE undefined) ketemu HANYA saat dijalankan.
2. **JANGAN hardcode path lokal** (`C:\...`, `D:\omp`). Pakai env → PATH →
   lokasi standar OS → bundle repo.
3. **Fail-closed** untuk semua jaringan. Tor mati = gagal, bukan bocor.
4. **Semua modul di `src/ghost/`**. Data runtime di ROOT via `ghost_paths`.
5. **Deps gate wajib** sebelum operasi (aksi info/deps/status dikecualikan).
6. Merge → main; CI harus hijau 3 OS dulu. Satu branch (`main`).
7. Cleanup: matikan Tor + hapus cache setelah selesai.

## Target Uji (JANGAN nembak target tanpa izin)

- Lab lokal: `http://127.0.0.1:PORT`
- Publik netral: `httpbin.org`, `example.com`
- Lab legal: `testphp.vulnweb.com`, `testasp.vulnweb.com`
- Scope bounty yang eksplisit jadi milik/berwenang operator
