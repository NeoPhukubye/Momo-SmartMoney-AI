#!/bin/bash
# Commit remaining files one at a time, 30 minutes apart
# Started at: $(date)

FILES=("backend/" "docker-compose.yml" "frontend/" "render.yaml")
COMMIT_MSG_PREFIX="add"

for file in "${FILES[@]}"; do
    git add "$file"
    git commit -m "$COMMIT_MSG_PREFIX $file"
    echo "Committed: $file at $(date)"

    # Wait 30 minutes before next commit (unless it's the last file)
    if [ "$file" != "${FILES[-1]}" ]; then
        echo "Waiting 30 minutes before next commit..."
        sleep 1800
    fi
done

echo "All files committed at $(date)"
