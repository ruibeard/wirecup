# Wirecup

A tiny `.cup` language for low-fidelity UI mocks. Agents write text. The server draws it. Nobody writes HTML.

## This machine

Repo: `/Users/ruibeard/code/wirecup`

```bash
/Users/ruibeard/code/wirecup/dist/wirecup .
```

Opens http://localhost:8765 and reloads when `.wirecup/*.cup` changes.

Agents: read `AGENTS.md`, then the skill.

## Commands

```bash
./dist/wirecup .              # watch and preview
./dist/wirecup file.cup       # render one file to HTML
./dist/wirecup --web file.cup # one-off browser preview
./dist/wirecup . -p 9000      # custom port
```

## Cheat sheet

One character starts the line:

```
h Heading
t Paragraph text
i Input field
b Button
n Navigation link
x Image placeholder
s Select placeholder
l List item
v Badge
a Alert box
k Checkbox
c Card (indent children)
r Row (indent children)
g Grid (indent rows)
- Thin divider
= Thick divider
```

Full rules are in the skill, not here.

## License

MIT. macOS arm64.
