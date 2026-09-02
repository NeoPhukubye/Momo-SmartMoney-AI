#!/bin/bash
# Commit and push all files one by one without delay

# Modified files
git diff --name-only --diff-filter=M | while read -r file; do
    echo "Committing modified: $file"
    git add "$file"
    git commit -m "add $file"
    git push
done

# Untracked files
git ls-files --others --exclude-standard | sort | while read -r file; do
    echo "Committing untracked: $file"
    git add "$file"
    git commit -m "add $file"
    git push
done

echo "ALL DONE"
