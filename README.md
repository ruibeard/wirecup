# Wirecup

Text-based wireframe language for rapid low-fidelity mockups.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/ruibeard/wirecup/main/install | bash
```

## Usage

### Watch & Preview

```bash
./wirecup .
```

Opens `http://localhost:8765` with live reload. Edit files in `.wirecup/` and see changes instantly.

### Render Single File

```bash
./wirecup input.cup
```

Generates `input.html` in the same directory.

### Preview in Browser

```bash
./wirecup --web input.cup
```

Opens rendered mockup in browser, closes when you press Enter.

### Flags

- `-p PORT` - custom port (default: 8765)
- `--watch DIR` - watch custom directory

## What It Does

Watches `.agents/.cup/` for `.cup` files. Each file becomes a clickable route. Renders to HTML mockups instantly. Hot-reloads in browser.

## Syntax

One character per line = one UI element.

```
h Heading
t Paragraph text
i Input field
b Button|/next-page
n nav link|/ about|/about
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

## Example

Create `.wirecup/login.cup`:

```
h Login
t Enter credentials
i Email
i Password
b Sign In|dashboard
```

Run `./wirecup .` → visit `http://localhost:8765/` → click "login.cup" → see it rendered.

Click "Sign In" button → navigates to `/dashboard` route.

## Use With AI

The install includes `.agents/skills/wirecup/SKILL.md` for OpenCode/LLM integration.

Tell an LLM: *"Use the wirecup skill to write a mockup for [description]"*

The LLM writes `.cup` files to `.wirecup/`. You see them render live at `http://localhost:8765`.

## Requirements

- macOS (arm64)

## License

MIT