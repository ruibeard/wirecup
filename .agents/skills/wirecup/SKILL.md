# Skill: wirecup

Sketch low-fidelity UI wireframes as token-efficient `.cup` files. Render to standalone HTML for browser viewing.

---

## Quick Start

1.  **Write** a `.cup` file describing the screen.
2.  **Render** it to HTML via CLI.
3.  **Open** the HTML in any browser.

---

## Wirecup Syntax

### Philosophy
- `1` leading character defines the element type.
- No closing tags, quoted attributes, or wrapper syntax.
- Whitespace and indentation carry structure.
- Optimized for fast generation, review, and diffs.

### Element Reference

| Char | Element | Usage |
|------|---------|-------|
| `b` | **button** | `b Label` or `b Label|target` |
| `i` | **input** | `i Placeholder text` (empty becomes `________`) |
| `t` | **text** | `t Any paragraph text` |
| `h` | **heading** | `h Section Title` |
| `x` | **image / placeholder** | `x Chart` or `x` — box for any visual |
| `c` | **card** | Container for indented children |
| `n` | **nav** | Horizontal row: `n Home About Contact` |
| `s` | **select** | Dropdown placeholder |
| `l` | **list item** | Bullet-style item |
| `r` | **row** | Flex row for indented children (horizontal layout) |
| `g` | **grid / table** | Header on own line; indented rows = body cells |
| `v` | **badge** | Status pill: `v Active` |
| `a` | **alert** | Status banner (auto-colored by keywords) |
| `k` | **checkbox** | `k Label text` |
| `-` | **divider** | Thin horizontal line |
| `=` | **divider** | Thick horizontal line |

### Compact Form
The space after the type character is optional when unambiguous:

```text
hLogin
tEmail
iWork email
bSubmit
```

### Indentation & Nesting
Indent children with 2 spaces under block elements (`c`, `r`, `g`). Max 2 indent levels.

**Card:**
```text
c
  h Revenue
  t $12,400
  b View
```

**Row (horizontal layout):**
```text
r
  c
    h Users
    t 1,204
  c
    h Sales
    t $42K
```

**Grid / Table:**
Header on the `g` line. Indented lines become rows. Cells split by **2+ spaces**.
```text
g Name  Status  Action
  Alice  v Active  b Open|alice
  Bob    v Pending b Review|bob
```
- In table rows, cells starting with `v ` render as badges.
- Cells starting with `b ` render as buttons.

### Links
Append `|target` to buttons and nav items:

```text
b Submit|login
n Home|index About|about Profile|profile
```

Target resolution rules:
- `http*` → stays as-is
- `*.cup` → becomes `.html`
- targets with `.` → stay unchanged
- everything else → gets `.html` appended

### Design Constraints
- **5–20 lines per screen** (ideal for one mockup).
- **Max 2 indent levels**.
- Use `x` freely for charts, diagrams, maps, avatars, media.
- Keep copy short.

---

## Examples

### Minimal Login
```text
n Logo
-
h Login
t Email
i
t Password
i
b Sign In|dashboard
t Forgot password?
```

### Dashboard
```text
n Home|index Dashboard|dashboard Settings|settings Profile|profile
=
h Welcome Back
t Here's what's happening today
r
  c
    x
    h Users
    t 1,204
  c
    x
    h Revenue
    t $42K
  c
    x
    h Orders
    t 89
-
l New order #1024 from Alice
l Bob signed up
l Server alert resolved
```

---

## Rendering

Render a `.cup` file to HTML with the Python script:

```bash
python wirecup-render.py input.cup -o output.html
```

If you omit `-o`, the HTML is written next to the input file with the same name and `.html` extension.

---

## Viewing Results

The output HTML is **self-contained** (uses Tailwind CDN + embedded styles). Open it directly in any browser:

```bash
# macOS
open output.html

# Linux
xdg-open output.html

# Or simply double-click the file
```

No build step, no server required.

### Screenshots / Sharing
If you need a PNG for sharing or documentation, open the HTML in a browser and take a screenshot, or use a headless tool:

```bash
# Using Chrome headless
chrome --headless --disable-gpu --screenshot=output.png --window-size=1200,800 file:///path/to/output.html
```

---

## Workflow for LLMs

When a user asks for a wireframe, mockup, or UI screen:

1. **Write** the Wirecup `.cup` content following the syntax and constraints above.
2. **Render** it by running `python wirecup-render.py file.cup`.
3. **Present** the resulting HTML to the user. Tell them to open it in a browser.
4. **Iterate** based on feedback — edit the `.cup` and re-render.

Full formal spec available at: `wirecup-spec.md`
