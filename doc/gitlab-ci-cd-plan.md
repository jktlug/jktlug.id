# GitLab CI/CD Plan for jktlug.id

## Goal
Migrate (or extend) the jktlug.id build and deployment pipeline to **GitLab CI/CD**, leveraging:
1. **GitLab Pages** for static site hosting (alternative to GitHub Pages).
2. **GitLab Container Registry** for the production Nginx Docker image.
3. **Existing K3s manifests** for deployment to a K3s cluster.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   GitLab Repo   │────▶│  GitLab CI/CD    │────▶│  GitLab Pages   │
│                 │     │  (Shared Runner) │     │  (Static Site)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  GitLab Registry │
                       │  (Docker Image)  │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   K3s Cluster    │
                       │  (Production)    │
                       └──────────────────┘
```

---

## Strategy

### Why not pure Docker build in CI?
The existing `Dockerfile` uses **BuildKit cache mounts** (`RUN --mount=type=cache,target=/root/.stack`) to persist Stack/GHC data between local builds. On GitLab shared runners, each job gets a fresh Docker-in-Docker daemon, so this mount cache is lost. A full `docker build` would reinstall GHC and recompile all Haskell dependencies on every pipeline run (~15–30 minutes).

### Recommended approach: "Native Stack + Runtime Image"
1. **Build the site natively** on the CI runner using Stack (just like the old GitHub Actions workflow).
2. **Cache `~/.stack`** with GitLab's cache mechanism. On cache hits, builds take ~1–2 minutes.
3. **Produce `_site/`** as a CI artifact.
4. **GitLab Pages**: rename `_site/` → `public/` and deploy.
5. **Docker image**: build a lightweight `Dockerfile.runtime` that copies the pre-built `_site/` into an Nginx image. This takes ~10 seconds.
6. **Push** the image to GitLab Container Registry.
7. **(Optional) Deploy** to K3s using `kubectl` or a GitLab Agent.

### Local development: CI → local k3s dev (no registry)
For a fully local loop (local GitLab CE + local k3s), the pipeline deploys to the
`jktlug-dev` namespace **without any container registry**:

1. `docker-build-dev` (dind): builds `Dockerfile.runtime` and exports the image as
   an `image.tar` artifact.
2. `deploy-k3s-dev` (`rancher/k3s` image): imports the tarball directly into the
   host k3s containerd via the mounted socket, then `kubectl rollout restart` in
   `jktlug-dev`. Same flow as `bin/dev-deploy.sh`.

One-time host setup (already done on this machine):
- Runner `config.toml` `[runners.docker]`:
  ```toml
  volumes = ["/cache",
    "/run/k3s/containerd/containerd.sock:/run/k3s/containerd/containerd.sock",
    "/etc/rancher/k3s/k3s.yaml:/etc/rancher/k3s/k3s.yaml:ro"]
  extra_hosts = ["host.docker.internal:host-gateway"]
  ```
- Firewall: `sudo ufw allow from 172.16.0.0/12 to any port 6443 proto tcp`
  (ufw blocks Docker bridge → host traffic to the k3s API otherwise).
- Gotcha: in the `rancher/k3s` image, call `ctr`/`kubectl` directly (they are
  symlinks to the k3s multicall binary) — `k3s ctr` / `k3s kubectl` misbehave,
  and there is no `apk` to install extra packages.

### Alternative approach: "Full Docker Build with Registry Cache"
If you prefer to keep a single `Dockerfile` and avoid native Stack builds in CI:
- Use `docker buildx` with `--cache-from type=registry,ref=...` and `--cache-to type=registry,ref=...`.
- Note: BuildKit `RUN --mount=type=cache` caches will still be lost between fresh DinD jobs, but Docker **layer** cache will survive. This means `stack setup` and `stack build --dependencies-only` will hit the layer cache if `stack.yaml.lock` hasn't changed.
- Slower than native Stack caching on cache misses, but simpler conceptually.

---

## Required Files

| File | Purpose |
|------|---------|
| `.gitlab-ci.yml` | Pipeline definition (stages: build → test → deploy → containerize) |
| `Dockerfile.runtime` | Lightweight Nginx image that serves pre-built `_site/` |

---

## Prerequisites

1. **GitLab project** with CI/CD enabled.
2. **Container Registry** enabled (Settings → Packages & Registries → Container Registry).
3. **Pages** enabled (Settings → Pages).
4. If deploying to K3s:
   - A Kubernetes agent (GitLab Agent for Kubernetes) or a runner with `kubectl` access.
   - A `KUBECONFIG` CI/CD variable (file type, masked) or a deploy token.

---

## Pipeline Stages

### 1. `build-site` (stage: build)
- **Image:** `debian:trixie`
- **Cache:** `~/.stack` keyed by `stack.yaml.lock` + `jktlug-website.cabal`
- **Script:**
  ```bash
  stack setup --no-terminal
  stack build --dependencies-only --no-terminal
  stack build --no-terminal
  stack exec site-compiler rebuild
  ```
- **Artifact:** `_site/` (retention: 1 day)

### 2. `test` (stage: test)
- Uses the same Stack cache (read-only).
- Runs `stack build --test --no-terminal`.

### 3. `pages` (stage: deploy)
- **Image:** `busybox`
- **Depends on:** `build-site`
- **Script:** `mv _site public`
- **Rules:** Only on default branch (`main`).
- **Result:** Site available at `https://<namespace>.gitlab.io/jktlug.id` or a custom domain.

