#!/usr/bin/env bash
# Install repository-local git hooks by setting core.hooksPath to .githooks
set -euo pipefail

echo "Installing git hooks (setting core.hooksPath to .githooks)"
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit

echo "Installed. To enable hooks for this repo on other clones, run:"
echo "  git config core.hooksPath .githooks"
