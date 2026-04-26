#!/usr/bin/env python3
"""Token efficiency benchmark for Wirecup .cup files vs rendered HTML."""

import importlib.util
import re
from pathlib import Path

try:
    import tiktoken
except ModuleNotFoundError:
    tiktoken = None

ROOT = Path(__file__).parent
EXAMPLES = ROOT / "examples"


def load_renderer():
    spec = importlib.util.spec_from_file_location("wirecup_render", ROOT / "wirecup-render.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load wirecup-render.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def count_tokens(text: str) -> int:
    if tiktoken is None:
        return len(re.findall(r"\w+|[^\w\s]", text))
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


def benchmark(cup_path: Path, renderer, support_css: str):
    cup_text = cup_path.read_text()
    html_text = renderer.render(cup_text.splitlines(), support_css)
    cup_tok = count_tokens(cup_text)
    html_tok = count_tokens(html_text)
    ratio = html_tok / cup_tok if cup_tok else 0
    print(f"{cup_path.relative_to(ROOT)!s:45}  cup={cup_tok:4}  html={html_tok:5}  ratio={ratio:.1f}x")


def main():
    renderer = load_renderer()
    support_css = renderer.load_support_css()

    if tiktoken is None:
        print("tiktoken is not installed; using approximate regex token counts.")
        print()

    print(f"{'File':45}  {'cup':>4}  {'html':>5}  {'ratio':>5}")
    print("-" * 70)

    for cup_path in sorted(EXAMPLES.rglob("*.cup")):
        benchmark(cup_path, renderer, support_css)


if __name__ == "__main__":
    main()
