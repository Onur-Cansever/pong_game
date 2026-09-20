#!/usr/bin/env python3
"""Pong sunucu: statik dosyalar + /brain (AI) endpoint'i. Bağımlılık yok."""
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import brain

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8077

def _data_roots():
    """Statik dosyaların aranacağı dizinler (PyInstaller onefile uyumlu).
    onefile exe'de kaynaklar geçici _MEIPASS dizinine çıkarilir; __file__ ise
    bazen orijinal kaynak dizinini gösterir. Üçü de denenir."""
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(meipass)
    roots.append(ROOT)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        if exe_dir not in roots:
            roots.append(exe_dir)
    return roots

def _static_file(path):
    safe = os.path.normpath(path).lstrip("/")
    for r in _data_roots():
        fp = os.path.join(r, safe)
        if os.path.isfile(fp):
            return fp
    return None

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
        # statik (PyInstaller onefile: _MEIPASS / kaynak / exe dizini denenir)
        fp = _static_file(path)
        if fp:
            ctype = "text/html; charset=utf-8" if fp.endswith(".html") \
                    else "application/octet-stream"
            with open(fp, "rb") as f:
                self._send(200, f.read(), ctype)
        else:
            return self._send(404,
                "not found: %s  (aranan dizinler: %s)"
                % (path, "; ".join(_data_roots())), "text/plain")

if __name__ == "__main__":
    # Port: --port 8078  (varsayılan 8077)
    if "--port" in sys.argv:
        PORT = int(sys.argv[sys.argv.index("--port") + 1])
    # PyInstaller onefile: _MEIPASS dizinini sys.path'e ekleyerek brain.py yüklenir
    if getattr(sys, "frozen", False):
        _mp = getattr(sys, "_MEIPASS", None)
        if _mp and _mp not in sys.path:
            sys.path.insert(0, _mp)
    # Donmuş exe'de AI hafızası exe'nin yanına yazılsın (geçici _MEIPASS yerine)
    if getattr(sys, "frozen", False):
        brain.LS_PATH = os.path.join(os.path.dirname(sys.executable), "ai_memory.json")
    brain.load_memory()
    print(f"Pong sunucu: http://localhost:{PORT}  (beyin: /brain, hafıza: /ai_memory)")
    # Tarayıcıyı otomatik aç (isteğe bağlı: --no-open ile kapatılır)
    if "--no-open" not in sys.argv:
        import webbrowser, threading
        threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    try:
        ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    except OSError as e:
        # Port kapalıysa (örn. baslat.bat hâlâ çalışıyor) net hata ver
        print("Port %d kullanılamadı: %s" % (PORT, e))
        print("Başka bir Pong sunucusu mu çalışıyor? (öncekini kapatıp dene) ya da:")
        print("  python server.py --port 8078")
        try:
            input("Kapatmak için Enter...")
        except Exception:
            pass
        sys.exit(1)
