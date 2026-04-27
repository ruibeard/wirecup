#!/usr/bin/env bash
set -euo pipefail

base_url="https://raw.githubusercontent.com/ruibeard/wirecup/main"

mkdir -p .agents/.cup .agents/skills/wirecup
curl -fsSL "$base_url/wirecup" -o wirecup
curl -fsSL "$base_url/wirecup.css" -o wirecup.css
curl -fsSL "$base_url/.agents/skills/wirecup/SKILL.md" -o .agents/skills/wirecup/SKILL.md

chmod +x wirecup

# Keep downloaded files out of git
if [ -f .gitignore ]; then
    if ! grep -qxF "wirecup" .gitignore 2>/dev/null; then
        echo "wirecup" >> .gitignore
    fi
    if ! grep -qxF "wirecup.css" .gitignore 2>/dev/null; then
        echo "wirecup.css" >> .gitignore
    fi
else
    printf 'wirecup\nwirecup.css\n' > .gitignore
fi

printf 'Installed Wirecup. Run: ./wirecup .\n'

./wirecup .
