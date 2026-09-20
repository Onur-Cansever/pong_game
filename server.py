#!/usr/bin/env python3
"""Pong sunucu: statik dosyalar + /brain (AI) endpoint'i. Bağımlılık yok."""
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import brain

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8077

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # sessiz
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/brain":
            try:
                ln = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(ln) or b"{}")
                out = brain.brain(data)
                self._send(200, json.dumps(out))
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)}))
        else:
            self._send(404, "{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            path = "/pong.html"
        if path == "/brain":
            # sağlık kontrolü
            return self._send(200, json.dumps({"ok": True,
                "skill": brain.load_memory().get("skill", 0)}))
        if path.startswith("/ai_memory"):
            return self._send(200, json.dumps(brain.load_memory()))
        if path == "/clear_memory":
            brain.clear_memory()
            return self._send(200, json.dumps({"ok": True}))
        # statik
        safe = os.path.normpath(path).lstrip("/")
        fp = os.path.join(ROOT, safe)
        if os.path.isfile(fp):
            ctype = "text/html; charset=utf-8" if fp.endswith(".html") \
                    else "application/octet-stream"
            with open(fp, "rb") as f:
                self._send(200, f.read(), ctype)
        else:
            self._send(404, "not found", "text/plain")

if __name__ == "__main__":
    brain.load_memory()
    print(f"Pong sunucu: http://localhost:{PORT}  (beyin: /brain, hafıza: /ai_memory)")
    # Tarayıcıyı otomatik aç (isteğe bağlı: --no-open ile kapatılır)
    if "--no-open" not in sys.argv:
        import webbrowser, threading
        threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
