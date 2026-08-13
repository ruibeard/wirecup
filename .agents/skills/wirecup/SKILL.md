---
name: wirecup
description: A tiny DSL for low-fidelity UI mockups
---

# Skill: wirecup

Wirecup is a tiny DSL for low-fidelity UI mockups.

You write `.cup` source. The wirecup server renders it. Never write the HTML
yourself, and never ask a tool to hand HTML back to you.

## Running it

Start the server once per project:

```bash
wirecup .
```

That watches `.wirecup/*.cup` and `wirecup.css`, serves the preview on port
8765, and reloads the browser on every change.

## The MCP server

The same binary serves MCP on stdin/stdout:

```bash
wirecup . --mcp
```

Two tools. Use your normal file tools to read, list or delete mocks.

| Tool | Use |
|------|-----|
| `spec` | this whole spec in one block |
| `write` | save a mock, get its preview URL |

`write` checks the source with the same parser that draws it. Bad source is
reported with line numbers and never reaches disk.

Write mocks to `.wirecup/name.cup`. Route `/name` renders `.wirecup/name.cup`.
The newest edited file is the default page at `/`.

If the project has no `wirecup` binary, fetch one:

```bash
curl -fsSL https://raw.githubusercontent.com/ruibeard/wirecup/main/install | bash
```

## Spec

### Core rule

The first non-space character on a line selects the element type. The rest of
the line is the content. The space after the type character is optional.

### Elements

| Char | Element | Meaning |
|------|---------|---------|
| `n` | nav | horizontal navigation row |
| `h` | heading | section heading |
| `t` | text | paragraph or label text |
| `i` | input | input placeholder box |
| `b` | button | button or linked button |
| `x` | image | image/chart/media placeholder |
| `s` | select | select/dropdown placeholder |
| `l` | list item | bullet list item |
| `v` | badge | small neutral pill |
| `a` | alert | neutral message box |
| `k` | checkbox | checkbox row |
| `u` | include | reusable snippet |
| `c` | card | container for indented children |
| `r` | row | horizontal flex group for indented children |
| `g` | grid | table-like block |
| `-` | divider | thin divider |
| `=` | divider | thick divider |

### Links

`n` and `b` support `label|target`.

- `http*` stays unchanged
- `/route` stays unchanged
- `target.cup` becomes `/target`
- `target` becomes `/target`
- no `|target` means the item does not navigate

### Nav

Nav items split on 2 or more spaces, so a label may hold single spaces:

```
n Home|home  Live Rooms|live-rooms  Docs|https://example.com
```

`n` draws its own bottom rule. Do not put a `=` under it.

### Containers and indentation

`c`, `r` and `g` take indented children. Indentation defines the structure.
Children continue until the indentation returns to the parent level.

Cards inside an `r` share the width evenly.

### Grid

The `g` line is the header row. Indented lines below it are data rows.

Data rows are rows, not elements. Their first character means nothing.

- cells split on 2 or more spaces, or on tabs
- a cell may start with `v `, `b `, `s `, `i ` or `k ` to place that element
- any other cell is plain text
- a short row is padded out to the header width

```
g Unit  Status  Action
  12 Madingley Road (4)  v Available  b Select|claim
  4 New Court  v Taken
```

### Lists

Consecutive `l` lines are grouped into one list.

### Includes

Put snippets in `.wirecup/_includes/name.cup`. Call one with `u name arg1 arg2`.
Use `$1`, `$2` and `$*` inside the snippet.

There are no built-in snippets. Every include is a file in the project.

### Alerts and badges

Badges and alerts are neutral sketch elements. They carry no colour meaning.
A mock should not look decided before the decision is made.

### Compact mode

For lower token use:

- omit the space after the element character, for example `hTitle`
- use one space per indentation level
- use tabs between grid cells

### Error rule

An unknown first character on an element line is a spec error. The server shows
the failing line numbers instead of the mock.

Examples belong in `examples/`, not in this skill.
