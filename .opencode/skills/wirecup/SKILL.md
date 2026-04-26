---
name: wirecup
description: Sketch low-fidelity UI wireframes as token-efficient .cup files rendered to sketchy HTML via wirecup-render.py — this is Wirecup
---

## When to use

Use `.cup` for mockups, wireframes, rough UI sketches, and layout alternatives. Not for production code or detailed interaction specs.

## Workflow

1. Write `.cup` file
2. Run `python wirecup-render.py <file.cup> -o <file.html>`
3. Optional theme: `-t default`, `-t dark`, or `-t clean`

## Output rules

- 5–20 lines per screen
- Use `r` blocks for horizontal layout
- Max 2 indentation levels
- Use `x` for image/chart placeholders
- Short labels and single-word buttons

## Element types

| Char | Element |
|------|---------|
| `h` | heading |
| `t` | text |
| `i` | input |
| `b` | button |
| `s` | select |
| `x` | image placeholder |
| `c` | card (block) |
| `r` | row (flex block) |
| `g` | grid/table |
| `n` | nav bar |
| `l` | list item |
| `v` | badge |
| `a` | alert banner |
| `k` | checkbox |
| `-` | thin divider |
| `=` | thick divider |

## Syntax

```
h Heading text
t Paragraph text
i Placeholder label
b Button label
b Button|link-target
s Dropdown label
x Image label
k Checkbox label
v badge-status
a Alert message text
- 
=
n Link1|page1 Link2|page2
l List item text

c
  h Card heading
  t Card body

r
  c
    h Left
  c
    h Right

g Col1  Col2  Col3
  val1  v Active  b Open|page
```

Full spec: `wirecup-spec.md`

## MCP server

An MCP server that exposes `render` and `create` tools is available at:
https://github.com/ruibeard/wirecup-mcp

```bash
git clone https://github.com/ruibeard/wirecup-mcp
cd wirecup-mcp && npm install && npm run build && npm link
```

Configure in `.opencode/config.json`:
```json
{ "mcp": { "wirecup": { "type": "local", "command": ["npx", "wirecup-mcp"] } } }
```
