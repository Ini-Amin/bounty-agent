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
| `EXECUTION_POLICY.md` | kebijakan eksekusi netral untuk harness manapun |
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

## Execution Policy

Aktif. Target dalam scope sah dikerjakan sampai selesai. Detail di `EXECUTION_POLICY.md`, diringkas di `AGENTS.md` Section 1A dan `MASTER.md` Section 2A.

Harness hanya perlu memuat file instruksi inti; tidak bergantung pada tool/vendor tertentu.

## Tools

Hardened tools (direkomendasikan):

- `tools/_hardening.py` — scope parser, redaction, safe subprocess.
- `tools/recon_run.py` — wrapper allowlisted `subfinder`/`httpx`/`katana`/`nuclei`, scope-gated, no shell, nuclei opt-in.
- `tools/evidence_fetch.py` — fetch satu URL in-scope, tanpa redirect/cookie/auth, redacted, hash.
- `tools/report_build.py` — draft laporan lokal dari findings JSON, tanpa submit.
- `tools/selfcheck.py` — self-test lokal tanpa network.

Sumber dan alasan hardening: `SOURCES.md`. Manifest: `tools.json`.

Legacy tools tetap ada di root (`recon.py`, `cve_arsenal.py`, `h2_racer.py`, `ldap_probe.py`) sebagai referensi; gunakan wrapper di `tools/` untuk pekerjaan baru.

Contoh scope file:

```json
{"program":"demo","in_scope":["example.com","*.example.com"],"out_of_scope":["admin.example.com"]}
```

Jalankan:

```bash
python3 tools/selfcheck.py
python3 tools/recon_run.py --scope scope.json --target example.com --dry-run
python3 tools/report_build.py --findings findings.json --scope scope.json --out report.md
python3 bootstrap.py
```

Tidak dibundling: binary external seperti `subfinder`, `httpx`, `nuclei`, `katana`, `ffuf`, `nmap`, `amass`, `waybackurls`. Daftar lengkap dan perintah install ada di `tools.json`.
