#!/usr/bin/env python3
"""
wirecup-render.py — Render .cup files to HTML wireframes (Tailwind edition)

Usage:
    python wirecup-render.py file.cup [-o out.html] [--theme theme.json] [--out-dir ./dist]

Folder layout when using --out-dir:
    dist/
      html/     <- .html files
      png/      <- put screenshots here
"""

import json
import argparse
from pathlib import Path

# ── Default Theme ──────────────────────────────────────────────────

DEFAULT_THEME = {
    "fonts": {
        "primary": "Kalam",
        "fallback": "Comic Sans MS, cursive, sans-serif",
        "google_url": "https://fonts.googleapis.com/css2?family=Kalam:wght@300;400;700&display=swap"
    },
    "colors": {
        "bg_page": "#f5f5f0",
        "bg_card": "#fffef8",
        "bg_input": "#fafafa",
        "bg_button": "#eee",
        "bg_image": "#e8e8e8",
        "bg_badge_green": "#e6f4ea",
        "bg_badge_amber": "#fef3e8",
        "bg_badge_red": "#fce8e8",
        "bg_badge_blue": "#e8f0fe",
        "bg_badge_grey": "#f1f3f4",
        "bg_alert_green": "#e6f4ea",
        "bg_alert_amber": "#fef3e8",
        "bg_alert_red": "#fce8e8",
        "bg_alert_blue": "#e8f0fe",
        "bg_table_header": "#f0f0e8",
        "bg_table_alt": "#fafaf5",
        "text_primary": "#333",
        "text_secondary": "#555",
        "text_muted": "#999",
        "text_placeholder": "#bbb",
        "text_badge_green": "#137333",
        "text_badge_amber": "#b06000",
        "text_badge_red": "#a50e0e",
        "text_badge_blue": "#174ea6",
        "text_badge_grey": "#5f6368",
        "text_alert_green": "#137333",
        "text_alert_amber": "#b06000",
        "text_alert_red": "#a50e0e",
        "text_alert_blue": "#174ea6",
        "border_page": "#ccc",
        "border_light": "#aaa",
        "border_medium": "#888",
        "border_dark": "#555",
        "border_card": "#777",
        "border_image": "#aaa",
        "border_badge_green": "#34a853",
        "border_badge_amber": "#f9ab00",
        "border_badge_red": "#ea4335",
        "border_badge_blue": "#4285f4",
        "border_badge_grey": "#9aa0a6",
        "border_alert_green": "#34a853",
        "border_alert_amber": "#f9ab00",
        "border_alert_red": "#ea4335",
        "border_alert_blue": "#4285f4",
        "border_checkbox": "#666",
        "shadow": "rgba(0,0,0,0.1)",
        "shadow_button": "#bbb"
    },
    "sketchy": {
        "page_rotation": -0.3,
        "card_rotation": 0.2,
        "card_rotation_alt": -0.1,
        "divider_rotation": -0.1
    },
    "layout": {
        "page_width": "900px",
        "page_padding": "30px",
        "card_padding": "14px",
        "card_margin": "10px 0",
        "card_radius": "6px",
        "button_padding": "8px 18px",
        "button_radius": "6px",
        "input_padding": "8px 10px",
        "input_radius": "4px",
        "image_min_height": "80px",
        "image_border": "dashed",
        "alert_padding": "12px 16px",
        "alert_radius": "6px",
        "badge_padding": "3px 10px",
        "badge_radius": "12px",
        "table_padding": "8px 12px"
    }
}


def load_theme(path: str | None) -> dict:
    if not path:
        return DEFAULT_THEME
    p = Path(path)
    if not p.exists():
        p = Path(__file__).parent / "themes" / path
        if not p.exists() and not p.suffix:
            p = p.with_suffix(".json")
        if not p.exists():
            raise FileNotFoundError(f"Theme not found: {path}")
    with open(p, "r") as f:
        user = json.load(f)
    theme = {
        "fonts": {**DEFAULT_THEME["fonts"]},
        "colors": {**DEFAULT_THEME["colors"]},
        "sketchy": {**DEFAULT_THEME["sketchy"]},
        "layout": {**DEFAULT_THEME["layout"]},
    }
    for section in ("fonts", "colors", "sketchy", "layout"):
        if section in user:
            theme[section].update(user[section])
    return theme


