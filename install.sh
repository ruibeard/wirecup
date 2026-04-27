#!/usr/bin/env bash
set -euo pipefail

base_url="https://raw.githubusercontent.com/ruibeard/wirecup/main"

mkdir -p .agents/.cup .agents/skills/wirecup
curl -fsSL "$base_url/wirecup" -o wirecup
curl -fsSL "$base_url/.agents/skills/wirecup/SKILL.md" -o .agents/skills/wirecup/SKILL.md

chmod +x wirecup

printf 'Installed Wirecup. Run: ./wirecup .\n'

./wirecup .
