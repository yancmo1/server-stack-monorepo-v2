#!/bin/bash
# Restore UI redesign files to last committed state (HEAD)
# Run from repository root.
set -euo pipefail
FILES=( \
  "apps/5k-tracker-pwa/templates/base.html" \
  "apps/5k-tracker-pwa/static/css/style.css" \
)

echo "Restoring UI files to HEAD..."
for f in "${FILES[@]}"; do
  if git ls-files --error-unmatch "$f" > /dev/null 2>&1; then
    git restore --source=HEAD -- "$f"
    echo "Restored $f"
  else
    echo "File $f not tracked by git, skipping"
  fi
done

echo "Done."
