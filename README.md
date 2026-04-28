# Wirecup

Text-based wireframe language for rapid low-fidelity mockups.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/ruibeard/wirecup/main/install | bash
```

This downloads the binary and creates the following:

```
~/.wirecup/
├── .agents/
│   └── skills/
│       └── wirecup/
│           └── SKILL.md           # LLM skill for OpenCode
└── wirecup                         # Compiled binary
```

**Start watching your project:**
```bash
./wirecup .
```

Opens `http://localhost:8765` with live reload.

## How to Use

Tell your LLM: *"Use the wirecup skill to create a mockup for [description]"*

The LLM writes `.cup` files to `.wirecup/`. Changes appear live at `http://localhost:8765`.

## Commands

```bash
./wirecup .                    # Watch & preview (http://localhost:8765)
./wirecup file.cup             # Render to static HTML
./wirecup --web file.cup       # Preview in browser (temporary)
./wirecup . -p 9000            # Custom port
```

## Syntax

One character per line = one UI element.

```
h Heading
t Paragraph text
i Input field
b Button
n Navigation link
x Image placeholder
s Select dropdown
l List item
v Badge
a Alert box
k Checkbox
c Card (indent children)
r Row/flex (indent children)
g Grid/table (indent rows)
- Divider
= Thick divider
```

## Requirements

- macOS (arm64)

## License

MIT