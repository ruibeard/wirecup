# Pen Format Spec v1

> The most token-efficient mockup language. Designed for LLMs/agents to sketch UI like pen-on-paper.

## Philosophy
- **1 char** = element type
- **No quotes, no brackets, no closing tags**
- **Visual by default** — reads like ASCII wireframes
- **Whitespace is the only layout engine**

---

## Element Types (1 letter)

| Char | Element | Render |
|------|---------|--------|
| `b` | button | [ Label ] |
| `i` | input | [________] |
| `t` | text / label | plain text |
| `h` | heading | **BOLD TEXT** |
| `x` | image / placeholder | [////] |
| `c` | card / container box | draws border around indented block |
| `n` | nav / menu | horizontal row of links |
| `s` | select / dropdown | [ v Option ] |
| `l` | list item | • text |
| `r` | row (group) | flex row of children |
| `g` | grid / table | data table with header row |
| `v` | badge / tag | status pill |
| `a` | alert / banner | notification bar |
| `k` | checkbox | [ ] label |
| `-` | divider line | ─────────── |
| `=` | thick divider | ═══════════ |

---

## Syntax Rules

### 1. Basic Line
```
<t> <content>
```
First non-whitespace char is the type. Rest is content.

### 2. Indentation = Nesting
Indented lines go INSIDE the previous unindented element (usually `c` card).

### 3. Implicit Row
Multiple elements on same line separated by `  ` (2+ spaces) render side-by-side.

### 4. Container Block
`c` starts a bordered card. All indented lines after it go inside.

---

## Examples

### Minimal Login (27 tokens)
```
n Home  About  Contact
-
h Login
t Email
i
t Password
i
b Submit
```

### Dashboard Card (35 tokens)
```
c
  x
  h Revenue
  t $12,400
  b View
```

### Complex Page
```
n Logo  Dashboard  Settings  Profile
=
c
  h Welcome Back
  t Here's what's happening
  r
    c
      x
      h Users
      t 1,204
    c
      x
      h Sales
      t $42K
-
l New order #1024
l User signed up
```

---

## Compact Mode (even fewer tokens)

Drop the space after type char when unambiguous:

```
hLogin
tEmail
i
i
bSubmit
```

This is valid. The parser reads first char as type, remainder as content.

---

## Output

Render to:
- **HTML** — viewable mockups with wireframe CSS
- **SVG** — scalable vector (optional)
- **ANSI** — terminal view

---

## Design Constraints

1. **Never nest deeper than 2 levels** (keeps it sketchy)
2. **Prefer 3-12 lines per component**
3. **Use `x` generously** — nobody draws every detail on paper
4. **Skip labels on inputs** — placeholder text is enough for sketches
5. **Single-word buttons** — sketches don't need "Click here to"
