#!/usr/bin/env python3
"""
wirecup-render.py — Render .cup files to HTML wireframes (Tailwind edition)

Usage:
    python wirecup-render.py file.cup           # dev server with live reload
    python wirecup-render.py file.cup --build   # one-off render
    python wirecup-render.py file.cup -o out.html --build
    python wirecup-render.py file.cup --port 8080
"""

import argparse
import http.server
import json
import os
import socketserver
import threading
import time
from pathlib import Path


def load_theme() -> str:
    p = Path(__file__).parent / "theme.css"
    return p.read_text()


def tailwind_config() -> str:
    return """
<script>
tailwind.config = {
  theme: {
    extend: {
      colors: {
        page: 'var(--bg-page)',
        card: 'var(--bg-card)',
        input: 'var(--bg-input)',
        button: 'var(--bg-button)',
        image: 'var(--bg-image)',
        'badge-green': 'var(--bg-badge-green)',
        'badge-amber': 'var(--bg-badge-amber)',
        'badge-red': 'var(--bg-badge-red)',
        'badge-blue': 'var(--bg-badge-blue)',
        'badge-grey': 'var(--bg-badge-grey)',
        'alert-green': 'var(--bg-alert-green)',
        'alert-amber': 'var(--bg-alert-amber)',
        'alert-red': 'var(--bg-alert-red)',
        'alert-blue': 'var(--bg-alert-blue)',
        'table-header': 'var(--bg-table-header)',
        'table-alt': 'var(--bg-table-alt)',
        primary: 'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        muted: 'var(--text-muted)',
        placeholder: 'var(--text-placeholder)',
        'border-page': 'var(--border-page)',
        'border-light': 'var(--border-light)',
        'border-medium': 'var(--border-medium)',
        'border-dark': 'var(--border-dark)',
        'border-card': 'var(--border-card)',
        'border-image': 'var(--border-image)',
      },
      fontFamily: {
        kalam: ["Kalam", "Comic Sans MS", "cursive"],
      },
    },
  },
};
</script>
"""


def css(theme_text: str) -> str:
    return f'<script src="https://cdn.tailwindcss.com"></script>\n{tailwind_config()}\n<style>\n{theme_text}\n</style>'


