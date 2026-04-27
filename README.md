# Wirecup

A minimal DSL for low-fidelity UI wireframes. Write `.cup` files and see live HTML previews in your browser.

## Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/ruibeard/wirecup/main/install | bash
```

That's it. Browser opens at `http://localhost:8765/`. Edit `.agents/.cup/*.cup` files and see changes live.

## Installation

The one-liner does:

1. Downloads `wirecup` (executable Python script)
2. Downloads `wirecup.css` (styling)
3. Creates `.agents/.cup/` directory
4. Runs `./wirecup .` to start dev server

## Usage

### Development Mode

```bash
./wirecup [project_dir] [-p PORT] [--save]
```

**Flags:**
- `-p PORT` - port to serve on (default: 8765)
- `--save` - also write `.html` files alongside `.cup` files

**What it does:**
- Watches `.agents/.cup/` for changes
- Live-reloads in browser
- Opens browser automatically

### One-shot Rendering

```bash
./wirecup --render < input.cup > output.html
```

Read `.cup` from stdin, write HTML to stdout.

## Project Structure

```
your-project/
├── wirecup              # Executable script (Python)
├── wirecup.css          # Styling
└── .agents/
    └── .cup/            # Your wireframe files
        ├── page1.cup
        ├── page2.cup
        └── _includes/   # Shared snippets
```

## Requirements

- Python 3.7+
- Any OS (macOS, Linux, Windows)

## License

MIT
