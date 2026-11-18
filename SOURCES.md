# BOUNTY — Vetted Sources

Sumber eksternal yang dipakai sebagai referensi. Tidak ada kode yang disalin mentah dari sumber mana pun. Tool di paket ini adalah wrapper aman yang memanggil binary resmi bila tersedia.

## Recon & scanning

- [ProjectDiscovery Open Source](https://docs.projectdiscovery.io/opensource) — index dokumentasi resmi `subfinder`, `httpx`, `nuclei`, `katana`.
- [Subfinder usage](https://docs.projectdiscovery.io/opensource/subfinder/usage) — enumerasi subdomain pasif.
- [Running httpx](https://docs.projectdiscovery.io/opensource/httpx/running) — HTTP probing + tech detection.
- [OWASP WSTG](https://wstg.owasp.org/) — metodologi testing web resmi.
- [OWASP WSTG repository](https://github.com/OWASP/wstg) — source guide, CC licensed.

## Reporting & severity

- [HackerOne: Quality Reports](https://docs.hackerone.com/en/articles/8475116-quality-reports) — struktur laporan bermutu.
- [HackerOne: Submitting Reports](https://docs.hackerone.com/en/articles/8473994-submitting-reports) — alur submit.
- [HackerOne: Defining Severity](https://docs.hackerone.com/en/articles/8495674-defining-severity) — pedoman severity.
- [HackerOne: Disclosure Guidelines](https://hackerone.com/disclosure-guidelines) — coordinated disclosure.
- [Bugcrowd: Reporting a Bug](https://docs.bugcrowd.com/researchers/reporting-managing-submissions/reporting-a-bug) — pelaporan Bugcrowd.
- [FIRST CVSS v4.0](https://www.first.org/cvss/v4.0/specification-document) — spesifikasi CVSS resmi.

## Hardening rules applied

- Tidak ada `shell=True`.
- Semua subprocess memakai arg list dan timeout.
- Scope divalidasi sebelum target diproses.
- Metadata IP / private IP / loopback diblokir default.
- Redirect tidak diikuti otomatis pada evidence fetch.
- Header sensitif dan token di-redact sebelum ditulis.
- Tidak ada hardcoded API key, cookie, bearer token, atau path pribadi.
- Tidak ada destructive action, state-changing request, atau eksfiltrasi data korban.
- Output lokal saja; tidak ada upload otomatis.
