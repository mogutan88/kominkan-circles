#!/usr/bin/env bash
# Rebuild the SPAs and publish them to GitHub Pages.
#
#   ./publish.sh                 # commit message: "Update site (YYYY-MM-DD HH:MM)"
#   ./publish.sh "my message"    # custom commit message
set -euo pipefail

cd "$(dirname "$0")"

REPO="mogutan88/kominkan-circles"
URL="https://mogutan88.github.io/kominkan-circles/"
MSG="${1:-Update site ($(date '+%Y-%m-%d %H:%M'))}"

echo "==> Building SPAs"
python3 spa/build.py

echo "==> Committing"
git add -A
if git diff --cached --quiet; then
  echo "No changes to publish."
  exit 0
fi
git commit -m "$MSG"

echo "==> Pushing"
git push origin main

# Optionally wait for the Pages build when the GitHub CLI is available.
if command -v gh >/dev/null 2>&1; then
  echo "==> Waiting for GitHub Pages to build"
  for _ in $(seq 1 30); do
    status="$(gh api "repos/$REPO/pages/builds/latest" --jq .status 2>/dev/null || echo unknown)"
    case "$status" in
      built)   echo "Published: $URL"; echo "           ${URL}calendar.html"; exit 0 ;;
      errored) echo "GitHub Pages build failed. See https://github.com/$REPO/actions" >&2; exit 1 ;;
    esac
    sleep 5
  done
  echo "Still building; check $URL in a minute."
else
  echo "Pushed. The site updates in about a minute: $URL"
fi
