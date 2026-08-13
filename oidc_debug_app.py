import base64
import hashlib
import html
import json
import os
import secrets
import textwrap
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer


HOST = "localhost"
PORT = 8199
REDIRECT_URI = f"http://{HOST}:{PORT}"


TENANTS = {
    "working": {
        "label": "Working 168c / KXSSO",
        "tenant_id": "168c9905-3a5c-40ac-b5e3-3d33291c3f6c",
        "client_id": "62506fec-034a-4875-98ec-9021482cebdc",
        "client_secret_env": "OIDC_WORKING_SECRET",
    },
    "other": {
        "label": "Other 49a5 / JOHNS-KX-Application-SSO",
        "tenant_id": "49a50445-bdfa-4b79-ade3-547b4f3986e9",
        "client_id": "1ae8ed21-f20f-41b6-bcd6-000f4119bf5d",
        "client_secret_env": "OIDC_OTHER_SECRET",
    },
}


SESSIONS = {}


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_pkce_pair() -> tuple[str, str]:
    verifier = b64url(secrets.token_bytes(48))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def decode_jwt(token: str):
    parts = token.split(".")
    if len(parts) < 2:
        return {"error": "not-a-jwt", "raw": token}

    def decode_part(part: str):
        padding = "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part + padding).decode("utf-8"))

    try:
        return {
            "header": decode_part(parts[0]),
            "payload": decode_part(parts[1]),
        }
    except Exception as exc:
        return {"error": f"jwt-decode-failed: {exc}"}


