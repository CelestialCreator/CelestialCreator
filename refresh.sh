#!/usr/bin/env bash
# Refresh the card locally and push. Fallback while the Actions workflow needs
# the `workflow` scope: gh auth refresh -h github.com -s workflow
set -euo pipefail
cd "$(dirname "$0")"

export GITHUB_TOKEN="$(gh auth token)"   # your own token -> sees private repos too
python3 update_profile.py

git add dark_mode.svg light_mode.svg
git diff --staged --quiet && { echo "no change"; exit 0; }
git -c user.name=Akshay -c user.email=mhaskarakshay1992@gmail.com commit -qm "chore: refresh profile card"
git push
echo "pushed"
