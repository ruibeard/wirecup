#!/usr/bin/env bash
set -euo pipefail

base_url="https://raw.githubusercontent.com/ruibeard/wirecup/main"

mkdir -p .agents/.cup .agents/skills/wirecup
curl -fsSL "$base_url/wirecuprender" -o wirecuprender
curl -fsSL "$base_url/wirecup.css" -o wirecup.css
curl -fsSL "$base_url/.agents/skills/wirecup/SKILL.md" -o .agents/skills/wirecup/SKILL.md

chmod +x wirecuprender

printf 'Installed Wirecup. Run: ./wirecuprender\n'

./wirecuprender