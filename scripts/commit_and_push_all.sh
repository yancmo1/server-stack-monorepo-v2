#!/bin/bash
# commit_and_push_all.sh
# Commits all changes in the monorepo with an auto-generated message and pushes to origin

cd "$(dirname "$0")"

BRANCH=$(git rev-parse --abbrev-ref HEAD)
CHANGED=$(git status --porcelain)
if [ -z "$CHANGED" ]; then
  echo "No changes to commit."
  exit 0
fi

MSG="Auto-commit: $(date '+%Y-%m-%d %H:%M') - $(git status -s | wc -l) file(s) changed"
git add .
git commit -m "$MSG"
git push origin "$BRANCH"
echo "Committed and pushed to $BRANCH with message: $MSG"
