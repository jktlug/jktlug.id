#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing Python test dependencies..."
    pip3 install -r requirements.txt
fi

if ! python3 -c "import playwright" 2>/dev/null; then
    echo "Installing Playwright browsers..."
    python3 -m playwright install chromium
fi

echo "Running e2e tests..."
python3 -m pytest "$@"