### 4. `docker-build` (stage: containerize)
- **Image:** `docker:24` with `docker:24-dind` service.
- **Depends on:** `build-site`
- **Script:**
  ```bash
  docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  docker build -f Dockerfile.runtime -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA -t $CI_REGISTRY_IMAGE:latest .
  docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  docker push $CI_REGISTRY_IMAGE:latest
  ```
- **Rules:** Only on default branch.

### 5. `deploy-k3s` (stage: deploy) — Optional
- **Image:** `bitnami/kubectl:latest`
- **Script:**
  ```bash
  kubectl set image deployment/jktlug-website nginx=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA -n jktlug
  kubectl rollout status deployment/jktlug-website -n jktlug
  ```
- **Rules:** Only on default branch, manual trigger recommended.

---

## Setup Steps

### Step 1: Add CI/CD variables (if needed)
Go to **Settings → CI/CD → Variables**:
- `KUBECONFIG` (file): Base64-encoded kubeconfig for your K3s cluster (optional, for K3s deploy).

### Step 2: Configure Pages domain (optional)
If using a custom domain for GitLab Pages:
1. Add `CNAME` or `TXT` DNS records as instructed in GitLab.
2. Create a `public/CNAME` file during the `pages` job (e.g., `echo "jktlug.id" > public/CNAME`).

### Step 3: Configure Container Registry
No extra steps needed. GitLab provides `$CI_REGISTRY`, `$CI_REGISTRY_USER`, and `$CI_REGISTRY_PASSWORD` automatically.

### Step 4: Update K3s manifests for GitLab Registry
In `k3s/deployment.yaml`, update the image:
```yaml
image: registry.gitlab.com/<namespace>/jktlug.id:latest
```
If the registry is private, create a pull secret:
```bash
kubectl create secret docker-registry gitlab-pull-secret \
  --namespace jktlug \
  --docker-server=registry.gitlab.com \
  --docker-username=<gitlab-deploy-token-username> \
  --docker-password=<gitlab-deploy-token-password>
```
Then uncomment `imagePullSecrets` in `k3s/deployment.yaml`.

---

## Performance Expectations

| Scenario | Approx. Time |
|----------|-------------|
| Cold cache (first run) | 20–30 min |
| Warm Stack cache, source changed | 2–5 min |
| Warm Stack cache, only wiki/template changed | 1–2 min |
| Docker image build (`Dockerfile.runtime`) | 10–30 sec |
| GitLab Pages deploy | 10–20 sec |

---

## Security Notes

1. **Runner tags:** If using shared runners, ensure they support Docker-in-Docker for the `docker-build` job.
2. **Registry authentication:** `$CI_REGISTRY_PASSWORD` is a short-lived job token. For K3s pull secrets, use a **Deploy Token** or **Group Access Token** with `read_registry` scope.
3. **K3s deployment:** Consider requiring **manual approval** (GitLab Environments + `when: manual`) for production K3s deployments.
4. **Image scanning:** Add `trivy` or GitLab's built-in Container Scanning template to the pipeline.

---

## Appendix: GitLab CI/CD File Structure

```
.
├── .gitlab-ci.yml          # Pipeline definition
├── Dockerfile              # Full multi-stage build (local dev / GHCR)
├── Dockerfile.runtime      # Lightweight Nginx image (CI / GitLab Registry)
├── k3s/
│   ├── deployment.yaml     # Points to GitLab Registry image
│   └── ...
└── doc/gitlab-ci-cd-plan.md # This document
```
