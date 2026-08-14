#!/usr/bin/env python3

import argparse, contextlib, errno, html, http.server, json, logging, os, re, socketserver
import sys, threading, time, urllib.parse, urllib.request, webbrowser
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger("wirecup")

APP_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
PROJECT_ROOT = Path.cwd()
CUP_DIR = PROJECT_ROOT / ".wirecup"
INCLUDE_DIR = CUP_DIR / "_includes"
LINK_PREFIX = LINK_SUFFIX = NAV_PREFIX = NAV_SUFFIX = None  # set by preview_links()
FONT_URL = "https://fonts.googleapis.com/css2?family=Balsamiq+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap"

def _css() -> str:
    p = PROJECT_ROOT / "wirecup.css"
    return (p if p.exists() else APP_ROOT / "wirecup.css").read_text()

def page_wrap(css: str, inner: str, title: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="{FONT_URL}" rel="stylesheet">
<style>body{{font-family:'Balsamiq Sans','Comic Sans MS',cursive,sans-serif;}}</style>
<style>{css}</style>
</head>
<body class="min-h-screen p-8 md:p-12 bg-stone-100">
<div class="page mx-auto bg-stone-50 p-8 border-2 border-stone-300 shadow-lg max-w-[900px] sketchy-page">
{inner}
</div>
</body>
</html>"""

def parse_link(content, prefix=None, suffix=None):
    if "|" not in content:
        return content.strip(), ""
    label, target = (p.strip() for p in content.split("|", 1))
    if not target:
        return label, ""
    if target.startswith(("http", "/")):
        return label, target
    if target.endswith(".cup"):
        target = target[:-4]
    p = prefix if prefix is not None else LINK_PREFIX or "/"
    s = suffix if suffix is not None else LINK_SUFFIX or ""
    return label, p + target.strip("/") + s

def el_nav(content):
    def _item(item):
        label, href = parse_link(item, NAV_PREFIX or "/", NAV_SUFFIX or "")
        return f'<a href="{href}" class="hover:underline text-stone-800">{label}</a>' if href else f'<span class="text-stone-800">{label}</span>'
    return f'<nav class="flex gap-6 pb-2 mb-4 border-b-2 border-stone-500 text-[0.95em]">{"".join(_item(i) for i in split_cells(content))}</nav>'

def el_button(content):
    label, href = parse_link(content)
    label = label or "OK"
    cls = "inline-block my-2 px-5 py-2 border-2 border-stone-700 rounded-md bg-stone-200 cursor-default shadow-sm text-stone-800 no-underline"
    return f'<a href="{href}" class="{cls}">{label}</a>' if href else f'<button class="{cls}">{label}</button>'

def el_badge(content):
    return f'<span class="inline-block my-0.5 mx-1 px-3 py-0.5 text-[0.8em] font-bold rounded-xl border-2 bg-stone-100 border-stone-400 text-stone-600">{content.strip()}</span>'

SIMPLE_ELS = {
    "n": el_nav,
    "h": lambda c: f'<h2 class="text-[1.6em] font-bold my-3 tracking-tight text-stone-800">{c}</h2>',
    "t": lambda c: f'<p class="my-1.5 text-[0.95em] text-stone-600">{c}</p>',
    "i": lambda c: f'<div class="inline-block min-w-[200px] my-1.5 p-2.5 border-2 border-stone-500 rounded bg-neutral-50 text-stone-400 italic">{c.strip() or "________"}</div>',
    "b": el_button,
    "x": lambda c: f'<div class="flex items-center justify-center my-1.5 min-h-20 min-w-[80px] bg-stone-200 border-2 border-stone-400 text-stone-400 text-[0.8em]" style="border-style:dashed">{c.strip() or "img"}</div>',
    "s": lambda c: f'<div class="relative inline-block my-1.5 pr-7 pl-2.5 py-2 border-2 border-stone-500 rounded bg-neutral-50">{c.strip() or "..."}<span class="absolute right-2 top-1/2 -translate-y-1/2">▾</span></div>',
    "v": el_badge,
    "a": lambda c: f'<div class="my-2.5 p-4 rounded-md border-2 text-[0.95em] bg-stone-100 border-stone-400 text-stone-700">{c.strip()}</div>',
    "k": lambda c: f'<label class="flex items-center gap-2 my-1.5 text-[0.95em] text-stone-800"><span class="inline-block w-[18px] h-[18px] border-2 border-stone-600 rounded-[3px] shrink-0"></span><span>{c.strip()}</span></label>',
    "-": lambda _: '<hr class="my-3 border-0 border-t-[2px] border-stone-400 sketchy-divider">',
    "=": lambda _: '<hr class="my-3 border-0 border-t-[3px] border-stone-500 sketchy-divider">',
}

def split_cells(line):
    return [p.strip() for p in re.split(r"\t+|  +", line.strip()) if p.strip()]

def resolve_include(content):
    parts = content.split()
    if not parts:
        raise ValueError("Include line must specify a snippet name")
    name, args = parts[0], parts[1:]
    path = INCLUDE_DIR / f"{name}.cup"
    if not path.exists():
        raise ValueError(f"Unknown Wirecup include {name!r}")
    tmpl = path.read_text()
    for k, v in {"$*": " ".join(args), **{f"${i}": a for i, a in enumerate(args, 1)}}.items():
        tmpl = tmpl.replace(k, v)
    return tmpl.splitlines()

CELL_ELS = "vbsik"  # element types allowed inside a grid cell

def render_cell(cell):
    if cell and cell[0] in CELL_ELS and (len(cell) == 1 or cell[1] == " "):
        return SIMPLE_ELS[cell[0]](cell[2:] if len(cell) > 2 else "")
    return cell

def render_table(header_line, rows):
    headers = split_cells(header_line)
    head = "".join(f'<th class="px-3 py-2 border-2 border-stone-500 text-left bg-stone-200 font-bold">{c}</th>' for c in headers)
    body = []
    for i, row in enumerate(rows):
        bg = "bg-stone-50" if i % 2 else ""
        cells = [render_cell(c) for c in split_cells(row)]
        cells += [""] * (len(headers) - len(cells))  # keep every row the full width
        cells = [f'<td class="px-3 py-2 border-2 border-stone-500 {bg}">{c}</td>' for c in cells]
        body.append(f'<tr>{"".join(cells)}</tr>')
    return f'<div class="my-2.5 overflow-x-auto"><table class="w-full border-collapse text-[0.9em]"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'

def indent_level(line):
    return len(line) - len(line.lstrip())

def collect_children(lines, index, level):
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

BLOCK_ELS = "ucrgl"

def validate_cup_file(lines):
    """Check the first character of every element line.

    Lines indented under a `g` are table rows, not elements. They are skipped.
    """
    errors = []
    grid_levels = []
    for i, line in enumerate(lines, 1):
        s = line.lstrip()
        if not s:
            continue
        level = indent_level(line)
        while grid_levels and level <= grid_levels[-1]:
            grid_levels.pop()
        if grid_levels:
            continue
        if s in ("-", "="):
            continue
        kind = s[0]
        if kind == "g":
            grid_levels.append(level)
            continue
        if kind not in SIMPLE_ELS and kind not in BLOCK_ELS:
            errors.append(f"Line {i}: Unknown element type '{kind}'")
    return errors

def render(lines, css, title):
    def render_lines(block):
        parts, list_items = [], []
        def flush():
            if list_items:
                parts.append(f'<ul class="my-2 pl-5 list-disc">{"".join(list_items)}</ul>')
                list_items.clear()
        index = 0
        while index < len(block):
            raw = block[index]; index += 1
            s = raw.lstrip()
            if not s:
                continue
            kind = s[0] if s not in ("-", "=") else s
            content = s[1:].lstrip() if s not in ("-", "=") else ""
            level = indent_level(raw)
            if kind == "l":
                list_items.append(f'<li class="my-1 pl-4 list-disc text-stone-800">{content}</li>')
            elif kind in SIMPLE_ELS:
                flush(); parts.append(SIMPLE_ELS[kind](content))
            elif kind == "u":
                flush(); parts.append(render_lines(resolve_include(content)))
            elif kind in "crg":
                flush()
                children, index = collect_children(block, index, level)
                if kind == "g":
                    parts.append(render_table(content, children))
                else:
                    inner = render_lines(children)
                    parts.append(f'<div class="card my-3 p-4 border-2 border-stone-500 rounded-md bg-stone-50 sketchy-card flex-1 min-w-[240px]">{inner}</div>' if kind == "c" else f'<div class="flex gap-4 items-stretch flex-wrap">{inner}</div>')
            else:
                raise ValueError(f"Unknown Wirecup element type {kind!r}: {s}")
        flush()
        return "\n".join(parts)
    return page_wrap(css, render_lines(lines), title)

RELOAD_SCRIPT = '<script>(function(){const e=new EventSource("/__wirecup_events");e.onmessage=()=>location.reload();e.onerror=()=>e.close();})();</script>'
IFRAME_NAV_SCRIPT = '<script>(function(){if(window.parent===window)return;document.addEventListener("click",function(e){const a=e.target.closest("a");if(!a)return;const h=a.getAttribute("href");if(h&&h.startsWith("/render/")){e.preventDefault();window.parent.location.href="/__wirecup?file="+encodeURIComponent(h.slice(8));}});})();</script>'

def cup_files():
    if not CUP_DIR.exists(): return []
    return sorted((p for p in CUP_DIR.rglob("*.cup") if "_includes" not in p.relative_to(CUP_DIR).parts), key=lambda p: p.stat().st_mtime)

def current_cup():
    f = cup_files(); return f[-1] if f else None

def rel_files():
    return sorted(p.relative_to(CUP_DIR).as_posix() for p in cup_files())

def selected_file(query=""):
    files = rel_files()
    req = urllib.parse.parse_qs(query).get("file", [None])[0]
    if req in files: return req
    c = current_cup()
    if c:
        r = c.relative_to(CUP_DIR).as_posix()
        if r in files: return r
    return files[0] if files else None

def safe_cup_path(file):
    if not file.endswith(".cup"): return None
    candidate = (CUP_DIR / file).resolve()
    try:
        rel = candidate.relative_to(CUP_DIR.resolve())
    except ValueError:
        return None
    return candidate if "_includes" not in rel.parts and candidate.is_file() else None

def cup_for_route(path):
    name = path.strip("/")
    if name:
        c = CUP_DIR / f"{name}.cup"
        if c.exists(): return c
    return current_cup()

@contextlib.contextmanager
def preview_links():
    global LINK_PREFIX, LINK_SUFFIX, NAV_PREFIX, NAV_SUFFIX
    LINK_PREFIX, LINK_SUFFIX, NAV_PREFIX, NAV_SUFFIX = "/__wirecup?file=", ".cup", "/render/", ".cup"
    try: yield
    finally: LINK_PREFIX = LINK_SUFFIX = NAV_PREFIX = NAV_SUFFIX = None

def render_cup_file(cup_path):
    try:
        content = cup_path.read_text()
        lines = content.splitlines()

        errors = validate_cup_file(lines)
        if errors:
            error_msg = "<br>".join(html.escape(e) for e in errors)
            error_html = page_wrap(_css(), f'<div class="p-4 bg-red-50 border-2 border-red-300 rounded text-red-800"><h2 class="font-bold mb-2">Wirecup Error</h2><pre class="text-sm">{error_msg}</pre></div>', cup_path.stem)
            return error_html.replace("</body>", RELOAD_SCRIPT + "</body>")

        with preview_links():
            out = render(lines, _css(), cup_path.stem)
        return out.replace("</body>", IFRAME_NAV_SCRIPT + RELOAD_SCRIPT + "</body>")
    except Exception as e:
        error_html = page_wrap(_css(), f'<div class="p-4 bg-red-50 border-2 border-red-300 rounded text-red-800"><h2 class="font-bold mb-2">Render Error</h2><pre class="text-sm">{html.escape(str(e))}</pre></div>', cup_path.stem)
        return error_html.replace("</body>", RELOAD_SCRIPT + "</body>")

def preview_shell(query=""):
    files = rel_files()
    selected = selected_file(query)
    rows = []
    for file in files:
        count = (len((CUP_DIR / file).read_text()) + 3) // 4
        active = file == selected
        cls = "border-stone-600 bg-yellow-50" if active else "border-transparent bg-stone-50 hover:border-stone-300"
        href = "/__wirecup?file=" + urllib.parse.quote(file)
        ph = "/render/" + urllib.parse.quote(file, safe="/")
        label = html.escape(Path(file).stem)
        rows.append(f'<a class="flex items-center justify-between p-2 rounded-lg border-2 no-underline text-inherit {cls}" href="{href}"><div class="flex flex-col min-w-0"><span class="text-sm font-medium truncate">{label}</span><span class="text-[10px] text-stone-400">{count} tokens</span></div><span class="ml-2 text-stone-500 hover:text-stone-700 shrink-0" onclick="event.preventDefault();event.stopPropagation();window.open(\'{ph}\',\'_blank\');" role="button"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg></span></a>')
    if not rows:
        rows.append('<p class="text-sm text-stone-500">No .cup files found</p>')
    if selected:
        count = (len((CUP_DIR / selected).read_text()) + 3) // 4
        main = f'<span class="absolute top-4 left-4 z-10 text-xs text-stone-500 bg-stone-100 px-2 py-1 rounded">{count} tokens</span><iframe src="/render/{urllib.parse.quote(selected, safe="/")}" class="w-full h-full border-0"></iframe>'
    else:
        main = f'<div class="p-8"><h2 class="text-xl font-semibold">No previews available</h2><p class="mt-2 text-stone-500">Create a <code>.cup</code> file in <code>{html.escape(str(CUP_DIR))}</code></p></div>'
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Wirecup</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Balsamiq+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
<style>body{{font-family:'Balsamiq Sans',sans-serif;}}</style></head>
<body class="m-0 bg-stone-100 text-stone-800">
<div class="flex h-screen">
  <aside class="w-64 h-full overflow-y-auto border-r-2 border-stone-300 bg-stone-200 p-3 flex flex-col">
    <h1 class="text-lg font-semibold mb-3 text-stone-700">Wirecup</h1>
    <div class="space-y-1 flex-1">{"".join(rows)}</div>
    <div class="pt-4 border-t border-stone-300"><span class="text-xs text-stone-500">{html.escape(str(PROJECT_ROOT))}</span></div>
  </aside>
  <main class="flex-1 flex flex-col relative min-w-0">{main}</main>
</div>
{RELOAD_SCRIPT}</body></html>"""

class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    html = cup_name = ""
    current_route = "/"
    sse_clients = []
    server_port = 8765

    def _send_html(self, body):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data):
        import json
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        if path == "/api/ready":
            return self._send_json({
                "ready": True,
                "port": self.server_port,
                "project": str(PROJECT_ROOT),
                "url": f"http://localhost:{self.server_port}/"
            })
        if path == "/api/files":
            out = []
            for f in rel_files():
                text = (CUP_DIR / f).read_text()
                out.append({"file": f, "bytes": len(text), "errors": validate_cup_file(text.splitlines())})
            return self._send_json({"project": str(PROJECT_ROOT), "dir": str(CUP_DIR), "files": out})
        if path == "/__wirecup_events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            LiveReloadHandler.sse_clients.append(self.wfile)
            try:
                while True: time.sleep(1)
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                LiveReloadHandler.sse_clients.remove(self.wfile)
            return
        if path == "/__wirecup":
            return self._send_html(preview_shell(parsed.query).encode())
        if path.startswith("/render/"):
            cup = safe_cup_path(urllib.parse.unquote(path[8:]))
            if not cup: self.send_error(404, "Not found"); return
            return self._send_html(render_cup_file(cup).encode())
        if path.count("/") == 1 and "." not in path.strip("/"):
            if path != "/":
                LiveReloadHandler.current_route = path
                _rebuild()
            return self._send_html((preview_shell() if path == "/" else self.html).encode())
        super().do_GET()

    def do_POST(self):
        if urllib.parse.urlsplit(self.path).path == "/api/validate":
            size = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(size).decode("utf-8", "replace")
            errors = validate_cup_file(body.splitlines())
            return self._send_json({"ok": not errors, "errors": errors})
        self.send_error(404, "Not found")

    def log_message(self, *args):
        logger.debug("%s - %s", self.address_string(), args[0] % args[1:])

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def project_on_port(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ready", timeout=0.4) as r:
            data = json.loads(r.read().decode())
        return Path(data["project"]).resolve() if data.get("ready") else None
    except Exception:
        return None

def listen(port, attempts=32):
    mine = PROJECT_ROOT.resolve()
    for p in range(port, port + attempts):
        taken = project_on_port(p)
        if taken == mine:
            return None, p
        try:
            return ReusableTCPServer(("", p), LiveReloadHandler), p
        except OSError as e:
            if e.errno != errno.EADDRINUSE:
                raise
    raise OSError(f"No free port in {port}-{port + attempts - 1}")

def _rebuild():
    cup = cup_for_route(LiveReloadHandler.current_route)
    if cup is None:
        LiveReloadHandler.cup_name = ""
        LiveReloadHandler.html = page_wrap(_css(), '<p class="text-stone-600">No .cup files yet. Write one into .wirecup/</p>', "wirecup").replace("</body>", RELOAD_SCRIPT + "</body>")
    else:
        LiveReloadHandler.html = render_cup_file(cup)
        LiveReloadHandler.cup_name = cup.name

def dev_server(port, save, no_browser=False):
    ev = threading.Event(); ev.set()

    class Watcher(FileSystemEventHandler):
        def _h(self, e):
            if not e.is_directory:
                p = Path(e.src_path)
                if p.suffix == ".cup" or p.name == "wirecup.css": ev.set()
        on_modified = on_created = _h

    def rebuild():
        _rebuild()
        cup = cup_for_route(LiveReloadHandler.current_route)
        if save and cup: cup.with_suffix(".html").write_text(LiveReloadHandler.html)
        logger.debug(f"Reloaded {LiveReloadHandler.cup_name or '.wirecup'}")
        dead = []
        for w in LiveReloadHandler.sse_clients:
            try: w.write(b"data: reload\n\n"); w.flush()
            except (BrokenPipeError, ConnectionResetError): dead.append(w)
        for w in dead: LiveReloadHandler.sse_clients.remove(w)

    CUP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Watching {CUP_DIR}")
    _rebuild()
    os.chdir(CUP_DIR)
    server, port = listen(port)
    url = f"http://localhost:{port}/"
    if server is None:
        logger.info(f"Already running at {url}")
        print(url, file=sys.stderr, flush=True)
        if not no_browser:
            webbrowser.open(url)
        return
    LiveReloadHandler.server_port = port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://localhost:{port}/"
    logger.info(f"Server ready at {url}")
    print(url, file=sys.stderr, flush=True)
    obs = Observer()
    h = Watcher()
    obs.schedule(h, str(CUP_DIR), recursive=True)
    obs.schedule(h, str(PROJECT_ROOT), recursive=False)
    obs.start()
    if not no_browser:
        threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()
    try:
        while True:
            ev.wait(5.0)
            if ev.is_set(): ev.clear(); rebuild()
    except KeyboardInterrupt:
        obs.stop(); server.shutdown()
    finally:
        obs.join()

def get_version():
    version_file = APP_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "dev"

def main():
    p = argparse.ArgumentParser(description="Wirecup wireframe renderer")
    p.add_argument("target", nargs="?", default=".")
    p.add_argument("--web", action="store_true")
    p.add_argument("-p", "--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    p.add_argument("--version", action="version", version=f"wirecup {get_version()}")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s"
    )
    target = Path(args.target).resolve()
    if target.is_dir():
        global PROJECT_ROOT, CUP_DIR, INCLUDE_DIR
        PROJECT_ROOT = target
        CUP_DIR = target / ".wirecup"
        INCLUDE_DIR = CUP_DIR / "_includes"
        dev_server(args.port, save=False, no_browser=args.no_browser)
    elif target.is_file() and target.suffix == ".cup":
        css_p = target.parent / "wirecup.css"
        css = css_p.read_text() if css_p.exists() else _css()
        out = render(target.read_text().splitlines(), css, target.stem)
        if args.web:
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                f.write(out); tmp = f.name
            webbrowser.open(f"file://{tmp}"); input("Press Enter to exit..."); os.unlink(tmp)
        else:
            op = target.with_suffix(".html"); op.write_text(out); print(f"Rendered {op}")
    else:
        print(f"Error: {target} is not a directory or .cup file"); sys.exit(1)

if __name__ == "__main__":
    main()
