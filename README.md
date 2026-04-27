# Wirecup

A minimal DSL for low-fidelity UI wireframes. Write `.cup` files and see live HTML previews in your browser.

## Quick Start

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ruibeard/wirecup/main/install)
```

That's it. Browser opens at `http://localhost:8765/`. Edit `.agents/.cup/*.cup` files and see changes live.

## Installation

The one-liner install script does:

1. Downloads `wirecup` (executable Python script)
2. Downloads `wirecup.css` (styling)
3. Creates `.agents/.cup/` directory for your wireframes
4. Runs `./wirecup .` to start the dev server

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

Read `.cup` from stdin, write HTML to stdout. Useful for build scripts.

## Project Structure

After install, you have:

```
your-project/
├── wirecup              # Executable script (Python)
├── wirecup.css          # Styling
└── .agents/
    └── .cup/            # Your wireframe files
        ├── page1.cup    # Wireframe definition
        ├── page2.cup
        └── _includes/   # Shared snippets
```

## `.cup` Syntax

See examples in the Wirecup repo's `.agents/.cup/` directory.

## Requirements

- Python 3.7+
- Any OS (macOS, Linux, Windows)

## License

MIT
