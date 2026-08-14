---
name: wirecup
description: Tiny DSL for low-fidelity UI mockups. Use when mocking screens, wireframes, or flows in .cup files.
---

# Wirecup

You write `.cup` source. The server renders it. Never write HTML, and never ask
a tool to hand HTML back.

## Run

From the project you are mocking:

```bash
/Users/ruibeard/code/wirecup/dist/wirecup .
```

That watches `.wirecup/*.cup`, serves http://localhost:8765, and reloads on
change.

Write files with your normal editor tools:

- `.wirecup/name.cup` → `/name`
- newest file is `/`

## Spec

### Core rule

The first non-space character on a line picks the element. The rest is content.
The space after the type character is optional.

### Elements

| Char | Element | Meaning |
|------|---------|---------|
| `n` | nav | horizontal navigation row |
| `h` | heading | section heading |
| `t` | text | paragraph or label text |
| `i` | input | input placeholder box |
| `b` | button | button or linked button |
| `x` | image | image/chart/media placeholder |
| `s` | select | closed dropdown placeholder |
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

`s` is a closed box with a ▾. It is not a real dropdown and it does not take options.

### Links

`n` and `b` support `label|target`.

- `http*` stays unchanged
- `/route` stays unchanged
- `target.cup` becomes `/target`
- `target` becomes `/target`
- no `|target` means the item does not navigate

### Nav

Items split on 2 or more spaces, so a label may hold single spaces:

```
n Home|home  Live Rooms|live-rooms  Docs|https://example.com
```

`n` draws its own bottom rule. Do not put a `=` under it.

### Containers

`c`, `r` and `g` take indented children. Children continue until indentation
returns to the parent. Cards inside an `r` share width evenly.

### Grid

The `g` line is the header. Indented lines below it are data rows, not elements.
Their first character means nothing.

- cells split on 2 or more spaces, or on tabs
- a cell may start with `v `, `b `, `s `, `i ` or `k ` to place that element
- any other cell is plain text
- a short row is padded to the header width

```
g Unit  Status  Action
  12 Madingley Road (4)  v Available  b Select|claim
  4 New Court  v Taken
```

### Lists

Consecutive `l` lines become one list.

### Includes

Put snippets in `.wirecup/_includes/name.cup`. Call with `u name arg1 arg2`.
Use `$1`, `$2` and `$*` in the snippet. There are no built-in snippets.

### Alerts and badges

Neutral sketch elements. Colour carries no meaning. A mock should not look
decided before the decision is made.

### Compact mode

- skip the space after the type character (`hTitle`)
- one space per indent level
- tabs between grid cells

### Errors

An unknown first character on an element line is a spec error. The server shows
the failing line numbers instead of the mock.
