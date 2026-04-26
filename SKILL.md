---
name: wirecup
description: Use for creating, editing, reviewing, or rendering Wirecup .cup UI wireframes.
---

# Wirecup

Source/download: https://github.com/ruibeard/wirecup

Compact `.cup` DSL for low-fidelity UI wireframes.

Workflow:

```bash
python3 wirecuprender input.cup
```

This renders HTML, starts hot reload, opens the browser, and uses Tailwind CDN utilities.

## Elements

| Char | Element | Form |
|------|---------|------|
| `n` | nav | `n Home About` |
| `h` | heading | `h Login` |
| `t` | text | `t Email` |
| `i` | input | `i Work email` |
| `b` | button | `b Submit|target` |
| `x` | image | `x Chart` |
| `s` | select | `s Status` |
| `l` | list item | `l Item` |
| `v` | badge | `v Active` |
| `a` | alert | `a Success` |
| `k` | checkbox | `k Remember me` |
| `c` | card | indented children |
| `r` | row | indented children |
| `g` | grid | header + indented rows |
| `-` | divider | `-` |
| `=` | thick divider | `=` |

## Rules

- first non-space char selects element
- content follows element char
- compact form works: `hLogin`
- indentation creates children for `c`, `r`, `g`
- unknown elements error

## Links

```text
b Button|target
n Home|index Docs|docs.cup
```

- `http*` stays as-is
- `*.cup` becomes `.html`
- targets with `.` stay as-is
- other targets get `.html`
- `target.cup` becomes `target.html`

## Grid

Cells split on `2+` spaces.

```text
g Name  Status  Action
  Alice  v Active  b Open|alice
  Bob    v Pending b Review|bob
```

## Example

```text
n Home Dashboard Settings
=
h Dashboard
r
  c
    h Users
    t 1,204
  c
    h Sales
    t $42K
-
l New order
l User signed up
```

## Run

```bash
python3 wirecuprender input.cup
```
