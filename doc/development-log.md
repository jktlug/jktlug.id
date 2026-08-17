# Development Session Log

This document captures major changes and decisions made during development
sessions.

---

## 2026-05-28 — Python E2E Tests, Private Registry, and k3s Deployment

### Summary

Added a Python Playwright end-to-end test suite, set up documentation for it,
clarified the Haskell unit test architecture, and re-wired CI/CD to push Docker
images to a self-hosted private registry on a humble VPS with automatic k3s
deployment.

---

### 1. Python Playwright End-to-End Tests

**Motivation:** The existing Haskell HTF tests verify parser logic, but there
was no automated way to verify the generated static site renders correctly in a
real browser.

**What was added:**

| File | Purpose |
|---|---|
| `tests/e2e/requirements.txt` | Python dependencies (`pytest`, `pytest-playwright`) |
| `tests/e2e/conftest.py` | Session-scoped fixture that starts a local HTTP server serving `_site/` and yields a `base_url` |
| `tests/e2e/test_homepage.py` | Tests homepage title, about section, navigation menu, and external link security attributes |
| `tests/e2e/test_wiki.py` | Tests wiki pages (`Main_Page`, `JKTLUG:Organization`) render correctly |
| `tests/e2e/run.sh` | Convenience script: installs deps/browsers and runs pytest |
| `doc/e2e-tests.md` | Full documentation: installation, running, architecture, CI integration, troubleshooting |

**Integration with existing build scripts:**

- Updated `./Test` to accept `-e` / `--e2e` flag. When passed, the script builds
  the site and then runs `tests/e2e/run.sh`.
- Updated `.gitignore` to ignore Python test artifacts (`__pycache__`,
  `.pytest_cache`, `.venv`).

**How to run:**

```bash
# Build site + run e2e tests
./Test --e2e

# Or run only e2e tests (site must already be built)
tests/e2e/run.sh
```

---

### 2. Unit Test vs. E2E Test Architecture Clarification

**Key insight:** The project has **two distinct test layers** that serve
different purposes and cannot replace each other.

| Layer | Language | Framework | Tests |
|---|---|---|---|
| **Unit tests** | Haskell | HTF | Individual functions (`parsePage`, `fixWikiLinks`, etc.) |
| **E2E tests** | Python | Playwright | Final rendered HTML in a real browser |

**Existing test harness:**

- `app/Test.hs` is the HTF test runner. It imports test modules via
  `import {-@ HTF_TESTS @-} ModuleNameTest` and auto-discovers `test_*`
  functions using the `htfpp` preprocessor.
- `app/SiteCompiler.hs` is **not** a test file—it is the Hakyll site compiler
  that generates `_site/`.

**Coverage status:**

| Module | Has unit tests? |
|---|---|
| `JKTLUG.Hello` | ✅ `HelloTest.hs` |
| `JKTLUG.MediaWiki` | ⚠️ Partial (`MediaWikiTest.hs`) |
| `JKTLUG.Parser` | ❌ No |
| `JKTLUG.WikiLink` | ❌ No |
| `JKTLUG.WikiParam` | ❌ No |

**Recommendation:** Keep both. E2E tests verify the user-facing output; unit
tests are essential for the custom MediaWiki parser pipeline because they
pinpoint exact function failures instead of making you dig through HTML.

---

### 3. GitLab CI/CD and k3s Relationship

**How they connect:**

1. GitLab CI builds the site and creates a lightweight runtime Docker image
   (`Dockerfile.runtime`).
2. The image is pushed to a container registry.
3. The `deploy-k3s` job (manual trigger) uses `kubectl set image` to update the
   k3s Deployment, then waits for the rollout to complete.

**Pipeline stages:**

```
build-site → run-tests → pages (GitLab Pages)
                        → docker-build (Registry)
                          → deploy-k3s (kubectl patch)
```

**Important discrepancy noted:**

- `.gitlab-ci.yml` pushes to **GitLab Container Registry** (`$CI_REGISTRY_IMAGE`).
- `k3s/README.md` references **GHCR** (`ghcr.io/jktlug/JKTLUG.id`).

