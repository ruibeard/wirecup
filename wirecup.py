#!/usr/bin/env python3

import argparse
import html
import http.server
import json
import os
import re
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


APP_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
PROJECT_ROOT = Path.cwd()
CUP_DIR = PROJECT_ROOT / ".wirecup"
INCLUDE_DIR = CUP_DIR / "_includes"

LINK_PREFIX = "/"
LINK_SUFFIX = ""
NAV_PREFIX = "/"
NAV_SUFFIX = ""


def support_css_path() -> Path:
    project_css = PROJECT_ROOT / "wirecup.css"
    if project_css.exists():
        return project_css
    return APP_ROOT / "wirecup.css"


def set_project_root(path: Path) -> None:
    global PROJECT_ROOT, CUP_DIR, INCLUDE_DIR
    PROJECT_ROOT = path.expanduser().resolve()
    CUP_DIR = PROJECT_ROOT / ".wirecup"
    INCLUDE_DIR = CUP_DIR / "_includes"


def page_wrap(support_css: str, inner: str, title: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script>
tailwind.config = {{
  theme: {{
    extend: {{
      fontFamily: {{
        balsamiq: ["Balsamiq Sans", "Comic Sans MS", "cursive"],
      }},
    }},
  }},
}};
</script>
<script src="https://cdn.tailwindcss.com"></script>
<style>
{support_css}
</style>
</head>
<body class="min-h-screen p-8 md:p-12 font-balsamiq bg-stone-100">
<div class="page mx-auto bg-stone-50 p-8 border-2 border-stone-300 shadow-lg max-w-[900px] sketchy-page">
{inner}
</div>
</body>
</html>"""


def parse_link(content: str, prefix: str | None = None, suffix: str | None = None) -> tuple[str, str]:
    if "|" not in content:
        return content.strip(), ""
    label, target = (part.strip() for part in content.split("|", 1))
    if not target:
        return label, ""
    if target.startswith("http"):
        return label, target
    if target.startswith("/"):
        return label, target
    if target.endswith(".cup"):
        target = target[:-4]
    p = prefix if prefix is not None else LINK_PREFIX
    s = suffix if suffix is not None else LINK_SUFFIX
    return label, p + target.strip("/") + s


def el_nav(content: str) -> str:
    items = []
    for item in content.split():
        label, href = parse_link(item, NAV_PREFIX, NAV_SUFFIX)
        if href:
            items.append(f'<a href="{href}" class="hover:underline text-stone-800">{label}</a>')
        else:
            items.append(f'<span class="text-stone-800">{label}</span>')
    return f'<nav class="flex gap-6 pb-2 mb-4 border-b-2 border-stone-500 text-[0.95em]">{"".join(items)}</nav>'


def el_heading(content: str) -> str:
    return f'<h2 class="text-[1.6em] font-bold my-3 tracking-tight text-stone-800">{content}</h2>'


def el_text(content: str) -> str:
    return f'<p class="my-1.5 text-[0.95em] text-stone-600">{content}</p>'


def el_input(content: str) -> str:
    placeholder = content.strip() or "________"
    return f'<div class="inline-block min-w-[200px] my-1.5 p-2.5 border-2 border-stone-500 rounded bg-neutral-50 text-stone-400 italic">{placeholder}</div>'


def el_button(content: str) -> str:
    label, href = parse_link(content, LINK_PREFIX, LINK_SUFFIX)
    label = label or "OK"
    classes = "inline-block my-2 px-5 py-2 border-2 border-stone-700 rounded-md bg-stone-200 cursor-default shadow-sm text-stone-800 no-underline"
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
    width = "3px" if thick else "2px"
    color = "stone-500" if thick else "stone-400"
    return f'<hr class="my-3 border-0 border-t-[{width}] border-{color} sketchy-divider">'


def el_badge(content: str) -> str:
    return f'<span class="inline-block my-0.5 mx-1 px-3 py-0.5 text-[0.8em] font-bold rounded-xl border-2 bg-stone-100 border-stone-400 text-stone-600">{content.strip()}</span>'


def el_alert(content: str) -> str:
    return f'<div class="my-2.5 p-4 rounded-md border-2 text-[0.95em] bg-stone-100 border-stone-400 text-stone-700">{content.strip()}</div>'


def el_checkbox(content: str) -> str:
    return f'<label class="flex items-center gap-2 my-1.5 text-[0.95em] text-stone-800"><span class="inline-block w-[18px] h-[18px] border-2 border-stone-600 rounded-[3px] shrink-0"></span><span>{content.strip()}</span></label>'


def split_cells(line: str) -> list[str]:
    return [part.strip() for part in re.split(r"\t+|  +", line.strip()) if part.strip()]


def resolve_include(content: str) -> list[str]:
    parts = content.split()
    if not parts:
        raise ValueError("Include line must specify a snippet name")
    name = parts[0]
    args = parts[1:]

    include_path = INCLUDE_DIR / f"{name}.cup"
    if not include_path.exists():
        raise ValueError(f"Unknown Wirecup include {name!r}")

    template = include_path.read_text()
    replacements = {"$*": " ".join(args)}
    replacements.update({f"${index}": arg for index, arg in enumerate(args, start=1)})
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template.splitlines()


def render_table(header_line: str, rows: list[str]) -> str:
    headers = split_cells(header_line)
    head = "".join(f'<th class="px-3 py-2 border-2 border-stone-500 text-left bg-stone-200 font-bold">{cell}</th>' for cell in headers)
    body = []
    for index, row in enumerate(rows):
        bg = "bg-stone-50" if index % 2 else ""
        cells = []
        for cell in split_cells(row):
            if cell.startswith("v "):
                inner = el_badge(cell[2:])
            elif cell.startswith("b "):
                inner = el_button(cell[2:])
            else:
                inner = cell
            cells.append(f'<td class="px-3 py-2 border-2 border-stone-500 {bg}">{inner}</td>')
        body.append(f'<tr>{"".join(cells)}</tr>')
    return f'<div class="my-2.5 overflow-x-auto"><table class="w-full border-collapse text-[0.9em]"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def parse_line(line: str) -> tuple[str, str] | None:
    stripped = line.lstrip()
    if not stripped:
        return None
    if stripped == "-":
        return "-", ""
    if stripped == "=":
        return "=", ""
    return stripped[0], stripped[1:].lstrip()


def indent_level(line: str) -> int:
    return len(line) - len(line.lstrip())


def collect_children(lines: list[str], index: int, level: int) -> tuple[list[str], int]:
    children = []
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if indent_level(line) <= level:
            break
        children.append(line)
        index += 1
    return children, index


def render(lines: list[str], support_css: str, title: str) -> str:
    simple = {
        "n": el_nav,
        "h": el_heading,
        "t": el_text,
        "i": el_input,
        "b": el_button,
        "x": el_image,
        "s": el_select,
        "v": el_badge,
        "a": el_alert,
        "k": el_checkbox,
        "-": lambda _: el_divider(),
        "=": lambda _: el_divider(thick=True),
    }

    def render_lines(block_lines: list[str], start: int = 0) -> tuple[str, int]:
        parts = []
        list_items = []
        index = start

        def flush_list():
            if list_items:
                parts.append(f'<ul class="my-2 pl-5 list-disc">{"".join(list_items)}</ul>')
                list_items.clear()

        while index < len(block_lines):
            raw = block_lines[index]
            index += 1
            parsed = parse_line(raw)
            if not parsed:
                continue
            kind, content = parsed
            level = indent_level(raw)

            if kind == "l":
                list_items.append(el_list(content))
            elif kind in simple:
                flush_list()
                parts.append(simple[kind](content))
            elif kind == "u":
                flush_list()
                include_lines = resolve_include(content)
                inner, _ = render_lines(include_lines, 0)
                parts.append(inner)
            elif kind in {"c", "r", "g"}:
                flush_list()
                children, index = collect_children(block_lines, index, level)
                if kind == "g":
                    parts.append(render_table(content, children))
                else:
                    inner, _ = render_lines(children, 0)
                    if kind == "c":
                        parts.append(f'<div class="card my-3 p-4 border-2 border-stone-500 rounded-md bg-stone-50 sketchy-card">{inner}</div>')
                    else:
                        parts.append(f'<div class="flex gap-4 items-start flex-wrap">{inner}</div>')
            else:
                raise ValueError(f"Unknown Wirecup element type {kind!r}: {raw.lstrip()}")

        flush_list()
        return "\n".join(parts), index

    inner, _ = render_lines(lines)
    return page_wrap(support_css, inner, title)


RELOAD_SCRIPT = """
<script>
(function(){
  const eventSource = new EventSource('/__wirecup_events');
  eventSource.onmessage = () => location.reload();
  eventSource.onerror = () => eventSource.close();
})();
</script>
"""


IFRAME_NAV_SCRIPT = """
<script>
(function(){
  if (window.parent === window) return;
  document.addEventListener("click", function(event) {
    const link = event.target.closest("a");
    if (!link) return;
    const href = link.getAttribute("href");
    if (href && href.startsWith("/render/")) {
      event.preventDefault();
      window.parent.location.href = "/__wirecup?file=" + encodeURIComponent(href.slice("/render/".length));
    }
  });
})();
</script>
"""


def quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="/")


def token_count(content: str) -> int:
    return (len(content) + 3) // 4


def file_label(file: str) -> str:
    return Path(file).with_suffix("").name


def relative_cup_files() -> list[str]:
    if not CUP_DIR.exists():
        return []
    files = []
    for path in CUP_DIR.rglob("*.cup"):
        relative = path.relative_to(CUP_DIR)
        if "_includes" in relative.parts:
            continue
        files.append(relative.as_posix())
    return sorted(files)


def selected_file(query: str = "") -> str | None:
    files = relative_cup_files()
    requested = urllib.parse.parse_qs(query).get("file", [None])[0]
    if requested in files:
        return requested
    latest = current_cup()
    if latest is not None:
        latest_relative = latest.relative_to(CUP_DIR).as_posix()
        if latest_relative in files:
            return latest_relative
    return files[0] if files else None


def safe_cup_path(file: str) -> Path | None:
    if not file.endswith(".cup"):
        return None
    candidate = (CUP_DIR / file).resolve()
    root = CUP_DIR.resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return None
    if "_includes" in relative.parts:
        return None
    return candidate if candidate.is_file() else None


def preview_shell(query: str = "") -> str:
    files = relative_cup_files()
    selected = selected_file(query)
    rows = []
    for file in files:
        path = CUP_DIR / file
        count = token_count(path.read_text())
        active = file == selected
        item_class = "border-stone-600 bg-yellow-50" if active else "border-transparent bg-stone-50 hover:border-stone-300"
        href = "/__wirecup?file=" + urllib.parse.quote(file)
        preview_href = "/render/" + quote_path(file)
        rows.append(f"""
<a class="flex items-center justify-between p-2 rounded-lg border-2 no-underline text-inherit {item_class}" href="{href}">
  <div class="flex flex-col min-w-0">
    <span class="text-sm font-medium truncate">{html.escape(file_label(file))}</span>
    <span class="text-[10px] text-stone-400">{count} tokens</span>
  </div>
  <span class="ml-2 text-stone-500 hover:text-stone-700 shrink-0" onclick="event.preventDefault(); event.stopPropagation(); window.open('{preview_href}', '_blank');" role="button" aria-label="Open {html.escape(file)}">
    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
      <polyline points="15 3 21 3 21 9"/>
      <line x1="10" y1="14" x2="21" y2="3"/>
    </svg>
  </span>
</a>""")

    if not rows:
        rows.append('<p class="text-sm text-stone-500">No .cup files found</p>')

    if selected:
        preview_url = "/render/" + quote_path(selected)
        selected_count = token_count((CUP_DIR / selected).read_text())
        main = f"""
<span class="absolute top-4 left-4 z-10 text-xs text-stone-500 bg-stone-100 px-2 py-1 rounded">{selected_count} tokens</span>
<iframe src="{preview_url}" class="w-full h-full border-0"></iframe>"""
    else:
        main = f"""
<div class="p-8">
  <h2 class="text-xl font-semibold">No previews available</h2>
  <p class="mt-2 text-stone-500">Create a <code class="text-sm bg-stone-200 px-1 rounded">.cup</code> file in <code class="text-sm bg-stone-200 px-1 rounded">{html.escape(str(CUP_DIR))}</code> and refresh this page.</p>
</div>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wirecup</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Balsamiq+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
<style>body {{ font-family: 'Balsamiq Sans', sans-serif; }}</style>
</head>
<body class="m-0 bg-stone-100 text-stone-800">
<div class="flex h-screen">
  <aside class="w-52 h-full overflow-y-auto border-r-2 border-stone-300 bg-stone-200 p-3 flex flex-col">
    <h1 class="text-lg font-semibold mb-3 text-stone-700">Wirecup</h1>
    <div class="space-y-1 flex-1">{"".join(rows)}</div>
    <div class="pt-4 border-t border-stone-300">
      <span class="text-xs text-stone-500">{html.escape(str(PROJECT_ROOT))}</span>
    </div>
  </aside>
  <main class="flex-1 flex flex-col relative min-w-0">{main}</main>
</div>
{RELOAD_SCRIPT}
</body>
</html>"""


class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    html: str = ""
    cup_name: str = ""
    current_route: str = "/"
    reload_time: float = 0.0
    sse_clients: list = []

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        if path == "/__wirecup_events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            LiveReloadHandler.sse_clients.append(self.wfile)
            try:
                while True:
                    time.sleep(1)
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                LiveReloadHandler.sse_clients.remove(self.wfile)
            return
        if path.startswith("/__wirecup_reload"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"t": self.reload_time}).encode())
            return
        if path == "/__wirecup_current":
            body = json.dumps({"file": self.cup_name, "route": self.current_route, "t": self.reload_time}).encode()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/__wirecup":
            body = preview_shell(parsed.query).encode()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path.startswith("/render/"):
            file = urllib.parse.unquote(path.removeprefix("/render/"))
            cup_path = safe_cup_path(file)
            if cup_path is None:
                self.send_error(404, "Wirecup file not found")
                return
            body = render_cup_file(cup_path).encode()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path.startswith("/") and path.count("/") == 1 and "." not in path.strip("/"):
            # If it's "/" show the preview shell, otherwise show the route preview
            if path == "/":
                body = preview_shell().encode()
            else:
                LiveReloadHandler.current_route = path
                rebuild_current()
                body = self.html.encode()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def route_name(path: str) -> str:
    name = path.strip("/")
    return name or latest_cup_name() or "wirecup"


def watch_state(*paths: Path) -> tuple[float, ...]:
    return tuple(path.stat().st_mtime for path in paths if path.exists())


def cup_files() -> list[Path]:
    if not CUP_DIR.exists():
        return []
    return sorted((path for path in CUP_DIR.rglob("*.cup") if "_includes" not in path.relative_to(CUP_DIR).parts), key=lambda path: path.stat().st_mtime)


def latest_cup_name() -> str | None:
    cup_path = current_cup()
    return cup_path.stem if cup_path else None


def current_cup() -> Path | None:
    files = cup_files()
    return files[-1] if files else None


def cup_for_route(path: str) -> Path | None:
    route = route_name(path)
    cup_path = CUP_DIR / f"{route}.cup"
    if cup_path.exists():
        return cup_path
    return current_cup()


def with_preview_links() -> tuple[str, str, str, str]:
    global LINK_PREFIX, LINK_SUFFIX, NAV_PREFIX, NAV_SUFFIX
    previous = (LINK_PREFIX, LINK_SUFFIX, NAV_PREFIX, NAV_SUFFIX)
    LINK_PREFIX = "/__wirecup?file="
    LINK_SUFFIX = ".cup"
    NAV_PREFIX = "/render/"
    NAV_SUFFIX = ".cup"
    return previous


def restore_links(previous: tuple[str, str, str, str]) -> None:
    global LINK_PREFIX, LINK_SUFFIX, NAV_PREFIX, NAV_SUFFIX
    LINK_PREFIX, LINK_SUFFIX, NAV_PREFIX, NAV_SUFFIX = previous


def render_cup_file(cup_path: Path) -> str:
    css_path = support_css_path()
    previous = with_preview_links()
    try:
        rendered = render(cup_path.read_text().splitlines(), css_path.read_text(), cup_path.stem)
    finally:
        restore_links(previous)
    return rendered.replace("</body>", IFRAME_NAV_SCRIPT + "\n" + RELOAD_SCRIPT + "\n</body>")


def rebuild_current():
    cup_path = cup_for_route(LiveReloadHandler.current_route)
    if cup_path is None:
        LiveReloadHandler.cup_name = ""
        LiveReloadHandler.html = page_wrap(
            support_css_path().read_text(),
            '<p class="text-stone-600">No .cup files yet. Write one into .wirecup/</p>',
            "wirecup",
        ).replace("</body>", RELOAD_SCRIPT + "\n</body>")
        return
    html = render_cup_file(cup_path)
    LiveReloadHandler.cup_name = cup_path.name
    LiveReloadHandler.html = html


def broadcast_reload():
    """Send reload event to all connected SSE clients"""
    message = b"data: reload\n\n"
    disconnected = []
    for wfile in LiveReloadHandler.sse_clients:
        try:
            wfile.write(message)
            wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            disconnected.append(wfile)
    for wfile in disconnected:
        LiveReloadHandler.sse_clients.remove(wfile)


def dev_server(port: int, save: bool):
    css_path = support_css_path()
    rebuild_event = threading.Event()
    rebuild_event.set()  # Initial rebuild on start
    
    class CupFileWatcher(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            path = Path(event.src_path)
            # Watch .cup files and wirecup.css
            if path.suffix == ".cup" or path.name == "wirecup.css":
                rebuild_event.set()
        
        def on_created(self, event):
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix == ".cup" or path.name == "wirecup.css":
                rebuild_event.set()
    
    def watched_paths() -> list[Path]:
        paths = [css_path]
        paths.extend(cup_files())
        if INCLUDE_DIR.exists():
            paths.extend(sorted(INCLUDE_DIR.glob("*.cup")))
        return paths

    def rebuild():
        rebuild_current()
        cup_path = cup_for_route(LiveReloadHandler.current_route)
        if save and cup_path is not None:
            cup_path.with_suffix(".html").write_text(LiveReloadHandler.html)
        LiveReloadHandler.reload_time = time.time()
        print(f"Reloaded {LiveReloadHandler.cup_name or '.wirecup'}", flush=True)
        sys.stdout.flush()
        broadcast_reload()

    if not CUP_DIR.exists():
        CUP_DIR.mkdir(parents=True, exist_ok=True)
    elif CUP_DIR.is_file():
        raise ValueError(f"{CUP_DIR} exists as a file, not a directory")
    
    LiveReloadHandler.current_route = "/"
    rebuild()
    os.chdir(CUP_DIR)
    server = ReusableTCPServer(("", port), LiveReloadHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = f"http://localhost:{port}/"
    print(url, flush=True)
    sys.stdout.flush()
    
    # Set up watchdog observer
    observer = Observer()
    event_handler = CupFileWatcher()
    
    # Watch .agents/.cup and also watch project root for wirecup.css changes
    observer.schedule(event_handler, str(CUP_DIR), recursive=True)
    observer.schedule(event_handler, str(PROJECT_ROOT), recursive=False)
    observer.start()
    
    # Open browser in a non-blocking thread
    def open_browser():
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        while True:
            # Wait for rebuild event or timeout every 5 seconds
            rebuild_event.wait(timeout=5.0)
            if rebuild_event.is_set():
                rebuild_event.clear()
                rebuild()
    except KeyboardInterrupt:
        observer.stop()
        server.shutdown()
    finally:
        observer.join()



def main():
    parser = argparse.ArgumentParser(description="Wirecup - text-based wireframe renderer", add_help=True)
    parser.add_argument("target", nargs="?", default=".", help="Directory to watch (default: .) or .cup file to render")
    parser.add_argument("--web", action="store_true", help="Open in browser (for .cup files)")
    parser.add_argument("-p", "--port", type=int, default=8765, help="Port for server (default: 8765)")
    args = parser.parse_args()
    
    target = Path(args.target).resolve()
    
    # Auto-detect: is it a directory or a file?
    if target.is_dir():
        # Watch mode
        set_project_root(target)
        dev_server(args.port, save=False)
    elif target.is_file() and target.suffix == ".cup":
        # Render mode
        cup_text = target.read_text()
        css_path = target.parent / "wirecup.css"
        if not css_path.exists():
            css_path = support_css_path()
        support_css = css_path.read_text() if css_path.exists() else ""
        html = render(cup_text.splitlines(), support_css, target.stem)
        
        if args.web:
            # Open in browser temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                f.write(html)
                temp_path = f.name
            webbrowser.open(f"file://{temp_path}")
            input("Press Enter to exit...")
            os.unlink(temp_path)
        else:
            # Write to HTML file
            output_path = target.with_suffix(".html")
            output_path.write_text(html)
            print(f"Rendered {output_path}")
    else:
        print(f"Error: {target} is not a directory or .cup file")
        sys.exit(1)


if __name__ == "__main__":
    main()
