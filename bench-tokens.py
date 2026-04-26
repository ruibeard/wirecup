#!/usr/bin/env python3
"""Token efficiency benchmark for Wirecup .cup vs HTML output."""

import tiktoken
from pathlib import Path

encoder = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoder.encode(text))

def benchmark(cup_path: Path):
    html_path = cup_path.with_suffix(".html")
    cup_text = cup_path.read_text()
    html_text = html_path.read_text()
    cup_tok = count_tokens(cup_text)
    html_tok = count_tokens(html_text)
    ratio = html_tok / cup_tok if cup_tok else 0
    print(f"{cup_path.name:45}  cup={cup_tok:4}  html={html_tok:5}  ratio={ratio:.1f}x")

print(f"{'File':45}  {'cup':>4}  {'html':>5}  {'ratio':>5}")
print("-" * 70)

for p in sorted(Path("examples").rglob("*.cup")):
    benchmark(p)

# Also benchmark a verbose natural-language description of login
print()
print("--- Bonus: verbose description vs .cup ---")
verbose = """
Create a login page. At the top, add a navigation bar with a logo on the left.
Below that, place a horizontal divider. Then add a large heading that says "Login".
Under the heading, add a text label "Email" followed by an empty text input field.
Then add a text label "Password" followed by another empty text input field.
Below the inputs, add a button labeled "Sign In" that links to the dashboard page.
Finally, add a text link that says "Forgot password?".
"""
print(f"login.cup        = {count_tokens(Path('examples/cup/login.cup').read_text())} tokens")
print(f"verbose desc     = {count_tokens(verbose)} tokens")
print(f"rendered HTML    = {count_tokens(Path('examples/cup/login.html').read_text())} tokens")
