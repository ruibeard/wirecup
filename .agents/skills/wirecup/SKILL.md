# Skill: wirecup

Write compact `.cup` wireframes. Render them with one command.

## Install In Another Project

Source repo:

`https://github.com/ruibeard/wirecup`

Download these files:

- `https://raw.githubusercontent.com/ruibeard/wirecup/main/wirecuprender`
- `https://raw.githubusercontent.com/ruibeard/wirecup/main/wirecup.css`
- `https://raw.githubusercontent.com/ruibeard/wirecup/main/.agents/skills/wirecup/SKILL.md`

Minimal setup:

```bash
mkdir -p .agents/skills/wirecup
curl -L https://raw.githubusercontent.com/ruibeard/wirecup/main/wirecuprender -o wirecuprender
curl -L https://raw.githubusercontent.com/ruibeard/wirecup/main/wirecup.css -o wirecup.css
curl -L https://raw.githubusercontent.com/ruibeard/wirecup/main/.agents/skills/wirecup/SKILL.md -o .agents/skills/wirecup/SKILL.md
chmod +x wirecuprender
```

If you only want the renderer and not the skill, download just `wirecuprender` and `wirecup.css`.

## Run

```bash
python3 wirecuprender input.cup
```

This serves the rendered page from memory, watches `input.cup` and `wirecup.css`, and opens the browser.

To also save `input.html` next to the source file:

```bash
python3 wirecuprender input.cup --save
```

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
| `v` | badge | `v Draft` |
| `a` | alert | `a Heads up: Billing address missing` |
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
- Badges and alerts are neutral sketch elements, not semantic colors.

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
