#!/usr/bin/env bash
# ============================================================
#  BEAT THE AI - Pong  (Linux) — tek bolumlu uygulama uret
#  Ciktı: dist/Pong  (calistirilabilir; icinden sunucu + oyun)
#  Kullanım:
#    ./build.sh            (Pong ismiyle)
#    ./build.sh --port 9000  (port sabitleyerek)
#  Gerekli: Python + PyInstaller  (ilk calistirmada kendisi kurar)
# ============================================================
set -e
cd "$(dirname "$0")"

# ---- venv (PyInstaller'i ana Python'a dokunmadan kur) ----
VENV_DIR="${BUILD_VENV:-.build-venv}"
if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo ">> Python venv olusturuluyor: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
PY="$VENV_DIR/bin/python"

if ! "$PY" -c "import PyInstaller" 2>/dev/null; then
    echo ">> PyInstaller kuruluyor..."
    "$PY" -m pip install --quiet pyinstaller
fi

# ---- argumanlari PyInstaller'a ilet ----
PORT_ARG=""
if [ "$1" = "--port" ]; then
    PORT_ARG="--port ${2:-8077}"
fi

echo ">> PyInstaller ile Linux binary derleniyor..."
"$VENV_DIR/bin/pyinstaller" --onefile --name Pong \
    --hidden-import brain \
    --add-data "pong.html:." --add-data "terminator_music.webm:." \
    --distpath dist --workpath build --specpath . \
    server.py
chmod +x dist/Pong

echo ""
echo "TAMAM: dist/Pong"
echo "  Calistirmak icin:  ./dist/Pong          (tarayici acilir)"
echo "  Port degistirme:  ./dist/Pong --port 9000"
echo "  Arkadasina gonder:  zip -r pong-linux.zip dist/Pong"
echo ""
echo "Not: Bu binary YALNIZCA Linux x86_64 icin derlendi."
echo "     Windows icin:  ./build-windows.sh (bu makinede wine ile)"
echo "                     ya da Windows'ta exe-yap.bat"
