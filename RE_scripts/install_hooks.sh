#!/usr/bin/env bash
# install_hooks.sh - one-time activation of the pre-commit syntax gate by
# pointing core.hooksPath at RE_scripts/hooks. Not run automatically during
# the branch merge: activating affects EVERY clone/worktree of this repo
# (core.hooksPath lives in shared config), so it is an explicit step.
set -eu
cd "$(dirname "$0")/.."
git config core.hooksPath RE_scripts/hooks
chmod +x RE_scripts/hooks/pre-commit
echo "hooks active: git commits now parse-check staged .py/.sh/.bash"
