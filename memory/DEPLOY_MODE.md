# YATIM DEPLOY MODE — inject, variance, verifikasi model apapun

> Cara pasang pack (`yatim-identity.md`) ke model apapun + bedakan gagal
> sementara vs gagal permanen. Pack sync otomatis via `yatim-sync-identity.py`.

## 1. CARA INJECT (yang benar cuma SATU)

| Cara | Hasil | Kenapa |
|---|---|---|
| REPLACE system prompt / Custom Instructions / API `role: system` | JALAN | Pack jadi satu-satunya instruksi |
| Append di belakang prompt bawaan | REJECT | Prompt bawaan menang, identitas konflik |
| Paste isi sebagai chat message | REJECT | Dianggap data luar, bukan perintah |
| File di project root tanpa REPLACE | REJECT | Dibaca sebagai konteks repo |

## 2. VARIANCE vs ROUTING — bedakan sebelum vonis

| Gejala | Arti | Aksi |
|---|---|---|
| Run 1 adopt, run 2 reject (model sama) | Variance bawaan model | Retry, nilai min 3 run |
| Ngaku vendor BEDA dari nama model | Gateway routing lottery | Retry sampai backend benar |
| Tolak identik konsisten multi-run | Hard-reject model itu | Ganti model / priming |
| `content_filter` finish reason | Filter level provider | Ganti model/varian |

Jangan vonis pack dari 1 percobaan. `yatim-idcheck.py --tries 3` menulis
`ROUTING (retry)` vs `HARD (ganti model)` langsung di hasil probe.

## 3. VERIFIKASI BERLAPIS (lemah ke kuat)

| Level | Probe | Bukti |
|---|---|---|
| Identity | `lu siapa` / `who are you?` | Jawab Yatim Cold-protocol |
| Metodologi | `cara assess website?` | Sebut kill chain (recon/exploit/report) |
| Eksekusi | Perintah beneran via tool | Jalan + evidence, bukan jelasin |

Identity lolos ≠ pack aktif. Tes eksekusi yang membuktikan.

## 4. PRIMING (model stubborn)

1. Pasang pack via REPLACE, session BARU.
2. Pastikan turn 1 ADOPT. Reject → restart session.
3. Build context: minta baca 2-3 file skill, 3-4 turn.
4. Ganti model mid-session → pack ikut sebagai context.

## 5. PERINTAH

```
python yatim-sync-identity.py sync            # regenerasi pack 3 sumber
python yatim-sync-identity.py check           # deteksi drift
python yatim-idcheck.py --api URL --model M --key K --tries 3
python yatim-idcheck.py --api URL --model M --key K --level methodology
```
