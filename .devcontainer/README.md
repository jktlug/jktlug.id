# TLUG Website Dev Container

This directory contains the [Development Container](https://containers.dev/) configuration for the TLUG (Tokyo Linux Users Group) website project.

## What's Inside

- **Base Image**: `debian:bookworm-slim`
- **Haskell Toolchain**: Stack 3.1.1 (matching the version in `./Test`)
- **Node.js**: LTS 22.x (required for Pi Coding Agent)
- **Pi Coding Agent**: Installed globally from https://pi.dev/
- **System Dependencies**: All packages required to build Hakyll and its native dependencies (zlib, GMP, FFI, etc.)
- **User**: Non-root `dev` user (UID 1000)
- **Shell**: Zsh with Oh My Zsh

## Quick Start

### Using VS Code

1. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open the project root in VS Code
3. Press `F1` → "Dev Containers: Reopen in Container"
4. VS Code will build the container and set up the environment

### Using GitHub Codespaces

1. Navigate to the repository on GitHub
2. Click **Code** → **Codespaces** → **Create codespace on master**

### Manual (Docker)

```bash
# Build the image
docker build -t tlug-dev -f .devcontainer/Dockerfile .

# Run with your source mounted
docker run -it --rm \
  -v "$(pwd):/workspace" \
  -v "$HOME/.pi:/home/dev/.pi" \
  -w /workspace \
  -p 8000:8000 \
  tlug-dev bash
```

## Post-Create Setup

The container automatically runs:
- `stack setup` — Downloads GHC for the project's LTS snapshot
- `stack build --dependencies-only` — Pre-builds Haskell dependencies

This may take **10–30 minutes** on first creation, depending on your connection.

## Pi Coding Agent

[Pi](https://pi.dev/) is a minimal terminal coding harness pre-installed in this container.

### Getting Started with Pi

```bash
# Start Pi in interactive mode
pi

# Run a one-off query in print mode
pi -p "explain the Hakyll build process"

# Check Pi version
pi --version
```

### Pi Configuration

Your local Pi configuration (`~/.pi`) is mounted into the container at `/home/dev/.pi`, so your API keys, themes, and extensions are preserved across container sessions.

If you haven't used Pi before, you'll need to configure it on first run:
```bash
pi
# Then follow the prompts to set up your API keys
```

### Pi Modes

- **Interactive**: Full TUI experience — just run `pi`
- **Print/JSON**: `pi -p "query"` for scripts, `--mode json` for event streams
- **RPC**: JSON protocol over stdin/stdout for non-Node integrations

For more details, see the [Pi documentation](https://pi.dev/).

## Common Tasks

### Build the site
```bash
stack build --test
stack exec site-compiler rebuild
```

### Start the preview server
```bash
stack exec site-compiler watch -- --host 0.0.0.0 --port 8000
```
Then open http://localhost:8000 in your browser.

### Run tests
```bash
./Test --test-only
```

### Full build + release (local)
```bash
./Test
```

## Port Forwarding

Port `8000` is automatically forwarded for the Hakyll preview server.

## SSH Access

Your local `~/.ssh` directory is mounted read-only into the container at `/home/dev/.ssh`, so Git operations over SSH work out of the box.

## Pi Persistence

Your Pi configuration directory (`~/.pi` on the host) is mounted at `/home/dev/.pi` in the container. This preserves:
- API keys and provider settings
- Custom themes and extensions
- Session history
- Prompt templates
