---
name: wirecup
description: A tiny DSL for low-fidelity UI mockups
---

# Skill: wirecup

Wirecup is a tiny DSL for low-fidelity UI mockups.

This skill is the canonical spec and operating guide.

## Bootstrap

If the project does not already have `wirecup` and `wirecup.css`, fetch them:

```bash
curl -fsSL https://raw.githubusercontent.com/ruibeard/wirecup/main/install.sh | bash
```

## Workflow

Run the preview server:

```bash
./wirecup .
```

What it does:

- watches `/.wirecup/*.cup`
- opens the browser
- serves the current mock at `/`
- hot reloads when `.cup` files or `wirecup.css` change
- uses routes instead of `.html` files

Where to write mocks:

```bash
.wirecup/login.cup
.wirecup/dashboard.cup
.wirecup/product.cup
```

Route behavior:

- the newest edited `.cup` file becomes the default page at `/`
- route `/login` renders `.wirecup/login.cup`
- route `/dashboard` renders `.wirecup/dashboard.cup`
- route `/product` renders `.wirecup/product.cup`

Optional:

```bash
./wirecup . --save
```

That also writes `.html` files next to the `.cup` files.

## Spec

### Core rule

The first non-space character on a line selects the element type.

Everything after that character is the element content.

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
| `s` | select | select/dropdown placeholder |
| `l` | list item | bullet list item |
| `v` | badge | small neutral pill |
| `a` | alert | neutral message box |
| `k` | checkbox | checkbox row |
| `u` | include | reusable snippet or built-in helper |
| `c` | card | container for indented children |
| `r` | row | horizontal flex group for indented children |
| `g` | grid | table-like block |
| `-` | divider | thin divider |
| `=` | divider | thick divider |

### Text elements

`h`, `t`, `v`, `a`, `k`, `x`, and `s` render exactly the text you provide.

### Input

`i` renders an input placeholder box.

An empty `i` renders a blank placeholder line.

### Buttons and nav links

`n` and `b` support `label|target` links.

Target resolution rules:

- `http*` stays unchanged
- `/route` stays unchanged
- `target.cup` becomes `/target`
- `target` becomes `/target`
- if there is no `|target`, the item is non-navigating

### Includes

`u` expands a reusable snippet.

Built-in:

- `u ballot-nav current-route`

This renders the shared ballot navigation and leaves the current route non-clickable.

Custom snippets:

- create `.wirecup/_includes/name.cup`
- reference it with `u name arg1 arg2`
- use `$1`, `$2`, and `$*` inside the include file

### Lists

Consecutive `l` lines are grouped into one list.

### Dividers

Use `-` for a thin divider and `=` for a thick divider.

### Containers and indentation

`c`, `r`, and `g` take indented child lines.

Indentation defines structure.

Children continue until indentation returns to the parent level.

### Grid

`g` creates a table-like layout.

The `g` line is the header row.

Indented lines under it are body rows.

Cells are split by 2 or more spaces.

Grid cell rules:

- cells starting with `v ` render as badges
- cells starting with `b ` render as buttons
- other cell text renders as plain text
- cells may be separated by tabs or by 2 or more spaces

### Compact mode

For lower token usage:

- omit the space after the element character, for example `hTitle`
- use minimal indentation, for example one space per level
- prefer tabs in `g` header and row cells

### Alerts and badges

Badges and alerts are neutral sketch elements.

They do not carry semantic color meaning in the spec.

### Error rule

Unknown element characters are invalid.

If a line starts with an unsupported first character, that is a spec error.

Examples belong in `examples/`, not in this skill.
