---
name: wirecup
description: Sketch low-fidelity UI wireframes as token-efficient .cup files rendered to sketchy HTML
---

Write `.cup` files, render with `python wirecup-render.py <file.cup> -o <file.html>`.

5–20 lines per screen. Max 2 indent levels. `x` for any image/chart placeholder.

Full syntax: `wirecup-spec.md`

## MCP

```bash
git clone https://github.com/ruibeard/mockups
cd mockups/mcp && npm install && npm run build && npm link
```

```json
{ "mcp": { "wirecup": { "type": "local", "command": ["npx", "wirecup-mcp"] } } }
```
