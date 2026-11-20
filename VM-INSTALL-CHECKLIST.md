# VM Install Checklist — OpenCode2API + WARP rotation

Tujuan: mereplikasi gateway rotasi kuota OpenCode di VM baru. Semua nilai rahasia
memakai placeholder — isi di VM, jangan pernah commit.

## 0. Prasyarat VM

- [ ] Linux (Fedora tested), Python 3.10–3.13, Node >= 18
- [ ] Google Chrome, `wireguard-tools`, `ffmpeg`
- [ ] IPv6 `/64` global di interface utama (cek: `ip -6 -brief addr`)
  - Tanpa `/64`, opsi `source_ipv6: auto` tidak bisa dipakai → harus pakai tunnel WARP
- [ ] Akses `sudo` (untuk `wg-quick` kalau pakai WARP tunnel)

## 1. Repo + dependency

```bash
git clone <REPO_URL> ~/Auto-FreeCF
bash ~/Auto-FreeCF/scripts/install.sh      # venv + deps + shim kancahub
kancahub doctor                             # harus bersih
```

## 2. Binary gateway

```bash
install -m 755 <OPENCODE2API_BINARY> ~/.local/bin/opencode2api
~/.local/bin/opencode2api --help            # harus muncul -config / -listen
```

Binary asal: `~/.local/bin/opencode2api` (Go ELF x86-64). Copy juga
`~/.local/bin/opencode2api.bak.*` kalau perlu rollback.

## 3. Config gateway

Buat `~/.config/auto-freecf/opencode2api/config.json` (chmod 600):

```json
{
  "listen": "127.0.0.1:8799",
  "server_keys": [
    "<OC_SK_KEY_1>",
    "<OC_SK_KEY_2>"
  ],
  "anonymous": true,
  "warp": {
    "enabled": true,
    "pool_size": 8,
    "source_ipv6": "auto"
  },
  "proxies": [
    "http://127.0.0.1:25346#pool",
    "http://127.0.0.1:7928"
  ],
  "upstream": {
    "zen": "https://opencode.ai/zen",
    "go": "https://opencode.ai/zen/go",
    "anonymous": "https://opencode.ai/inference"
  },
  "retry": {
    "max_attempts": 12,
    "timeout_seconds": 3600
  },
  "performance": {
    "attempt_timeout_seconds": 180
  }
}
```

- `server_keys`: ambil dari `config.json` mesin lama (secret — jangan taruh di repo)
- `anonymous: true` → upstream `https://opencode.ai/inference`
- `warp.pool_size: 8` → 8 jalur egress
- `retry.max_attempts: 12` → 429 ditelan, coba key/IP lain

## 4. Arahkan OpenCode ke gateway

Di `~/.config/opencode/opencode.json`, blok provider:

```json
"provider": {
  "opencode2api": {
    "name": "OpenCode2API Gateway",
    "npm": "@ai-sdk/openai-compatible",
    "options": {
      "baseURL": "http://127.0.0.1:8799/v1",
      "apiKey": "public"
    },
    "models": {
      "<MODEL_ID>": { "name": "<MODEL_NAME>" }
    }
  }
}
```

Set `model` dan `small_model` di root ke `opencode2api/<MODEL_ID>`.

## 5. Autostart (systemd user)

Copy service, lalu aktifkan:

```bash
mkdir -p ~/.config/systemd/user
cp ~/Auto-FreeCF/scripts/systemd/opencode-anon.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now opencode-anon
systemctl --user status opencode-anon
```

Service menjalankan:

```
~/.local/bin/opencode2api -config ~/.config/auto-freecf/opencode2api/config.json
```

## 6. Egress — pilih salah satu

### Opsi A — IPv6 source (dipakai mesin sekarang)

- Pastikan interface punya global `/64`
- Biarkan `source_ipv6: "auto"`
- Tidak perlu `wg-quick`

### Opsi B — WARP tunnel (Kalau tidak ada IPv6 /64)

```bash
kancahub warp gen       # generate profil via PetaniProxy
kancahub warp up        # pasang /etc/wireguard/warp.conf + wg-quick
kancahub warp status    # cek egress IP
```

Butuh `~/petani-proxy/core/warp_generator.py` + `sudo` + `wireguard-tools`.

## 7. Proxy lokal

- `127.0.0.1:25346` — pool, harus jalan
- `127.0.0.1:7928` — secondary, di mesin lama sedang mati (opsional)

Cek: `ss -ltnp | grep -E '8799|25346|7928'`

## 8. Verifikasi

```bash
ss -ltnp | grep 8799                       # gateway listen
systemctl --user is-active opencode-anon   # active
curl -s http://127.0.0.1:8799/v1/models -H 'Authorization: Bearer public' | head
opencode                                   # pilih model opencode2api, chat test
```

## Catatan keamanan

- `config.json`, `auth.json`, `opencode.json` mengandung secret → perms 600, gitignore
- Jangan commit `oc_sk_*`, JWT, `cfut_`, `thk_`, session token
- Rotasi kuota ini memakai endpoint anonymous + banyak key/IP — perhatikan batas
  pemakaian masing-masing provider
