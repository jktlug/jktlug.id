# Private Docker Registry for jktlug.id

Lightweight registry stack for a humble VPS. Runs Docker Registry behind
Caddy (automatic HTTPS + basic auth).

## Requirements

- A VPS with Docker + Docker Compose
- A domain or subdomain pointing at the VPS (e.g. `registry.jktlug.id`)
- Ports 80 and 443 open

## Quick start

```bash
cd ~/registry

# 1. Generate a password hash for Caddy basic auth
docker run --rm caddy:2-alpine caddy hash-password

# 2. Paste the hash into Caddyfile (replace the example hash)

# 3. Start
docker compose up -d

# 4. Verify
# Caddy will auto-provision a Let's Encrypt certificate.
curl -u jktlug:yourpassword https://registry.jktlug.id/v2/_catalog
```

## Storage

Images are stored in `./data/` (bind-mounted to `/var/lib/registry`).
Back this up if you want to keep your images across server rebuilds.

## Resource usage

| Component | Typical RAM |
|---|---|
| Docker Registry | ~10–30 MB |
| Caddy | ~15–30 MB |
| **Total** | **~50 MB** |

A $5/month VPS (1 vCPU, 1 GB RAM) handles this with room to spare.

## k3s integration

See `k3s/registries.yaml` in the repo for how to give k3s read access.
