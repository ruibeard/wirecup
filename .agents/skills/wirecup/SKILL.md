# Skill: wirecup

Wirecup is a tiny DSL for low-fidelity UI mockups.

This skill is the canonical spec and operating guide.

## Bootstrap

If the project does not already have `wirecuprender` and `wirecup.css`, fetch them:

```bash
mkdir -p .agents/.cup
curl -L https://raw.githubusercontent.com/ruibeard/wirecup/main/wirecuprender -o wirecuprender
curl -L https://raw.githubusercontent.com/ruibeard/wirecup/main/wirecup.css -o wirecup.css
chmod +x wirecuprender
```

## Workflow

Run the preview server:

```bash
python3 wirecuprender
```

What it does:

- watches `.agents/.cup/*.cup`
- opens the browser
- serves the current mock at `/`
- hot reloads when `.cup` files or `wirecup.css` change
- uses routes instead of `.html` files

Where to write mocks:

```bash
.agents/.cup/login.cup
.agents/.cup/dashboard.cup
.agents/.cup/product.cup
```

Route behavior:

- the newest edited `.cup` file becomes the default page at `/`
- route `/login` renders `.agents/.cup/login.cup`
- route `/dashboard` renders `.agents/.cup/dashboard.cup`
- route `/product` renders `.agents/.cup/product.cup`

Optional:

```bash
python3 wirecuprender --save
```

That also writes `.html` files next to the `.cup` files.

## Spec

### Core rule

The first non-space character on a line selects the element type.

Everything after that character is the element content.

Examples:

```text
h Login
t Email
b Sign In|dashboard
```

The space after the type character is optional.

These are valid too:

```text
hLogin
tEmail
bSign In|dashboard
```

### Elements

| Char | Element | Meaning | Example |
|------|---------|---------|---------|
| `n` | nav | horizontal navigation row | `n Login|login Dashboard|dashboard` |
| `h` | heading | section heading | `h Account Settings` |
| `t` | text | paragraph or label text | `t Work email` |
| `i` | input | input placeholder box | `i name@company.com` |
| `b` | button | button or linked button | `b Save|settings` |
| `x` | image | image/chart/media placeholder | `x Product Image` |
| `s` | select | select/dropdown placeholder | `s Pro Annual` |
| `l` | list item | bullet list item | `l New designer invited` |
| `v` | badge | small neutral pill | `v Draft` |
| `a` | alert | neutral message box | `a Heads up: Billing address missing` |
| `k` | checkbox | checkbox row | `k Keep me signed in` |
| `c` | card | container for indented children | `c` |
| `r` | row | horizontal flex group for indented children | `r` |
| `g` | grid | table-like block | `g Name  Status  Action` |
| `-` | divider | thin divider | `-` |
| `=` | divider | thick divider | `=` |

### Text elements

`h`, `t`, `v`, `a`, `k`, `x`, and `s` render exactly the text you provide.

Examples:

```text
h Team Dashboard
t Quick view of work and blockers.
v Draft
a Heads up: Billing address missing
k Enable weekly summary emails
x Team Avatar
s Pro Annual
```

### Input

`i` renders an input placeholder box.

Examples:

```text
i name@company.com
i ********
i
```

An empty `i` renders a blank placeholder line.

### Buttons and nav links

`n` and `b` support `label|target` links.

Examples:

```text
n Login|login Dashboard|dashboard Docs|https://example.com/docs
b Sign In|dashboard
b Open Product|product
```

Target resolution rules:

- `http*` stays unchanged
- `/route` stays unchanged
- `target.cup` becomes `/target`
- `target` becomes `/target`
- if there is no `|target`, the item is non-navigating

Examples:

```text
b Save|settings
```

becomes a link to `/settings`

```text
n Product|product.cup
```

becomes a link to `/product`

### Lists

Consecutive `l` lines are grouped into one list.

Example:

```text
l Alice uploaded the Q2 deck
l Vendor contract waiting on signature
l New bug report assigned to Platform
```

### Dividers

Use `-` for a thin divider and `=` for a thick divider.

Example:

```text
-
=
```

### Containers and indentation

`c`, `r`, and `g` take indented child lines.

Indentation defines structure.

Children continue until indentation returns to the parent level.

Example card:

```text
c
  h Workspace Profile
  t Name
  i Acme Studio
  b Save|settings
```

Example row:

```text
r
  c
    h Open Tasks
    t 14
  c
    h Team Note
    a Sprint review moved to Thursday afternoon.
```

### Grid

`g` creates a table-like layout.

The `g` line is the header row.

Indented lines under it are body rows.

Cells are split by 2 or more spaces.

Example:

```text
g Area  Owner  Action
  Design System  Maya  b Open|design-system
  Billing  Arun  b Review|billing
  Website  Lena  b View|website
```

Grid cell rules:

- cells starting with `v ` render as badges
- cells starting with `b ` render as buttons
- other cell text renders as plain text

Example:

```text
g Name  Status  Action
  Billing  v Needs Review  b Review|billing
  Domain  v Live  b Open|domain
```

### Alerts and badges

Badges and alerts are neutral sketch elements.

They do not carry semantic color meaning in the spec.

These are valid because of the text, not because of special color behavior:

```text
v Draft
v Needs Review
a Heads up: Billing address still needs review.
```

### Error rule

Unknown element characters are invalid.

If a line starts with an unsupported first character, that is a spec error.

## Examples

### Login

```text
n Wirecup
=
h Sign In
t Work email
i name@company.com
t Password
i ********
k Keep me signed in
b Sign In|dashboard
t Forgot your password?
```

### Dashboard

```text
n Overview  Dashboard  Products|product  Settings
=
h Team Dashboard
t Quick view of work, notes, and open items.
r
  c
    h Open Tasks
    t 14
    b View Queue|tasks
  c
    h Team Note
    a Sprint review moved to Thursday afternoon.
  c
    h Release Status
    v Draft
    t Mobile app cut planned for Friday.
-
h Activity
l Alice uploaded the Q2 deck
l New bug report assigned to Platform
l Vendor contract waiting on signature
```

### Product

```text
n Dashboard|dashboard  Catalog  Cart|cart
=
h Vintage Camera
t Internal product page for a hardware listing.
r
  c
    x Product Image
  c
    t Price
    i $299
    t Condition
    s Excellent
    v In Stock
    b Add to Cart|cart
```
