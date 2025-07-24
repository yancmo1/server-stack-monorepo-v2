#!/bin/bash
# commit_all_git_repos.sh
# Recursively find all git repos and commit/push changes

find . -type d -name ".git" | while read gitdir; do
  repo_dir=$(dirname "$gitdir")
  echo "Processing $repo_dir"
  cd "$repo_dir"
  git add .
  CHANGES=$(git status --porcelain)
  if [ -n "$CHANGES" ]; then
    MSG="Update: sync all new files and changes before migration ($(date '+%Y-%m-%d %H:%M:%S'))"
    git commit -m "$MSG"
    git push
    echo "Committed and pushed in $repo_dir"
  else
    echo "No changes to commit in $repo_dir"
  fi
  cd - > /dev/null
done
