#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# 1. Get the latest snapshot
python3 run.py > output.json

# 2. Initialize the README file with a clean header and Markdown Table structure
cat << 'EOF' > README.md
# openSUSE Live ISO

Automated daily builds tracker for openSUSE Live images.

| Flavor | Version | Build ID | Download Link |
| :--- | :--- | :--- | :--- |
EOF

# 3. Loop through each item in the JSON array using jq
jq -c '.[]' output.json | while read -r item; do
    # Extract fields from the current JSON object
    FLAVOR=$(echo "$item" | jq -r '.flavor')
    VERSION=$(echo "$item" | jq -r '.version')
    BUILD_ID=$(echo "$item" | jq -r '.build_id')
    DOWNLOAD_LINK=$(echo "$item" | jq -r '.download_link')

    # Append the row inside the markdown table format
    echo "| **$FLAVOR** | \`$VERSION\` | \`$BUILD_ID\` | [Download Image]($DOWNLOAD_LINK) |" >> README.md
done

# 4. Clean up temporary JSON file
rm output.json

# 5. Check if we are inside a valid Git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "Warning: Not a git repository. Skipping version comparison and git operations."
  echo "README.md has been updated locally with a pretty table."
  exit 0
fi

# 6. Check for changes
if git diff --quiet README.md; then
  echo "No version changes detected across flavors. Exiting."
  exit 0
fi

echo "New version updates detected!"

# 7. Only perform Git operations if running inside GitHub Actions
if [ "$GITHUB_ACTIONS" = "true" ]; then
  echo "Running in GitHub Actions environment. Committing and pushing changes..."

  git config --global user.name "github-actions[bot]"
  git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

  git add README.md
  git commit -m "chore: update openSUSE Live ISO flavors and versions"
  git push
else
  echo "Running locally within a Git repo. README.md has been updated, skipping git commit/push."
fi
