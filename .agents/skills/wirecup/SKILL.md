# Skill: wirecup

Write compact `.cup` wireframes. Render them with one command.

## Run

```bash
python3 wirecuprender input.cup
```

This writes `input.html`, serves it, watches `input.cup` and `wirecup.css`, and opens the browser.

## Syntax

| Char | Meaning | Example |
|------|---------|---------|
| `n` | nav | `n Home About` |
| `h` | heading | `h Login` |
| `t` | text | `t Email` |
| `i` | input | `i Work email` |
| `b` | button | `b Submit|dashboard` |
| `x` | image box | `x Chart` |
| `s` | select | `s Status` |
| `l` | list item | `l Item` |
| `v` | badge | `v Active` |
| `a` | alert | `a Warning` |
| `k` | checkbox | `k Remember me` |
| `c` | card | `c` then indented children |
| `r` | row | `r` then indented children |
| `g` | grid | `g Name  Status` then indented rows |
| `-` | divider | `-` |
| `=` | thick divider | `=` |

## Rules

- First non-space character picks the element.
- The space after it is optional: `hLogin` works.
- Indentation creates children for `c`, `r`, and `g`.
- Grid cells split on 2+ spaces.
- In grids, cells starting with `v ` become badges and `b ` become buttons.

## Links

Use `label|target` in `n` and `b`.

- `http*` stays unchanged.
- `*.cup` becomes `.html`.
- Targets with `.` stay unchanged.
- Other targets get `.html`.

## Example

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