# ── CSS Generation (Tailwind + theme vars) ─────────────────────────

def css(theme: dict) -> str:
    c = theme["colors"]
    s = theme["sketchy"]
    f = theme["fonts"]
    vars_css = "\n".join(f"  --{k}: {v};" for k, v in c.items())
    layout_css = "\n".join(f"  --{k}: {v};" for k, v in theme["layout"].items())
    return f"""
<script src="https://cdn.tailwindcss.com"></script>
<style>
@import url('{f['google_url']}');
:root {{
{vars_css}
{layout_css}
}}
body {{ font-family: '{f['primary']}', {f['fallback']}; background: var(--bg_page); }}
.sketchy-page {{ transform: rotate({s['page_rotation']}deg); }}
.sketchy-card {{ transform: rotate({s['card_rotation']}deg); }}
.sketchy-card-alt {{ transform: rotate({s['card_rotation_alt']}deg); }}
.sketchy-divider {{ transform: rotate({s['divider_rotation']}deg); }}
</style>
"""


# ── HTML Helpers ───────────────────────────────────────────────────

def box(tag: str, classes: str, content: str, style: str = "") -> str:
    st = f' style="{style}"' if style else ""
    return f"<{tag} class=\"{classes}\"{st}>{content}</{tag}>"


def page_wrap(theme: dict, inner: str) -> str:
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{css(theme)}
</head>
<body class="min-h-screen p-8 md:p-12">
<div class="page mx-auto bg-[var(--bg-card)] p-[var(--page-padding)] border-2 border-[var(--border-page)] shadow-lg max-w-[var(--page-width)] sketchy-page">
{inner}
</div>
</body>
</html>"""


# ── Element Renderers ──────────────────────────────────────────────

def parse_link(content: str) -> tuple[str, str]:
    """Split content into label + href. Returns (label, href)."""
    if "|" not in content:
        return content.strip(), ""
    label, target = content.split("|", 1)
    label = label.strip()
    target = target.strip()
    if target.startswith("http"):
        href = target
    elif target.endswith(".cup"):
        href = target[:-4] + ".html"
    elif "." in target:
        href = target
    else:
        href = target + ".html"
    return label, href


def el_nav(content: str) -> str:
    items = []
    for x in content.split():
        if not x.strip():
            continue
        label, href = parse_link(x)
        if href:
            items.append(f'<a href="{href}" class="hover:underline text-[var(--text-primary)]">{label}</a>')
        else:
            items.append(f'<span class="hover:underline cursor-default text-[var(--text-primary)]">{label}</span>')
    return f'<nav class="flex gap-6 pb-2 mb-4 border-b-2 border-[var(--border-medium)] text-[0.95em]">{"".join(items)}</nav>'


def el_heading(content: str) -> str:
    return f'<h2 class="text-[1.6em] font-bold my-3 tracking-tight text-[var(--text-primary)]">{content}</h2>'


def el_text(content: str) -> str:
    return f'<p class="my-1.5 text-[0.95em] text-[var(--text-secondary)]">{content}</p>'


def el_input(content: str) -> str:
    placeholder = content.strip() or "________"
    return f'<div class="inline-block min-w-[200px] my-1.5 p-[var(--input-padding)] border-2 border-[var(--border-medium)] rounded-[var(--input-radius)] bg-[var(--bg-input)] text-[var(--text-placeholder)] italic">{placeholder}</div>'


def el_button(content: str) -> str:
    label, href = parse_link(content)
    if not label:
        label = "OK"
    classes = "inline-block my-2 px-[18px] py-[8px] border-2 border-[var(--border-dark)] rounded-[var(--button-radius)] bg-[var(--bg-button)] cursor-default shadow-[1px_2px_0_var(--shadow-button)] active:shadow-none active:translate-x-px active:translate-y-0.5 text-[var(--text-primary)] no-underline"
    if href:
        return f'<a href="{href}" class="{classes}">{label}</a>'
    return f'<button class="{classes}">{label}</button>'


def el_image(content: str) -> str:
    label = content.strip() or "img"
    border_style = "dashed" if "dashed" in str(DEFAULT_THEME["layout"]["image_border"]) else "solid"
    return f'<div class="flex items-center justify-center my-1.5 min-h-[var(--image-min-height)] min-w-[80px] bg-[var(--bg-image)] border-2 border-[var(--border-image)] text-[var(--text-muted)] text-[0.8em]" style="border-style:{border_style}">{label}</div>'


def el_select(content: str) -> str:
    label = content.strip() or "..."
    return f'<div class="relative inline-block my-1.5 pr-7 pl-2.5 py-[8px] border-2 border-[var(--border-medium)] rounded-[var(--input-radius)] bg-[var(--bg-input)]">{label}<span class="absolute right-2 top-1/2 -translate-y-1/2">▾</span></div>'


def el_list(content: str) -> str:
    return f'<li class="my-1 pl-4 list-disc text-[var(--text-primary)]">{content}</li>'


def el_divider(thick: bool = False) -> str:
    w = "3px" if thick else "2px"
    c = "var(--border-card)" if thick else "var(--border-light)"
    return f'<hr class="my-3 border-0 border-t-[{w}] border-[{c}] sketchy-divider">'


def el_badge(content: str) -> str:
    text = content.strip().lower()
    mapping = {
        "badge-green": ("approved confirmed active free available success yes green").split(),
        "badge-amber": ("pending review warning amber yellow wait").split(),
        "badge-red": ("rejected error blocked red no unavailable withdrawn").split(),
        "badge-blue": ("info blue new updated note").split(),
    }
    cls = "badge-grey"
    for k, words in mapping.items():
        if text in words:
            cls = k
            break
    color = cls.replace("badge-", "")
    return f'<span class="inline-block my-0.5 mx-1 px-[10px] py-[3px] text-[0.8em] font-bold rounded-[var(--badge-radius)] border-2 bg-[var(--bg_badge_{color})] border-[var(--border_badge_{color})] text-[var(--text_badge_{color})]">{content.strip()}</span>'


def el_alert(content: str) -> str:
    text = content.strip().lower()
    if any(w in text for w in ("success", "confirmed", "approved", "green")):
        color = "green"
    elif any(w in text for w in ("warning", "pending", "review", "amber", "attention")):
        color = "amber"
    elif any(w in text for w in ("error", "rejected", "failed", "red", "urgent")):
        color = "red"
    else:
        color = "blue"
    return f'<div class="my-2.5 p-[var(--alert-padding)] rounded-[var(--alert-radius)] border-2 text-[0.95em] bg-[var(--bg_alert_{color})] border-[var(--border_alert_{color})] text-[var(--text_alert_{color})]">{content.strip()}</div>'


def el_checkbox(content: str) -> str:
    return f'<label class="flex items-center gap-2 my-1.5 text-[0.95em] text-[var(--text-primary)]"><span class="inline-block w-[18px] h-[18px] border-2 border-[var(--border-checkbox)] rounded-[3px] shrink-0"></span><span>{content.strip()}</span></label>'


# ── Table ──────────────────────────────────────────────────────────

def split_cells(line: str) -> list[str]:
    import re
    parts = re.split(r"  +", line.strip())
    return [p.strip() for p in parts if p.strip()]


def render_table(header_line: str, rows: list[str]) -> str:
    headers = split_cells(header_line)
    header_html = "".join(f'<th class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] text-left bg-[var(--bg_table_header)] font-bold">{h}</th>' for h in headers)
    rows_html = ""
    for idx, row in enumerate(rows):
        cells = split_cells(row)
        bg = "bg-[var(--bg_table_alt)]" if idx % 2 else ""
        cell_html = ""
        for cell in cells:
            cell = cell.strip()
            if cell.startswith("v "):
                cell_html += f'<td class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] {bg}">{el_badge(cell[2:])}</td>'
            elif cell.startswith("b "):
                cell_html += f'<td class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] {bg}">{el_button(cell[2:])}</td>'
            else:
                cell_html += f'<td class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] {bg}">{cell}</td>'
        rows_html += f'<tr>{cell_html}</tr>'
    return f'<div class="my-2.5 overflow-x-auto"><table class="w-full border-collapse text-[0.9em]"><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>'


# ── Parser ─────────────────────────────────────────────────────────

def parse_line(line: str) -> tuple[str, str] | None:
    stripped = line.lstrip()
    if not stripped:
        return None
    if stripped == "-":
        return ("-", "")
    if stripped == "=":
        return ("=", "")
    typ = stripped[0]
    content = stripped[1:].lstrip()
    return (typ, content)


def indent_level(line: str) -> int:
    return len(line) - len(line.lstrip())


def render(lines: list[str], theme: dict) -> str:
    def render_lines(block_lines: list[str], start_idx: int = 0) -> tuple[str, int]:
        parts = []
        local_i = start_idx
        while local_i < len(block_lines):
            raw = block_lines[local_i]
            local_i += 1
            parsed = parse_line(raw)
            if not parsed:
                continue
            typ, content = parsed
            lv = indent_level(raw)

            if typ == "n":
                parts.append(el_nav(content))
            elif typ == "h":
                parts.append(el_heading(content))
            elif typ == "t":
                parts.append(el_text(content))
            elif typ == "i":
                parts.append(el_input(content))
            elif typ == "b":
                parts.append(el_button(content))
            elif typ == "x":
                parts.append(el_image(content))
            elif typ == "s":
                parts.append(el_select(content))
            elif typ == "l":
                parts.append(el_list(content))
            elif typ == "-":
                parts.append(el_divider())
            elif typ == "=":
                parts.append(el_divider(thick=True))
            elif typ == "v":
                parts.append(el_badge(content))
            elif typ == "a":
                parts.append(el_alert(content))
            elif typ == "k":
                parts.append(el_checkbox(content))
            elif typ == "g":
                row_lines = []
                while local_i < len(block_lines):
                    nxt = block_lines[local_i]
                    if nxt.strip() == "":
                        local_i += 1
                        continue
                    if indent_level(nxt) <= lv:
                        break
                    row_lines.append(nxt)
                    local_i += 1
                parts.append(render_table(content, row_lines))
            elif typ == "c":
                child_lines = []
                while local_i < len(block_lines):
                    nxt = block_lines[local_i]
                    if nxt.strip() == "":
                        local_i += 1
                        continue
                    if indent_level(nxt) <= lv:
                        break
                    child_lines.append(nxt)
                    local_i += 1
                inner, _ = render_lines(child_lines, 0)
                parts.append(f'<div class="card my-[var(--card-margin)] p-[var(--card-padding)] border-2 border-[var(--border-card)] rounded-[var(--card-radius)] bg-[var(--bg-card)] sketchy-card">{inner}</div>')
            elif typ == "r":
                child_lines = []
                while local_i < len(block_lines):
                    nxt = block_lines[local_i]
                    if nxt.strip() == "":
                        local_i += 1
                        continue
                    if indent_level(nxt) <= lv:
                        break
                    child_lines.append(nxt)
                    local_i += 1
                inner, _ = render_lines(child_lines, 0)
                parts.append(f'<div class="flex gap-4 items-start flex-wrap">{inner}</div>')
            else:
                parts.append(el_text(raw.lstrip()))
        return "\n".join(parts), local_i

    result, _ = render_lines(lines, 0)
    return page_wrap(theme, result)


# ── CLI ────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Render wirecup .cup files to HTML")
    p.add_argument("file", help="Input .cup file")
    p.add_argument("-o", "--output", help="Output HTML file name (default: auto)")
    p.add_argument("-t", "--theme", help="Theme JSON file (or name in themes/ dir)")
    p.add_argument("-d", "--out-dir", help="Base output directory. HTML goes to <dir>/html/, PNGs to <dir>/png/")
    args = p.parse_args()

    theme = load_theme(args.theme)
    text = Path(args.file).read_text()
    lines = text.splitlines()
    html = render(lines, theme)

    in_path = Path(args.file)
    stem = in_path.stem

    if args.out_dir:
        base = Path(args.out_dir)
        html_dir = base / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        png_dir = base / "png"
        png_dir.mkdir(parents=True, exist_ok=True)
        out_path = html_dir / f"{stem}.html"
    else:
        if args.output:
            out_path = Path(args.output)
        else:
            out_path = in_path.with_suffix(".html")

    out_path.write_text(html)
    print(f"Wrote HTML: {out_path}")
    if args.out_dir:
        print(f"Tip: save screenshots to {png_dir}/{stem}.png")


if __name__ == "__main__":
    main()