This suggests the project may have historically used GitHub Actions, while the
GitLab CI file was added later. The registries need to be aligned for a single
source of truth.

---

### 4. Self-Hosted Private Registry on a Humble VPS

**Decision:** Instead of relying on GHCR or GitLab Registry, run a private
Docker Registry directly on the VPS that hosts k3s.

**Why:** Full control, no external dependency, and a Docker Registry + Caddy
uses only ~50 MB RAM—perfect for a small VPS.

**Files created:**

| File | Purpose |
|---|---|
| `registry/docker-compose.yml` | Runs Docker Registry + Caddy reverse proxy |
| `registry/Caddyfile` | Automatic HTTPS (Let's Encrypt) + basic auth |
| `registry/README.md` | VPS setup instructions |
| `k3s/registries.yaml` | k3s `containerd` configuration for registry authentication |

**Architecture:**

```
GitHub Actions Runner
    │
    ├── build job ──► compiles _site/
    │
    ├── push-image job ──► builds Dockerfile.runtime
    │                      pushes to registry.JKTLUG.id/jktlug/JKTLUG.id:<sha>
    │
    └── deploy-k3s job ──► kubectl set image
                           kubectl rollout status
                              │
                              ▼
                        k3s cluster (same VPS or elsewhere)
                        pulls image from registry.JKTLUG.id
```

**Required GitHub secrets:**

| Secret | Value |
|---|---|
| `REGISTRY_USERNAME` | Caddy basic auth user |
| `REGISTRY_PASSWORD` | Caddy basic auth password |
| `KUBECONFIG` | Base64-encoded k3s kubeconfig |

**k3s node configuration:**

```bash
sudo cp k3s/registries.yaml /etc/rancher/k3s/registries.yaml
sudo systemctl restart k3s
```

---

### 5. GitHub Actions Workflow Updated

**File:** `.github/workflows/main.yaml`

**Changes:**

- `REGISTRY` changed from `ghcr.io` to `registry.JKTLUG.id`
- Login step now uses `secrets.REGISTRY_USERNAME` and `secrets.REGISTRY_PASSWORD`
  instead of `GITHUB_TOKEN`
- `push-image` job now explicitly builds `Dockerfile.runtime` and pushes to the
  private registry with both `:latest` and `:<sha>` tags
- Added `deploy-k3s` job that updates the Deployment and waits for rollout
- Removed the duplicate `.github/workflows/private-registry.yml`

**k3s manifest updated:**

- `k3s/deployment.yaml` now defaults to
  `registry.JKTLUG.id/jktlug/JKTLUG.id:latest`

---

### Files Changed / Created in This Session

```
.github/workflows/main.yaml          (rewritten for private registry)
.gitignore                           (+ Python artifacts)
Test                                 (+ --e2e flag)
doc/e2e-tests.md                     (new)
doc/development-log.md               (new, this file)
k3s/deployment.yaml                  (image → private registry)
k3s/registries.yaml                  (new)
registry/Caddyfile                   (new)
registry/README.md                   (new)
registry/docker-compose.yml          (new)
tests/e2e/conftest.py                (new)
tests/e2e/requirements.txt           (new)
tests/e2e/run.sh                     (new)
tests/e2e/test_homepage.py           (new)
tests/e2e/test_wiki.py               (new)
```

---

### Next Steps / Open Questions

1. **Unit test coverage:** Consider adding `WikiLinkTest.hs` and
   `WikiParamTest.hs` to the Haskell HTF suite.
2. **TLS for registry:** Caddy handles this automatically, but ensure
   `registry.JKTLUG.id` DNS points to the VPS before starting Caddy.
3. **Registry backup:** `./registry/data/` should be included in backup
   strategy.
4. **Image retention:** The registry will grow over time. Consider setting up
   a garbage collection policy or periodic cleanup job.
5. **CI trigger:** The `deploy-k3s` job is automatic on `main` pushes. If you
   want a manual approval gate, add an `environment` with required reviewers.