def html_page(title: str, body: str) -> bytes:
    page = f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; color: #111827; }}
    h1, h2 {{ margin: 0 0 16px; }}
    .buttons {{ display: flex; gap: 12px; margin: 20px 0 28px; }}
    a.button {{ background: #2563eb; color: white; padding: 12px 16px; text-decoration: none; border-radius: 8px; font-weight: 600; }}
    a.button.secondary {{ background: #374151; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f3f4f6; padding: 16px; border-radius: 8px; overflow: auto; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .note {{ color: #4b5563; margin-bottom: 20px; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""
    return page.encode("utf-8")


def render_home() -> bytes:
    items = []
    for key, tenant in TENANTS.items():
        secret_present = bool(os.environ.get(tenant["client_secret_env"]))
        items.append(
            f"<li><code>{html.escape(tenant['label'])}</code> - secret {'present' if secret_present else 'missing'} in <code>{tenant['client_secret_env']}</code></li>"
        )

    body = f"""
    <h1>OIDC Debug App</h1>
    <p class=\"note\">Starts a standard authorization code flow with PKCE and redeems the code locally so we can inspect the exact token claims and any Entra error.</p>
    <div class=\"buttons\">
      <a class=\"button\" href=\"/start?tenant=working\">Test working tenant</a>
      <a class=\"button secondary\" href=\"/start?tenant=other\">Test other tenant</a>
    </div>
    <h2>Config</h2>
    <ul>{''.join(items)}</ul>
    <p><code>Redirect URI:</code> {html.escape(REDIRECT_URI)}</p>
    <p><code>Scope:</code> openid profile email offline_access User.Read</p>
    """
    return html_page("OIDC Debug App", body)


def render_result(title: str, payload: dict) -> bytes:
    pretty = html.escape(json.dumps(payload, indent=2, sort_keys=True))
    body = f"""
    <h1>{html.escape(title)}</h1>
    <div class=\"buttons\">
      <a class=\"button secondary\" href=\"/\">Back</a>
    </div>
    <pre>{pretty}</pre>
    """
    return html_page(title, body)


def fetch_token(token_url: str, form_data: dict[str, str]) -> dict:
    encoded = urllib.parse.urlencode(form_data).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return {
                "ok": True,
                "status": response.status,
                "json": json.loads(raw),
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return {
            "ok": False,
            "status": exc.code,
            "json": parsed,
        }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if parsed.path == "/" and not ("code" in params or "error" in params):
                self.respond(200, render_home())
                return

            callback_paths = {"/", "/callback"}

            if parsed.path == "/start":
                tenant_key = params.get("tenant", [""])[0]
                tenant = TENANTS.get(tenant_key)
                if not tenant:
                    self.respond(400, render_result("Invalid tenant", {"error": "unknown tenant"}))
                    return

                state = secrets.token_urlsafe(24)
                nonce = secrets.token_urlsafe(24)
                verifier, challenge = make_pkce_pair()

                SESSIONS[state] = {
                    "tenant_key": tenant_key,
                    "nonce": nonce,
                    "verifier": verifier,
                    "created_at": time.time(),
                }

                auth_url = (
                    f"https://login.microsoftonline.com/{tenant['tenant_id']}/oauth2/v2.0/authorize?"
                    + urllib.parse.urlencode(
                        {
                            "client_id": tenant["client_id"],
                            "response_type": "code",
                            "redirect_uri": REDIRECT_URI,
                            "response_mode": "query",
                            "scope": "openid profile email offline_access User.Read",
                            "state": state,
                            "nonce": nonce,
                            "code_challenge": challenge,
                            "code_challenge_method": "S256",
                            "prompt": "select_account",
                        }
                    )
                )
                self.send_response(302)
                self.send_header("Location", auth_url)
                self.end_headers()
                return

            if parsed.path in callback_paths and ("code" in params or "error" in params):
                if "error" in params:
                    payload = {
                        "authorize_error": params.get("error", [None])[0],
                        "authorize_error_description": params.get("error_description", [None])[0],
                        "state": params.get("state", [None])[0],
                    }
                    self.respond(200, render_result("Authorize error", payload))
                    return

                code = params.get("code", [None])[0]
                state = params.get("state", [None])[0]
                session = SESSIONS.pop(state, None)
                if not code or not session:
                    self.respond(400, render_result("Callback error", {"error": "missing code or invalid state"}))
                    return

                tenant = TENANTS[session["tenant_key"]]
                secret = os.environ.get(tenant["client_secret_env"], "")
                token_response = fetch_token(
                    f"https://login.microsoftonline.com/{tenant['tenant_id']}/oauth2/v2.0/token",
                    {
                        "client_id": tenant["client_id"],
                        "client_secret": secret,
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": REDIRECT_URI,
                        "code_verifier": session["verifier"],
                        "scope": "openid profile email offline_access User.Read",
                    },
                )

                result = {
                    "tenant": tenant,
                    "token_response_ok": token_response["ok"],
                    "token_status": token_response["status"],
                    "token_json": token_response["json"],
                }

                if token_response["ok"]:
                    token_json = token_response["json"]
                    id_token = token_json.get("id_token")
                    access_token = token_json.get("access_token")

                    redacted = dict(token_json)
                    if "id_token" in redacted:
                        redacted["id_token"] = "<redacted jwt>"
                    if "access_token" in redacted:
                        redacted["access_token"] = "<redacted jwt>"
                    if "refresh_token" in redacted:
                        redacted["refresh_token"] = "<redacted>"

                    result["token_json"] = redacted
                    result["decoded_id_token"] = decode_jwt(id_token) if id_token else None
                    result["decoded_access_token"] = decode_jwt(access_token) if access_token else None

                self.respond(200, render_result("OIDC result", result))
                return

            self.respond(404, render_result("Not found", {"path": parsed.path}))
        except Exception as exc:
            payload = {
                "error": str(exc),
                "path": self.path,
            }
            self.respond(500, render_result("Server error", payload))

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt, *args):
        return

    def respond(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(textwrap.dedent(
        f"""
        OIDC debug app running.
        Open: http://{HOST}:{PORT}/
        Redirect URI in use: {REDIRECT_URI}
        """
    ).strip())
    server.serve_forever()


if __name__ == "__main__":
    main()
