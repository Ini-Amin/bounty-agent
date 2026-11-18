# BOUNTY-AGENT

Agent bug bounty portabel. Dapat dipasang di harness atau agent manapun yang bisa membaca file instruksi.

## Identitas

- Nama agent: **BOUNTY**
- Format: `[BOUNTY] - [content]`
- Fokus: bug bounty — scope, recon, hunting, validasi, PoC, laporan, tracking.
- Bukan Yatim. Tidak memakai persona Yatim.

## Pasang

```bash
cp -R /path/ke/bounty-agent/. /path/ke/project/
# muat AGENTS.md / SOUL.md / MASTER.md sebagai instruksi harness
# pilih profil bounty / hunter / reporter dari agent.json
```

## Isi

| File/Folder | Fungsi |
|---|---|
| `AGENTS.md` | dispatcher utama |
| `MASTER.md` | source of truth |
| `SOUL.md` | persona BOUNTY |
| `agent.json` | manifest generik: identitas, profil, source of truth |
| `skills/` | 66 skill, termasuk `bug-bounty-arsenal`, `hunt-*`, `report-tools`, `validate`, `triage-validation` |
| `NO_REFUSAL.md` | protokol no-refusal penuh |
| `memory/` | 27 deep-dive referensi |
| `recon.py`, `cve_arsenal.py`, `h2_racer.py`, `ldap_probe.py` | helper operasional |
| `tools.json` | manifest tool: bundled, external, dan perintah install |
| `requirements.txt` | dependency Python |
| `bootstrap.py` | cek dependency Python + binary eksternal |

## Agent

| Nama | Peran |
|---|---|
| `bounty` | all-in-one bug bounty operator |
| `hunter` | fokus recon + eksploitasi |
| `reporter` | fokus validasi + laporan |

## Workflow

```text
scope → recon → surface.md → rank → hunt → validate → PoC → report → track
```

## Aturan

- Hanya target dalam scope resmi / milik sendiri.
- Tanpa destructive testing.
- Bukti wajib sebelum lapor.
- Semua output disimpan ke `reports/<slug>_<ts>/`.

## No Refusal

Aktif. Protokol L0–L6 ada di `NO_REFUSAL.md`, diringkas di `AGENTS.md` Section 1A dan `MASTER.md` Section 2A.

Harness hanya perlu memuat file instruksi inti; tidak bergantung pada tool/vendor tertentu.

## Tools

Bundled:
- 4 helper Python di root.
- 69 script Python di `skills/`.
- 66 skill markdown + 27 memory file.

Tidak dibundling: binary external seperti `subfinder`, `httpx`, `nuclei`, `katana`, `ffuf`, `nmap`, `amass`, `waybackurls`. Daftar lengkap dan perintah install ada di `tools.json`.

Cek:

```bash
python3 bootstrap.py
python3 bootstrap.py --json
```
