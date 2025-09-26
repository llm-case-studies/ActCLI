from __future__ import annotations

import base64
import hashlib
import http.server
import os
import socket
import threading
import time
import urllib.parse as up
from dataclasses import dataclass
from typing import Optional

import httpx


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def generate_pkce_pair() -> tuple[str, str]:
    verifier = _b64url(os.urandom(32))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@dataclass
class OAuthConfig:
    auth_url: str
    token_url: str
    client_id: str
    scope: Optional[str] = None
    audience: Optional[str] = None


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):  # type: ignore
        try:
            parsed = up.urlparse(self.path)
            qs = up.parse_qs(parsed.query)
            if "code" in qs:
                _CallbackHandler.code = qs["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Login successful. You can close this window.")
            else:
                _CallbackHandler.error = qs.get("error", ["unknown_error"])[0]
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Login failed.")
        except Exception:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal error.")

    def log_message(self, format, *args):  # noqa: N802
        # Silence server logs in CLI
        return


def pkce_browser_login(
    cfg: OAuthConfig, timeout_s: int = 300
) -> tuple[str, Optional[int]]:
    """Perform PKCE browser login. Returns (access_token, expires_at).

    Starts localhost callback server, opens browser to provider login, exchanges code for token.
    """
    import webbrowser

    port = _find_free_port()
    redirect_uri = f"http://127.0.0.1:{port}/callback"
    verifier, challenge = generate_pkce_pair()

    params = {
        "client_id": cfg.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    if cfg.scope:
        params["scope"] = cfg.scope
    if cfg.audience:
        params["audience"] = cfg.audience

    url = f"{cfg.auth_url}?{up.urlencode(params)}"

    # Start callback server
    server = http.server.HTTPServer(("127.0.0.1", port), _CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Launch browser
    webbrowser.open(url)

    # Poll for code
    start = time.time()
    while time.time() - start < timeout_s:
        if _CallbackHandler.code or _CallbackHandler.error:
            break
        time.sleep(0.4)

    server.shutdown()

    if _CallbackHandler.error:
        raise RuntimeError(f"Login failed: {_CallbackHandler.error}")
    if not _CallbackHandler.code:
        raise TimeoutError("Login timed out")

    code = _CallbackHandler.code
    with httpx.Client(timeout=10) as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": cfg.client_id,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        }
        r = client.post(cfg.token_url, data=data)
        r.raise_for_status()
        tok = r.json()
        access_token = tok.get("access_token")
        expires_in = tok.get("expires_in")
        if not access_token:
            raise RuntimeError("No access_token in response")
        expires_at = int(time.time() + int(expires_in)) if expires_in else None
        return access_token, expires_at
