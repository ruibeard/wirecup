#!/usr/bin/env python3
"""
wirecup-render.py — Render .cup files to HTML wireframes (Tailwind edition)

Usage:
    python wirecup-render.py file.cup
    python wirecup-render.py file.cup --port 8080
"""

import argparse
import http.server
import json
import os
import socketserver
import threading
import time
import webbrowser
from pathlib import Path


def load_support_css() -> str:
    p = Path(__file__).parent / "wirecup.css"
    return p.read_text()


def tailwind_config() -> str:
    return """
<script>
tailwind.config = {
  theme: {
    extend: {
      fontFamily: {
        kalam: ["Kalam", "Comic Sans MS", "cursive"],
      },
    },
  },
};
</script>
"""


def css(support_css: str) -> str:
    return f'{tailwind_config()}\n<script src="https://cdn.tailwindcss.com"></script>\n<style>\n{support_css}\n</style>'


def page_wrap(support_css: str, inner: str, title: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{css(support_css)}
</head>
<body class="min-h-screen p-8 md:p-12 font-kalam bg-stone-100">
<div class="page mx-auto bg-stone-50 p-8 border-2 border-stone-300 shadow-lg max-w-[900px] sketchy-page">
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
            items.append(f'<a href="{href}" class="hover:underline text-stone-800">{label}</a>')
        else:
            items.append(f'<span class="hover:underline cursor-default text-stone-800">{label}</span>')
    return f'<nav class="flex gap-6 pb-2 mb-4 border-b-2 border-stone-500 text-[0.95em]">{"".join(items)}</nav>'


def el_heading(content: str) -> str:
    return f'<h2 class="text-[1.6em] font-bold my-3 tracking-tight text-stone-800">{content}</h2>'


def el_text(content: str) -> str:
    return f'<p class="my-1.5 text-[0.95em] text-stone-600">{content}</p>'


def el_input(content: str) -> str:
    placeholder = content.strip() or "________"
    return f'<div class="inline-block min-w-[200px] my-1.5 p-2.5 border-2 border-stone-500 rounded bg-neutral-50 text-stone-400 italic">{placeholder}</div>'


def el_button(content: str) -> str:
    label, href = parse_link(content)
    if not label:
        label = "OK"
    classes = "inline-block my-2 px-5 py-2 border-2 border-stone-700 rounded-md bg-stone-200 cursor-default shadow-sm active:shadow-none active:translate-x-px active:translate-y-0.5 text-stone-800 no-underline"
    if href:
        return f'<a href="{href}" class="{classes}">{label}</a>'
    return f'<button class="{classes}">{label}</button>'


def el_image(content: str) -> str:
    label = content.strip() or "img"
    return f'<div class="flex items-center justify-center my-1.5 min-h-20 min-w-[80px] bg-stone-200 border-2 border-stone-400 text-stone-400 text-[0.8em]" style="border-style:dashed">{label}</div>'


def el_select(content: str) -> str:
    label = content.strip() or "..."
    return f'<div class="relative inline-block my-1.5 pr-7 pl-2.5 py-2 border-2 border-stone-500 rounded bg-neutral-50">{label}<span class="absolute right-2 top-1/2 -translate-y-1/2">▾</span></div>'


def el_list(content: str) -> str:
    return f'<li class="my-1 pl-4 list-disc text-stone-800">{content}</li>'


def el_divider(thick: bool = False) -> str:
    w = "3px" if thick else "2px"
    c = "stone-500" if thick else "stone-400"
    return f'<hr class="my-3 border-0 border-t-[{w}] border-{c} sketchy-divider">'


def el_badge(content: str) -> str:
    text = content.strip().lower()
    mapping = {
        "badge-green": ("approved confirmed active free available success yes green").split(),
        "badge-amber": ("pending review warning amber yellow wait").split(),
        "badge-red": ("rejected error blocked red no unavailable withdrawn").split(),
        "badge-blue": ("info blue new updated note").split(),
    }
    cls = "grey"
    for k, words in mapping.items():
        if text in words:
            cls = k.replace("badge-", "")
            break
    classes = {
        "green": "bg-green-100 border-green-500 text-green-700",
        "amber": "bg-amber-100 border-amber-500 text-amber-700",
        "red": "bg-red-100 border-red-500 text-red-700",
        "blue": "bg-blue-100 border-blue-500 text-blue-700",
        "grey": "bg-stone-100 border-stone-400 text-stone-600",
    }[cls]
    return f'<span class="inline-block my-0.5 mx-1 px-3 py-0.5 text-[0.8em] font-bold rounded-xl border-2 {classes}">{content.strip()}</span>'


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
    classes = {
        "green": "bg-green-100 border-green-500 text-green-700",
        "amber": "bg-amber-100 border-amber-500 text-amber-700",
        "red": "bg-red-100 border-red-500 text-red-700",
        "blue": "bg-blue-100 border-blue-500 text-blue-700",
    }[color]
    return f'<div class="my-2.5 p-4 rounded-md border-2 text-[0.95em] {classes}">{content.strip()}</div>'


def el_checkbox(content: str) -> str:
    return f'<label class="flex items-center gap-2 my-1.5 text-[0.95em] text-stone-800"><span class="inline-block w-[18px] h-[18px] border-2 border-stone-600 rounded-[3px] shrink-0"></span><span>{content.strip()}</span></label>'


def split_cells(line: str) -> list[str]:
    import re
    parts = re.split(r"  +", line.strip())
    return [p.strip() for p in parts if p.strip()]


def render_table(header_line: str, rows: list[str]) -> str:
    headers = split_cells(header_line)
    header_html = "".join(f'<th class="px-3 py-2 border-2 border-stone-500 text-left bg-stone-200 font-bold">{h}</th>' for h in headers)
    rows_html = ""
    for idx, row in enumerate(rows):
        cells = split_cells(row)
        bg = "bg-stone-50" if idx % 2 else ""
        cell_html = ""
        for cell in cells:
            cell = cell.strip()
            if cell.startswith("v "):
                cell_html += f'<td class="px-3 py-2 border-2 border-stone-500 {bg}">{el_badge(cell[2:])}</td>'
            elif cell.startswith("b "):
                cell_html += f'<td class="px-3 py-2 border-2 border-stone-500 {bg}">{el_button(cell[2:])}</td>'
            else:
                cell_html += f'<td class="px-3 py-2 border-2 border-stone-500 {bg}">{cell}</td>'
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


def render(lines: list[str], support_css: str, title: str = "Wirecup") -> str:
    def render_lines(block_lines: list[str], start_idx: int = 0) -> tuple[str, int]:
        parts = []
        list_items = []
        local_i = start_idx

        def flush_list():
            if list_items:
                parts.append(f'<ul class="my-2 pl-5 list-disc">{"".join(list_items)}</ul>')
                list_items.clear()

        while local_i < len(block_lines):
            raw = block_lines[local_i]
            local_i += 1
            parsed = parse_line(raw)
            if not parsed:
                continue
            typ, content = parsed
            lv = indent_level(raw)

            if typ == "n":
                flush_list()
                parts.append(el_nav(content))
            elif typ == "h":
                flush_list()
                parts.append(el_heading(content))
            elif typ == "t":
                flush_list()
                parts.append(el_text(content))
            elif typ == "i":
                flush_list()
                parts.append(el_input(content))
            elif typ == "b":
                flush_list()
                parts.append(el_button(content))
            elif typ == "x":
                flush_list()
                parts.append(el_image(content))
            elif typ == "s":
                flush_list()
                parts.append(el_select(content))
            elif typ == "l":
                list_items.append(el_list(content))
            elif typ == "-":
                flush_list()
                parts.append(el_divider())
            elif typ == "=":
                flush_list()
                parts.append(el_divider(thick=True))
            elif typ == "v":
                flush_list()
                parts.append(el_badge(content))
            elif typ == "a":
                flush_list()
                parts.append(el_alert(content))
            elif typ == "k":
                flush_list()
                parts.append(el_checkbox(content))
            elif typ == "g":
                flush_list()
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
                flush_list()
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
                parts.append(f'<div class="card my-3 p-4 border-2 border-stone-500 rounded-md bg-stone-50 sketchy-card">{inner}</div>')
            elif typ == "r":
                flush_list()
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
                raise ValueError(f"Unknown Wirecup element type {typ!r}: {raw.lstrip()}")
        flush_list()
        return "\n".join(parts), local_i

    result, _ = render_lines(lines, 0)
    return page_wrap(support_css, result, title)


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


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def dev_server(cup_path: Path, out_path: Path, port: int):
    cup_path = cup_path.resolve()
    out_path = out_path.resolve()
    support_css_path = (Path(__file__).parent / "wirecup.css").resolve()
    last_mtimes = (0.0, 0.0)

    def rebuild():
        nonlocal last_mtimes
        text = cup_path.read_text()
        lines = text.splitlines()
        support_css = support_css_path.read_text()
        html = render(lines, support_css, cup_path.stem)
        html = html.replace('</body>', RELOAD_SCRIPT + '\n</body>')
        out_path.write_text(html)
        LiveReloadHandler.reload_time = time.time()
        print(f"  Reloaded {out_path.name}")
        last_mtimes = (cup_path.stat().st_mtime, support_css_path.stat().st_mtime)

    rebuild()

    serve_dir = out_path.parent.resolve()
    os.chdir(serve_dir)

    server = ReusableTCPServer(("", port), LiveReloadHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://localhost:{port}/{out_path.name}"
    print(f"\n  Serving at {url}")
    print("  Watching for changes... (Ctrl+C to stop)\n")
    webbrowser.open(url)

    try:
        while True:
            time.sleep(0.5)
            current_mtimes = (cup_path.stat().st_mtime, support_css_path.stat().st_mtime)
            if current_mtimes != last_mtimes:
                rebuild()
    except KeyboardInterrupt:
        server.shutdown()
        print("\nStopped.")


# ── CLI ────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="Render, serve, watch, and open a Wirecup .cup file."
    )
    p.add_argument("file", help="Input .cup file")
    p.add_argument("-o", "--output", help="Output HTML file name (default: auto)")
    p.add_argument("-p", "--port", type=int, default=8765, help="Dev server port (default: 8765)")
    p.add_argument("-d", "--out-dir", help="Base output directory. HTML goes to <dir>/html/")
    args = p.parse_args()

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

    dev_server(in_path, out_path, args.port)


if __name__ == "__main__":
    main()
