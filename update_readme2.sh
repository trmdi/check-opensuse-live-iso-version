#!/usr/bin/env bash

# File to generate
OUTPUT_FILE="README.md"

# Run the python script and store the JSON output
JSON_DATA=$(python3 run2.py)

# Check if the python script executed successfully
if [ $? -ne 0 ] || [ -z "$JSON_DATA" ]; then
    echo "Error: Failed to get data from run2.py" >&2
    exit 1
fi

OPENSUSE_RELEASE=$(echo "$JSON_DATA" | jq -r '.[] | select(.package == "openSUSE-release") | .version' | cut -d "-" -f 1)

JSON_DATA=$(echo "$JSON_DATA" | jq 'del(.[] | select(.package == "openSUSE-release"))')


# Start writing the README.md with the requested header formatting
cat << EOF > "$OUTPUT_FILE"
# openSUSE Tumbleweed Installation / Live ISO

#### Download Links:
* **KDE Live:** [Download ISO](https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-KDE-Live-x86_64-Current.iso?mirrorlist)
* **GNOME Live:** [Download ISO](https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-GNOME-Live-x86_64-Current.iso?mirrorlist)
* **XFCE Live:** [Download ISO](https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-XFCE-Live-x86_64-Current.iso?mirrorlist)
* **Offline Image:** [Download ISO](https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-DVD-x86_64-Current.iso?mirrorlist)

---

### Current release $OPENSUSE_RELEASE:

| Component | Version |
| :--- | :--- |
EOF

echo "$JSON_DATA" | jq -c '.[]' | while read -r item; do
    display=$(echo "$item" | jq -r '.display')
    version=$(echo "$item" | jq -r '.version')

    # Append the row
    echo "| **$display** | $version |" >> "$OUTPUT_FILE"
done

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
	echo "Warning: Not a git repository. Skipping version comparison and git operations."
	echo "README.md has been updated locally with a pretty table."
	exit 0
fi

if git diff --quiet README.md; then
	echo "No version changes detected in README.md. Exiting."
	exit 0
fi

echo "New version updates detected!"

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
