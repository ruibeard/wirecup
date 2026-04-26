# Wirecup Spec

Wirecup is a compact text DSL for sketching UI like pen on paper.

## Philosophy

- `1` leading character defines element type
- no closing tags, quoted attributes, or wrapper syntax
- whitespace and indentation carry most structure
- optimized for fast generation, review, and diffs

## Element Types

| Char | Element | Notes |
|------|---------|-------|
| `b` | button | `b Label` or `b Label|target` |
| `i` | input | content becomes placeholder text |
| `t` | text | plain paragraph text |
| `h` | heading | section heading |
| `x` | image | placeholder box |
| `c` | card | bordered container for indented children |
| `n` | nav | horizontal nav row |
| `s` | select | dropdown placeholder |
| `l` | list item | bullet-style item |
| `r` | row | flex row for indented children |
| `g` | grid | table with header row plus indented rows |
| `v` | badge | status pill |
| `a` | alert | status banner |
| `k` | checkbox | checkbox plus label |
| `-` | divider | thin divider |
| `=` | divider | thick divider |

## Core Syntax

### Basic line

```text
<type> <content>
```

First non-whitespace character is the element type. Remaining text is element content.

### Compact form

The space after the type is optional when the line stays unambiguous.

```text
hLogin
tEmail
iWork email
bSubmit
```

### Indentation

Indented lines belong to the nearest preceding block element that accepts children.

Supported block elements:
- `c` card
- `r` row
- `g` grid

### Cards

`c` starts a bordered container.

```text
c
  h Revenue
  t $12,400
  b View
```

### Rows

Use `r` for horizontal layout.

```text
r
  c
    h Users
    t 1,204
  c
    h Sales
    t $42K
```

Note: general same-line implicit row layout is not currently supported by the renderer. Use `r` explicitly.

### Nav links and button links

Buttons and nav items can append `|target`.

```text
b Submit|login
n Home|index About|about Profile|profile
```

Target resolution:
- `http*` stays unchanged
- `*.cup` becomes `.html`
- targets containing `.` stay unchanged
- everything else gets `.html` appended

Note: nav items are currently split on whitespace, so multi-word nav labels are not supported without renderer changes.

### Grid / table

`g` uses its own line content as the header row. Indented child lines become body rows. Cells are split by `2+` spaces.

```text
g Name  Status  Action
  Alice  v Active  b Open|alice
  Bob    v Pending b Review|bob
```

Within table rows, cells starting with `v ` render as badges and cells starting with `b ` render as buttons.

## Example Screens

### Minimal login

```text
n Home About Contact
-
h Login
i Email
i Password
b Submit|login
```

### Dashboard

```text
n Dashboard Settings Profile
=
c
  h Welcome Back
  t Here's what's happening
  r
    c
      x Chart
      h Users
      t 1,204
    c
      x Chart
      h Sales
      t $42K
-
l New order #1024
l User signed up
```

## Design Guidance

- keep nesting shallow
- prefer `3-12` lines per component or card
- use `x` freely for diagrams, charts, and media placeholders
- keep copy short
- use Wirecup for structure first, polish later

## Rendering

Render a file with:

```bash
python wirecup-render.py input.cup -o output.html
```

Use a built-in theme with:

```bash
python wirecup-render.py input.cup -o output.html -t clean
```

Supported built-in themes:
- `default`
- `dark`
- `clean`

The renderer also accepts an explicit path to a theme JSON file.