def page_wrap(theme_text: str, inner: str) -> str:
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{css(theme_text)}
</head>
<body class="min-h-screen p-8 md:p-12 font-kalam bg-page">
<div class="page mx-auto bg-card p-8 border-2 border-border-page shadow-lg max-w-[900px] sketchy-page">
{inner}
</div>
</body>
</html>"""


def parse_link(content: str) -> tuple[str, str]:
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
            items.append(f'<a href="{href}" class="hover:underline text-primary">{label}</a>')
        else:
            items.append(f'<span class="hover:underline cursor-default text-primary">{label}</span>')
    return f'<nav class="flex gap-6 pb-2 mb-4 border-b-2 border-border-medium text-[0.95em]">{"".join(items)}</nav>'


def el_heading(content: str) -> str:
    return f'<h2 class="text-[1.6em] font-bold my-3 tracking-tight text-primary">{content}</h2>'


def el_text(content: str) -> str:
    return f'<p class="my-1.5 text-[0.95em] text-secondary">{content}</p>'


def el_input(content: str) -> str:
    placeholder = content.strip() or "________"
    return f'<div class="inline-block min-w-[200px] my-1.5 p-2.5 border-2 border-border-medium rounded bg-input text-placeholder italic">{placeholder}</div>'


def el_button(content: str) -> str:
    label, href = parse_link(content)
    if not label:
        label = "OK"
    classes = "inline-block my-2 px-5 py-2 border-2 border-border-dark rounded-md bg-button cursor-default shadow-[1px_2px_0_var(--shadow-button)] active:shadow-none active:translate-x-px active:translate-y-0.5 text-primary no-underline"
    if href:
        return f'<a href="{href}" class="{classes}">{label}</a>'
    return f'<button class="{classes}">{label}</button>'


def el_image(content: str) -> str:
    label = content.strip() or "img"
    return f'<div class="flex items-center justify-center my-1.5 min-h-20 min-w-[80px] bg-image border-2 border-border-image text-muted text-[0.8em]" style="border-style:dashed">{label}</div>'


def el_select(content: str) -> str:
    label = content.strip() or "..."
    return f'<div class="relative inline-block my-1.5 pr-7 pl-2.5 py-2 border-2 border-border-medium rounded bg-input">{label}<span class="absolute right-2 top-1/2 -translate-y-1/2">▾</span></div>'


def el_list(content: str) -> str:
    return f'<li class="my-1 pl-4 list-disc text-primary">{content}</li>'


def el_divider(thick: bool = False) -> str:
    w = "3px" if thick else "2px"
    c = "border-card" if thick else "border-light"
    return f'<hr class="my-3 border-0 border-t-[{w}] border-{c} sketchy-divider">'


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
    return f'<span class="inline-block my-0.5 mx-1 px-3 py-0.5 text-[0.8em] font-bold rounded-xl border-2 bg-badge-{color} border-border-badge-{color} text-text-badge-{color}">{content.strip()}</span>'


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
    return f'<div class="my-2.5 p-4 rounded-md border-2 text-[0.95em] bg-alert-{color} border-border-alert-{color} text-text-alert-{color}">{content.strip()}</div>'


def el_checkbox(content: str) -> str:
    return f'<label class="flex items-center gap-2 my-1.5 text-[0.95em] text-primary"><span class="inline-block w-[18px] h-[18px] border-2 border-border-checkbox rounded-[3px] shrink-0"></span><span>{content.strip()}</span></label>'


def split_cells(line: str) -> list[str]:
    import re
    parts = re.split(r"  +", line.strip())
    return [p.strip() for p in parts if p.strip()]


def render_table(header_line: str, rows: list[str]) -> str:
    headers = split_cells(header_line)
    header_html = "".join(f'<th class="px-3 py-2 border-2 border-border-medium text-left bg-table-header font-bold">{h}</th>' for h in headers)
    rows_html = ""
    for idx, row in enumerate(rows):
        cells = split_cells(row)
        bg = "bg-table-alt" if idx % 2 else ""
        cell_html = ""
        for cell in cells:
            cell = cell.strip()
            if cell.startswith("v "):
                cell_html += f'<td class="px-3 py-2 border-2 border-border-medium {bg}">{el_badge(cell[2:])}</td>'
            elif cell.startswith("b "):
                cell_html += f'<td class="px-3 py-2 border-2 border-border-medium {bg}">{el_button(cell[2:])}</td>'
            else:
                cell_html += f'<td class="px-3 py-2 border-2 border-border-medium {bg}">{cell}</td>'
        rows_html += f'<tr>{cell_html}</tr>'
    return f'<div class="my-2.5 overflow-x-auto"><table class="w-full border-collapse text-[0.9em]"><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>'


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


def render(lines: list[str], theme_text: str) -> str:
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
                parts.append(f'<div class="card my-3 p-4 border-2 border-border-card rounded-md bg-card sketchy-card">{inner}</div>')
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
    return page_wrap(theme_text, result)


# ── Live Reload Server ─────────────────────────────────────────────

RELOAD_SCRIPT = """
<script>
(function(){
  let last = 0;
  setInterval(async () => {
    try {
      const r = await fetch('/__wirecup_reload?t=' + Date.now());
      const j = await r.json();
      if (last && j.t !== last) location.reload();
      last = j.t;
    } catch(e) {}
  }, 400);
})();
</script>
"""


class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    reload_time: float = 0.0

    def do_GET(self):
        if self.path.startswith('/__wirecup_reload'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'t': self.reload_time}).encode())
            return
        super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def dev_server(cup_path: Path, out_path: Path, theme_text: str, port: int):
    last_mtime = 0.0

    def rebuild():
        nonlocal last_mtime
        text = cup_path.read_text()
        lines = text.splitlines()
        html = render(lines, theme_text)
        html = html.replace('</body>', RELOAD_SCRIPT + '\n</body>')
        out_path.write_text(html)
        LiveReloadHandler.reload_time = time.time()
        print(f"  Reloaded {out_path.name}")
        last_mtime = cup_path.stat().st_mtime

    rebuild()

    serve_dir = out_path.parent.resolve()
    os.chdir(serve_dir)

    server = socketserver.TCPServer(("", port), LiveReloadHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print(f"\n  Serving at http://localhost:{port}/{out_path.name}")
    print("  Watching for changes... (Ctrl+C to stop)\n")

    try:
        while True:
            time.sleep(0.5)
            current_mtime = cup_path.stat().st_mtime
            if current_mtime != last_mtime:
                rebuild()
    except KeyboardInterrupt:
        server.shutdown()
        print("\nStopped.")


# ── CLI ────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="Render wirecup .cup files to HTML. Default: dev server with live reload."
    )
    p.add_argument("file", help="Input .cup file")
    p.add_argument("-o", "--output", help="Output HTML file name (default: auto)")
    p.add_argument("-b", "--build", action="store_true", help="One-off render, no server")
    p.add_argument("-p", "--port", type=int, default=8765, help="Dev server port (default: 8765)")
    p.add_argument("-d", "--out-dir", help="Base output directory. HTML goes to <dir>/html/")
    args = p.parse_args()

    theme_text = load_theme()
    in_path = Path(args.file)
    stem = in_path.stem

    if args.out_dir:
        base = Path(args.out_dir)
        html_dir = base / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        out_path = html_dir / f"{stem}.html"
    else:
        if args.output:
            out_path = Path(args.output)
        else:
            out_path = in_path.with_suffix(".html")

    if args.build:
        text = in_path.read_text()
        lines = text.splitlines()
        html = render(lines, theme_text)
        out_path.write_text(html)
        print(f"Wrote HTML: {out_path}")
    else:
        dev_server(in_path, out_path, theme_text, args.port)


if __name__ == "__main__":
    main()
